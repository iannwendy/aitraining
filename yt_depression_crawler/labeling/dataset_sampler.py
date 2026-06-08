"""Tạo tập initial_train.csv từ weak labels tự tin cao."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from yt_depression_crawler.processing.cleaner import normalize_text
from yt_depression_crawler.core.config import (
    AUTO_LABELED_FILE,
    INITIAL_TRAIN_COLUMNS,
    INITIAL_TRAIN_DEPRESSION_SAMPLES,
    INITIAL_TRAIN_FILE,
    INITIAL_TRAIN_MAX_CHARS,
    INITIAL_TRAIN_MIN_CHARS,
    INITIAL_TRAIN_NORMAL_SAMPLES,
    INITIAL_TRAIN_RANDOM_SEED,
    LABELING_REPORT_FILE,
)

logger = logging.getLogger(__name__)


def build_initial_train_dataset(
    input_file: Path = AUTO_LABELED_FILE,
    output_file: Path = INITIAL_TRAIN_FILE,
    report_file: Path = LABELING_REPORT_FILE,
    depression_samples: int = INITIAL_TRAIN_DEPRESSION_SAMPLES,
    normal_samples: int = INITIAL_TRAIN_NORMAL_SAMPLES,
    random_seed: int = INITIAL_TRAIN_RANDOM_SEED,
) -> dict:
    """Chọn mẫu high-confidence, need_review=False để train mô hình đầu tiên."""
    if not input_file.exists() or input_file.stat().st_size == 0:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=INITIAL_TRAIN_COLUMNS).to_csv(output_file, index=False, encoding="utf-8-sig")
        report = {"initial_train_rows": 0, "reason": "missing_auto_labeled_file"}
        _merge_report(report_file, {"initial_train": report})
        return report

    df = pd.read_csv(input_file, dtype=str).fillna("")
    for column in INITIAL_TRAIN_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df["comment_text"] = df["comment_text"].map(normalize_text)
    df["text_len"] = df["comment_text"].str.len()
    df["depression_score"] = pd.to_numeric(df["depression_score"], errors="coerce").fillna(0).astype(int)
    df["need_review_bool"] = df["need_review"].map(_to_bool)
    df = df.drop_duplicates(subset=["comment_text"], keep="first")
    df = df[(df["text_len"] >= INITIAL_TRAIN_MIN_CHARS) & (df["text_len"] <= INITIAL_TRAIN_MAX_CHARS)]

    depression_pool = df[
        (df["weak_label"] == "depression_auto")
        & (df["confidence"] == "high")
        & (~df["need_review_bool"])
    ].sort_values("depression_score", ascending=False)
    normal_pool = df[
        (df["weak_label"] == "normal_auto")
        & (df["confidence"] == "high")
        & (~df["need_review_bool"])
    ].sort_values("depression_score", ascending=True)

    selected_depression = depression_pool.head(depression_samples)
    selected_normal = normal_pool.head(normal_samples)
    train_df = pd.concat([selected_depression, selected_normal], ignore_index=True)
    if not train_df.empty:
        train_df = train_df.sample(frac=1, random_state=random_seed).reset_index(drop=True)
    train_df = train_df.reindex(columns=INITIAL_TRAIN_COLUMNS)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(output_file, index=False, encoding="utf-8-sig")

    report = {
        "initial_train_rows": int(len(train_df)),
        "requested_depression": depression_samples,
        "requested_normal": normal_samples,
        "selected_depression": int(len(selected_depression)),
        "selected_normal": int(len(selected_normal)),
        "available_high_confidence_depression": int(len(depression_pool)),
        "available_high_confidence_normal": int(len(normal_pool)),
        "min_chars": INITIAL_TRAIN_MIN_CHARS,
        "max_chars": INITIAL_TRAIN_MAX_CHARS,
        "random_seed": random_seed,
    }
    _merge_report(report_file, {"initial_train": report})
    logger.info("Da tao initial train: %s dong -> %s", len(train_df), output_file)
    return report


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _merge_report(report_file: Path, payload: dict) -> None:
    report_file.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if report_file.exists() and report_file.stat().st_size > 0:
        try:
            existing = json.loads(report_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    existing.update(payload)
    report_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    summary = build_initial_train_dataset()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
