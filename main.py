"""Entry point chạy toàn bộ pipeline crawl và làm sạch comment."""

from __future__ import annotations

import logging
import sys

from yt_depression_crawler.processing.cleaner import clean_comments
from yt_depression_crawler.core.config import CLEANED_FILE, LOG_FILE, RAW_FILE, YOUTUBE_API_KEY, ensure_directories
from yt_depression_crawler.ingestion.crawler import YouTubeCommentCrawler
from yt_depression_crawler.core.keywords import get_keywords
from yt_depression_crawler.processing.storage import count_csv_rows
from yt_depression_crawler.ingestion.youtube_client import YouTubeClient


def setup_logging() -> None:
    ensure_directories()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    keywords = get_keywords()
    logger.info("Bat dau crawl voi %s keyword", len(keywords))

    client = YouTubeClient(YOUTUBE_API_KEY)
    crawler = YouTubeCommentCrawler(client)
    crawl_stats = crawler.run(keywords)
    cleaned_count = clean_comments(RAW_FILE, CLEANED_FILE)
    raw_total = count_csv_rows(RAW_FILE)

    print("\n===== THONG KE CRAWL =====")
    print(f"Tong keyword: {crawl_stats.total_keywords}")
    print(f"Tong video tim duoc: {crawl_stats.total_videos_found}")
    print(f"Tong video da crawl: {crawl_stats.total_videos_crawled}")
    print(f"Tong video bo qua vi da xu ly: {crawl_stats.total_videos_skipped}")
    print(f"Tong comment raw trong file: {raw_total}")
    print(f"Tong comment raw moi luu lan nay: {crawl_stats.total_raw_comments_saved}")
    print(f"Tong comment sau lam sach: {cleaned_count}")
    print(f"Raw CSV: {RAW_FILE}")
    print(f"Cleaned CSV: {CLEANED_FILE}")
    print(f"Log: {LOG_FILE}")


if __name__ == "__main__":
    main()
