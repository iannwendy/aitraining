"""Chạy toàn bộ pipeline weak labeling và tạo initial_train.csv."""

from __future__ import annotations

import json
import logging

from yt_depression_crawler.labeling.auto_labeler import auto_label_comments
from yt_depression_crawler.labeling.dataset_sampler import build_initial_train_dataset


def run_labeling_pipeline() -> dict:
    auto_label_report = auto_label_comments()
    train_report = build_initial_train_dataset()
    return {
        "auto_labeling": auto_label_report,
        "initial_train": train_report,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    summary = run_labeling_pipeline()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
