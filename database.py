"""
database.py – Dual-backend persistence for Gyan Saathi.

  • If SUPABASE_DB_URL is found in st.secrets or environment,
    uses PostgreSQL (via psycopg2) — persistent on Streamlit Cloud.
  • Otherwise falls back to local SQLite — works offline / in dev.

All public functions have the same signature regardless of backend.
"""

import json
import os
import hashlib
import secrets
from datetime import datetime

# ── Backend detection ─────────────────────────────────────────────────────────

def _get_db_url() -> str:
    """Return Supabase PostgreSQL URL from st.secrets or env, else ''."""
    try:
        import streamlit as st
        val = st.secrets.get("SUPABASE_DB_URL", "")
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv("SUPABASE_DB_URL", "")


USE_POSTGRES: bool = bool(_get_db_url())

# ── Connection helpers ────────────────────────────────────────────────────────

def _pg_connect():
    """Return a psycopg2 connection to Supabase."""
    import psycopg2
    import psycopg2.extras
    conn = psycopg2.connect(_get_db_url(), sslmode="require")
    conn.autocommit = False
    return conn


def _sqlite_path() -> str:
    return os.path.join(os.path.dirname(__file__), "gyan_saathi.db")


def _sqlite_connect():
    import sqlite3
    conn = sqlite3.connect(_sqlite_path())
    conn.row_factory = sqlite3.Row
    return conn


# ── Unified execute helper ────────────────────────────────────────────────────

def _exec(sql: str, params: tuple = (), fetchone=False, fetchall=False, returning=False):
    """
    Execute a single SQL statement against whichever backend is active.
    PostgreSQL uses %s placeholders; SQLite uses ?.
    We store SQL with ? and convert on the fly for PostgreSQL.
    """
    if USE_POSTGRES:
        pg_sql = sql.replace("?", "%s")
        # Replace SQLite-specific syntax
        pg_sql = pg_sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT",
                                "SERIAL PRIMARY KEY")
        pg_sql = pg_sql.replace("AUTOINCREMENT", "")
        conn = _pg_connect()
        try:
            import psycopg2.extras
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(pg_sql, params)
            result = None
            if fetchone:
                row = cur.fetchone()
                result = dict(row) if row else None
            elif fetchall:
                rows = cur.fetchall()
                result = [dict(r) for r in rows]
            elif returning:
                row = cur.fetchone()
                result = row[list(row.keys())[0]] if row else None
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        import sqlite3
        conn = _sqlite_connect()
        try:
            cur = conn.execute(sql, params)
            result = None
            if fetchone:
                row = cur.fetchone()
                result = dict(row) if row else None
            elif fetchall:
                rows = cur.fetchall()
                result = [dict(r) for r in rows]
            elif returning:
                result = cur.lastrowid
            conn.commit()
            return result
        finally:
            conn.close()


def _exec_script(statements: list[str]):
    """Execute multiple DDL statements (CREATE TABLE IF NOT EXISTS ...)."""
    if USE_POSTGRES:
        conn = _pg_connect()
        try:
            cur = conn.cursor()
            for stmt in statements:
                pg = stmt.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
                pg = pg.replace("AUTOINCREMENT", "")
                # Remove SQLite inline comments
                import re
                pg = re.sub(r'--[^\n]*', '', pg).strip()
                if pg:
                    cur.execute(pg)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        import sqlite3
        conn = _sqlite_connect()
        try:
            conn.executescript("\n".join(statements))
            conn.commit()
        finally:
            conn.close()


# ── Password helpers ──────────────────────────────────────────────────────────

def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()


# ── Schema ────────────────────────────────────────────────────────────────────

_DDL = [
    """CREATE TABLE IF NOT EXISTS users (
        id            SERIAL PRIMARY KEY,
        username      TEXT    NOT NULL UNIQUE,
        display_name  TEXT    NOT NULL,
        role          TEXT    NOT NULL DEFAULT 'student',
        avatar        TEXT    DEFAULT '🐯',
        salt          TEXT    NOT NULL,
        password_hash TEXT    NOT NULL,
        stars         INTEGER DEFAULT 0,
        streak        INTEGER DEFAULT 0,
        badges        TEXT    DEFAULT '[]',
        last_login    TEXT,
        created_at    TEXT    NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS sessions (
        id          SERIAL PRIMARY KEY,
        user_id     INTEGER,
        student     TEXT    NOT NULL,
        avatar      TEXT,
        started_at  TEXT    NOT NULL,
        finished_at TEXT,
        stars       INTEGER DEFAULT 0,
        mastery     TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS responses (
        id          SERIAL PRIMARY KEY,
        session_id  INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        skill       TEXT,
        difficulty  INTEGER,
        correct     INTEGER NOT NULL,
        answered_at TEXT    NOT NULL
    )""",
]


def init_db():
    """Create tables if they don't exist."""
    if USE_POSTGRES:
        _exec_script(_DDL)
    else:
        # SQLite: use AUTOINCREMENT version
        import sqlite3
        conn = _sqlite_connect()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    username      TEXT    NOT NULL UNIQUE,
                    display_name  TEXT    NOT NULL,
                    role          TEXT    NOT NULL DEFAULT 'student',
                    avatar        TEXT    DEFAULT '🐯',
                    salt          TEXT    NOT NULL,
                    password_hash TEXT    NOT NULL,
                    stars         INTEGER DEFAULT 0,
                    streak        INTEGER DEFAULT 0,
                    badges        TEXT    DEFAULT '[]',
                    last_login    TEXT,
                    created_at    TEXT    NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER,
                    student     TEXT    NOT NULL,
                    avatar      TEXT,
                    started_at  TEXT    NOT NULL,
                    finished_at TEXT,
                    stars       INTEGER DEFAULT 0,
                    mastery     TEXT
                );
                CREATE TABLE IF NOT EXISTS responses (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    skill       TEXT,
                    difficulty  INTEGER,
                    correct     INTEGER NOT NULL,
                    answered_at TEXT    NOT NULL
                );
            """)
            conn.commit()
        finally:
            conn.close()


# ── Auth ──────────────────────────────────────────────────────────────────────

def register_user(username: str, display_name: str, password: str,
                  role: str = "student", avatar: str = "🐯") -> tuple[bool, str]:
    username = username.strip().lower()
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."
    if not display_name.strip():
        return False, "Please enter your name."

    salt    = secrets.token_hex(16)
    pw_hash = _hash_password(password, salt)

    try:
        _exec(
            "INSERT INTO users (username, display_name, role, avatar, salt, password_hash, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, display_name.strip(), role, avatar,
             salt, pw_hash, datetime.utcnow().isoformat()),
        )
        return True, ""
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return False, "That username is already taken. Try another one!"
        return False, f"Registration failed: {e}"


def login_user(username: str, password: str) -> tuple[bool, dict | str]:
    username = username.strip().lower()
    row = _exec("SELECT * FROM users WHERE username = ?", (username,), fetchone=True)

    if row is None:
        return False, "Username not found. Please register first."

    expected = _hash_password(password, row["salt"])
    if expected != row["password_hash"]:
        return False, "Wrong password. Try again! 🔑"

    _exec("UPDATE users SET last_login=? WHERE id=?",
          (datetime.utcnow().isoformat(), row["id"]))

    row.pop("salt", None)
    row.pop("password_hash", None)
    return True, row


def get_user(user_id: int) -> dict | None:
    row = _exec("SELECT * FROM users WHERE id=?", (user_id,), fetchone=True)
    if row is None:
        return None
    row.pop("salt", None)
    row.pop("password_hash", None)
    return row


def update_user_stars_badges(user_id: int, stars: int, badges: list[str]):
    _exec("UPDATE users SET stars=?, badges=? WHERE id=?",
          (stars, json.dumps(badges), user_id))


# ── Quiz sessions ─────────────────────────────────────────────────────────────

def start_session(student: str, avatar: str, user_id: int | None = None) -> int:
    if USE_POSTGRES:
        return _exec(
            "INSERT INTO sessions (user_id, student, avatar, started_at) "
            "VALUES (?, ?, ?, ?) RETURNING id",
            (user_id, student, avatar, datetime.utcnow().isoformat()),
            returning=True,
        )
    else:
        return _exec(
            "INSERT INTO sessions (user_id, student, avatar, started_at) VALUES (?, ?, ?, ?)",
            (user_id, student, avatar, datetime.utcnow().isoformat()),
            returning=True,
        )


def record_response(session_id: int, question_id: int, skill: str,
                    difficulty: int, correct: bool):
    _exec(
        "INSERT INTO responses (session_id, question_id, skill, difficulty, correct, answered_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, question_id, skill, difficulty, int(correct),
         datetime.utcnow().isoformat()),
    )


def finish_session(session_id: int, stars: int, mastery: dict):
    _exec(
        "UPDATE sessions SET finished_at=?, stars=?, mastery=? WHERE id=?",
        (datetime.utcnow().isoformat(), stars, json.dumps(mastery), session_id),
    )


def get_all_sessions():
    return _exec(
        "SELECT * FROM sessions WHERE finished_at IS NOT NULL ORDER BY finished_at DESC",
        fetchall=True,
    ) or []


def get_skill_weakness_summary():
    rows = _exec(
        """SELECT skill, SUM(1-correct) AS wrong_count
           FROM responses
           WHERE session_id IN (
               SELECT id FROM sessions WHERE finished_at IS NOT NULL
           )
           GROUP BY skill""",
        fetchall=True,
    ) or []
    return {r["skill"]: r["wrong_count"] for r in rows}


# Initialise on import
init_db()
