"""YouTube Integration - Fetch video metadata and comments.

Uses YouTube Data API v3 to extract comments from a single video URL.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ── URL Parsing ────────────────────────────────────────────────────────────────

YOUTUBE_URL_PATTERNS = [
    # Standard watch URL
    r'(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})',
    # Short URL
    r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})',
    # Embed URL
    r'(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
    # Shorts URL
    r'(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
]


def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats."""
    for pattern in YOUTUBE_URL_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class VideoMetadata:
    video_id: str
    title: str
    channel: str
    view_count: int
    like_count: int
    comment_count: int
    thumbnail_url: str
    published_at: str


@dataclass
class Comment:
    comment_id: str
    text: str
    author: str
    like_count: int
    published_at: str
    is_reply: bool


# ── YouTube Fetcher ───────────────────────────────────────────────────────────

class YouTubeFetcher:
    """Fetch video metadata and comments from YouTube Data API v3."""

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError(
                "Missing YOUTUBE_API_KEY. "
                "Please set YOUTUBE_API_KEY in your .env file."
            )
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

    def _make_request(self, endpoint: str, params: dict) -> dict:
        """Make authenticated request to YouTube API."""
        params["key"] = self.api_key
        url = f"{self.base_url}/{endpoint}"

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def get_video_metadata(self, video_id: str) -> VideoMetadata:
        """Fetch video metadata."""
        data = self._make_request(
            "videos",
            {
                "part": "snippet,statistics,contentDetails",
                "id": video_id,
            }
        )

        items = data.get("items", [])
        if not items:
            raise ValueError(f"Video not found: {video_id}")

        item = items[0]
        snippet = item["snippet"]
        stats = item.get("statistics", {})
        content = item.get("contentDetails", {})

        # Parse duration from ISO 8601 format
        duration = content.get("duration", "PT0S")
        duration_seconds = self._parse_duration(duration)

        return VideoMetadata(
            video_id=video_id,
            title=snippet.get("title", ""),
            channel=snippet.get("channelTitle", ""),
            view_count=int(stats.get("viewCount", 0)),
            like_count=int(stats.get("likeCount", 0)),
            comment_count=int(stats.get("commentCount", 0)),
            thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            published_at=snippet.get("publishedAt", ""),
        )

    def _parse_duration(self, iso_duration: str) -> int:
        """Parse ISO 8601 duration to seconds."""
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, iso_duration)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        return 0

    def get_comments(
        self,
        video_id: str,
        max_comments: int = 100,
    ) -> list[Comment]:
        """Fetch top-level comments from a video."""
        comments: list[Comment] = []
        page_token: Optional[str] = None

        while len(comments) < max_comments:
            params = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": min(100, max_comments - len(comments)),
                "order": "relevance",
                "textFormat": "plainText",
            }
            if page_token:
                params["pageToken"] = page_token

            try:
                data = self._make_request("commentThreads", params)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    error_msg = e.response.json().get("error", {}).get("errors", [{}])[0].get("reason", "")
                    if "commentsDisabled" in error_msg or "videoNotFound" in error_msg:
                        logger.warning(f"Comments disabled or video not found: {video_id}")
                        return []
                    elif "quotaExceeded" in error_msg.lower():
                        raise ValueError("YouTube API quota exceeded. Please try again later.")
                raise
            except Exception as e:
                logger.error(f"Error fetching comments: {e}")
                raise

            items = data.get("items", [])

            for item in items:
                snippet = item["snippet"]
                top_comment = snippet["topLevelComment"]["snippet"]

                # Skip replies
                is_reply = snippet.get("isReply", False)
                if is_reply:
                    continue

                comment = Comment(
                    comment_id=top_comment.get("id", ""),
                    text=top_comment.get("textDisplay") or top_comment.get("textOriginal", ""),
                    author=top_comment.get("authorDisplayName", "Anonymous"),
                    like_count=int(top_comment.get("likeCount", 0)),
                    published_at=top_comment.get("publishedAt", ""),
                    is_reply=False,
                )

                # Only add non-empty comments
                if comment.text.strip():
                    comments.append(comment)

            # Check for next page
            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return comments[:max_comments]

    def fetch_video_and_comments(
        self,
        url: str,
        max_comments: int = 100,
    ) -> tuple[VideoMetadata, list[Comment]]:
        """Fetch both video metadata and comments from a URL."""
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {url}")

        metadata = self.get_video_metadata(video_id)
        comments = self.get_comments(video_id, max_comments)

        return metadata, comments


# ── Module-level Singleton ─────────────────────────────────────────────────────

_fetcher: Optional[YouTubeFetcher] = None


def get_fetcher() -> YouTubeFetcher:
    """Get or create YouTube fetcher instance."""
    global _fetcher
    if _fetcher is None:
        import os
        api_key = os.environ.get("YOUTUBE_API_KEY", "")
        if not api_key:
            # Try to load from .env files (multiple locations)
            try:
                from pathlib import Path
                # Possible .env locations
                backend_dir = Path(__file__).resolve().parents[1]  # /app/backend/
                web_demo_dir = Path(__file__).resolve().parents[2]  # /app/
                project_root = Path(__file__).resolve().parents[3]  # /yt-depression-crawler/

                env_paths = [
                    backend_dir / ".env",
                    web_demo_dir / ".env",
                    project_root / ".env",
                ]

                from dotenv import load_dotenv
                for env_path in env_paths:
                    if env_path.exists():
                        load_dotenv(env_path)
                        api_key = os.environ.get("YOUTUBE_API_KEY", "")
                        if api_key:
                            break
            except Exception:
                pass

        if not api_key:
            raise ValueError(
                "YOUTUBE_API_KEY not found. "
                "Please set YOUTUBE_API_KEY in your .env file. "
                "Get your API key from: https://console.cloud.google.com/apis/credentials"
            )

        _fetcher = YouTubeFetcher(api_key)

    return _fetcher
