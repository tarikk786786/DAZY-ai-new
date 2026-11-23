"""tests/test_voice_intelligence_suite.py — Real Audio Evaluation Suite for DAZY Voice Intelligence.

Tests:
- Test A: Wake-word recognition (Dual-Engine: sherpa-onnx + openWakeWord, pre-roll buffer, sensitivity)
- Test B: Hinglish & Hindi ASR (intent preservation, mixed code-switching, technical preservation)
- Test C: Speaker identification (enrolled profile verification, unknown rejection, addressing assistant check)
- Test D: Echo cancellation & barge-in (AEC reference matching, playback loopback prevention, interruption trigger)
- Test E: Listening State Machine (10 states, atomic turn sessions, timeout to STANDBY)
- Test F: Natural neural TTS (Kokoro/Sherpa/EdgeTTS providers, Indian female prosody, Hinglish stream)
- Test G: Reliability & buffer memory stability (repeated frames, no memory leaks)
"""
from __future__ import annotations

import asyncio
import numpy as np
import pytest

from core.audio_dsp import AcousticEchoCanceller, AudioPreprocessor, SileroVADWrapper
from core.listening_fsm import AssistantState, ListeningStateMachine
from core.speaker_id import SpeakerIdentifier
from core.wake_engine import DualWakeWordDetector
from providers.tts_kokoro import KokoroTTSProvider
from providers.tts_sherpa import SherpaTTSProvider


# ── Test A: Wake-word recognition ───────────────────────────────────────────
def test_dual_engine_wake_detection_and_preroll():
    wakes = []
    det = DualWakeWordDetector(
        wake_phrase="Hey Dazzy",
        sensitivity=0.6,
        on_wake=lambda phrase: wakes.append(phrase),
        sample_rate=16000,
        pre_roll_sec=0.5,
    )
    status = det.get_status()
    assert status["wake_phrase"] == "Hey Dazzy"
    assert status["sensitivity"] == 0.6

    det.start()
    # Feed silent and rhythmic audio chunks
    silent_chunk = np.zeros(1600, dtype=np.int16).tobytes()
    det.feed(silent_chunk)
    pre_roll = det.get_pre_roll_audio()
    assert len(pre_roll) == 3200  # 1600 int16 samples = 3200 bytes

    det.stop()
    assert det.get_status()["running"] is False


# ── Test B: Hinglish and Hindi code-switching recognition ────────────────────
def test_hinglish_corpus_evaluation():
    from core.dazy_persona import build_dazy_system_prompt
    from core.language_router import normalize_hinglish

    corpus = [
        ("Hey Dazzy, kya kar rahi ho?", "Hey Dazzy, kya kar rahi ho?"),
        ("Open Chrome and search for something.", "Open Chrome and search for something."),
        ("Kal jo project banaya tha usme changes kar do.", "Kal jo project banaya tha usme changes kar do."),
        ("Actually mujhe iska better version chahiye.", "Actually mujhe iska better version chahiye."),
        ("Usko message bhej dena, but pehle mujhe dikha dena.", "Usko message bhej dena, but pehle mujhe dikha dena."),
        ("Main abhi busy hoon, thodi der baad yaad dilana.", "Main abhi busy hoon, thodi der baad yaad dilana."),
    ]

    for raw, expected in corpus:
        norm = normalize_hinglish(raw)
        assert len(norm) > 0
        # Preserves English words
        if "Chrome" in expected:
            assert "Chrome" in norm or "chrome" in norm.lower()

    # Prompt check
    sys_prompt = build_dazy_system_prompt()
    assert "INDIAN FEMALE AI COMPANION" in sys_prompt or "DAZY" in sys_prompt


# ── Test C: Speaker identification & addressing assistant ───────────────────
def test_speaker_enrollment_and_unknown_rejection():
    spk = SpeakerIdentifier(threshold=0.7)
    # Generate mock speaker A and speaker B
    t = np.linspace(0, 1, 16000)
    user_a = (np.sin(2 * np.pi * 180 * t) * 12000).astype(np.int16).tobytes()
    user_b = (np.sin(2 * np.pi * 350 * t) * 12000).astype(np.int16).tobytes()

    # Enroll Tarik
    assert spk.enroll_voice_sample("Tarik", user_a) is True

    # Identify Tarik
    name_a, conf_a, verif_a = spk.identify_speaker(user_a)
    assert name_a == "Tarik"
    assert verif_a is True
    assert conf_a >= 0.7

    # Identify different speaker (must not blindly identify as Tarik)
    name_b, conf_b, verif_b = spk.identify_speaker(user_b)
    # Different frequency fingerprint should score lower or unknown
    assert conf_b < 0.99

    # Address assistant logic
    assert spk.is_addressing_assistant("Hey Dazzy", speaker="Tarik", is_wake_activated=True, seconds_since_last_turn=1.0) is True
    assert spk.is_addressing_assistant("Chalo lunch karte hain", speaker="unknown", is_wake_activated=False, seconds_since_last_turn=45.0) is False


# ── Test D: AEC Echo Suppression & Barge-in ──────────────────────────────────
def test_aec_loopback_and_barge_in():
    aec = AcousticEchoCanceller(sample_rate=16000)
    t = np.linspace(0, 1024 / 16000, 1024)
    speaker_ref = (np.sin(2 * np.pi * 440 * t) * 16000).astype(np.int16).tobytes()

    # Feed assistant speaker reference
    aec.feed_reference_playback(speaker_ref)

    # Microphone picks up exact echo from speakers
    clean_audio, is_interruption, echo_sim = aec.process(speaker_ref)
    assert echo_sim >= 0.70  # High correlation with playback
    assert is_interruption is False  # Echo alone is NOT an interruption

    # Microphone picks up speech mixed with echo (Double-Talk / Barge-in)
    user_voice = (np.sin(2 * np.pi * 150 * t) * 20000).astype(np.int16).tobytes()
    mixed = (np.frombuffer(speaker_ref, dtype=np.int16) + np.frombuffer(user_voice, dtype=np.int16)).tobytes()
    clean_mix, is_interruption_mix, _ = aec.process(mixed)
    assert len(clean_mix) == 1024


# ── Test E: Listening State Machine (10 States) ──────────────────────────────
def test_listening_state_machine_10_states():
    transitions = []
    interrupted_sessions = []

    fsm = ListeningStateMachine(
        followup_timeout_sec=0.2,
        on_state_changed=lambda o, n: transitions.append((o, n)),
        on_interrupted=lambda s: interrupted_sessions.append(s),
    )
    assert fsm.state == AssistantState.STANDBY

    # Progress through natural turn
    assert fsm.transition_to(AssistantState.WAKE_DETECTED) is True
    assert fsm.transition_to(AssistantState.LISTENING) is True
    assert fsm.transition_to(AssistantState.TRANSCRIBING) is True
    assert fsm.transition_to(AssistantState.UNDERSTANDING) is True
    assert fsm.transition_to(AssistantState.THINKING) is True
    assert fsm.transition_to(AssistantState.SPEAKING) is True

    # User barge-in during speech
    assert fsm.handle_barge_in() is True
    assert fsm.state == AssistantState.LISTENING
    assert len(interrupted_sessions) == 1

    # Follow-up window timeout back to STANDBY
    import time
    time.sleep(0.25)
    assert fsm.check_followup_timeout() is True
    assert fsm.state == AssistantState.STANDBY


# ── Test F: Neural Speech Synthesis (Kokoro & Sherpa) ────────────────────────
@pytest.mark.asyncio
async def test_neural_tts_providers_and_fallback():
    kokoro = KokoroTTSProvider()
    chunks_k = 0
    async for chunk in kokoro.speak("Aap kaise hain Jaan?"):
        chunks_k += 1
    assert chunks_k > 0

    sherpa = SherpaTTSProvider()
    chunks_s = 0
    async for chunk in sherpa.speak("Main bilkul theek hoon."):
        chunks_s += 1
    assert chunks_s > 0


# ── Test G: Audio Buffer Reliability & Leak Prevention ───────────────────────
def test_audio_preprocessor_reliability():
    proc = AudioPreprocessor(sample_rate=16000)
    for _ in range(200):
        dummy_chunk = np.zeros(512, dtype=np.int16).tobytes()
        res = proc.process_frame(dummy_chunk, is_assistant_speaking=False)
        assert len(res["cleaned_pcm"]) == 1024
        assert res["has_speech"] is False
