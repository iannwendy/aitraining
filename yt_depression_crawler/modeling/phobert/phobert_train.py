"""Train PhoBERT lần 1 trên weak-labeled high-confidence dataset."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from yt_depression_crawler.core.config import (
    GOLD_REVIEW_FILE,
    LABELING_REPORT_FILE,
    PHOBERT_BATCH_SIZE,
    PHOBERT_EARLY_STOPPING_PATIENCE,
    PHOBERT_EPOCHS,
    PHOBERT_EVAL_BATCH_SIZE,
    PHOBERT_GOLD_METRICS_FILE,
    PHOBERT_GRAD_CLIP_NORM,
    PHOBERT_LEARNING_RATE,
    PHOBERT_MAX_LENGTH,
    PHOBERT_METRICS_FILE,
    PHOBERT_MODEL_NAME,
    PHOBERT_OUTPUT_DIR,
    PHOBERT_RANDOM_SEED,
    PHOBERT_WARMUP_RATIO,
    PHOBERT_WEIGHT_DECAY,
    TEST_FILE,
    TRAIN_FILE,
    VAL_FILE,
    ensure_directories,
)
from yt_depression_crawler.modeling.phobert.phobert_utils import (
    PhoBertDataset,
    compute_class_weights,
    compute_metrics,
    get_device,
    load_labeled_split,
    prepare_many_texts,
    set_seed,
)

logger = logging.getLogger(__name__)


def train_phobert_first(
    train_file: Path = TRAIN_FILE,
    val_file: Path = VAL_FILE,
    test_file: Path = TEST_FILE,
    output_dir: Path = PHOBERT_OUTPUT_DIR,
    metrics_file: Path = PHOBERT_METRICS_FILE,
) -> dict:
    """Train PhoBERT và lưu best checkpoint theo validation macro F1."""
    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

    ensure_directories()
    set_seed(PHOBERT_RANDOM_SEED)
    device = get_device()
    logger.info("Train PhoBERT device=%s model=%s", device, PHOBERT_MODEL_NAME)

    train_df = load_labeled_split(train_file)
    val_df = load_labeled_split(val_file)
    test_df = load_labeled_split(test_file)

    tokenizer = AutoTokenizer.from_pretrained(PHOBERT_MODEL_NAME, use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(PHOBERT_MODEL_NAME, num_labels=2)
    model.to(device)

    train_texts = prepare_many_texts(train_df["comment_text"].tolist())
    val_texts = prepare_many_texts(val_df["comment_text"].tolist())
    test_texts = prepare_many_texts(test_df["comment_text"].tolist())

    train_dataset = PhoBertDataset(train_texts, train_df["label"].astype(int).tolist(), tokenizer, PHOBERT_MAX_LENGTH)
    val_dataset = PhoBertDataset(val_texts, val_df["label"].astype(int).tolist(), tokenizer, PHOBERT_MAX_LENGTH)
    test_dataset = PhoBertDataset(test_texts, test_df["label"].astype(int).tolist(), tokenizer, PHOBERT_MAX_LENGTH)

    train_loader = DataLoader(train_dataset, batch_size=PHOBERT_BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=PHOBERT_EVAL_BATCH_SIZE)
    test_loader = DataLoader(test_dataset, batch_size=PHOBERT_EVAL_BATCH_SIZE)

    optimizer = torch.optim.AdamW(model.parameters(), lr=PHOBERT_LEARNING_RATE, weight_decay=PHOBERT_WEIGHT_DECAY)
    total_steps = max(len(train_loader) * PHOBERT_EPOCHS, 1)
    warmup_steps = math.floor(total_steps * PHOBERT_WARMUP_RATIO)
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps)
    class_weights = compute_class_weights(train_df["label"].astype(int).tolist()).to(device)
    loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights)

    best_val_f1 = -1.0
    best_epoch = 0
    patience_left = PHOBERT_EARLY_STOPPING_PATIENCE
    history: list[dict] = []

    output_dir.mkdir(parents=True, exist_ok=True)
    for epoch in range(1, PHOBERT_EPOCHS + 1):
        train_loss = _train_one_epoch(model, train_loader, optimizer, scheduler, loss_fn, device, epoch)
        val_metrics = evaluate_model(model, val_loader, device)
        epoch_record = {"epoch": epoch, "train_loss": round(train_loss, 4), "validation": val_metrics}
        history.append(epoch_record)
        logger.info("PhoBERT epoch=%s train_loss=%s val_f1=%s", epoch, epoch_record["train_loss"], val_metrics["f1_macro"])

        if val_metrics["f1_macro"] > best_val_f1:
            best_val_f1 = val_metrics["f1_macro"]
            best_epoch = epoch
            patience_left = PHOBERT_EARLY_STOPPING_PATIENCE
            model.save_pretrained(output_dir)
            tokenizer.save_pretrained(output_dir)
        else:
            patience_left -= 1
            if patience_left <= 0:
                logger.info("Early stopping PhoBERT tai epoch %s", epoch)
                break

    best_model = AutoModelForSequenceClassification.from_pretrained(output_dir)
    best_model.to(device)
    test_metrics = evaluate_model(best_model, test_loader, device)
    gold_metrics = evaluate_gold_if_available(best_model, tokenizer, device)

    report = {
        "model_name": PHOBERT_MODEL_NAME,
        "output_dir": str(output_dir),
        "device": str(device),
        "train_rows": int(len(train_df)),
        "val_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "best_epoch": best_epoch,
        "best_val_f1_macro": best_val_f1,
        "history": history,
        "test": test_metrics,
        "gold": gold_metrics,
        "settings": {
            "max_length": PHOBERT_MAX_LENGTH,
            "batch_size": PHOBERT_BATCH_SIZE,
            "eval_batch_size": PHOBERT_EVAL_BATCH_SIZE,
            "epochs": PHOBERT_EPOCHS,
            "learning_rate": PHOBERT_LEARNING_RATE,
            "weight_decay": PHOBERT_WEIGHT_DECAY,
        },
    }
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    metrics_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _merge_labeling_report({"phobert_first": report})
    logger.info("Da train PhoBERT -> %s", output_dir)
    return report


def _train_one_epoch(model, data_loader, optimizer, scheduler, loss_fn, device, epoch: int) -> float:
    import torch

    model.train()
    losses: list[float] = []
    progress = tqdm(data_loader, desc=f"PhoBERT train epoch {epoch}", leave=False)
    for batch in progress:
        labels = batch.pop("labels").to(device)
        batch = {key: value.to(device) for key, value in batch.items()}
        optimizer.zero_grad(set_to_none=True)
        outputs = model(**batch)
        loss = loss_fn(outputs.logits, labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), PHOBERT_GRAD_CLIP_NORM)
        optimizer.step()
        scheduler.step()
        loss_value = float(loss.detach().cpu().item())
        losses.append(loss_value)
        progress.set_postfix(loss=round(loss_value, 4))
    return sum(losses) / max(len(losses), 1)


def evaluate_model(model, data_loader, device) -> dict:
    import torch

    model.eval()
    preds: list[int] = []
    labels_all: list[int] = []
    with torch.no_grad():
        for batch in data_loader:
            labels = batch.pop("labels").to(device)
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(**batch)
            batch_preds = torch.argmax(outputs.logits, dim=-1)
            preds.extend(batch_preds.detach().cpu().tolist())
            labels_all.extend(labels.detach().cpu().tolist())
    return compute_metrics(labels_all, preds)


def evaluate_gold_if_available(model, tokenizer, device) -> dict | None:
    import torch
    from torch.utils.data import DataLoader

    if not GOLD_REVIEW_FILE.exists() or GOLD_REVIEW_FILE.stat().st_size == 0:
        return None
    gold_df = pd.read_csv(GOLD_REVIEW_FILE, dtype={"comment_text": str}).fillna("")
    if gold_df.empty or "label" not in gold_df.columns:
        return None
    gold_df["label"] = pd.to_numeric(gold_df["label"], errors="coerce").astype(int)
    gold_texts = prepare_many_texts(gold_df["comment_text"].tolist())
    gold_dataset = PhoBertDataset(gold_texts, gold_df["label"].astype(int).tolist(), tokenizer, PHOBERT_MAX_LENGTH)
    gold_loader = DataLoader(gold_dataset, batch_size=PHOBERT_EVAL_BATCH_SIZE)
    metrics = evaluate_model(model, gold_loader, device)
    PHOBERT_GOLD_METRICS_FILE.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return metrics


def _merge_labeling_report(payload: dict) -> None:
    existing: dict = {}
    if LABELING_REPORT_FILE.exists() and LABELING_REPORT_FILE.stat().st_size > 0:
        try:
            existing = json.loads(LABELING_REPORT_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    existing.update(payload)
    LABELING_REPORT_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    print(json.dumps(train_phobert_first(), ensure_ascii=False, indent=2))
