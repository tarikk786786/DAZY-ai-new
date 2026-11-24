"""core/ai_os/schemas.py — Typed Pydantic models for DAZY AI OS entities."""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Enumerations ─────────────────────────────────────────────────────────────

class DataQualityState(str, enum.Enum):
    LIVE = "LIVE"
    CACHED = "CACHED"
    STALE = "STALE"
    DEMO = "DEMO"
    MOCKED = "MOCKED"
    UNTESTED = "UNTESTED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


class HealthStatus(str, enum.Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    OFFLINE = "OFFLINE"
    UNKNOWN = "UNKNOWN"


class WorkerStatus(str, enum.Enum):
    CREATED = "CREATED"
    READY = "READY"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SUSPECTED_UNHEALTHY = "SUSPECTED_UNHEALTHY"


class TaskStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


class RepairRiskLevel(str, enum.Enum):
    LOW_RISK_SAFE = "LOW_RISK_SAFE"
    APPROVAL_REQUIRED_RISKY = "APPROVAL_REQUIRED_RISKY"


# ── Core Entity Schemas ──────────────────────────────────────────────────────

class CapabilityFlags(BaseModel):
    text: bool = True
    vision: bool = False
    audio: bool = False
    tools: bool = True
    structured_output: bool = True
    streaming: bool = True


class ProviderInfo(BaseModel):
    id: str
    name: str
    kind: str = "llm"  # llm, stt, tts, embedding
    endpoint: str = ""
    health: HealthStatus = HealthStatus.UNKNOWN
    latency_ms: float = 0.0
    last_checked: str = Field(default_factory=_utc_now_iso)
    quality_state: DataQualityState = DataQualityState.UNTESTED
    note: str = ""


class ModelInfo(BaseModel):
    id: str
    provider_id: str
    name: str
    capabilities: CapabilityFlags = Field(default_factory=CapabilityFlags)
    context_window: int = 128000
    cost_per_1k_input_usd: float = 0.0
    cost_per_1k_output_usd: float = 0.0
    rate_limit_rpm: int = 60
    rate_limit_tpm: int = 1000000
    quality_state: DataQualityState = DataQualityState.LIVE
    is_active: bool = True


class WorkerInfo(BaseModel):
    id: str
    name: str
    role: str
    parent_id: Optional[str] = None
    status: WorkerStatus = WorkerStatus.READY
    model_id: str = "gemini-2.5-flash"
    capabilities: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    heartbeat_ts: float = 0.0
    usage_tokens: int = 0
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=_utc_now_iso)


class TaskRecord(BaseModel):
    id: str
    correlation_id: str
    title: str
    status: TaskStatus = TaskStatus.QUEUED
    assigned_worker_id: Optional[str] = None
    priority: int = 1  # 0: Urgent, 1: High, 2: Normal, 3: Low
    dependencies: List[str] = Field(default_factory=list)
    attempts: int = 0
    max_retries: int = 3
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    output_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=_utc_now_iso)
    updated_at: str = Field(default_factory=_utc_now_iso)


class MCPServerInfo(BaseModel):
    id: str
    name: str
    transport: str = "stdio"  # stdio, sse, stream
    command_or_url: str = ""
    status: HealthStatus = HealthStatus.UNKNOWN
    tools_provided: List[str] = Field(default_factory=list)
    resources_provided: List[str] = Field(default_factory=list)
    latency_ms: float = 0.0
    last_connected: Optional[str] = None
    quality_state: DataQualityState = DataQualityState.UNTESTED


class ToolInfo(BaseModel):
    id: str
    name: str
    description: str = ""
    parameters_schema: Dict[str, Any] = Field(default_factory=dict)
    provider_kind: str = "native"  # native, mcp, skill
    permission_required: bool = False
    execution_count: int = 0
    error_count: int = 0
    avg_duration_sec: float = 0.0


class IncidentRecord(BaseModel):
    id: str
    title: str
    severity: str = "WARNING"  # CRITICAL, ERROR, WARNING, INFO
    component: str = "system"
    root_cause: str = ""
    status: str = "OPEN"  # OPEN, INVESTIGATING, REPAIRED, CLOSED
    detected_at: str = Field(default_factory=_utc_now_iso)
    resolved_at: Optional[str] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)


class RepairPlan(BaseModel):
    id: str
    incident_id: str
    risk_level: RepairRiskLevel = RepairRiskLevel.LOW_RISK_SAFE
    description: str = ""
    allowlisted_action: str = ""  # bounded_retry, restart_worker, failover_provider, reconnect_mcp
    rollback_plan: str = ""
    verification_tests: List[str] = Field(default_factory=list)
    requires_approval: bool = False
    is_executed: bool = False
    is_verified: bool = False
    result_message: str = ""


# ── 3D Brain & Graph Models ──────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # orchestrator, model, worker, tool, mcp, memory, database, api, audio
    status: str = "HEALTHY"
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    quality_state: DataQualityState = DataQualityState.LIVE
    telemetry: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str = "data_flow"  # dependency, data_flow, invocation, telemetry
    active: bool = False
    throughput: float = 0.0


class GraphSnapshot(BaseModel):
    timestamp: str = Field(default_factory=_utc_now_iso)
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    correlation_id: str = "sys_init"
