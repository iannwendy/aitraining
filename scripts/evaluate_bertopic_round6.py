"""Evaluate BERTopic and PhoBERT+BERTopic on Round 6 dataset.

This script:
  1. Loads the BERTopic model (topic-only features)
  2. Loads PhoBERT embeddings from Round 6 models
  3. Trains a logistic regression classifier on topic features alone (BERTopic-only)
  4. Trains a logistic regression classifier on PhoBERT + topic features (combined)
  5. Evaluates both on in-domain and cross-domain test sets
  6. Reports all metrics: Accuracy, Precision, Recall, F1, F1-macro, F1-weighted

Usage:
    PYTHONPATH="$PWD" .venv/bin/python scripts/evaluate_bertopic_round6.py
"""

from __future__ import annotations

import json
import os
import pickle
import sys
from pathlib import Path
from datetime import datetime

# Set offline mode for HuggingFace
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)

DATA_DIR = PROJECT_DIR / "data"
MODEL_DIR = PROJECT_DIR / "models"
RESULTS_DIR = PROJECT_DIR / "results"
UNIFIED_DIR = PROJECT_DIR / "data_unified"

TRAIN_FILE = DATA_DIR / "labeled" / "final_train.csv"
VAL_FILE = DATA_DIR / "labeled" / "final_val.csv"
TEST_FILE = DATA_DIR / "labeled" / "final_test.csv"
VSMEC_FILE = UNIFIED_DIR / "cross_domain_test.csv"

BERTOPIC_DIR = MODEL_DIR / "bertopic"
BERTOPIC_MODEL_FILE = BERTOPIC_DIR / "bertopic_model.pkl"
PHOBERT_ROUND6_DIR = MODEL_DIR / "round6_retrained"

OUTPUT_DIR = RESULTS_DIR / f"round6_bertopic_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")


def load_data():
    """Load train/val/test/vsmec."""
    train = pd.read_csv(TRAIN_FILE, dtype=str).fillna("")
    val = pd.read_csv(VAL_FILE, dtype=str).fillna("")
    test = pd.read_csv(TEST_FILE, dtype=str).fillna("")
    vsmec = pd.read_csv(VSMEC_FILE, dtype=str).fillna("")

    train["label"] = pd.to_numeric(train["label"], errors="coerce").astype(int)
    val["label"] = pd.to_numeric(val["label"], errors="coerce").astype(int)
    test["label"] = pd.to_numeric(test["label"], errors="coerce").astype(int)
    vsmec["label"] = pd.to_numeric(vsmec["label"], errors="coerce").astype(int)

    return train, val, test, vsmec


def compute_all_metrics(y_true, y_pred):
    """Compute all 4 metrics + macro/weighted F1."""
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average="binary", pos_label=1, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average="binary", pos_label=1, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, average="binary", pos_label=1, zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def get_bertopic_features(texts, topic_model, embedder):
    """Extract BERTopic features (topic_id + topic_prob)."""
    embeddings = embedder.encode(texts, show_progress_bar=True, batch_size=64)
    topics, probs = topic_model.transform(texts, embeddings=embeddings)

    # Handle probs (could be scalar, list, or 2D)
    if probs is None:
        probs_arr = np.zeros(len(texts))
    else:
        probs_arr = np.asarray(probs, dtype=np.float64).reshape(-1)
        if probs_arr.ndim > 1:
            probs_arr = probs_arr.max(axis=-1)

    return np.column_stack([
        np.array(topics, dtype=np.float64).reshape(-1, 1),
        probs_arr.reshape(-1, 1),
    ])


def get_phobert_embeddings(texts, model_dir, tokenizer_name="vinai/phobert-base", max_len=128, batch_size=16):
    """Extract PhoBERT CLS embeddings from a trained model."""
    from transformers import AutoTokenizer, AutoModel

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, use_fast=False)
    model = AutoModel.from_pretrained(str(model_dir))
    model.to(device)
    model.eval()

    embeddings = []
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            encoded = tokenizer(batch_texts, padding=True, truncation=True, max_length=max_len, return_tensors="pt")
            encoded = {k: v.to(device) for k, v in encoded.items()}
            outputs = model(**encoded)
            cls_emb = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            embeddings.append(cls_emb)

    del model
    return np.vstack(embeddings)


def main():
    print("=" * 70)
    print("ROUND 6: BERTopic & PhoBERT+BERTopic Evaluation")
    print("=" * 70)

    # ── Load data ─────────────────────────────────────────────────────
    print("\nLoading data...")
    train_df, val_df, test_df, vsmec_df = load_data()
    print(f"Train: {len(train_df):,} | Val: {len(val_df):,} | Test: {len(test_df):,} | VSMEC: {len(vsmec_df):,}")

    # Use train+val for fitting (paper §4.3 practice)
    fit_texts = train_df["comment_text"].tolist() + val_df["comment_text"].tolist()
    fit_labels = train_df["label"].astype(int).tolist() + val_df["label"].astype(int).tolist()
    test_texts = test_df["comment_text"].tolist()
    test_labels = test_df["label"].astype(int).tolist()
    vsmec_texts = vsmec_df["comment_text"].tolist() if "comment_text" in vsmec_df.columns else vsmec_df["text"].tolist()
    vsmec_labels = vsmec_df["label"].astype(int).tolist()

    print(f"Fit set: {len(fit_texts):,} | Test: {len(test_texts):,} | VSMEC: {len(vsmec_texts):,}")

    # ── Load BERTopic model ───────────────────────────────────────────
    print("\nLoading BERTopic model...")
    # SECURITY NOTE: Loading BERTopic pickle from our own models/bertopic/
    # directory. This is a trusted artifact produced by our own training scripts
    # (run_bertopic_standalone.py / train_bertopic_models.py). Same-risk as
    # joblib.load on our TF-IDF/LogReg/SVC pipelines. Safe in this context.
    with open(BERTOPIC_MODEL_FILE, "rb") as f:
        topic_model = pickle.load(f)
    print(f"BERTopic model loaded: {len(topic_model.get_topic_info())} topics")

    from sentence_transformers import SentenceTransformer
    print("Loading sentence embedder...")
    topic_embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    # ── 1. BERTopic-only ──────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("1. BERTOPIC-ONLY CLASSIFIER")
    print("=" * 70)

    print("Extracting BERTopic features for fit set...")
    topic_fit = get_bertopic_features(fit_texts, topic_model, topic_embedder)
    print(f"  Feature shape: {topic_fit.shape}")

    print("Extracting BERTopic features for test set...")
    topic_test = get_bertopic_features(test_texts, topic_model, topic_embedder)

    print("Extracting BERTopic features for VSMEC...")
    topic_vsmec = get_bertopic_features(vsmec_texts, topic_model, topic_embedder)

    # Train classifier
    scaler_bert = StandardScaler()
    X_fit_bert = scaler_bert.fit_transform(topic_fit)
    X_test_bert = scaler_bert.transform(topic_test)
    X_vsmec_bert = scaler_bert.transform(topic_vsmec)

    clf_bert = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    clf_bert.fit(X_fit_bert, fit_labels)

    bertopic_in = clf_bert.predict(X_test_bert)
    bertopic_cross = clf_bert.predict(X_vsmec_bert)

    bertopic_in_metrics = compute_all_metrics(test_labels, bertopic_in)
    bertopic_cross_metrics = compute_all_metrics(vsmec_labels, bertopic_cross)

    print(f"\nBERTopic In-domain: Acc={bertopic_in_metrics['accuracy']:.4f}, F1={bertopic_in_metrics['f1_score']:.4f}, F1-M={bertopic_in_metrics['f1_macro']:.4f}")
    print(f"BERTopic Cross-domain: Acc={bertopic_cross_metrics['accuracy']:.4f}, F1={bertopic_cross_metrics['f1_score']:.4f}, F1-M={bertopic_cross_metrics['f1_macro']:.4f}")

    # ── 2. PhoBERT + BERTopic ─────────────────────────────────────────
    print("\n" + "=" * 70)
    print("2. PHOBERT + BERTOPIC COMBINED")
    print("=" * 70)

    # Use seed 42 first (or whichever exists)
    phobert_seed42_dir = PHOBERT_ROUND6_DIR / "phobert_seed_42" / "best_model"
    if not phobert_seed42_dir.exists():
        print(f"WARNING: PhoBERT model not found at {phobert_seed42_dir}")
        print("Skipping PhoBERT+BERTopic evaluation. Will retry after training completes.")
        phobert_combined_in_metrics = None
        phobert_combined_cross_metrics = None
    else:
        print("Extracting PhoBERT CLS embeddings for fit set...")
        phobert_fit = get_phobert_embeddings(fit_texts, phobert_seed42_dir)
        print(f"  Embedding shape: {phobert_fit.shape}")

        print("Extracting PhoBERT CLS embeddings for test set...")
        phobert_test = get_phobert_embeddings(test_texts, phobert_seed42_dir)

        print("Extracting PhoBERT CLS embeddings for VSMEC...")
        phobert_vsmec = get_phobert_embeddings(vsmec_texts, phobert_seed42_dir)

        # Combine features
        X_fit_combined = np.hstack([phobert_fit, topic_fit])
        X_test_combined = np.hstack([phobert_test, topic_test])
        X_vsmec_combined = np.hstack([phobert_vsmec, topic_vsmec])

        scaler_comb = StandardScaler()
        X_fit_comb = scaler_comb.fit_transform(X_fit_combined)
        X_test_comb = scaler_comb.transform(X_test_combined)
        X_vsmec_comb = scaler_comb.transform(X_vsmec_combined)

        clf_comb = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)
        clf_comb.fit(X_fit_comb, fit_labels)

        combined_in = clf_comb.predict(X_test_comb)
        combined_cross = clf_comb.predict(X_vsmec_comb)

        phobert_combined_in_metrics = compute_all_metrics(test_labels, combined_in)
        phobert_combined_cross_metrics = compute_all_metrics(vsmec_labels, combined_cross)

        print(f"\nPhoBERT+BERTopic In-domain: Acc={phobert_combined_in_metrics['accuracy']:.4f}, F1={phobert_combined_in_metrics['f1_score']:.4f}, F1-M={phobert_combined_in_metrics['f1_macro']:.4f}")
        print(f"PhoBERT+BERTopic Cross-domain: Acc={phobert_combined_cross_metrics['accuracy']:.4f}, F1={phobert_combined_cross_metrics['f1_score']:.4f}, F1-M={phobert_combined_cross_metrics['f1_macro']:.4f}")

    # ── Save results ──────────────────────────────────────────────────
    results = {
        "timestamp": datetime.now().isoformat(),
        "round": "round6",
        "dataset": {
            "train": len(train_df),
            "val": len(val_df),
            "test": len(test_df),
            "vsmec": len(vsmec_df),
        },
        "bertopic_only": {
            "in_domain": bertopic_in_metrics,
            "cross_domain": bertopic_cross_metrics,
        },
        "phobert_bertopic_combined": {
            "in_domain": phobert_combined_in_metrics,
            "cross_domain": phobert_combined_cross_metrics,
        } if phobert_combined_in_metrics else None,
    }

    output_file = OUTPUT_DIR / "bertopic_evaluation_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n✓ Results saved to: {output_file}")
    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
