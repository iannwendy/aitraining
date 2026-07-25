"""Train TF-IDF baselines and evaluate both fixed holdouts.

The vectorizer is fit on training text only. Validation, in-domain test and
VSMEC are never passed to ``fit``. Results and row-level predictions are stored
under ``results/reproducible_round5`` for later table/figure generation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC


PROJECT_DIR = Path(__file__).resolve().parents[1]
LABELED_DIR = PROJECT_DIR / "data" / "labeled"
MODEL_DIR = PROJECT_DIR / "models"
RESULTS_DIR = PROJECT_DIR / "results" / "reproducible_round5"
CROSS_DOMAIN_FILE = PROJECT_DIR / "data_unified" / "cross_domain_test.csv"
SPLIT_FILES = {
    "validation": LABELED_DIR / "final_val.csv",
    "in_domain": LABELED_DIR / "final_test.csv",
    "cross_domain": CROSS_DOMAIN_FILE,
}


def metrics(y_true, y_pred) -> dict[str, object]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1_depression": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
    }


def build_pipeline(classifier) -> Pipeline:
    features = FeatureUnion([
        ("word", TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            max_features=80_000,
            min_df=2,
            sublinear_tf=True,
        )),
        ("char", TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            max_features=80_000,
            min_df=2,
            sublinear_tf=True,
        )),
    ])
    return Pipeline([("features", features), ("classifier", classifier)])


def main() -> dict[str, object]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-file", type=Path, default=LABELED_DIR / "final_train.csv")
    parser.add_argument("--tag", default="clean")
    parser.add_argument(
        "--result-name",
        default=None,
        help="Optional JSON filename so locked holdout export does not overwrite validation-only results",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        choices=sorted(SPLIT_FILES),
        default=sorted(SPLIT_FILES),
        help="Evaluation splits to load after fitting; use validation only while selecting candidates",
    )
    args = parser.parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(args.train_file)
    selected_splits = list(dict.fromkeys(args.splits))
    datasets = {
        split_name: pd.read_csv(SPLIT_FILES[split_name])
        for split_name in selected_splits
    }
    models = {
        "tfidf_logreg": build_pipeline(LogisticRegression(
            max_iter=2_000,
            class_weight="balanced",
            solver="liblinear",
            random_state=42,
        )),
        "tfidf_linearsvc": build_pipeline(LinearSVC(
            max_iter=5_000,
            class_weight="balanced",
            random_state=42,
        )),
    }

    report: dict[str, object] = {
        "protocol": "fit train only; fixed human-only validation/test; VSMEC affective proxy holdout",
        "dataset": {
            "train_rows": len(train),
            "evaluated_splits": selected_splits,
            "split_rows": {
                split_name: len(frame) for split_name, frame in datasets.items()
            },
        },
        "models": {},
    }

    for name, pipeline in models.items():
        pipeline.fit(train["comment_text"].astype(str), train["label"].astype(int))
        model_report = {}
        for split_name, frame in datasets.items():
            texts = frame["comment_text"].astype(str)
            predictions = pipeline.predict(texts)
            if hasattr(pipeline, "predict_proba"):
                scores = pipeline.predict_proba(texts)[:, 1]
                score_type = "probability"
            else:
                scores = expit(np.asarray(pipeline.decision_function(texts), dtype=float))
                score_type = "sigmoid_decision_function"
            model_report[split_name] = metrics(frame["label"].astype(int), predictions)
            model_report[split_name]["score_type"] = score_type
            pd.DataFrame({
                "comment_text": frame["comment_text"].astype(str),
                "label": frame["label"].astype(int),
                "prediction": predictions,
                "score_depression": scores,
            }).to_csv(RESULTS_DIR / f"{name}_{args.tag}_{split_name}_predictions.csv", index=False)

        report["models"][name] = model_report
        joblib.dump(pipeline, MODEL_DIR / f"{name}_round5_{args.tag}.joblib")
        print(
            f"{name}: "
            + "; ".join(
                f"{split_name} F1={model_report[split_name]['f1_macro']:.4f}"
                for split_name in selected_splits
            )
        )

    output = RESULTS_DIR / (
        args.result_name or f"classical_results_{args.tag}.json"
    )
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {output}")
    return report


if __name__ == "__main__":
    main()
