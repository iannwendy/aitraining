"""Inference engines for web demo."""
from .phobert_engine import PhoBertEngine, predict_text
from .bertopic_engine import BERTopicEngine, get_topic_for_text
from .metrics_loader import load_all_metrics, load_dashboard_stats
from .registry import ResultsRegistry, update_registry, init_default_registry

__all__ = [
    "PhoBertEngine",
    "predict_text",
    "BERTopicEngine",
    "get_topic_for_text",
    "load_all_metrics",
    "load_dashboard_stats",
    "ResultsRegistry",
    "update_registry",
    "init_default_registry",
]
