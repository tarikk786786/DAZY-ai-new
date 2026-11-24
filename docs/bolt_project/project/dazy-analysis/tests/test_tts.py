"""Unit tests for DAZY expressive voice formatting and TTS providers."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.voice_style import (
    format_for_dhvaani,
    format_for_higgs,
    format_for_piper,
    format_for_svara,
)
from providers import registry


def test_svara_emotion_tagging():
    info = format_for_svara("Achha! Yeh toh bahut achhi news hai.", emotion="happy")
    assert "<happy>" in info["text"]
    assert info["emotion_tag"] == "happy"
    assert info["speaker"] == "female_01"


def test_svara_provider_registered():
    decl = registry.get_declaration("svara")
    assert decl is not None
    assert decl["kind"] == "tts"
    assert "Svara" in decl["label"]
    needs_keys = [f.key for f in decl.get("needs", ())]
    assert "backend" in needs_keys
    assert "device" in needs_keys
    assert "speaker" in needs_keys


def test_higgs_emotion_tagging():
    info = format_for_higgs("Main hamesha aapke saath hoon.", emotion="affection", intensity=0.75)
    assert "<emotion=affection intensity=0.75>" in info["text"]
    assert info["emotion"] == "affection"
    assert info["intensity"] == 0.75


def test_dhvaani_conditioning_formatting():
    info = format_for_dhvaani("Namaste, aapka swagat hai.", language="hi", emotion="happy")
    assert info["language"] == "hi"
    assert info["style"] == "happy"
    assert info["reference_speaker"] == "dazy_original_female"


def test_piper_fallback_prosody():
    info_fast = format_for_piper("Hurry up!", emotion="excited")
    info_slow = format_for_piper("Take your time.", emotion="sad")
    assert info_fast["length_scale"] < 1.0     # faster
    assert info_slow["length_scale"] > 1.0     # slower


def test_tts_providers_registered():
    tts_providers = registry.discover(kind="tts")
    ids = [p["id"] for p in tts_providers]
    assert "higgs" in ids
    assert "dhvaani" in ids
    assert "piper" in ids
