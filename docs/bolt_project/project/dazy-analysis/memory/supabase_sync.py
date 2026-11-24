"""memory/supabase_sync.py — DAZY Supabase Cloud Synchronisation Engine.

Provides secure local-first bidirectional synchronisation between DAZY's local
SQLite store and your Supabase PostgreSQL cloud backend.
Project: mllmkgwlkmbnaclanunr (https://mllmkgwlkmbnaclanunr.supabase.co)
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from memory.dazy_memory import DazyMemoryEngine, dazy_memory

logger = logging.getLogger("dazy.supabase_sync")

DEFAULT_SUPABASE_URL = os.environ.get(
    "SUPABASE_URL", "https://mllmkgwlkmbnaclanunr.supabase.co"
)
DEFAULT_SUPABASE_KEY = os.environ.get(
    "SUPABASE_PUBLISHABLE_KEY", os.environ.get("SUPABASE_ANON_KEY", "")
)


@dataclass
class SyncResult:
    success: bool
    synced_count: int
    pending_count: int
    error: Optional[str] = None


class SupabaseSyncEngine:
    """Manages secure, low-bandwidth delta synchronization with Supabase Cloud."""

    def __init__(
        self,
        supabase_url: str = DEFAULT_SUPABASE_URL,
        supabase_key: str = DEFAULT_SUPABASE_KEY,
        memory_engine: Optional[DazyMemoryEngine] = None,
    ):
        self.url = supabase_url.rstrip("/")
        self.key = supabase_key
        self.memory = memory_engine or dazy_memory
        self._online = False

    def is_configured(self) -> bool:
        return bool(self.url and self.key)

    async def check_health(self) -> bool:
        """Pings Supabase health endpoint to check internet connectivity and project status."""
        if not self.is_configured():
            return False
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(
                    f"{self.url}/rest/v1/",
                    headers={"apikey": self.key, "Authorization": f"Bearer {self.key}"},
                )
                self._online = res.status_code in (200, 401, 403, 404)
                return self._online
        except Exception as e:
            logger.debug("Supabase connection check failed: %s", e)
            self._online = False
            return False

    async def sync_outbound(self) -> SyncResult:
        """Reads local unsynced records from SQLite and syncs to Supabase."""
        if not self.is_configured():
            return SyncResult(success=False, synced_count=0, pending_count=0, error="Supabase key not configured")

        is_alive = await self.check_health()
        if not is_alive:
            return SyncResult(success=False, synced_count=0, pending_count=0, error="Supabase offline or unreachable")

        unsynced = [m for m in self.memory.get_all_long_term(limit=50) if not m.get("synced")]
        if not unsynced:
            return SyncResult(success=True, synced_count=0, pending_count=0)

        synced_count = 0
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                for item in unsynced:
                    payload = {
                        "category": item["category"],
                        "key": item["key"],
                        "value": item["value"],
                        "importance": item["importance"],
                        "updated_at": item["updated_at"],
                    }
                    res = await client.post(
                        f"{self.url}/rest/v1/dazy_memories",
                        headers={
                            "apikey": self.key,
                            "Authorization": f"Bearer {self.key}",
                            "Content-Type": "application/json",
                            "Prefer": "resolution=merge-duplicates",
                        },
                        json=payload,
                    )
                    if res.status_code in (200, 201, 204):
                        synced_count += 1
                        # Mark synced in SQLite
                        with self.memory._get_connection() as conn:
                            conn.execute(
                                "UPDATE long_term_memory SET synced = 1 WHERE category = ? AND key = ?",
                                (item["category"], item["key"]),
                            )
                            conn.commit()

            return SyncResult(success=True, synced_count=synced_count, pending_count=len(unsynced) - synced_count)
        except Exception as exc:
            logger.warning("Supabase sync encountered error: %s", exc)
            return SyncResult(success=False, synced_count=synced_count, pending_count=len(unsynced), error=str(exc))

    async def sync_inbound(self) -> list[dict[str, Any]]:
        """Pulls remote memories updated since last sync and merges into local SQLite."""
        if not self.is_configured():
            return []

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(
                    f"{self.url}/rest/v1/dazy_memories?select=*&order=updated_at.desc&limit=25",
                    headers={"apikey": self.key, "Authorization": f"Bearer {self.key}"},
                )
                if res.status_code == 200:
                    records = res.json()
                    merged = []
                    for r in records:
                        cat = r.get("category", "notes")
                        k = r.get("key")
                        v = r.get("value")
                        if k and v:
                            self.memory.remember(k, v, category=cat, source="supabase_sync")
                            merged.append(r)
                    return merged
        except Exception as exc:
            logger.debug("Supabase inbound sync error: %s", exc)
        return []


supabase_sync = SupabaseSyncEngine()
