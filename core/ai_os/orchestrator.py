"""core/ai_os/orchestrator.py — Durable Task & Workflow Orchestration Engine."""
from __future__ import annotations

import asyncio
import logging
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .schemas import TaskRecord, TaskStatus, WorkerStatus
from .events import EventEnvelope, EventType
from .registry import ControlPlaneRegistry

logger = logging.getLogger("dazy.ai_os.orchestrator")


class DurableTaskEngine:
    """Manages persistent, idempotent task execution with correlation tracking."""

    _instance: Optional[DurableTaskEngine] = None
    _lock = threading.RLock()

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path(__file__).resolve().parent.parent.parent / "memory" / "ai_os_tasks.db"
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

        self._active_tasks: Dict[str, TaskRecord] = {}
        self._idempotency_map: Dict[str, str] = {}  # idempotency_key -> task_id
        self._event_listeners: List[Callable[[EventEnvelope], None]] = []
        self._registry = ControlPlaneRegistry.get_instance()
        self._load_from_db()

    @classmethod
    def get_instance(cls) -> DurableTaskEngine:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    correlation_id TEXT,
                    idempotency_key TEXT,
                    title TEXT,
                    status TEXT,
                    assigned_worker_id TEXT,
                    priority INTEGER,
                    attempts INTEGER,
                    max_retries INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    error TEXT
                )
            """)
            try:
                conn.execute("ALTER TABLE tasks ADD COLUMN idempotency_key TEXT")
            except Exception:
                pass
            conn.commit()

    def _load_from_db(self) -> None:
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("SELECT * FROM tasks ORDER BY created_at ASC").fetchall()
                for r in rows:
                    t = TaskRecord(
                        id=r["id"],
                        correlation_id=r["correlation_id"],
                        title=r["title"],
                        status=TaskStatus(r["status"]) if r["status"] in TaskStatus._value2member_map_ else TaskStatus.QUEUED,
                        assigned_worker_id=r["assigned_worker_id"],
                        priority=r["priority"],
                        attempts=r["attempts"],
                        max_retries=r["max_retries"],
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                        error=r["error"],
                    )
                    self._active_tasks[t.id] = t
                    if "idempotency_key" in r.keys() and r["idempotency_key"]:
                        self._idempotency_map[r["idempotency_key"]] = t.id
        except Exception as e:
            logger.debug("Failed to load tasks from db: %s", e)

    def add_event_listener(self, listener: Callable[[EventEnvelope], None]) -> None:
        self._event_listeners.append(listener)

    def _emit(self, event_type: EventType, correlation_id: str, payload: Dict[str, Any]) -> None:
        envelope = EventEnvelope.create(
            event_type=event_type,
            correlation_id=correlation_id,
            source_component="core.ai_os.orchestrator",
            payload=payload,
        )
        for listener in self._event_listeners:
            try:
                listener(envelope)
            except Exception as e:
                logger.warning("Event listener failed: %s", e)

    def submit_task(
        self,
        title: str,
        input_payload: Dict[str, Any],
        worker_id: str = "wrk_orchestrator",
        correlation_id: Optional[str] = None,
        priority: int = 1,
        idempotency_key: Optional[str] = None,
    ) -> TaskRecord:
        """Submits a new durable task into the queue with idempotency protection."""
        with self._lock:
            # Idempotency check
            if idempotency_key and idempotency_key in self._idempotency_map:
                existing_id = self._idempotency_map[idempotency_key]
                if existing_id in self._active_tasks:
                    logger.info("Idempotent task match for key %s -> %s", idempotency_key, existing_id)
                    return self._active_tasks[existing_id]

            task_id = f"task_{uuid.uuid4().hex[:12]}"
            corr_id = correlation_id or f"corr_{uuid.uuid4().hex[:12]}"

            record = TaskRecord(
                id=task_id,
                correlation_id=corr_id,
                title=title,
                status=TaskStatus.QUEUED,
                assigned_worker_id=worker_id,
                priority=priority,
                input_payload=input_payload,
            )

            self._active_tasks[task_id] = record
            if idempotency_key:
                self._idempotency_map[idempotency_key] = task_id
            self._persist_task(record, idempotency_key)

        self._emit(EventType.TASK_CREATED, corr_id, {"task_id": task_id, "title": title, "worker": worker_id})
        return record

    def _persist_task(self, t: TaskRecord, idempotency_key: Optional[str] = None) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tasks
                (id, correlation_id, idempotency_key, title, status, assigned_worker_id, priority, attempts, max_retries, created_at, updated_at, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t.id, t.correlation_id, idempotency_key, t.title, t.status.value, t.assigned_worker_id,
                t.priority, t.attempts, t.max_retries, t.created_at, t.updated_at, t.error
            ))
            conn.commit()

    def cancel_task(self, task_id: str, reason: str = "Cancelled by operator") -> Optional[TaskRecord]:
        """Safely cancels an active or queued task."""
        return self.update_task_status(task_id, TaskStatus.FAILED, error=reason)

    def retry_task(self, task_id: str) -> Optional[TaskRecord]:
        """Retries a failed task if attempts <= max_retries."""
        with self._lock:
            if task_id not in self._active_tasks:
                return None
            t = self._active_tasks[task_id]
            if t.attempts >= t.max_retries:
                logger.warning("Task %s reached max retries (%d)", task_id, t.max_retries)
                return t
            updated = t.model_copy(update={
                "attempts": t.attempts + 1,
                "status": TaskStatus.QUEUED,
                "error": None,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
            self._active_tasks[task_id] = updated
            self._persist_task(updated)
        self._emit(EventType.TASK_STARTED, updated.correlation_id, {"task_id": task_id, "retry_attempt": updated.attempts})
        return updated

    def check_worker_timeouts(self, timeout_seconds: float = 60.0) -> List[str]:
        """Flags workers that haven't sent a heartbeat within the timeout period."""
        timed_out = []
        now = time.time()
        for w in self._registry.get_workers():
            if w.status == WorkerStatus.RUNNING and (now - w.heartbeat_ts) > timeout_seconds:
                self._registry.update_worker_status(w.id, WorkerStatus.DEGRADED, error="Heartbeat timeout exceeded")
                timed_out.append(w.id)
        return timed_out

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        output: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[TaskRecord]:
        with self._lock:
            if task_id not in self._active_tasks:
                return None
            t = self._active_tasks[task_id]
            updated = t.model_copy(update={
                "status": status,
                "output_result": output or t.output_result,
                "error": error or t.error,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
            self._active_tasks[task_id] = updated
            self._persist_task(updated)

            # Update assigned worker status
            if updated.assigned_worker_id:
                w_status = WorkerStatus.RUNNING if status == TaskStatus.RUNNING else (
                    WorkerStatus.FAILED if status == TaskStatus.FAILED else WorkerStatus.READY
                )
                self._registry.update_worker_status(updated.assigned_worker_id, w_status, error)

        # Emit events
        if status == TaskStatus.RUNNING:
            self._emit(EventType.TASK_STARTED, updated.correlation_id, {"task_id": task_id})
        elif status == TaskStatus.COMPLETED:
            self._emit(EventType.TASK_COMPLETED, updated.correlation_id, {"task_id": task_id, "output": output})
        elif status == TaskStatus.FAILED:
            self._emit(EventType.TASK_FAILED, updated.correlation_id, {"task_id": task_id, "error": error})

        return updated

    def get_tasks(self, limit: int = 50) -> List[TaskRecord]:
        with self._lock:
            return list(self._active_tasks.values())[:limit]
