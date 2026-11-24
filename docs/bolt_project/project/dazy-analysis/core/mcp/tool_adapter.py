"""core/mcp/tool_adapter.py — Adapts MCP tools to Mark-LVII tool schemas."""
from __future__ import annotations

from typing import Any, Callable


def adapt_mcp_tool(server_id: str, tool_def: dict[str, Any], invoke_fn: Callable) -> dict[str, Any]:
    """Converts an MCP Tool definition into a standard Mark-LVII capability dictionary.

    MCP schema:
        {"name": "...", "description": "...", "inputSchema": {...}}
    Mark-LVII schema:
        {"name": "...", "description": "...", "parameters": {...}}
    """
    raw_name = tool_def.get("name", "unnamed_tool")
    mcp_name = f"mcp_{server_id}_{raw_name}"
    description = tool_def.get("description", "")
    parameters = tool_def.get("inputSchema") or {"type": "object", "properties": {}}

    # Convert schema types to uppercase for Mark-LVII compatibility if needed
    decl = {
        "name": mcp_name,
        "description": f"[MCP:{server_id}] {description}".strip(),
        "parameters": parameters,
    }

    return decl
