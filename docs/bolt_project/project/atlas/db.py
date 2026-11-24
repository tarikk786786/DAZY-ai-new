"""Atlas SQLite layer. One row per capability entry, fully evidence-tracked."""
import sqlite3
import threading
from typing import Any

from . import config

_local = threading.local()

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS entries (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    capability TEXT NOT NULL,
    subcapability TEXT NOT NULL DEFAULT '',
    category_id TEXT NOT NULL REFERENCES categories(id),
    repo_url TEXT NOT NULL,
    docs_url TEXT NOT NULL DEFAULT '',
    entry_type TEXT NOT NULL DEFAULT 'library'
        CHECK (entry_type IN ('library','api','model','mcp','skill','dataset','framework','tool')),
    -- All of these start as UNKNOWN. Only real verification changes them.
    licence TEXT NOT NULL DEFAULT 'unknown',
    cost_class TEXT NOT NULL DEFAULT 'unknown'
        CHECK (cost_class IN ('oss','free_api_quota','free_hosted','paid','freemium','unknown')),
    maintenance TEXT NOT NULL DEFAULT 'unknown'
        CHECK (maintenance IN ('active','stale','archived','unknown')),
    security_note TEXT NOT NULL DEFAULT '',
    runtime TEXT NOT NULL DEFAULT 'unknown',
    platform TEXT NOT NULL DEFAULT 'unknown',
    languages TEXT NOT NULL DEFAULT '',        -- human languages supported (e.g. hi,en)
    description TEXT NOT NULL DEFAULT '',
    alternatives TEXT NOT NULL DEFAULT '',      -- comma-separated entry ids
    -- Verification evidence — the heart of the honesty contract.
    verified_at TEXT,                           -- NULL = never verified
    verified_evidence TEXT NOT NULL DEFAULT '', -- what we actually saw (HTTP codes, fields)
    stars INTEGER,
    last_commit TEXT,
    archived INTEGER,
    last_verified_status INTEGER,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_entries_category ON entries(category_id);
CREATE INDEX IF NOT EXISTS idx_entries_repo ON entries(repo_url);
CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(name, description, capability, content='entries', content_rowid='rowid');
CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
    INSERT INTO entries_fts(rowid, name, description, capability) VALUES (new.rowid, new.name, new.description, new.capability);
END;
CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, name, description, capability) VALUES ('delete', old.rowid, old.name, old.description, old.capability);
END;
"""


def conn() -> sqlite3.Connection:
    c = getattr(_local, "conn", None)
    if c is None:
        c = sqlite3.connect(config.DB_PATH, timeout=10, check_same_thread=False)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA foreign_keys=ON")
        _local.conn = c
    return c


def migrate() -> None:
    with conn():
        conn().executescript(SCHEMA)


def query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    return [dict(r) for r in conn().execute(sql, params).fetchall()]


def one(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    row = conn().execute(sql, params).fetchone()
    return dict(row) if row else None


def execute(sql: str, params: tuple = ()) -> None:
    with conn():
        conn().execute(sql, params)
