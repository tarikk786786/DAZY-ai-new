"""core/voice_session_manager.py — Singleton Voice Session Manager & Atomic Audio Controller for DAZY.

Enforces:
1. Singleton audio architecture: Exactly ONE microphone capture stream and ONE playback session.
2. Atomic TTS transactions: Every vocal response has a unique turn_id and playback_id.
3. Single voice guarantee: Atomic fallback switching between primary and secondary TTS engines without dual-playback or overlap.
4. Anti-replay & Anti-looping: Suppresses duplicate transcript/response events within time windows.
5. Startup silence protection: Assistant never speaks on application startup without user initiation.
6. Auto-Speak Modes: SILENT, WAKE_ONLY, CONTINUOUS, PUSH_TO_TALK.
7. Half-duplex & AEC feedback protection: Prevents assistant from hearing or transcribing its own synthesized voice.
"""
from __future__ import annotations

import asyncio
import enum
import hashlib
import logging
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Set

import numpy as np

logger = logging.getLogger("dazy.voice_session_manager")


class AutoSpeakMode(enum.Enum):
    SILENT = "SILENT"                 # Never speaks aloud (text only)
    WAKE_ONLY = "WAKE_ONLY"           # Only speaks if wake word or follow-up is active
    CONTINUOUS = "CONTINUOUS"         # Speaks after every verified user utterance
    PUSH_TO_TALK = "PUSH_TO_TALK"     # Speaks only when push-to-talk was used


class AtomicTTSPlayer:
    """Manages atomic audio playback ensuring zero overlap and instant cancellation."""

    def __init__(self):
        self._lock = threading.RLock()
        self.is_playing: bool = False
        self.current_turn_id: Optional[str] = None
        self.current_playback_id: Optional[str] = None
        self.current_provider: Optional[str] = None
        self._interrupted_turn_ids: Set[str] = set()
        self.playback_queue: list = []
        self.duplicate_event_count: int = 0
        self.cancellation_count: int = 0
        self._stop_callbacks: List[Callable[[], None]] = []

    def register_stop_callback(self, cb: Callable[[], None]) -> None:
        with self._lock:
            self._stop_callbacks.append(cb)

    def start_playback_transaction(self, turn_id: str, provider: str) -> str:
        """Starts a new atomic playback transaction, cancelling any previous playback."""
        with self._lock:
            if self.is_playing:
                logger.info("AtomicTTSPlayer: Preempting existing playback for turn %s", self.current_turn_id)
                self.cancel_current("preempted_by_new_turn")

            playback_id = str(uuid.uuid4())[:8]
            self.current_turn_id = turn_id
            self.current_playback_id = playback_id
            self.current_provider = provider
            self.is_playing = True
            logger.info("AtomicTTSPlayer: Started transaction turn_id=%s, playback_id=%s, provider=%s",
                        turn_id, playback_id, provider)
            return playback_id

    def cancel_current(self, reason: str = "cancelled", cancel_turn: bool = True) -> None:
        """Immediately halts any in-progress playback and purges queued chunks."""
        with self._lock:
            if not self.is_playing and not self.current_playback_id:
                return

            cancelled_turn = self.current_turn_id
            if cancel_turn and cancelled_turn:
                self._interrupted_turn_ids.add(cancelled_turn)

            logger.info("AtomicTTSPlayer: Cancelling playback (turn=%s, reason=%s)", cancelled_turn, reason)
            self.is_playing = False
            self.current_turn_id = None
            self.current_playback_id = None
            self.current_provider = None
            self.playback_queue.clear()
            self.cancellation_count += 1

            # Stop sounddevice immediately if active
            try:
                import sounddevice as sd
                sd.stop()
            except Exception:
                pass

            for cb in self._stop_callbacks:
                try:
                    cb()
                except Exception as e:
                    logger.debug("Error in stop callback: %s", e)

    def is_turn_cancelled(self, turn_id: str) -> bool:
        with self._lock:
            return turn_id in self._interrupted_turn_ids

    def finish_playback_transaction(self, playback_id: Optional[str] = None) -> None:
        with self._lock:
            if playback_id is None or self.current_playback_id == playback_id:
                logger.info("AtomicTTSPlayer: Finished transaction playback_id=%s", playback_id or self.current_playback_id)
                self.is_playing = False
                self.current_playback_id = None
                self.current_turn_id = None
                self.current_provider = None


class VoiceSessionManager:
    """Thread-safe and async-safe Singleton orchestrating the entire audio lifecycle."""

    _instance: Optional["VoiceSessionManager"] = None
    _singleton_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "VoiceSessionManager":
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """For unit testing purposes."""
        with cls._singleton_lock:
            if cls._instance is not None:
                cls._instance.shutdown()
                cls._instance = None

    def __init__(self):
        if VoiceSessionManager._instance is not None:
            raise RuntimeError("VoiceSessionManager is a singleton. Use VoiceSessionManager.get_instance().")

        self.player = AtomicTTSPlayer()
        self._lock = threading.RLock()

        # Session state
        self.active_turn_id: Optional[str] = None
        self.active_mic_stream: Optional[Any] = None
        self.active_vad_instance: Optional[Any] = None
        self.active_speaker_name: str = "unknown"
        self.active_speaker_confidence: float = 0.0

        # Auto-speak and Startup safety
        self.auto_speak_mode: AutoSpeakMode = AutoSpeakMode.WAKE_ONLY
        self.startup_silence_guard: bool = True  # Must stay True until user explicitly interacts
        self.authoritative_voice: str = "en-IN-NeerjaNeural"  # Default feminine Indian voice

        # Self-listening and Echo tail protection
        self.tail_margin_sec: float = 0.35
        self.reported_output_latency_sec: float = 0.20
        self._tail_until: float = 0.0

        # Deduplication memory (hashes with timestamps)
        self._recent_transcripts: Dict[str, float] = {}   # hash -> timestamp
        self._recent_responses: Dict[str, float] = {}     # hash -> timestamp
        self._dedup_window_sec: float = 30.0

        # Diagnostics counters
        self.total_turns_started: int = 0
        self.duplicate_transcripts_dropped: int = 0
        self.duplicate_responses_dropped: int = 0
        self.self_echo_frames_suppressed: int = 0
        self.active_mic_sessions_count: int = 0
        self.active_tts_sessions_count: int = 0

        # Structured audio diagnostic counters
        self.is_mic_open: bool = False
        self.frames_captured: int = 0
        self.frames_queued: int = 0
        self.frames_dropped_overflow: int = 0
        self.audio_status_warnings: int = 0
        self.last_audio_warning: str = ""
        self.input_callbacks_count: int = 0
        self.frames_captured_count: int = 0
        self.frames_processed_count: int = 0
        self.bytes_queued_count: int = 0
        self.bytes_sent_to_ai_count: int = 0
        self.transcripts_received_count: int = 0
        self.responses_received_count: int = 0

    def record_input_callback(self, frames: int = 1024) -> None:
        with self._lock:
            self.input_callbacks_count += 1
            self.frames_captured_count += frames

    def record_frame_processed(self) -> None:
        with self._lock:
            self.frames_processed_count += 1

    def record_bytes_queued(self, nbytes: int) -> None:
        with self._lock:
            self.bytes_queued_count += nbytes

    def record_bytes_sent_to_ai(self, nbytes: int) -> None:
        with self._lock:
            self.bytes_sent_to_ai_count += nbytes

    def record_transcript_received(self) -> None:
        with self._lock:
            self.transcripts_received_count += 1

    def record_response_received(self) -> None:
        with self._lock:
            self.responses_received_count += 1
        self.frames_captured: int = 0
        self.frames_queued: int = 0
        self.frames_dropped_overflow: int = 0
        self.audio_status_warnings: int = 0
        self.last_audio_warning: str = ""
        self.is_mic_open: bool = False

    def set_auto_speak_mode(self, mode: AutoSpeakMode | str) -> None:
        if isinstance(mode, str):
            val = mode.strip().upper()
            aliases = {
                "AUTO": AutoSpeakMode.CONTINUOUS,
                "CONTINUOUS": AutoSpeakMode.CONTINUOUS,
                "ALWAYS": AutoSpeakMode.CONTINUOUS,
                "WAKE": AutoSpeakMode.WAKE_ONLY,
                "WAKE_ONLY": AutoSpeakMode.WAKE_ONLY,
                "SILENT": AutoSpeakMode.SILENT,
                "MUTE": AutoSpeakMode.SILENT,
                "MUTED": AutoSpeakMode.SILENT,
                "PUSH_TO_TALK": AutoSpeakMode.PUSH_TO_TALK,
                "PTT": AutoSpeakMode.PUSH_TO_TALK,
            }
            mode = aliases.get(val, AutoSpeakMode.WAKE_ONLY)
        with self._lock:
            self.auto_speak_mode = mode
            logger.info("VoiceSessionManager: AutoSpeakMode set to %s", mode.value)

    def clear_startup_guard(self) -> None:
        """User or explicit wake word has initiated first contact."""
        with self._lock:
            if self.startup_silence_guard:
                self.startup_silence_guard = False
                logger.info("VoiceSessionManager: Startup silence guard cleared.")

    def new_turn(self, speaker_name: str = "unknown", confidence: float = 0.0) -> str:
        """Begins a new turn session with unique turn_id and resets turn-level states."""
        with self._lock:
            self.clear_startup_guard()
            self.active_turn_id = str(uuid.uuid4())
            self.active_speaker_name = speaker_name
            self.active_speaker_confidence = confidence
            self.total_turns_started += 1
            logger.info("VoiceSessionManager: New turn started turn_id=%s, speaker=%s (%.2f)",
                        self.active_turn_id, speaker_name, confidence)
            return self.active_turn_id

    # ── Self-Listening & Echo Tail Management ──────────────────────────────

    def mark_speaking_started(self) -> None:
        with self._lock:
            self.active_tts_sessions_count = 1
            self._tail_until = 0.0

    def mark_speaking_ended(self) -> None:
        with self._lock:
            self.active_tts_sessions_count = 0
            self._tail_until = time.monotonic() + self.reported_output_latency_sec + self.tail_margin_sec

    def is_assistant_speaking_or_echo(self) -> bool:
        """Returns True if the assistant is playing audio OR in the acoustic echo decay tail."""
        with self._lock:
            if self.player.is_playing or self.active_tts_sessions_count > 0:
                return True
            return time.monotonic() < self._tail_until

    def should_suppress_mic_input(self, pcm_data: bytes | np.ndarray) -> bool:
        """Half-duplex acoustic protection: blocks mic input during assistant speech unless barge-in."""
        if not self.is_assistant_speaking_or_echo():
            return False

        # Assistant is currently speaking or in reverberation tail
        self.self_echo_frames_suppressed += 1
        return True

    # ── Deduplication & Replay Guards ──────────────────────────────────────

    def is_duplicate_transcript(self, transcript: str) -> bool:
        """Suppresses exact same transcript emitted multiple times within the dedup window."""
        clean = transcript.strip().lower()
        if not clean:
            return True

        h = hashlib.sha256(clean.encode("utf-8")).hexdigest()
        now = time.monotonic()

        with self._lock:
            # Purge expired
            expired = [k for k, t in self._recent_transcripts.items() if now - t > self._dedup_window_sec]
            for k in expired:
                del self._recent_transcripts[k]

            if h in self._recent_transcripts:
                self.duplicate_transcripts_dropped += 1
                logger.warning("VoiceSessionManager: Dropping duplicate transcript: '%s'", clean)
                return True

            self._recent_transcripts[h] = now
            return False

    def is_duplicate_response(self, text: str) -> bool:
        """Prevents re-speaking the exact same response within the dedup window."""
        clean = text.strip().lower()
        if not clean:
            return True

        h = hashlib.sha256(clean.encode("utf-8")).hexdigest()
        now = time.monotonic()

        with self._lock:
            expired = [k for k, t in self._recent_responses.items() if now - t > self._dedup_window_sec]
            for k in expired:
                del self._recent_responses[k]

            if h in self._recent_responses:
                self.duplicate_responses_dropped += 1
                logger.warning("VoiceSessionManager: Dropping duplicate response to prevent replay: '%s'", clean)
                return True

            self._recent_responses[h] = now
            return False

    def record_response(self, text: str) -> None:
        """Explicitly records a response in the deduplication history."""
        clean = text.strip().lower()
        if not clean:
            return
        h = hashlib.sha256(clean.encode("utf-8")).hexdigest()
        now = time.monotonic()
        with self._lock:
            self._recent_responses[h] = now

    def can_auto_speak(self, is_wake_triggered: bool = False, is_follow_up: bool = False) -> bool:
        """Validates if speaking aloud is permitted under the current mode and state."""
        with self._lock:
            if self.startup_silence_guard:
                logger.info("VoiceSessionManager: Blocked speech due to startup_silence_guard.")
                return False

            if self.auto_speak_mode == AutoSpeakMode.SILENT:
                return False

            if self.auto_speak_mode == AutoSpeakMode.WAKE_ONLY:
                return is_wake_triggered or is_follow_up

            if self.auto_speak_mode == AutoSpeakMode.CONTINUOUS:
                return True

            if self.auto_speak_mode == AutoSpeakMode.PUSH_TO_TALK:
                return True

            return False

    # ── Single Microphone Stream Ownership ──────────────────────────────────

    def register_mic_stream(self, stream_obj: Any) -> bool:
        with self._lock:
            if self.active_mic_stream is not None and self.active_mic_stream != stream_obj:
                logger.warning("VoiceSessionManager: Multiple mic streams attempted! Closing previous stream.")
                try:
                    self.active_mic_stream.stop()
                    self.active_mic_stream.close()
                except Exception:
                    pass
            self.active_mic_stream = stream_obj
            self.active_mic_sessions_count = 1
            return True

    def unregister_mic_stream(self, stream_obj: Any) -> None:
        with self._lock:
            if self.active_mic_stream == stream_obj:
                self.active_mic_stream = None
                self.active_mic_sessions_count = 0
                self.is_mic_open = False

    def set_mic_active(self, active: bool) -> None:
        with self._lock:
            self.is_mic_open = active
            self.active_mic_sessions_count = 1 if active else 0

    def record_audio_warning(self, warning: str) -> None:
        with self._lock:
            self.audio_status_warnings += 1
            self.last_audio_warning = str(warning)

    def record_frame_captured(self) -> None:
        with self._lock:
            self.frames_captured += 1

    def record_frame_queued(self) -> None:
        with self._lock:
            self.frames_queued += 1

    def record_frame_dropped_overflow(self) -> None:
        with self._lock:
            self.frames_dropped_overflow += 1

    # ── Atomic Single-Voice Fallback Execution ──────────────────────────────

    async def execute_atomic_speech(
        self,
        turn_id: str,
        text: str,
        primary_synth_fn: Callable[[str], Any],
        fallback_synth_fn: Optional[Callable[[str], Any]] = None,
        primary_name: str = "primary",
        fallback_name: str = "fallback",
    ) -> bool:
        """Executes TTS speech with guaranteed single-playback semantics.
        
        If primary fails:
        1. Immediately cancels and purges any pending audio from primary.
        2. Calls fallback_synth_fn.
        3. Never plays both simultaneously.
        """
        if self.is_duplicate_response(text):
            return False

        playback_id = self.player.start_playback_transaction(turn_id, primary_name)
        self.mark_speaking_started()

        try:
            # Attempt primary
            success = await self._run_synth_stream(turn_id, playback_id, text, primary_synth_fn)
            if success:
                self.player.finish_playback_transaction(playback_id)
                self.mark_speaking_ended()
                return True
        except Exception as e:
            logger.warning("VoiceSessionManager: Primary TTS '%s' failed: %s", primary_name, e)

        # Primary failed or was cancelled
        if self.player.is_turn_cancelled(turn_id):
            logger.info("VoiceSessionManager: Turn %s was cancelled during speech.", turn_id)
            self.player.finish_playback_transaction(playback_id)
            self.mark_speaking_ended()
            return False

        if fallback_synth_fn is None:
            self.player.finish_playback_transaction(playback_id)
            self.mark_speaking_ended()
            return False

        # Switch to secondary/fallback with clean state
        logger.info("VoiceSessionManager: Activating atomic fallback TTS '%s' for turn %s", fallback_name, turn_id)
        self.player.cancel_current("primary_failed_switch_to_fallback", cancel_turn=False)
        fallback_playback_id = self.player.start_playback_transaction(turn_id, fallback_name)
        self.mark_speaking_started()

        try:
            success = await self._run_synth_stream(turn_id, fallback_playback_id, text, fallback_synth_fn)
            self.player.finish_playback_transaction(fallback_playback_id)
            self.mark_speaking_ended()
            return success
        except Exception as e2:
            logger.error("VoiceSessionManager: Fallback TTS '%s' failed as well: %s", fallback_name, e2)
            self.player.finish_playback_transaction(fallback_playback_id)
            self.mark_speaking_ended()
            return False

    async def _run_synth_stream(
        self,
        turn_id: str,
        playback_id: str,
        text: str,
        synth_fn: Callable[[str], Any],
    ) -> bool:
        """Executes a synthesis function and checks cancellation at each step."""
        if self.player.is_turn_cancelled(turn_id):
            return False

        res = synth_fn(text)
        if asyncio.iscoroutine(res):
            await res
        return True

    # ── Diagnostics Panel Data ──────────────────────────────────────────────

    def get_diagnostics(self) -> Dict[str, Any]:
        """Provides real-time state for UI diagnostic HUD and Web dashboard."""
        with self._lock:
            return {
                "active_mic_sessions": self.active_mic_sessions_count,
                "active_tts_sessions": 1 if self.player.is_playing else 0,
                "active_speaker": self.active_speaker_name,
                "speaker_confidence": round(self.active_speaker_confidence, 2),
                "current_turn_id": self.active_turn_id or "idle",
                "current_playback_id": self.player.current_playback_id or "none",
                "current_tts_provider": self.player.current_provider or "none",
                "authoritative_voice": self.authoritative_voice,
                "auto_speak_mode": self.auto_speak_mode.value,
                "startup_silence_guard": self.startup_silence_guard,
                "duplicate_events_dropped": self.duplicate_transcripts_dropped + self.duplicate_responses_dropped,
                "self_echo_suppressed_count": self.self_echo_frames_suppressed,
                "cancellations_count": self.player.cancellation_count,
                "is_speaking": self.player.is_playing,
                "is_echo_tail": time.monotonic() < self._tail_until,
                "is_mic_open": self.is_mic_open,
                "frames_captured": self.frames_captured,
                "frames_queued": self.frames_queued,
                "frames_dropped_overflow": self.frames_dropped_overflow,
                "audio_status_warnings": self.audio_status_warnings,
                "last_audio_warning": self.last_audio_warning,
                "input_callbacks_count": self.input_callbacks_count,
                "frames_captured_count": self.frames_captured_count,
                "frames_processed_count": self.frames_processed_count,
                "bytes_queued_count": self.bytes_queued_count,
                "bytes_sent_to_ai_count": self.bytes_sent_to_ai_count,
                "transcripts_received_count": self.transcripts_received_count,
                "responses_received_count": self.responses_received_count,
            }

    def shutdown(self) -> None:
        """Clean shutdown of streams and players."""
        self.player.cancel_current("shutdown")
        with self._lock:
            if self.active_mic_stream is not None:
                try:
                    self.active_mic_stream.stop()
                    self.active_mic_stream.close()
                except Exception:
                    pass
                self.active_mic_stream = None
                self.active_mic_sessions_count = 0
