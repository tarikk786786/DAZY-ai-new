"""Unit tests for DAZY persona engine and configuration."""
import os
import sys
from pathlib import Path

# Add Mark-LVII root to sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.dazy_persona import build_dazy_system_prompt, load_dazy_config, load_persona_guidelines
from memory.dazy_preferences import load_dazy_preferences, save_dazy_preferences, update_preference


def test_dazy_config_loads():
    cfg = load_dazy_config()
    assert isinstance(cfg, dict)
    assistant = cfg.get("assistant", {})
    assert assistant.get("name") == "DAZY"
    assert assistant.get("default_language") == "hinglish"
    assert assistant.get("voice", {}).get("primary_provider") in ("svara", "higgs")


def test_dazy_persona_markdown_loads():
    guidelines = load_persona_guidelines()
    assert "DAZY" in guidelines
    assert "Indian female" in guidelines or "Hinglish" in guidelines


def test_build_dazy_system_prompt():
    prompt = build_dazy_system_prompt(base_prompt="You are a helpful assistant.")
    assert "DAZY" in prompt
    assert "Hinglish" in prompt
    assert "VS Code open kar diya hai" in prompt


def test_dazy_preferences():
    prefs = load_dazy_preferences()
    assert isinstance(prefs, dict)
    assert "preferred_language" in prefs
    # Update temporary test pref
    update_preference("nickname", "Aarav")
    updated = load_dazy_preferences()
    assert updated.get("nickname") == "Aarav"

    prompt_with_pref = build_dazy_system_prompt("", user_preferences=updated)
    assert "Aarav" in prompt_with_pref
