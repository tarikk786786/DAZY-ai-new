"""memory/dazy_preferences.py — User relationship and cultural preferences for DAZY.

Persists preferences like nicknames, honorifics, language mode, warmth bias,
and conversational history notes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parent.parent
_PREFS_FILE = _ROOT / "memory" / "dazy_preferences.json"

_DEFAULT_PREFS: dict[str, Any] = {
    "nickname": "",
    "preferred_language": "hinglish",
    "warmth_level": 0.85,
    "formality": 0.25,
    "cultural_notes": "Enjoys warm conversational rapport and witty banter; prefers technical terms in English.",
    "favorite_topics": [],
    "relationship_rapport_score": 0.5,
}


def load_dazy_preferences() -> dict[str, Any]:
    """Loads dazy_preferences.json, returning defaults if not found."""
    if _PREFS_FILE.is_file():
        try:
            with open(_PREFS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                res = dict(_DEFAULT_PREFS)
                res.update(data)
                return res
        except Exception:
            pass
    return dict(_DEFAULT_PREFS)


def save_dazy_preferences(prefs: dict[str, Any]) -> bool:
    """Saves updated preferences to memory/dazy_preferences.json."""
    try:
        _PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_PREFS_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def update_preference(key: str, value: Any) -> bool:
    """Updates a single preference entry."""
    prefs = load_dazy_preferences()
    prefs[key] = value
    return save_dazy_preferences(prefs)
