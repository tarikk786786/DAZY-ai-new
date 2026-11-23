"""core/mcp/manager.py — Dynamic MCP Manager and lifecycle controller."""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from core.capabilities.registry import Capability, get_capability_registry
from core.mcp.client import MCPClient
from core.mcp.registry import MCPServerRecord, get_mcp_registry
from core.mcp.security import verify_mcp_call
from core.mcp.tool_adapter import adapt_mcp_tool


class MCPManager:
    """Manages external MCP servers, dynamic connection, and capability mounting."""

    def __init__(self):
        self.registry = get_mcp_registry()
        self.active_clients: dict[str, MCPClient] = {}

    async def attach_server(self, record: MCPServerRecord) -> bool:
        """Connects to an MCP server, queries its tools, and mounts them."""
        self.registry.register_server(record)
        client = MCPClient(
            server_id=record.id,
            command=record.command,
            args=record.args,
            url=record.url,
        )
        ok = await client.connect()
        if not ok:
            record.status = "error"
            record.error = "Connection failed"
            return False

        record.status = "connected"
        self.active_clients[record.id] = client

        # Mount tools into CapabilityRegistry
        cap_reg = get_capability_registry()
        for tool_def in record.tools:
            adapted = adapt_mcp_tool(record.id, tool_def, client.call_tool)
            cap = Capability(
                id=f"mcp:{record.id}:{tool_def.get('name')}",
                name=adapted["name"],
                kind="mcp",
                description=adapted["description"],
                parameters=adapted["parameters"],
                handler=lambda args, _t=tool_def.get('name'), _c=client: _c.call_tool(_t, args),
                source=f"mcp://{record.id}",
            )
            cap_reg.register(cap)

        return True

    async def detach_server(self, server_id: str) -> None:
        """Disconnects an MCP server and unmounts its tools."""
        client = self.active_clients.pop(server_id, None)
        if client:
            await client.close()
        rec = self.registry.get_server(server_id)
        if rec:
            rec.status = "disconnected"
            cap_reg = get_capability_registry()
            for tool_def in rec.tools:
                mcp_name = f"mcp_{rec.id}_{tool_def.get('name')}"
                cap_reg.unregister(mcp_name)


_GLOBAL_MCP_MANAGER: Optional[MCPManager] = None


def get_mcp_manager() -> MCPManager:
    global _GLOBAL_MCP_MANAGER
    if _GLOBAL_MCP_MANAGER is None:
        _GLOBAL_MCP_MANAGER = MCPManager()
    return _GLOBAL_MCP_MANAGER
