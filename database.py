"""
database.py – Local SQLite persistence for Gyan Saathi.

Tables:
  users     – registered accounts (students + teachers)
  sessions  – one row per quiz attempt
  responses – one row per question answered
"""

import sqlite3
import json
import os
import hashlib
import secrets
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "gyan_saathi.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()


# ── Schema ────────────────────────────────────────────────────────────────────

def init_db():
    """Create tables if they don't exist yet."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                username     TEXT    NOT NULL UNIQUE,
                display_name TEXT    NOT NULL,
                role         TEXT    NOT NULL DEFAULT 'student',  -- 'student' | 'teacher'
                avatar       TEXT    DEFAULT '🐯',
                salt         TEXT    NOT NULL,
                password_hash TEXT   NOT NULL,
                stars        INTEGER DEFAULT 0,
                streak       INTEGER DEFAULT 0,
                badges       TEXT    DEFAULT '[]',  -- JSON list of badge names
                last_login   TEXT,
                created_at   TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER REFERENCES users(id),
                student     TEXT    NOT NULL,
                avatar      TEXT,
                started_at  TEXT    NOT NULL,
                finished_at TEXT,
                stars       INTEGER DEFAULT 0,
                mastery     TEXT     -- JSON blob: {skill: score}
            );

            CREATE TABLE IF NOT EXISTS responses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  INTEGER NOT NULL REFERENCES sessions(id),
                question_id INTEGER NOT NULL,
                skill       TEXT,
                difficulty  INTEGER,
                correct     INTEGER NOT NULL,  -- 1 or 0
                answered_at TEXT    NOT NULL
            );
        """)


# ── Auth ──────────────────────────────────────────────────────────────────────

def register_user(username: str, display_name: str, password: str,
                  role: str = "student", avatar: str = "🐯") -> tuple[bool, str]:
    """
    Register a new user.
    Returns (True, "") on success or (False, error_message) on failure.
    """
    username = username.strip().lower()
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."
    if not display_name.strip():
        return False, "Please enter your name."

    salt = secrets.token_hex(16)
    pw_hash = _hash_password(password, salt)

    try:
        with _connect() as conn:
            conn.execute(
                """INSERT INTO users
                   (username, display_name, role, avatar, salt, password_hash, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (username, display_name.strip(), role, avatar,
                 salt, pw_hash, datetime.utcnow().isoformat()),
            )
        return True, ""
    except sqlite3.IntegrityError:
        return False, "That username is already taken. Try another one!"


def login_user(username: str, password: str) -> tuple[bool, dict | str]:
    """
    Verify credentials.
    Returns (True, user_dict) on success or (False, error_message) on failure.
    """
    username = username.strip().lower()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

    if row is None:
        return False, "Username not found. Please register first."

    row = dict(row)
    expected = _hash_password(password, row["salt"])
    if expected != row["password_hash"]:
        return False, "Wrong password. Try again! 🔑"

    # Update last_login
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET last_login=? WHERE id=?",
            (datetime.utcnow().isoformat(), row["id"]),
        )

    row.pop("salt", None)
    row.pop("password_hash", None)
    return True, row


def get_user(user_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id=?", (user_id,)
        ).fetchone()
    if row is None:
        return None
    d = dict(row)
    d.pop("salt", None)
    d.pop("password_hash", None)
    return d


def update_user_stars_badges(user_id: int, stars: int, badges: list[str]):
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET stars=?, badges=? WHERE id=?",
            (stars, json.dumps(badges), user_id),
        )


# ── Quiz sessions ─────────────────────────────────────────────────────────────

def start_session(student: str, avatar: str, user_id: int | None = None) -> int:
    """Open a new quiz session and return its id."""
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO sessions (user_id, student, avatar, started_at) VALUES (?, ?, ?, ?)",
            (user_id, student, avatar, datetime.utcnow().isoformat()),
        )
        return cur.lastrowid


def record_response(session_id: int, question_id: int, skill: str,
                    difficulty: int, correct: bool):
    with _connect() as conn:
        conn.execute(
            """INSERT INTO responses
               (session_id, question_id, skill, difficulty, correct, answered_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, question_id, skill, difficulty, int(correct),
             datetime.utcnow().isoformat()),
        )


def finish_session(session_id: int, stars: int, mastery: dict):
    with _connect() as conn:
        conn.execute(
            """UPDATE sessions
               SET finished_at=?, stars=?, mastery=?
               WHERE id=?""",
            (datetime.utcnow().isoformat(), stars,
             json.dumps(mastery), session_id),
        )


def get_all_sessions():
    """Return all finished sessions (for Teacher dashboard)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions WHERE finished_at IS NOT NULL ORDER BY finished_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_skill_weakness_summary():
    """
    Return {skill: wrong_count} aggregated across all finished sessions.
    Used by the Teacher page.
    """
    with _connect() as conn:
        rows = conn.execute(
            """SELECT skill, SUM(1-correct) AS wrong_count
               FROM responses
               WHERE session_id IN (
                   SELECT id FROM sessions WHERE finished_at IS NOT NULL
               )
               GROUP BY skill"""
        ).fetchall()
        return {r["skill"]: r["wrong_count"] for r in rows}


# Initialise DB on import
init_db()
