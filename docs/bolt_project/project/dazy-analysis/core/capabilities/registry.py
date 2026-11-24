"""core/capabilities/registry.py — Unified capability registry for DAZY.

Consolidates:
1. Native Actions (actions/*.py)
2. Drop-in Plugins (plugins/*.py)
3. Agent Skills (agents/skills/*)
4. Connected MCP Tools (core/mcp/*)
into a unified lookup, routing, and declaration registry.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class Capability:
    id: str
    name: str
    kind: str             # "action" | "plugin" | "skill" | "mcp"
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable] = None
    source: str = ""
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class CapabilityRegistry:
    def __init__(self):
        self._capabilities: dict[str, Capability] = {}

    def register(self, cap: Capability) -> None:
        self._capabilities[cap.name] = cap

    def unregister(self, name: str) -> None:
        self._capabilities.pop(name, None)

    def get(self, name: str) -> Optional[Capability]:
        return self._capabilities.get(name)

    def list_all(self, kind: Optional[str] = None) -> list[Capability]:
        if kind:
            return [c for c in self._capabilities.values() if c.kind == kind and c.enabled]
        return [c for c in self._capabilities.values() if c.enabled]

    def export_tool_declarations(self) -> list[dict[str, Any]]:
        """Exports capabilities in Gemini/OpenAI tool declaration format."""
        decls = []
        for c in self.list_all():
            decls.append({
                "name": c.name,
                "description": c.description,
                "parameters": c.parameters or {"type": "OBJECT", "properties": {}},
            })
        return decls


_GLOBAL_REGISTRY: Optional[CapabilityRegistry] = None


def get_capability_registry() -> CapabilityRegistry:
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = CapabilityRegistry()
    return _GLOBAL_REGISTRY
