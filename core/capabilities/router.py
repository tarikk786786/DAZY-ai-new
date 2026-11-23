"""core/capabilities/router.py — Capability and tool execution router."""
from __future__ import annotations

import inspect
from typing import Any, Optional

from core.capabilities.registry import Capability, get_capability_registry


def execute_capability(
    name: str,
    parameters: dict[str, Any],
    player: Any = None,
    session_memory: Any = None
) -> str:
    """Dispatches a tool call to the matching capability handler."""
    reg = get_capability_registry()
    cap = reg.get(name)

    if not cap:
        return f"Unknown tool or capability: {name}"

    if not cap.enabled:
        return f"Capability {name} is currently disabled"

    if not cap.handler or not callable(cap.handler):
        return f"Capability {name} has no executable handler"

    try:
        # Check signature for expected arguments
        sig = inspect.signature(cap.handler)
        kwargs = {}
        if "parameters" in sig.parameters:
            kwargs["parameters"] = parameters
        elif "params" in sig.parameters:
            kwargs["params"] = parameters
        else:
            kwargs = parameters

        if "player" in sig.parameters:
            kwargs["player"] = player
        if "session_memory" in sig.parameters:
            kwargs["session_memory"] = session_memory

        result = cap.handler(**kwargs)
        return str(result)
    except Exception as e:
        return f"Execution of {name} failed: {e}"
