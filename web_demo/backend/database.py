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
    user_id     INTEGER REFERENCES users(id),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC);
"""

_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

_CREATE_USERS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
"""

_CREATE_PREDICTIONS_USER_INDEX = """
CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id);
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
        init_users_table()
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
    user_id: Optional[int] = None,
) -> dict:
    """Insert a prediction and return the saved record."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO predictions
                (id, text, prediction, confidence, prob_normal, prob_depression,
                 topic_id, topic_name, risk_level, model_name, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                user_id,
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


def get_prediction_by_id(id: str) -> Optional[dict]:
    """Fetch a single prediction by ID."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM predictions WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_history(limit: int = 50, offset: int = 0, user_id: Optional[int] = None) -> list[dict]:
    """Fetch recent predictions, newest first."""
    conn = get_connection()
    try:
        if user_id:
            rows = conn.execute(
                """
                SELECT * FROM predictions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset),
            ).fetchall()
        else:
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


def get_history_count(user_id: Optional[int] = None) -> int:
    """Total number of stored predictions."""
    conn = get_connection()
    try:
        if user_id:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM predictions WHERE user_id = ?", (user_id,)
            ).fetchone()
        else:
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


# ── Users Table ────────────────────────────────────────────────────────────────

def init_users_table() -> None:
    """Initialize users table and create default admin/user."""
    conn = get_connection()
    try:
        conn.executescript(_CREATE_USERS_TABLE)
        conn.execute(_CREATE_USERS_INDEX)
        conn.execute(_CREATE_PREDICTIONS_USER_INDEX)

        # Check if default users exist
        admin = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
        if not admin:
            from auth import get_password_hash
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", get_password_hash("admin123"), "admin")
            )
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("user", get_password_hash("user123"), "user")
            )
            conn.commit()
            logger.info("Default users created: admin, user")
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[dict]:
    """Fetch user by username."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, username, password_hash, role, is_active, created_at FROM users WHERE username = ? AND is_active = 1",
            (username,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Fetch user by ID."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, username, role, is_active, created_at FROM users WHERE id = ? AND is_active = 1",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_user(username: str, password_hash: str) -> Optional[dict]:
    """Create a new user."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, "user")
        )
        conn.commit()
        return get_user_by_id(cur.lastrowid)
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_all_users() -> list[dict]:
    """Get all users (for admin)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, username, role, is_active, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_admin_stats() -> dict:
    """Get stats for admin dashboard."""
    conn = get_connection()
    try:
        total_users = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE is_active = 1").fetchone()["cnt"]
        total_predictions = conn.execute("SELECT COUNT(*) as cnt FROM predictions").fetchone()["cnt"]
        predictions_by_user = conn.execute(
            """
            SELECT u.username, COUNT(p.id) as pred_count
            FROM users u
            LEFT JOIN predictions p ON u.id = p.user_id
            GROUP BY u.id, u.username
            ORDER BY pred_count DESC
            """,
        ).fetchall()
        recent_predictions = conn.execute(
            """
            SELECT p.*, u.username
            FROM predictions p
            LEFT JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
            LIMIT 10
            """,
        ).fetchall()
        return {
            "total_users": total_users,
            "total_predictions": total_predictions,
            "predictions_by_user": [dict(row) for row in predictions_by_user],
            "recent_predictions": [dict(row) for row in recent_predictions],
        }
    finally:
        conn.close()


# ── Auto-init on import ────────────────────────────────────────────────────────

try:
    init_db()
except Exception as e:
    logger.warning("Database init failed on import (may retry later): %s", e)
