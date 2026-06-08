"""Train PhoBERT lần 1 và predict phần dữ liệu còn lại."""

from __future__ import annotations

import json
import logging

from yt_depression_crawler.modeling.phobert.phobert_predict import predict_remaining_comments
from yt_depression_crawler.modeling.phobert.phobert_postprocess import build_phobert_followup_files
from yt_depression_crawler.modeling.phobert.phobert_train import train_phobert_first


def run_phobert_pipeline() -> dict:
    train_report = train_phobert_first()
    prediction_report = predict_remaining_comments()
    postprocess_report = build_phobert_followup_files()
    return {
        "phobert_train": train_report,
        "phobert_predictions": prediction_report,
        "phobert_postprocess": postprocess_report,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    print(json.dumps(run_phobert_pipeline(), ensure_ascii=False, indent=2))
