"""Chạy pipeline chuẩn bị train và baseline model."""

from __future__ import annotations

import json
import logging

from yt_depression_crawler.modeling.baseline.baseline_model import train_baseline_model
from yt_depression_crawler.labeling.review_sampler import create_review_samples
from yt_depression_crawler.modeling.train_splitter import create_train_val_test_splits


def run_ml_pipeline() -> dict:
    review_report = create_review_samples()
    split_report = create_train_val_test_splits()
    baseline_report = train_baseline_model()
    return {
        "review_samples": review_report,
        "splits": split_report,
        "baseline_model": baseline_report,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    print(json.dumps(run_ml_pipeline(), ensure_ascii=False, indent=2))
