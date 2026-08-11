"""BERTopic inference engine for topic assignment.

Loads the trained BERTopic model and assigns topics to input texts.
Falls back to keyword-based matching if the pickled model is incompatible
(which happens across bertopic/sklearn version bumps).
"""

from __future__ import annotations

import json
import logging
import pickle
import re
from collections import Counter
from pathlib import Path
from typing import Optional

import numpy as np

# Disable proxies
import os
for _var in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(_var, None)

# ── Paths ─────────────────────────────────────────────────────────────────────
# Backend code is in /app/ (copied from web_demo/backend/)
# Models are mounted at /app/models/
_BACKEND_DIR = Path(__file__).resolve().parent  # /app/inference
_APP_DIR = _BACKEND_DIR.parent  # /app/

BERTOPIC_MODEL_FILE = _APP_DIR / "models" / "bertopic" / "bertopic_model.pkl"
BERTOPIC_METRICS_FILE = _APP_DIR / "models" / "bertopic" / "bertopic_metrics.json"

logger = logging.getLogger(__name__)

# ── Topic label cache ─────────────────────────────────────────────────────────

_TOPIC_LABELS: Optional[dict[int, str]] = None
_TOPIC_METRICS: Optional[dict] = None
_TOPIC_KEYWORDS: Optional[dict[int, list[str]]] = None


def _load_topic_labels() -> dict[int, str]:
    """Load topic ID → label mapping from BERTopic metrics."""
    global _TOPIC_LABELS
    if _TOPIC_LABELS is not None:
        return _TOPIC_LABELS

    _TOPIC_LABELS = {}
    if BERTOPIC_METRICS_FILE.exists():
        with open(BERTOPIC_METRICS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for entry in data.get("topic_distribution", []):
            tid = entry.get("topic_id", 0)
            words = entry.get("top_words", [])
            if words:
                label = " | ".join([w["word"] for w in words[:5]])
            else:
                label = f"topic_{tid}"
            _TOPIC_LABELS[tid] = label
    return _TOPIC_LABELS


def _load_topic_keywords() -> dict[int, list[str]]:
    """Load topic ID → top keywords for keyword matching."""
    global _TOPIC_KEYWORDS
    if _TOPIC_KEYWORDS is not None:
        return _TOPIC_KEYWORDS

    _TOPIC_KEYWORDS = {}
    if BERTOPIC_METRICS_FILE.exists():
        with open(BERTOPIC_METRICS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for entry in data.get("topic_distribution", []):
            tid = entry.get("topic_id", 0)
            words = [w["word"] for w in entry.get("top_words", [])]
            _TOPIC_KEYWORDS[tid] = words
    return _TOPIC_KEYWORDS


def _load_topic_metrics() -> dict:
    """Load full BERTopic metrics."""
    global _TOPIC_METRICS
    if _TOPIC_METRICS is not None:
        return _TOPIC_METRICS
    _TOPIC_METRICS = {}
    if BERTOPIC_METRICS_FILE.exists():
        with open(BERTOPIC_METRICS_FILE, "r", encoding="utf-8") as f:
            _TOPIC_METRICS = json.load(f)
    return _TOPIC_METRICS


# ── Keyword-based topic matcher ───────────────────────────────────────────────

def _strip_diacritics(text: str) -> str:
    """Strip Vietnamese diacritics for matching against BERTopic's no-diacritic keywords."""
    import unicodedata
    text = unicodedata.normalize("NFD", text)
    # Combine-diacritic marks include circumflexes, tones; keep 'đ'/'Đ' separately
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D")


def _tokenize(text: str) -> list[str]:
    """Tokenize text into no-diacritic lowercase word tokens.

    BERTopic was trained on Vietnamese text without diacritics, so we strip
    diacritics before matching against topic keywords.
    """
    if not text:
        return []
    text = str(text).lower()
    # Try Vietnamese word tokenization first for better recall
    try:
        from underthesea import word_tokenize
        text = word_tokenize(text, format="text")
    except Exception:
        pass
    # Strip diacritics to align with topic keywords
    text = _strip_diacritics(text)
    tokens = re.findall(r"[a-z0-9]+", text)
    return [t for t in tokens if len(t) >= 2]


def _keyword_score(text_tokens: list[str], topic_keywords: list[str]) -> float:
    """Score a text against a topic's keywords (weighted overlap, position-aware)."""
    if not text_tokens or not topic_keywords:
        return 0.0
    text_counter = Counter(text_tokens)

    score = 0.0
    for word, t_count in text_counter.items():
        if word in topic_keywords:
            idx = topic_keywords.index(word)
            # Earlier keywords (higher score) get more weight
            weight = 1.0 / (1 + idx * 0.05)
            score += t_count * weight

    # Length normalization
    if len(text_tokens) > 0:
        score = score / (1 + 0.1 * len(text_tokens))
    return score


# ── Engine ────────────────────────────────────────────────────────────────────

class BERTopicEngine:
    """Singleton BERTopic inference engine.

    Primary: pickled BERTopic model + sentence-transformer embedder.
    Fallback: keyword-based matching against topic top-words.
    """

    _instance: Optional["BERTopicEngine"] = None

    def __init__(self) -> None:
        self.topic_model = None
        self.embedder = None
        self._model_error: Optional[str] = None
        self._using_fallback = False

        # Try to load the full pickled model
        if BERTOPIC_MODEL_FILE.exists():
            try:
                logger.info("Loading BERTopic model from %s", BERTOPIC_MODEL_FILE)
                with open(BERTOPIC_MODEL_FILE, "rb") as f:
                    self.topic_model = pickle.load(f)
                logger.info("BERTopic full model loaded")
            except Exception as e:
                self._model_error = str(e)
                logger.warning(
                    "BERTopic pickle load failed (%s) — using keyword fallback",
                    e,
                )
                self._using_fallback = True

        # Load topic labels and keywords
        self.topic_labels = _load_topic_labels()
        self.topic_keywords = _load_topic_keywords()
        logger.info(
            "BERTopic engine ready (%d topics, mode=%s)",
            len(self.topic_labels),
            "fallback" if self._using_fallback else "full",
        )

    @classmethod
    def get_instance(cls) -> "BERTopicEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _ensure_full_model(self) -> bool:
        """Lazy-load the embedder + verify model. Returns True if usable."""
        if self.topic_model is None:
            return False
        if self.embedder is None:
            try:
                logger.info("Loading sentence-transformer embedder...")
                from sentence_transformers import SentenceTransformer
                self.embedder = SentenceTransformer(
                    "paraphrase-multilingual-MiniLM-L12-v2"
                )
            except Exception as e:
                logger.warning("Embedder load failed: %s", e)
                return False
        return True

    def predict_topic(self, text: str) -> dict:
        """Assign a topic to a single text."""
        result = self.predict_topics([text])
        return result[0] if result else {"topic_id": -1, "topic_name": None, "probability": 0.0}

    def predict_topics(self, texts: list[str]) -> list[dict]:
        """Assign topics to a batch of texts."""
        if not texts:
            return []

        # Try full model first
        if self._ensure_full_model():
            try:
                embeddings = self.embedder.encode(
                    [str(t) for t in texts],
                    show_progress_bar=False,
                    batch_size=64,
                    normalize_embeddings=True,
                )
                topics, probs = self.topic_model.transform(texts, embeddings=embeddings)
                return self._format_results(topics, probs)
            except Exception as e:
                logger.warning("Full model predict failed: %s — fallback to keyword", e)

        # Fallback: keyword-based matching
        return self._predict_topics_keyword(texts)

    def _format_results(self, topics, probs) -> list[dict]:
        results = []
        for tid, prob in zip(topics, probs):
            if isinstance(prob, np.ndarray):
                prob = float(np.max(prob))
            elif not isinstance(prob, float):
                prob = float(prob)
            label = self.topic_labels.get(int(tid), f"topic_{tid}")
            results.append({
                "topic_id": int(tid),
                "topic_name": label,
                "probability": round(prob, 4),
            })
        return results

    def _predict_topics_keyword(self, texts: list[str]) -> list[dict]:
        """Keyword-based topic matching fallback using top_words of each topic."""
        results = []
        # Filter out outlier topic (-1)
        valid_topics = [(tid, kws) for tid, kws in self.topic_keywords.items() if tid != -1]

        for text in texts:
            tokens = _tokenize(text)
            if not tokens:
                results.append({"topic_id": -1, "topic_name": None, "probability": 0.0})
                continue

            # Score each topic and pick the best one
            best_topic_id = -1
            best_score = 0.0
            for tid, kws in valid_topics:
                s = _keyword_score(tokens, kws)
                if s > best_score:
                    best_score = s
                    best_topic_id = tid

            if best_topic_id == -1 or best_score < 0.05:
                results.append({"topic_id": -1, "topic_name": None, "probability": 0.0})
            else:
                label = self.topic_labels.get(best_topic_id, f"topic_{best_topic_id}")
                # Normalize probability (0.05 → 0.3, 1.0 → 0.95)
                prob = min(0.95, 0.3 + best_score * 0.7)
                results.append({
                    "topic_id": int(best_topic_id),
                    "topic_name": label,
                    "probability": round(prob, 4),
                })
        return results

    def get_top_topics(self, limit: int = 20) -> list[dict]:
        """Return the top N most frequent meaningful topics (excluding -1 outliers)."""
        metrics = _load_topic_metrics()
        distribution = metrics.get("topic_distribution", [])

        meaningful = [t for t in distribution if t["topic_id"] != -1]
        meaningful.sort(key=lambda x: x["document_count"], reverse=True)
        top = meaningful[:limit]

        results = []
        total = sum(t["document_count"] for t in meaningful)
        for entry in top:
            tid = entry["topic_id"]
            words = [w["word"] for w in entry.get("top_words", [])[:5]]
            results.append({
                "id": tid,
                "name": self.topic_labels.get(tid, f"topic_{tid}"),
                "keywords": words,
                "count": entry["document_count"],
                "percentage": round(entry["document_count"] / total * 100, 2) if total > 0 else 0,
                "examples": [],
            })
        return results

    def reload(self) -> None:
        """Hot-reload the model."""
        global _TOPIC_LABELS, _TOPIC_METRICS, _TOPIC_KEYWORDS
        _TOPIC_LABELS = None
        _TOPIC_METRICS = None
        _TOPIC_KEYWORDS = None
        BERTopicEngine._instance = None
        BERTopicEngine._instance = BERTopicEngine()


# ── Module-level convenience ──────────────────────────────────────────────────

_engine: Optional[BERTopicEngine] = None


def get_engine() -> BERTopicEngine:
    global _engine
    if _engine is None:
        _engine = BERTopicEngine.get_instance()
    return _engine


def get_topic_for_text(text: str) -> dict:
    """Convenience: get topic for a single text."""
    return get_engine().predict_topic(text)


def get_topics(limit: int = 20) -> list[dict]:
    """Convenience: get top N topics."""
    return get_engine().get_topics(limit=limit)
