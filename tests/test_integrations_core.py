"""Unit tests for DAZY Lightweight Integrations and Activepieces Automation Subsystem."""
import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.automation.approval import require_approval_for_action, ActionRiskLevel
from core.automation.manager import get_automation_manager
from core.automation.planner import AutomationPlanner
from core.automation.suggestion_engine import get_suggestion_engine
from core.mcp.activepieces_adapter import get_activepieces_adapter
from integrations.api_discovery import get_api_discovery_manager
from integrations.auth_manager import get_auth_manager
from integrations.credential_manager import get_credential_manager
from integrations.http_client import get_shared_client
from plugins.automation import run as run_automation_plugin


def test_http_client_singleton():
    client1 = get_shared_client()
    client2 = get_shared_client()
    assert client1 is client2
    assert client1.timeout == 15.0


def test_credential_manager_vault():
    cred_mgr = get_credential_manager()
    cred_mgr.store_secret("activepieces", "api_key", "test_ap_key_12345")
    retrieved = cred_mgr.get_secret("activepieces", "api_key")
    assert retrieved == "test_ap_key_12345"
    cred_mgr.delete_secret("activepieces", "api_key")


def test_auth_manager_lifecycle():
    auth_mgr = get_auth_manager()
    auth_mgr.set_token("test_service", "access_token_xyz", "refresh_token_abc", expires_in=3600)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        tok = loop.run_until_complete(auth_mgr.get_valid_token("test_service"))
        assert tok == "access_token_xyz"
    finally:
        loop.close()


def test_api_discovery_curated():
    disco = get_api_discovery_manager()
    results = disco.search_curated("weather")
    assert any("Open-Meteo" in r.name for r in results)

    quran_results = disco.search_curated("quran")
    assert any("Quran" in r.name for r in quran_results)


def test_activepieces_adapter():
    adapter = get_activepieces_adapter()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        flows = loop.run_until_complete(adapter.list_flows())
        assert len(flows) >= 3
        conns = loop.run_until_complete(adapter.list_connections())
        assert any(c["appName"] == "gmail" for c in conns)
    finally:
        loop.close()


def test_automation_planner_and_approval():
    planner = AutomationPlanner()
    spec = planner.plan_from_text("Create my morning briefing every day at 7 AM")
    assert "Morning Briefing" in spec.name
    assert spec.folder == "Personal"
    assert spec.trigger_type == "schedule"

    # Test approval gates
    req_pub, _ = require_approval_for_action("publish_flow", {})
    assert req_pub is True

    req_read, _ = require_approval_for_action("list_flows", {})
    assert req_read is False


def test_suggestion_engine_advisor():
    engine = get_suggestion_engine()
    pending = engine.list_pending_suggestions()
    assert len(pending) >= 2

    # Simulate recurring email checks
    for _ in range(4):
        engine.record_activity("check my emails please")

    assert len(engine.list_pending_suggestions()) >= 2


def test_automation_plugin_run():
    status_str = run_automation_plugin({"action": "status"})
    assert "Activepieces" in status_str

    advice_str = run_automation_plugin({"action": "get_advice"})
    assert "DAZY Advisor Recommendation" in advice_str
