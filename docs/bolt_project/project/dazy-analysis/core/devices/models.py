"""core/devices/models.py — Data models for the DAZY Multi-Device Ecosystem."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DeviceType(str, Enum):
    DESKTOP_WINDOWS = "windows_desktop"
    MOBILE_ANDROID = "android_mobile"
    TABLET = "tablet"
    MACOS = "macos"
    LINUX = "linux"
    WEB_DASHBOARD = "web_dashboard"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    IDLE = "idle"
    BUSY = "busy"


class TrustLevel(str, Enum):
    UNPAIRED = "unpaired"
    PENDING_VERIFICATION = "pending_verification"
    PAIRED_TRUSTED = "trusted"
    REVOKED = "revoked"


@dataclass
class DevicePermissions:
    allow_task_handoff: bool = True
    allow_notifications: bool = True
    allow_screen_context_share: bool = False
    allow_remote_file_transfer: bool = False
    allow_remote_control: bool = False


@dataclass
class DazyDevice:
    device_id: str
    friendly_name: str
    device_type: DeviceType
    os_version: str
    status: DeviceStatus = DeviceStatus.ONLINE
    trust_level: TrustLevel = TrustLevel.PAIRED_TRUSTED
    last_seen: float = field(default_factory=time.time)
    battery_level: Optional[float] = None
    is_charging: bool = False
    network_ip: Optional[str] = None
    active_tasks_count: int = 0
    permissions: DevicePermissions = field(default_factory=DevicePermissions)

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "friendly_name": self.friendly_name,
            "device_type": self.device_type.value,
            "os_version": self.os_version,
            "status": self.status.value,
            "trust_level": self.trust_level.value,
            "last_seen": self.last_seen,
            "battery_level": self.battery_level,
            "is_charging": self.is_charging,
            "network_ip": self.network_ip,
            "active_tasks_count": self.active_tasks_count,
            "permissions": {
                "allow_task_handoff": self.permissions.allow_task_handoff,
                "allow_notifications": self.permissions.allow_notifications,
                "allow_screen_context_share": self.permissions.allow_screen_context_share,
                "allow_remote_file_transfer": self.permissions.allow_remote_file_transfer,
                "allow_remote_control": self.permissions.allow_remote_control,
            },
        }
