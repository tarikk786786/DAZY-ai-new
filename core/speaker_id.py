"""core/speaker_id.py — Dual-Speaker Diarization, Voice Enrollment & Identity Attribution for DAZY.

Features:
- Two Distinct Human Speakers:
  - Speaker A: Primary User / Owner (Tarik) with full administrative permissions.
  - Speaker B: Secondary Enrolled User (Companion / Guest) with tailored permissions.
- Rejection of Unknown Speakers: Unregistered voices or voices below threshold are marked "unknown".
- Assistant Echo Disqualification: Synthetic speech fingerprints are marked "assistant_echo" and never attributed to humans.
- Immutable Assistant Voice: Speaker identity never mutates the assistant's authoritative feminine voice.
- Multi-vector voice enrollment profiles: Normal, quiet, and varying speech velocities.
- Secure local JSON storage in memory/voice_profiles/enrolled_speakers.json.
"""
from __future__ import annotations

import collections
import hashlib
import json
import logging
import math
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("dazy.speaker_id")

_BASE_DIR = Path(__file__).resolve().parent.parent
_VOICE_PROFILES_DIR = _BASE_DIR / "memory" / "voice_profiles"
_VOICE_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
_PROFILES_FILE = _VOICE_PROFILES_DIR / "enrolled_speakers.json"

# Fixed authoritative voice for DAZY
AUTHORITATIVE_FEMININE_VOICE = "en-IN-NeerjaNeural"


class SpeakerIdentifier:
    """Extracts speaker embeddings and verifies speaker identity with confidence scoring."""

    def __init__(self, threshold: float = 0.65):
        self.threshold = threshold
        # Structure: { speaker_name: { "role": str, "permissions": dict, "embeddings": list[list[float]] } }
        self._profiles: Dict[str, Dict[str, Any]] = {}
        self._assistant_echo_fingerprints: collections.deque = collections.deque(maxlen=20)
        self._sherpa_extractor = None
        self._sherpa_manager = None
        self._active_backend = "feature_embedding"

        self._load_profiles()
        self._init_models()

    def _init_models(self) -> None:
        """Initializes sherpa-onnx SpeakerEmbeddingExtractor or fallback."""
        try:
            import sherpa_onnx
            model_path = _VOICE_PROFILES_DIR / "3dspeaker_speech_campplus_sv_zh_en_16k-common.onnx"
            if model_path.is_file():
                cfg = sherpa_onnx.SpeakerEmbeddingExtractorConfig(
                    model=str(model_path),
                    num_threads=2,
                    provider="cpu",
                )
                self._sherpa_extractor = sherpa_onnx.SpeakerEmbeddingExtractor(cfg)
                self._sherpa_manager = sherpa_onnx.SpeakerEmbeddingManager(self._sherpa_extractor.dim)
                self._active_backend = "sherpa-onnx"
                logger.info("sherpa-onnx SpeakerEmbeddingExtractor initialized.")
                return
        except Exception as e:
            logger.debug("sherpa-onnx speaker extraction not loaded: %s", e)

        self._active_backend = "mfcc_spectral_embedding"
        logger.info("SpeakerIdentifier initialized with calibrated acoustic spectral embeddings.")

    def _load_profiles(self) -> None:
        """Loads enrolled speaker vectors from secure local storage."""
        if _PROFILES_FILE.is_file():
            try:
                with open(_PROFILES_FILE, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    # Migrate legacy format if needed
                    for k, v in raw.items():
                        if isinstance(v, list):
                            # Legacy format: list of vectors
                            role = "owner" if k.lower() in ("tarik", "owner") else "companion"
                            self._profiles[k] = {
                                "role": role,
                                "permissions": {
                                    "execute_system_commands": role == "owner",
                                    "access_private_memory": role == "owner",
                                    "modify_settings": role == "owner",
                                },
                                "embeddings": v,
                            }
                        elif isinstance(v, dict):
                            self._profiles[k] = v
            except Exception as e:
                logger.error("Failed to load voice profiles: %s", e)
                self._profiles = {}

    def _save_profiles(self) -> None:
        """Saves enrolled speaker vectors to secure local storage."""
        try:
            with open(_PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(self._profiles, f, indent=2)
        except Exception as e:
            logger.error("Failed to save voice profiles: %s", e)

    def extract_embedding(self, pcm_16k: bytes | np.ndarray) -> np.ndarray:
        """Extracts a normalized 64-dim speaker embedding vector from 16kHz audio."""
        if isinstance(pcm_16k, bytes):
            samples = np.frombuffer(pcm_16k, dtype=np.int16).astype(np.float32) / 32768.0
        else:
            samples = pcm_16k.astype(np.float32)
            if np.max(np.abs(samples)) > 1.0:
                samples = samples / 32768.0

        if len(samples) < 512:  # Need at least one 512-sample FFT window
            return np.zeros(64, dtype=np.float32)

        if self._sherpa_extractor is not None:
            try:
                stream = self._sherpa_extractor.create_stream()
                stream.accept_waveform(16000, samples)
                stream.input_finished()
                emb = self._sherpa_extractor.compute(stream)
                norm = np.linalg.norm(emb)
                return (emb / (norm + 1e-6)).astype(np.float32)
            except Exception:
                pass

        # Robust MFCC/Filterbank 64-dim spectral embedding fallback
        n_fft = 512
        hop = 256
        n_frames = max(1, (len(samples) - n_fft) // hop)
        features = []
        for i in range(min(n_frames, 32)):
            frame = samples[i * hop : i * hop + n_fft] * np.hanning(n_fft)
            mag = np.abs(np.fft.rfft(frame))
            indices = np.linspace(1, len(mag) - 1, 64, dtype=int)
            features.append(mag[indices])

        if features:
            avg_feat = np.mean(features, axis=0)
            norm = np.linalg.norm(avg_feat)
            return (avg_feat / (norm + 1e-6)).astype(np.float32)

        return np.zeros(64, dtype=np.float32)

    def register_assistant_playback(self, pcm_16k: bytes | np.ndarray) -> None:
        """Registers assistant synthesized speech chunks to disqualify them from human speaker attribution."""
        emb = self.extract_embedding(pcm_16k)
        if not np.all(emb == 0):
            self._assistant_echo_fingerprints.append(emb)

    def is_assistant_speech(self, pcm_chunk: bytes | np.ndarray, similarity_threshold: float = 0.85) -> bool:
        """Checks if the microphone input matches recent assistant synthesized speech."""
        curr_emb = self.extract_embedding(pcm_chunk)
        if np.all(curr_emb == 0):
            return False

        for ref_emb in self._assistant_echo_fingerprints:
            sim = float(np.dot(curr_emb, ref_emb) / (np.linalg.norm(curr_emb) * np.linalg.norm(ref_emb) + 1e-6))
            if sim >= similarity_threshold:
                return True
        return False

    def enroll_voice_sample(
        self,
        speaker_name: str,
        pcm_sample: bytes | np.ndarray,
        role: str = "companion",
        permissions: Optional[Dict[str, bool]] = None,
    ) -> bool:
        """Enrolls a voice sample for a distinct speaker (Speaker A or Speaker B)."""
        emb = self.extract_embedding(pcm_sample)
        if np.all(emb == 0):
            return False

        if speaker_name not in self._profiles:
            # Auto-determine role for owner
            if speaker_name.lower() in ("tarik", "owner"):
                role = "owner"
                perm = {
                    "execute_system_commands": True,
                    "access_private_memory": True,
                    "modify_settings": True,
                }
            else:
                perm = permissions or {
                    "execute_system_commands": True,
                    "access_private_memory": False,
                    "modify_settings": False,
                }
            self._profiles[speaker_name] = {
                "role": role,
                "permissions": perm,
                "embeddings": [],
            }

        self._profiles[speaker_name]["embeddings"].append(emb.tolist())
        self._save_profiles()
        logger.info("Enrolled new voice sample for %s (role: %s, total samples: %d)",
                    speaker_name, role, len(self._profiles[speaker_name]["embeddings"]))
        return True

    def delete_speaker(self, speaker_name: str) -> bool:
        """Deletes an enrolled speaker profile."""
        if speaker_name in self._profiles:
            del self._profiles[speaker_name]
            self._save_profiles()
            return True
        return False

    def get_speaker_profile(self, speaker_name: str) -> Optional[Dict[str, Any]]:
        """Returns metadata and permissions for a registered speaker."""
        return self._profiles.get(speaker_name)

    def list_enrolled_speakers(self) -> List[dict]:
        """Lists all enrolled speakers and their sample counts."""
        return [
            {
                "name": name,
                "role": data.get("role", "companion"),
                "sample_count": len(data.get("embeddings", [])),
                "permissions": data.get("permissions", {}),
            }
            for name, data in self._profiles.items()
        ]

    def identify_speaker(self, pcm_chunk: bytes | np.ndarray) -> Tuple[str, float, bool]:
        """Identifies who is speaking in the audio chunk.
        
        Returns:
            speaker_name (str): Enrolled name or "unknown"
            confidence (float): Match score (0.0 to 1.0)
            is_verified (bool): True if confidence >= threshold
        """
        # Step 1: Disqualify assistant's own synthesized echo
        if self.is_assistant_speech(pcm_chunk):
            logger.debug("Disqualified audio: Matches assistant synthesized speech echo.")
            return "assistant_echo", 0.0, False

        curr_emb = self.extract_embedding(pcm_chunk)
        if np.all(curr_emb == 0):
            return "unknown", 0.0, False

        if not self._profiles:
            return "unknown", 0.0, False

        best_speaker = "unknown"
        best_score = 0.0

        for name, pdata in self._profiles.items():
            enrolled_list = pdata.get("embeddings", [])
            for ref_vec in enrolled_list:
                ref_arr = np.array(ref_vec, dtype=np.float32)
                sim = float(np.dot(curr_emb, ref_arr) / (np.linalg.norm(curr_emb) * np.linalg.norm(ref_arr) + 1e-6))
                if sim > best_score:
                    best_score = sim
                    best_speaker = name

        is_verified = best_score >= self.threshold
        if not is_verified:
            best_speaker = "unknown"

        return best_speaker, round(best_score, 3), is_verified

    def get_authoritative_assistant_voice(self) -> str:
        """Guarantees the assistant speaks with one consistent feminine Indian voice."""
        return AUTHORITATIVE_FEMININE_VOICE

    def is_addressing_assistant(
        self,
        transcript: str,
        speaker: str,
        is_wake_activated: bool,
        seconds_since_last_turn: float,
        followup_window_sec: float = 20.0,
    ) -> bool:
        """Determines if the spoken message was genuinely directed to DAZY."""
        # Never address assistant if marked as echo
        if speaker == "assistant_echo":
            return False

        # Rule 1: Explicit wake word activation always addresses assistant
        if is_wake_activated:
            return True

        # Rule 2: Active conversational follow-up window (<20s) from verified speaker
        if seconds_since_last_turn <= followup_window_sec and speaker != "unknown":
            return True

        # Rule 3: Name or assistant call-out in text
        t_lower = transcript.lower()
        if any(w in t_lower for w in ["dazy", "dazzy", "daisy", "daji"]):
            return True

        # Rule 4: Direct conversational inquiry intended for assistant
        if any(t_lower.startswith(p) for p in ["kya aap", "can you", "please", "batao", "suno", "open", "check"]):
            if seconds_since_last_turn <= followup_window_sec * 1.5:
                return True

        return False
