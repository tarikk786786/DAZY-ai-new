"""core/voice_style.py — Voice style and emotion adapter for TTS backends.

Converts structured emotional states and deliveries into concrete parameters
for Higgs TTS 3, DhVaani 0.5, Piper, and System TTS.
"""
from __future__ import annotations

from typing import Any, Optional

# Mapping DAZY standard emotions to Higgs TTS 3 emotion labels
# Higgs supports: affection, contentment, amusement, relief, sadness, enthusiasm, contemplation
HIGGS_EMOTION_MAP: dict[str, str] = {
    "neutral": "contentment",
    "affection": "affection",
    "happy": "contentment",
    "playful": "amusement",
    "empathetic": "relief",
    "curious": "contemplation",
    "excited": "enthusiasm",
    "sad": "sadness",
    "serious": "contemplation",
    "confident": "contentment",
}

# Mapping DAZY emotions to DhVaani reference voice styles
DHVAANI_STYLE_MAP: dict[str, str] = {
    "neutral": "neutral",
    "affection": "warm",
    "happy": "happy",
    "playful": "playful",
    "empathetic": "empathetic",
    "curious": "warm",
    "excited": "excited",
    "sad": "empathetic",
    "serious": "serious",
    "confident": "neutral",
}


# Mapping DAZY emotions to Svara TTS v1 emotion tags
# Svara documents emotion tags: <happy>, <sad>, <anger>, <fear>
SVARA_EMOTION_MAP: dict[str, Optional[str]] = {
    "neutral": None,
    "happy": "happy",
    "excited": "happy",
    "playful": "happy",
    "affection": None,      # warm natural prosody
    "empathetic": "sad",     # soft gentle delivery
    "sad": "sad",
    "curious": None,
    "serious": None,
    "confident": None,
}


def format_for_svara(
    text: str,
    emotion: str = "neutral",
    speaker: str = "female_01",
    language: str = "hi-en"
) -> dict[str, Any]:
    """Formats text with Svara TTS v1 emotion tags and speaker configuration.

    Example output: 'Achha! Yeh toh bahut achhi news hai. <happy>'
    """
    clean_text = text.strip()
    emo_tag = SVARA_EMOTION_MAP.get(emotion.lower())
    
    if emo_tag:
        tagged_text = f"{clean_text} <{emo_tag}>"
    else:
        tagged_text = clean_text

    return {
        "text": tagged_text,
        "raw_text": clean_text,
        "emotion_tag": emo_tag,
        "speaker": speaker,
        "language": language,
        "sample_rate": 24000,
    }


def format_for_higgs(
    text: str,
    emotion: str = "neutral",
    intensity: float = 0.5,
    delivery: str = "conversational"
) -> dict[str, Any]:
    """Prepares payload and inline emotion tags for Higgs TTS 3.

    Higgs supports inline tags and prompt instructions:
    <emotion=affection intensity=0.8> ... </emotion>
    """
    higgs_emo = HIGGS_EMOTION_MAP.get(emotion.lower(), "contentment")
    clamped_intensity = max(0.1, min(1.0, round(intensity, 2)))
    
    # Tagged text formatting for expressive rendering
    tagged_text = f"<emotion={higgs_emo} intensity={clamped_intensity}> {text.strip()} </emotion>"
    
    return {
        "text": tagged_text,
        "raw_text": text,
        "emotion": higgs_emo,
        "intensity": clamped_intensity,
        "delivery": delivery,
        "speaking_rate": 1.05 if higgs_emo == "enthusiasm" else (0.95 if higgs_emo in ("sadness", "relief") else 1.0),
    }


def format_for_dhvaani(
    text: str,
    language: str = "hi",
    emotion: str = "neutral",
    reference_speaker: str = "dazy_original_female"
) -> dict[str, Any]:
    """Prepares conditioning options for DhVaani 0.5 Indic voice synthesis."""
    style = DHVAANI_STYLE_MAP.get(emotion.lower(), "neutral")
    return {
        "text": text,
        "language": language,
        "style": style,
        "reference_speaker": reference_speaker,
        "speed": 1.0,
    }


def format_for_piper(
    text: str,
    emotion: str = "neutral",
    intensity: float = 0.5
) -> dict[str, Any]:
    """Maps emotion to Piper lightweight synthesis adjustments (length_scale, noise_scale)."""
    # Piper uses length_scale for speech speed (lower = faster)
    emo = emotion.lower()
    if emo in ("excited", "happy"):
        length_scale = 0.92
        noise_scale = 0.75
    elif emo in ("sad", "empathetic"):
        length_scale = 1.10
        noise_scale = 0.55
    elif emo == "serious":
        length_scale = 1.0
        noise_scale = 0.60
    else:
        length_scale = 1.0
        noise_scale = 0.667

    return {
        "text": text,
        "length_scale": length_scale,
        "noise_scale": noise_scale,
        "noise_w": 0.8,
    }
