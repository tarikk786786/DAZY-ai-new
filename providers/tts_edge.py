"""providers/tts_edge.py — Microsoft Edge TTS Provider for DAZY.

Provides ultra-realistic Indian female neural voices (Neerja / Swara / Ananya)
with zero cost, zero downloads, and sweet romantic tone.
"""
from __future__ import annotations

import asyncio
import io
import logging
from typing import AsyncIterator, Optional

import edge_tts
import miniaudio

from . import audio
from .base import Field

logger = logging.getLogger("dazy.tts_edge")

INDIAN_FEMALE_VOICES = (
    ("en-IN-NeerjaNeural", "Neerja (Indian English / Hinglish · Warm, Romantic Girlfriend)"),
    ("hi-IN-SwaraNeural", "Swara (Hindi / Hinglish · Melodic & Expressive)"),
    ("en-IN-AnanyaNeural", "Ananya (Indian English · Youthful & Cheerful)"),
    ("ur-PK-UzmaNeural", "Uzma (Urdu · Gentle & Poetic)"),
)

DEFAULT_FEMALE_VOICE = "en-IN-NeerjaNeural"


class EdgeTTSProvider:
    """Async streaming TTS provider using Microsoft Edge neural voices."""

    def __init__(self, cfg: dict):
        self.voice = cfg.get("voice") or DEFAULT_FEMALE_VOICE
        self.rate_offset = cfg.get("rate", 0)  # e.g. +0%, -5%
        self.pitch_offset = cfg.get("pitch", 0)

    async def speak(self, text: str, **kwargs) -> AsyncIterator[bytes]:
        """Synthesizes text into 24 kHz 16-bit mono PCM chunks."""
        clean_text = text.strip()
        if not clean_text:
            return

        rate_str = f"{self.rate_offset:+d}%" if self.rate_offset else "+0%"
        pitch_str = f"{self.pitch_offset:+d}Hz" if self.pitch_offset else "+0Hz"

        try:
            comm = edge_tts.Communicate(
                clean_text,
                voice=self.voice,
                rate=rate_str,
                pitch=pitch_str,
            )
            mp3_buf = bytearray()
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    mp3_buf.extend(chunk["data"])

            if not mp3_buf:
                return

            # Decode MP3 to 24 kHz signed 16-bit mono PCM
            decoded = miniaudio.decode(
                bytes(mp3_buf),
                output_format=miniaudio.SampleFormat.SIGNED16,
                nchannels=1,
                sample_rate=audio.SPEAKER_RATE,
            )
            pcm = bytes(decoded.samples)

            for piece in audio.chunk(pcm, ms=50, rate=audio.SPEAKER_RATE):
                yield piece

        except Exception as exc:
            logger.warning("EdgeTTS synthesis error: %s", exc)
            raise


def _make(cfg: dict) -> EdgeTTSProvider:
    return EdgeTTSProvider(cfg)


PROVIDER = {
    "id": "edge_tts",
    "kind": "tts",
    "label": "DAZY Edge Voice (Indian Female Neural)",
    "hint": "Sweet romantic Indian female neural voices · Free · High Fidelity",
    "requires": (),
    "catalog": (
        {
            "id": "edge_neerja",
            "label": "Neerja (Romantic Hinglish Girlfriend)",
            "note": "free · neural · Indian female voice",
            "values": {"voice": "en-IN-NeerjaNeural"},
        },
        {
            "id": "edge_swara",
            "label": "Swara (Hindi / Hinglish)",
            "note": "free · neural · Indian female voice",
            "values": {"voice": "hi-IN-SwaraNeural"},
        },
    ),
    "needs": (
        Field(
            "voice",
            "Voice",
            kind="choice",
            choices=tuple(k for k, _ in INDIAN_FEMALE_VOICES),
            default=DEFAULT_FEMALE_VOICE,
            required=True,
            hint="Choose DAZY's romantic Indian female neural voice",
        ),
        Field(
            "rate",
            "Speed adjustment (%)",
            kind="number",
            default=0,
            required=False,
            advanced=True,
            hint="Percentage adjustment to speaking speed (-20 to +20)",
        ),
        Field(
            "pitch",
            "Pitch adjustment (Hz)",
            kind="number",
            default=0,
            required=False,
            advanced=True,
            hint="Pitch offset (-50 to +50 Hz)",
        ),
    ),
    "caps": {"audio_out": True},
    "factory": _make,
}
