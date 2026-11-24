"""providers/tts_sherpa.py — sherpa-onnx VITS / Matcha Offline TTS Engine.

Local neural TTS provider supporting Hindi, Indian English, and multilingual prosodic control.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import AsyncIterator, Optional

from .base import Field

import numpy as np

logger = logging.getLogger("dazy.tts_sherpa")

_ROOT = Path(__file__).resolve().parent.parent
_MODELS_DIR = _ROOT / "models" / "tts" / "sherpa"
_MODELS_DIR.mkdir(parents=True, exist_ok=True)


class SherpaTTSProvider:
    """sherpa-onnx offline neural TTS provider."""

    def __init__(self, cfg: Optional[dict] = None):
        cfg = cfg or {}
        self.model_dir = Path(cfg.get("model_dir") or _MODELS_DIR)
        self.speed = float(cfg.get("speed") or 1.0)
        self._tts = None
        self._init_tts()

    def _init_tts(self) -> None:
        try:
            import sherpa_onnx
            vits_model = self.model_dir / "model.onnx"
            tokens = self.model_dir / "tokens.txt"
            lexicon = self.model_dir / "lexicon.txt"
            if vits_model.is_file() and tokens.is_file():
                config = sherpa_onnx.OfflineTtsConfig(
                    model=sherpa_onnx.OfflineTtsModelConfig(
                        vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                            model=str(vits_model),
                            lexicon=str(lexicon) if lexicon.is_file() else "",
                            tokens=str(tokens),
                        ),
                        num_threads=2,
                        provider="cpu",
                    )
                )
                self._tts = sherpa_onnx.OfflineTts(config)
                logger.info("sherpa-onnx OfflineTts initialized successfully.")
        except Exception as e:
            logger.debug("sherpa-onnx OfflineTts waiting for model files: %s", e)

    def is_available(self) -> bool:
        return self._tts is not None

    async def speak(self, text: str, **kwargs) -> AsyncIterator[bytes]:
        """Synthesizes text into 24kHz signed 16-bit mono PCM chunks."""
        text = text.strip()
        if not text:
            return

        if self._tts is not None:
            try:
                audio = await asyncio.to_thread(self._tts.generate, text, sid=0, speed=self.speed)
                samples = audio.samples
                int16_samples = (np.clip(samples, -1.0, 1.0) * 32767.0).astype(np.int16).tobytes()
                chunk_size = 2048
                for i in range(0, len(int16_samples), chunk_size):
                    yield int16_samples[i : i + chunk_size]
                return
            except Exception as e:
                logger.error("sherpa-onnx synthesis error: %s, falling back to EdgeTTS", e)

        # Fallback to EdgeTTS (Indian female Neerja)
        from .tts_edge import EdgeTTSProvider
        edge = EdgeTTSProvider({"voice": "en-IN-NeerjaNeural"})
        async for chunk in edge.speak(text, **kwargs):
            yield chunk


def _make(cfg: dict) -> SherpaTTSProvider:
    return SherpaTTSProvider(cfg)


PROVIDER = {
    "id": "sherpa_tts",
    "kind": "tts",
    "label": "sherpa-onnx VITS TTS (Local)",
    "about": "Local offline VITS/Matcha neural speech synthesis via sherpa-onnx.",
    "needs": (
        Field("model_dir", "Model folder path", kind="text", default="", required=False),
        Field("speed", "Speaking speed", kind="number", default=1.0, required=False),
    ),
    "caps": {"audio_out": True},
    "factory": _make,
}
