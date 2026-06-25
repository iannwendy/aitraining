"""Dùng PhoBERT đã train để gán nhãn phần comment còn lại."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from yt_depression_crawler.core.config import (
    AUTO_LABELED_FILE,
    PHOBERT_MAX_LENGTH,
    PHOBERT_OUTPUT_DIR,
    PHOBERT_PREDICTION_COLUMNS,
    PHOBERT_PREDICT_BATCH_SIZE,
    PHOBERT_PREDICT_CHUNK_SIZE,
    PHOBERT_REMAINING_PREDICTIONS_FILE,
)
from yt_depression_crawler.modeling.phobert.phobert_utils import ID_TO_LABEL, PhoBertDataset, get_device, prepare_many_texts

logger = logging.getLogger(__name__)


def predict_remaining_comments(
    input_file: Path = AUTO_LABELED_FILE,
    model_dir: Path = PHOBERT_OUTPUT_DIR,
    output_file: Path = PHOBERT_REMAINING_PREDICTIONS_FILE,
    resume: bool = True,
) -> dict:
    """Predict các dòng chưa chắc chắn hoặc không high-confidence."""
    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    if not model_dir.exists() or not (model_dir / "config.json").exists():
        raise FileNotFoundError(f"Missing trained PhoBERT model in {model_dir}")
    if not input_file.exists() or input_file.stat().st_size == 0:
        raise FileNotFoundError(f"Missing auto labeled file: {input_file}")

    df = pd.read_csv(input_file, dtype=str).fillna("")
    df = df[df["comment_text"].str.strip().ne("")].copy()
    remaining_df = df[(df["weak_label"] == "uncertain") | (df["confidence"] != "high")].copy()
    remaining_df = remaining_df.drop_duplicates(subset=["comment_text"], keep="first")

    already_predicted: set[str] = set()
    if resume and output_file.exists() and output_file.stat().st_size > 0:
        existing = pd.read_csv(output_file, dtype=str, usecols=["comment_text"]).fillna("")
        already_predicted = set(existing["comment_text"].astype(str).tolist())
        remaining_df = remaining_df[~remaining_df["comment_text"].isin(already_predicted)].copy()

    device = get_device()
    tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model.to(device)
    model.eval()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    write_header = not (resume and output_file.exists() and output_file.stat().st_size > 0)
    predicted_now = 0

    chunk_starts = range(0, len(remaining_df), PHOBERT_PREDICT_CHUNK_SIZE)
    for start in tqdm(chunk_starts, total=(len(remaining_df) + PHOBERT_PREDICT_CHUNK_SIZE - 1) // PHOBERT_PREDICT_CHUNK_SIZE, desc="PhoBERT chunks"):
        chunk_df = remaining_df.iloc[start : start + PHOBERT_PREDICT_CHUNK_SIZE].copy()
        texts = prepare_many_texts(chunk_df["comment_text"].tolist())
        dataset = PhoBertDataset(texts, None, tokenizer, PHOBERT_MAX_LENGTH)
        data_loader = DataLoader(dataset, batch_size=PHOBERT_PREDICT_BATCH_SIZE)

        probs_normal: list[float] = []
        probs_depression: list[float] = []
        labels: list[str] = []
        probabilities: list[float] = []

        with torch.no_grad():
            for batch in data_loader:
                batch = {key: value.to(device) for key, value in batch.items()}
                outputs = model(**batch)
                probs = torch.softmax(outputs.logits, dim=-1).detach().cpu()
                pred_ids = torch.argmax(probs, dim=-1).tolist()
                for index, pred_id in enumerate(pred_ids):
                    normal_prob = float(probs[index, 0].item())
                    depression_prob = float(probs[index, 1].item())
                    prob = depression_prob if pred_id == 1 else normal_prob
                    labels.append(ID_TO_LABEL[pred_id])
                    probabilities.append(round(prob, 4))
                    probs_normal.append(round(normal_prob, 4))
                    probs_depression.append(round(depression_prob, 4))

        output_df = pd.DataFrame(
            {
                "comment_text": chunk_df["comment_text"].tolist(),
                "source_weak_label": chunk_df.get("weak_label", "").tolist(),
                "source_confidence": chunk_df.get("confidence", "").tolist(),
                "source_depression_score": chunk_df.get("depression_score", "").tolist(),
                "phobert_label": labels,
                "probability": probabilities,
                "prob_normal": probs_normal,
                "prob_depression": probs_depression,
            }
        ).reindex(columns=PHOBERT_PREDICTION_COLUMNS)
        encoding = "utf-8-sig" if write_header else "utf-8"
        output_df.to_csv(output_file, mode="a", header=write_header, index=False, encoding=encoding)
        write_header = False
        predicted_now += len(output_df)

    final_output = pd.read_csv(output_file, dtype=str).fillna("") if output_file.exists() and output_file.stat().st_size > 0 else pd.DataFrame(columns=PHOBERT_PREDICTION_COLUMNS)

    report = {
        "input_rows": int(len(df)),
        "skipped_existing_rows": int(len(already_predicted)),
        "predicted_now": int(predicted_now),
        "predicted_rows": int(len(final_output)),
        "label_counts": final_output["phobert_label"].value_counts().to_dict() if "phobert_label" in final_output else {},
        "output_file": str(output_file),
    }
    logger.info("Da predict PhoBERT remaining: %s dong moi, tong %s dong -> %s", predicted_now, len(final_output), output_file)
    return report


def predict_texts(texts, model_dir, batch_size=None):
    """Predict labels for a list of arbitrary texts using a fine-tuned checkpoint.

    Thin adapter around :func:`predict_remaining_comments`. Synthesises a
    minimal ``AUTO_LABELED``-shaped DataFrame (every row marked as
    ``uncertain`` / not ``high`` confidence) so that
    ``predict_remaining_comments`` will score them, then re-parses the
    produced predictions CSV.

    Args:
        texts: list of raw comment strings.
        model_dir: path to the fine-tuned model directory.
        batch_size: optional override for ``PHOBERT_PREDICT_BATCH_SIZE`` in
            ``yt_depression_crawler.core.config``.

    Returns:
        list of dicts: [{"predicted_label": int, "predicted_label_name": str,
                          "probability": float, "prob_normal": float,
                          "prob_depression": float, "comment_text": str}, ...]
    """
    import os
    import tempfile
    from pathlib import Path

    from yt_depression_crawler.core import config

    if not texts:
        return []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_csv = tmpdir_path / "input.csv"
        output_csv = tmpdir_path / "predictions.csv"

        # Build a minimal AUTO_LABELED-shaped frame. Every row is tagged as
        # "uncertain" so the filter inside predict_remaining_comments keeps it.
        input_df = pd.DataFrame(
            {
                "comment_text": [str(t) for t in texts],
                "weak_label": "uncertain",
                "confidence": "low",
                "depression_score": 0.0,
                "matched_keywords": "",
                "need_review": True,
            }
        )
        input_df.to_csv(input_csv, index=False)

        old_output = getattr(config, "PHOBERT_REMAINING_PREDICTIONS_FILE", None)
        old_batch_size = getattr(config, "PHOBERT_PREDICT_BATCH_SIZE", None)
        config.PHOBERT_REMAINING_PREDICTIONS_FILE = output_csv
        if batch_size is not None:
            config.PHOBERT_PREDICT_BATCH_SIZE = batch_size
        try:
            predict_remaining_comments(
                input_file=input_csv,
                model_dir=Path(model_dir),
                output_file=output_csv,
                resume=False,
            )
        finally:
            config.PHOBERT_REMAINING_PREDICTIONS_FILE = old_output
            if batch_size is not None and old_batch_size is not None:
                config.PHOBERT_PREDICT_BATCH_SIZE = old_batch_size

        if not output_csv.exists() or output_csv.stat().st_size == 0:
            return [
                {
                    "comment_text": t,
                    "predicted_label": -1,
                    "predicted_label_name": "",
                    "probability": 0.0,
                    "prob_normal": 0.0,
                    "prob_depression": 0.0,
                }
                for t in texts
            ]

        preds_df = pd.read_csv(output_csv).fillna("")
        label_name_to_id = {name: idx for idx, name in ID_TO_LABEL.items()}
        results = []
        for _, row in preds_df.iterrows():
            label_name = str(row.get("phobert_label", ""))
            results.append(
                {
                    "comment_text": str(row.get("comment_text", "")),
                    "predicted_label": label_name_to_id.get(label_name, -1),
                    "predicted_label_name": label_name,
                    "probability": float(row.get("probability", 0.0) or 0.0),
                    "prob_normal": float(row.get("prob_normal", 0.0) or 0.0),
                    "prob_depression": float(row.get("prob_depression", 0.0) or 0.0),
                }
            )
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    print(json.dumps(predict_remaining_comments(), ensure_ascii=False, indent=2))
