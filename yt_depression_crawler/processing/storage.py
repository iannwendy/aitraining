"""Tien ich luu/doc du lieu bang CSV va TXT."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from yt_depression_crawler.core.config import RAW_COMMENT_COLUMNS, VIDEO_METADATA_COLUMNS
from yt_depression_crawler.ingestion.youtube_client import VideoInfo


logger = logging.getLogger(__name__)


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_comments_csv(comments: list[dict[str, Any]], output_file: Path) -> int:
    """Append comments vao CSV. Tra ve so dong da ghi."""
    if not comments:
        return 0

    _ensure_parent(output_file)
    _ensure_csv_columns(output_file, RAW_COMMENT_COLUMNS)
    df = pd.DataFrame(comments)
    df = df.reindex(columns=RAW_COMMENT_COLUMNS)
    write_header = not output_file.exists() or output_file.stat().st_size == 0
    df.to_csv(output_file, mode="a", header=write_header, index=False, encoding="utf-8-sig")
    logger.info("Da luu %s comment vao %s", len(df), output_file)
    return len(df)

def _ensure_csv_columns(path: Path, columns: list[str]) -> None:
    """Nang cap header CSV cu khi schema them cot moi."""
    if not path.exists() or path.stat().st_size == 0:
        return

    try:
        df = pd.read_csv(path, dtype=str).fillna("")
    except pd.errors.EmptyDataError:
        pd.DataFrame(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")
        return

    if list(df.columns) == columns:
        return

    df = df.reindex(columns=columns).fillna("")
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info("Da nang cap schema CSV %s", path)


def save_video_metadata(videos: list[VideoInfo], output_file: Path) -> int:
    """Append metadata video vao CSV, tranh trung theo video_id + keyword."""
    if not videos:
        return 0

    _ensure_parent(output_file)
    new_df = pd.DataFrame([video.__dict__ for video in videos])
    new_df = new_df.reindex(columns=VIDEO_METADATA_COLUMNS)

    if output_file.exists() and output_file.stat().st_size > 0:
        old_df = pd.read_csv(output_file, dtype=str).fillna("")
        merged = pd.concat([old_df, new_df], ignore_index=True)
        merged = merged.drop_duplicates(subset=["video_id", "keyword"], keep="first")
    else:
        merged = new_df.drop_duplicates(subset=["video_id", "keyword"], keep="first")

    merged.to_csv(output_file, index=False, encoding="utf-8-sig")
    logger.info("Da cap nhat metadata video vao %s", output_file)
    return len(new_df)


def load_processed_videos(path: Path) -> set[str]:
    """Doc danh sach video_id da xu ly."""
    if not path.exists():
        return set()

    with path.open("r", encoding="utf-8") as file:
        return {line.strip() for line in file if line.strip()}


def mark_video_processed(video_id: str, path: Path) -> None:
    """Danh dau video da xu ly de lan sau khong crawl lai."""
    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as file:
        file.write(f"{video_id}\n")

def normalize_comment_text_for_dedupe(text: str) -> str:
    """Chuan hoa text ve key on dinh de chong trung."""
    return " ".join(str(text).strip().split()).lower()

def load_existing_comment_keys(path: Path) -> tuple[set[str], set[str]]:
    """Doc comment_id va comment_text da co de han che ghi trung khi resume."""
    if not path.exists() or path.stat().st_size == 0:
        return set(), set()

    try:
        df = pd.read_csv(path, dtype=str).fillna("")
    except pd.errors.EmptyDataError:
        return set(), set()

    comment_ids: set[str] = set()
    comment_texts: set[str] = set()

    if "comment_id" in df.columns:
        comment_ids = {comment_id.strip() for comment_id in df["comment_id"] if comment_id.strip()}
    if "comment_text" in df.columns:
        comment_texts = {
            normalize_comment_text_for_dedupe(text)
            for text in df["comment_text"]
            if str(text).strip()
        }

    return comment_ids, comment_texts


def remove_duplicates(input_file: Path, output_file: Path | None = None) -> int:
    """Loai trung comment_text trong CSV va ghi de file dich."""
    if not input_file.exists() or input_file.stat().st_size == 0:
        return 0

    target = output_file or input_file
    df = pd.read_csv(input_file, dtype=str).fillna("")
    before = len(df)
    if "comment_id" in df.columns:
        has_comment_id = df["comment_id"].str.strip().ne("")
        with_id = df[has_comment_id].drop_duplicates(subset=["comment_id"], keep="first")
        without_id = df[~has_comment_id]
        df = pd.concat([with_id, without_id], ignore_index=True)
    df = df.drop_duplicates(subset=["comment_text"], keep="first")
    df.to_csv(target, index=False, encoding="utf-8-sig")
    logger.info("Loai trung CSV: %s -> %s dong", before, len(df))
    return len(df)


def count_csv_rows(path: Path) -> int:
    """Dem so dong du lieu trong CSV, bo qua header."""
    if not path.exists() or path.stat().st_size == 0:
        return 0

    return len(pd.read_csv(path, dtype=str))
