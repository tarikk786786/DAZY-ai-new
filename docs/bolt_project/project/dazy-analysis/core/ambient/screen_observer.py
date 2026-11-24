"""core/ambient/screen_observer.py — Event-Driven Screen & App Observer.

Provides lightweight active window awareness using native Windows APIs (ctypes user32)
without continuous video recording, heavy background OCR loops, or excessive memory use.
"""
from __future__ import annotations

import asyncio
import ctypes
import logging
import platform
import time
from dataclasses import dataclass
from typing import Callable, Optional

import psutil

from core.ambient.governor import ResourceGovernor, ThrottleLevel, governor

logger = logging.getLogger("dazy.screen_observer")

_IS_WINDOWS = platform.system() == "Windows"


@dataclass
class WindowContext:
    process_name: str
    window_title: str
    pid: int
    timestamp: float
    summary: str


class ScreenObserver:
    """Monitors active application changes with zero continuous screenshot recording."""

    def __init__(self, resource_governor: Optional[ResourceGovernor] = None):
        self.governor = resource_governor or governor
        self._last_context: Optional[WindowContext] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._listeners: list[Callable[[WindowContext], None]] = []

    def add_listener(self, listener: Callable[[WindowContext], None]) -> None:
        self._listeners.append(listener)

    def get_current_foreground_window(self) -> Optional[WindowContext]:
        """Reads active window information using Win32 API without taking screenshots."""
        if not _IS_WINDOWS:
            return None

        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return None

            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.strip()

            pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            proc_id = pid.value

            proc_name = "unknown"
            if proc_id:
                try:
                    proc = psutil.Process(proc_id)
                    proc_name = proc.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    proc_name = f"pid_{proc_id}"

            # Create summary
            summary = f"{proc_name}: {title}" if title else proc_name
            return WindowContext(
                process_name=proc_name,
                window_title=title,
                pid=proc_id,
                timestamp=time.time(),
                summary=summary,
            )
        except Exception as exc:
            logger.debug("Failed to read foreground window: %s", exc)
            return None

    def poll_change(self) -> Optional[WindowContext]:
        """Checks for active window change, de-duplicating consecutive identical contexts."""
        curr = self.get_current_foreground_window()
        if not curr:
            return None

        if self._last_context is None:
            self._last_context = curr
            self._notify(curr)
            return curr

        # Only notify if process or title changed significantly
        if curr.process_name != self._last_context.process_name or curr.window_title != self._last_context.window_title:
            self._last_context = curr
            self._notify(curr)
            return curr

        return None

    def _notify(self, ctx: WindowContext) -> None:
        for cb in self._listeners:
            try:
                cb(ctx)
            except Exception as e:
                logger.warning("ScreenObserver listener error: %s", e)

    async def start(self) -> None:
        """Starts background loop with adaptive interval governed by ResourceGovernor."""
        if self._running:
            return
        self._running = True

        while self._running:
            # Check governor throttle
            status = self.governor.evaluate_system()
            if status.throttle_level == ThrottleLevel.SUSPENDED:
                # Suspended due to battery or extreme load: sleep 30s
                await asyncio.sleep(30.0)
                continue

            interval = self.governor.get_poll_interval(base_seconds=2.5)
            try:
                self.poll_change()
            except Exception as e:
                logger.debug("Error in poll_change: %s", e)

            await asyncio.sleep(interval)

    def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()


screen_observer = ScreenObserver()
