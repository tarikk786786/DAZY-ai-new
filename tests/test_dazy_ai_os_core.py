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


def test_canonical_tarik_identity_and_persona():
    from core.dazy_persona import build_dazy_system_prompt
    from memory.config_manager import get_user_name

    # 1. Configured name must be Tarik
    assert get_user_name() == "Tarik", "Canonical user name must resolve to Tarik"

    # 2. Persona prompt must include Tarik and forbid John/Alex
    prompt = build_dazy_system_prompt()
    assert "Tarik" in prompt, "System prompt must address user as Tarik"
    assert "John" not in prompt, "System prompt must never contain John"
    assert "Alex" not in prompt, "System prompt must never contain Alex"


def test_durable_task_idempotency_and_concurrency():
    from core.ai_os import DurableTaskEngine
    engine = DurableTaskEngine.get_instance()

    # Submit task with idempotency key
    key = "idem_task_concurrent_001"
    t1 = engine.submit_task(
        title="Concurrent Job A",
        input_payload={"batch": 1},
        idempotency_key=key,
    )
    # Duplicate submission with same key must return identical task record!
    t2 = engine.submit_task(
        title="Concurrent Job A Duplicate",
        input_payload={"batch": 2},
        idempotency_key=key,
    )
    assert t1.id == t2.id, "Idempotent submission must deduplicate task"
    assert t1.title == t2.title


def test_memory_scopes_isolation_and_reasoning_synthesis():
    from core.ai_os.memory import MemoryAuditService, MemoryScope
    mem = MemoryAuditService.get_instance()

    # Store memory for Tarik in project A
    m1 = mem.store_memory(
        content="User preferred audio output is Virtual Cable B",
        scope=MemoryScope.LONG_TERM,
        owner="Tarik",
        project_id="proj_audio",
    )
    assert m1.owner == "Tarik"

    # Search by different owner -> Must return 0 results! (Strict user isolation)
    leak_check = mem.search_memory("Virtual Cable", owner="AnonymousUser")
    assert len(leak_check) == 0, "Cross-user memory access must be blocked"

    # Search with correct owner and project -> Must return result
    hits = mem.search_memory("Virtual Cable", owner="Tarik", project_id="proj_audio")
    assert len(hits) >= 1
    assert hits[0].retrieval_count >= 1

    # Verify reasoning prompt context synthesis
    reasoning_ctx = mem.build_reasoning_context("Virtual Cable", owner="Tarik", project_id="proj_audio")
    assert "Virtual Cable B" in reasoning_ctx
    assert "[LONG_TERM]" in reasoning_ctx


def test_controlled_repair_runaway_loop_prevention():
    from core.ai_os import ControlledRepairEngine, RepairRiskLevel
    repair = ControlledRepairEngine.get_instance()

    inc = repair.record_incident(
        title="Recurring Flapping Service",
        severity="WARNING",
        component="worker_flapper",
        root_cause="OOM kill loop",
    )
    plan = repair.propose_repair(
        incident_id=inc.id,
        action="bounded_retry",
        description="Retry flapping service",
    )
    # 3 attempts should succeed
    for _ in range(3):
        assert repair.execute_repair(plan.id) is True

    # 4th attempt must be flagged as runaway and blocked without explicit operator approval!
    blocked = repair.execute_repair(plan.id, force_approved=False)
    assert blocked is False, "Runaway repair loop must be blocked from autonomous execution"


def test_mcp_security_ssrf_and_sensitive_checks():
    from core.mcp.security import verify_mcp_call

    # Allowed safe call
    ok, _ = verify_mcp_call("read_docs", {"topic": "python"})
    assert ok is True

    # Destructive blocked
    blocked_del, reason_del = verify_mcp_call("delete_database", {})
    assert blocked_del is False
    assert "Sensitive" in reason_del

    # SSRF blocked
    blocked_ssrf, reason_ssrf = verify_mcp_call("fetch_url", {"url": "http://169.254.169.254/latest/meta-data"})
    assert blocked_ssrf is False
    assert "SSRF" in reason_ssrf


def test_repo_radar_and_user_profile_endpoints():
    import time
    from starlette.testclient import TestClient
    from dashboard.server import DashboardServer

    server = DashboardServer()
    token = "test_token_tarik_123"
    server._tokens[token] = time.time()
    app = server._build_app()

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Profile /api/me
    res_me = client.get("/api/me", headers=headers)
    assert res_me.status_code == 200
    data_me = res_me.json()
    assert data_me["id"] == "usr_tarik"
    assert data_me["displayName"] == "Tarik"
    assert data_me["timezone"] == "Asia/Kolkata"

    # 2. Repo Radar /api/os/repo-radar
    res_radar = client.get("/api/os/repo-radar", headers=headers)
    assert res_radar.status_code == 200
    data_radar = res_radar.json()
    assert "repositories" in data_radar
    repos = {r["name"]: r for r in data_radar["repositories"]}
    assert "nanobot" in repos
    assert repos["nanobot"]["resource_rating"] == "light"
    assert "Silero VAD" in repos

    # 3. Testing Center Status /api/testing/status
    res_test = client.get("/api/testing/status", headers=headers)
    assert res_test.status_code == 200
    data_test = res_test.json()
    assert data_test["ok"] is True
    assert data_test["total_tests"] == 132
    assert data_test["passed"] == 132
    assert data_test["release_ready"] is True
    assert len(data_test["sections"]) == 13

    # 4. Safe Smoke Suite /api/testing/run-smoke
    res_smoke = client.post("/api/testing/run-smoke", headers=headers)
    assert res_smoke.status_code == 200
    data_smoke = res_smoke.json()
    assert data_smoke["ok"] is True
    assert data_smoke["smoke_passed"] is True
    assert data_smoke["memory_isolated"] is True
    assert data_smoke["status_label"] == "REAL TESTED"





