"""Wrapper cho YouTube Data API v3."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from yt_depression_crawler.core.config import (
    API_TIMEOUT_SECONDS,
    REGION_CODE,
    RELEVANCE_LANGUAGE,
    SEARCH_ORDER,
    YOUTUBE_API_SERVICE_NAME,
    YOUTUBE_API_VERSION,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VideoInfo:
    video_id: str
    title: str
    channel: str
    published_at: str
    keyword: str


class YouTubeClient:
    """Ket noi va goi YouTube Data API v3 chinh thuc."""

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("Missing YOUTUBE_API_KEY. Hay tao file .env tu .env.example.")

        self.quota_exceeded = False
        self.last_error_reason: str | None = None

        self.youtube = build(
            YOUTUBE_API_SERVICE_NAME,
            YOUTUBE_API_VERSION,
            developerKey=api_key,
            cache_discovery=False,
        )

    def search_videos(self, keyword: str, max_results: int) -> list[VideoInfo]:
        """Tim video theo keyword va tra ve metadata can thiet."""
        videos: list[VideoInfo] = []
        page_token: str | None = None
        remaining = max_results
        self.last_error_reason = None

        while remaining > 0:
            request_size = min(50, remaining)
            try:
                response = (
                    self.youtube.search()
                    .list(
                        part="snippet",
                        q=keyword,
                        type="video",
                        maxResults=request_size,
                        order=SEARCH_ORDER,
                        regionCode=REGION_CODE,
                        relevanceLanguage=RELEVANCE_LANGUAGE,
                        pageToken=page_token,
                    )
                    .execute(num_retries=2)
                )
            except HttpError as exc:
                self._log_http_error(exc, f"search keyword={keyword!r}")
                break
            except Exception as exc:  # noqa: BLE001 - log va tiep tuc keyword khac
                logger.exception("Loi khi search keyword %r: %s", keyword, exc)
                self.last_error_reason = "exception"
                break

            for item in response.get("items", []):
                video_id = item.get("id", {}).get("videoId")
                snippet = item.get("snippet", {})
                if not video_id:
                    continue

                videos.append(
                    VideoInfo(
                        video_id=video_id,
                        title=snippet.get("title", ""),
                        channel=snippet.get("channelTitle", ""),
                        published_at=snippet.get("publishedAt", ""),
                        keyword=keyword,
                    )
                )

            remaining = max_results - len(videos)
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return videos[:max_results]

    def get_comments(
        self,
        video: VideoInfo,
        max_comments: int,
    ) -> tuple[list[dict[str, Any]], bool]:
        """Lay top-level comments cua mot video. Khong crawl reply comment."""
        comments: list[dict[str, Any]] = []
        page_token: str | None = None
        self.last_error_reason = None

        while len(comments) < max_comments:
            request_size = min(100, max_comments - len(comments))
            try:
                response = (
                    self.youtube.commentThreads()
                    .list(
                        part="snippet",
                        videoId=video.video_id,
                        maxResults=request_size,
                        order="relevance",
                        textFormat="plainText",
                        pageToken=page_token,
                    )
                    .execute(num_retries=2)
                )
            except HttpError as exc:
                self._log_http_error(exc, f"comments video_id={video.video_id}")
                break
            except Exception as exc:  # noqa: BLE001 - log va tiep tuc video khac
                logger.exception("Loi khi crawl comment video %s: %s", video.video_id, exc)
                self.last_error_reason = "exception"
                break

            for item in response.get("items", []):
                top_level_comment = item.get("snippet", {}).get("topLevelComment", {})
                top_comment = (
                    top_level_comment
                    .get("snippet", {})
                )
                text = top_comment.get("textDisplay") or top_comment.get("textOriginal") or ""
                comments.append(
                    {
                        "comment_id": top_level_comment.get("id") or item.get("id", ""),
                        "video_id": video.video_id,
                        "video_title": video.title,
                        "keyword": video.keyword,
                        "comment_text": text,
                        "like_count": top_comment.get("likeCount", 0),
                        "published_at": top_comment.get("publishedAt", ""),
                    }
                )

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        success = self.last_error_reason is None
        return comments[:max_comments], success

    def _log_http_error(self, exc: HttpError, context: str) -> None:
        """Ghi log loi API theo nhom de chuong trinh khong crash."""
        status = getattr(exc.resp, "status", "unknown")
        reason = "unknown"

        try:
            error_details = exc.error_details or []
            if error_details:
                reason = error_details[0].get("reason", reason)
        except Exception:  # noqa: BLE001 - HttpError co the khac format
            pass

        if status == 404 and reason == "unknown":
            reason = "notFound"

        self.last_error_reason = reason

        if reason in {"commentsDisabled", "forbidden"}:
            logger.warning("Bo qua video vi comment bi tat/khong duoc truy cap: %s", context)
        elif reason in {"quotaExceeded", "dailyLimitExceeded"}:
            self.quota_exceeded = True
            logger.error("YouTube API quota exceeded tai %s. Hay doi ngay hoac API key.", context)
        elif status == 404:
            logger.warning("Video khong ton tai hoac da bi xoa: %s", context)
        else:
            logger.warning("YouTube API error status=%s reason=%s tai %s", status, reason, context)
