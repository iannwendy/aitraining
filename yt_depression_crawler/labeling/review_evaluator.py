"""Đánh giá weak labels trên gold_review.csv."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score

from yt_depression_crawler.core.config import GOLD_REVIEW_FILE, LABELING_REPORT_FILE, REVIEW_EVAL_ERRORS_FILE, REVIEW_EVAL_REPORT_FILE

logger = logging.getLogger(__name__)

WEAK_LABEL_TO_LABEL = {"normal_auto": 0, "depression_auto": 1}


def evaluate_weak_labels_on_gold(
    gold_file: Path = GOLD_REVIEW_FILE,
    report_file: Path = REVIEW_EVAL_REPORT_FILE,
    errors_file: Path = REVIEW_EVAL_ERRORS_FILE,
    labeling_report_file: Path = LABELING_REPORT_FILE,
) -> dict:
    """So sánh weak_label với final_label trong gold set."""
    if not gold_file.exists() or gold_file.stat().st_size == 0:
        report = {"gold_rows": 0, "reason": "missing_gold_review_file"}
        _write_json(report_file, report)
        _merge_report(labeling_report_file, {"review_eval": report})
        return report

    df = pd.read_csv(gold_file, dtype=str).fillna("")
    df["label"] = pd.to_numeric(df["label"], errors="coerce").astype(int)
    eval_df = df[df["weak_label"].isin(WEAK_LABEL_TO_LABEL)].copy()
    eval_df["pred_label"] = eval_df["weak_label"].map(WEAK_LABEL_TO_LABEL).astype(int)

    skipped = int(len(df) - len(eval_df))
    if eval_df.empty:
        report = {"gold_rows": int(len(df)), "evaluated_rows": 0, "skipped_uncertain": skipped}
        _write_json(report_file, report)
        _merge_report(labeling_report_file, {"review_eval": report})
        return report

    y_true = eval_df["label"].astype(int)
    y_pred = eval_df["pred_label"].astype(int)
    report = {
        "gold_rows": int(len(df)),
        "evaluated_rows": int(len(eval_df)),
        "skipped_uncertain": skipped,
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
    }

    errors = eval_df[y_true.to_numpy() != y_pred.to_numpy()].copy()
    if not errors.empty:
        errors["true_label"] = errors["label"].map({0: "normal", 1: "depression"})
        errors["predicted_label"] = errors["pred_label"].map({0: "normal", 1: "depression"})
        errors["error_type"] = errors.apply(_error_type, axis=1)
    errors = errors.reindex(
        columns=[
            "comment_text",
            "true_label",
            "predicted_label",
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
    report["error_rows"] = int(len(errors))
    report["errors_file"] = str(errors_file)

    _write_json(report_file, report)
    _merge_report(labeling_report_file, {"review_eval": report})
    logger.info("Da danh gia weak label tren gold: f1_macro=%s", report["f1_macro"])
    return report


def _error_type(row: pd.Series) -> str:
    if int(row["label"]) == 0 and int(row["pred_label"]) == 1:
        return "false_positive"
    if int(row["label"]) == 1 and int(row["pred_label"]) == 0:
        return "false_negative"
    return "unknown"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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
    print(json.dumps(evaluate_weak_labels_on_gold(), ensure_ascii=False, indent=2))
