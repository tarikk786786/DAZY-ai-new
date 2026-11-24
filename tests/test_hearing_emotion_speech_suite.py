"""tests/test_hearing_emotion_speech_suite.py — Automated Acoustic, Emotional Intelligence, and Speech Suite.

Comprehensive regression and real-world evaluation testing:
1. Normal, quiet, and whispered speech acoustic detection
2. Background noise resilience (fan noise, low SNR)
3. Turn-boundary hangover and pause preservation
4. Multilingual recognition and language stabilization (Hindi, Hinglish, English, Odia)
5. Multimodal conversational emotion analysis (Sadness, Excitement, Frustration, Confusion, Urgency)
6. Explicit user emotion correction handling
7. Zero asterisk & markdown speech normalization
8. Indian feminine TTS benchmarking (Chatterbox, Mithi v2 Flash, Volt-TTS)
9. Hardware audio diagnostics API endpoints
"""
from __future__ import annotations

import time
import numpy as np
import pytest
from fastapi.testclient import TestClient

from core.audio_dsp import AudioPreprocessor, SileroVADWrapper
from core.streaming_asr import LanguageStabilizer, StreamingASRManager
from core.multimodal_emotion import MultimodalEmotionEngine, AcousticProsodyAnalyzer
from core.pronunciation_engine import normalize_text_for_speech, detect_speech_language
from core.tts_benchmark import TTSBenchmarkSuite
from dashboard.server import DashboardServer


# ── Acoustic PCM Generators ───────────────────────────────────────────────────

def make_normal_speech_pcm(duration_sec: float = 0.5, sr: int = 16000) -> bytes:
    """Voiced harmonic speech with natural vocal formant profile (RMS ~0.12)."""
    t = np.linspace(0, duration_sec, int(duration_sec * sr), endpoint=False)
    f0 = 180.0
    signal = (
        0.50 * np.sin(2 * np.pi * f0 * t)
        + 0.30 * np.sin(2 * np.pi * (f0 * 2) * t)
        + 0.15 * np.sin(2 * np.pi * (f0 * 3) * t)
    )
    # Natural cadence envelope
    envelope = np.sin(np.pi * np.linspace(0, 1, len(t))) ** 1.5
    signal = signal * envelope * 0.25
    return (signal * 32767.0).astype(np.int16).tobytes()


def make_whispered_speech_pcm(duration_sec: float = 0.5, sr: int = 16000) -> bytes:
    """Unvoiced whispered speech: high-frequency frication noise (1.5kHz - 5.5kHz, RMS ~0.018)."""
    n_samples = int(duration_sec * sr)
    noise = np.random.normal(0, 0.015, n_samples)
    t = np.linspace(0, duration_sec, n_samples, endpoint=False)
    # Add high-frequency resonances
    whisper = noise + 0.008 * np.sin(2 * np.pi * 2600 * t) + 0.005 * np.sin(2 * np.pi * 3800 * t)
    return (whisper * 32767.0).astype(np.int16).tobytes()


def make_low_volume_speech_pcm(duration_sec: float = 0.5, sr: int = 16000) -> bytes:
    """Very quiet soft speech (RMS ~0.008)."""
    t = np.linspace(0, duration_sec, int(duration_sec * sr), endpoint=False)
    f0 = 190.0
    signal = 0.012 * np.sin(2 * np.pi * f0 * t)
    return (signal * 32767.0).astype(np.int16).tobytes()


def make_fan_noise_pcm(duration_sec: float = 0.5, sr: int = 16000) -> bytes:
    """Low-frequency continuous fan rumble (f < 300Hz, RMS ~0.015)."""
    t = np.linspace(0, duration_sec, int(duration_sec * sr), endpoint=False)
    rumble = 0.015 * np.sin(2 * np.pi * 120 * t) + 0.008 * np.sin(2 * np.pi * 60 * t)
    return (rumble * 32767.0).astype(np.int16).tobytes()


# ── 1. Hearing & Whisper VAD Tests ────────────────────────────────────────────

def test_normal_speech_detection():
    dsp = AudioPreprocessor()
    pcm = make_normal_speech_pcm(0.5)
    res = dsp.process_frame(pcm)
    assert res["has_speech"] is True
    assert res["rms_level"] > 0.01
    assert res["gain_applied"] > 0.0


def test_whisper_and_quiet_speech_recall():
    dsp = AudioPreprocessor()
    whisper_pcm = make_whispered_speech_pcm(0.5)
    res_whisper = dsp.process_frame(whisper_pcm)
    # Whisper must NOT be discarded as silence
    assert res_whisper["has_speech"] is True

    quiet_pcm = make_low_volume_speech_pcm(0.5)
    res_quiet = dsp.process_frame(quiet_pcm)
    # Low volume speech must be detected via adaptive gain / sensitive VAD
    assert res_quiet["has_speech"] is True


def test_fan_noise_rejection():
    vad = SileroVADWrapper()
    fan_pcm = make_fan_noise_pcm(0.5)
    # Fan noise without speech must not trigger speech flag
    is_speech = vad.is_speech(fan_pcm)
    assert is_speech is False


def test_turn_boundary_hangover_pause_preservation():
    dsp = AudioPreprocessor(hangover_frames=5)
    speech_pcm = make_normal_speech_pcm(0.1)
    silence_pcm = (np.zeros(1600, dtype=np.float32) * 32767.0).astype(np.int16).tobytes()

    # Step 1: Active speech
    r1 = dsp.process_frame(speech_pcm)
    assert r1["has_speech"] is True

    # Step 2: Natural pause (silence immediately following speech)
    r2 = dsp.process_frame(silence_pcm)
    # Hangover must preserve speech active flag so audio is not cut off mid-clause
    assert r2["raw_speech"] is False
    assert r2["has_speech"] is True


# ── 2. Multilingual Recognition & Language Stabilization Tests ───────────────

def test_language_detection_lexical():
    # English
    assert detect_speech_language("Good morning DAZY, what is our schedule today?") == "english"
    # Hindi
    assert detect_speech_language("नमस्ते, आज मौसम कैसा रहेगा?") == "hindi"
    # Hinglish
    assert detect_speech_language("Main bilkul theek hoon, aap batao kya haal hai") == "hinglish"


def test_language_stabilizer_hysteresis():
    stabilizer = LanguageStabilizer(hysteresis_count=2)
    assert stabilizer.current_lang == "en"

    # Single isolated detection does not flip immediately
    s1 = stabilizer.update("hi")
    assert s1 == "en"

    # Second consecutive detection confirms switch
    s2 = stabilizer.update("hi")
    assert s2 == "hi"

    # English transient word does not flip immediately
    s3 = stabilizer.update("en")
    assert s3 == "hi"


# ── 3. Multimodal Conversational Emotional Intelligence Tests ─────────────────

def test_emotional_policy_empathetic_sadness():
    engine = MultimodalEmotionEngine()
    policy = engine.analyze("I am feeling so exhausted, tired and down today...")
    assert policy.tts_style == "soft_empathetic"
    assert policy.tts_speed <= 0.95
    assert "compassionate warmth" in policy.llm_prompt_guidance
    assert "pretend to possess personal human feelings" in policy.llm_prompt_guidance


def test_emotional_policy_enthusiastic_excitement():
    engine = MultimodalEmotionEngine()
    policy = engine.analyze("OMG DAZY we just launched our project, this is amazing!")
    assert policy.tts_style == "cheerful_bright"
    assert policy.tts_speed >= 1.05
    assert "positive energy" in policy.llm_prompt_guidance


def test_emotional_policy_patient_frustration():
    engine = MultimodalEmotionEngine()
    policy = engine.analyze("Ugh, this stupid bug is frustrating me so much!")
    assert policy.tts_style == "calm_patient"
    assert "steady calmness" in policy.llm_prompt_guidance


def test_emotional_policy_clear_confusion():
    engine = MultimodalEmotionEngine()
    policy = engine.analyze("Wait, what does that mean? I am really confused.")
    assert policy.tts_style == "clear_supportive"
    assert "clarity" in policy.llm_prompt_guidance


def test_explicit_user_emotion_correction():
    engine = MultimodalEmotionEngine()
    # User clarifies they are not angry
    policy = engine.analyze("I am not angry, I am just tired")
    assert "angry" in engine._user_explicit_corrections
    assert engine._user_explicit_corrections["angry"] == "tired"


def test_acoustic_prosody_pitch_and_tempo():
    analyzer = AcousticProsodyAnalyzer(sample_rate=16000)
    pcm = make_normal_speech_pcm(0.5)
    prosody = analyzer.extract_features(pcm)
    assert prosody.pitch_mean_hz > 100.0
    assert prosody.energy_rms > 0.01
    assert prosody.dynamic_range_db > 5.0


# ── 4. Speech Normalization & Zero-Asterisk Tests ─────────────────────────────

def test_speech_normalization_strips_markdown_and_asterisks():
    input_text = "**Hello!** This is a *test* with `code block` and a [link](https://example.com) ### Section 1"
    normalized = normalize_text_for_speech(input_text)
    assert "*" not in normalized
    assert "`" not in normalized
    assert "[" not in normalized
    assert "https://" not in normalized
    assert "###" not in normalized
    assert "Hello! This is a test with code block and a link Section 1" in normalized


def test_speech_normalization_preserves_hinglish_and_currency():
    input_text = "Tarik bhai, ₹500 transfer ho gaye hain. Thanks a lot!"
    normalized = normalize_text_for_speech(input_text)
    assert "500 rupees" in normalized
    assert "*" not in normalized


def test_speech_normalization_removes_table_pipes():
    table_text = "| Feature | Status |\n| Voice | Ready |"
    normalized = normalize_text_for_speech(table_text)
    assert "|" not in normalized
    assert "Voice" in normalized


# ── 5. Indian Feminine Voice TTS Benchmarking Tests ──────────────────────────

def test_tts_benchmark_runner():
    bench = TTSBenchmarkSuite()
    results = bench.run_all()
    assert len(results) == 15  # 5 test sentences * 3 candidate providers

    chatterbox_results = [r for r in results if r.provider == "Chatterbox Turbo"]
    mithi_results = [r for r in results if r.provider == "Mithi v2 Flash"]
    volt_results = [r for r in results if r.provider == "Volt-TTS (Preview)"]

    assert len(chatterbox_results) == 5
    assert len(mithi_results) == 5
    assert len(volt_results) == 5

    for r in results:
        assert r.audio_duration_sec > 0.3
        assert r.num_bytes > 5000
        assert r.rtf < 1.0  # Real-time factor strictly faster than real-time


# ── 6. Audio Hardware Diagnostics Endpoints Tests ────────────────────────────

def test_audio_hardware_diagnostics_api():
    server = DashboardServer()
    client = TestClient(server.app)
    token = "diag_test_token"
    server._tokens[token] = time.time()

    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/audio-hardware-diagnostics", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    diag = data["diagnostics"]
    assert "selected_microphone" in diag
    assert "input_sample_rate" in diag
    assert diag["input_sample_rate"] == 16000
    assert "vad_state" in diag
    assert "tts_provider" in diag


def test_audio_tests_endpoints_mic_speaker_speech():
    server = DashboardServer()
    client = TestClient(server.app)
    token = "diag_test_token"
    server._tokens[token] = time.time()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Mic test
    res_mic = client.post("/api/audio-test/mic", headers=headers)
    assert res_mic.status_code == 200
    assert res_mic.json()["status"] == "PASS"

    # 2. Speaker test
    res_spk = client.post("/api/audio-test/speaker", headers=headers)
    assert res_spk.status_code == 200
    assert res_spk.json()["status"] == "PASS"

    # 3. Speech test
    res_speech = client.post("/api/audio-test/speech", headers=headers)
    assert res_speech.status_code == 200
    assert res_speech.json()["status"] == "PASS"
    assert "*" not in res_speech.json()["normalized_speech_text"]
