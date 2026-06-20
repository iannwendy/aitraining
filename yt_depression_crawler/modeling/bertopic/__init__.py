"""BERTopic modeling module for Vietnamese depression corpus."""

from yt_depression_crawler.modeling.bertopic.bertopic_model import (
    assign_topics_to_corpus,
    build_topic_model,
    build_topic_summary,
    compute_embeddings,
    generate_visualization,
    get_embedding_model,
    get_topic_features,
    load_corpus,
    load_trained_model,
    predict_topics,
    save_model_artifacts,
    train_bertopic,
)
from yt_depression_crawler.modeling.bertopic.bertopic_report import (
    analyze_by_source,
    analyze_depression_topics,
    analyze_topic_distribution,
    analyze_topic_evolution,
    export_topics_for_thesis,
    generate_report,
    load_bertopic_results,
    print_report_summary,
)

__all__ = [
    "train_bertopic",
    "load_corpus",
    "get_embedding_model",
    "compute_embeddings",
    "build_topic_model",
    "assign_topics_to_corpus",
    "build_topic_summary",
    "save_model_artifacts",
    "generate_visualization",
    "predict_topics",
    "get_topic_features",
    "load_trained_model",
    "generate_report",
    "load_bertopic_results",
    "analyze_topic_distribution",
    "analyze_by_source",
    "analyze_depression_topics",
    "analyze_topic_evolution",
    "export_topics_for_thesis",
    "print_report_summary",
]
