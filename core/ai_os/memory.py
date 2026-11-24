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
    project_id: Optional[str] = None
    source: str = "conversation"
    correlation_id: str = ""
    sensitivity: SensitivityLevel = SensitivityLevel.INTERNAL
    task_id: Optional[str] = None
    confidence_score: float = 1.0
    creator_id: str = "wrk_memory_curator"
    retrieval_count: int = 0
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
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
        self._load_from_db()

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
                    project_id TEXT,
                    source TEXT,
                    correlation_id TEXT,
                    sensitivity TEXT,
                    task_id TEXT,
                    confidence_score REAL,
                    creator_id TEXT,
                    retrieval_count INTEGER,
                    created_at REAL,
                    updated_at REAL
                )
            """)
            conn.commit()

    def _load_from_db(self) -> None:
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("SELECT * FROM memory_items ORDER BY created_at ASC").fetchall()
                for r in rows:
                    rec = MemoryRecord(
                        id=r["id"],
                        scope=MemoryScope(r["scope"]) if r["scope"] in MemoryScope._value2member_map_ else MemoryScope.SHORT_TERM,
                        content=r["content"],
                        owner=r["owner"],
                        project_id=r["project_id"] if "project_id" in r.keys() else None,
                        source=r["source"],
                        correlation_id=r["correlation_id"],
                        sensitivity=SensitivityLevel(r["sensitivity"]) if r["sensitivity"] in SensitivityLevel._value2member_map_ else SensitivityLevel.INTERNAL,
                        task_id=r["task_id"],
                        confidence_score=r["confidence_score"] if "confidence_score" in r.keys() else 1.0,
                        creator_id=r["creator_id"] if "creator_id" in r.keys() else "wrk_memory_curator",
                        retrieval_count=r["retrieval_count"],
                        created_at=r["created_at"],
                        updated_at=r["updated_at"] if "updated_at" in r.keys() else r["created_at"],
                    )
                    self._records[rec.id] = rec
        except Exception as e:
            logger.debug("Failed to load memory from db: %s", e)

    def store_memory(
        self,
        content: str,
        scope: MemoryScope = MemoryScope.SHORT_TERM,
        owner: str = "Tarik",
        project_id: Optional[str] = None,
        source: str = "user_input",
        correlation_id: str = "",
        task_id: Optional[str] = None,
        confidence_score: float = 1.0,
        creator_id: str = "wrk_memory_curator",
        sensitivity: SensitivityLevel = SensitivityLevel.INTERNAL,
        metadata: Optional[dict] = None,
    ) -> MemoryRecord:
        mem_id = f"mem_{uuid.uuid4().hex[:12]}"
        now = time.time()
        rec = MemoryRecord(
            id=mem_id,
            scope=scope,
            content=content,
            owner=owner,
            project_id=project_id,
            source=source,
            correlation_id=correlation_id,
            task_id=task_id,
            confidence_score=confidence_score,
            creator_id=creator_id,
            sensitivity=sensitivity,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        with self._lock:
            self._records[mem_id] = rec
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO memory_items
                    (id, scope, content, owner, project_id, source, correlation_id, sensitivity, task_id, confidence_score, creator_id, retrieval_count, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rec.id, rec.scope.value, rec.content, rec.owner, rec.project_id, rec.source,
                    rec.correlation_id, rec.sensitivity.value, rec.task_id, rec.confidence_score,
                    rec.creator_id, rec.retrieval_count, rec.created_at, rec.updated_at
                ))
                conn.commit()
        return rec

    def update_memory(self, memory_id: str, new_content: str, metadata: Optional[dict] = None) -> Optional[MemoryRecord]:
        with self._lock:
            if memory_id not in self._records:
                return None
            rec = self._records[memory_id]
            updated = rec.model_copy(update={
                "content": new_content,
                "updated_at": time.time(),
                "metadata": metadata or rec.metadata,
            })
            self._records[memory_id] = updated
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("""
                    UPDATE memory_items SET content = ?, updated_at = ? WHERE id = ?
                """, (updated.content, updated.updated_at, memory_id))
                conn.commit()
            return updated

    def delete_memory(self, memory_id: str) -> bool:
        with self._lock:
            if memory_id in self._records:
                del self._records[memory_id]
                with sqlite3.connect(self._db_path) as conn:
                    conn.execute("DELETE FROM memory_items WHERE id = ?", (memory_id,))
                    conn.commit()
                return True
            return False

    def expire_memories(self, max_age_seconds: float = 86400 * 7, scope: Optional[MemoryScope] = None) -> int:
        """Purges transient memories older than max_age_seconds (e.g. WORKING or SHORT_TERM)."""
        expired_ids = []
        cutoff = time.time() - max_age_seconds
        with self._lock:
            for mid, rec in list(self._records.items()):
                if scope and rec.scope != scope:
                    continue
                if rec.scope in (MemoryScope.WORKING, MemoryScope.SHORT_TERM) and rec.created_at < cutoff:
                    expired_ids.append(mid)
            for mid in expired_ids:
                self.delete_memory(mid)
        return len(expired_ids)

    def search_memory(
        self,
        query: str,
        scope: Optional[MemoryScope] = None,
        owner: str = "Tarik",
        project_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryRecord]:
        """Scoped, isolated memory retrieval preventing cross-project or cross-user leakage."""
        q_lower = query.lower()
        results: List[MemoryRecord] = []
        with self._lock:
            for rec in self._records.values():
                # Strict owner isolation
                if rec.owner != owner:
                    continue
                # Strict project isolation when project_id is specified
                if project_id and rec.project_id != project_id:
                    continue
                if scope and rec.scope != scope:
                    continue
                if q_lower in rec.content.lower():
                    rec.retrieval_count += 1
                    results.append(rec)
                    if len(results) >= limit:
                        break
        return results

    def build_reasoning_context(self, query: str, owner: str = "Tarik", project_id: Optional[str] = None) -> str:
        """Synthesizes isolated long-term, semantic, and procedural memories into prompt reasoning context."""
        matches = self.search_memory(query, owner=owner, project_id=project_id, limit=6)
        if not matches:
            return ""
        lines = [f"[{m.scope.value}] {m.content}" for m in matches]
        return "\n[RETRIEVED RELEVANT MEMORY CONTEXT]\n" + "\n".join(lines) + "\n"

    def get_recent(self, limit: int = 20) -> List[MemoryRecord]:
        with self._lock:
            return sorted(self._records.values(), key=lambda r: r.created_at, reverse=True)[:limit]
