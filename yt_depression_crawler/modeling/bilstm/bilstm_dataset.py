"""Dataset + vocabulary for BiLSTM training on Vietnamese comments.

Tokenization uses ``underthesea.word_tokenize`` (same as PhoBERT) so
both models consume the same surface tokenization. The vocabulary is
frequency-based with three reserved indices: 0 = PAD, 1 = UNK, 2 = NUM
(numeric token placeholder). Other special tokens could be added but are
not required by the paper's BiLSTM configuration.
"""
from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Iterable

import torch
from torch.utils.data import Dataset


logger = logging.getLogger(__name__)


PAD_TOKEN = "<pad>"
UNK_TOKEN = "<unk>"
NUM_TOKEN = "<num>"

PAD_IDX = 0
UNK_IDX = 1
NUM_IDX = 2


def _tokenize(text: str) -> list[str]:
    """Word-tokenize Vietnamese text. Falls back to whitespace split if
    underthesea is unavailable.
    """
    text = (text or "").strip()
    if not text:
        return []
    try:
        from underthesea import word_tokenize

        return word_tokenize(text, format="text").split()
    except Exception:
        return text.split()


def _normalize_token(token: str) -> str:
    """Map numeric-looking tokens to a single placeholder to keep vocab
    bounded. Pure-digits, comma-formatted, and dot-formatted numbers all
    collapse to ``<num>``.
    """
    stripped = token.replace(",", "").replace(".", "")
    if stripped.isdigit():
        return NUM_TOKEN
    return token


class Vocab:
    """Frequency-bounded vocabulary for BiLSTM.

    Reserves indices 0/1/2 for PAD/UNK/NUM and adds remaining tokens
    ordered by descending corpus frequency up to ``max_size``.
    """

    def __init__(self, max_size: int = 15_000) -> None:
        self.max_size = max_size
        self.itos: list[str] = [PAD_TOKEN, UNK_TOKEN, NUM_TOKEN]
        self.stoi: dict[str, int] = {t: i for i, t in enumerate(self.itos)}

    def __len__(self) -> int:
        return len(self.itos)

    def build(self, texts: Iterable[str]) -> "Vocab":
        counter: Counter[str] = Counter()
        for text in texts:
            for token in _tokenize(text):
                counter[_normalize_token(token)] += 1
        for token, _ in counter.most_common(self.max_size - len(self.itos)):
            if token in self.stoi:
                continue
            self.stoi[token] = len(self.itos)
            self.itos.append(token)
        logger.info("Built vocab: %d tokens (max_size=%d)", len(self.itos), self.max_size)
        return self

    def encode(self, text: str, max_len: int = 100) -> list[int]:
        ids: list[int] = []
        for token in _tokenize(text)[:max_len]:
            normalized = _normalize_token(token)
            ids.append(self.stoi.get(normalized, UNK_IDX))
        # Pad to max_len
        if len(ids) < max_len:
            ids = ids + [PAD_IDX] * (max_len - len(ids))
        return ids

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"max_size": self.max_size, "itos": self.itos}, ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> "Vocab":
        payload = json.loads(path.read_text(encoding="utf-8"))
        v = cls(max_size=payload["max_size"])
        v.itos = list(payload["itos"])
        v.stoi = {t: i for i, t in enumerate(v.itos)}
        return v


class BiLSTMDataset(Dataset):
    """Tokenize + numericalize + pad to ``max_len``. Stores as torch
    tensors for direct use with torch DataLoader.
    """

    def __init__(
        self,
        texts: list[str],
        labels: list[int] | None,
        vocab: Vocab,
        max_len: int = 100,
    ) -> None:
        self.texts = texts
        self.labels = labels
        self.vocab = vocab
        self.max_len = max_len
        self.encoded = [vocab.encode(t, max_len=max_len) for t in texts]

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> dict:
        item = {
            "input_ids": torch.tensor(self.encoded[idx], dtype=torch.long),
        }
        if self.labels is not None:
            item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


def load_split(path: Path) -> tuple[list[str], list[int]]:
    """Load (text, label) tuples from a CSV file produced by Phase 2."""
    import pandas as pd

    df = pd.read_csv(path, dtype={"comment_text": str, "label": int}).fillna("")
    df["label"] = pd.to_numeric(df["label"], errors="coerce").fillna(0).astype(int)
    texts = [str(t) for t in df["comment_text"].tolist()]
    labels = df["label"].tolist()
    return texts, labels