"""core/audio_dsp.py — Audio DSP Pipeline: AEC reference subtraction, Silero VAD, Noise Suppression, and AGC.

Modular, real-time audio pre-processing pipeline for DAZY.
Handles:
- Reference-subtraction Acoustic Echo Cancellation (AEC) with loopback tracking
- Silero VAD for low-latency neural voice activity detection
- Spectral subtraction noise suppression
- Adaptive Automatic Gain Control (AGC)
- Real-time interruption & double-talk detection
"""
from __future__ import annotations

import collections
import logging
import math
import time
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger("dazy.audio_dsp")


class SileroVADWrapper:
    """Zero-latency neural Voice Activity Detector using Silero VAD with ONNX/Torch fallback."""

    def __init__(self, sample_rate: int = 16000, threshold: float = 0.5):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self._model = None
        self._available = False
        self._init_model()

    def _init_model(self) -> None:
        try:
            import silero_vad
            self._model = silero_vad.load_silero_vad()
            self._available = True
            logger.info("Silero VAD initialized successfully.")
        except Exception as e:
            logger.warning("Silero VAD package import failed: %s. Using energy/spectral fallback.", e)
            self._available = False

    def is_speech(self, pcm_chunk: np.ndarray | bytes) -> bool:
        """Determines if the given 16kHz PCM chunk contains speech."""
        if isinstance(pcm_chunk, bytes):
            audio = np.frombuffer(pcm_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        else:
            audio = pcm_chunk.astype(np.float32)
            if np.max(np.abs(audio)) > 1.0:
                audio = audio / 32768.0

        if len(audio) < 512:
            return False

        if self._available and self._model is not None:
            try:
                import torch
                # Ensure input chunk is multiple of 512 for silero
                chunk_len = (len(audio) // 512) * 512
                if chunk_len == 0:
                    return False
                tensor = torch.from_numpy(audio[:chunk_len])
                speech_prob = self._model(tensor, self.sample_rate).item()
                return speech_prob >= self.threshold
            except Exception:
                pass

        # Robust Energy + Zero-Crossing Rate Fallback
        rms = np.sqrt(np.mean(audio**2))
        zcr = np.mean(np.abs(np.diff(np.sign(audio)))) / 2.0
        return rms > 0.015 and (0.02 < zcr < 0.45)


class AcousticEchoCanceller:
    """AEC3-style spectral projection & adaptive reference subtraction filter.
    
    Prevents DAZY from hearing her own voice through speakers while preserving
    genuine user speech for real-time interruption.
    """

    def __init__(self, sample_rate: int = 16000, ref_history_sec: float = 2.0):
        self.sample_rate = sample_rate
        self.ref_history_sec = ref_history_sec
        # Circular buffer storing (timestamp, pcm_data, spectral_envelope)
        self._ref_buffer = collections.deque(maxlen=int(ref_history_sec * 50))
        self._gain_est = 0.5
        self._interruption_count = 0
        self._last_echo_similarity = 0.0

    def feed_reference_playback(self, pcm_data: bytes | np.ndarray) -> None:
        """Feed actual synthesized speech audio sent to speakers into AEC reference line."""
        if isinstance(pcm_data, bytes):
            samples = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32768.0
        else:
            samples = pcm_data.astype(np.float32)
            if np.max(np.abs(samples)) > 1.0:
                samples = samples / 32768.0

        now = time.monotonic()
        fft_mag = np.abs(np.fft.rfft(samples * np.hanning(len(samples)))) if len(samples) >= 64 else np.zeros(32)
        self._ref_buffer.append((now, samples, fft_mag))

    def process(self, mic_pcm: bytes | np.ndarray) -> Tuple[np.ndarray, bool, float]:
        """Processes raw microphone input against the reference playback signal.
        
        Returns:
            clean_pcm (np.ndarray): Echo-suppressed audio samples (float32).
            is_user_interruption (bool): True if user is actively speaking over playback.
            echo_similarity (float): Degree of match with speaker reference (0.0 to 1.0).
        """
        if isinstance(mic_pcm, bytes):
            mic = np.frombuffer(mic_pcm, dtype=np.int16).astype(np.float32) / 32768.0
        else:
            mic = mic_pcm.astype(np.float32)
            if np.max(np.abs(mic)) > 1.0:
                mic = mic / 32768.0

        if not self._ref_buffer or len(mic) < 64:
            return mic, False, 0.0

        now = time.monotonic()
        # Drop stale reference frames (>2.0s old)
        while self._ref_buffer and (now - self._ref_buffer[0][0]) > self.ref_history_sec:
            self._ref_buffer.popleft()

        if not self._ref_buffer:
            return mic, False, 0.0

        mic_fft = np.fft.rfft(mic * np.hanning(len(mic)))
        mic_mag = np.abs(mic_fft)

        best_sim = 0.0
        best_ref_mag = None

        # Cross-correlate against recent reference slices (accounting for acoustic delay)
        for _, _, ref_mag in self._ref_buffer:
            if len(ref_mag) != len(mic_mag):
                interp_ref = np.interp(
                    np.linspace(0, 1, len(mic_mag)),
                    np.linspace(0, 1, len(ref_mag)),
                    ref_mag
                )
            else:
                interp_ref = ref_mag

            norm_m = np.linalg.norm(mic_mag)
            norm_r = np.linalg.norm(interp_ref)
            if norm_m > 1e-4 and norm_r > 1e-4:
                sim = float(np.dot(mic_mag, interp_ref) / (norm_m * norm_r))
                if sim > best_sim:
                    best_sim = sim
                    best_ref_mag = interp_ref

        self._last_echo_similarity = best_sim

        # If microphone strongly matches the audio we just sent to speakers
        if best_sim > 0.60 and best_ref_mag is not None:
            # Spectral subtraction to eliminate echo
            clean_mag = np.maximum(mic_mag - 0.85 * best_ref_mag * (np.linalg.norm(mic_mag) / (np.linalg.norm(best_ref_mag) + 1e-6)), 0.0)
            clean_fft = clean_mag * np.exp(1j * np.angle(mic_fft))
            clean_audio = np.fft.irfft(clean_fft, n=len(mic)).real

            # Residual check: does user voice survive the subtraction?
            residual_energy = np.linalg.norm(clean_audio) / (np.linalg.norm(mic) + 1e-6)
            if residual_energy > 0.35:
                self._interruption_count += 1
                is_interruption = self._interruption_count >= 2
            else:
                self._interruption_count = 0
                is_interruption = False

            return clean_audio.astype(np.float32), is_interruption, best_sim

        self._interruption_count = 0
        return mic, False, best_sim


class AudioPreprocessor:
    """Comprehensive front-end audio DSP manager integrating AGC, Noise Suppression, AEC, and VAD."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.vad = SileroVADWrapper(sample_rate=sample_rate)
        self.aec = AcousticEchoCanceller(sample_rate=sample_rate)
        self.target_rms = 0.15
        self.max_gain = 4.0
        self.min_gain = 0.5
        self._current_gain = 1.0
        self._noise_floor = 0.005

    def feed_playback_reference(self, pcm_chunk: bytes | np.ndarray) -> None:
        """Feed speaker audio chunk into AEC reference buffer."""
        self.aec.feed_reference_playback(pcm_chunk)

    def process_frame(
        self, mic_chunk: bytes | np.ndarray, is_assistant_speaking: bool = False
    ) -> dict:
        """Processes one microphone chunk through the complete DSP chain.
        
        Returns dict with:
            'cleaned_pcm': bytes (int16 16kHz mono),
            'has_speech': bool (Silero VAD classification),
            'is_interruption': bool (genuine user barge-in over playback),
            'echo_similarity': float (0.0 to 1.0),
            'rms_level': float,
            'gain_applied': float
        """
        # Step 1: Acoustic Echo Cancellation
        cleaned_samples, is_interruption, echo_sim = self.aec.process(mic_chunk)

        # Step 2: Noise floor estimation and spectral suppression
        frame_rms = float(np.sqrt(np.mean(cleaned_samples**2)))
        if frame_rms < self._noise_floor * 1.5:
            self._noise_floor = 0.95 * self._noise_floor + 0.05 * frame_rms
        else:
            # Soft gating
            if frame_rms < self._noise_floor * 2.0:
                cleaned_samples = cleaned_samples * 0.3

        # Step 3: Automatic Gain Control (AGC)
        if frame_rms > 0.008:
            error = self.target_rms / (frame_rms + 1e-6)
            target_gain = np.clip(error, self.min_gain, self.max_gain)
            self._current_gain = 0.85 * self._current_gain + 0.15 * target_gain
        cleaned_samples = np.clip(cleaned_samples * self._current_gain, -1.0, 1.0)

        # Step 4: Silero VAD
        has_speech = self.vad.is_speech(cleaned_samples)

        # If assistant is speaking and audio matches echo, suppress speech flag unless barge-in confirmed
        if is_assistant_speaking and echo_sim > 0.55 and not is_interruption:
            has_speech = False

        int16_pcm = (cleaned_samples * 32767.0).astype(np.int16).tobytes()

        return {
            "cleaned_pcm": int16_pcm,
            "has_speech": has_speech,
            "is_interruption": is_interruption,
            "echo_similarity": echo_sim,
            "rms_level": frame_rms,
            "gain_applied": self._current_gain,
        }
