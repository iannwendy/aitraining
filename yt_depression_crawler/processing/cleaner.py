"""Làm sạch comment YouTube đã crawl."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

from yt_depression_crawler.core.config import RAW_COMMENT_COLUMNS

logger = logging.getLogger(__name__)

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")
REPEATED_CHAR_RE = re.compile(r"(.)\1{14,}")
SPAM_PHRASES = {
    "sub4sub",
    "subscribe",
    "đăng ký kênh",
    "dang ky kenh",
    "kiếm tiền online",
    "kiem tien online",
    "nhận quà miễn phí",
    "nhan qua mien phi",
}


def normalize_text(text: str) -> str:
    """Chuẩn hóa khoảng trắng, giữ nguyên Unicode tiếng Việt và emoji."""
    return WHITESPACE_RE.sub(" ", str(text).strip())


def is_basic_spam(text: str) -> bool:
    """Lọc spam đơn giản, tránh can thiệp quá mạnh vào dữ liệu nghiên cứu."""
    normalized = normalize_text(text)
    lowered = normalized.lower()

    if URL_RE.search(normalized):
        return True
    if any(phrase in lowered for phrase in SPAM_PHRASES):
        return True
    if REPEATED_CHAR_RE.search(normalized):
        return True

    tokens = lowered.split()
    if len(tokens) >= 8 and len(set(tokens)) <= 2:
        return True

    return False


def clean_comments(input_file: Path, output_file: Path) -> int:
    """Đọc raw CSV, lọc dữ liệu và xuất cleaned CSV. Trả về số dòng sạch."""
    if not input_file.exists() or input_file.stat().st_size == 0:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=RAW_COMMENT_COLUMNS).to_csv(
            output_file,
            index=False,
            encoding="utf-8-sig",
        )
        logger.warning("Chua co raw comment de lam sach: %s", input_file)
        return 0

    try:
        df = pd.read_csv(input_file, dtype=str).fillna("")
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=RAW_COMMENT_COLUMNS)

    if "comment_text" not in df.columns:
        df["comment_text"] = ""

    df["comment_text"] = df["comment_text"].map(normalize_text)
    df = df[df["comment_text"].str.len() >= 5]
    df = df[~df["comment_text"].map(is_basic_spam)]
    if "comment_id" in df.columns:
        has_comment_id = df["comment_id"].str.strip().ne("")
        with_id = df[has_comment_id].drop_duplicates(subset=["comment_id"], keep="first")
        without_id = df[~has_comment_id]
        df = pd.concat([with_id, without_id], ignore_index=True)
    df = df.drop_duplicates(subset=["comment_text"], keep="first")
    df = df.reindex(columns=RAW_COMMENT_COLUMNS)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    logger.info("Lam sach comment xong: %s dong -> %s", len(df), output_file)
    return len(df)
