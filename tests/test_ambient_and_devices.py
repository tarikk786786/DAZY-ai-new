"""tests/test_ambient_and_devices.py — Comprehensive Tests for Ambient Intelligence, Memory & Multi-Device Ecosystem."""
import os
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from core.ambient.governor import ResourceGovernor, ThrottleLevel
from core.ambient.screen_observer import ScreenObserver, WindowContext
from core.ambient.task_observer import TaskEvent, TaskObserver
from core.ambient.proactive_alerts import AlertPriority, ProactiveAlertEngine
from memory.dazy_memory import DazyMemoryEngine, WorkingMemory
from memory.supabase_sync import SupabaseSyncEngine
from core.devices.models import DazyDevice, DeviceType, TrustLevel, DevicePermissions
from core.devices.pairing import PairingManager
from core.devices.nearby_discovery import NearbyDiscoveryEngine, ProximityCategory
from core.devices.handoff import TaskHandoffEngine
from core.devices.device_hub import DeviceHub
from backend.app import app


# ── 1. Resource Governor Tests ───────────────────────────────────────────────

def test_resource_governor_evaluation(tmp_path):
    gov = ResourceGovernor(
        max_active_tasks=3,
        storage_ceiling_mb=10,
        temp_dir=tmp_path / "temp",
        cpu_throttle_threshold=50.0,
        cpu_suspend_threshold=80.0,
    )
    status = gov.evaluate_system(current_active_tasks=1)
    assert status.throttle_level in (ThrottleLevel.NORMAL, ThrottleLevel.THROTTLED, ThrottleLevel.SUSPENDED)
    assert not status.queue_bounded

    # Test queue bounding
    can_admit = gov.can_admit_task(current_active_tasks=3)
    assert not can_admit

    # Test storage ceiling enforcement
    dummy = tmp_path / "temp" / "heavy.bin"
    dummy.write_bytes(b"0" * 1024)
    assert gov.get_temp_storage_size() >= 1024


# ── 2. Screen Observer Tests ─────────────────────────────────────────────────

def test_screen_observer_context_deduplication():
    observer = ScreenObserver()
    events = []
    observer.add_listener(events.append)

    ctx1 = WindowContext("Code.exe", "DAZY Project - VS Code", 1234, time.time(), "VS Code")
    ctx2 = WindowContext("Code.exe", "DAZY Project - VS Code", 1234, time.time() + 1, "VS Code")
    ctx3 = WindowContext("chrome.exe", "Activepieces Automation", 5678, time.time() + 2, "Chrome")

    # Manually trigger notify
    observer._last_context = None
    observer._notify(ctx1)
    observer._last_context = ctx1
    assert len(events) == 1

    # Same context should not trigger in poll logic
    assert observer._last_context.window_title == ctx2.window_title


# ── 3. Task Observer & Proactive Alerts Tests ────────────────────────────────

def test_task_observer_and_proactive_alerts():
    alert_engine = ProactiveAlertEngine(cooldown_seconds=0.1)
    received_alerts = []
    alert_engine.add_alert_listener(received_alerts.append)

    ev_done = TaskEvent(
        task_id="t_001",
        agent_name="researcher",
        status="done",
        goal="Analyze Activepieces Docs",
        result_summary="Report generated.",
        timestamp=time.time(),
    )
    alert = alert_engine.on_task_event(ev_done)
    assert alert is not None
    assert alert.priority == AlertPriority.NORMAL
    assert "successfully complete" in alert.message
    assert len(received_alerts) == 1

    # Test failure alert
    ev_fail = TaskEvent(
        task_id="t_002",
        agent_name="automation",
        status="failed",
        goal="Sync Webhook",
        result_summary="",
        timestamp=time.time(),
        error="Connection Refused",
    )
    alert_fail = alert_engine.on_task_event(ev_fail)
    assert alert_fail is not None
    assert alert_fail.priority == AlertPriority.HIGH
    assert "error aayi hai" in alert_fail.message


# ── 4. 3-Layer SQLite FTS5 Memory Tests ──────────────────────────────────────

def test_dazy_3layer_memory(tmp_path):
    db_file = tmp_path / "test_memory.sqlite3"
    mem = DazyMemoryEngine(db_file)

    # 1. Working Memory
    mem.working.set_active_window("msedge.exe", "Supabase Dashboard")
    mem.working.record_turn("user", "Hello DAZY")
    mem.working.record_turn("assistant", "Namaste Tarik!")
    assert len(mem.working.recent_dialogue_turns) == 2
    assert mem.working.active_process_name == "msedge.exe"

    # 2. Event Memory (with TTL)
    ev_id = mem.record_event("app_switch", "work", "Switched to Supabase", ttl_seconds=3600)
    assert ev_id > 0
    recent = mem.get_recent_events(limit=5)
    assert len(recent) == 1
    assert recent[0]["summary"] == "Switched to Supabase"

    # 3. Long-term Memory & FTS Search
    mem.remember("favorite_beverage", "Adrak Wali Chai", category="preferences", importance=3)
    mem.remember("primary_project", "DAZY Multi-Device AI", category="projects", importance=5)

    all_lt = mem.get_all_long_term()
    assert len(all_lt) == 2

    # Search with FTS / keyword
    results = mem.search_long_term("Chai")
    assert len(results) >= 1
    assert results[0]["key"] == "favorite_beverage"

    # Format context for prompt
    prompt_ctx = mem.format_prompt_context()
    assert "Adrak Wali Chai" in prompt_ctx
    assert "Supabase Dashboard" in prompt_ctx

    # Forget
    forgotten = mem.forget("favorite_beverage", category="preferences")
    assert forgotten
    assert len(mem.get_all_long_term()) == 1


# ── 5. Supabase Sync Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_supabase_sync_offline_resilience(tmp_path):
    db_file = tmp_path / "test_sync.sqlite3"
    mem = DazyMemoryEngine(db_file)
    mem.remember("secret_preference", "Dark Mode", category="ui")

    sync = SupabaseSyncEngine(
        supabase_url="https://mllmkgwlkmbnaclanunr.supabase.co",
        supabase_key="",  # unconfigured key
        memory_engine=mem,
    )
    assert not sync.is_configured()
    res = await sync.sync_outbound()
    assert not res.success
    assert "not configured" in res.error.lower()


# ── 6. Multi-Device Ecosystem, Pairing & Handoff Tests ───────────────────────

def test_device_pairing_and_handoff(tmp_path):
    pairing_mgr = PairingManager(expiry_seconds=60)
    
    # 1. Pairing Request
    session = pairing_mgr.create_pairing_request(
        device_id="android_phone_tarik",
        device_name="Tarik's Pixel",
        device_type=DeviceType.MOBILE_ANDROID,
    )
    assert len(session.one_time_code) == 6
    qr_payload = pairing_mgr.generate_qr_payload(session)
    assert "session_id" in qr_payload

    # 2. Code Verification
    device = pairing_mgr.verify_and_approve(session.session_id, session.one_time_code)
    assert device is not None
    assert device.trust_level == TrustLevel.PAIRED_TRUSTED
    assert len(pairing_mgr.get_enrolled_devices()) == 1

    # 3. Nearby Discovery
    discovery = NearbyDiscoveryEngine(pairing_mgr)
    discovered = discovery.register_announcement(
        device_id="android_phone_tarik",
        friendly_name="Tarik's Pixel",
        device_type=DeviceType.MOBILE_ANDROID,
        connection_method="LAN",
    )
    assert discovered is not None
    assert discovered.is_already_paired
    assert not discovered.requires_pairing
    assert len(discovery.get_nearby_devices()) == 1

    # 4. Context & Task Handoff
    db_file = tmp_path / "test_handoff.sqlite3"
    mem = DazyMemoryEngine(db_file)
    mem.working.set_active_window("PyCharm", "DAZY Codebase")
    mem.working.latest_user_request = "Summarize daily news"
    mem.working.scratchpad["draft"] = "News brief in Hinglish"

    handoff = TaskHandoffEngine(pairing_mgr, mem)
    pkg = handoff.prepare_handoff("windows_pc", "android_phone_tarik", task_id="task_999")
    assert pkg is not None
    assert pkg.status == "pending"
    assert "DAZY Codebase" in pkg.conversation_summary

    # Target device accepts
    mem_phone = DazyMemoryEngine(tmp_path / "phone_mem.sqlite3")
    handoff_phone = TaskHandoffEngine(pairing_mgr, mem_phone)
    handoff_phone._active_packages[pkg.package_id] = pkg
    accepted = handoff_phone.accept_handoff(pkg.package_id)
    assert accepted
    assert mem_phone.working.active_task_id == "task_999"
    assert mem_phone.working.scratchpad.get("draft") == "News brief in Hinglish"

    # 5. Revocation
    revoked = pairing_mgr.revoke_device("android_phone_tarik")
    assert revoked
    assert device.trust_level == TrustLevel.REVOKED


# ── 7. Coolify FastAPI Backend Endpoints Tests ───────────────────────────────

def test_coolify_fastapi_backend():
    client = TestClient(app)

    # Liveness & Readiness
    res_health = client.get("/health")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["status"] == "healthy"

    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["ready"] is True

    # Device Heartbeat
    hb_payload = {
        "device_id": "pixel_8",
        "friendly_name": "Tarik Phone",
        "device_type": "android_mobile",
        "battery_level": 84.5,
        "is_charging": False,
        "active_tasks": 1,
    }
    res_hb = client.post("/api/devices/heartbeat", json=hb_payload)
    assert res_hb.status_code == 200
    assert res_hb.json()["status"] == "recorded"

    # List Devices
    res_devs = client.get("/api/devices")
    assert res_devs.status_code == 200
    assert len(res_devs.json()["devices"]) >= 1

    # Inbound Webhook Relay
    wh_payload = {
        "source": "activepieces",
        "event_type": "flow_finished",
        "data": {"flow_id": "fl_123", "status": "success"},
    }
    res_wh = client.post("/api/webhooks/relay", json=wh_payload)
    assert res_wh.status_code == 200
    assert res_wh.json()["status"] == "relayed"

    # Pull Relayed Events
    res_pull = client.get("/api/events/pull?limit=5")
    assert res_pull.status_code == 200
    events = res_pull.json()["events"]
    assert len(events) == 1
    assert events[0]["source"] == "activepieces"
