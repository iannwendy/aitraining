"""Pipeline entry point cho BERTopic (Step 13).

Run:
    python -m yt_depression_crawler.pipelines.bertopic_pipeline

Output artifacts:
- models/bertopic/bertopic_model.pkl         : trained topic model
- models/bertopic/corpus_with_topics.csv     : all 316K sentences + topic_id
- models/bertopic/bertopic_metrics.json     : metrics
- models/bertopic/topic_visualization.html  : interactive barchart
- models/bertopic_report.json                : full analysis report
"""

from __future__ import annotations

import json
import logging
import sys
import time

from yt_depression_crawler.modeling.bertopic import (
    generate_report,
    print_report_summary,
    train_bertopic,
)

logger = logging.getLogger(__name__)


def run_bertopic_pipeline(
    compute_embeddings_only: bool = False,
    min_topic_size: int = 50,
) -> dict:
    """Run full BERTopic pipeline on corpus_text_all.

    Args:
        compute_embeddings_only: If True, only compute and save embeddings (first step)
        min_topic_size: Minimum documents per topic (adjust for corpus size)

    Returns:
        dict with all metrics and file paths
    """
    t0 = time.time()

    logger.info("Starting BERTopic Pipeline (Step 13)")
    logger.info("=" * 60)

    try:
        # Step 1: Train BERTopic (or compute embeddings only)
        if compute_embeddings_only:
            logger.info("Mode: embeddings-only (pass 1 of 2-step approach)")
            result = train_bertopic(compute_embeddings_only=True)
            elapsed = time.time() - t0
            return {
                "status": "embeddings_computed",
                "elapsed_seconds": round(elapsed, 1),
                **result,
            }

        # Step 2: Train topic model
        logger.info("Training BERTopic model...")
        train_result = train_bertopic(
            min_topic_size=min_topic_size,
            use_cached_embeddings=True,  # Reuse if already computed
        )

        # Step 3: Generate analysis report
        logger.info("Generating analysis report...")
        report = generate_report()
        print_report_summary(report)

        elapsed = time.time() - t0

        return {
            "status": "completed",
            "elapsed_seconds": round(elapsed, 1),
            "training": train_result,
            "report_generated": True,
        }

    except Exception as e:
        logger.exception("BERTopic pipeline failed: %s", e)
        return {
            "status": "error",
            "error": str(e),
            "elapsed_seconds": round(time.time() - t0, 1),
        }


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # Parse CLI args
    embeddings_only = "--embeddings-only" in sys.argv
    min_topic_size = 50

    for arg in sys.argv[1:]:
        if arg.startswith("--min-topic-size="):
            min_topic_size = int(arg.split("=")[1])

    result = run_bertopic_pipeline(
        compute_embeddings_only=embeddings_only,
        min_topic_size=min_topic_size,
    )

    print("\n" + "=" * 60)
    print("BERTOPIC PIPELINE RESULT")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
