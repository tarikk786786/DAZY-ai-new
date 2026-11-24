"""core/devices/device_hub.py — DAZY Central Device Hub.

Coordinates local machine status, enrolled paired devices, nearby discoveries,
and device privacy controls.
"""
from __future__ import annotations

import logging
import platform
import socket
import time
from typing import Optional

import psutil

from core.devices.handoff import TaskHandoffEngine, task_handoff
from core.devices.models import DazyDevice, DevicePermissions, DeviceStatus, DeviceType, TrustLevel
from core.devices.nearby_discovery import NearbyDiscoveryEngine, nearby_discovery
from core.devices.pairing import PairingManager, pairing_manager

logger = logging.getLogger("dazy.hub")


class DeviceHub:
    """Central manager for all DAZY-connected hardware."""

    def __init__(
        self,
        pairing_mgr: Optional[PairingManager] = None,
        discovery_engine: Optional[NearbyDiscoveryEngine] = None,
        handoff_engine: Optional[TaskHandoffEngine] = None,
    ):
        self.pairing = pairing_mgr or pairing_manager
        self.discovery = discovery_engine or nearby_discovery
        self.handoff = handoff_engine or task_handoff
        self.master_device_monitoring = True
        self._local_device = self._detect_local_device()

    def _detect_local_device(self) -> DazyDevice:
        hostname = socket.gethostname()
        battery = psutil.sensors_battery()
        battery_pct = battery.percent if battery else None
        charging = battery.power_plugged if battery else False

        ip = "127.0.0.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except Exception:
            pass

        return DazyDevice(
            device_id=f"win_{hostname.lower()}",
            friendly_name=f"{hostname} (Tarik's PC)",
            device_type=DeviceType.DESKTOP_WINDOWS,
            os_version=f"Windows {platform.release()}",
            status=DeviceStatus.ONLINE,
            trust_level=TrustLevel.PAIRED_TRUSTED,
            battery_level=battery_pct,
            is_charging=charging,
            network_ip=ip,
            permissions=DevicePermissions(
                allow_task_handoff=True,
                allow_notifications=True,
                allow_screen_context_share=True,
                allow_remote_file_transfer=True,
                allow_remote_control=True,
            ),
        )

    def get_local_device(self) -> DazyDevice:
        # Refresh dynamic battery
        b = psutil.sensors_battery()
        if b:
            self._local_device.battery_level = b.percent
            self._local_device.is_charging = b.power_plugged
        self._local_device.last_seen = time.time()
        return self._local_device

    def get_all_devices(self) -> list[DazyDevice]:
        devices = [self.get_local_device()]
        for d in self.pairing.get_enrolled_devices():
            if d.device_id != self._local_device.device_id:
                devices.append(d)
        return devices

    def set_master_monitoring(self, enabled: bool) -> bool:
        self.master_device_monitoring = enabled
        logger.info("Master device monitoring set to %s", enabled)
        return self.master_device_monitoring


device_hub = DeviceHub()
