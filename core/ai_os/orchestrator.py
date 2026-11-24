"""core/ai_os/orchestrator.py — Durable Task & Workflow Orchestration Engine."""
from __future__ import annotations

import asyncio
import json
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
                    dependencies TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    error TEXT
                )
            """)
            try:
                conn.execute("ALTER TABLE tasks ADD COLUMN idempotency_key TEXT")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE tasks ADD COLUMN dependencies TEXT")
            except Exception:
                pass
            conn.commit()

    def _load_from_db(self) -> None:
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("SELECT * FROM tasks ORDER BY created_at ASC").fetchall()
                for r in rows:
                    raw_deps = r["dependencies"] if "dependencies" in r.keys() else "[]"
                    deps = []
                    if raw_deps:
                        try:
                            deps = json.loads(raw_deps) if isinstance(raw_deps, str) else list(raw_deps)
                        except Exception:
                            deps = []
                    t = TaskRecord(
                        id=r["id"],
                        correlation_id=r["correlation_id"],
                        title=r["title"],
                        status=TaskStatus(r["status"]) if r["status"] in TaskStatus._value2member_map_ else TaskStatus.QUEUED,
                        assigned_worker_id=r["assigned_worker_id"],
                        priority=r["priority"],
                        attempts=r["attempts"],
                        max_retries=r["max_retries"],
                        dependencies=deps,
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
        deps_json = json.dumps(t.dependencies) if t.dependencies else "[]"
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tasks
                (id, correlation_id, idempotency_key, title, status, assigned_worker_id, priority, attempts, max_retries, dependencies, created_at, updated_at, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t.id, t.correlation_id, idempotency_key, t.title, t.status.value, t.assigned_worker_id,
                t.priority, t.attempts, t.max_retries, deps_json, t.created_at, t.updated_at, t.error
            ))
            conn.commit()

    def submit_dag(
        self,
        tasks_plan: List[Dict[str, Any]],
        correlation_id: Optional[str] = None,
    ) -> List[TaskRecord]:
        """Submits a Directed Acyclic Graph (DAG) of subtasks with cycle detection (GodMode-Team pattern).
        Each task dict:
          - key: unique identifier within the plan (e.g. 'plan_repo', 'run_tests')
          - title: human-readable task description
          - worker_id: optional assigned worker
          - dependencies: list of prerequisite keys
          - input_payload: dict of task inputs
        """
        corr_id = correlation_id or f"corr_dag_{uuid.uuid4().hex[:12]}"
        
        # 1. Validate Acyclicity using topological sort
        graph: Dict[str, List[str]] = {}
        in_degree: Dict[str, int] = {}
        key_to_item: Dict[str, Dict[str, Any]] = {}

        for item in tasks_plan:
            k = item.get("key") or item.get("title")
            key_to_item[k] = item
            graph[k] = []
            in_degree[k] = 0

        for item in tasks_plan:
            k = item.get("key") or item.get("title")
            for dep in item.get("dependencies", []):
                if dep not in in_degree:
                    raise ValueError(f"Unknown dependency '{dep}' for task '{k}'")
                graph[dep].append(k)
                in_degree[k] += 1

        queue = [k for k, d in in_degree.items() if d == 0]
        visited_count = 0
        while queue:
            node = queue.pop(0)
            visited_count += 1
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count != len(tasks_plan):
            raise ValueError("Circular dependency detected in DAG task plan")

        # 2. Materialize TaskRecords with real IDs
        key_to_id: Dict[str, str] = {}
        created_records: List[TaskRecord] = []

        with self._lock:
            for item in tasks_plan:
                k = item.get("key") or item.get("title")
                task_id = f"dag_task_{uuid.uuid4().hex[:12]}"
                key_to_id[k] = task_id

            for item in tasks_plan:
                k = item.get("key") or item.get("title")
                task_id = key_to_id[k]
                resolved_deps = [key_to_id[d] for d in item.get("dependencies", [])]
                
                # If dependencies exist, task starts WAITING; otherwise QUEUED
                initial_status = TaskStatus.WAITING if resolved_deps else TaskStatus.QUEUED

                record = TaskRecord(
                    id=task_id,
                    correlation_id=corr_id,
                    title=item.get("title", k),
                    status=initial_status,
                    assigned_worker_id=item.get("worker_id", "wrk_orchestrator"),
                    priority=item.get("priority", 1),
                    dependencies=resolved_deps,
                    input_payload=item.get("input_payload", {}),
                )
                self._active_tasks[task_id] = record
                self._persist_task(record)
                created_records.append(record)

        for rec in created_records:
            self._emit(
                EventType.TASK_CREATED,
                corr_id,
                {"task_id": rec.id, "title": rec.title, "status": rec.status.value, "deps": rec.dependencies}
            )

        return created_records

    def get_ready_tasks(self, correlation_id: Optional[str] = None) -> List[TaskRecord]:
        """Returns all tasks in QUEUED status whose prerequisite dependencies are all COMPLETED."""
        with self._lock:
            ready: List[TaskRecord] = []
            for t in self._active_tasks.values():
                if correlation_id and t.correlation_id != correlation_id:
                    continue
                if t.status in (TaskStatus.QUEUED, TaskStatus.WAITING):
                    deps_satisfied = True
                    for dep_id in t.dependencies:
                        dep_task = self._active_tasks.get(dep_id)
                        if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                            deps_satisfied = False
                            break
                    if deps_satisfied:
                        ready.append(t)
            return ready

    def advance_dag(self, task_id: str, output: Optional[Dict[str, Any]] = None) -> List[TaskRecord]:
        """Completes a task and advances the DAG by unblocking dependent tasks."""
        with self._lock:
            updated = self.update_task_status(task_id, TaskStatus.COMPLETED, output=output)
            if not updated:
                return []

            corr_id = updated.correlation_id
            newly_ready: List[TaskRecord] = []

            for t in self._active_tasks.values():
                if t.correlation_id == corr_id and t.status == TaskStatus.WAITING and task_id in t.dependencies:
                    # Check if all deps for t are now complete
                    all_done = all(
                        self._active_tasks.get(d) and self._active_tasks[d].status == TaskStatus.COMPLETED
                        for d in t.dependencies
                    )
                    if all_done:
                        t_ready = t.model_copy(update={
                            "status": TaskStatus.QUEUED,
                            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        })
                        self._active_tasks[t.id] = t_ready
                        self._persist_task(t_ready)
                        newly_ready.append(t_ready)
                        self._emit(EventType.TASK_STARTED, corr_id, {"task_id": t.id, "title": t.title, "unblocked_by": task_id})

            return newly_ready

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
