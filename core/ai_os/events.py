"""core/ai_os/events.py — Versioned real-time event contracts with correlation IDs."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


def _gen_uuid() -> str:
    return str(uuid.uuid4())


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EventType(str, enum.Enum):
    SYSTEM_HEALTH_CHANGED = "system.health.changed"
    PROVIDER_HEALTH_CHANGED = "provider.health.changed"
    WORKER_STATUS_CHANGED = "worker.status.changed"
    WORKER_HEARTBEAT = "worker.heartbeat"
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    MODEL_CALL_STARTED = "model.call.started"
    MODEL_CALL_COMPLETED = "model.call.completed"
    TOOL_CALL_STARTED = "tool.call.started"
    TOOL_CALL_COMPLETED = "tool.call.completed"
    TOOL_CALL_FAILED = "tool.call.failed"
    MEMORY_RETRIEVAL = "memory.retrieval"
    MEMORY_WRITE = "memory.write"
    INTEGRATION_TEST_COMPLETED = "integration.test.completed"
    INCIDENT_CREATED = "incident.created"
    INCIDENT_UPDATED = "incident.updated"
    REPAIR_PROPOSED = "repair.proposed"
    REPAIR_APPROVAL_REQUIRED = "repair.approval_required"
    REPAIR_STARTED = "repair.started"
    REPAIR_VERIFIED = "repair.verified"
    REPAIR_ROLLED_BACK = "repair.rolled_back"
    TELEMETRY_PACKET = "telemetry.packet"
    VOICE_STATE_CHANGED = "voice.state.changed"


class AIEvent(BaseModel):
    event_id: str = Field(default_factory=_gen_uuid)
    timestamp: str = Field(default_factory=_utc_now_iso)
    event_type: EventType
    correlation_id: str
    source_component: str
    schema_version: str = "1.0"
    tenant_scope: str = "default"
    payload: Dict[str, Any] = Field(default_factory=dict)


class EventEnvelope(BaseModel):
    """Outer transport envelope for WebSocket broadcasts."""
    type: str = "ai_os_event"
    event: AIEvent

    @classmethod
    def create(
        cls,
        event_type: EventType,
        correlation_id: str,
        source_component: str,
        payload: Dict[str, Any],
        tenant_scope: str = "default",
    ) -> EventEnvelope:
        ev = AIEvent(
            event_type=event_type,
            correlation_id=correlation_id,
            source_component=source_component,
            payload=payload,
            tenant_scope=tenant_scope,
        )
        return cls(event=ev)
