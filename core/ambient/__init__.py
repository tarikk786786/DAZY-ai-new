"""core/ambient — DAZY Low-Resource Ambient Intelligence Subsystem.

Coordinates screen observer, task monitor, resource governor, and proactive alerts.
"""
from core.ambient.governor import GovernorStatus, ResourceGovernor, ThrottleLevel, governor
from core.ambient.proactive_alerts import AlertPriority, ProactiveAlert, ProactiveAlertEngine, alert_engine
from core.ambient.screen_observer import ScreenObserver, WindowContext, screen_observer
from core.ambient.task_observer import TaskEvent, TaskObserver, task_observer

__all__ = [
    "ThrottleLevel",
    "GovernorStatus",
    "ResourceGovernor",
    "governor",
    "WindowContext",
    "ScreenObserver",
    "screen_observer",
    "TaskEvent",
    "TaskObserver",
    "task_observer",
    "AlertPriority",
    "ProactiveAlert",
    "ProactiveAlertEngine",
    "alert_engine",
]
