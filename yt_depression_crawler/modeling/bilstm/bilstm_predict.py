"""Inference helper for BiLSTM models."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import torch

from yt_depression_crawler.core.config import PHOBERT_DEVICE
from yt_depression_crawler.modeling.bilstm.bilstm_dataset import (
    BiLSTMDataset,
    Vocab,
)
from yt_depression_crawler.modeling.bilstm.bilstm_model import (
    BiLSTMConfig,
    BiLSTMPhoBERT,
    BiLSTMRandom,
)

logger = logging.getLogger(__name__)


def _get_device() -> torch.device:
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


def load_bilstm_checkpoint(model_dir: Path) -> tuple:
    """Load model + vocab + variant from disk."""
    payload = torch.load(model_dir / "model.pt", map_location="cpu", weights_only=False)
    cfg = BiLSTMConfig(**payload["config"])
    variant = payload["variant"]
    if variant == "random":
        model = BiLSTMRandom(cfg)
    else:
        model = BiLSTMPhoBERT(cfg)
        model.set_vocab(json.loads((model_dir / "vocab.json").read_text(encoding="utf-8"))["itos"])
    model.load_state_dict(payload["state_dict"])
    model.eval()
    vocab = Vocab.load(model_dir / "vocab.json")
    return model, vocab, variant, cfg


def predict_texts(texts: list[str], model_dir: Path, batch_size: int = 32,
                  max_len: int = 100) -> list[dict]:
    """Predict labels + probabilities for a list of texts.

    Returns a list of dicts: [{"predicted_label": int,
    "prob_normal": float, "prob_depression": float, "comment_text": str}, ...]
    """
    from torch.utils.data import DataLoader

    model, vocab, variant, cfg = load_bilstm_checkpoint(model_dir)
    device = _get_device()
    model.to(device)
    ds = BiLSTMDataset(texts, labels=None, vocab=vocab, max_len=max_len)
    loader = DataLoader(ds, batch_size=batch_size)

    results: list[dict] = []
    idx = 0
    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            logits = model(input_ids)
            probs = torch.softmax(logits, dim=-1).detach().cpu()
            for i in range(probs.shape[0]):
                results.append({
                    "comment_text": texts[idx],
                    "predicted_label": int(torch.argmax(probs[i]).item()),
                    "prob_normal": float(probs[i, 0].item()),
                    "prob_depression": float(probs[i, 1].item()),
                })
                idx += 1
    return results