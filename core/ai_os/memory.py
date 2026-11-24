"""core/ai_os/memory.py — Memory Provenance & Audit Subsystem."""
from __future__ import annotations

import enum
import logging
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("dazy.ai_os.memory")


class MemoryScope(str, enum.Enum):
    WORKING = "WORKING"
    SHORT_TERM = "SHORT_TERM"
    LONG_TERM = "LONG_TERM"
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    PROCEDURAL = "PROCEDURAL"
    PROJECT = "PROJECT"


class SensitivityLevel(str, enum.Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class MemoryRecord(BaseModel):
    id: str
    scope: MemoryScope
    content: str
    owner: str = "Tarik"
    source: str = "conversation"
    correlation_id: str = ""
    sensitivity: SensitivityLevel = SensitivityLevel.INTERNAL
    task_id: Optional[str] = None
    retrieval_count: int = 0
    created_at: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryAuditService:
    """Manages memory items with full provenance, retrieval auditing, and user retention."""

    _instance: Optional[MemoryAuditService] = None
    _lock = threading.RLock()

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path(__file__).resolve().parent.parent.parent / "memory" / "ai_os_provenance.db"
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._records: Dict[str, MemoryRecord] = {}

    @classmethod
    def get_instance(cls) -> MemoryAuditService:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_items (
                    id TEXT PRIMARY KEY,
                    scope TEXT,
                    content TEXT,
                    owner TEXT,
                    source TEXT,
                    correlation_id TEXT,
                    sensitivity TEXT,
                    task_id TEXT,
                    retrieval_count INTEGER,
                    created_at REAL
                )
            """)
            conn.commit()

    def store_memory(
        self,
        content: str,
        scope: MemoryScope = MemoryScope.SHORT_TERM,
        owner: str = "Tarik",
        source: str = "user_input",
        correlation_id: str = "",
        task_id: Optional[str] = None,
        sensitivity: SensitivityLevel = SensitivityLevel.INTERNAL,
        metadata: Optional[dict] = None,
    ) -> MemoryRecord:
        mem_id = f"mem_{uuid.uuid4().hex[:12]}"
        rec = MemoryRecord(
            id=mem_id,
            scope=scope,
            content=content,
            owner=owner,
            source=source,
            correlation_id=correlation_id,
            task_id=task_id,
            sensitivity=sensitivity,
            metadata=metadata or {},
        )
        with self._lock:
            self._records[mem_id] = rec
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO memory_items
                    (id, scope, content, owner, source, correlation_id, sensitivity, task_id, retrieval_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rec.id, rec.scope.value, rec.content, rec.owner, rec.source,
                    rec.correlation_id, rec.sensitivity.value, rec.task_id, rec.retrieval_count, rec.created_at
                ))
                conn.commit()
        return rec

    def search_memory(self, query: str, scope: Optional[MemoryScope] = None, limit: int = 10) -> List[MemoryRecord]:
        q_lower = query.lower()
        results: List[MemoryRecord] = []
        with self._lock:
            for rec in self._records.values():
                if scope and rec.scope != scope:
                    continue
                if q_lower in rec.content.lower():
                    # Increment audit retrieval counter
                    rec.retrieval_count += 1
                    results.append(rec)
                    if len(results) >= limit:
                        break
        return results

    def get_recent(self, limit: int = 20) -> List[MemoryRecord]:
        with self._lock:
            return sorted(self._records.values(), key=lambda r: r.created_at, reverse=True)[:limit]
