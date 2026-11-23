"""memory/dazy_memory.py — DAZY 3-Layer Memory Subsystem.

Implements:
1. Working Memory (In-Memory, fast, transient context).
2. Event Memory (Short-Term SQLite with automatic TTL expiration).
3. Long-Term Memory (Persistent SQLite with FTS5 full-text search).
"""
from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("dazy.memory")


# ── 1. Working Memory ────────────────────────────────────────────────────────

@dataclass
class WorkingMemory:
    """Transient in-memory context: active task, current foreground app, and conversation state."""
    active_task_id: Optional[str] = None
    active_process_name: str = "desktop"
    active_window_title: str = ""
    latest_user_request: str = ""
    recent_dialogue_turns: list[dict[str, str]] = field(default_factory=list)
    scratchpad: dict[str, Any] = field(default_factory=dict)

    def set_active_window(self, process_name: str, window_title: str) -> None:
        self.active_process_name = process_name
        self.active_window_title = window_title

    def record_turn(self, role: str, text: str) -> None:
        self.recent_dialogue_turns.append({"role": role, "text": text, "time": str(time.time())})
        if len(self.recent_dialogue_turns) > 10:
            self.recent_dialogue_turns.pop(0)

    def clear_transient(self) -> None:
        self.active_task_id = None
        self.scratchpad.clear()


# ── 2. SQLite Persistent & Event Engine with FTS5 ────────────────────────────

class DazyMemoryEngine:
    """Manages Event Memory (TTL) and Long-Term Memory (FTS5) in a compact SQLite database."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            base = Path(__file__).resolve().parent
            db_path = base / "dazy_store.sqlite3"
        self.db_path = db_path
        self.working = WorkingMemory()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cur = conn.cursor()
            # 1. Short-term Event Memory (with TTL)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS event_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    details TEXT,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_event_expires ON event_memory(expires_at)")

            # 2. Long-term Persistent Memory
            cur.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    source TEXT DEFAULT 'user',
                    importance INTEGER DEFAULT 1,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    synced INTEGER DEFAULT 0,
                    UNIQUE(category, key)
                )
            """)

            # 3. SQLite FTS5 Full-Text Search virtual table
            try:
                cur.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS fts_memory USING fts5(
                        category,
                        key,
                        value,
                        content='long_term_memory',
                        content_rowid='id'
                    )
                """)
                # Triggers to keep FTS index synchronized
                cur.execute("""
                    CREATE TRIGGER IF NOT EXISTS trg_memory_ai AFTER INSERT ON long_term_memory BEGIN
                        INSERT INTO fts_memory(rowid, category, key, value) VALUES (new.id, new.category, new.key, new.value);
                    END;
                """)
                cur.execute("""
                    CREATE TRIGGER IF NOT EXISTS trg_memory_ad AFTER DELETE ON long_term_memory BEGIN
                        INSERT INTO fts_memory(fts_memory, rowid, category, key, value) VALUES('delete', old.id, old.category, old.key, old.value);
                    END;
                """)
                cur.execute("""
                    CREATE TRIGGER IF NOT EXISTS trg_memory_au AFTER UPDATE ON long_term_memory BEGIN
                        INSERT INTO fts_memory(fts_memory, rowid, category, key, value) VALUES('delete', old.id, old.category, old.key, old.value);
                        INSERT INTO fts_memory(rowid, category, key, value) VALUES (new.id, new.category, new.key, new.value);
                    END;
                """)
            except sqlite3.OperationalError:
                # In environments where FTS5 is not compiled, standard LIKE fallback is used
                pass

            # 4. Sync queue table for offline-first replication
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id INTEGER NOT NULL,
                    operation TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    attempts INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    # ── Event Memory Operations (Short-Term with TTL) ─────────────────────────

    def record_event(
        self,
        event_type: str,
        category: str,
        summary: str,
        details: str = "",
        ttl_seconds: float = 604800.0,  # default 7 days
    ) -> int:
        now = time.time()
        expires = now + ttl_seconds
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO event_memory (event_type, category, summary, details, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_type, category, summary, details, now, expires),
            )
            conn.commit()
            return cur.lastrowid or 0

    def prune_expired_events(self) -> int:
        now = time.time()
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM event_memory WHERE expires_at < ?", (now,))
            deleted = cur.rowcount
            conn.commit()
            return deleted

    def get_recent_events(self, limit: int = 15) -> list[dict[str, Any]]:
        self.prune_expired_events()
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT event_type, category, summary, details, created_at FROM event_memory ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]

    # ── Long-Term Memory Operations (Persistent & FTS5) ──────────────────────

    def remember(
        self,
        key: str,
        value: str,
        category: str = "notes",
        source: str = "user",
        importance: int = 1,
    ) -> bool:
        now = time.time()
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO long_term_memory (category, key, value, source, importance, created_at, updated_at, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(category, key) DO UPDATE SET
                    value=excluded.value,
                    importance=excluded.importance,
                    updated_at=excluded.updated_at,
                    synced=0
                """,
                (category, key, value, source, importance, now, now),
            )
            rec_id = cur.lastrowid
            # Enqueue for cloud sync
            cur.execute(
                """
                INSERT INTO sync_queue (table_name, record_id, operation, payload, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("long_term_memory", rec_id or 0, "UPSERT", f"{category}:{key}", now),
            )
            conn.commit()
            return True

    def forget(self, key: str, category: str = "notes") -> bool:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM long_term_memory WHERE category=? AND key=?", (category, key))
            deleted = cur.rowcount > 0
            if deleted:
                cur.execute(
                    """
                    INSERT INTO sync_queue (table_name, record_id, operation, payload, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    ("long_term_memory", 0, "DELETE", f"{category}:{key}", time.time()),
                )
            conn.commit()
            return deleted

    def search_long_term(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        """Searches long-term memory using SQLite FTS5 with ranked bm25 scores, falling back to LIKE."""
        clean_q = "".join(c for c in query if c.isalnum() or c.isspace()).strip()
        if not clean_q:
            return self.get_all_long_term(limit=limit)

        with self._get_connection() as conn:
            cur = conn.cursor()
            # Try FTS5 match first
            try:
                cur.execute(
                    """
                    SELECT m.category, m.key, m.value, m.importance, m.updated_at
                    FROM fts_memory f
                    JOIN long_term_memory m ON f.rowid = m.id
                    WHERE fts_memory MATCH ?
                    ORDER BY bm25(fts_memory)
                    LIMIT ?
                    """,
                    (clean_q, limit),
                )
                rows = [dict(r) for r in cur.fetchall()]
                if rows:
                    return rows
            except sqlite3.OperationalError:
                pass

            # Fallback to LIKE
            like_pat = f"%{clean_q}%"
            cur.execute(
                """
                SELECT category, key, value, importance, updated_at
                FROM long_term_memory
                WHERE key LIKE ? OR value LIKE ? OR category LIKE ?
                ORDER BY importance DESC, updated_at DESC
                LIMIT ?
                """,
                (like_pat, like_pat, like_pat, limit),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_all_long_term(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT category, key, value, importance, updated_at, synced FROM long_term_memory ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]

    def format_prompt_context(self) -> str:
        """Formats active working memory + key persistent memories into DAZY prompt context."""
        parts = []
        if self.working.active_process_name and self.working.active_process_name != "desktop":
            parts.append(f"[Active Screen Context: {self.working.active_process_name} — {self.working.active_window_title}]")

        memories = self.get_all_long_term(limit=12)
        if memories:
            parts.append("[Known User Facts & Memory:]")
            for m in memories:
                parts.append(f"- {m['category']}/{m['key']}: {m['value']}")

        return "\n".join(parts)


dazy_memory = DazyMemoryEngine()
