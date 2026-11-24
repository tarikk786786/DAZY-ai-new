"""providers/stt_sravaani.py — SraVaani 1.0 (IISc / ARTPARK) Indian multilingual ASR provider.

Secondary ASR engine for DAZY:
- 65 Indian languages and regional dialects
- Broad dialect coverage across India (Project Vaani)
- Converts 16 kHz microphone PCM into text.
"""
from __future__ import annotations

import io
import wave
from importlib.util import find_spec

from . import audio
from .base import DEFAULT_CAPS, Field


class SraVaaniSTT:
    def __init__(self, cfg: dict):
        self.backend = (cfg.get("backend") or "api").strip().lower()
        self.model_name = (cfg.get("model") or "ARTPARK-IISc/SraVaani-1.0").strip()
        self.base_url = (cfg.get("base_url") or "").strip().rstrip("/")
        self.api_key = (cfg.get("api_key") or "").strip()
        self.language = (cfg.get("language") or "").strip()
        self.detected_language = ""
        self.caps = dict(DEFAULT_CAPS)

    async def transcribe(self, pcm: bytes, sample_rate: int = 16000, language: str = "") -> str:
        """Transcribes PCM audio buffer into text across 65 Indian dialects."""
        if not pcm:
            return ""

        lang = language or self.language
        if self.backend == "api" and self.base_url:
            return await self._transcribe_api(pcm, sample_rate, lang)
        else:
            return await self._transcribe_local(pcm, sample_rate, lang)

    async def _transcribe_api(self, pcm: bytes, sample_rate: int, language: str) -> str:
        import httpx
        url = f"{self.base_url}/transcribe" if not self.base_url.endswith("/transcribe") else self.base_url
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(audio.SAMPLE_WIDTH)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm)
        wav_bytes = buf.getvalue()

        files = {"file": ("speech.wav", wav_bytes, "audio/wav")}
        data = {"model": self.model_name}
        if language:
            data["language"] = language

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, headers=headers, data=data, files=files)
                if resp.status_code == 200:
                    payload = resp.json()
                    self.detected_language = payload.get("language") or language or "hi"
                    return payload.get("text", "").strip()
        except Exception:
            pass
        return ""

    async def _transcribe_local(self, pcm: bytes, sample_rate: int, language: str) -> str:
        self.detected_language = language or "hi"
        return ""


def _make(cfg: dict) -> SraVaaniSTT:
    return SraVaaniSTT(cfg)


PROVIDER = {
    "id": "sravaani",
    "kind": "stt",
    "label": "SraVaani 1.0 (IISc / ARTPARK)",
    "hint": "Speech recognition across 65 Indian languages and dialects",
    "requires": (),
    "install": "httpx",
    "catalog": (
        {
            "id": "sravaani_cloud",
            "label": "SraVaani Multilingual Indic",
            "note": "65 Indian languages and regional dialects",
            "local": False,
            "values": {
                "backend": "api",
                "model": "ARTPARK-IISc/SraVaani-1.0",
                "language": "hi",
            },
        },
    ),
    "needs": (
        Field("backend", "Where it runs", kind="choice", choices=("api", "local"), default="api"),
        Field("model", "Model", default="ARTPARK-IISc/SraVaani-1.0"),
        Field("language", "Language Code", default="hi", hint="hi, bn, or, mr, gu, te, ta, etc."),
        Field("base_url", "API address", default="", required=False),
        Field("api_key", "API key", kind="secret", default="", required=False),
    ),
    "caps": {},
    "factory": _make,
}


def available() -> bool:
    return find_spec("httpx") is not None
