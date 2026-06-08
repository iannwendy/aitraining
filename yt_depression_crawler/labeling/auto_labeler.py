"""Weak labeling comment bằng keyword scoring."""

from __future__ import annotations

import json
import logging
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from yt_depression_crawler.processing.cleaner import normalize_text
from yt_depression_crawler.core.config import (
    AUTO_LABELED_COLUMNS,
    AUTO_LABELED_FILE,
    CLEANED_FILE,
    DEPRESSION_AUTO_THRESHOLD,
    DEPRESSION_MEDIUM_WEIGHT,
    DEPRESSION_STRONG_WEIGHT,
    HIGH_CONFIDENCE_DEPRESSION_THRESHOLD,
    HIGH_CONFIDENCE_NORMAL_THRESHOLD,
    LABELING_REPORT_FILE,
    NORMAL_AUTO_THRESHOLD,
    NORMAL_WEIGHT,
)
from yt_depression_crawler.labeling.label_config import (
    DEPRESSION_MEDIUM_KEYWORDS,
    DEPRESSION_STRONG_KEYWORDS,
    NORMAL_KEYWORDS,
    REVIEW_CONTEXT_KEYWORDS,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LabelResult:
    weak_label: str
    confidence: str
    depression_score: int
    matched_keywords: str
    need_review: bool


def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt để match cả text có dấu và không dấu."""
    normalized = unicodedata.normalize("NFD", text)
    without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return without_marks.replace("đ", "d").replace("Đ", "D")


def normalize_for_match(text: str) -> str:
    base = normalize_text(text).lower()
    no_accent = strip_accents(base)
    return f" {no_accent} "


def _prepare_keywords(keywords: list[str]) -> list[tuple[str, str]]:
    prepared: list[tuple[str, str]] = []
    seen: set[str] = set()
    for keyword in keywords:
        display = normalize_text(keyword).lower()
        match_key = strip_accents(display)
        if not display or match_key in seen:
            continue
        seen.add(match_key)
        prepared.append((display, match_key))
    return prepared


STRONG_KEYWORDS = _prepare_keywords(DEPRESSION_STRONG_KEYWORDS)
MEDIUM_KEYWORDS = _prepare_keywords(DEPRESSION_MEDIUM_KEYWORDS)
NORMAL_KEYWORDS_PREPARED = _prepare_keywords(NORMAL_KEYWORDS)
REVIEW_CONTEXTS = _prepare_keywords(REVIEW_CONTEXT_KEYWORDS)


def find_matches(text_for_match: str, prepared_keywords: list[tuple[str, str]]) -> list[str]:
    matches: list[str] = []
    for display, match_key in prepared_keywords:
        if f" {match_key} " in text_for_match or match_key in text_for_match.strip():
            matches.append(display)
    return matches


def label_comment(comment_text: str) -> LabelResult:
    text = normalize_text(comment_text)
    text_for_match = normalize_for_match(text)
    strong_matches = find_matches(text_for_match, STRONG_KEYWORDS)
    medium_matches = find_matches(text_for_match, MEDIUM_KEYWORDS)
    normal_matches = find_matches(text_for_match, NORMAL_KEYWORDS_PREPARED)
    review_matches = find_matches(text_for_match, REVIEW_CONTEXTS)

    score = (
        len(strong_matches) * DEPRESSION_STRONG_WEIGHT
        + len(medium_matches) * DEPRESSION_MEDIUM_WEIGHT
        + len(normal_matches) * NORMAL_WEIGHT
    )

    if score >= DEPRESSION_AUTO_THRESHOLD:
        weak_label = "depression_auto"
        confidence = "high" if score >= HIGH_CONFIDENCE_DEPRESSION_THRESHOLD else "medium"
    elif score <= NORMAL_AUTO_THRESHOLD:
        weak_label = "normal_auto"
        confidence = "high" if score <= HIGH_CONFIDENCE_NORMAL_THRESHOLD else "medium"
    else:
        weak_label = "uncertain"
        confidence = "low"

    has_mixed_signal = bool((strong_matches or medium_matches) and normal_matches)
    near_boundary = score in {-3, -2, -1, 0, 1, 2, 3, 4, 5}
    too_short_for_strong = len(text) < 20 and bool(strong_matches)
    need_review = (
        weak_label == "uncertain"
        or has_mixed_signal
        or bool(review_matches)
        or near_boundary
        or too_short_for_strong
    )

    matched = strong_matches + medium_matches + normal_matches + review_matches
    return LabelResult(
        weak_label=weak_label,
        confidence=confidence,
        depression_score=score,
        matched_keywords="|".join(dict.fromkeys(matched)),
        need_review=need_review,
    )


def auto_label_comments(
    input_file: Path = CLEANED_FILE,
    output_file: Path = AUTO_LABELED_FILE,
    report_file: Path = LABELING_REPORT_FILE,
) -> dict:
    """Tạo auto_labeled_comments.csv và cập nhật report JSON."""
    if not input_file.exists() or input_file.stat().st_size == 0:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=AUTO_LABELED_COLUMNS).to_csv(output_file, index=False, encoding="utf-8-sig")
        report = {"total_input": 0, "total_labeled": 0, "label_counts": {}}
        _write_report(report_file, report)
        return report

    df = pd.read_csv(input_file, dtype=str).fillna("")
    if "comment_text" not in df.columns:
        raise ValueError(f"Missing comment_text column in {input_file}")

    df["comment_text"] = df["comment_text"].map(normalize_text)
    df = df[df["comment_text"].str.len() >= 5]
    df = df.drop_duplicates(subset=["comment_text"], keep="first")

    results = [label_comment(text) for text in df["comment_text"]]
    output_df = pd.DataFrame(
        {
            "comment_text": df["comment_text"].tolist(),
            "weak_label": [result.weak_label for result in results],
            "confidence": [result.confidence for result in results],
            "depression_score": [result.depression_score for result in results],
            "matched_keywords": [result.matched_keywords for result in results],
            "need_review": [result.need_review for result in results],
        }
    )
    output_df = output_df.reindex(columns=AUTO_LABELED_COLUMNS)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_file, index=False, encoding="utf-8-sig")

    report = build_labeling_report(output_df, results, total_input=len(df))
    _write_report(report_file, {"auto_labeling": report})
    logger.info("Auto-label xong: %s dong -> %s", len(output_df), output_file)
    return report


def build_labeling_report(output_df: pd.DataFrame, results: list[LabelResult], total_input: int) -> dict:
    keyword_counter: Counter[str] = Counter()
    for result in results:
        for keyword in result.matched_keywords.split("|"):
            if keyword:
                keyword_counter[keyword] += 1

    return {
        "total_input": total_input,
        "total_labeled": int(len(output_df)),
        "label_counts": output_df["weak_label"].value_counts().to_dict(),
        "confidence_counts": output_df["confidence"].value_counts().to_dict(),
        "need_review_count": int(output_df["need_review"].astype(bool).sum()),
        "high_confidence_depression": int(
            ((output_df["weak_label"] == "depression_auto") & (output_df["confidence"] == "high")).sum()
        ),
        "high_confidence_normal": int(
            ((output_df["weak_label"] == "normal_auto") & (output_df["confidence"] == "high")).sum()
        ),
        "top_matched_keywords": keyword_counter.most_common(30),
    }


def _write_report(report_file: Path, payload: dict) -> None:
    report_file.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if report_file.exists() and report_file.stat().st_size > 0:
        try:
            existing = json.loads(report_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    existing.update(payload)
    report_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    summary = auto_label_comments()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
