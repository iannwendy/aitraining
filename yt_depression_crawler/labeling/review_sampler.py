"""Tạo tập mẫu để review thủ công từ weak labels."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from yt_depression_crawler.core.config import (
    AUTO_LABELED_FILE,
    LABELING_REPORT_FILE,
    REVIEW_SAMPLE_PER_BUCKET,
    REVIEW_SAMPLES_FILE,
    INITIAL_TRAIN_RANDOM_SEED,
)

logger = logging.getLogger(__name__)


REVIEW_COLUMNS = [
    "review_bucket",
    "comment_text",
    "weak_label",
    "confidence",
    "depression_score",
    "matched_keywords",
    "need_review",
    "suggested_label",
    "final_label",
    "reviewer_note",
]


def create_review_samples(
    input_file: Path = AUTO_LABELED_FILE,
    output_file: Path = REVIEW_SAMPLES_FILE,
    report_file: Path = LABELING_REPORT_FILE,
    sample_per_bucket: int = REVIEW_SAMPLE_PER_BUCKET,
    random_seed: int = INITIAL_TRAIN_RANDOM_SEED,
) -> dict:
    """Chọn mẫu đại diện để người review kiểm tra chất lượng weak label."""
    if not input_file.exists() or input_file.stat().st_size == 0:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=REVIEW_COLUMNS).to_csv(output_file, index=False, encoding="utf-8-sig")
        report = {"review_rows": 0, "reason": "missing_auto_labeled_file"}
        _merge_report(report_file, {"review_samples": report})
        return report

    df = pd.read_csv(input_file, dtype=str).fillna("")
    df["depression_score"] = pd.to_numeric(df["depression_score"], errors="coerce").fillna(0).astype(int)
    df["need_review_bool"] = df["need_review"].map(_to_bool)
    df = df.drop_duplicates(subset=["comment_text"], keep="first")

    buckets = [
        ("depression_high", df[(df["weak_label"] == "depression_auto") & (df["confidence"] == "high")]),
        ("normal_high", df[(df["weak_label"] == "normal_auto") & (df["confidence"] == "high")]),
        ("uncertain", df[df["weak_label"] == "uncertain"]),
        ("need_review", df[df["need_review_bool"]]),
        ("boundary", df[df["depression_score"].isin([-2, -1, 0, 1, 2, 3, 4, 5])]),
    ]

    samples: list[pd.DataFrame] = []
    bucket_counts: dict[str, int] = {}
    used_texts: set[str] = set()

    for index, (bucket_name, bucket_df) in enumerate(buckets):
        bucket_df = bucket_df[~bucket_df["comment_text"].isin(used_texts)]
        if bucket_df.empty:
            bucket_counts[bucket_name] = 0
            continue

        size = min(sample_per_bucket, len(bucket_df))
        sampled = bucket_df.sample(n=size, random_state=random_seed + index).copy()
        sampled["review_bucket"] = bucket_name
        sampled["suggested_label"] = sampled["weak_label"].map(_suggested_label)
        sampled["final_label"] = ""
        sampled["reviewer_note"] = ""
        used_texts.update(sampled["comment_text"].tolist())
        bucket_counts[bucket_name] = int(len(sampled))
        samples.append(sampled)

    if samples:
        output_df = pd.concat(samples, ignore_index=True)
    else:
        output_df = pd.DataFrame(columns=REVIEW_COLUMNS)

    output_df = output_df.reindex(columns=REVIEW_COLUMNS)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_file, index=False, encoding="utf-8-sig")

    report = {
        "review_rows": int(len(output_df)),
        "sample_per_bucket": sample_per_bucket,
        "bucket_counts": bucket_counts,
    }
    _merge_report(report_file, {"review_samples": report})
    logger.info("Da tao review samples: %s dong -> %s", len(output_df), output_file)
    return report


def _suggested_label(weak_label: str) -> str:
    if weak_label == "depression_auto":
        return "depression"
    if weak_label == "normal_auto":
        return "normal"
    return ""


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
    print(json.dumps(create_review_samples(), ensure_ascii=False, indent=2))
