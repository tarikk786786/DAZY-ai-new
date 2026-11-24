"""core/devices/nearby_discovery.py — DAZY Nearby Device Discovery Engine.

Discovers nearby DAZY-enabled companions (e.g. Android phone) over local network
or Bluetooth without continuous invasive scanning or false distance claims.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from core.devices.models import DeviceType, TrustLevel
from core.devices.pairing import PairingManager, pairing_manager

logger = logging.getLogger("dazy.nearby")


class ProximityCategory(str, Enum):
    IMMEDIATE_LOCAL = "immediate_local"   # Same local network / BLE beacon
    REACHABLE_NETWORK = "reachable_network" # Same subnet or active socket
    CLOUD_CONNECTED = "cloud_connected"   # Reachable via Supabase / Coolify
    UNKNOWN = "unknown"


@dataclass
class DiscoveredNearbyDevice:
    device_id: str
    friendly_name: str
    device_type: DeviceType
    proximity: ProximityCategory
    is_already_paired: bool
    requires_pairing: bool
    connection_method: str  # "mDNS", "LAN", "BLE"
    discovered_at: float


class NearbyDiscoveryEngine:
    """Manages secure, privacy-respecting nearby device discovery."""

    def __init__(self, pairing_mgr: Optional[PairingManager] = None):
        self.pairing = pairing_mgr or pairing_manager
        self.master_enabled = True
        self._discovered: dict[str, DiscoveredNearbyDevice] = {}
        self._listeners: list[Callable[[DiscoveredNearbyDevice], None]] = []

    def toggle_master_discovery(self, enabled: bool) -> bool:
        self.master_enabled = enabled
        if not enabled:
            self._discovered.clear()
            logger.info("Nearby discovery disabled by user.")
        return self.master_enabled

    def add_listener(self, cb: Callable[[DiscoveredNearbyDevice], None]) -> None:
        self._listeners.append(cb)

    def register_announcement(
        self,
        device_id: str,
        friendly_name: str,
        device_type: DeviceType,
        connection_method: str = "LAN",
    ) -> Optional[DiscoveredNearbyDevice]:
        """Processes an incoming nearby presence beacon (e.g. from Android app)."""
        if not self.master_enabled:
            return None

        # Check if already enrolled
        enrolled = {d.device_id: d for d in self.pairing.get_enrolled_devices()}
        is_paired = device_id in enrolled and enrolled[device_id].trust_level == TrustLevel.PAIRED_TRUSTED

        discovered = DiscoveredNearbyDevice(
            device_id=device_id,
            friendly_name=friendly_name,
            device_type=device_type,
            proximity=ProximityCategory.IMMEDIATE_LOCAL if connection_method in ("BLE", "mDNS") else ProximityCategory.REACHABLE_NETWORK,
            is_already_paired=is_paired,
            requires_pairing=not is_paired,
            connection_method=connection_method,
            discovered_at=time.time(),
        )
        self._discovered[device_id] = discovered
        for cb in self._listeners:
            try:
                cb(discovered)
            except Exception as e:
                logger.warning("Discovery callback error: %s", e)

        return discovered

    def get_nearby_devices(self) -> list[DiscoveredNearbyDevice]:
        if not self.master_enabled:
            return []
        now = time.time()
        # Drop stale discoveries (> 3 minutes old)
        fresh = [d for d in self._discovered.values() if now - d.discovered_at < 180.0]
        return fresh


nearby_discovery = NearbyDiscoveryEngine()
