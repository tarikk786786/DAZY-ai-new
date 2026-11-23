"""core/mcp/registry.py — MCP Server and Tool Registry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MCPServerRecord:
    id: str
    name: str
    transport: str            # "stdio" | "sse" | "http"
    command: str = ""
    args: list[str] = field(default_factory=list)
    url: str = ""
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    tools: list[dict[str, Any]] = field(default_factory=list)
    status: str = "disconnected"    # "connected" | "disconnected" | "error"
    error: str = ""


class MCPRegistry:
    def __init__(self):
        self._servers: dict[str, MCPServerRecord] = {}

    def register_server(self, record: MCPServerRecord) -> None:
        self._servers[record.id] = record

    def unregister_server(self, server_id: str) -> None:
        self._servers.pop(server_id, None)

    def get_server(self, server_id: str) -> Optional[MCPServerRecord]:
        return self._servers.get(server_id)

    def list_servers(self) -> list[MCPServerRecord]:
        return list(self._servers.values())


_GLOBAL_MCP_REGISTRY: Optional[MCPRegistry] = None


def get_mcp_registry() -> MCPRegistry:
    global _GLOBAL_MCP_REGISTRY
    if _GLOBAL_MCP_REGISTRY is None:
        _GLOBAL_MCP_REGISTRY = MCPRegistry()
    return _GLOBAL_MCP_REGISTRY
