"""Đánh giá baseline model trên gold_review.csv."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score

from yt_depression_crawler.core.config import (
    BASELINE_GOLD_ERRORS_FILE,
    BASELINE_GOLD_METRICS_FILE,
    BASELINE_MODEL_FILE,
    GOLD_REVIEW_FILE,
    LABELING_REPORT_FILE,
)

logger = logging.getLogger(__name__)


def evaluate_baseline_on_gold(
    gold_file: Path = GOLD_REVIEW_FILE,
    model_file: Path = BASELINE_MODEL_FILE,
    metrics_file: Path = BASELINE_GOLD_METRICS_FILE,
    errors_file: Path = BASELINE_GOLD_ERRORS_FILE,
    labeling_report_file: Path = LABELING_REPORT_FILE,
) -> dict:
    """Evaluate TF-IDF LogisticRegression baseline bằng human-reviewed labels."""
    if not gold_file.exists() or gold_file.stat().st_size == 0:
        raise FileNotFoundError(f"Missing gold review file: {gold_file}")
    if not model_file.exists() or model_file.stat().st_size == 0:
        raise FileNotFoundError(f"Missing baseline model file: {model_file}")

    df = pd.read_csv(gold_file, dtype=str).fillna("")
    df["label"] = pd.to_numeric(df["label"], errors="coerce").astype(int)
    model = joblib.load(model_file)
    y_true = df["label"].astype(int)
    y_pred = model.predict(df["comment_text"])

    probabilities = None
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(df["comment_text"])

    metrics = {
        "gold_rows": int(len(df)),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_macro": round(float(precision_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "f1_depression": round(float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
        "classification_report": classification_report(
            y_true,
            y_pred,
            labels=[0, 1],
            target_names=["normal", "depression"],
            output_dict=True,
            zero_division=0,
        ),
        "model_file": str(model_file),
    }

    eval_df = df.copy()
    eval_df["true_label"] = eval_df["label"].map({0: "normal", 1: "depression"})
    eval_df["pred_label"] = pd.Series(y_pred).map({0: "normal", 1: "depression"})
    if probabilities is not None:
        eval_df["pred_prob_depression"] = probabilities[:, 1]
    else:
        eval_df["pred_prob_depression"] = ""
    errors = eval_df[eval_df["label"].astype(int).to_numpy() != y_pred].copy()
    if not errors.empty:
        errors["error_type"] = errors.apply(_error_type, axis=1)
    errors = errors.reindex(
        columns=[
            "comment_text",
            "true_label",
            "pred_label",
            "pred_prob_depression",
            "weak_label",
            "confidence",
            "depression_score",
            "matched_keywords",
            "review_bucket",
            "reviewer_note",
            "error_type",
        ]
    )
    errors_file.parent.mkdir(parents=True, exist_ok=True)
    errors.to_csv(errors_file, index=False, encoding="utf-8-sig")
    metrics["error_rows"] = int(len(errors))
    metrics["errors_file"] = str(errors_file)

    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    metrics_file.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    _merge_report(labeling_report_file, {"baseline_gold_eval": metrics})
    logger.info("Da evaluate baseline tren gold: f1_macro=%s", metrics["f1_macro"])
    return metrics


def _error_type(row: pd.Series) -> str:
    if int(row["label"]) == 0 and row["pred_label"] == "depression":
        return "false_positive"
    if int(row["label"]) == 1 and row["pred_label"] == "normal":
        return "false_negative"
    return "unknown"


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
    print(json.dumps(evaluate_baseline_on_gold(), ensure_ascii=False, indent=2))
