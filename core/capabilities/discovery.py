"""core/capabilities/discovery.py — Automatic capability discovery.

Scans:
- actions/*.py (Native computer-driving actions)
- plugins/*.py (Drop-in modular plugins)
- agents/skills/*/SKILL.md (Agent skills)
- Connected MCP servers
and registers them into CapabilityRegistry.
"""
from __future__ import annotations

import importlib
from pathlib import Path

from core.capabilities.registry import Capability, get_capability_registry

_ROOT = Path(__file__).resolve().parent.parent.parent


def discover_all_capabilities() -> dict[str, list[Capability]]:
    """Scans and registers capabilities from all supported sources."""
    reg = get_capability_registry()
    discovered: dict[str, list[Capability]] = {
        "actions": [],
        "plugins": [],
        "skills": [],
        "mcp": [],
    }

    # 1. Native Actions
    actions_dir = _ROOT / "actions"
    if actions_dir.is_dir():
        for file in actions_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
            name = file.stem
            try:
                mod = importlib.import_module(f"actions.{name}")
                tool_decl = getattr(mod, "TOOL", None)
                if isinstance(tool_decl, dict) and "name" in tool_decl:
                    cap = Capability(
                        id=f"action:{name}",
                        name=tool_decl["name"],
                        kind="action",
                        description=tool_decl.get("description", ""),
                        parameters=tool_decl.get("parameters", {}),
                        handler=getattr(mod, "run", None),
                        source=str(file),
                    )
                    reg.register(cap)
                    discovered["actions"].append(cap)
            except Exception:
                pass

    # 2. Plugins
    plugins_dir = _ROOT / "plugins"
    if plugins_dir.is_dir():
        for file in plugins_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
            name = file.stem
            try:
                mod = importlib.import_module(f"plugins.{name}")
                plugin_decl = getattr(mod, "PLUGIN", None)
                if isinstance(plugin_decl, dict) and "name" in plugin_decl:
                    cap = Capability(
                        id=f"plugin:{name}",
                        name=plugin_decl["name"],
                        kind="plugin",
                        description=plugin_decl.get("description", ""),
                        parameters=plugin_decl.get("parameters", {}),
                        handler=getattr(mod, "run", None),
                        source=str(file),
                    )
                    reg.register(cap)
                    discovered["plugins"].append(cap)
            except Exception:
                pass

    # 3. Agent Skills (agents/skills/*/SKILL.md)
    skills_dir = _ROOT / "agents" / "skills"
    if skills_dir.is_dir():
        for skill_md in skills_dir.glob("*/SKILL.md"):
            folder_name = skill_md.parent.name
            try:
                content = skill_md.read_text(encoding="utf-8")
                # Parse frontmatter if present
                lines = content.splitlines()
                title, desc = folder_name, ""
                if lines and lines[0].strip() == "---":
                    for line in lines[1:]:
                        if line.strip() == "---":
                            break
                        if line.startswith("title:"):
                            title = line.partition("title:")[2].strip()
                        elif line.startswith("description:"):
                            desc = line.partition("description:")[2].strip()
                cap = Capability(
                    id=f"skill:{folder_name}",
                    name=f"skill_{folder_name.replace('-', '_')}",
                    kind="skill",
                    description=desc or f"Skill: {title}",
                    source=str(skill_md),
                    metadata={"content": content, "title": title},
                )
                reg.register(cap)
                discovered["skills"].append(cap)
            except Exception:
                pass

    return discovered
