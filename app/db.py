from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("IPOSTPILOT_DATA_DIR", str(ROOT / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(os.environ.get("IPOSTPILOT_DB", str(DATA_DIR / "ipostpilot.sqlite3")))


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with connect() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY, status TEXT NOT NULL, video_path TEXT,
              transcript_path TEXT, creator_id TEXT, mode TEXT, error TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS proposals (
              id TEXT PRIMARY KEY, job_id TEXT NOT NULL, start REAL, end REAL,
              title TEXT, hook TEXT, transcript TEXT, rationale TEXT, confidence REAL,
              status TEXT DEFAULT 'pending', edited_json TEXT, words_json TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS feedback (
              id INTEGER PRIMARY KEY AUTOINCREMENT, proposal_id TEXT NOT NULL,
              action TEXT NOT NULL, feedback TEXT, edited_json TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS creators (
              id TEXT PRIMARY KEY, name TEXT NOT NULL, preferences_json TEXT NOT NULL DEFAULT '{}',
              profile_json TEXT, profile_markdown TEXT, profile_status TEXT NOT NULL DEFAULT 'draft',
              profile_version INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS creator_examples (
              id TEXT PRIMARY KEY, creator_id TEXT NOT NULL, name TEXT NOT NULL,
              transcript TEXT NOT NULL, video_path TEXT, label TEXT NOT NULL DEFAULT 'approved',
              metadata_json TEXT NOT NULL DEFAULT '{}', created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        columns = {row["name"] for row in con.execute("PRAGMA table_info(jobs)")}
        if "creator_id" not in columns:
            con.execute("ALTER TABLE jobs ADD COLUMN creator_id TEXT")
        proposal_columns = {row["name"] for row in con.execute("PRAGMA table_info(proposals)")}
        if "words_json" not in proposal_columns:
            con.execute("ALTER TABLE proposals ADD COLUMN words_json TEXT")
        example_columns = {row["name"] for row in con.execute("PRAGMA table_info(creator_examples)")}
        if "video_path" not in example_columns:
            con.execute("ALTER TABLE creator_examples ADD COLUMN video_path TEXT")


def row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def json_or_none(value: str | None) -> Any:
    return json.loads(value) if value else None
