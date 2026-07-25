"""BiLSTM model definitions + training entry point.

Paper Section 4.2 specifies:
- Learned embedding: 128 dimensions, vocab size 15,000
- Two stacked LSTM layers: hidden dim 128, dropout 0.5
- Classifier head: 256 -> 64 -> 2 with ReLU + dropout
- Adam optimizer, lr=1e-3, batch_size=32, 8 epochs
- Max sequence length: 100 tokens
- Cross-entropy loss WITHOUT class weighting (Appendix B Table)

We implement two variants:
- BiLSTMRandom: nn.Embedding(15K, 128) with random init
- BiLSTMPhoBERT: PhoBERT word embeddings frozen + same LSTM stack
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from yt_depression_crawler.core.config import PHOBERT_DEVICE
from yt_depression_crawler.modeling.bilstm.bilstm_dataset import (
    PAD_IDX,
    UNK_IDX,
    Vocab,
    load_split,
)

logger = logging.getLogger(__name__)


@dataclass
class BiLSTMConfig:
    vocab_size: int = 15_000
    embed_dim: int = 128
    hidden_dim: int = 128
    num_layers: int = 2
    dropout: float = 0.5
    num_classes: int = 2
    classifier_hidden: int = 64


class BiLSTMRandom(nn.Module):
    """Random-init embedding + 2-layer BiLSTM + classifier (paper spec)."""

    def __init__(self, cfg: BiLSTMConfig) -> None:
        super().__init__()
        self.embedding = nn.Embedding(cfg.vocab_size, cfg.embed_dim, padding_idx=PAD_IDX)
        self.lstm = nn.LSTM(
            cfg.embed_dim,
            cfg.hidden_dim,
            num_layers=cfg.num_layers,
            dropout=cfg.dropout if cfg.num_layers > 1 else 0.0,
            bidirectional=True,
            batch_first=True,
        )
        lstm_out_dim = cfg.hidden_dim * 2  # bidirectional
        self.classifier = nn.Sequential(
            nn.Linear(lstm_out_dim, lstm_out_dim),
            nn.ReLU(),
            nn.Dropout(cfg.dropout),
            nn.Linear(lstm_out_dim, cfg.classifier_hidden),
            nn.ReLU(),
            nn.Dropout(cfg.dropout),
            nn.Linear(cfg.classifier_hidden, cfg.num_classes),
        )

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        # input_ids: [B, T]
        embeds = self.embedding(input_ids)  # [B, T, E]
        lstm_out, _ = self.lstm(embeds)  # [B, T, 2H]
        # Use last non-pad position's hidden state
        mask = (input_ids != PAD_IDX).unsqueeze(-1).float()
        lstm_out = lstm_out * mask
        seq_lens = mask.sum(dim=1).clamp(min=1.0)  # [B, 1]
        pooled = lstm_out.sum(dim=1) / seq_lens
        return self.classifier(pooled)


class BiLSTMPhoBERT(nn.Module):
    """PhoBERT word embeddings frozen + same BiLSTM stack.

    Loads ``vinai/phobert-base`` (or local copy), extracts its word
    embedding matrix (768-dim), freezes it, and uses a linear projection
    down to ``hidden_dim`` before the BiLSTM. Falls back to random init
    for tokens not in PhoBERT's vocab (using UNK_IDX mapping).
    """

    PHOBERT_NAME = "vinai/phobert-base"
    PHOBERT_EMBED_DIM = 768

    def __init__(self, cfg: BiLSTMConfig, local_model_dir: str | None = None) -> None:
        super().__init__()
        # Use PhoBERT's native embed dim for the embedding layer so we
        # can copy weights verbatim; project down to ``hidden_dim`` so
        # the LSTM + classifier shapes match the random-init variant.
        self.embed_dim = self.PHOBERT_EMBED_DIM
        self.embedding = nn.Embedding(cfg.vocab_size, self.embed_dim, padding_idx=PAD_IDX)
        self._load_phobert_weights(local_model_dir or self.PHOBERT_NAME)
        # Freeze — gradients should not flow into the pretrained embeddings
        self.embedding.weight.requires_grad = False

        # Project 768 -> hidden_dim before BiLSTM
        self.input_proj = nn.Linear(self.embed_dim, cfg.hidden_dim)

        self.lstm = nn.LSTM(
            cfg.hidden_dim,
            cfg.hidden_dim,
            num_layers=cfg.num_layers,
            dropout=cfg.dropout if cfg.num_layers > 1 else 0.0,
            bidirectional=True,
            batch_first=True,
        )
        lstm_out_dim = cfg.hidden_dim * 2
        self.classifier = nn.Sequential(
            nn.Linear(lstm_out_dim, lstm_out_dim),
            nn.ReLU(),
            nn.Dropout(cfg.dropout),
            nn.Linear(lstm_out_dim, cfg.classifier_hidden),
            nn.ReLU(),
            nn.Dropout(cfg.dropout),
            nn.Linear(cfg.classifier_hidden, cfg.num_classes),
        )

    def _load_phobert_weights(self, model_name_or_path: str) -> None:
        """Copy PhoBERT word embeddings into ``self.embedding``.

        Vocab mapping: BiLSTM vocab has up to 15K surface tokens; PhoBERT
        has ~64K BPE sub-tokens. We align by exact-string lookup. Tokens
        that don't appear in PhoBERT's vocab keep their random init — this
        is acceptable since BiLSTM is trained end-to-end and the encoder
        is frozen but the LSTM + classifier can adapt.
        """
        from transformers import AutoModel

        # Suppress noisy download messages; load offline if possible.
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        try:
            phobert = AutoModel.from_pretrained(model_name_or_path)
        except Exception as exc:
            logger.warning(
                "Could not load PhoBERT from %s (%s). Falling back to "
                "random init for all embedding rows.",
                model_name_or_path, exc,
            )
            return

        phobert_emb = phobert.embeddings.word_embeddings.weight.detach()
        # Build surface-token → phobert-id lookup using AutoTokenizer
        from transformers import AutoTokenizer

        tok = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=False)
        phobert_stoi = tok.get_vocab()

        vocab = self.embedding.weight.data
        matched = 0
        for tok_idx, token in enumerate(self._bi_vocab_tokens()):
            if token in phobert_stoi:
                src = phobert_emb[phobert_stoi[token]]
                vocab[tok_idx] = src
                matched += 1
        logger.info(
            "Initialized %d/%d BiLSTM vocab rows from PhoBERT embeddings",
            matched, len(self._bi_vocab_tokens()),
        )

    def _bi_vocab_tokens(self) -> list[str]:
        """Read the BiLSTM vocab saved to disk by ``Vocab.save``.

        Required because the BiLSTM vocab is built from a frequency pass
        over the training corpus and is NOT shared with the model class
        (which only knows the embedding layer shape). We persist the
        vocab next to the model checkpoint so this method can reload it.
        """
        # The ``tokens`` attribute is set by ``set_vocab`` before training.
        # If unset, return empty (all-PAD/UNK/NUM random init).
        return getattr(self, "_vocab_tokens", [])

    def set_vocab(self, tokens: list[str]) -> None:
        """Attach BiLSTM vocab to the model so _load_phobert_weights can
        iterate it. Called by train_bilstm() before instantiation.
        """
        self._vocab_tokens = tokens

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        embeds = self.embedding(input_ids)
        embeds = self.input_proj(embeds)
        lstm_out, _ = self.lstm(embeds)
        mask = (input_ids != PAD_IDX).unsqueeze(-1).float()
        lstm_out = lstm_out * mask
        seq_lens = mask.sum(dim=1).clamp(min=1.0)
        pooled = lstm_out.sum(dim=1) / seq_lens
        return self.classifier(pooled)


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


def _evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> dict:
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
    )

    model.eval()
    preds, labels_all = [], []
    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)
            logits = model(input_ids)
            batch_preds = torch.argmax(logits, dim=-1)
            preds.extend(batch_preds.detach().cpu().tolist())
            labels_all.extend(labels.detach().cpu().tolist())

    return {
        "accuracy": round(float(accuracy_score(labels_all, preds)), 4),
        "precision_macro": round(float(precision_score(labels_all, preds, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(labels_all, preds, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(labels_all, preds, average="macro", zero_division=0)), 4),
        "f1_depression": round(float(f1_score(labels_all, preds, pos_label=1, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(labels_all, preds, labels=[0, 1]).tolist(),
        "classification_report": classification_report(
            labels_all, preds, labels=[0, 1],
            target_names=["normal", "depression"],
            output_dict=True, zero_division=0,
        ),
    }


def train_bilstm(
    variant: str = "random",  # "random" or "phobert"
    train_file: Path = None,
    val_file: Path = None,
    test_file: Path = None,
    output_dir: Path = None,
    epochs: int = 8,
    batch_size: int = 32,
    lr: float = 1e-3,
    max_len: int = 100,
    vocab_size: int = 15_000,
    phobert_local_dir: str | None = None,
    seed: int = 42,
) -> dict:
    """Train BiLSTM and evaluate on val + test.

    Returns a dict with metrics for each split, matching the schema of
    other models in the project so it can be aggregated into Table 5.1.
    """
    import tempfile

    if variant not in {"random", "phobert"}:
        raise ValueError(f"variant must be 'random' or 'phobert', got {variant!r}")

    output_dir.mkdir(parents=True, exist_ok=True)
    device = _get_device()
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    import random
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    logger.info("Train BiLSTM-%s on device=%s seed=%d", variant, device, seed)

    train_texts, train_labels = load_split(train_file)
    val_texts, val_labels = load_split(val_file)
    test_texts, test_labels = load_split(test_file)

    vocab = Vocab(max_size=vocab_size).build(train_texts)
    vocab.save(output_dir / "vocab.json")

    from yt_depression_crawler.modeling.bilstm.bilstm_dataset import BiLSTMDataset

    train_ds = BiLSTMDataset(train_texts, train_labels, vocab, max_len=max_len)
    val_ds = BiLSTMDataset(val_texts, val_labels, vocab, max_len=max_len)
    test_ds = BiLSTMDataset(test_texts, test_labels, vocab, max_len=max_len)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)
    test_loader = DataLoader(test_ds, batch_size=batch_size)

    cfg = BiLSTMConfig(vocab_size=len(vocab), embed_dim=128, hidden_dim=128, num_layers=2, dropout=0.5)
    if variant == "random":
        model = BiLSTMRandom(cfg)
    else:
        model = BiLSTMPhoBERT(cfg, local_model_dir=phobert_local_dir)
        model.set_vocab(vocab.itos)
        # Reload embeddings now that vocab is attached
        model._load_phobert_weights(phobert_local_dir or BiLSTMPhoBERT.PHOBERT_NAME)

    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()  # NO class weighting per Appendix B Table

    history: list[dict] = []
    best_val_f1 = -1.0
    best_state: dict | None = None
    best_epoch = 0

    for epoch in range(1, epochs + 1):
        model.train()
        losses: list[float] = []
        for batch in tqdm(train_loader, desc=f"BiLSTM epoch {epoch}", leave=False):
            input_ids = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(input_ids)
            loss = loss_fn(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(float(loss.detach().cpu().item()))

        val_metrics = _evaluate(model, val_loader, device)
        history.append({"epoch": epoch, "train_loss": round(sum(losses) / max(len(losses), 1), 4),
                       "validation": val_metrics})
        logger.info("BiLSTM epoch=%d train_loss=%.4f val_f1=%.4f",
                    epoch, history[-1]["train_loss"], val_metrics["f1_macro"])
        if val_metrics["f1_macro"] > best_val_f1:
            best_val_f1 = val_metrics["f1_macro"]
            best_epoch = epoch
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    test_metrics = _evaluate(model, test_loader, device)
    torch.save({"state_dict": model.state_dict(), "config": cfg.__dict__,
                "variant": variant, "vocab_size": len(vocab)},
               output_dir / "model.pt")
    vocab.save(output_dir / "vocab.json")  # ensure persistence after retrain

    # Cross-domain eval (VSMEC) — same loader works because dataset is text-only
    from yt_depression_crawler.modeling.bilstm.bilstm_dataset import load_split as _load
    from pandas import read_csv
    vsmec_df = read_csv(Path("data_unified/cross_domain_test.csv"))
    vsmec_texts = [str(t) for t in vsmec_df["comment_text"].tolist()]
    vsmec_labels = vsmec_df["label"].astype(int).tolist()
    vsmec_ds = BiLSTMDataset(vsmec_texts, vsmec_labels, vocab, max_len=max_len)
    vsmec_loader = DataLoader(vsmec_ds, batch_size=batch_size)
    vsmec_metrics = _evaluate(model, vsmec_loader, device)

    metrics = {
        "variant": variant,
        "seed": seed,
        "train_rows": int(len(train_texts)),
        "val_rows": int(len(val_texts)),
        "test_rows": int(len(test_texts)),
        "best_epoch": best_epoch,
        "best_val_f1_macro": best_val_f1,
        "history": history,
        "validation": test_metrics if False else _evaluate(model, val_loader, device),
        "test": test_metrics,
        "cross_domain_vsmec": vsmec_metrics,
        "settings": {
            "epochs": epochs,
            "batch_size": batch_size,
            "lr": lr,
            "max_len": max_len,
            "vocab_size": len(vocab),
            "embed_dim": 128,
            "hidden_dim": 128,
            "num_layers": 2,
            "dropout": 0.5,
            "seed": seed,
        },
    }

    metrics_path = output_dir / "bilstm_metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Da train BiLSTM-%s -> %s", variant, output_dir)
    return metrics