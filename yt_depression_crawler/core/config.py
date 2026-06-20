"""Cau hinh cho YouTube depression comment crawler.

Nguoi dung co the chinh cac hang so trong file nay de thay doi quy mo crawl.
API key duoc doc tu file .env, khong hard-code trong source code.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


# YouTube API
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
API_TIMEOUT_SECONDS = 30


# Crawl scale for a 500K-comment dataset target.
# None = dung tat ca keyword mac dinh + bo sung trong keywords.py/config.py.
MAX_KEYWORDS: int | None = None

# Với khoảng 50 keyword mặc định, cấu hình này có trần lý thuyết khoảng
# 50 * 100 * 100 = 500.000 comment trước lọc. Thực tế sẽ thấp hơn vì nhiều
# video tắt comment, ít comment, trùng lặp hoặc bị lọc spam/ngắn.
MAX_VIDEOS_PER_KEYWORD = 100
MAX_COMMENTS_PER_VIDEO = 100

# Dừng pipeline khi raw_comments.csv đạt mốc này để tránh crawl vượt quá xa.
TARGET_RAW_COMMENTS: int | None = 500_000


# YouTube search order: relevance, date, rating, title, videoCount, viewCount
SEARCH_ORDER = "relevance"
REGION_CODE = "VN"
RELEVANCE_LANGUAGE = "vi"


# Cho phep them keyword tai day, vi du:
# ADDITIONAL_KEYWORDS = ["ap luc thi cu", "toi thay vo vong"]
ADDITIONAL_KEYWORDS: list[str] = []


# Files
OUTPUT_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
RAW_FILE = OUTPUT_DIR / "raw_comments.csv"
CLEANED_FILE = OUTPUT_DIR / "cleaned_comments.csv"
AUTO_LABELED_FILE = OUTPUT_DIR / "auto_labeled_comments.csv"
INITIAL_TRAIN_FILE = OUTPUT_DIR / "initial_train.csv"
REVIEW_SAMPLES_FILE = OUTPUT_DIR / "review_samples.csv"
GOLD_REVIEW_FILE = OUTPUT_DIR / "gold_review.csv"
REVIEW_EVAL_REPORT_FILE = OUTPUT_DIR / "review_eval_report.json"
REVIEW_EVAL_ERRORS_FILE = OUTPUT_DIR / "review_eval_errors.csv"
BASELINE_GOLD_ERRORS_FILE = OUTPUT_DIR / "baseline_gold_errors.csv"
TRAIN_FILE = OUTPUT_DIR / "train.csv"
VAL_FILE = OUTPUT_DIR / "val.csv"
TEST_FILE = OUTPUT_DIR / "test.csv"
LABELING_REPORT_FILE = OUTPUT_DIR / "labeling_report.json"
PROCESSED_VIDEOS_FILE = OUTPUT_DIR / "processed_videos.txt"
VIDEO_METADATA_FILE = OUTPUT_DIR / "video_metadata.csv"
LOG_FILE = LOG_DIR / "crawler.log"
MODEL_DIR = BASE_DIR / "models"
BASELINE_MODEL_FILE = MODEL_DIR / "tfidf_logreg.joblib"
BASELINE_METRICS_FILE = MODEL_DIR / "baseline_metrics.json"
BASELINE_GOLD_METRICS_FILE = MODEL_DIR / "baseline_gold_metrics.json"
PHOBERT_MODEL_NAME = "vinai/phobert-base"
PHOBERT_OUTPUT_DIR = MODEL_DIR / "phobert_first"
PHOBERT_METRICS_FILE = PHOBERT_OUTPUT_DIR / "phobert_metrics.json"
PHOBERT_GOLD_METRICS_FILE = PHOBERT_OUTPUT_DIR / "phobert_gold_metrics.json"
PHOBERT_REMAINING_PREDICTIONS_FILE = OUTPUT_DIR / "phobert_remaining_predictions.csv"
PHOBERT_CONFIDENT_PREDICTIONS_FILE = OUTPUT_DIR / "phobert_confident_predictions.csv"
PHOBERT_ACTIVE_LEARNING_FILE = OUTPUT_DIR / "phobert_active_learning_samples.csv"
PHOBERT_POSTPROCESS_REPORT_FILE = PHOBERT_OUTPUT_DIR / "phobert_postprocess_report.json"

# BERTopic settings
BERTOPIC_MODEL_DIR = MODEL_DIR / "bertopic"
BERTOPIC_METRICS_FILE = BERTOPIC_MODEL_DIR / "bertopic_metrics.json"
BERTOPIC_TOPICS_FILE = BERTOPIC_MODEL_DIR / "corpus_with_topics.csv"
BERTOPIC_MODEL_FILE = BERTOPIC_MODEL_DIR / "bertopic_model.pkl"
BERTOPIC_EMBEDDINGS_FILE = BERTOPIC_MODEL_DIR / "embeddings.npy"
BERTOPIC_VISUALIZATION_FILE = BERTOPIC_MODEL_DIR / "topic_visualization.html"
BERTOPIC_REPORT_FILE = MODEL_DIR / "bertopic_report.json"

# BERTopic defaults for Vietnamese 316K corpus
BERTOPIC_MIN_TOPIC_SIZE = 50  # Balanced for 316K documents
BERTOPIC_N_TOPICS = "auto"  # Auto-determine (BERTopic default)
BERTOPIC_EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # Good for Vietnamese
BERTOPIC_UMAP_N_NEIGHBORS = 15
BERTOPIC_UMAP_MIN_DIST = 0.0
BERTOPIC_HDBSCAN_MIN_CLUSTER_SIZE = 50
BERTOPIC_HDBSCAN_MIN_SAMPLES = 10
BERTOPIC_TOP_N_WORDS = 10
BERTOPIC_CALCULATE_PROBABILITIES = False  # Memory efficient for large corpus

# Weak-labeling settings
INITIAL_TRAIN_DEPRESSION_SAMPLES = 10_000
INITIAL_TRAIN_NORMAL_SAMPLES = 10_000
INITIAL_TRAIN_RANDOM_SEED = 42
INITIAL_TRAIN_MIN_CHARS = 10
INITIAL_TRAIN_MAX_CHARS = 500
REVIEW_SAMPLE_PER_BUCKET = 150
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# PhoBERT training settings
PHOBERT_MAX_LENGTH = 128
PHOBERT_BATCH_SIZE = 8
PHOBERT_EVAL_BATCH_SIZE = 16
PHOBERT_PREDICT_BATCH_SIZE = 32
PHOBERT_PREDICT_CHUNK_SIZE = 2000
PHOBERT_PSEUDO_LABEL_PROB_THRESHOLD = 0.90
PHOBERT_ACTIVE_LEARNING_PROB_THRESHOLD = 0.70
PHOBERT_ACTIVE_LEARNING_MAX_SAMPLES = 1000
PHOBERT_EPOCHS = 3
PHOBERT_LEARNING_RATE = 2e-5
PHOBERT_WEIGHT_DECAY = 0.01
PHOBERT_WARMUP_RATIO = 0.06
PHOBERT_GRAD_CLIP_NORM = 1.0
PHOBERT_EARLY_STOPPING_PATIENCE = 2
PHOBERT_RANDOM_SEED = 42
PHOBERT_DEVICE = "auto"  # auto, cpu, cuda, mps
PHOBERT_USE_WORD_SEGMENTATION = True

# Keyword scoring
DEPRESSION_STRONG_WEIGHT = 5
DEPRESSION_MEDIUM_WEIGHT = 3
NORMAL_WEIGHT = -2
DEPRESSION_AUTO_THRESHOLD = 5
NORMAL_AUTO_THRESHOLD = -2
HIGH_CONFIDENCE_DEPRESSION_THRESHOLD = 8
HIGH_CONFIDENCE_NORMAL_THRESHOLD = -4


RAW_COMMENT_COLUMNS = [
    "comment_id",
    "video_id",
    "video_title",
    "keyword",
    "comment_text",
    "like_count",
    "published_at",
]

AUTO_LABELED_COLUMNS = [
    "comment_text",
    "weak_label",
    "confidence",
    "depression_score",
    "matched_keywords",
    "need_review",
]

INITIAL_TRAIN_COLUMNS = [
    "comment_text",
    "weak_label",
    "confidence",
    "depression_score",
    "matched_keywords",
    "need_review",
]

PHOBERT_PREDICTION_COLUMNS = [
    "comment_text",
    "source_weak_label",
    "source_confidence",
    "source_depression_score",
    "phobert_label",
    "probability",
    "prob_normal",
    "prob_depression",
]

VIDEO_METADATA_COLUMNS = [
    "video_id",
    "title",
    "channel",
    "published_at",
    "keyword",
]


def ensure_directories() -> None:
    """Tao thu muc output/log neu chua ton tai."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    PHOBERT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
