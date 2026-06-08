"""Tạo train/val/test split từ initial_train.csv."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from yt_depression_crawler.processing.cleaner import normalize_text
from yt_depression_crawler.core.config import (
    INITIAL_TRAIN_FILE,
    INITIAL_TRAIN_RANDOM_SEED,
    LABELING_REPORT_FILE,
    TEST_FILE,
    TEST_RATIO,
    TRAIN_FILE,
    TRAIN_RATIO,
    VAL_FILE,
    VAL_RATIO,
)

logger = logging.getLogger(__name__)


SPLIT_COLUMNS = [
    "comment_text",
    "label",
    "weak_label",
    "confidence",
    "depression_score",
    "matched_keywords",
]


def create_train_val_test_splits(
    input_file: Path = INITIAL_TRAIN_FILE,
    train_file: Path = TRAIN_FILE,
    val_file: Path = VAL_FILE,
    test_file: Path = TEST_FILE,
    report_file: Path = LABELING_REPORT_FILE,
    random_seed: int = INITIAL_TRAIN_RANDOM_SEED,
) -> dict:
    """Tạo split stratified với label số: depression=1, normal=0."""
    if not input_file.exists() or input_file.stat().st_size == 0:
        for path in [train_file, val_file, test_file]:
            path.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(columns=SPLIT_COLUMNS).to_csv(path, index=False, encoding="utf-8-sig")
        report = {"total_rows": 0, "reason": "missing_initial_train_file"}
        _merge_report(report_file, {"splits": report})
        return report

    df = pd.read_csv(input_file, dtype=str).fillna("")
    df = df[df["weak_label"].isin(["depression_auto", "normal_auto"])]
    df["comment_text"] = df["comment_text"].map(normalize_text)
    df = df.drop_duplicates(subset=["comment_text"], keep="first")
    df["label"] = df["weak_label"].map({"normal_auto": 0, "depression_auto": 1}).astype(int)
    df["depression_score"] = pd.to_numeric(df["depression_score"], errors="coerce").fillna(0).astype(int)
    df = df.reindex(columns=SPLIT_COLUMNS)

    if df.empty or df["label"].nunique() < 2:
        raise ValueError("Need both depression_auto and normal_auto rows to create train/val/test splits.")

    temp_ratio = VAL_RATIO + TEST_RATIO
    if round(TRAIN_RATIO + temp_ratio, 6) != 1.0:
        raise ValueError("TRAIN_RATIO + VAL_RATIO + TEST_RATIO must equal 1.0")

    train_df, temp_df = train_test_split(
        df,
        test_size=temp_ratio,
        random_state=random_seed,
        stratify=df["label"],
    )
    relative_test_ratio = TEST_RATIO / temp_ratio
    val_df, test_df = train_test_split(
        temp_df,
        test_size=relative_test_ratio,
        random_state=random_seed,
        stratify=temp_df["label"],
    )

    for path, split_df in [(train_file, train_df), (val_file, val_df), (test_file, test_df)]:
        path.parent.mkdir(parents=True, exist_ok=True)
        split_df.to_csv(path, index=False, encoding="utf-8-sig")

    report = {
        "total_rows": int(len(df)),
        "train_rows": int(len(train_df)),
        "val_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "label_counts": df["label"].value_counts().sort_index().to_dict(),
        "train_label_counts": train_df["label"].value_counts().sort_index().to_dict(),
        "val_label_counts": val_df["label"].value_counts().sort_index().to_dict(),
        "test_label_counts": test_df["label"].value_counts().sort_index().to_dict(),
        "label_mapping": {"normal": 0, "depression": 1},
        "ratios": {"train": TRAIN_RATIO, "val": VAL_RATIO, "test": TEST_RATIO},
    }
    _merge_report(report_file, {"splits": report})
    logger.info("Da tao train/val/test: %s/%s/%s", len(train_df), len(val_df), len(test_df))
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
    print(json.dumps(create_train_val_test_splits(), ensure_ascii=False, indent=2))
