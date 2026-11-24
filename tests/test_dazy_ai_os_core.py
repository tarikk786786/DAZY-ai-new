"""tests/test_dazy_ai_os_core.py — Automated verification for DAZY AI OS Subsystem."""
import pytest
from core.ai_os import (
    ControlPlaneRegistry,
    DurableTaskEngine,
    ControlledRepairEngine,
    GraphProjectionService,
    TaskStatus,
    WorkerStatus,
    RepairRiskLevel,
    DataQualityState,
    HealthStatus,
    EventType,
    EventEnvelope,
)


def test_registry_initialization_and_topologies():
    reg = ControlPlaneRegistry.get_instance()
    
    # 1. Providers
    providers = reg.get_providers()
    assert len(providers) >= 3, "Should have seeded default providers"
    prov_ids = {p.id for p in providers}
    assert "prov_gemini" in prov_ids
    assert "prov_edge_tts" in prov_ids
    assert "prov_whisper" in prov_ids

    # 2. Models
    models = reg.get_models()
    assert len(models) >= 1
    m = models[0]
    assert m.id == "gemini-2.5-flash"
    assert m.capabilities.tools is True
    assert m.capabilities.audio is True
    assert m.capabilities.vision is True

    # 3. Workers
    workers = reg.get_workers()
    assert len(workers) >= 6
    roles = {w.role for w in workers}
    assert "Task Decomposition & Brain Routing" in roles
    assert "VAD, Diarization, Prosody & Speech Normalization" in roles

    # 4. MCP Servers
    mcp_servers = reg.get_mcp_servers()
    assert len(mcp_servers) >= 5
    mcp_names = {s.name for s in mcp_servers}
    assert "context7" in mcp_names
    assert "playwright-mcp" in mcp_names


def test_durable_task_engine_lifecycle():
    task_engine = DurableTaskEngine.get_instance()
    events_caught = []

    def on_event(env: EventEnvelope):
        events_caught.append(env)

    task_engine.add_event_listener(on_event)

    # 1. Submit task
    t = task_engine.submit_task(
        title="Automated Test Suite Execution",
        input_payload={"suite": "ai_os"},
        worker_id="wrk_orchestrator",
        correlation_id="corr_test_01",
    )
    assert t.status == TaskStatus.QUEUED
    assert t.assigned_worker_id == "wrk_orchestrator"

    # 2. Start task
    t_running = task_engine.update_task_status(t.id, TaskStatus.RUNNING)
    assert t_running.status == TaskStatus.RUNNING

    # 3. Complete task
    t_done = task_engine.update_task_status(
        t.id, TaskStatus.COMPLETED, output={"passed": 120, "failed": 0}
    )
    assert t_done.status == TaskStatus.COMPLETED
    assert t_done.output_result["passed"] == 120

    # Verify event emission
    event_types = [e.event.event_type for e in events_caught]
    assert EventType.TASK_CREATED in event_types
    assert EventType.TASK_STARTED in event_types
    assert EventType.TASK_COMPLETED in event_types


def test_controlled_repair_engine_and_risk_gating():
    repair_engine = ControlledRepairEngine.get_instance()

    # 1. Safe Allowlisted Action (bounded retry)
    inc_safe = repair_engine.record_incident(
        title="Transient Upstream Timeout",
        severity="WARNING",
        component="llm_gateway",
        root_cause="HTTP 504 gateway timeout",
    )
    plan_safe = repair_engine.propose_repair(
        incident_id=inc_safe.id,
        action="bounded_retry",
        description="Retry with exponential jitter",
    )
    assert plan_safe.risk_level == RepairRiskLevel.LOW_RISK_SAFE
    assert plan_safe.requires_approval is False

    ok_safe = repair_engine.execute_repair(plan_safe.id)
    assert ok_safe is True

    # 2. Risky Action requiring human authorization
    inc_risky = repair_engine.record_incident(
        title="Schema Corruption",
        severity="CRITICAL",
        component="database",
        root_cause="Missing migration table",
    )
    plan_risky = repair_engine.propose_repair(
        incident_id=inc_risky.id,
        action="destructive_schema_migration",
        description="Apply DDL migration",
        rollback_plan="Restore from snapshot",
    )
    assert plan_risky.risk_level == RepairRiskLevel.APPROVAL_REQUIRED_RISKY
    assert plan_risky.requires_approval is True

    # Attempt execution without approval -> Must fail safely!
    ok_blocked = repair_engine.execute_repair(plan_risky.id, force_approved=False)
    assert ok_blocked is False, "Risky repair must NOT execute without human authorization"

    # Execution with explicit approval
    ok_approved = repair_engine.execute_repair(plan_risky.id, force_approved=True)
    assert ok_approved is True


def test_3d_graph_projection_snapshot():
    graph_svc = GraphProjectionService.get_instance()
    snapshot = graph_svc.build_snapshot(correlation_id="test_snap_01")

    assert len(snapshot.nodes) >= 12, "Should project orchestrator, models, workers, and MCP tools"
    assert len(snapshot.edges) >= 10, "Should project connections between orchestrator and components"

    # Verify center node
    center = next((n for n in snapshot.nodes if n.id == "node_orchestrator"), None)
    assert center is not None
    assert center.x == 0.0 and center.y == 0.0 and center.z == 0.0

    # Verify edge connectivity
    edge_targets = {e.target for e in snapshot.edges}
    assert any("wrk_" in t for t in edge_targets), "Edges must connect to workers"
    assert any("gemini" in t for t in edge_targets), "Edges must connect to model rungs"


def test_telemetry_service_and_tracing():
    from core.ai_os import TelemetryService
    telemetry = TelemetryService.get_instance()

    events_received = []
    telemetry.subscribe(lambda evt: events_received.append(evt))

    # Span execution
    with telemetry.start_span("test_inference_pipeline", attributes={"model": "gemini-2.5-flash"}) as span:
        telemetry.record_tokens(prompt_tokens=42, completion_tokens=18)
        telemetry.log_event("info", "Token streaming started", correlation_id=span.trace_id)

    assert span.status == "OK"
    assert span.duration_ms >= 0.0

    summary = telemetry.get_summary()
    assert summary["metrics"]["tokens_total"] >= 60.0
    assert summary["metrics"]["requests_total"] >= 1.0
    assert len(summary["recent_spans"]) >= 1
    assert any(evt.get("type") == "trace_span" for evt in events_received)
    assert any(evt.get("type") == "metric_update" for evt in events_received)


def test_desktop_companion_ai_os_integration():
    from core.ai_os import DurableTaskEngine, ControlledRepairEngine, TelemetryService
    
    # 1. Enqueue task via desktop hook logic
    task_engine = DurableTaskEngine.get_instance()
    task = task_engine.submit_task(
        title="Desktop Quick Shortcut Verification",
        input_payload={"trigger": "hotkey_ctrl_alt_d"},
        worker_id="wrk_orchestrator",
    )
    assert task.id.startswith("task_")
    assert task.title == "Desktop Quick Shortcut Verification"

    # 2. Trigger Emergency Stop from desktop hook
    repair = ControlledRepairEngine.get_instance()
    inc = repair.record_incident(
        title="Desktop Emergency Stop Triggered",
        severity="CRITICAL",
        component="desktop_companion",
        root_cause="Operator manual emergency shutdown from desktop shell",
    )
    assert inc.severity == "CRITICAL"
    assert inc.component == "desktop_companion"

    # 3. Verify telemetry trace captured
    telemetry = TelemetryService.get_instance()
    telemetry.log_event("warn", "EMERGENCY STOP executed from Desktop Companion", data={"incident_id": inc.id})
    summary = telemetry.get_summary()
    assert any("EMERGENCY STOP" in l["message"] for l in summary["recent_logs"])


