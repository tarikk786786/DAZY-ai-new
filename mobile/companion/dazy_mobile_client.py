"""mobile/companion/dazy_mobile_client.py — DAZY Mobile Companion SDK.

Lightweight client library for the DAZY Android Companion application.
Communicates with Supabase Cloud for memories and Coolify FastAPI backend for
task coordination and notifications without requiring heavy on-device models.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

import httpx

logger = logging.getLogger("dazy.mobile")


class DazyMobileClient:
    """Client for Android companion app to interact with DAZY ecosystem."""

    def __init__(
        self,
        backend_url: str = "http://localhost:8000",
        supabase_url: str = "https://mllmkgwlkmbnaclanunr.supabase.co",
        supabase_key: str = "",
        device_id: str = "android_mobile_1",
        friendly_name: str = "Tarik's Android Phone",
    ):
        self.backend_url = backend_url.rstrip("/")
        self.supabase_url = supabase_url.rstrip("/")
        self.supabase_key = supabase_key
        self.device_id = device_id
        self.friendly_name = friendly_name

    async def send_heartbeat(self, battery_level: float, is_charging: bool, active_tasks: int = 0) -> bool:
        """Sends periodic lightweight heartbeat to the Coolify backend."""
        payload = {
            "device_id": self.device_id,
            "friendly_name": self.friendly_name,
            "device_type": "android_mobile",
            "battery_level": battery_level,
            "is_charging": is_charging,
            "active_tasks": active_tasks,
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(f"{self.backend_url}/api/devices/heartbeat", json=payload)
                return res.status_code == 200
        except Exception as exc:
            logger.debug("Failed to send mobile heartbeat: %s", exc)
            return False

    async def fetch_shared_memories(self, limit: int = 20) -> list[dict[str, Any]]:
        """Pulls shared user memories directly from Supabase Cloud."""
        if not self.supabase_key:
            return []
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(
                    f"{self.supabase_url}/rest/v1/dazy_memories?select=*&order=updated_at.desc&limit={limit}",
                    headers={"apikey": self.supabase_key, "Authorization": f"Bearer {self.supabase_key}"},
                )
                if res.status_code == 200:
                    return res.json()
        except Exception as exc:
            logger.debug("Failed to fetch memories: %s", exc)
        return []

    async def request_desktop_task(self, action: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Sends an authorized remote request from mobile to desktop."""
        payload = {
            "action": action,
            "target_device": "windows_desktop",
            "parameters": parameters,
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(f"{self.backend_url}/api/tasks/coordinate", json=payload)
                return res.json()
        except Exception as exc:
            return {"status": "error", "message": str(exc)}
