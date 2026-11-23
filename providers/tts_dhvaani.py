"""providers/tts_dhvaani.py — DhVaani 0.5 (IISc / ARTPARK) Indian language TTS provider.

Secondary Indian voice engine for DAZY:
- 27 Indian languages (Hindi, Urdu, Bengali, Odia, Marathi, Telugu, Tamil, etc.)
- Reference voice conditioning for Indian female speaker identity
- Highly lightweight (~0.1B parameters, ~491 MB)
- Emits 24 kHz mono PCM audio stream.
"""
from __future__ import annotations

import asyncio
from importlib.util import find_spec
from typing import Any, AsyncIterator, Optional

from core.voice_style import format_for_dhvaani
from . import audio
from .base import DEFAULT_CAPS, Field

CHUNK_MS = 60
SPEAKER_RATE = audio.SPEAKER_RATE


class DhVaaniTTS:
    def __init__(self, cfg: dict):
        self.backend = (cfg.get("backend") or "api").strip().lower()
        self.model_name = (cfg.get("model") or "ARTPARK-IISc/DhVaani-0.5").strip()
        self.base_url = (cfg.get("base_url") or "").strip().rstrip("/")
        self.api_key = (cfg.get("api_key") or "").strip()
        self.language = (cfg.get("language") or "hi").strip()
        self.reference_speaker = (cfg.get("reference_speaker") or "dazy_original_female").strip()
        self.caps = dict(DEFAULT_CAPS)
        self.caps["audio_out"] = True

    async def speak(self, text: str, voice: str = "", language: str = "",
                    emotion: str = "", **kwargs) -> AsyncIterator[bytes]:
        """Synthesizes text in Indian languages into 24 kHz mono PCM audio stream."""
        if not text or not text.strip():
            return

        lang = language or self.language
        emo = emotion or "neutral"

        cond = format_for_dhvaani(text, language=lang, emotion=emo, reference_speaker=self.reference_speaker)

        if self.backend == "api" and self.base_url:
            async for chunk in self._speak_api(cond):
                yield chunk
        else:
            async for chunk in self._speak_local(cond):
                yield chunk

    async def _speak_api(self, cond: dict[str, Any]) -> AsyncIterator[bytes]:
        import httpx
        url = f"{self.base_url}/synthesize" if not self.base_url.endswith("/synthesize") else self.base_url
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        body = {
            "model": self.model_name,
            "text": cond["text"],
            "language": cond["language"],
            "reference_speaker": cond["reference_speaker"],
            "style": cond.get("style", "neutral"),
            "format": "wav"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code == 200:
                    raw_audio = resp.content
                    pcm = audio.wav_to_pcm(raw_audio, want_rate=SPEAKER_RATE) if raw_audio.startswith(b"RIFF") else audio.resample(raw_audio, 24000, SPEAKER_RATE)
                    chunk_bytes = int(SPEAKER_RATE * (CHUNK_MS / 1000.0) * audio.SAMPLE_WIDTH)
                    for i in range(0, len(pcm), chunk_bytes):
                        yield pcm[i : i + chunk_bytes]
                    return
        except Exception:
            pass

    async def _speak_local(self, cond: dict[str, Any]) -> AsyncIterator[bytes]:
        # Hook for local DhVaani ONNX or PyTorch weights
        pass


def _make(cfg: dict) -> DhVaaniTTS:
    return DhVaaniTTS(cfg)


PROVIDER = {
    "id": "dhvaani",
    "kind": "tts",
    "label": "DhVaani 0.5 (IISc / ARTPARK)",
    "hint": "27 Indian languages with reference voice conditioning (Hindi, Urdu, Bengali, Odia)",
    "requires": (),
    "install": "httpx",
    "catalog": (
        {
            "id": "dhvaani_indic",
            "label": "DhVaani Indic Voice",
            "note": "27 Indian languages · female reference conditioning",
            "local": False,
            "values": {
                "backend": "api",
                "model": "ARTPARK-IISc/DhVaani-0.5",
                "language": "hi",
                "reference_speaker": "dazy_original_female",
            },
        },
    ),
    "needs": (
        Field("backend", "Where it runs", kind="choice", choices=("api", "local"), default="api"),
        Field("model", "Model checkpoint", default="ARTPARK-IISc/DhVaani-0.5"),
        Field("language", "Default Language", kind="choice",
              choices=("hi", "ur", "bn", "or", "mr", "gu", "pa", "te", "ta", "kn", "ml"),
              default="hi"),
        Field("base_url", "API address", default="", required=False),
        Field("api_key", "API key", kind="secret", default="", required=False),
        Field("reference_speaker", "Reference Speaker", default="dazy_original_female"),
    ),
    "caps": {"audio_out": True},
    "factory": _make,
}


def available() -> bool:
    return find_spec("httpx") is not None
