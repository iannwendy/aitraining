"""Quản lý tiến trình crawl nền cho dashboard web."""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
import json
from typing import Any

from yt_depression_crawler.labeling.auto_labeler import auto_label_comments
from yt_depression_crawler.modeling.baseline.baseline_model import train_baseline_model
from yt_depression_crawler.processing.cleaner import clean_comments
from yt_depression_crawler.core.config import (
    AUTO_LABELED_FILE,
    BASELINE_GOLD_METRICS_FILE,
    BASELINE_METRICS_FILE,
    CLEANED_FILE,
    GOLD_REVIEW_FILE,
    INITIAL_TRAIN_FILE,
    LABELING_REPORT_FILE,
    LOG_FILE,
    PHOBERT_GOLD_METRICS_FILE,
    PHOBERT_ACTIVE_LEARNING_FILE,
    PHOBERT_CONFIDENT_PREDICTIONS_FILE,
    PHOBERT_METRICS_FILE,
    PHOBERT_POSTPROCESS_REPORT_FILE,
    PHOBERT_REMAINING_PREDICTIONS_FILE,
    PROCESSED_VIDEOS_FILE,
    RAW_FILE,
    REVIEW_SAMPLES_FILE,
    TARGET_RAW_COMMENTS,
    TEST_FILE,
    TRAIN_FILE,
    YOUTUBE_API_KEY,
    VAL_FILE,
    ensure_directories,
)
from yt_depression_crawler.ingestion.crawler import YouTubeCommentCrawler
from yt_depression_crawler.labeling.dataset_sampler import build_initial_train_dataset
from yt_depression_crawler.labeling.gold_baseline_eval import evaluate_baseline_on_gold
from yt_depression_crawler.labeling.gold_builder import build_gold_review_set
from yt_depression_crawler.pipelines.gold_pipeline import run_gold_pipeline
from yt_depression_crawler.core.keywords import get_keywords
from yt_depression_crawler.pipelines.ml_pipeline import run_ml_pipeline
from yt_depression_crawler.labeling.review_sampler import create_review_samples
from yt_depression_crawler.labeling.review_evaluator import evaluate_weak_labels_on_gold
from yt_depression_crawler.processing.storage import count_csv_rows, load_processed_videos
from yt_depression_crawler.modeling.train_splitter import create_train_val_test_splits
from yt_depression_crawler.ingestion.youtube_client import YouTubeClient

logger = logging.getLogger(__name__)


class CrawlManager:
    """Start/stop crawler trong một background thread."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._label_thread: threading.Thread | None = None
        self._ml_thread: threading.Thread | None = None
        self._phobert_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._state: dict[str, Any] = {
            "running": False,
            "stop_requested": False,
            "api_state": "ready" if YOUTUBE_API_KEY else "missing_api_key",
            "last_error": None,
            "started_at": None,
            "finished_at": None,
            "current_keyword": None,
            "current_video_id": None,
            "current_video_title": None,
            "total_videos_found": 0,
            "total_videos_crawled": 0,
            "total_videos_skipped": 0,
            "total_raw_comments_saved": 0,
            "quota_exceeded": False,
            "labeling_running": False,
            "labeling_state": "idle",
            "labeling_task": None,
            "labeling_started_at": None,
            "labeling_finished_at": None,
            "labeling_last_error": None,
            "ml_running": False,
            "ml_state": "idle",
            "ml_task": None,
            "ml_started_at": None,
            "ml_finished_at": None,
            "ml_last_error": None,
            "phobert_running": False,
            "phobert_state": "idle",
            "phobert_task": None,
            "phobert_started_at": None,
            "phobert_finished_at": None,
            "phobert_last_error": None,
        }

    def start(self) -> tuple[bool, str]:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False, "Crawler dang chay."
            if self._label_thread and self._label_thread.is_alive():
                return False, "Labeling task dang chay, hay doi labeling xong."
            if self._ml_thread and self._ml_thread.is_alive():
                return False, "ML task dang chay, hay doi ML xong."
            if self._phobert_thread and self._phobert_thread.is_alive():
                return False, "PhoBERT task dang chay, hay doi PhoBERT xong."
            if not YOUTUBE_API_KEY:
                self._state["api_state"] = "missing_api_key"
                return False, "Thieu YOUTUBE_API_KEY trong .env."

            self._stop_event.clear()
            self._state.update(
                {
                    "running": True,
                    "stop_requested": False,
                    "api_state": "running",
                    "last_error": None,
                    "started_at": self._now(),
                    "finished_at": None,
                    "current_keyword": None,
                    "current_video_id": None,
                    "current_video_title": None,
                    "total_videos_found": 0,
                    "total_videos_crawled": 0,
                    "total_videos_skipped": 0,
                    "total_raw_comments_saved": 0,
                    "quota_exceeded": False,
                }
            )
            self._thread = threading.Thread(target=self._run_crawler, name="crawler-worker", daemon=True)
            self._thread.start()

        return True, "Da bat dau crawl."

    def stop(self) -> tuple[bool, str]:
        with self._lock:
            if not self._thread or not self._thread.is_alive():
                return False, "Crawler khong chay."
            self._stop_event.set()
            self._state["stop_requested"] = True
            self._state["api_state"] = "stopping"
        return True, "Da gui yeu cau dung."

    def run_auto_label(self) -> tuple[bool, str]:
        return self._start_labeling_task("auto_label", auto_label_comments)

    def build_initial_train(self) -> tuple[bool, str]:
        return self._start_labeling_task("build_initial_train", build_initial_train_dataset)

    def run_labeling_pipeline(self) -> tuple[bool, str]:
        def task() -> dict:
            auto_report = auto_label_comments()
            train_report = build_initial_train_dataset()
            return {"auto_labeling": auto_report, "initial_train": train_report}

        return self._start_labeling_task("labeling_pipeline", task)

    def create_review_set(self) -> tuple[bool, str]:
        return self._start_ml_task("create_review_samples", create_review_samples)

    def create_train_splits(self) -> tuple[bool, str]:
        return self._start_ml_task("create_train_splits", create_train_val_test_splits)

    def train_baseline(self) -> tuple[bool, str]:
        return self._start_ml_task("train_baseline", train_baseline_model)

    def run_training_pipeline(self) -> tuple[bool, str]:
        return self._start_ml_task("ml_pipeline", run_ml_pipeline)

    def build_gold_review(self) -> tuple[bool, str]:
        return self._start_ml_task("build_gold_review", build_gold_review_set)

    def evaluate_weak_on_gold(self) -> tuple[bool, str]:
        return self._start_ml_task("evaluate_weak_on_gold", evaluate_weak_labels_on_gold)

    def evaluate_baseline_gold(self) -> tuple[bool, str]:
        return self._start_ml_task("evaluate_baseline_gold", evaluate_baseline_on_gold)

    def run_gold_review_pipeline(self) -> tuple[bool, str]:
        return self._start_ml_task("gold_pipeline", run_gold_pipeline)

    def train_phobert(self) -> tuple[bool, str]:
        def task() -> dict:
            from yt_depression_crawler.modeling.phobert.phobert_train import train_phobert_first

            return train_phobert_first()

        return self._start_phobert_task("train_phobert", task)

    def predict_phobert_remaining(self) -> tuple[bool, str]:
        def task() -> dict:
            from yt_depression_crawler.modeling.phobert.phobert_predict import predict_remaining_comments

            return predict_remaining_comments()

        return self._start_phobert_task("predict_phobert_remaining", task)

    def postprocess_phobert_predictions(self) -> tuple[bool, str]:
        def task() -> dict:
            from yt_depression_crawler.modeling.phobert.phobert_postprocess import build_phobert_followup_files

            return build_phobert_followup_files()

        return self._start_phobert_task("postprocess_phobert", task)

    def run_phobert_first_pipeline(self) -> tuple[bool, str]:
        def task() -> dict:
            from yt_depression_crawler.pipelines.phobert_pipeline import run_phobert_pipeline

            return run_phobert_pipeline()

        return self._start_phobert_task("phobert_pipeline", task)

    def status(self) -> dict[str, Any]:
        raw_count = count_csv_rows(RAW_FILE)
        cleaned_count = count_csv_rows(CLEANED_FILE)
        auto_labeled_count = count_csv_rows(AUTO_LABELED_FILE)
        initial_train_count = count_csv_rows(INITIAL_TRAIN_FILE)
        review_count = count_csv_rows(REVIEW_SAMPLES_FILE)
        gold_count = count_csv_rows(GOLD_REVIEW_FILE)
        phobert_prediction_count = count_csv_rows(PHOBERT_REMAINING_PREDICTIONS_FILE)
        phobert_confident_count = count_csv_rows(PHOBERT_CONFIDENT_PREDICTIONS_FILE)
        phobert_active_count = count_csv_rows(PHOBERT_ACTIVE_LEARNING_FILE)
        train_count = count_csv_rows(TRAIN_FILE)
        val_count = count_csv_rows(VAL_FILE)
        test_count = count_csv_rows(TEST_FILE)
        processed_count = len(load_processed_videos(PROCESSED_VIDEOS_FILE))
        target = TARGET_RAW_COMMENTS
        progress_percent = None
        if target:
            progress_percent = min(round(raw_count / target * 100, 2), 100.0)

        with self._lock:
            state = dict(self._state)

        state.update(
            {
                "raw_comments": raw_count,
                "cleaned_comments": cleaned_count,
                "auto_labeled_comments": auto_labeled_count,
                "initial_train_rows": initial_train_count,
                "review_samples": review_count,
                "gold_review_rows": gold_count,
                "phobert_prediction_rows": phobert_prediction_count,
                "phobert_confident_rows": phobert_confident_count,
                "phobert_active_learning_rows": phobert_active_count,
                "train_rows": train_count,
                "val_rows": val_count,
                "test_rows": test_count,
                "processed_videos": processed_count,
                "target_raw_comments": target,
                "progress_percent": progress_percent,
                "labeling_report": self._read_labeling_report(),
                "baseline_metrics": self._read_json_file(BASELINE_METRICS_FILE),
                "baseline_gold_metrics": self._read_json_file(BASELINE_GOLD_METRICS_FILE),
                "phobert_metrics": self._read_json_file(PHOBERT_METRICS_FILE),
                "phobert_gold_metrics": self._read_json_file(PHOBERT_GOLD_METRICS_FILE),
                "phobert_postprocess": self._read_json_file(PHOBERT_POSTPROCESS_REPORT_FILE),
                "log_tail": self._tail_log(),
            }
        )
        return state

    def _start_labeling_task(self, task_name: str, task_func) -> tuple[bool, str]:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False, "Crawler dang chay, hay dung crawl truoc khi labeling."
            if self._label_thread and self._label_thread.is_alive():
                return False, "Labeling task dang chay."
            if self._ml_thread and self._ml_thread.is_alive():
                return False, "ML task dang chay."
            if self._phobert_thread and self._phobert_thread.is_alive():
                return False, "PhoBERT task dang chay."

            self._state.update(
                {
                    "labeling_running": True,
                    "labeling_state": "running",
                    "labeling_task": task_name,
                    "labeling_started_at": self._now(),
                    "labeling_finished_at": None,
                    "labeling_last_error": None,
                }
            )
            self._label_thread = threading.Thread(
                target=self._run_labeling_task,
                args=(task_name, task_func),
                name=f"{task_name}-worker",
                daemon=True,
            )
            self._label_thread.start()

        return True, f"Da bat dau {task_name}."

    def _start_ml_task(self, task_name: str, task_func) -> tuple[bool, str]:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False, "Crawler dang chay, hay dung crawl truoc khi chuan bi train."
            if self._label_thread and self._label_thread.is_alive():
                return False, "Labeling task dang chay."
            if self._ml_thread and self._ml_thread.is_alive():
                return False, "ML task dang chay."
            if self._phobert_thread and self._phobert_thread.is_alive():
                return False, "PhoBERT task dang chay."

            self._state.update(
                {
                    "ml_running": True,
                    "ml_state": "running",
                    "ml_task": task_name,
                    "ml_started_at": self._now(),
                    "ml_finished_at": None,
                    "ml_last_error": None,
                }
            )
            self._ml_thread = threading.Thread(
                target=self._run_ml_task,
                args=(task_name, task_func),
                name=f"{task_name}-worker",
                daemon=True,
            )
            self._ml_thread.start()

        return True, f"Da bat dau {task_name}."

    def _start_phobert_task(self, task_name: str, task_func) -> tuple[bool, str]:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False, "Crawler dang chay, hay dung crawl truoc khi train PhoBERT."
            if self._label_thread and self._label_thread.is_alive():
                return False, "Labeling task dang chay."
            if self._ml_thread and self._ml_thread.is_alive():
                return False, "ML task dang chay."
            if self._phobert_thread and self._phobert_thread.is_alive():
                return False, "PhoBERT task dang chay."

            self._state.update(
                {
                    "phobert_running": True,
                    "phobert_state": "running",
                    "phobert_task": task_name,
                    "phobert_started_at": self._now(),
                    "phobert_finished_at": None,
                    "phobert_last_error": None,
                }
            )
            self._phobert_thread = threading.Thread(
                target=self._run_phobert_task,
                args=(task_name, task_func),
                name=f"{task_name}-worker",
                daemon=True,
            )
            self._phobert_thread.start()

        return True, f"Da bat dau {task_name}."

    def _run_labeling_task(self, task_name: str, task_func) -> None:
        try:
            result = task_func()
            with self._lock:
                self._state.update(
                    {
                        "labeling_running": False,
                        "labeling_state": "completed",
                        "labeling_task": task_name,
                        "labeling_finished_at": self._now(),
                        "labeling_last_error": None,
                        "labeling_last_result": result,
                    }
                )
        except Exception as exc:  # noqa: BLE001 - hien thi loi len dashboard
            logger.exception("Labeling task failed: %s", exc)
            with self._lock:
                self._state.update(
                    {
                        "labeling_running": False,
                        "labeling_state": "error",
                        "labeling_task": task_name,
                        "labeling_finished_at": self._now(),
                        "labeling_last_error": str(exc),
                    }
                )

    def _run_ml_task(self, task_name: str, task_func) -> None:
        try:
            result = task_func()
            with self._lock:
                self._state.update(
                    {
                        "ml_running": False,
                        "ml_state": "completed",
                        "ml_task": task_name,
                        "ml_finished_at": self._now(),
                        "ml_last_error": None,
                        "ml_last_result": result,
                    }
                )
        except Exception as exc:  # noqa: BLE001 - dashboard can hien thi loi
            logger.exception("ML task failed: %s", exc)
            with self._lock:
                self._state.update(
                    {
                        "ml_running": False,
                        "ml_state": "error",
                        "ml_task": task_name,
                        "ml_finished_at": self._now(),
                        "ml_last_error": str(exc),
                    }
                )

    def _run_phobert_task(self, task_name: str, task_func) -> None:
        try:
            result = task_func()
            with self._lock:
                self._state.update(
                    {
                        "phobert_running": False,
                        "phobert_state": "completed",
                        "phobert_task": task_name,
                        "phobert_finished_at": self._now(),
                        "phobert_last_error": None,
                        "phobert_last_result": result,
                    }
                )
        except Exception as exc:  # noqa: BLE001 - dashboard can hien thi loi
            logger.exception("PhoBERT task failed: %s", exc)
            with self._lock:
                self._state.update(
                    {
                        "phobert_running": False,
                        "phobert_state": "error",
                        "phobert_task": task_name,
                        "phobert_finished_at": self._now(),
                        "phobert_last_error": str(exc),
                    }
                )

    def _run_crawler(self) -> None:
        try:
            ensure_directories()
            client = YouTubeClient(YOUTUBE_API_KEY)
            crawler = YouTubeCommentCrawler(
                client,
                stop_event=self._stop_event,
                progress_callback=self._on_progress,
            )
            keywords = get_keywords()
            stats = crawler.run(keywords)
            cleaned_count = clean_comments(RAW_FILE, CLEANED_FILE)

            with self._lock:
                self._state.update(
                    {
                        "running": False,
                        "stop_requested": False,
                        "finished_at": self._now(),
                        "total_videos_found": stats.total_videos_found,
                        "total_videos_crawled": stats.total_videos_crawled,
                        "total_videos_skipped": stats.total_videos_skipped,
                        "total_raw_comments_saved": stats.total_raw_comments_saved,
                        "quota_exceeded": client.quota_exceeded,
                        "api_state": self._finish_state(client.quota_exceeded),
                        "cleaned_comments_last_run": cleaned_count,
                    }
                )
        except Exception as exc:  # noqa: BLE001 - dashboard can hien thi loi thay vi crash web server
            logger.exception("Crawler worker failed: %s", exc)
            with self._lock:
                self._state.update(
                    {
                        "running": False,
                        "stop_requested": False,
                        "api_state": "error",
                        "last_error": str(exc),
                        "finished_at": self._now(),
                    }
                )

    def _on_progress(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._state.update(
                {
                    "current_keyword": payload.get("keyword"),
                    "current_video_id": payload.get("video_id"),
                    "current_video_title": payload.get("video_title"),
                    "total_videos_found": payload.get("total_videos_found", 0),
                    "total_videos_crawled": payload.get("total_videos_crawled", 0),
                    "total_videos_skipped": payload.get("total_videos_skipped", 0),
                    "total_raw_comments_saved": payload.get("total_raw_comments_saved", 0),
                    "quota_exceeded": payload.get("quota_exceeded", False),
                    "last_error": payload.get("last_error_reason"),
                }
            )

    def _finish_state(self, quota_exceeded: bool) -> str:
        if quota_exceeded:
            return "quota_exceeded"
        if self._stop_event.is_set():
            return "stopped"
        return "completed"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _tail_log(lines: int = 80) -> list[str]:
        if not LOG_FILE.exists():
            return []
        with LOG_FILE.open("r", encoding="utf-8", errors="replace") as file:
            return file.readlines()[-lines:]

    @staticmethod
    def _read_labeling_report() -> dict:
        return CrawlManager._read_json_file(LABELING_REPORT_FILE)

    @staticmethod
    def _read_json_file(path) -> dict:
        if not path.exists() or path.stat().st_size == 0:
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
