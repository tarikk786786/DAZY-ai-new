"""Unit tests for DAZY Indian speech recognition (ASR) providers."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from providers import registry


def test_asr_providers_registered():
    stt_providers = registry.discover(kind="stt")
    ids = [p["id"] for p in stt_providers]
    assert "shrutam2" in ids
    assert "sravaani" in ids
    assert "whisper" in ids


def test_shrutam2_provider_fields():
    decl = registry.get_declaration("shrutam2")
    assert decl is not None
    assert decl["kind"] == "stt"
    assert "BharatGen" in decl["label"] or "shrutam2" in decl["id"]
    needs_keys = [f.key for f in decl.get("needs", ())]
    assert "backend" in needs_keys
    assert "model" in needs_keys


def test_sravaani_provider_fields():
    decl = registry.get_declaration("sravaani")
    assert decl is not None
    assert decl["kind"] == "stt"
    needs_keys = [f.key for f in decl.get("needs", ())]
    assert "language" in needs_keys
