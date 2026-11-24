"""core/ambient/proactive_alerts.py — DAZY Proactive Alert Engine.

Produces context-aware, non-intrusive alerts in DAZY's warm Indian companion tone.
Includes deduplication cooldowns so alerts remain helpful and gentle.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from core.ambient.governor import GovernorStatus, ThrottleLevel
from core.ambient.screen_observer import WindowContext
from core.ambient.task_observer import TaskEvent

logger = logging.getLogger("dazy.alerts")


class AlertPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ProactiveAlert:
    id: str
    title: str
    message: str
    priority: AlertPriority
    timestamp: float
    category: str
    suggested_action: Optional[str] = None


class ProactiveAlertEngine:
    """Evaluates background signals and generates respectful, proactive suggestions."""

    def __init__(self, cooldown_seconds: float = 60.0):
        self.cooldown_seconds = cooldown_seconds
        self._last_alert_times: dict[str, float] = {}
        self._alert_listeners: list[Callable[[ProactiveAlert], None]] = []

    def add_alert_listener(self, cb: Callable[[ProactiveAlert], None]) -> None:
        self._alert_listeners.append(cb)

    def _can_fire(self, alert_key: str) -> bool:
        now = time.time()
        last = self._last_alert_times.get(alert_key, 0.0)
        if now - last < self.cooldown_seconds:
            return False
        self._last_alert_times[alert_key] = now
        return True

    def on_task_event(self, ev: TaskEvent) -> Optional[ProactiveAlert]:
        """Generates friendly alert when background work status changes."""
        key = f"task_{ev.task_id}_{ev.status}"
        if not self._can_fire(key):
            return None

        alert = None
        if ev.status == "done":
            alert = ProactiveAlert(
                id=f"alert_{int(time.time()*1000)}",
                title="Kaam Ho Gaya! ✓",
                message=f"Tarik, aapka background agent task ({ev.goal or ev.agent_name}) successfully complete ho gaya hai.",
                priority=AlertPriority.NORMAL,
                timestamp=time.time(),
                category="task_completion",
                suggested_action="check_result",
            )
        elif ev.status == "failed":
            alert = ProactiveAlert(
                id=f"alert_{int(time.time()*1000)}",
                title="Task Alert ⚠️",
                message=f"Aapke task '{ev.goal or ev.agent_name}' mein ek error aayi hai: {ev.error or 'Unexpected issue'}.",
                priority=AlertPriority.HIGH,
                timestamp=time.time(),
                category="task_error",
                suggested_action="retry_or_inspect",
            )

        if alert:
            self._dispatch(alert)
        return alert

    def on_governor_status(self, status: GovernorStatus) -> Optional[ProactiveAlert]:
        """Alerts gently when battery is getting low or resources need throttling."""
        if status.throttle_level == ThrottleLevel.SUSPENDED and status.on_battery:
            key = "battery_critical"
            if self._can_fire(key):
                alert = ProactiveAlert(
                    id=f"alert_{int(time.time()*1000)}",
                    title="Battery Warning ⚡",
                    message=f"Tarik, battery {int(status.battery_percent or 0)}% bachi hai. Maine heavy background processing temporarily pause kar di hai.",
                    priority=AlertPriority.CRITICAL,
                    timestamp=time.time(),
                    category="system_health",
                    suggested_action="plug_charger",
                )
                self._dispatch(alert)
                return alert
        elif status.throttle_level == ThrottleLevel.THROTTLED:
            key = "system_throttled"
            if self._can_fire(key):
                alert = ProactiveAlert(
                    id=f"alert_{int(time.time()*1000)}",
                    title="Resource Optimization 🌿",
                    message="System load thoda high tha, isliye maine ambient scan speed slow kar di hai taaki laptop smooth rahe.",
                    priority=AlertPriority.LOW,
                    timestamp=time.time(),
                    category="system_health",
                )
                self._dispatch(alert)
                return alert
        return None

    def on_window_context(self, ctx: WindowContext) -> Optional[ProactiveAlert]:
        """Provides smart contextual advice for known workflow apps."""
        # E.g. If user opens VS Code on DAZY repo or Activepieces
        key = f"window_{ctx.process_name}"
        if not self._can_fire(key):
            return None

        alert = None
        lower_title = ctx.window_title.lower()
        if "activepieces" in lower_title:
            alert = ProactiveAlert(
                id=f"alert_{int(time.time()*1000)}",
                title="Activepieces Detected ⚡",
                message="Aap Activepieces par kaam kar rahe hain. Kya mujhe is workflow ko test karne ya MCP sync check karne ki zaroorat hai?",
                priority=AlertPriority.LOW,
                timestamp=time.time(),
                category="workflow_suggestion",
                suggested_action="check_mcp_workflows",
            )
        elif "gmail" in lower_title or "mail" in lower_title:
            alert = ProactiveAlert(
                id=f"alert_{int(time.time()*1000)}",
                title="Email Briefing Ready ✉️",
                message="Tarik, agar aap chahein toh main aapki priority unread emails summarise kar sakti hoon.",
                priority=AlertPriority.LOW,
                timestamp=time.time(),
                category="workflow_suggestion",
                suggested_action="summarize_inbox",
            )

        if alert:
            self._dispatch(alert)
        return alert

    def _dispatch(self, alert: ProactiveAlert) -> None:
        for cb in self._alert_listeners:
            try:
                cb(alert)
            except Exception as e:
                logger.warning("Alert listener error: %s", e)


alert_engine = ProactiveAlertEngine()
