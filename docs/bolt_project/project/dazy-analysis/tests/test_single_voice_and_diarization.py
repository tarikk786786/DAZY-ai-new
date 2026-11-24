"""tests/test_single_voice_and_diarization.py — Regression Test Suite for Single-Voice & Two-Speaker Isolation.

Verifies:
1. Startup silence guard: No automatic speech on launch.
2. Single-voice transaction: AtomicTTSPlayer ensures at most 1 active TTS transaction.
3. Atomic fallback: When primary TTS fails, it switches to secondary with zero overlap or dual-playback.
4. Two distinct human speakers (Speaker A & B) with independent profiles and unknown rejection.
5. Assistant synthetic voice rejection: Disqualifies synthetic speech so assistant never listens to itself.
6. Half-duplex & Echo Tail suppression: Mic input blocked during playback and echo tail unless barge-in.
7. User barge-in: Genuine interruption immediately halts playback and purges playback queue.
8. Deduplication: Duplicate transcript events and duplicate response texts are suppressed.
"""
from __future__ import annotations

import asyncio
import time
import pytest
import numpy as np

from core.voice_session_manager import VoiceSessionManager, AutoSpeakMode, AtomicTTSPlayer
from core.speaker_id import SpeakerIdentifier, AUTHORITATIVE_FEMININE_VOICE
from core.listening_fsm import ListeningStateMachine, AssistantState


@pytest.fixture(autouse=True)
def reset_vsm():
    VoiceSessionManager.reset_instance()
    yield
    VoiceSessionManager.reset_instance()


def test_startup_silence_guard_and_auto_speak_modes():
    """Verify assistant remains completely silent on launch until explicit interaction."""
    vsm = VoiceSessionManager.get_instance()
    assert vsm.startup_silence_guard is True

    # Attempt to speak without user initiation
    assert vsm.can_auto_speak() is False
    assert vsm.can_auto_speak(is_wake_triggered=True) is False

    # Clear startup guard via explicit user interaction
    vsm.clear_startup_guard()
    assert vsm.startup_silence_guard is False

    # Test WAKE_ONLY mode (default)
    vsm.set_auto_speak_mode(AutoSpeakMode.WAKE_ONLY)
    assert vsm.can_auto_speak(is_wake_triggered=False, is_follow_up=False) is False
    assert vsm.can_auto_speak(is_wake_triggered=True) is True
    assert vsm.can_auto_speak(is_follow_up=True) is True

    # Test SILENT mode
    vsm.set_auto_speak_mode(AutoSpeakMode.SILENT)
    assert vsm.can_auto_speak(is_wake_triggered=True) is False

    # Test CONTINUOUS mode
    vsm.set_auto_speak_mode(AutoSpeakMode.CONTINUOUS)
    assert vsm.can_auto_speak() is True


def test_atomic_tts_player_single_playback_and_preemption():
    """Verify only ONE audio transaction can play at a time with clean preemption."""
    player = AtomicTTSPlayer()

    # Start first transaction
    pb_1 = player.start_playback_transaction(turn_id="turn_1", provider="edge_tts")
    assert player.is_playing is True
    assert player.current_playback_id == pb_1
    assert player.current_provider == "edge_tts"

    # Start second transaction without closing first — must preempt cleanly
    pb_2 = player.start_playback_transaction(turn_id="turn_2", provider="kokoro_tts")
    assert player.is_playing is True
    assert player.current_playback_id == pb_2
    assert player.current_provider == "kokoro_tts"
    assert player.is_turn_cancelled("turn_1") is True
    assert player.is_turn_cancelled("turn_2") is False

    # Cancel current playback
    player.cancel_current("user_interruption")
    assert player.is_playing is False
    assert player.current_playback_id is None
    assert player.is_turn_cancelled("turn_2") is True


@pytest.mark.asyncio
async def test_atomic_fallback_tts_execution():
    """Verify fallback activates cleanly if primary fails, without dual-speech."""
    vsm = VoiceSessionManager.get_instance()
    vsm.clear_startup_guard()
    vsm.set_auto_speak_mode(AutoSpeakMode.CONTINUOUS)

    played_voices = []

    def failing_primary(text: str):
        played_voices.append("primary_started")
        raise RuntimeError("Primary TTS network timeout")

    def working_fallback(text: str):
        played_voices.append("fallback_success")
        return b"pcm_fallback_audio"

    turn_id = vsm.new_turn("Tarik", 0.95)
    success = await vsm.execute_atomic_speech(
        turn_id=turn_id,
        text="Hello Tarik, main aapki madad ke liye tayyar hoon.",
        primary_synth_fn=failing_primary,
        fallback_synth_fn=working_fallback,
        primary_name="primary_edge",
        fallback_name="secondary_kokoro",
    )

    assert success is True
    # Primary failed and cleanly gave way to fallback
    assert played_voices == ["primary_started", "fallback_success"]
    assert vsm.player.is_playing is False


def test_two_distinct_human_speakers_and_unknown_rejection():
    """Verify Speaker A (Tarik) and Speaker B are distinctly recognized and never confused with unknown."""
    spk = SpeakerIdentifier(threshold=0.70)

    t = np.linspace(0, 1, 16000)
    voice_a = (np.sin(2 * np.pi * 150 * t) * 14000).astype(np.int16).tobytes()  # Speaker A ~ 150 Hz
    voice_b = (np.sin(2 * np.pi * 420 * t) * 14000).astype(np.int16).tobytes()  # Speaker B ~ 420 Hz
    stranger = (np.sin(2 * np.pi * 850 * t) * 14000).astype(np.int16).tobytes() # Stranger ~ 850 Hz

    # Enroll Speaker A (Tarik, Owner)
    assert spk.enroll_voice_sample("Tarik", voice_a, role="owner") is True
    # Enroll Speaker B (Priya, Companion)
    assert spk.enroll_voice_sample("Priya", voice_b, role="companion") is True

    # Identify Speaker A
    name_a, conf_a, ver_a = spk.identify_speaker(voice_a)
    assert name_a == "Tarik"
    assert ver_a is True
    assert conf_a >= 0.70

    # Identify Speaker B
    name_b, conf_b, ver_b = spk.identify_speaker(voice_b)
    assert name_b == "Priya"
    assert ver_b is True
    assert conf_b >= 0.70

    # Test distinct profile roles and permissions
    prof_a = spk.get_speaker_profile("Tarik")
    prof_b = spk.get_speaker_profile("Priya")
    assert prof_a["role"] == "owner"
    assert prof_a["permissions"]["execute_system_commands"] is True
    assert prof_a["permissions"]["access_private_memory"] is True

    assert prof_b["role"] == "companion"
    assert prof_b["permissions"]["access_private_memory"] is False

    # Test stranger voice rejection
    name_s, conf_s, ver_s = spk.identify_speaker(stranger)
    assert name_s == "unknown"
    assert ver_s is False

    # Authoritative Assistant Voice is immutable
    assert spk.get_authoritative_assistant_voice() == AUTHORITATIVE_FEMININE_VOICE


def test_synthetic_assistant_voice_echo_rejection():
    """Verify assistant's own synthesized speech is identified as echo and disqualified from human speech."""
    spk = SpeakerIdentifier(threshold=0.70)
    t = np.linspace(0, 1, 16000)
    assistant_audio = (np.sin(2 * np.pi * 260 * t) * 14000).astype(np.int16).tobytes()

    # Register assistant speech playback
    spk.register_assistant_playback(assistant_audio)

    # Microphone hears this exact playback audio
    identified_name, _, is_ver = spk.identify_speaker(assistant_audio)
    assert identified_name == "assistant_echo"
    assert is_ver is False

    # Even with wake phrase, assistant echo is never allowed to address the assistant
    assert spk.is_addressing_assistant("Hey Dazy", speaker="assistant_echo", is_wake_activated=True, seconds_since_last_turn=1.0) is False


def test_half_duplex_and_echo_tail_suppression():
    """Verify microphone input is completely suppressed during speaking and echo tail to prevent self-looping."""
    vsm = VoiceSessionManager.get_instance()
    t = np.linspace(0, 0.1, 1600)
    dummy_frame = (np.sin(2 * np.pi * 200 * t) * 10000).astype(np.int16).tobytes()

    # When idle: mic is NOT suppressed
    assert vsm.should_suppress_mic_input(dummy_frame) is False

    # When speaking starts: mic IS suppressed
    pb_id = vsm.player.start_playback_transaction("t_123", "edge_tts")
    vsm.mark_speaking_started()
    assert vsm.should_suppress_mic_input(dummy_frame) is True

    # When speaking ends: still suppressed during echo tail
    vsm.player.finish_playback_transaction(pb_id)
    vsm.mark_speaking_ended()
    assert vsm.is_assistant_speaking_or_echo() is True
    assert vsm.should_suppress_mic_input(dummy_frame) is True

    # Fast forward beyond echo tail margin
    vsm._tail_until = time.monotonic() - 0.1
    assert vsm.is_assistant_speaking_or_echo() is False
    assert vsm.should_suppress_mic_input(dummy_frame) is False


def test_barge_in_stops_speech():
    """Verify barge-in detection immediately interrupts assistant speech."""
    fsm = ListeningStateMachine(followup_timeout_sec=5.0)
    fsm.transition_to(AssistantState.WAKE_DETECTED)
    fsm.transition_to(AssistantState.LISTENING)
    fsm.transition_to(AssistantState.TRANSCRIBING)
    fsm.transition_to(AssistantState.THINKING)
    fsm.transition_to(AssistantState.SPEAKING)
    assert fsm.state == AssistantState.SPEAKING

    # User speaks over assistant
    assert fsm.handle_barge_in() is True
    # State transitions through INTERRUPTED directly into LISTENING
    assert fsm.state == AssistantState.LISTENING


def test_deduplication_guards():
    """Verify duplicate transcripts and duplicate responses are dropped to prevent repeat loops."""
    vsm = VoiceSessionManager.get_instance()

    # Transcript deduplication
    assert vsm.is_duplicate_transcript("Hello Dazy") is False
    assert vsm.is_duplicate_transcript("Hello Dazy") is True  # Duplicate!
    assert vsm.is_duplicate_transcript("hello dazy") is True  # Case insensitive duplicate!
    assert vsm.is_duplicate_transcript("Kaise ho aap?") is False

    # Response deduplication
    assert vsm.is_duplicate_response("Main bilkul theek hoon, aap batao.") is False
    assert vsm.is_duplicate_response("Main bilkul theek hoon, aap batao.") is True  # Replay blocked!
    assert vsm.duplicate_responses_dropped == 1
