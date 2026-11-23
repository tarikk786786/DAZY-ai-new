"""Unit tests for DAZY language detection and Hinglish normalization."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.language_router import detect_language, normalize_hinglish


def test_detect_language():
    assert detect_language("Hello how are you doing today?") == "en"
    assert detect_language("Aap kaise ho, kya chal raha hai?") == "hi-en"
    assert detect_language("नमस्ते आप कैसे हैं") == "hi"
    assert detect_language("آپ کیسے ہیں؟") == "ur"
    assert detect_language("আপনি কেমন আছেন?") == "bn"


def test_normalize_hinglish_preserves_commands():
    raw = "DAZY plz open Chrome and VS Code, then check my battery status"
    norm = normalize_hinglish(raw)
    assert "please" in norm
    assert "Chrome" in norm
    assert "VS Code" in norm
    assert "battery" in norm


def test_normalize_hinglish_slang_and_repeats():
    raw = "Achhaaaaa masttt idea hai yrr thx"
    norm = normalize_hinglish(raw)
    assert "achha" in norm.lower()
    assert "mast" in norm.lower()
    assert "yaar" in norm.lower()
    assert "thanks" in norm.lower()
