"""SQLite database for prediction history persistence."""

from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

_BACKEND_DIR = Path(__file__).resolve().parent  # web_demo/backend/

# In Docker, _BACKEND_DIR = /app/backend/
# The /app/backend/data dir is created by Dockerfile and mounted as a volume
DATA_DIR = _BACKEND_DIR / "data"

# Default DB path — stored in backend/data/ (mounted from host in docker-compose)
DEFAULT_DB_PATH = DATA_DIR / "predictions.db"

logger = logging.getLogger(__name__)

# ── Schema ───────────────────────────────────────────────────────────────────

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS predictions (
    id          TEXT PRIMARY KEY,
    text        TEXT NOT NULL,
    prediction  TEXT NOT NULL CHECK (prediction IN ('depression', 'normal')),
    confidence  REAL NOT NULL,
    prob_normal  REAL,
    prob_depression REAL,
    topic_id    INTEGER,
    topic_name  TEXT,
    risk_level  TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
    model_name  TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC);
"""


def get_db_path() -> Path:
    """Return the DB path, creating the data directory if needed."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the database schema."""
    conn = get_connection()
    try:
        conn.executescript(_CREATE_TABLE)
        conn.executescript(_CREATE_INDEX)
        conn.commit()
        logger.info("Database initialized at %s", get_db_path())
    finally:
        conn.close()


# ── CRUD ─────────────────────────────────────────────────────────────────────

def save_prediction(
    text: str,
    prediction: str,
    confidence: float,
    *,
    prob_normal: float = 0.0,
    prob_depression: float = 0.0,
    topic_id: Optional[int] = None,
    topic_name: Optional[str] = None,
    risk_level: str = "low",
    model_name: Optional[str] = None,
) -> dict:
    """Insert a prediction and return the saved record."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO predictions
                (id, text, prediction, confidence, prob_normal, prob_depression,
                 topic_id, topic_name, risk_level, model_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                text,
                prediction,
                confidence,
                prob_normal,
                prob_depression,
                topic_id,
                topic_name,
                risk_level,
                model_name,
            ),
        )
        conn.commit()
        row_id = cur.lastrowid

        # Fetch back the saved record
        row = conn.execute(
            "SELECT * FROM predictions WHERE rowid = ?", (row_id,)
        ).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


def get_history(limit: int = 50, offset: int = 0) -> list[dict]:
    """Fetch recent predictions, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM predictions
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_history_count() -> int:
    """Total number of stored predictions."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) as cnt FROM predictions").fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()


def delete_prediction(id: str) -> bool:
    """Delete a prediction by ID. Returns True if deleted."""
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM predictions WHERE id = ?", (id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def clear_history() -> int:
    """Delete all predictions. Returns count deleted."""
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM predictions")
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def get_prediction_stats() -> dict:
    """Aggregate statistics from stored predictions."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN prediction = 'depression' THEN 1 ELSE 0 END) as depression_count,
                SUM(CASE WHEN prediction = 'normal' THEN 1 ELSE 0 END) as normal_count,
                AVG(confidence) as avg_confidence,
                COUNT(DISTINCT topic_name) as unique_topics
            FROM predictions
            """
        ).fetchone()
        r = dict(row) if row else {}
        return {
            "total": r.get("total", 0),
            "depression_count": r.get("depression_count", 0),
            "normal_count": r.get("normal_count", 0),
            "avg_confidence": round(float(r.get("avg_confidence", 0) or 0), 4),
            "unique_topics": r.get("unique_topics", 0),
        }
    finally:
        conn.close()


# ── Auto-init on import ────────────────────────────────────────────────────────

try:
    init_db()
except Exception as e:
    logger.warning("Database init failed on import (may retry later): %s", e)
