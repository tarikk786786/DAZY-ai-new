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
    """Zero-latency neural Voice Activity Detector using Silero VAD with ONNX/Torch fallback,
    equipped with dual-threshold whisper and low-volume sensitivity handling.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        threshold: float = 0.45,
        whisper_threshold: float = 0.20,
    ):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.whisper_threshold = whisper_threshold
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

    def analyze_whisper_acoustics(self, audio: np.ndarray) -> Tuple[bool, float]:
        """Acoustic feature analysis for whispered and soft speech.
        
        Whispered speech lacks periodic vocal cord vibration and has energy shifted
        upwards into 1.5 kHz - 6.0 kHz frication noise bands with high ZCR.
        """
        if len(audio) < 128:
            return False, 0.0

        rms = float(np.sqrt(np.mean(audio**2)))
        zcr = float(np.mean(np.abs(np.diff(np.sign(audio)))) / 2.0)

        # High-frequency spectral ratio (HFSR)
        fft_mag = np.abs(np.fft.rfft(audio * np.hanning(len(audio))))
        freqs = np.fft.rfftfreq(len(audio), d=1.0 / self.sample_rate)
        
        high_mask = (freqs >= 1400) & (freqs <= 6500)
        high_energy = float(np.sum(fft_mag[high_mask] ** 2))
        total_energy = float(np.sum(fft_mag**2) + 1e-9)
        hfsr = high_energy / total_energy

        # Whispered speech: low energy (0.002 to 0.035), high ZCR (>0.12), high HFSR (>0.32)
        is_whisper_acoustic = (0.002 <= rms <= 0.040) and (zcr >= 0.12) and (hfsr >= 0.30)
        confidence = float(np.clip((hfsr * 0.5) + (zcr * 0.3) + (1.0 - min(1.0, rms * 25.0)) * 0.2, 0.0, 1.0))
        return is_whisper_acoustic, confidence

    def is_speech(self, pcm_chunk: np.ndarray | bytes) -> bool:
        """Determines if the given 16kHz PCM chunk contains speech (normal or whisper)."""
        has_speech, _, _ = self.classify_speech(pcm_chunk)
        return has_speech

    def classify_speech(self, pcm_chunk: np.ndarray | bytes) -> Tuple[bool, bool, float]:
        """Classifies speech presence, whisper status, and model confidence.
        
        Returns:
            has_speech (bool): True if speech or whisper detected.
            is_whisper (bool): True if whispered/soft speech specifically detected.
            confidence (float): Estimated confidence (0.0 to 1.0).
        """
        if isinstance(pcm_chunk, bytes):
            audio = np.frombuffer(pcm_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        else:
            audio = pcm_chunk.astype(np.float32)
            if np.max(np.abs(audio)) > 1.0:
                audio = audio / 32768.0

        if len(audio) < 512:
            return False, False, 0.0

        is_whisper_cand, whisper_conf = self.analyze_whisper_acoustics(audio)
        neural_prob = 0.0

        if self._available and self._model is not None:
            try:
                import torch
                chunk_len = (len(audio) // 512) * 512
                if chunk_len > 0:
                    tensor = torch.from_numpy(audio[:chunk_len])
                    neural_prob = float(self._model(tensor, self.sample_rate).item())
                    
                    # Normal speech passes standard threshold
                    if neural_prob >= self.threshold:
                        return True, False, neural_prob
                    
                    # Whispered speech passes lowered sensitive threshold when acoustic signature matches
                    if neural_prob >= self.whisper_threshold and is_whisper_cand:
                        return True, True, max(neural_prob, whisper_conf)
            except Exception:
                pass

        # Robust Fallback for offline / mock testing or when torch is unavailable
        rms = float(np.sqrt(np.mean(audio**2)))
        zcr = float(np.mean(np.abs(np.diff(np.sign(audio)))) / 2.0)

        # Standard voice fallback
        if rms > 0.012 and (0.02 < zcr < 0.45):
            return True, False, min(0.95, rms * 15.0)

        # Whispered voice fallback
        if is_whisper_cand and whisper_conf > 0.45:
            return True, True, whisper_conf

        return False, False, neural_prob


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
    """Comprehensive front-end audio DSP manager integrating AGC, Noise Suppression, AEC, and Whisper/Silero VAD."""

    def __init__(self, sample_rate: int = 16000, hangover_frames: int = 12, pre_roll_frames: int = 5):
        self.sample_rate = sample_rate
        self.vad = SileroVADWrapper(sample_rate=sample_rate)
        self.aec = AcousticEchoCanceller(sample_rate=sample_rate)
        self.target_rms = 0.15
        self.max_gain = 4.0
        self.min_gain = 0.5
        self._current_gain = 1.0
        self._noise_floor = 0.005
        
        # Turn boundary & whisper preservation
        self.hangover_frames = hangover_frames
        self._hangover_remaining = 0
        self._pre_roll_buffer: collections.deque = collections.deque(maxlen=pre_roll_frames)
        self._is_active_speech_turn = False

    def feed_playback_reference(self, pcm_chunk: bytes | np.ndarray) -> None:
        """Feed speaker audio chunk into AEC reference buffer."""
        self.aec.feed_reference_playback(pcm_chunk)

    def process_frame(
        self, mic_chunk: bytes | np.ndarray, is_assistant_speaking: bool = False
    ) -> dict:
        """Processes one microphone chunk through the complete DSP chain.
        
        Returns dict with:
            'cleaned_pcm': bytes (int16 16kHz mono),
            'has_speech': bool (Silero VAD classification with hangover smoothing),
            'is_whisper': bool (detected whispered/quiet speech),
            'vad_confidence': float,
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
            # Soft gating for non-speech noise
            if frame_rms < self._noise_floor * 2.0:
                cleaned_samples = cleaned_samples * 0.4

        # Step 3: Automatic Gain Control (AGC) - adaptive boost without amplifying noise floor
        effective_rms = max(frame_rms, self._noise_floor)
        if effective_rms > 0.004:
            # Don't apply high gain if SNR is too low
            snr_approx = effective_rms / (self._noise_floor + 1e-6)
            if snr_approx > 1.3:
                error = self.target_rms / (effective_rms + 1e-6)
                target_gain = float(np.clip(error, self.min_gain, self.max_gain))
                self._current_gain = 0.85 * self._current_gain + 0.15 * target_gain
            else:
                self._current_gain = 0.95 * self._current_gain + 0.05 * 1.0
        cleaned_samples = np.clip(cleaned_samples * self._current_gain, -1.0, 1.0)

        # Step 4: Silero VAD + Whisper Classification
        raw_has_speech, is_whisper, vad_conf = self.vad.classify_speech(cleaned_samples)

        # Step 5: Hangover & Turn-Boundary Management
        if raw_has_speech:
            self._hangover_remaining = self.hangover_frames
            self._is_active_speech_turn = True
            has_speech = True
        elif self._hangover_remaining > 0:
            self._hangover_remaining -= 1
            has_speech = True
        else:
            self._is_active_speech_turn = False
            has_speech = False

        # If assistant is speaking and audio matches echo, suppress speech flag unless barge-in confirmed
        if is_assistant_speaking and echo_sim > 0.55 and not is_interruption:
            has_speech = False
            raw_has_speech = False
            is_whisper = False

        int16_pcm = (cleaned_samples * 32767.0).astype(np.int16).tobytes()
        self._pre_roll_buffer.append(int16_pcm)

        return {
            "cleaned_pcm": int16_pcm,
            "has_speech": has_speech,
            "raw_speech": raw_has_speech,
            "is_whisper": is_whisper,
            "vad_confidence": vad_conf,
            "is_interruption": is_interruption,
            "echo_similarity": echo_sim,
            "rms_level": frame_rms,
            "gain_applied": self._current_gain,
        }
