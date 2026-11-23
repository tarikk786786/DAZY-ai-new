"""core/capabilities/installer.py — Safe installer for skills and plugins."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parent.parent.parent


def install_skill(name: str, content: str) -> tuple[bool, str]:
    """Installs a new SKILL.md under agents/skills/<name>/SKILL.md."""
    if not name or not content:
        return False, "Skill name and content required"

    clean_name = name.strip().lower().replace(" ", "-")
    target_dir = _ROOT / "agents" / "skills" / clean_name
    target_file = target_dir / "SKILL.md"

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file.write_text(content, encoding="utf-8")
        return True, f"Skill installed at {target_file}"
    except Exception as e:
        return False, f"Failed to install skill: {e}"


def install_plugin(filename: str, source_code: str) -> tuple[bool, str]:
    """Installs a new drop-in plugin under plugins/<filename>.py."""
    if not filename.endswith(".py"):
        filename = f"{filename}.py"

    target_file = _ROOT / "plugins" / filename
    try:
        target_file.write_text(source_code, encoding="utf-8")
        return True, f"Plugin installed at {target_file}"
    except Exception as e:
        return False, f"Failed to install plugin: {e}"
