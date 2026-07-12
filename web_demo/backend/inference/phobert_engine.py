"""PhoBERT inference engine for depression detection.

Loads the Round 5 fine-tuned PhoBERT model and provides batch inference.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Disable proxies so transformers loads from local cache
for _var in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(_var, None)

# ── Paths ─────────────────────────────────────────────────────────────────────
# Backend code is in /app/ (copied from web_demo/backend/)
# Models are mounted at /app/models/
_BACKEND_DIR = Path(__file__).resolve().parent  # /app/inference
_APP_DIR = _BACKEND_DIR.parent  # /app/

PHOBERT_MODEL_DIR = _APP_DIR / "models" / "round5_predictions" / "best_model"
PHOBERT_TOKENIZER_DIR = _APP_DIR / "models" / "phobert_base_local"
MAX_LENGTH = 128
BATCH_SIZE = 16

LABEL_MAP = {0: "normal", 1: "depression"}
logger = logging.getLogger(__name__)


# ── Dataset ───────────────────────────────────────────────────────────────────

class _InferenceDataset(Dataset):
    def __init__(self, texts: list[str], tokenizer, max_length: int):
        self.encodings = tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors="pt",
        )

    def __len__(self) -> int:
        return self.encodings["input_ids"].shape[0]

    def __getitem__(self, idx: int) -> dict:
        return {key: value[idx] for key, value in self.encodings.items()}


# ── Engine ────────────────────────────────────────────────────────────────────

class PhoBertEngine:
    """Singleton PhoBERT inference engine."""

    _instance: Optional["PhoBertEngine"] = None

    def __init__(self) -> None:
        self.device = self._get_device()
        logger.info("PhoBertEngine device: %s", self.device)

        logger.info("Loading PhoBERT tokenizer from %s", PHOBERT_TOKENIZER_DIR)
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(PHOBERT_TOKENIZER_DIR), use_fast=False
        )

        logger.info("Loading PhoBERT model from %s", PHOBERT_MODEL_DIR)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            str(PHOBERT_MODEL_DIR)
        )
        self.model.to(self.device)
        self.model.eval()
        logger.info("PhoBERT model loaded successfully")

    @staticmethod
    def _get_device() -> torch.device:
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    @classmethod
    def get_instance(cls) -> "PhoBertEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def predict_single(self, text: str) -> dict:
        """Run inference on a single text."""
        return self.predict_batch([text])[0]

    def predict_batch(self, texts: list[str]) -> list[dict]:
        """Run inference on a batch of texts."""
        if not texts:
            return []

        # Normalize texts
        normalized = [_normalize_text(t) for t in texts]

        # Tokenize
        dataset = _InferenceDataset(normalized, self.tokenizer, MAX_LENGTH)
        loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False)

        all_probs: list[float] = []
        all_preds: list[int] = []

        with torch.no_grad():
            for batch in loader:
                batch = {k: v.to(self.device) for k, v in batch.items()}
                outputs = self.model(**batch)
                probs = torch.softmax(outputs.logits, dim=-1)
                preds = torch.argmax(probs, dim=-1)

                # prob_depression = class 1
                all_probs.extend(probs[:, 1].cpu().tolist())
                all_preds.extend(preds.cpu().tolist())

        results = []
        for text, pred, prob in zip(texts, all_preds, all_probs):
            label = LABEL_MAP[pred]
            results.append({
                "prediction": label,
                "confidence": round(float(prob), 4),
                "prob_normal": round(float(1 - prob), 4),
                "prob_depression": round(float(prob), 4),
                "risk_level": _get_risk_level(label, prob),
            })
        return results

    def reload(self) -> None:
        """Hot-reload the model (e.g. after a new round is trained)."""
        logger.info("Reloading PhoBERT model...")
        PhoBertEngine._instance = None
        PhoBertEngine._instance = PhoBertEngine()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize_text(text: str) -> str:
    """Lightweight Vietnamese text normalization (no underthesea dependency)."""
    if not text or not isinstance(text, str):
        return ""
    # Lowercase
    text = text.lower().strip()
    # Normalize unicode
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("“", '"').replace("”", '"')
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text


def _get_risk_level(label: str, prob: float) -> str:
    """Map prediction to risk level."""
    if label == "normal":
        return "low"
    # For depression: high confidence (prob) → higher risk
    if prob >= 0.90:
        return "high"
    elif prob >= 0.70:
        return "medium"
    return "low"


# ── Module-level convenience ──────────────────────────────────────────────────

_engine: Optional[PhoBertEngine] = None


def get_engine() -> PhoBertEngine:
    global _engine
    if _engine is None:
        _engine = PhoBertEngine.get_instance()
    return _engine


def predict_text(text: str) -> dict:
    """Convenience function for single-text prediction."""
    return get_engine().predict_single(text)


def predict_batch(texts: list[str]) -> list[dict]:
    """Convenience function for batch prediction."""
    return get_engine().predict_batch(texts)
