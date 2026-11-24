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
        self._event_listeners: List[Callable[[EventEnvelope], None]] = []
        self._registry = ControlPlaneRegistry.get_instance()

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
            conn.commit()

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
    ) -> TaskRecord:
        """Submits a new durable task into the queue."""
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

        with self._lock:
            self._active_tasks[task_id] = record
            self._persist_task(record)

        self._emit(EventType.TASK_CREATED, corr_id, {"task_id": task_id, "title": title, "worker": worker_id})
        return record

    def _persist_task(self, t: TaskRecord) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tasks
                (id, correlation_id, title, status, assigned_worker_id, priority, attempts, max_retries, created_at, updated_at, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t.id, t.correlation_id, t.title, t.status.value, t.assigned_worker_id,
                t.priority, t.attempts, t.max_retries, t.created_at, t.updated_at, t.error
            ))
            conn.commit()

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
