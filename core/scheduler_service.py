"""core/scheduler_service.py — Local Job & Routine Scheduler for DAZY using APScheduler.

Provides:
1. Local cron, interval, and one-shot scheduled automation jobs.
2. Background routine execution (e.g. daily briefings, memory compaction, health audits).
3. Thread-safe job registration, cancellation, and inspection.
4. Seamless integration with DAZY's asyncio event loop.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("dazy.scheduler")

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.warning("apscheduler not installed; SchedulerService will run in disabled mode.")


class SchedulerService:
    """Orchestrates background tasks, routines, and recurring triggers for DAZY."""

    def __init__(self, use_asyncio: bool = False):
        self._scheduler: Optional[Any] = None
        self._jobs: Dict[str, Any] = {}
        if APSCHEDULER_AVAILABLE:
            if use_asyncio:
                self._scheduler = AsyncIOScheduler()
            else:
                self._scheduler = BackgroundScheduler()
            logger.info("SchedulerService initialized with APScheduler.")

    def start(self) -> None:
        """Starts the scheduler background loop."""
        if self._scheduler and not self._scheduler.running:
            try:
                self._scheduler.start()
                logger.info("SchedulerService started.")
            except Exception as e:
                logger.error("Failed to start SchedulerService: %s", e)

    def shutdown(self) -> None:
        """Gracefully shuts down the scheduler."""
        if self._scheduler and self._scheduler.running:
            try:
                self._scheduler.shutdown(wait=False)
                logger.info("SchedulerService shut down.")
            except Exception as e:
                logger.error("Error shutting down SchedulerService: %s", e)

    def add_interval_job(
        self,
        job_id: str,
        func: Callable[..., Any],
        seconds: int = 60,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Schedules a recurring function to run every `seconds`."""
        if not self._scheduler:
            return False
        try:
            self.remove_job(job_id)
            job = self._scheduler.add_job(
                func,
                IntervalTrigger(seconds=seconds),
                id=job_id,
                args=args or [],
                kwargs=kwargs or {},
                replace_existing=True,
            )
            self._jobs[job_id] = job
            logger.info("Added interval job '%s' (every %ds)", job_id, seconds)
            return True
        except Exception as e:
            logger.error("Failed to add interval job '%s': %s", job_id, e)
            return False

    def add_cron_job(
        self,
        job_id: str,
        func: Callable[..., Any],
        hour: int,
        minute: int = 0,
        args: Optional[List[Any]] = None,
    ) -> bool:
        """Schedules a daily job at a specific hour and minute."""
        if not self._scheduler:
            return False
        try:
            self.remove_job(job_id)
            job = self._scheduler.add_job(
                func,
                CronTrigger(hour=hour, minute=minute),
                id=job_id,
                args=args or [],
                replace_existing=True,
            )
            self._jobs[job_id] = job
            logger.info("Added cron job '%s' (daily at %02d:%02d)", job_id, hour, minute)
            return True
        except Exception as e:
            logger.error("Failed to add cron job '%s': %s", job_id, e)
            return False

    def remove_job(self, job_id: str) -> bool:
        """Cancels an existing scheduled job."""
        if not self._scheduler:
            return False
        try:
            if job_id in self._jobs or self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)
                self._jobs.pop(job_id, None)
                logger.info("Removed job '%s'", job_id)
                return True
        except Exception as e:
            logger.debug("Job removal '%s' note: %s", job_id, e)
        return False

    def list_jobs(self) -> List[Dict[str, Any]]:
        """Lists active scheduled jobs."""
        if not self._scheduler:
            return []
        out = []
        for j in self._scheduler.get_jobs():
            nrt = getattr(j, "next_run_time", None)
            out.append({
                "id": j.id,
                "name": j.name,
                "next_run_time": str(nrt) if nrt else None,
            })
        return out
