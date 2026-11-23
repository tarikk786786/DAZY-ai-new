"""core/ambient/task_observer.py — DAZY Background Task & Agent Monitor.

Watches task state transitions (running, progress, completed, failed)
without polling spam or heavy overhead.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from core.ambient.governor import ResourceGovernor, governor
from core.tasks.store import TaskStore

logger = logging.getLogger("dazy.task_observer")


@dataclass
class TaskEvent:
    task_id: str
    agent_name: str
    status: str
    goal: str
    result_summary: str
    timestamp: float
    error: Optional[str] = None


class TaskObserver:
    """Monitors running agents and background tasks from core.tasks."""

    def __init__(self, task_store_root: Optional[Path] = None, resource_governor: Optional[ResourceGovernor] = None):
        root = task_store_root or (Path(__file__).resolve().parent.parent.parent / "tasks")
        self.store = TaskStore(root)
        self.governor = resource_governor or governor
        self._last_statuses: dict[str, str] = {}
        self._listeners: list[Callable[[TaskEvent], None]] = []
        self._running = False

    def add_listener(self, listener: Callable[[TaskEvent], None]) -> None:
        self._listeners.append(listener)

    def scan_tasks(self) -> list[TaskEvent]:
        """Scans store for task status changes and emits events."""
        events: list[TaskEvent] = []
        try:
            tasks = self.store.all()
        except Exception as e:
            logger.debug("Failed to read task store: %s", e)
            return events

        current_active = 0
        for t in tasks:
            tid = t.get("id")
            if not tid:
                continue

            status = t.get("status", "unknown")
            if status in ("queued", "running", "scheduled", "waiting_quota"):
                current_active += 1

            prev_status = self._last_statuses.get(tid)
            if prev_status != status:
                self._last_statuses[tid] = status
                # Create event
                agent = t.get("agent", "dazy_agent")
                goal = t.get("goal", "")
                result = t.get("result", "")
                error = t.get("error")

                event = TaskEvent(
                    task_id=tid,
                    agent_name=agent,
                    status=status,
                    goal=goal,
                    result_summary=result[:200] if result else "",
                    timestamp=time.time(),
                    error=error,
                )
                events.append(event)
                self._notify(event)

        # Notify governor of current active task count
        self.governor.evaluate_system(current_active_tasks=current_active)
        return events

    def _notify(self, ev: TaskEvent) -> None:
        for cb in self._listeners:
            try:
                cb(ev)
            except Exception as e:
                logger.warning("TaskObserver callback error: %s", e)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True

        while self._running:
            interval = self.governor.get_poll_interval(base_seconds=4.0)
            try:
                self.scan_tasks()
            except Exception as e:
                logger.debug("Error in scan_tasks: %s", e)
            await asyncio.sleep(interval)

    def stop(self) -> None:
        self._running = False


task_observer = TaskObserver()
