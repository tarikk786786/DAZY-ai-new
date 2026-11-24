"""Unit tests for DAZY capabilities and MCP subsystems."""
import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.capabilities.discovery import discover_all_capabilities
from core.capabilities.evaluator import evaluate_capability_safety
from core.capabilities.registry import Capability, get_capability_registry
from core.capabilities.router import execute_capability
from core.mcp.manager import get_mcp_manager
from core.mcp.registry import MCPServerRecord
from core.mcp.security import verify_mcp_call
from core.mcp.tool_adapter import adapt_mcp_tool


def test_capability_discovery_finds_actions_and_skills():
    discovered = discover_all_capabilities()
    assert len(discovered["actions"]) > 0
    assert len(discovered["skills"]) > 0

    reg = get_capability_registry()
    assert reg.get("open_app") is not None or len(reg.list_all()) > 0


def test_capability_evaluator():
    safe_cap = Capability(
        id="test:1",
        name="test_tool",
        kind="action",
        description="A test tool",
        parameters={"type": "object"},
        handler=lambda: "ok",
    )
    safe, msg = evaluate_capability_safety(safe_cap)
    assert safe is True


def test_mcp_security_flags_sensitive():
    allowed, _ = verify_mcp_call("search_docs", {"query": "hello"})
    assert allowed is True

    blocked, reason = verify_mcp_call("delete_user_data", {"user_id": 123})
    assert blocked is False
    assert "Sensitive" in reason


def test_mcp_tool_adapter():
    mcp_tool_def = {
        "name": "fetch_record",
        "description": "Fetches a record",
        "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}},
    }
    adapted = adapt_mcp_tool("database", mcp_tool_def, lambda *args: None)
    assert adapted["name"] == "mcp_database_fetch_record"
    assert "parameters" in adapted
