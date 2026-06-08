"""Hậu xử lý dự đoán PhoBERT.

Tạo 2 file chính:
- phobert_confident_predictions.csv: pseudo-label confidence cao để huấn luyện tiếp
- phobert_active_learning_samples.csv: mẫu khó để review thủ công
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from yt_depression_crawler.core.config import (
    PHOBERT_ACTIVE_LEARNING_FILE,
    PHOBERT_ACTIVE_LEARNING_MAX_SAMPLES,
    PHOBERT_ACTIVE_LEARNING_PROB_THRESHOLD,
    PHOBERT_CONFIDENT_PREDICTIONS_FILE,
    PHOBERT_POSTPROCESS_REPORT_FILE,
    PHOBERT_PSEUDO_LABEL_PROB_THRESHOLD,
    PHOBERT_REMAINING_PREDICTIONS_FILE,
    INITIAL_TRAIN_RANDOM_SEED,
)

logger = logging.getLogger(__name__)

ACTIVE_COLUMNS = [
    "review_bucket",
    "comment_text",
    "source_weak_label",
    "source_confidence",
    "source_depression_score",
    "phobert_label",
    "probability",
    "prob_normal",
    "prob_depression",
    "need_review",
    "suggested_label",
    "final_label",
    "reviewer_note",
]

CONFIDENT_COLUMNS = [
    "comment_text",
    "label",
    "probability",
    "source_weak_label",
    "source_confidence",
    "source_depression_score",
    "phobert_label",
    "prob_normal",
    "prob_depression",
]


def build_phobert_followup_files(
    predictions_file: Path = PHOBERT_REMAINING_PREDICTIONS_FILE,
    confident_output: Path = PHOBERT_CONFIDENT_PREDICTIONS_FILE,
    active_learning_output: Path = PHOBERT_ACTIVE_LEARNING_FILE,
) -> dict:
    """Tách dự đoán PhoBERT thành pseudo-label confidence cao và mẫu khó cần review."""

    if not predictions_file.exists() or predictions_file.stat().st_size == 0:
        confident_output.parent.mkdir(parents=True, exist_ok=True)
        active_learning_output.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=CONFIDENT_COLUMNS).to_csv(confident_output, index=False, encoding="utf-8-sig")
        pd.DataFrame(columns=ACTIVE_COLUMNS).to_csv(active_learning_output, index=False, encoding="utf-8-sig")
        report = {"reason": "missing_predictions_file", "confident_rows": 0, "active_rows": 0}
        _write_report(report)
        return report

    df = pd.read_csv(predictions_file, dtype=str).fillna("")
    if df.empty:
        confident_output.parent.mkdir(parents=True, exist_ok=True)
        active_learning_output.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=CONFIDENT_COLUMNS).to_csv(confident_output, index=False, encoding="utf-8-sig")
        pd.DataFrame(columns=ACTIVE_COLUMNS).to_csv(active_learning_output, index=False, encoding="utf-8-sig")
        report = {"reason": "empty_predictions_file", "confident_rows": 0, "active_rows": 0}
        _write_report(report)
        return report

    df["probability"] = pd.to_numeric(df["probability"], errors="coerce").fillna(0.0)
    df["prob_normal"] = pd.to_numeric(df["prob_normal"], errors="coerce").fillna(0.0)
    df["prob_depression"] = pd.to_numeric(df["prob_depression"], errors="coerce").fillna(0.0)
    df["source_depression_score"] = pd.to_numeric(df["source_depression_score"], errors="coerce").fillna(0).astype(int)

    confident_df = df[df["probability"] >= PHOBERT_PSEUDO_LABEL_PROB_THRESHOLD].copy()
    confident_df["label"] = confident_df["phobert_label"]
    confident_df = confident_df.reindex(columns=CONFIDENT_COLUMNS)
    confident_df = confident_df.drop_duplicates(subset=["comment_text"], keep="first")

    active_candidates = _build_active_learning_df(df)
    active_df = _sample_active_learning(active_candidates, PHOBERT_ACTIVE_LEARNING_MAX_SAMPLES)
    active_df = active_df.reindex(columns=ACTIVE_COLUMNS)

    confident_output.parent.mkdir(parents=True, exist_ok=True)
    active_learning_output.parent.mkdir(parents=True, exist_ok=True)
    confident_df.to_csv(confident_output, index=False, encoding="utf-8-sig")
    active_df.to_csv(active_learning_output, index=False, encoding="utf-8-sig")

    report = {
        "input_rows": int(len(df)),
        "confident_threshold": PHOBERT_PSEUDO_LABEL_PROB_THRESHOLD,
        "active_learning_threshold": PHOBERT_ACTIVE_LEARNING_PROB_THRESHOLD,
        "confident_rows": int(len(confident_df)),
        "active_rows": int(len(active_df)),
        "confident_label_counts": confident_df["label"].value_counts().to_dict() if not confident_df.empty else {},
        "active_bucket_counts": active_df["review_bucket"].value_counts().to_dict() if not active_df.empty else {},
        "confident_output": str(confident_output),
        "active_learning_output": str(active_learning_output),
    }
    _write_report(report)
    logger.info("Da tao pseudo-label confident: %s dong, active learning: %s dong", len(confident_df), len(active_df))
    return report


def _build_active_learning_df(df: pd.DataFrame) -> pd.DataFrame:
    source_label = df["source_weak_label"].fillna("")
    weak_normal = source_label.eq("normal_auto")
    weak_depression = source_label.eq("depression_auto")
    uncertain = source_label.eq("uncertain")

    disagreement = df[
        ((weak_normal) & (df["phobert_label"] == "depression"))
        | ((weak_depression) & (df["phobert_label"] == "normal"))
    ].copy()
    disagreement["review_bucket"] = "weak_model_disagreement"

    boundary = df[(df["probability"] >= 0.45) & (df["probability"] <= 0.55)].copy()
    boundary["review_bucket"] = "boundary_probability"

    low_confidence = df[df["probability"] < PHOBERT_ACTIVE_LEARNING_PROB_THRESHOLD].copy()
    low_confidence["review_bucket"] = "low_confidence"

    uncertain_pred = df[uncertain].copy()
    uncertain_pred["review_bucket"] = "source_uncertain"

    combined = pd.concat([disagreement, boundary, low_confidence, uncertain_pred], ignore_index=True)
    if combined.empty:
        return pd.DataFrame(columns=ACTIVE_COLUMNS)

    combined = combined.drop_duplicates(subset=["comment_text"], keep="first")
    combined["need_review"] = True
    combined["suggested_label"] = combined["phobert_label"]
    combined["final_label"] = ""
    combined["reviewer_note"] = ""
    return combined


def _sample_active_learning(df: pd.DataFrame, max_samples: int) -> pd.DataFrame:
    if df.empty or len(df) <= max_samples:
        return df.copy()

    bucket_names = list(df["review_bucket"].dropna().unique())
    per_bucket = max(1, max_samples // max(len(bucket_names), 1))
    selected_parts: list[pd.DataFrame] = []
    used_texts: set[str] = set()

    for index, bucket in enumerate(bucket_names):
        bucket_df = df[df["review_bucket"] == bucket].copy()
        bucket_df = bucket_df[~bucket_df["comment_text"].isin(used_texts)]
        if bucket_df.empty:
            continue
        bucket_df = bucket_df.sort_values("probability", ascending=True)
        take = min(per_bucket, len(bucket_df))
        sampled = bucket_df.head(take)
        if len(bucket_df) > take:
            # Giữ phần khó nhất trước, thêm một chút ngẫu nhiên để tránh review quá một màu.
            random_take = min(max(0, per_bucket - len(sampled)), len(bucket_df) - len(sampled))
            if random_take:
                sampled = pd.concat(
                    [
                        sampled,
                        bucket_df.iloc[take:].sample(n=random_take, random_state=INITIAL_TRAIN_RANDOM_SEED + index),
                    ],
                    ignore_index=True,
                )
        selected_parts.append(sampled)
        used_texts.update(sampled["comment_text"].tolist())

    selected = pd.concat(selected_parts, ignore_index=True) if selected_parts else pd.DataFrame(columns=df.columns)
    if len(selected) < max_samples:
        rest = df[~df["comment_text"].isin(set(selected["comment_text"].tolist()))].copy()
        rest = rest.sort_values("probability", ascending=True)
        selected = pd.concat([selected, rest.head(max_samples - len(selected))], ignore_index=True)

    return selected.head(max_samples).copy()


def _write_report(payload: dict) -> None:
    PHOBERT_POSTPROCESS_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    PHOBERT_POSTPROCESS_REPORT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    print(json.dumps(build_phobert_followup_files(), ensure_ascii=False, indent=2))
