"""integrations/base.py — Standard Contract for External Integrations."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class IntegrationStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNCONFIGURED = "unconfigured"


@dataclass
class HealthReport:
    healthy: bool
    status: IntegrationStatus
    latency_ms: float = 0.0
    message: str = "OK"
    details: dict[str, Any] = field(default_factory=dict)


class BaseIntegration:
    """Base adapter for remote REST and public APIs in DAZY."""

    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.status = IntegrationStatus.UNCONFIGURED
        self.last_error: Optional[str] = None
        self._rate_limit_remaining: Optional[int] = None

    async def check_health(self) -> HealthReport:
        """Pings or verifies connectivity to the remote service."""
        return HealthReport(healthy=True, status=self.status)

    async def close(self) -> None:
        """Cleans up sockets or local caches."""
        self.status = IntegrationStatus.DISCONNECTED
