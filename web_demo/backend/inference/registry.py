"""Results Registry — enables hot-reload of metrics after new training rounds.

The registry is a JSON file written by training scripts after each round.
Backend reads it at startup and can refresh on demand via POST /api/models/refresh.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

_BACKEND_DIR = Path(__file__).resolve().parent  # /app/inference
_APP_DIR = _BACKEND_DIR.parent  # /app/

REGISTRY_FILE = _APP_DIR / "models" / "results_registry.json"

logger = logging.getLogger(__name__)


class ResultsRegistry:
    """In-memory cache of the results registry file."""

    _instance: Optional["ResultsRegistry"] = None

    def __init__(self) -> None:
        self.data: dict = {}
        self.last_refresh: Optional[str] = None
        self.status: str = "idle"
        self.load()

    @classmethod
    def get(cls) -> "ResultsRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self) -> None:
        """Reload from disk."""
        self.status = "loading"
        try:
            if REGISTRY_FILE.exists():
                with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                self.last_refresh = datetime.now().isoformat()
                self.status = "idle"
                logger.info("Registry loaded from %s", REGISTRY_FILE)
            else:
                self.data = {}
                self.status = "idle"
                logger.info("No registry file found at %s", REGISTRY_FILE)
        except Exception as e:
            self.status = "error"
            logger.error("Failed to load registry: %s", e)

    def refresh(self) -> dict:
        """Trigger a reload from disk."""
        self.load()
        return {
            "status": self.status,
            "last_refresh": self.last_refresh,
            "round": self.data.get("latest", {}).get("round", None),
            "model_count": len(self.data.get("history", [])) + (1 if self.data.get("latest") else 0),
        }

    def get_status(self) -> dict:
        return {
            "status": self.status,
            "last_refresh": self.last_refresh,
            "round": self.data.get("latest", {}).get("round", None),
        }


def init_default_registry() -> None:
    """Create a default registry if it doesn't exist yet."""
    if REGISTRY_FILE.exists():
        return

    from .metrics_loader import load_all_metrics, load_dashboard_stats

    try:
        stats = load_dashboard_stats()
        metrics = load_all_metrics()

        # Find best models
        best_in = max(metrics, key=lambda m: m.get("in_domain_f1", 0), default=None)
        best_cross = max(metrics, key=lambda m: m.get("cross_domain_f1", 0), default=None)

        registry = {
            "latest": {
                "round": 5,
                "timestamp": datetime.now().isoformat(),
                "datasets": {
                    "cleaned_comments": {
                        "rows": stats.get("totalComments", 0),
                        "source": "data/cleaned_comments.csv",
                    },
                    "final_dataset": {
                        "rows": stats.get("totalPredictions", 0),
                        "source": "data/final_dataset.csv",
                    },
                    "gold_review": {
                        "rows": stats.get("goldLabels", 0),
                        "source": "data/gold_review.csv",
                    },
                },
                "metrics": {
                    "best_in_domain": {
                        "model": best_in.get("name", "PhoBERT + BERTopic") if best_in else "PhoBERT + BERTopic",
                        "f1": best_in.get("in_domain_f1", 0) if best_in else 0,
                    },
                    "best_cross_domain": {
                        "model": best_cross.get("name", "PhoBERT + BERTopic (+aug)") if best_cross else "PhoBERT + BERTopic (+aug)",
                        "f1": best_cross.get("cross_domain_f1", 0) if best_cross else 0,
                    },
                    "all_models": metrics,
                },
                "model_paths": {
                    "best": "models/round5_predictions/best_model/",
                    "bertopic": "models/bertopic/bertopic_model.pkl",
                    "tfidf_logreg": "models/tfidf_logreg.joblib",
                    "tfidf_svc": "models/tfidf_svc.joblib",
                },
            },
            "history": [],
        }

        REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)
        logger.info("Created default registry at %s", REGISTRY_FILE)
    except Exception as e:
        logger.error("Failed to create default registry: %s", e)


def update_registry(round_name: str, metrics: dict, model_paths: dict, datasets: dict) -> None:
    """Write a new snapshot to the registry (called by training scripts)."""
    existing: dict = {"latest": {}, "history": []}
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if "latest" in existing:
                history = existing.get("history", [])
                history.insert(0, existing["latest"])
                existing["history"] = history[:10]  # Keep last 10 rounds
        except Exception:
            pass

    existing["latest"] = {
        "round": round_name,
        "timestamp": datetime.now().isoformat(),
        "datasets": datasets,
        "metrics": metrics,
        "model_paths": model_paths,
    }

    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    logger.info("Updated registry with round %s", round_name)
