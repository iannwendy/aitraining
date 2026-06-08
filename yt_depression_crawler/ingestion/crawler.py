"""Điều phối quy trình search video và crawl comment."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from threading import Event

from tqdm import tqdm

from yt_depression_crawler.core.config import (
    MAX_COMMENTS_PER_VIDEO,
    MAX_VIDEOS_PER_KEYWORD,
    PROCESSED_VIDEOS_FILE,
    RAW_FILE,
    TARGET_RAW_COMMENTS,
    VIDEO_METADATA_FILE,
)
from yt_depression_crawler.processing.cleaner import is_basic_spam, normalize_text
from yt_depression_crawler.processing.storage import (
    load_existing_comment_keys,
    load_processed_videos,
    mark_video_processed,
    normalize_comment_text_for_dedupe,
    save_comments_csv,
    save_video_metadata,
    count_csv_rows,
)
from yt_depression_crawler.ingestion.youtube_client import YouTubeClient, VideoInfo

logger = logging.getLogger(__name__)
TERMINAL_VIDEO_ERRORS = {"commentsDisabled", "forbidden", "notFound", "videoNotFound"}


@dataclass
class CrawlStats:
    total_keywords: int = 0
    total_videos_found: int = 0
    total_videos_crawled: int = 0
    total_videos_skipped: int = 0
    total_raw_comments_saved: int = 0


class YouTubeCommentCrawler:
    """Crawler có khả năng resume bằng processed_videos.txt."""

    def __init__(
        self,
        client: YouTubeClient,
        stop_event: Event | None = None,
        progress_callback: Callable[[dict], None] | None = None,
    ) -> None:
        self.client = client
        self.stop_event = stop_event
        self.progress_callback = progress_callback
        self.processed_videos = load_processed_videos(PROCESSED_VIDEOS_FILE)
        self.existing_comment_ids, self.existing_comment_texts = load_existing_comment_keys(RAW_FILE)
        self.current_raw_rows = count_csv_rows(RAW_FILE)

    def run(self, keywords: list[str]) -> CrawlStats:
        stats = CrawlStats(total_keywords=len(keywords))

        for keyword in tqdm(keywords, desc="Keywords", unit="keyword"):
            if self._stop_requested():
                logger.info("Dung crawl theo yeu cau nguoi dung.")
                break

            if self._target_reached():
                logger.info("Dung crawl vi da dat muc tieu %s raw comment.", TARGET_RAW_COMMENTS)
                break

            if self.client.quota_exceeded:
                logger.error("Dung crawl vi YouTube API da het quota.")
                break

            videos = self.client.search_videos(keyword, MAX_VIDEOS_PER_KEYWORD)
            stats.total_videos_found += len(videos)
            save_video_metadata(videos, VIDEO_METADATA_FILE)
            self._emit_progress(stats, keyword=keyword)

            for video in tqdm(videos, desc=f"Videos: {keyword}", unit="video", leave=False):
                if self._stop_requested():
                    logger.info("Dung crawl video theo yeu cau nguoi dung.")
                    break

                if self._target_reached():
                    logger.info("Dung crawl video vi da dat muc tieu %s raw comment.", TARGET_RAW_COMMENTS)
                    break

                if self.client.quota_exceeded:
                    logger.error("Dung crawl video vi YouTube API da het quota.")
                    break

                if video.video_id in self.processed_videos:
                    stats.total_videos_skipped += 1
                    self._emit_progress(stats, keyword=keyword, video=video)
                    continue

                comments, success = self.client.get_comments(video, MAX_COMMENTS_PER_VIDEO)
                if self.client.quota_exceeded:
                    break
                if not success:
                    if self.client.last_error_reason in TERMINAL_VIDEO_ERRORS:
                        mark_video_processed(video.video_id, PROCESSED_VIDEOS_FILE)
                        self.processed_videos.add(video.video_id)
                        stats.total_videos_crawled += 1
                        logger.info(
                            "Danh dau video_id=%s da xu ly vi khong the crawl comment: %s",
                            video.video_id,
                            self.client.last_error_reason,
                        )
                        self._emit_progress(stats, keyword=keyword, video=video)
                        continue

                    logger.warning(
                        "Chua danh dau video_id=%s vi crawl that bai tam thoi: %s",
                        video.video_id,
                        self.client.last_error_reason,
                    )
                    continue

                comments = self._filter_new_comments(comments)
                saved_count = save_comments_csv(comments, RAW_FILE)
                mark_video_processed(video.video_id, PROCESSED_VIDEOS_FILE)

                self.processed_videos.add(video.video_id)
                stats.total_videos_crawled += 1
                stats.total_raw_comments_saved += saved_count
                self.current_raw_rows += saved_count
                logger.info(
                    "Da xu ly video_id=%s keyword=%r saved_comments=%s",
                    video.video_id,
                    keyword,
                    saved_count,
                )
                self._emit_progress(stats, keyword=keyword, video=video)

        return stats

    def _target_reached(self) -> bool:
        return TARGET_RAW_COMMENTS is not None and self.current_raw_rows >= TARGET_RAW_COMMENTS

    def _stop_requested(self) -> bool:
        return self.stop_event is not None and self.stop_event.is_set()

    def _emit_progress(
        self,
        stats: CrawlStats,
        keyword: str | None = None,
        video: VideoInfo | None = None,
    ) -> None:
        if self.progress_callback is None:
            return

        self.progress_callback(
            {
                "keyword": keyword,
                "video_id": video.video_id if video else None,
                "video_title": video.title if video else None,
                "total_videos_found": stats.total_videos_found,
                "total_videos_crawled": stats.total_videos_crawled,
                "total_videos_skipped": stats.total_videos_skipped,
                "total_raw_comments_saved": stats.total_raw_comments_saved,
                "current_raw_rows": self.current_raw_rows,
                "quota_exceeded": self.client.quota_exceeded,
                "last_error_reason": self.client.last_error_reason,
            }
        )

    def _filter_new_comments(self, comments: list[dict]) -> list[dict]:
        filtered: list[dict] = []

        for comment in comments:
            text = normalize_text(str(comment.get("comment_text", "")))
            comment_id = str(comment.get("comment_id", "")).strip()
            text_key = normalize_comment_text_for_dedupe(text)

            if len(text) < 5:
                continue
            if is_basic_spam(text):
                continue
            if comment_id and comment_id in self.existing_comment_ids:
                continue
            if text_key in self.existing_comment_texts:
                continue

            comment["comment_text"] = text
            if comment_id:
                self.existing_comment_ids.add(comment_id)
            self.existing_comment_texts.add(text_key)
            filtered.append(comment)

        return filtered
