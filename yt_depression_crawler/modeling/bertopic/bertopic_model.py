"""BERTopic topic modeling on corpus_text_all (316K documents).

Unsupervised topic discovery - no labels needed. Outputs:
1. Topic model (pickle) for later use
2. corpus_with_topics.csv (every sentence + its assigned topic)
3. Metrics report JSON

The topic assignments serve dual purpose:
- Input feature for "PhoBERT + BERTopic" model (Phase 3)
- Topic distribution description for thesis/report
"""

from __future__ import annotations

import json
import logging
import os
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from yt_depression_crawler.core.config import (
    BERTOPIC_CALCULATE_PROBABILITIES,
    BERTOPIC_EMBEDDING_MODEL,
    BERTOPIC_EMBEDDINGS_FILE,
    BERTOPIC_HDBSCAN_MIN_CLUSTER_SIZE,
    BERTOPIC_HDBSCAN_MIN_SAMPLES,
    BERTOPIC_METRICS_FILE,
    BERTOPIC_MIN_TOPIC_SIZE,
    BERTOPIC_MODEL_DIR,
    BERTOPIC_MODEL_FILE,
    BERTOPIC_N_TOPICS,
    BERTOPIC_REPORT_FILE,
    BERTOPIC_TOP_N_WORDS,
    BERTOPIC_TOPICS_FILE,
    BERTOPIC_UMAP_MIN_DIST,
    BERTOPIC_UMAP_N_NEIGHBORS,
    BERTOPIC_VISUALIZATION_FILE,
    ensure_directories,
)

logger = logging.getLogger(__name__)

# --- Corpus path (from unified pipeline) ---
CORPUS_FILE = Path(__file__).resolve().parents[3] / "data_unified" / "corpus_text_all.csv"


def load_corpus(corpus_path: Path = CORPUS_FILE) -> pd.DataFrame:
    """Load and lightly preprocess corpus_text_all."""
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus not found: {corpus_path}. Run build_unified.py first.")

    df = pd.read_csv(corpus_path, dtype=str).fillna("")
    df["text"] = df["text"].str.strip()
    df = df[df["text"].str.len() >= 10]  # Skip very short fragments
    df = df.reset_index(drop=True)
    logger.info("Loaded corpus: %d rows", len(df))
    return df


def get_embedding_model(model_name: str = BERTOPIC_EMBEDDING_MODEL) -> SentenceTransformer:
    """Load sentence transformer for multilingual embeddings."""
    logger.info("Loading embedding model: %s", model_name)
    return SentenceTransformer(model_name)


def compute_embeddings(
    texts: list[str],
    model: SentenceTransformer,
    batch_size: int = 256,
    show_progress: bool = True,
) -> np.ndarray:
    """Compute embeddings for all texts using batching for memory efficiency."""
    logger.info("Computing embeddings for %d texts (batch_size=%d)", len(texts), batch_size)
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        normalize_embeddings=True,  # L2 normalize for better clustering
    )
    logger.info("Embeddings shape: %s", embeddings.shape)
    return embeddings


def build_topic_model(
    embeddings: np.ndarray,
    texts: list[str],
    min_topic_size: int = BERTOPIC_MIN_TOPIC_SIZE,
    n_topics: Any = BERTOPIC_N_TOPICS,
    umap_n_neighbors: int = BERTOPIC_UMAP_N_NEIGHBORS,
    umap_min_dist: float = BERTOPIC_UMAP_MIN_DIST,
    hdbscan_min_cluster_size: int = BERTOPIC_HDBSCAN_MIN_CLUSTER_SIZE,
    hdbscan_min_samples: int = BERTOPIC_HDBSCAN_MIN_SAMPLES,
    calculate_probabilities: bool = BERTOPIC_CALCULATE_PROBABILITIES,
    top_n_words: int = BERTOPIC_TOP_N_WORDS,
) -> Any:
    """Build BERTopic model with UMAP + HDBSCAN pipeline."""
    from bertopic import BERTopic
    from bertopic.cluster import BaseCluster
    from hdbscan import HDBSCAN
    from umap import UMAP

    logger.info("Building BERTopic model with %d documents", len(texts))

    # UMAP reducer
    umap_model = UMAP(
        n_neighbors=umap_n_neighbors,
        min_dist=umap_min_dist,
        n_components=5,
        metric="cosine",
        random_state=42,
        low_memory=True,
    )

    # HDBSCAN clusterer
    hdbscan_model = HDBSCAN(
        min_cluster_size=hdbscan_min_cluster_size,
        min_samples=hdbscan_min_samples,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )

    # Build BERTopic
    topic_model = BERTopic(
        embedding_model=None,  # We provide pre-computed embeddings
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        calculate_probabilities=calculate_probabilities,
        top_n_words=top_n_words,
        verbose=True,
    )

    # Fit with pre-computed embeddings
    logger.info("Fitting BERTopic (this may take 10-30 min for 316K docs)...")
    topics, _ = topic_model.fit_transform(texts, embeddings)
    logger.info("BERTopic fitted. Number of topics discovered: %d", topic_model.get_topic_freq().shape[0])

    return topic_model


def assign_topics_to_corpus(
    topic_model: Any,
    texts: list[str],
    df: pd.DataFrame,
    embeddings: np.ndarray | None = None,
) -> pd.DataFrame:
    """Assign topic IDs and get topic info for every document."""
    logger.info("Assigning topics to %d documents...", len(texts))

    # Get topic assignments - pass embeddings if available
    if embeddings is not None:
        topics, _ = topic_model.transform(texts, embeddings=embeddings)
    else:
        topics, _ = topic_model.transform(texts)

    df = df.copy()
    df["topic_id"] = topics

    # Get topic info
    topic_info = topic_model.get_topic_info()
    topic_freq = topic_model.get_topic_freq()

    # Add topic label (keyword-based description)
    df["topic_label"] = df["topic_id"].apply(
        lambda tid: _make_topic_label(topic_model, tid)
    )

    logger.info("Topic assignment complete. Topics range: %d to %d",
                df["topic_id"].min(), df["topic_id"].max())
    return df


def _make_topic_label(topic_model: Any, topic_id: int) -> str:
    """Create a human-readable label from top words of a topic."""
    if topic_id == -1:
        return "outlier"
    try:
        words = topic_model.get_topic(topic_id)
        if words:
            top_words = [w for w, _ in words[:5]]
            return " | ".join(top_words)
        return f"topic_{topic_id}"
    except Exception:
        return f"topic_{topic_id}"


def build_topic_summary(topic_model: Any) -> dict:
    """Build summary statistics for all topics."""
    topic_info = topic_model.get_topic_info()
    summaries = []

    for _, row in topic_info.iterrows():
        topic_id = int(row["Topic"])
        count = int(row["Count"])
        name = row["Name"]

        # Get top words
        words_data = topic_model.get_topic(topic_id)
        top_words = []
        if words_data:
            for word, score in words_data[:10]:
                top_words.append({"word": word, "score": round(float(score), 4)})

        summaries.append({
            "topic_id": topic_id,
            "name": name,
            "document_count": count,
            "percentage": round(count / topic_info["Count"].sum() * 100, 2),
            "top_words": top_words,
        })

    return summaries


def save_model_artifacts(
    topic_model: Any,
    df_with_topics: pd.DataFrame,
    embeddings: np.ndarray | None,
    metrics: dict,
    summary: list[dict],
) -> dict:
    """Save all BERTopic artifacts to disk."""
    ensure_directories()

    # Save topic model
    BERTOPIC_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(BERTOPIC_MODEL_FILE, "wb") as f:
        pickle.dump(topic_model, f)
    logger.info("Saved BERTopic model to %s", BERTOPIC_MODEL_FILE)

    # Save corpus with topics
    df_with_topics.to_csv(BERTOPIC_TOPICS_FILE, index=False, encoding="utf-8-sig")
    logger.info("Saved corpus_with_topics to %s (%d rows)", BERTOPIC_TOPICS_FILE, len(df_with_topics))

    # Save embeddings (optional - large file)
    if embeddings is not None:
        np.save(BERTOPIC_EMBEDDINGS_FILE, embeddings)
        logger.info("Saved embeddings to %s", BERTOPIC_EMBEDDINGS_FILE)

    # Save metrics
    BERTOPIC_METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BERTOPIC_METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    logger.info("Saved metrics to %s", BERTOPIC_METRICS_FILE)

    return {
        "model_file": str(BERTOPIC_MODEL_FILE),
        "topics_file": str(BERTOPIC_TOPICS_FILE),
        "embeddings_file": str(BERTOPIC_EMBEDDINGS_FILE),
        "metrics_file": str(BERTOPIC_METRICS_FILE),
    }


def generate_visualization(topic_model: Any, output_path: Path = BERTOPIC_VISUALIZATION_FILE) -> str:
    """Generate and save interactive topic visualizations."""
    logger.info("Generating topic visualizations...")

    # Barchart of top topics
    fig = topic_model.visualize_barchart(top_n_topics=20)
    if fig:
        fig.write_html(str(output_path))
        logger.info("Saved topic barchart to %s", output_path)

    # Hierarchical visualization
    hierarchy_path = output_path.parent / "topic_hierarchy.html"
    fig_hier = topic_model.visualize_hierarchy()
    if fig_hier:
        fig_hier.write_html(str(hierarchy_path))
        logger.info("Saved topic hierarchy to %s", hierarchy_path)

    return str(output_path)


def train_bertopic(
    corpus_path: Path = CORPUS_FILE,
    embedding_model_name: str = BERTOPIC_EMBEDDING_MODEL,
    min_topic_size: int = BERTOPIC_MIN_TOPIC_SIZE,
    n_topics: Any = BERTOPIC_N_TOPICS,
    compute_embeddings_only: bool = False,
    use_cached_embeddings: bool = True,
) -> dict:
    """Main entry point: train BERTopic on corpus_text_all.

    Args:
        corpus_path: Path to corpus_text_all.csv
        embedding_model_name: SentenceTransformer model for embeddings
        min_topic_size: Minimum documents per topic
        n_topics: "auto" or int for max topics
        compute_embeddings_only: If True, only compute and save embeddings
        use_cached_embeddings: If True and embeddings exist, load from disk

    Returns:
        dict with training metrics and file paths
    """
    logger.info("=" * 60)
    logger.info("BERTopic Training Pipeline")
    logger.info("Corpus: %s", corpus_path)
    logger.info("=" * 60)

    # 1. Load corpus
    df = load_corpus(corpus_path)
    texts = df["text"].tolist()
    original_count = len(df)

    # 2. Compute or load embeddings
    embeddings = None
    if use_cached_embeddings and BERTOPIC_EMBEDDINGS_FILE.exists():
        logger.info("Loading cached embeddings from %s", BERTOPIC_EMBEDDINGS_FILE)
        embeddings = np.load(BERTOPIC_EMBEDDINGS_FILE)
        if embeddings.shape[0] != len(texts):
            logger.warning("Cached embeddings size mismatch. Recomputing...")
            embeddings = None

    if embeddings is None:
        model = get_embedding_model(embedding_model_name)
        embeddings = compute_embeddings(texts, model)

        if compute_embeddings_only:
            np.save(BERTOPIC_EMBEDDINGS_FILE, embeddings)
            return {
                "status": "embeddings_computed",
                "embeddings_file": str(BERTOPIC_EMBEDDINGS_FILE),
                "num_documents": len(texts),
                "embedding_dim": int(embeddings.shape[1]),
            }

    # 3. Build topic model
    topic_model = build_topic_model(
        embeddings=embeddings,
        texts=texts,
        min_topic_size=min_topic_size,
        n_topics=n_topics,
    )

    # 4. Assign topics to corpus
    df_with_topics = assign_topics_to_corpus(topic_model, texts, df, embeddings=embeddings)

    # 5. Build summary
    topic_summary = build_topic_summary(topic_model)

    # 6. Compute metrics
    topic_freq = topic_model.get_topic_freq()
    n_topics = topic_freq.shape[0]
    n_outliers = int(topic_freq[topic_freq["Topic"] == -1]["Count"].sum())
    n_docs = int(topic_freq["Count"].sum())

    metrics = {
        "corpus": {
            "original_rows": original_count,
            "processed_rows": len(texts),
            "columns": list(df.columns),
        },
        "model": {
            "embedding_model": embedding_model_name,
            "embedding_dim": int(embeddings.shape[1]),
            "min_topic_size": min_topic_size,
            "n_topics_discovered": n_topics,
            "n_outlier_documents": n_outliers,
            "outlier_percentage": round(n_outliers / n_docs * 100, 2) if n_docs > 0 else 0,
        },
        "topic_distribution": topic_summary[:50],  # Top 50 topics
        "source_breakdown": df_with_topics.groupby(["source", "topic_id"]).size().to_dict(),
    }

    # 7. Save artifacts
    files = save_model_artifacts(topic_model, df_with_topics, embeddings, metrics, topic_summary)

    # 8. Generate visualizations (optional)
    viz_path = generate_visualization(topic_model)
    if viz_path:
        metrics["visualization_file"] = viz_path

    metrics["files"] = files
    metrics["status"] = "completed"

    # 9. Save to global report
    _merge_report(BERTOPIC_REPORT_FILE, {"bertopic": metrics})

    logger.info("=" * 60)
    logger.info("BERTopic training COMPLETE")
    logger.info("  Topics discovered: %d", n_topics)
    logger.info("  Outliers: %d (%.1f%%)", n_outliers, n_outliers / n_docs * 100 if n_docs > 0 else 0)
    logger.info("  Output: %s", BERTOPIC_TOPICS_FILE)
    logger.info("=" * 60)

    return metrics


def _merge_report(report_file: Path, payload: dict) -> None:
    """Merge payload into existing report JSON."""
    report_file.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if report_file.exists() and report_file.stat().st_size > 0:
        try:
            existing = json.loads(report_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    existing.update(payload)
    report_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")


# =============================================================================
# Inference: assign topics to new texts (for PhoBERT + BERTopic pipeline)
# =============================================================================

def load_trained_model(model_path: Path = BERTOPIC_MODEL_FILE) -> Any:
    """Load a pre-trained BERTopic model from disk."""
    if not model_path.exists():
        raise FileNotFoundError(f"BERTopic model not found: {model_path}")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    logger.info("Loaded BERTopic model from %s", model_path)
    return model


def predict_topics(
    texts: list[str],
    topic_model: Any | None = None,
    model_path: Path = BERTOPIC_MODEL_FILE,
) -> list[int]:
    """Assign topic IDs to new texts using a trained model."""
    if topic_model is None:
        topic_model = load_trained_model(model_path)

    topics, _ = topic_model.transform(texts)
    return topics


def get_topic_features(
    texts: list[str],
    topic_model: Any | None = None,
    model_path: Path = BERTOPIC_MODEL_FILE,
) -> list[dict]:
    """Get rich topic features for each text (for PhoBERT + BERTopic model).

    Returns list of dicts with:
    - topic_id: int
    - topic_label: str (top words)
    - topic_probability: float (if available)
    """
    if topic_model is None:
        topic_model = load_trained_model(model_path)

    topics, probs = topic_model.transform(texts)

    results = []
    for i, (tid, prob) in enumerate(zip(topics, probs)):
        label = _make_topic_label(topic_model, tid)
        results.append({
            "topic_id": int(tid),
            "topic_label": label,
            "topic_probability": float(prob) if prob is not None else 0.0,
        })
    return results


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # Check for CLI args
    if len(sys.argv) > 1 and sys.argv[1] == "--embeddings-only":
        result = train_bertopic(compute_embeddings_only=True)
    else:
        result = train_bertopic()

    print(json.dumps(result, ensure_ascii=False, indent=2))
