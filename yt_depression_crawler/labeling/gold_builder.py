"""Tạo gold_review.csv từ review_samples.csv đã có final_label."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from yt_depression_crawler.processing.cleaner import normalize_text
from yt_depression_crawler.core.config import GOLD_REVIEW_FILE, LABELING_REPORT_FILE, REVIEW_SAMPLES_FILE

logger = logging.getLogger(__name__)

GOLD_COLUMNS = [
    "comment_text",
    "label",
    "final_label",
    "weak_label",
    "confidence",
    "depression_score",
    "matched_keywords",
    "review_bucket",
    "reviewer_note",
]

VALID_FINAL_LABELS = {"normal": 0, "depression": 1}


def build_gold_review_set(
    input_file: Path = REVIEW_SAMPLES_FILE,
    output_file: Path = GOLD_REVIEW_FILE,
    report_file: Path = LABELING_REPORT_FILE,
) -> dict:
    """Lọc các dòng final_label=normal/depression thành gold review set."""
    if not input_file.exists() or input_file.stat().st_size == 0:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=GOLD_COLUMNS).to_csv(output_file, index=False, encoding="utf-8-sig")
        report = {"gold_rows": 0, "reason": "missing_review_samples_file"}
        _merge_report(report_file, {"gold_review": report})
        return report

    df = pd.read_csv(input_file, dtype=str).fillna("")
    if "final_label" not in df.columns:
        raise ValueError(f"Missing final_label column in {input_file}")

    df["final_label"] = df["final_label"].str.strip().str.lower()
    final_counts = df["final_label"].replace("", "blank").value_counts().to_dict()
    gold_df = df[df["final_label"].isin(VALID_FINAL_LABELS)].copy()
    gold_df["comment_text"] = gold_df["comment_text"].map(normalize_text)
    gold_df = gold_df.drop_duplicates(subset=["comment_text"], keep="first")
    gold_df["label"] = gold_df["final_label"].map(VALID_FINAL_LABELS).astype(int)
    gold_df["depression_score"] = pd.to_numeric(gold_df["depression_score"], errors="coerce").fillna(0).astype(int)
    gold_df = gold_df.reindex(columns=GOLD_COLUMNS)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    gold_df.to_csv(output_file, index=False, encoding="utf-8-sig")

    report = {
        "review_rows": int(len(df)),
        "gold_rows": int(len(gold_df)),
        "final_label_counts": final_counts,
        "gold_label_counts": gold_df["final_label"].value_counts().to_dict(),
        "label_mapping": {"normal": 0, "depression": 1},
        "excluded_from_gold": int(len(df) - len(gold_df)),
    }
    _merge_report(report_file, {"gold_review": report})
    logger.info("Da tao gold review set: %s dong -> %s", len(gold_df), output_file)
    return report


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
    print(json.dumps(build_gold_review_set(), ensure_ascii=False, indent=2))
