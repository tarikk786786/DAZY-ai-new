"""core/ambient/governor.py — DAZY Resource Governor.

Adaptive system resource governor that inspects CPU, RAM, and battery state
to prevent runaway tasks, memory bloat, and battery drain.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

import psutil

logger = logging.getLogger("dazy.governor")


class ThrottleLevel(str, Enum):
    NORMAL = "normal"
    THROTTLED = "throttled"
    SUSPENDED = "suspended"


@dataclass
class GovernorStatus:
    throttle_level: ThrottleLevel
    cpu_percent: float
    ram_percent: float
    on_battery: bool
    battery_percent: Optional[float]
    active_tasks: int
    queue_bounded: bool
    storage_bytes_used: int
    storage_ceiling_bytes: int


class ResourceGovernor:
    """Monitors system load and enforces bounded execution and storage limits."""

    def __init__(
        self,
        max_active_tasks: int = 5,
        storage_ceiling_mb: int = 250,
        temp_dir: Optional[Path] = None,
        cpu_throttle_threshold: float = 75.0,
        cpu_suspend_threshold: float = 90.0,
        ram_throttle_threshold: float = 80.0,
        ram_suspend_threshold: float = 92.0,
        battery_throttle_threshold: float = 25.0,
        battery_suspend_threshold: float = 12.0,
    ):
        self.max_active_tasks = max_active_tasks
        self.storage_ceiling_bytes = storage_ceiling_mb * 1024 * 1024
        self.temp_dir = temp_dir or Path(os.environ.get("TEMP", "/tmp")) / "dazy_temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.cpu_throttle_threshold = cpu_throttle_threshold
        self.cpu_suspend_threshold = cpu_suspend_threshold
        self.ram_throttle_threshold = ram_throttle_threshold
        self.ram_suspend_threshold = ram_suspend_threshold
        self.battery_throttle_threshold = battery_throttle_threshold
        self.battery_suspend_threshold = battery_suspend_threshold

        self._current_level = ThrottleLevel.NORMAL
        self._on_throttle_change: list[Callable[[ThrottleLevel], None]] = []

    def register_throttle_callback(self, cb: Callable[[ThrottleLevel], None]) -> None:
        self._on_throttle_change.append(cb)

    def evaluate_system(self, current_active_tasks: int = 0) -> GovernorStatus:
        """Evaluate system load and determine appropriate throttle level."""
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent

        battery_info = psutil.sensors_battery()
        on_battery = False
        battery_percent = None

        if battery_info is not None:
            on_battery = not battery_info.power_plugged
            battery_percent = battery_info.percent

        # Determine level
        level = ThrottleLevel.NORMAL

        # Critical battery or extreme load -> SUSPEND
        if (on_battery and battery_percent is not None and battery_percent <= self.battery_suspend_threshold) or \
           cpu >= self.cpu_suspend_threshold or ram >= self.ram_suspend_threshold:
            level = ThrottleLevel.SUSPENDED
        # Low battery or elevated load -> THROTTLE
        elif (on_battery and battery_percent is not None and battery_percent <= self.battery_throttle_threshold) or \
             cpu >= self.cpu_throttle_threshold or ram >= self.ram_throttle_threshold:
            level = ThrottleLevel.THROTTLED

        if level != self._current_level:
            prev = self._current_level
            self._current_level = level
            logger.info("Governor throttle changed: %s -> %s", prev, level)
            for cb in self._on_throttle_change:
                try:
                    cb(level)
                except Exception as exc:
                    logger.warning("Governor callback failed: %s", exc)

        used_storage = self.get_temp_storage_size()
        if used_storage > self.storage_ceiling_bytes:
            self.enforce_storage_ceiling()

        return GovernorStatus(
            throttle_level=level,
            cpu_percent=cpu,
            ram_percent=ram,
            on_battery=on_battery,
            battery_percent=battery_percent,
            active_tasks=current_active_tasks,
            queue_bounded=current_active_tasks >= self.max_active_tasks,
            storage_bytes_used=used_storage,
            storage_ceiling_bytes=self.storage_ceiling_bytes,
        )

    def can_admit_task(self, current_active_tasks: int) -> bool:
        """Checks if a new background task can be admitted safely."""
        status = self.evaluate_system(current_active_tasks)
        if status.throttle_level == ThrottleLevel.SUSPENDED:
            return False
        if current_active_tasks >= self.max_active_tasks:
            return False
        return True

    def get_poll_interval(self, base_seconds: float = 3.0) -> float:
        """Returns adaptive polling interval based on throttle state."""
        if self._current_level == ThrottleLevel.NORMAL:
            return base_seconds
        elif self._current_level == ThrottleLevel.THROTTLED:
            return base_seconds * 4.0  # e.g. 12 seconds
        else:
            return base_seconds * 10.0  # e.g. 30 seconds

    def get_temp_storage_size(self) -> int:
        """Calculate total bytes in DAZY's temp directory."""
        if not self.temp_dir.exists():
            return 0
        total = 0
        for entry in self.temp_dir.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except OSError:
                    pass
        return total

    def enforce_storage_ceiling(self) -> int:
        """Prunes oldest files in temp_dir until usage is below 80% of ceiling."""
        if not self.temp_dir.exists():
            return 0
        files = []
        for entry in self.temp_dir.rglob("*"):
            if entry.is_file():
                try:
                    files.append((entry, entry.stat().st_mtime, entry.stat().st_size))
                except OSError:
                    pass
        # Oldest first
        files.sort(key=lambda x: x[1])
        target_size = int(self.storage_ceiling_bytes * 0.8)
        current_size = sum(f[2] for f in files)
        deleted_bytes = 0

        for path, _, size in files:
            if current_size <= target_size:
                break
            try:
                path.unlink(missing_ok=True)
                current_size -= size
                deleted_bytes += size
            except OSError:
                pass
        return deleted_bytes


# Global singleton instance
governor = ResourceGovernor()
