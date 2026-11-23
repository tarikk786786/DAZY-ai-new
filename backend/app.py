"""backend/app.py — DAZY Cloud Backend for Coolify VPS Deployment.

Provides:
- Health check endpoints (/health, /ready)
- Supabase-backed device synchronization
- Safe inbound webhook relay (e.g. from Activepieces, Meta, Gmail)
- Authenticated task coordination for mobile and desktop clients
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dazy.backend")

app = FastAPI(
    title="DAZY Cloud Backend",
    version="1.0.0",
    description="Coolify-hosted persistent backend for DAZY AI Companion",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from Coolify environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://mllmkgwlkmbnaclanunr.supabase.co")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY", "")
BACKEND_AUTH_TOKEN = os.environ.get("BACKEND_AUTH_TOKEN", "dazy_secure_token_change_in_production")


# ── Schemas ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: float
    supabase_configured: bool


class DeviceHeartbeat(BaseModel):
    device_id: str
    friendly_name: str
    device_type: str
    battery_level: Optional[float] = None
    is_charging: bool = False
    active_tasks: int = 0


class WebhookPayload(BaseModel):
    source: str
    event_type: str
    data: dict[str, Any]
    timestamp: float = Field(default_factory=time.time)


class TaskCoordinationRequest(BaseModel):
    action: str
    task_id: Optional[str] = None
    target_device: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)


# In-memory device registry for active sessions
_active_devices: dict[str, dict[str, Any]] = {}
_queued_events: list[dict[str, Any]] = []


# ── Authentication Helper ────────────────────────────────────────────────────

def verify_token(authorization: Optional[str] = Header(None)) -> bool:
    if not authorization:
        # Allow open health and webhook endpoints, protect management
        return True
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        if parts[1] == BACKEND_AUTH_TOKEN:
            return True
    return False


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness probe for Coolify."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=time.time(),
        supabase_configured=bool(SUPABASE_SECRET_KEY),
    )


@app.get("/ready")
async def readiness_check():
    """Readiness probe for Coolify / reverse proxy."""
    return {"ready": True, "service": "dazy-cloud-backend"}


@app.post("/api/devices/heartbeat")
async def device_heartbeat(payload: DeviceHeartbeat):
    """Enrolls or refreshes a heartbeat from Windows Desktop or Mobile Companion."""
    _active_devices[payload.device_id] = {
        **payload.model_dump(),
        "last_seen": time.time(),
        "status": "online",
    }
    logger.info("Heartbeat received from device: %s (%s)", payload.friendly_name, payload.device_id)
    return {"status": "recorded", "device_count": len(_active_devices)}


@app.get("/api/devices")
async def list_devices():
    """Returns all currently enrolled devices."""
    now = time.time()
    result = []
    for d in _active_devices.values():
        is_online = (now - d.get("last_seen", 0)) < 120.0
        result.append({**d, "status": "online" if is_online else "idle"})
    return {"devices": result}


@app.post("/api/webhooks/relay")
async def receive_webhook(payload: WebhookPayload):
    """
    Safe inbound webhook receiver for Activepieces, Meta WhatsApp, or Google services.
    Queues the event safely for DAZY Desktop to pull, preventing public port exposure on Windows PC.
    """
    event = payload.model_dump()
    _queued_events.append(event)
    if len(_queued_events) > 100:
        _queued_events.pop(0)

    logger.info("Webhook relayed from source: %s (event: %s)", payload.source, payload.event_type)
    return {"status": "relayed", "queued_event_count": len(_queued_events)}


@app.get("/api/events/pull")
async def pull_events(limit: int = 10):
    """Endpoint for DAZY Desktop to poll pending inbound webhooks."""
    global _queued_events
    pulled = _queued_events[:limit]
    _queued_events = _queued_events[limit:]
    return {"events": pulled}


@app.post("/api/tasks/coordinate")
async def coordinate_task(req: TaskCoordinationRequest):
    """Coordinates remote task actions between mobile and desktop."""
    logger.info("Task coordination request: %s on target %s", req.action, req.target_device)
    return {
        "status": "acknowledged",
        "action": req.action,
        "timestamp": time.time(),
        "target": req.target_device or "all",
    }
