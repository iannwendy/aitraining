"""Train and evaluate BERTopic-only and PhoBERT + BERTopic consistently.

BERTopic is fitted from scratch on the supervised training split only. This is
deliberate: the historical 316K-corpus BERTopic artifact may contain VSMEC and
in-domain holdout text, so using it for predictive evaluation would be
transductive leakage. Validation, in-domain test and VSMEC are transform-only.
"""

from __future__ import annotations

import argparse
import json
import logging
import pickle
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score, precision_score, recall_score,
)
from sklearn.preprocessing import StandardScaler


SEED = 42
FINAL_TRAIN = PROJECT_DIR / "data" / "labeled" / "final_train.csv"
FINAL_VAL = PROJECT_DIR / "data" / "labeled" / "final_val.csv"
FINAL_TEST = PROJECT_DIR / "data" / "labeled" / "final_test.csv"
CROSS_DOMAIN_TEST = PROJECT_DIR / "data_unified" / "cross_domain_test.csv"

# Fine-tuned on the repaired Round-5 training split.
PHOBERT_DIR = PROJECT_DIR / "models" / "round5_predictions" / "seed_42" / "best_model"
PHOBERT_TOKENIZER_DIR = PROJECT_DIR / "models" / "phobert_base_local"
OUTPUT_DIR = PROJECT_DIR / "results" / "reproducible_round5"
OUTPUT_METRICS = OUTPUT_DIR / "topic_models_results.json"
OUTPUT_PREDICTIONS_IN = OUTPUT_DIR / "phobert_bertopic_predictions_in_domain.csv"
OUTPUT_PREDICTIONS_CROSS = OUTPUT_DIR / "phobert_bertopic_predictions_cross_domain.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("phobert_bertopic")


def load_split(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"comment_text": str}).fillna("")
    df["label"] = pd.to_numeric(df["label"], errors="coerce").astype(int)
    df = df[df["comment_text"].str.strip().ne("")].copy()
    return df


def compute_metrics(y_true, y_pred) -> dict:
    labels = [0, 1]
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_macro": round(float(precision_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "f1_weighted": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "f1_depression": round(float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
    }


def validate_feature_matrix(name: str, values: np.ndarray) -> np.ndarray:
    """Fail fast on non-finite features and report their numeric range."""
    values = np.asarray(values, dtype=np.float64)
    if not np.isfinite(values).all():
        bad = int((~np.isfinite(values)).sum())
        raise ValueError(f"{name} contains {bad} non-finite values")
    logger.info(
        "%s feature range: min=%.6f max=%.6f max_abs=%.6f",
        name,
        float(values.min()),
        float(values.max()),
        float(np.abs(values).max()),
    )
    return values


def stable_binary_predict(name: str, classifier, values: np.ndarray) -> np.ndarray:
    """Apply a fitted binary linear classifier with explicit finite checks.

    This is algebraically identical to ``LogisticRegression.predict`` for a
    binary problem, but avoids a macOS Accelerate/scikit-learn ``matmul`` path
    that emits spurious overflow warnings on otherwise finite arrays.
    """
    if len(classifier.classes_) != 2 or classifier.coef_.shape[0] != 1:
        raise ValueError(f"{name} must be a fitted binary linear classifier")
    coef = validate_feature_matrix(f"{name} coefficients", classifier.coef_)
    intercept = validate_feature_matrix(
        f"{name} intercept", classifier.intercept_.reshape(1, -1)
    )
    scores = np.einsum("ij,j->i", values, coef[0], dtype=np.float64)
    scores = validate_feature_matrix(
        f"{name} decision scores", scores + intercept[0, 0]
    )
    return np.where(scores >= 0.0, classifier.classes_[1], classifier.classes_[0])


def get_phobert_embeddings(texts: list[str], device, tokenizer, model, prepare, dataset_cls, max_len: int, batch_size: int = 16) -> np.ndarray:
    """Extract CLS-token embeddings from fine-tuned PhoBERT."""
    import torch
    from torch.utils.data import DataLoader

    prepared = prepare(list(texts))
    dataset = dataset_cls(prepared, None, tokenizer, max_len)
    loader = DataLoader(dataset, batch_size=batch_size)

    embeddings = []
    model.eval()
    with torch.no_grad():
        for batch in loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            cls_emb = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            embeddings.append(cls_emb)
    return np.vstack(embeddings)


def get_topic_features(texts: list[str], topic_model, topic_embedder) -> np.ndarray:
    """Compute (topic_id, topic_prob) features using the trained BERTopic model."""
    embeddings = topic_embedder.encode(texts, show_progress_bar=True, batch_size=64)
    topics, probs = topic_model.transform(texts, embeddings=embeddings)

    # Some rows return probs as scalar or None — coerce to float.
    probs_arr = topic_probabilities(probs, len(texts))

    return np.column_stack([
        np.array(topics, dtype=np.float64).reshape(-1, 1),
        probs_arr.reshape(-1, 1),
    ])


def topic_probabilities(probs, expected_rows: int) -> np.ndarray:
    """Coerce BERTopic probability output to one confidence per row."""
    if probs is None:
        return np.zeros(expected_rows, dtype=np.float64)
    probs_arr = np.asarray(probs, dtype=np.float64)
    if probs_arr.ndim > 1:
        probs_arr = probs_arr.max(axis=1)
    else:
        probs_arr = probs_arr.reshape(-1)
    if len(probs_arr) != expected_rows:
        raise ValueError(
            f"BERTopic probability rows={len(probs_arr)}; expected={expected_rows}"
        )
    return probs_arr


def topic_features_from_assignments(topics, probs, expected_rows: int) -> np.ndarray:
    """Build the same two-feature representation used for transformed data."""
    topic_ids = np.asarray(topics, dtype=np.float64).reshape(-1)
    if len(topic_ids) != expected_rows:
        raise ValueError(f"BERTopic topic rows={len(topic_ids)}; expected={expected_rows}")
    return np.column_stack([
        topic_ids,
        topic_probabilities(probs, expected_rows),
    ])


def main() -> None:
    import torch
    from transformers import AutoModel, AutoTokenizer
    from yt_depression_crawler.modeling.phobert.phobert_utils import (
        PhoBertDataset, get_device, prepare_many_texts,
    )
    from sentence_transformers import SentenceTransformer
    from bertopic import BERTopic
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP

    parser = argparse.ArgumentParser()
    parser.add_argument("--train-file", type=Path, default=FINAL_TRAIN)
    parser.add_argument("--phobert-dir", type=Path, default=PHOBERT_DIR)
    parser.add_argument("--tag", default="clean")
    args = parser.parse_args()
    output_metrics = OUTPUT_DIR / f"topic_models_results_{args.tag}.json"
    output_predictions_in = OUTPUT_DIR / f"phobert_bertopic_{args.tag}_predictions_in_domain.csv"
    output_predictions_cross = OUTPUT_DIR / f"phobert_bertopic_{args.tag}_predictions_cross_domain.csv"
    output_topic_predictions_in = OUTPUT_DIR / f"bertopic_only_{args.tag}_predictions_in_domain.csv"
    output_topic_predictions_cross = OUTPUT_DIR / f"bertopic_only_{args.tag}_predictions_cross_domain.csv"
    topic_model_dir = PROJECT_DIR / "models" / "bertopic_round5" / args.tag
    topic_model_file = topic_model_dir / "bertopic_train_only.pkl"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    topic_model_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 70)
    logger.info("PhoBERT + BERTopic rerun with train-only topic fitting")
    logger.info("=" * 70)

    # ── Load data ────────────────────────────────────────────────────
    train_df = load_split(args.train_file)
    val_df = load_split(FINAL_VAL)
    test_df = load_split(FINAL_TEST)
    cross_df = load_split(CROSS_DOMAIN_TEST)
    logger.info("train=%d val=%d test=%d cross_domain=%d",
                len(train_df), len(val_df), len(test_df), len(cross_df))

    # ── Load models ──────────────────────────────────────────────────
    device = get_device()
    logger.info("Device: %s", device)

    logger.info("Loading PhoBERT from %s", args.phobert_dir)
    tokenizer = AutoTokenizer.from_pretrained(str(PHOBERT_TOKENIZER_DIR), use_fast=False)
    phobert = AutoModel.from_pretrained(str(args.phobert_dir))
    phobert.to(device)
    phobert.eval()

    logger.info("Loading topic embedder (paraphrase-multilingual-MiniLM-L12-v2)")
    topic_embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # Fit only on training data. Validation and test remain untouched.
    fit_texts = train_df["comment_text"].tolist()
    fit_labels = train_df["label"].astype(int).tolist()
    logger.info("Fitting on training only: %d samples", len(fit_texts))

    # ── Feature extraction ──────────────────────────────────────────
    logger.info("Extracting PhoBERT CLS embeddings for fit set...")
    phobert_fit = get_phobert_embeddings(
        fit_texts, device, tokenizer, phobert, prepare_many_texts, PhoBertDataset, 128
    )
    logger.info("  shape: %s", phobert_fit.shape)

    logger.info("Encoding training texts for leakage-safe BERTopic fitting...")
    topic_fit_embeddings = topic_embedder.encode(
        fit_texts, show_progress_bar=True, batch_size=64
    )
    topic_model = BERTopic(
        embedding_model=None,
        umap_model=UMAP(
            n_neighbors=15,
            n_components=5,
            min_dist=0.0,
            metric="cosine",
            random_state=SEED,
            low_memory=True,
        ),
        hdbscan_model=HDBSCAN(
            min_cluster_size=15,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=True,
        ),
        vectorizer_model=CountVectorizer(ngram_range=(1, 2), min_df=2),
        calculate_probabilities=False,
        verbose=True,
    )
    fit_topics, fit_probs = topic_model.fit_transform(
        fit_texts, embeddings=topic_fit_embeddings
    )
    topic_fit = topic_features_from_assignments(fit_topics, fit_probs, len(fit_texts))
    with open(topic_model_file, "wb") as f:
        pickle.dump(topic_model, f)
    logger.info("Saved train-only BERTopic model: %s", topic_model_file)
    logger.info("  shape: %s", topic_fit.shape)

    X_fit = np.hstack([phobert_fit, topic_fit])
    logger.info("Combined feature shape: %s", X_fit.shape)

    scaler = StandardScaler()
    X_fit = validate_feature_matrix("combined train", scaler.fit_transform(X_fit))

    # ── Train logistic regression ────────────────────────────────────
    clf = LogisticRegression(
        solver="liblinear",
        max_iter=2000,
        class_weight="balanced",
        random_state=SEED,
    )
    clf.fit(X_fit, fit_labels)
    logger.info("LogReg fitted. Class distribution: %s",
                dict(zip(*np.unique(fit_labels, return_counts=True))))

    # ── Evaluate on in-domain test ──────────────────────────────────
    logger.info("Extracting features for in-domain test (%d rows)...", len(test_df))
    phobert_test = get_phobert_embeddings(
        test_df["comment_text"].tolist(), device, tokenizer, phobert,
        prepare_many_texts, PhoBertDataset, 128
    )
    topic_test = get_topic_features(
        test_df["comment_text"].tolist(), topic_model, topic_embedder
    )
    X_test = validate_feature_matrix(
        "combined in-domain test",
        scaler.transform(np.hstack([phobert_test, topic_test])),
    )
    y_pred_in = stable_binary_predict("hybrid in-domain", clf, X_test)
    y_true_in = test_df["label"].astype(int).to_numpy()
    in_metrics = compute_metrics(y_true_in, y_pred_in)

    # Save in-domain predictions
    pd.DataFrame({
        "comment_text": test_df["comment_text"].values,
        "true_label": y_true_in,
        "pred_label": y_pred_in,
    }).to_csv(output_predictions_in, index=False)
    logger.info("In-domain F1-macro: %.4f | F1-dep: %.4f | Accuracy: %.4f",
                in_metrics["f1_macro"], in_metrics["f1_depression"], in_metrics["accuracy"])

    # ── Evaluate on cross-domain VSMEC ──────────────────────────────
    logger.info("Extracting features for cross-domain VSMEC (%d rows)...", len(cross_df))
    phobert_cross = get_phobert_embeddings(
        cross_df["comment_text"].tolist(), device, tokenizer, phobert,
        prepare_many_texts, PhoBertDataset, 128
    )
    topic_cross = get_topic_features(
        cross_df["comment_text"].tolist(), topic_model, topic_embedder
    )
    X_cross = validate_feature_matrix(
        "combined VSMEC",
        scaler.transform(np.hstack([phobert_cross, topic_cross])),
    )
    y_pred_cross = stable_binary_predict("hybrid VSMEC", clf, X_cross)
    y_true_cross = cross_df["label"].astype(int).to_numpy()
    cross_metrics = compute_metrics(y_true_cross, y_pred_cross)

    # BERTopic-only control: identical topic features and split protocol,
    # without contextual PhoBERT embeddings.
    topic_scaler = StandardScaler()
    topic_fit_scaled = topic_scaler.fit_transform(topic_fit)
    topic_clf = LogisticRegression(
        solver="liblinear",
        max_iter=2000,
        class_weight="balanced",
        random_state=SEED,
    )
    topic_clf.fit(topic_fit_scaled, fit_labels)
    topic_test_scaled = validate_feature_matrix(
        "topic-only in-domain", topic_scaler.transform(topic_test)
    )
    topic_cross_scaled = validate_feature_matrix(
        "topic-only VSMEC", topic_scaler.transform(topic_cross)
    )
    y_topic_in = stable_binary_predict(
        "topic-only in-domain", topic_clf, topic_test_scaled
    )
    y_topic_cross = stable_binary_predict(
        "topic-only VSMEC", topic_clf, topic_cross_scaled
    )
    topic_only_in = compute_metrics(y_true_in, y_topic_in)
    topic_only_cross = compute_metrics(y_true_cross, y_topic_cross)

    # Save cross-domain predictions
    pd.DataFrame({
        "comment_text": cross_df["comment_text"].values,
        "true_label": y_true_cross,
        "pred_label": y_pred_cross,
    }).to_csv(output_predictions_cross, index=False)
    pd.DataFrame({
        "comment_text": test_df["comment_text"].values,
        "true_label": y_true_in,
        "pred_label": y_topic_in,
    }).to_csv(output_topic_predictions_in, index=False)
    pd.DataFrame({
        "comment_text": cross_df["comment_text"].values,
        "true_label": y_true_cross,
        "pred_label": y_topic_cross,
    }).to_csv(output_topic_predictions_cross, index=False)
    logger.info("Cross-domain F1-macro: %.4f | F1-dep: %.4f | Accuracy: %.4f",
                cross_metrics["f1_macro"], cross_metrics["f1_depression"], cross_metrics["accuracy"])

    # ── Summary ─────────────────────────────────────────────────────
    logger.info("=" * 70)
    logger.info("PhoBERT + BERTopic (repaired Round-5 protocol)")
    logger.info("  In-domain    F1-macro: %.4f  F1-dep: %.4f  Accuracy: %.4f",
                in_metrics["f1_macro"], in_metrics["f1_depression"], in_metrics["accuracy"])
    logger.info("  Cross-domain F1-macro: %.4f  F1-dep: %.4f  Accuracy: %.4f",
                cross_metrics["f1_macro"], cross_metrics["f1_depression"], cross_metrics["accuracy"])
    logger.info("  Δ F1 (in - cross): %.4f",
                in_metrics["f1_macro"] - cross_metrics["f1_macro"])

    # ── Persist ─────────────────────────────────────────────────────
    report = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "protocol": "training only fit; fixed human-only in-domain test; VSMEC affective proxy holdout",
        "model": "PhoBERT seed 42 CLS embeddings + BERTopic features + LogisticRegression",
        "phobert_checkpoint": str(args.phobert_dir),
        "bertopic_model": str(topic_model_file),
        "bertopic_fit_scope": "supervised training split only",
        "bertopic_topic_count_excluding_outlier": int(
            sum(topic_id != -1 for topic_id in topic_model.get_topic_info()["Topic"].tolist())
        ),
        "fit_samples": len(fit_texts),
        "in_domain": in_metrics,
        "cross_domain": cross_metrics,
        "delta_f1_in_minus_cross": round(
            in_metrics["f1_macro"] - cross_metrics["f1_macro"], 4
        ),
        "predictions_in_domain_csv": str(output_predictions_in),
        "predictions_cross_domain_csv": str(output_predictions_cross),
        "bertopic_only": {
            "in_domain": topic_only_in,
            "cross_domain": topic_only_cross,
        },
    }
    output_metrics.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Metrics saved: %s", output_metrics)


if __name__ == "__main__":
    main()
