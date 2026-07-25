"""Utilities dùng chung cho PhoBERT training/prediction."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score

from yt_depression_crawler.processing.cleaner import normalize_text
from yt_depression_crawler.core.config import PHOBERT_DEVICE, PHOBERT_USE_WORD_SEGMENTATION

LABEL_TO_ID = {"normal": 0, "depression": 1}
ID_TO_LABEL = {0: "normal", 1: "depression"}


@dataclass(frozen=True)
class TextExample:
    text: str
    label: int | None = None


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def get_device():
    import torch

    requested = PHOBERT_DEVICE.lower().strip()
    if requested in {"cpu", "cuda", "mps"}:
        if requested == "cuda" and not torch.cuda.is_available():
            return torch.device("cpu")
        if requested == "mps" and not torch.backends.mps.is_available():
            return torch.device("cpu")
        return torch.device(requested)

    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def prepare_phobert_text(text: str) -> str:
    """Normalize và word-segment tiếng Việt để phù hợp PhoBERT."""
    normalized = normalize_text(text)
    if not PHOBERT_USE_WORD_SEGMENTATION:
        return normalized

    try:
        from underthesea import word_tokenize

        return word_tokenize(normalized, format="text")
    except Exception:
        return normalized


def prepare_many_texts(texts: Iterable[str]) -> list[str]:
    return [prepare_phobert_text(text) for text in texts]


def load_labeled_split(path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"comment_text": str}).fillna("")
    required = {"comment_text", "label"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")
    df = df[df["comment_text"].str.strip().ne("")].copy()
    df["label"] = pd.to_numeric(df["label"], errors="coerce").astype(int)
    return df


def compute_class_weights(labels: Iterable[int]):
    import torch

    labels_array = np.array(list(labels), dtype=int)
    counts = np.bincount(labels_array, minlength=2)
    total = counts.sum()
    weights = total / (len(counts) * np.maximum(counts, 1))
    return torch.tensor(weights, dtype=torch.float)


def compute_metrics(y_true, y_pred) -> dict:
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_macro": round(float(precision_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "f1_depression": round(float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
        "classification_report": classification_report(
            y_true,
            y_pred,
            labels=[0, 1],
            target_names=["normal", "depression"],
            zero_division=0,
            output_dict=True,
        ),
    }


class PhoBertDataset:
    def __init__(
        self,
        texts: list[str],
        labels: list[int] | None,
        tokenizer,
        max_length: int,
        weights: list[float] | None = None,
    ) -> None:
        import torch

        self.encodings = tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors="pt",
        )
        self.labels = torch.tensor(labels, dtype=torch.long) if labels is not None else None
        # weights are not added to per-item dict (the model doesn't
        # accept sample_weight kwarg); instead they are consumed by
        # WeightedRandomSampler in phobert_train._build_train_loader.
        self.weights = (
            torch.tensor(weights, dtype=torch.float) if weights is not None else None
        )

    def __len__(self) -> int:
        return self.encodings["input_ids"].shape[0]

    def __getitem__(self, idx: int) -> dict:
        item = {key: value[idx] for key, value in self.encodings.items()}
        if self.labels is not None:
            item["labels"] = self.labels[idx]
        return item
