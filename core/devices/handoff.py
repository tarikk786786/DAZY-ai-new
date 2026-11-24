"""core/devices/handoff.py — Cross-Device Context & Task Handoff Engine.

Enables seamless transition of active tasks and conversation state between
Windows desktop and Android mobile companion with permission verification.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

from core.devices.models import TrustLevel
from core.devices.pairing import PairingManager, pairing_manager
from memory.dazy_memory import DazyMemoryEngine, dazy_memory

logger = logging.getLogger("dazy.handoff")


@dataclass
class HandoffPackage:
    package_id: str
    source_device_id: str
    target_device_id: str
    task_id: Optional[str]
    conversation_summary: str
    active_scratchpad: dict[str, Any]
    timestamp: float
    status: str = "pending"  # "pending", "accepted", "transferred", "rejected"


class TaskHandoffEngine:
    """Coordinates secure handoff of ongoing tasks and conversation context."""

    def __init__(self, pairing_mgr: Optional[PairingManager] = None, mem_engine: Optional[DazyMemoryEngine] = None):
        self.pairing = pairing_mgr or pairing_manager
        self.memory = mem_engine or dazy_memory
        self._active_packages: dict[str, HandoffPackage] = {}

    def prepare_handoff(
        self,
        source_device_id: str,
        target_device_id: str,
        task_id: Optional[str] = None,
    ) -> Optional[HandoffPackage]:
        """Prepares a state snapshot to transfer to a target device."""
        enrolled = {d.device_id: d for d in self.pairing.get_enrolled_devices()}
        target = enrolled.get(target_device_id)

        if not target or target.trust_level != TrustLevel.PAIRED_TRUSTED:
            logger.warning("Handoff denied: Target device %s is not paired/trusted", target_device_id)
            return None

        if not target.permissions.allow_task_handoff:
            logger.warning("Handoff denied: Target device %s lacks allow_task_handoff permission", target_device_id)
            return None

        # Build snapshot from Working Memory
        wm = self.memory.working
        summary = f"Active window: {wm.active_process_name} - {wm.active_window_title}. " \
                  f"Latest request: {wm.latest_user_request}"

        pkg_id = f"handoff_{int(time.time()*1000)}"
        pkg = HandoffPackage(
            package_id=pkg_id,
            source_device_id=source_device_id,
            target_device_id=target_device_id,
            task_id=task_id or wm.active_task_id,
            conversation_summary=summary,
            active_scratchpad=dict(wm.scratchpad),
            timestamp=time.time(),
            status="pending",
        )
        self._active_packages[pkg_id] = pkg
        logger.info("Prepared handoff %s from %s to %s", pkg_id, source_device_id, target_device_id)
        return pkg

    def accept_handoff(self, package_id: str) -> bool:
        """Applies incoming handoff package into local working memory."""
        pkg = self._active_packages.get(package_id)
        if not pkg:
            return False

        pkg.status = "transferred"
        self.memory.working.active_task_id = pkg.task_id
        self.memory.working.scratchpad.update(pkg.active_scratchpad)
        logger.info("Applied handoff package %s to local working memory", package_id)
        return True


task_handoff = TaskHandoffEngine()
