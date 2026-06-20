"""Report utilities for BERTopic results.

Generates structured analysis reports for:
1. Topic distribution across depression-related discourse
2. Depression-specific topic patterns
3. Source breakdown (YouTube vs external)
4. Exportable summaries for thesis/report
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from yt_depression_crawler.core.config import (
    BERTOPIC_METRICS_FILE,
    BERTOPIC_REPORT_FILE,
    BERTOPIC_TOPICS_FILE,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Keyword lists for depression-related topic analysis
# =============================================================================

DEPRESSION_KEYWORDS = [
    "buồn", "chán", "mệt", "mất", "không", "khó", "đau", "sợ",
    "tuyệt vọng", "trầm cảm", "tự tử", "mất hy vọng", "cô đơn",
    "mình", "người", "như", "nên", "biết", "làm", "muốn", "phải",
]

SOURCE_WEIGHT_MAP = {
    "youtube": 1.0,  # Primary source
    "external": 0.8,  # External datasets
}


def load_bertopic_results(
    topics_file: Path = BERTOPIC_TOPICS_FILE,
    metrics_file: Path = BERTOPIC_METRICS_FILE,
) -> tuple[pd.DataFrame, dict]:
    """Load BERTopic results from disk."""
    if not topics_file.exists():
        raise FileNotFoundError(f"Topics file not found: {topics_file}")

    df = pd.read_csv(topics_file, dtype=str)
    df["topic_id"] = df["topic_id"].astype(int)

    metrics = {}
    if metrics_file.exists():
        with open(metrics_file, encoding="utf-8") as f:
            metrics = json.load(f)

    return df, metrics


def analyze_topic_distribution(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze overall topic distribution."""
    total_docs = len(df)
    topic_counts = df["topic_id"].value_counts().sort_index()

    # Filter out outliers (-1)
    non_outlier = df[df["topic_id"] != -1]
    n_outliers = total_docs - len(non_outlier)

    distribution = []
    for tid, count in topic_counts.items():
        pct = round(count / total_docs * 100, 2)
        if tid != -1:
            label = df[df["topic_id"] == tid]["topic_label"].iloc[0] if tid in df["topic_id"].values else ""
            distribution.append({
                "topic_id": int(tid),
                "label": label,
                "count": int(count),
                "percentage": pct,
            })

    # Sort by count descending
    distribution.sort(key=lambda x: x["count"], reverse=True)

    return {
        "total_documents": total_docs,
        "n_topics": len(topic_counts) - (1 if -1 in topic_counts else 0),
        "n_outliers": int(n_outliers),
        "outlier_percentage": round(n_outliers / total_docs * 100, 2),
        "topic_distribution": distribution,
    }


def analyze_by_source(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze topic distribution by source (YouTube vs external)."""
    source_breakdown = {}

    for source in df["source"].unique():
        source_df = df[df["source"] == source]
        topic_counts = source_df["topic_id"].value_counts()

        top_topics = []
        for tid, count in topic_counts.head(10).items():
            if tid != -1:
                label = source_df[source_df["topic_id"] == tid]["topic_label"].iloc[0] if tid in source_df["topic_id"].values else ""
                top_topics.append({
                    "topic_id": int(tid),
                    "label": label,
                    "count": int(count),
                    "percentage": round(count / len(source_df) * 100, 2),
                })

        source_breakdown[source] = {
            "total_documents": len(source_df),
            "n_topics": len(topic_counts) - (1 if -1 in topic_counts else 0),
            "top_topics": top_topics,
        }

    return source_breakdown


def analyze_depression_topics(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze topics that may be depression-related.

    Uses keyword matching to identify potentially relevant topics.
    """
    # Find topics containing depression-related words
    depression_topics = []

    for tid in df["topic_id"].unique():
        if tid == -1:
            continue

        topic_df = df[df["topic_id"] == tid]
        topic_label = topic_df["topic_label"].iloc[0] if "topic_label" in topic_df.columns else ""
        texts = topic_df["text"].tolist()

        # Count depression signals
        signals = 0
        for kw in DEPRESSION_KEYWORDS:
            for text in texts[:100]:  # Sample first 100 for speed
                if kw in text.lower():
                    signals += 1

        if signals > 5:  # Threshold for "depression-related"
            depression_topics.append({
                "topic_id": int(tid),
                "label": topic_label,
                "document_count": len(topic_df),
                "depression_signal_count": signals,
                "sample_texts": texts[:5],
            })

    # Sort by signal count
    depression_topics.sort(key=lambda x: x["depression_signal_count"], reverse=True)

    return {
        "n_depression_related_topics": len(depression_topics),
        "depression_related_topics": depression_topics[:20],  # Top 20
    }


def analyze_topic_evolution(df: pd.DataFrame) -> dict[str, Any]:
    """Analyze topic patterns by affect_signal if available."""
    if "affect_signal" not in df.columns or df["affect_signal"].isna().all():
        return {"note": "No affect_signal data available"}

    breakdown = {}
    for signal in df["affect_signal"].dropna().unique():
        signal_df = df[df["affect_signal"] == signal]
        top_topics = signal_df["topic_id"].value_counts().head(5).to_dict()
        breakdown[signal] = {
            "count": len(signal_df),
            "top_topics": {int(k): int(v) for k, v in top_topics.items() if k != -1},
        }

    return breakdown


def generate_report(
    topics_file: Path = BERTOPIC_TOPICS_FILE,
    metrics_file: Path = BERTOPIC_METRICS_FILE,
    output_file: Path = BERTOPIC_REPORT_FILE,
) -> dict[str, Any]:
    """Generate comprehensive BERTopic analysis report."""
    logger.info("Generating BERTopic analysis report...")

    df, model_metrics = load_bertopic_results(topics_file, metrics_file)

    report = {
        "title": "BERTopic Topic Analysis Report",
        "corpus": "corpus_text_all (YouTube + External Vietnamese Texts)",
        "overview": analyze_topic_distribution(df),
        "by_source": analyze_by_source(df),
        "depression_related": analyze_depression_topics(df),
        "affect_breakdown": analyze_topic_evolution(df),
        "model_info": model_metrics.get("model", {}),
    }

    # Save report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info("Report saved to %s", output_file)
    return report


def print_report_summary(report: dict[str, Any]) -> None:
    """Print a human-readable summary of the report."""
    print("\n" + "=" * 70)
    print("BERTOPIC ANALYSIS SUMMARY")
    print("=" * 70)

    overview = report.get("overview", {})
    print(f"\n📊 Overview:")
    print(f"   Total documents: {overview.get('total_documents', 'N/A'):,}")
    print(f"   Topics discovered: {overview.get('n_topics', 'N/A')}")
    print(f"   Outliers: {overview.get('n_outliers', 'N/A')} ({overview.get('outlier_percentage', 'N/A')}%)")

    print(f"\n📌 Top 10 Topics:")
    for i, topic in enumerate(overview.get("topic_distribution", [])[:10], 1):
        print(f"   {i:2d}. Topic {topic['topic_id']:4d} | {topic['label'][:40]:<40} | {topic['count']:>6,} docs ({topic['percentage']}%)")

    if report.get("depression_related"):
        dep = report["depression_related"]
        print(f"\n🧠 Depression-Related Topics ({dep.get('n_depression_related_topics', 0)} found):")
        for topic in dep.get("depression_related_topics", [])[:5]:
            print(f"   - Topic {topic['topic_id']}: {topic['label'][:50]}")
            print(f"     {topic['document_count']} docs, signal={topic['depression_signal_count']}")

    print("\n" + "=" * 70)


def export_topics_for_thesis(report: dict[str, Any], output_path: Path | None = None) -> str:
    """Export topic analysis in thesis-friendly format."""
    if output_path is None:
        output_path = Path("data/bertopic_thesis_export.json")

    # Create thesis-friendly structure
    thesis_data = {
        "section_title": "Topic Analysis of Vietnamese Depression Discourse",
        "method": "BERTopic (unsupervised) on 316K Vietnamese texts",
        "findings": {
            "total_topics": report.get("overview", {}).get("n_topics", 0),
            "total_documents_analyzed": report.get("overview", {}).get("total_documents", 0),
            "outlier_rate": report.get("overview", {}).get("outlier_percentage", 0),
            "top_15_topics": report.get("overview", {}).get("topic_distribution", [])[:15],
        },
        "depression_focus": {
            "n_depression_related": report.get("depression_related", {}).get("n_depression_related_topics", 0),
            "top_depression_topics": report.get("depression_related", {}).get("depression_related_topics", [])[:10],
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(thesis_data, f, ensure_ascii=False, indent=2)

    return str(output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    report = generate_report()
    print_report_summary(report)
    export_path = export_topics_for_thesis(report)
    print(f"\nThesis export saved to: {export_path}")
