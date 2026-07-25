"""Retrain PhoBERT on the repaired Round-5 splits with multiple seeds.

Usage:
    .venv/bin/python scripts/train_phobert_round5_multiseed.py
"""

from __future__ import annotations

# Set offline mode BEFORE importing transformers
import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import sys
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
from torch.optim import AdamW
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
import warnings
warnings.filterwarnings("ignore")

# ── Config ──────────────────────────────────────────────────────────────────
DATA_DIR = PROJECT_DIR / "data"
LABELED_DIR = DATA_DIR / "labeled"
MODEL_DIR = PROJECT_DIR / "models"
OUTPUT_DIR = MODEL_DIR / "round5_predictions"
RESULTS_DIR = PROJECT_DIR / "results"

TRAIN_FILE = LABELED_DIR / "final_train.csv"
VAL_FILE = LABELED_DIR / "final_val.csv"
TEST_FILE = LABELED_DIR / "final_test.csv"
CROSS_DOMAIN_FILE = PROJECT_DIR / "data_unified" / "cross_domain_test.csv"
EVALUATION_FILES = {
    "validation": VAL_FILE,
    "in_domain": TEST_FILE,
    "cross_domain": CROSS_DOMAIN_FILE,
}

MODEL_NAME = str(MODEL_DIR / "phobert_base_local")
MAX_LEN = 128
TRAIN_BATCH_SIZE = 8
VALIDATION_BATCH_SIZE = 16
EVALUATION_BATCH_SIZE = 32
EPOCHS = 3
SEEDS = [42, 123, 2024]

# ── Set seed ──────────────────────────────────────────────────────────────────
def set_seed(seed: int):
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    elif torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)

device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
print(f"Device: {device}")

# ── Tokenizer ─────────────────────────────────────────────────────────────────
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False)

# ── Custom Dataset ─────────────────────────────────────────────────────────────
class DepressionDataset(Dataset):
    def __init__(self, texts, labels=None):
        self.texts = texts
        self.labels = labels

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        encoding = tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=MAX_LEN,
            return_tensors="pt"
        )
        item = {key: val.squeeze(0) for key, val in encoding.items()}
        if self.labels is not None:
            item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item

# ── Training function ──────────────────────────────────────────────────────────
def train_model(seed: int, train_texts, train_labels, val_texts, val_labels, output_dir: Path):
    set_seed(seed)
    print(f"\n{'='*60}")
    print(f"TRAINING WITH SEED {seed}")
    print(f"{'='*60}")

    # Create model
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=2, ignore_mismatched_sizes=True
    )
    model.to(device)

    # Create datasets
    train_dataset = DepressionDataset(train_texts, train_labels)
    val_dataset = DepressionDataset(val_texts, val_labels)

    train_loader = DataLoader(train_dataset, batch_size=TRAIN_BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=VALIDATION_BATCH_SIZE, shuffle=False)

    # Optimizer
    optimizer = AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)
    total_steps = len(train_loader) * EPOCHS
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(total_steps * 0.06), num_training_steps=total_steps
    )

    # Class weights
    n_neg = (train_labels == 0).sum()
    n_pos = (train_labels == 1).sum()
    pos_weight = n_neg / n_pos
    criterion = nn.CrossEntropyLoss(weight=torch.tensor([1.0, pos_weight], dtype=torch.float32).to(device))

    best_f1 = 0.0
    seed_dir = output_dir / f"seed_{seed}"

    for epoch in range(EPOCHS):
        # Train
        model.train()
        total_loss = 0
        for batch in train_loader:
            optimizer.zero_grad()

            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            loss = criterion(outputs.logits, labels)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)

        # Eval
        model.eval()
        all_preds = []
        all_labels = []

        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels = batch["labels"]

                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
                all_preds.extend(preds)
                all_labels.extend(labels.numpy())

        # Calculate F1
        f1 = f1_score(all_labels, all_preds, average="macro")
        acc = accuracy_score(all_labels, all_preds)
        print(f"Epoch {epoch+1}: Loss={avg_loss:.4f}, Acc={acc:.4f}, F1={f1:.4f}")

        # Save best model
        if f1 > best_f1:
            best_f1 = f1
            seed_dir.mkdir(parents=True, exist_ok=True)
            checkpoint_path = seed_dir / "best_model"
            model.save_pretrained(str(checkpoint_path))
            tokenizer.save_pretrained(str(checkpoint_path))

    print(f"Best F1 for seed {seed}: {best_f1:.4f}")
    return best_f1, seed_dir

# ── Evaluation function ────────────────────────────────────────────────────────
def compute_metrics(labels, predictions):
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "precision_macro": float(precision_score(labels, predictions, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(labels, predictions, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(labels, predictions, average="weighted", zero_division=0)),
        "f1_depression": float(f1_score(labels, predictions, average="binary", pos_label=1, zero_division=0)),
        "confusion_matrix": confusion_matrix(labels, predictions, labels=[0, 1]).tolist(),
    }


def evaluate_model(model_dir: Path, test_texts, test_labels, split_name: str = "test"):
    print(f"\n--- Evaluating {split_name} set ---")

    model = AutoModelForSequenceClassification.from_pretrained(str(model_dir / "best_model"))
    model.to(device)
    model.eval()

    test_dataset = DepressionDataset(test_texts)
    test_loader = DataLoader(test_dataset, batch_size=EVALUATION_BATCH_SIZE, shuffle=False)

    all_preds = []
    all_probs = []

    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()

            all_preds.extend(preds)
            all_probs.extend(probs[:, 1].cpu().numpy())

    metrics = compute_metrics(test_labels, all_preds)

    print(f"{split_name.capitalize()} Results:")
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  F1 (macro): {metrics['f1_macro']:.4f}")
    print(f"  F1 (dep):   {metrics['f1_depression']:.4f}")
    print(f"  Precision:  {metrics['precision_macro']:.4f}")
    print(f"  Recall:     {metrics['recall_macro']:.4f}")

    return {
        **metrics,
        "predictions": all_preds,
        "probabilities": all_probs
    }

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-file", type=Path, default=TRAIN_FILE)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--result-name", default="phobert_results_clean.json")
    parser.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    parser.add_argument(
        "--evaluation-splits",
        nargs="+",
        choices=sorted(EVALUATION_FILES),
        default=sorted(EVALUATION_FILES),
        help="Splits to load after training; candidate selection runs must use validation only",
    )
    args = parser.parse_args()
    seeds = sorted(set(args.seeds))
    evaluation_splits = list(dict.fromkeys(args.evaluation_splits))
    if "validation" not in evaluation_splits:
        raise ValueError("validation must be included because checkpoints are selected on it")
    result_tag = Path(args.result_name).stem.replace("phobert_results_", "")

    timestamp = datetime.now().isoformat()
    results_dir = RESULTS_DIR / "reproducible_round5"
    results_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("ROUND 5 PHOBERT TRAINING WITH MULTIPLE SEEDS")
    print("="*60)

    # Load data
    print(f"\nLoading data...")
    train_df = pd.read_csv(args.train_file)
    val_df = pd.read_csv(VAL_FILE)
    evaluation_frames = {
        split_name: (val_df if split_name == "validation" else pd.read_csv(EVALUATION_FILES[split_name]))
        for split_name in evaluation_splits
    }

    print(
        f"Train: {len(train_df):,} | "
        + " | ".join(
            f"{split_name}: {len(frame):,}"
            for split_name, frame in evaluation_frames.items()
        )
    )

    train_texts = train_df["comment_text"].values
    train_labels = train_df["label"].values
    val_texts = val_df["comment_text"].values
    val_labels = val_df["label"].values

    # Train with each seed
    all_results = {}

    for seed in seeds:
        f1, model_dir = train_model(seed, train_texts, train_labels, val_texts, val_labels, args.output_dir)
        evaluation_results = {}
        for split_name, frame in evaluation_frames.items():
            evaluation_results[split_name] = evaluate_model(
                model_dir,
                frame["comment_text"].values,
                frame["label"].values,
                split_name,
            )
        all_results[seed] = {
            "model_dir": str(model_dir),
            "val_f1": float(f1),
            **evaluation_results,
        }

        for split_name, frame in evaluation_frames.items():
            split_results = evaluation_results[split_name]
            pd.DataFrame({
                "comment_text": frame["comment_text"].astype(str),
                "label": frame["label"].astype(int),
                "prediction": split_results["predictions"],
                "probability_depression": split_results["probabilities"],
            }).to_csv(
                results_dir / f"phobert_{result_tag}_seed{seed}_{split_name}_predictions.csv",
                index=False,
            )

    ensemble_predictions = {
        split_name: (
            np.asarray([
                all_results[seed][split_name]["predictions"] for seed in seeds
            ]).mean(axis=0) >= 0.5
        ).astype(int)
        for split_name in evaluation_splits
    }

    def summarize(split: str) -> dict:
        keys = ["accuracy", "precision_macro", "recall_macro", "f1_macro", "f1_weighted", "f1_depression"]
        summary = {}
        for key in keys:
            values = [all_results[s][split][key] for s in seeds]
            summary[key] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                "per_seed": {str(seed): float(all_results[seed][split][key]) for seed in seeds},
            }
        return summary

    # Save results
    results = {
        "timestamp": timestamp,
        "protocol": (
            "fit train only; checkpoint selection on fixed validation; only explicitly "
            "requested evaluation splits were loaded"
        ),
        "seeds": seeds,
        "dataset": {
            "train_rows": len(train_df),
            "validation_rows": len(val_df),
            "evaluated_splits": evaluation_splits,
            "split_rows": {
                split_name: len(frame)
                for split_name, frame in evaluation_frames.items()
            },
            "train_label_distribution": {
                str(int(k)): int(v)
                for k, v in train_df["label"].value_counts().sort_index().items()
            },
        },
        "settings": {
            "base_model": MODEL_NAME,
            "max_length": MAX_LEN,
            "train_batch_size": TRAIN_BATCH_SIZE,
            "validation_batch_size": VALIDATION_BATCH_SIZE,
            "evaluation_batch_size": EVALUATION_BATCH_SIZE,
            "epochs": EPOCHS,
            "learning_rate": 2e-5,
            "weight_decay": 0.01,
            "warmup_ratio": 0.06,
            "loss": "class-weighted cross entropy based on train label counts",
            "checkpoint_selection": "highest validation macro F1",
        },
        "per_seed": {
            str(seed): {
                "val_f1": all_results[seed]["val_f1"],
                **{
                    split_name: {
                        key: value
                        for key, value in all_results[seed][split_name].items()
                        if key not in ["predictions", "probabilities"]
                    }
                    for split_name in evaluation_splits
                },
            }
            for seed in seeds
        },
        "mean_std": {
            split_name: summarize(split_name) for split_name in evaluation_splits
        },
        "ensemble_majority_vote": {
            split_name: compute_metrics(
                evaluation_frames[split_name]["label"].astype(int).values,
                ensemble_predictions[split_name],
            )
            for split_name in evaluation_splits
        },
    }

    import json
    results_file = results_dir / args.result_name
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {results_file}")
    print(f"Models saved to: {args.output_dir}/seed_*/best_model")

    return results

if __name__ == "__main__":
    main()
