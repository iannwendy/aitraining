"""Train baseline TF-IDF + Logistic Regression / LinearSVC cho weak-labeled dataset."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from yt_depression_crawler.core.config import (
    BASELINE_METRICS_FILE,
    BASELINE_MODEL_FILE,
    BASELINE_SVC_METRICS_FILE,
    BASELINE_SVC_MODEL_FILE,
    FINAL_TEST_FILE,
    FINAL_TRAIN_FILE,
    FINAL_VAL_FILE,
    LABELING_REPORT_FILE,
    TEST_FILE,
    TRAIN_FILE,
    VAL_FILE,
    ensure_directories,
)

logger = logging.getLogger(__name__)


def train_baseline_model(
    train_file: Path = FINAL_TRAIN_FILE,
    val_file: Path = FINAL_VAL_FILE,
    test_file: Path = FINAL_TEST_FILE,
    model_file: Path = BASELINE_MODEL_FILE,
    metrics_file: Path = BASELINE_METRICS_FILE,
    report_file: Path = LABELING_REPORT_FILE,
) -> dict:
    """Train baseline TF-IDF + Logistic Regression trên final dataset (post round-3).

    Defaults to data/final_*.csv (1,786 train rows). Override train_file/val_file/
    test_file for ablation on the legacy pre-Phase-1 splits (data/train.csv).
    """
    ensure_directories()
    train_df = _load_split(train_file)
    val_df = _load_split(val_file)
    test_df = _load_split(test_file)

    pipeline = Pipeline(
        steps=[
            (
                "features",
                FeatureUnion(
                    [
                        (
                            "word_tfidf",
                            TfidfVectorizer(
                                analyzer="word",
                                ngram_range=(1, 2),
                                min_df=2,
                                max_features=80_000,
                                lowercase=True,
                            ),
                        ),
                        (
                            "char_tfidf",
                            TfidfVectorizer(
                                analyzer="char_wb",
                                ngram_range=(3, 5),
                                min_df=2,
                                max_features=80_000,
                                lowercase=True,
                            ),
                        ),
                    ]
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1_000,
                    class_weight="balanced",
                    solver="liblinear",
                    random_state=42,
                ),
            ),
        ]
    )

    pipeline.fit(train_df["comment_text"], train_df["label"].astype(int))
    metrics = {
        "train_rows": int(len(train_df)),
        "val_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "label_mapping": {"normal": 0, "depression": 1},
        "validation": _evaluate(pipeline, val_df),
        "test": _evaluate(pipeline, test_df),
        "model_file": str(model_file),
    }

    model_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_file)
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    metrics_file.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    _merge_report(report_file, {"baseline_model": metrics})
    logger.info("Da train baseline model -> %s", model_file)
    return metrics


def _build_baseline_features() -> FeatureUnion:
    """Shared TF-IDF feature union cho cả LogReg và LinearSVC.

    Word 1-2gram + char_wb 3-5gram, cùng vocab size với LogReg baseline để
    so sánh công bằng. Trả về FeatureUnion (chưa fit).
    """
    return FeatureUnion(
        [
            (
                "word_tfidf",
                TfidfVectorizer(
                    analyzer="word",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=80_000,
                    lowercase=True,
                ),
            ),
            (
                "char_tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=2,
                    max_features=80_000,
                    lowercase=True,
                ),
            ),
        ]
    )


def train_linear_svc_model(
    train_file: Path = FINAL_TRAIN_FILE,
    val_file: Path = FINAL_VAL_FILE,
    test_file: Path = FINAL_TEST_FILE,
    model_file: Path = BASELINE_SVC_MODEL_FILE,
    metrics_file: Path = BASELINE_SVC_METRICS_FILE,
    report_file: Path = LABELING_REPORT_FILE,
    C: float = 1.0,
) -> dict:
    """Train baseline TF-IDF + LinearSVC classifier trên final dataset (post round-3).

    LinearSVC thường cho decision boundary sharp hơn LogReg trên text sparse
    features và là baseline thứ hai đáng tham chiếu. Cùng class_weight='balanced'
    để xử lý imbalance giống LogReg.

    Returns:
        dict với key "validation" và "test" chứa classification metrics.
    """
    ensure_directories()
    train_df = _load_split(train_file)
    val_df = _load_split(val_file)
    test_df = _load_split(test_file)

    pipeline = Pipeline(
        steps=[
            ("features", _build_baseline_features()),
            (
                "classifier",
                LinearSVC(
                    C=C,
                    class_weight="balanced",
                    random_state=42,
                    max_iter=2_000,
                ),
            ),
        ]
    )

    pipeline.fit(train_df["comment_text"], train_df["label"].astype(int))
    metrics = {
        "train_rows": int(len(train_df)),
        "val_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "label_mapping": {"normal": 0, "depression": 1},
        "C": C,
        "validation": _evaluate(pipeline, val_df),
        "test": _evaluate(pipeline, test_df),
        "model_file": str(model_file),
    }

    model_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_file)
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    metrics_file.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    _merge_report(report_file, {"baseline_svc_model": metrics})
    logger.info("Da train LinearSVC baseline -> %s", model_file)
    return metrics


def _load_split(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(f"Missing split file: {path}")

    df = pd.read_csv(path, dtype={"comment_text": str}).fillna("")
    required = {"comment_text", "label"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")
    if df.empty or df["label"].nunique() < 2:
        raise ValueError(f"Split file must contain both classes: {path}")
    return df


def _evaluate(model: Pipeline, df: pd.DataFrame) -> dict:
    y_true = df["label"].astype(int)
    y_pred = model.predict(df["comment_text"])
    return {
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
            zero_division=0,
            output_dict=True,
        ),
    }


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
    print(json.dumps(train_baseline_model(), ensure_ascii=False, indent=2))
