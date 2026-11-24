"""core/mcp/security.py — MCP Tool Security and Permission Gates."""
from __future__ import annotations

from typing import Any

# Sensitive patterns that require explicit user confirmation
SENSITIVE_TOOL_PATTERNS = (
    "delete", "remove", "drop", "terminate", "format", "shutdown",
    "kill", "overwrite", "send_email", "post", "publish", "payment",
)

# SSRF and Cloud Metadata Blocklist
BLOCKED_HOST_PATTERNS = (
    "169.254.169.254",       # AWS/GCP/Azure instance metadata
    "metadata.google.internal",
    "169.254.169.250",
    "fd00:ec2::254",
)


def verify_mcp_call(tool_name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
    """Inspects MCP tool call for destructive actions, SSRF attempts, and high-risk operations.

    Integrates with core/confirm.py logic.
    """
    clean_name = tool_name.lower()
    for pattern in SENSITIVE_TOOL_PATTERNS:
        if pattern in clean_name:
            return False, f"Sensitive MCP operation '{tool_name}' requires confirmation"

    # Argument validation & SSRF check
    for key, val in arguments.items():
        if isinstance(val, str):
            val_lower = val.lower()
            for blocked in BLOCKED_HOST_PATTERNS:
                if blocked in val_lower:
                    return False, f"SSRF Protection: MCP tool argument '{key}' attempted metadata access ({blocked})"

    return True, "Allowed"
