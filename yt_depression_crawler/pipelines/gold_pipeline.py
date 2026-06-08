"""Chạy gold review build + weak-label eval + baseline-gold eval."""

from __future__ import annotations

import json
import logging

from yt_depression_crawler.labeling.gold_baseline_eval import evaluate_baseline_on_gold
from yt_depression_crawler.labeling.gold_builder import build_gold_review_set
from yt_depression_crawler.labeling.review_evaluator import evaluate_weak_labels_on_gold


def run_gold_pipeline() -> dict:
    gold_report = build_gold_review_set()
    weak_report = evaluate_weak_labels_on_gold()
    baseline_report = evaluate_baseline_on_gold()
    return {
        "gold_review": gold_report,
        "review_eval": weak_report,
        "baseline_gold_eval": baseline_report,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    print(json.dumps(run_gold_pipeline(), ensure_ascii=False, indent=2))
