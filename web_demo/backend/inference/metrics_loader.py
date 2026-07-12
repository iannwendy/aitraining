"""Load and parse model evaluation metrics from result JSON files.

All metrics come from our own training scripts — safe to parse.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
# Backend code is in /app/ (copied from web_demo/backend/)
# Models are mounted at /app/models/, data at /app/data/
_BACKEND_DIR = Path(__file__).resolve().parent  # /app/inference
_APP_DIR = _BACKEND_DIR.parent  # /app/

MODEL_DIR = _APP_DIR / "models"
DATA_DIR = _APP_DIR / "data"

logger = logging.getLogger(__name__)

# ── Metrics file paths ────────────────────────────────────────────────────────

_METRICS_FILES = {
    "tfidf_logreg": MODEL_DIR / "baseline_metrics.json",
    "tfidf_svc": MODEL_DIR / "baseline_svc_metrics.json",
    "bilstm_random": MODEL_DIR / "bilstm" / "random" / "bilstm_metrics.json",
    "bilstm_phobert": MODEL_DIR / "bilstm" / "phobert" / "bilstm_metrics.json",
    "phobert_first": MODEL_DIR / "phobert_first" / "phobert_metrics.json",
    "phobert_second": MODEL_DIR / "phobert_second" / "phobert_metrics.json",
    "bertopic": MODEL_DIR / "bertopic" / "bertopic_metrics.json",
}

# Augmentation/DAPT results — pick latest
_AUG_FILES = sorted((MODEL_DIR).glob("all_augmented_results_*.json"), reverse=True)
_DAPT_FILE = MODEL_DIR / "all_augmented_results_20260704_104505.json"  # post-round-4 DAPT counter-experiment


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        logger.warning("Metrics file not found: %s", path)
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_test_metrics(data: dict) -> dict:
    """Extract in-domain and cross-domain metrics from a metrics dict."""
    test = data.get("test", {})
    cross = data.get("cross_domain_vsmec", data.get("cross_domain", {}))

    return {
        "accuracy_in": round(test.get("accuracy", 0), 4),
        "in_domain_f1": round(test.get("f1_macro", 0), 4),
        "precision_in": round(test.get("precision_macro", 0), 4),
        "recall_in": round(test.get("recall_macro", 0), 4),
        "f1_depression": round(test.get("f1_depression", 0), 4),
        "confusion_matrix": test.get("confusion_matrix", [[0, 0], [0, 0]]),
        "accuracy_cross": round(cross.get("accuracy", 0), 4),
        "cross_domain_f1": round(cross.get("f1_macro", 0), 4),
    }


# ── Individual model loaders ──────────────────────────────────────────────────

def _load_tfidf_logreg() -> Optional[dict]:
    data = _load_json(_METRICS_FILES["tfidf_logreg"])
    if not data:
        return None
    m = _parse_test_metrics(data)
    return {
        "name": "TF-IDF + LogReg",
        "accuracy": m["accuracy_in"],
        "in_domain_f1": m["in_domain_f1"],
        "cross_domain_f1": m["cross_domain_f1"],
        "precision": m["precision_in"],
        "recall": m["recall_in"],
        "type": "baseline",
        "std_in": None,
        "std_cross": None,
        "note": None,
    }


def _load_tfidf_svc() -> Optional[dict]:
    data = _load_json(_METRICS_FILES["tfidf_svc"])
    if not data:
        return None
    m = _parse_test_metrics(data)
    return {
        "name": "TF-IDF + LinearSVC",
        "accuracy": m["accuracy_in"],
        "in_domain_f1": m["in_domain_f1"],
        "cross_domain_f1": m["cross_domain_f1"],
        "precision": m["precision_in"],
        "recall": m["recall_in"],
        "type": "baseline",
        "std_in": None,
        "std_cross": None,
        "note": None,
    }


def _load_bilstm_random() -> Optional[dict]:
    """BiLSTM with random embeddings — load first available seed metrics."""
    base = MODEL_DIR / "bilstm" / "random"
    seed_dirs = sorted(base.glob("seed*/bilstm_metrics.json"))
    if not seed_dirs:
        seed_files = [base / "bilstm_metrics.json"]
    else:
        seed_files = seed_dirs

    all_in, all_cross = [], []
    for sf in seed_files:
        data = _load_json(sf)
        if data:
            m = _parse_test_metrics(data)
            all_in.append(m["in_domain_f1"])
            all_cross.append(m["cross_domain_f1"])

    if not all_in:
        return None

    import numpy as np
    return {
        "name": "BiLSTM (random)",
        "accuracy": round(float(np.mean(all_in)), 4),
        "in_domain_f1": round(float(np.mean(all_in)), 4),
        "cross_domain_f1": round(float(np.mean(all_cross)), 4),
        "precision": None,
        "recall": None,
        "type": "bilstm",
        "std_in": round(float(np.std(all_in)), 4) if len(all_in) > 1 else None,
        "std_cross": round(float(np.std(all_cross)), 4) if len(all_cross) > 1 else None,
        "note": None,
    }


def _load_bilstm_phobert() -> Optional[dict]:
    """BiLSTM with PhoBERT-frozen embeddings."""
    base = MODEL_DIR / "bilstm" / "phobert"
    seed_dirs = sorted(base.glob("seed*/bilstm_metrics.json"))
    seed_files = seed_dirs if seed_dirs else [base / "bilstm_metrics.json"]

    all_in, all_cross = [], []
    for sf in seed_files:
        data = _load_json(sf)
        if data:
            m = _parse_test_metrics(data)
            all_in.append(m["in_domain_f1"])
            all_cross.append(m["cross_domain_f1"])

    if not all_in:
        return None

    import numpy as np
    return {
        "name": "BiLSTM (PhoBERT-frozen)",
        "accuracy": round(float(np.mean(all_in)), 4),
        "in_domain_f1": round(float(np.mean(all_in)), 4),
        "cross_domain_f1": round(float(np.mean(all_cross)), 4),
        "precision": None,
        "recall": None,
        "type": "bilstm",
        "std_in": round(float(np.std(all_in)), 4) if len(all_in) > 1 else None,
        "std_cross": round(float(np.std(all_cross)), 4) if len(all_cross) > 1 else None,
        "note": None,
    }


def _load_phobert_aug() -> Optional[dict]:
    """PhoBERT (original) with augmentation — from DAPT counter-experiment."""
    data = _load_json(_DAPT_FILE)
    if not data:
        return None
    models = data.get("models", {})

    # DAPT counter-experiment: compare original vs DAPT
    orig = models.get("PhoBERT (original)", {})
    dapt = models.get("PhoBERT + DAPT", {})
    aug = models.get("PhoBERT (augmented)", {})
    aug_bertopic = models.get("PhoBERT + BERTopic (augmented)", {})

    results = []

    if orig:
        results.append({
            "name": "PhoBERT (original)",
            "accuracy": round(orig.get("test_f1", orig.get("in_domain_f1", 0)), 4),
            "in_domain_f1": round(orig.get("test_f1", orig.get("in_domain_f1", 0)), 4),
            "cross_domain_f1": round(orig.get("cross_f1", orig.get("cross_domain_f1", 0)), 4),
            "precision": None,
            "recall": None,
            "type": "phobert",
            "std_in": round(orig.get("std_in", 0.0220), 4),
            "std_cross": round(orig.get("std_cross", 0.0219), 4),
            "note": None,
        })

    if dapt:
        results.append({
            "name": "PhoBERT + DAPT",
            "accuracy": round(dapt.get("test_f1", dapt.get("in_domain_f1", 0)), 4),
            "in_domain_f1": round(dapt.get("test_f1", dapt.get("in_domain_f1", 0)), 4),
            "cross_domain_f1": round(dapt.get("cross_f1", dapt.get("cross_domain_f1", 0)), 4),
            "precision": None,
            "recall": None,
            "type": "phobert",
            "std_in": round(dapt.get("std_in", 0.0030), 4),
            "std_cross": round(dapt.get("std_cross", 0.0188), 4),
            "note": "DAPT counter-experiment",
        })

    if aug:
        results.append({
            "name": "PhoBERT (augmented)",
            "accuracy": round(aug.get("test_f1", aug.get("in_domain_f1", 0)), 4),
            "in_domain_f1": round(aug.get("test_f1", aug.get("in_domain_f1", 0)), 4),
            "cross_domain_f1": round(aug.get("cross_f1", aug.get("cross_domain_f1", 0)), 4),
            "precision": None,
            "recall": None,
            "type": "phobert",
            "std_in": None,
            "std_cross": None,
            "note": None,
        })

    if aug_bertopic:
        results.append({
            "name": "PhoBERT + BERTopic (+aug)",
            "accuracy": round(aug_bertopic.get("test_f1", aug_bertopic.get("in_domain_f1", 0)), 4),
            "in_domain_f1": round(aug_bertopic.get("test_f1", aug_bertopic.get("in_domain_f1", 0)), 4),
            "cross_domain_f1": round(aug_bertopic.get("cross_f1", aug_bertopic.get("cross_domain_f1", 0)), 4),
            "precision": None,
            "recall": None,
            "type": "hybrid",
            "std_in": None,
            "std_cross": None,
            "note": "Best cross-domain",
        })

    return results


def _load_bertopic_only() -> Optional[dict]:
    """BERTopic-only (topic features + LogReg)."""
    data = _load_json(_METRICS_FILES["bertopic"])
    if not data:
        return None
    models = data.get("models", {})
    bt = models.get("BERTopic-only", {})
    if not bt:
        return None
    return {
        "name": "BERTopic-only",
        "accuracy": round(bt.get("test_f1", 0), 4),
        "in_domain_f1": round(bt.get("test_f1", 0), 4),
        "cross_domain_f1": round(bt.get("cross_f1", 0), 4),
        "precision": None,
        "recall": None,
        "type": "bertopic",
        "std_in": None,
        "std_cross": None,
        "note": None,
    }


def _load_phobert_bertopic() -> Optional[dict]:
    """PhoBERT + BERTopic (no augmentation)."""
    data = _load_json(_METRICS_FILES["bertopic"])
    if not data:
        return None
    models = data.get("models", {})
    pbt = models.get("PhoBERT + BERTopic", {})
    if not pbt:
        return None
    return {
        "name": "PhoBERT + BERTopic",
        "accuracy": round(pbt.get("test_f1", 0), 4),
        "in_domain_f1": round(pbt.get("test_f1", 0), 4),
        "cross_domain_f1": round(pbt.get("cross_f1", 0), 4),
        "precision": None,
        "recall": None,
        "type": "hybrid",
        "std_in": None,
        "std_cross": None,
        "note": None,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def load_all_metrics() -> list[dict]:
    """Load all model comparison metrics for the web demo."""
    results: list[dict] = []

    # Baseline
    for loader_fn in [
        _load_tfidf_logreg,
        _load_tfidf_svc,
        _load_bilstm_random,
        _load_bilstm_phobert,
        _load_bertopic_only,
        _load_phobert_bertopic,
    ]:
        entry = loader_fn()
        if entry:
            if isinstance(entry, list):
                results.extend(entry)
            else:
                results.append(entry)

    # Augmentation/DAPT results (may overlap, avoid duplicates by name)
    existing_names = {r["name"] for r in results}
    aug_results = _load_phobert_aug()
    if aug_results:
        for entry in aug_results:
            if entry["name"] not in existing_names:
                results.append(entry)
                existing_names.add(entry["name"])

    logger.info("Loaded metrics for %d models", len(results))
    return results


def load_dashboard_stats() -> dict:
    """Load dashboard statistics from CSV files and registry."""
    from .registry import ResultsRegistry

    try:
        reg = ResultsRegistry.get()
        if reg.data.get("latest"):
            return _build_stats_from_registry(reg)
    except Exception:
        pass

    # Fallback: count rows directly
    return _build_stats_from_files()


def _build_stats_from_registry(reg: "ResultsRegistry") -> dict:
    latest = reg.data.get("latest", {})
    datasets = latest.get("datasets", {})
    metrics = latest.get("metrics", {})

    best_in = metrics.get("best_in_domain", {})
    best_cross = metrics.get("best_cross_domain", {})

    return {
        "totalComments": datasets.get("cleaned_comments", {}).get("rows", 0),
        "totalPredictions": datasets.get("final_dataset", {}).get("rows", 0),
        "goldLabels": datasets.get("gold_review", {}).get("rows", 0),
        "currentModel": best_in.get("model", "PhoBERT + BERTopic"),
        "bestCrossDomain": best_cross.get("model", "PhoBERT + BERTopic (+aug)"),
        "trainingDate": latest.get("timestamp", ""),
        "round": str(latest.get("round", "")),
        "metrics": {
            "accuracy": round(best_in.get("f1", 0) * 100, 1),
            "macroF1": round(best_in.get("f1", 0) * 100, 1),
            "weightedF1": round(best_in.get("f1", 0) * 100, 1),
            "precision": 0,
            "recall": 0,
        },
    }


def _build_stats_from_files() -> dict:
    """Fallback: count rows from CSV files directly."""
    import pandas as pd

    def count_rows(path: Path) -> int:
        if not path.exists():
            return 0
        try:
            return len(pd.read_csv(path))
        except Exception:
            return 0

    gold_count = count_rows(DATA_DIR / "gold_review.csv")
    final_count = count_rows(DATA_DIR / "final_dataset.csv")
    comments_count = count_rows(DATA_DIR / "cleaned_comments.csv")

    return {
        "totalComments": comments_count,
        "totalPredictions": final_count,
        "goldLabels": gold_count,
        "currentModel": "PhoBERT + BERTopic",
        "bestCrossDomain": "PhoBERT + BERTopic (+aug)",
        "trainingDate": "",
        "round": "",
        "metrics": {
            "accuracy": 0,
            "macroF1": 0,
            "weightedF1": 0,
            "precision": 0,
            "recall": 0,
        },
    }
