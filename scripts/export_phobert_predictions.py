"""Export validation/test probabilities from existing PhoBERT checkpoints.

This is inference-only. It is used to give already-trained clean checkpoints the
same row-level outputs as newly trained augmented checkpoints, without retraining
or changing either fixed holdout.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer


PROJECT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_DIR / "results" / "reproducible_round5"
SPLITS = {
    "validation": PROJECT_DIR / "data" / "labeled" / "final_val.csv",
    "in_domain": PROJECT_DIR / "data" / "labeled" / "final_test.csv",
    "cross_domain": PROJECT_DIR / "data_unified" / "cross_domain_test.csv",
}


class TextDataset(Dataset):
    def __init__(self, texts: list[str], tokenizer, max_length: int):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        encoded = self.tokenizer(
            self.texts[index],
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        return {key: value.squeeze(0) for key, value in encoded.items()}


def metrics(labels: np.ndarray, predictions: np.ndarray) -> dict[str, object]:
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "precision_macro": float(
            precision_score(labels, predictions, average="macro", zero_division=0)
        ),
        "recall_macro": float(
            recall_score(labels, predictions, average="macro", zero_division=0)
        ),
        "f1_macro": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "f1_depression": float(
            f1_score(labels, predictions, average="binary", pos_label=1, zero_division=0)
        ),
        "confusion_matrix": confusion_matrix(labels, predictions, labels=[0, 1]).tolist(),
    }


def predict_checkpoint(
    checkpoint: Path,
    frames: dict[str, pd.DataFrame],
    batch_size: int,
    max_length: int,
    device: torch.device,
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint), use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(str(checkpoint))
    model.to(device)
    model.eval()
    outputs: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    for split_name, frame in frames.items():
        dataset = TextDataset(frame["comment_text"].astype(str).tolist(), tokenizer, max_length)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
        probabilities: list[float] = []
        with torch.no_grad():
            for batch in loader:
                batch = {key: value.to(device) for key, value in batch.items()}
                logits = model(**batch).logits
                probabilities.extend(torch.softmax(logits, dim=-1)[:, 1].cpu().numpy())
        scores = np.asarray(probabilities, dtype=float)
        outputs[split_name] = ((scores >= 0.5).astype(int), scores)

    del model
    if device.type == "mps":
        torch.mps.empty_cache()
    return outputs


def main() -> dict[str, object]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 2024])
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--splits", nargs="+", choices=sorted(SPLITS), default=sorted(SPLITS))
    args = parser.parse_args()

    device = torch.device(
        "cuda" if torch.cuda.is_available()
        else "mps" if torch.backends.mps.is_available()
        else "cpu"
    )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    frames = {name: pd.read_csv(SPLITS[name]) for name in args.splits}
    report: dict[str, object] = {
        "protocol": "inference only; no fitting or threshold selection",
        "tag": args.tag,
        "device": str(device),
        "per_seed": {},
    }

    for seed in sorted(set(args.seeds)):
        checkpoint = args.model_root / f"seed_{seed}" / "best_model"
        if not checkpoint.is_dir():
            raise FileNotFoundError(f"Missing checkpoint: {checkpoint}")
        split_outputs = predict_checkpoint(
            checkpoint, frames, args.batch_size, args.max_length, device
        )
        seed_report: dict[str, object] = {}
        for split_name, (predictions, scores) in split_outputs.items():
            frame = frames[split_name]
            labels = frame["label"].astype(int).to_numpy()
            seed_report[split_name] = metrics(labels, predictions)
            pd.DataFrame({
                "comment_text": frame["comment_text"].astype(str),
                "label": labels,
                "prediction": predictions,
                "probability_depression": scores,
            }).to_csv(
                RESULTS_DIR / f"phobert_{args.tag}_seed{seed}_{split_name}_predictions.csv",
                index=False,
            )
        report["per_seed"][str(seed)] = seed_report

    output = RESULTS_DIR / f"phobert_{args.tag}_inference_export.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {output}")
    return report


if __name__ == "__main__":
    main()
