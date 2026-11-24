"""core/mcp/security.py — MCP Tool Security and Permission Gates."""
from __future__ import annotations

from typing import Any

# Sensitive patterns that require explicit user confirmation
SENSITIVE_TOOL_PATTERNS = (
    "delete", "remove", "drop", "terminate", "format", "shutdown",
    "kill", "overwrite", "send_email", "post", "publish", "payment",
)


def verify_mcp_call(tool_name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
    """Inspects MCP tool call for destructive or high-risk actions.

    Integrates with core/confirm.py logic.
    """
    clean_name = tool_name.lower()
    for pattern in SENSITIVE_TOOL_PATTERNS:
        if pattern in clean_name:
            return False, f"Sensitive MCP operation '{tool_name}' requires confirmation"

    return True, "Allowed"
