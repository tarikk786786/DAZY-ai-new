"""providers/tts_kokoro.py — Kokoro-82M ONNX High-Fidelity Neural Speech Synthesis.

Local neural TTS provider supporting feminine conversational speech with Hindi/Hinglish & Indian English prosody.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import AsyncIterator, Optional

from .base import Field

import numpy as np

logger = logging.getLogger("dazy.tts_kokoro")

_ROOT = Path(__file__).resolve().parent.parent
_MODELS_DIR = _ROOT / "models" / "tts"
_MODELS_DIR.mkdir(parents=True, exist_ok=True)


class KokoroTTSProvider:
    """Kokoro ONNX neural speech synthesizer."""

    def __init__(self, cfg: Optional[dict] = None):
        cfg = cfg or {}
        self.model_path = cfg.get("model_path") or str(_MODELS_DIR / "kokoro-v0_19.onnx")
        self.voices_path = cfg.get("voices_path") or str(_MODELS_DIR / "voices.json")
        self.voice = cfg.get("voice") or "af_heart"
        self.speed = float(cfg.get("speed") or 1.0)
        self.lang = cfg.get("lang") or "en-us"
        self._kokoro = None
        self._init_kokoro()

    def _init_kokoro(self) -> None:
        try:
            import kokoro_onnx
            if Path(self.model_path).is_file() and Path(self.voices_path).is_file():
                self._kokoro = kokoro_onnx.Kokoro(self.model_path, self.voices_path)
                logger.info("Kokoro ONNX initialized with voice: %s", self.voice)
        except Exception as e:
            logger.debug("Kokoro ONNX initialization waiting for model file: %s", e)

    def is_available(self) -> bool:
        return self._kokoro is not None

    async def speak(self, text: str, **kwargs) -> AsyncIterator[bytes]:
        """Synthesizes text into 24kHz signed 16-bit mono PCM chunks."""
        text = text.strip()
        if not text:
            return

        if self._kokoro is not None:
            try:
                # Kokoro returns samples at 24000 Hz float32
                samples, sr = await asyncio.to_thread(
                    self._kokoro.create, text, voice=self.voice, speed=self.speed, lang=self.lang
                )
                int16_samples = (np.clip(samples, -1.0, 1.0) * 32767.0).astype(np.int16).tobytes()
                # Yield in chunks of 2048 bytes
                chunk_size = 2048
                for i in range(0, len(int16_samples), chunk_size):
                    yield int16_samples[i : i + chunk_size]
                return
            except Exception as e:
                logger.error("Kokoro synthesis error: %s, falling back to EdgeTTS", e)

        # Fallback to EdgeTTS (Indian female Neerja)
        from .tts_edge import EdgeTTSProvider
        edge = EdgeTTSProvider({"voice": "en-IN-NeerjaNeural"})
        async for chunk in edge.speak(text, **kwargs):
            yield chunk


def _make(cfg: dict) -> KokoroTTSProvider:
    return KokoroTTSProvider(cfg)


PROVIDER = {
    "id": "kokoro",
    "kind": "tts",
    "label": "Kokoro Neural TTS (Local)",
    "about": "High-fidelity local neural speech synthesis with Kokoro-82M ONNX.",
    "needs": (
        Field("voice", "Voice", kind="text", default="af_heart", required=False),
        Field("speed", "Speaking speed", kind="number", default=1.0, required=False),
    ),
    "caps": {"audio_out": True},
    "factory": _make,
}
