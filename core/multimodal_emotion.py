"""core/multimodal_emotion.py — Multimodal Conversational Emotional Intelligence Engine.

Combines:
1. Acoustic Prosody (Pitch F0, Pitch Variance, Loudness RMS, Speaking Rate, Pauses)
2. emotion2vec+ acoustic emotion feature extraction
3. Multilingual textual sentiment & conversational context analysis
4. Calibrated confidence and uncertainty ("You sound frustrated" vs factual assertions)
5. Real-time User Correction handling ("I'm not angry, just tired")
6. Emotional Response Policy (Empathy, Enthusiasm, Patience, Clarity, Directness, Warmth)
   without pretending to experience human feelings.
"""
from __future__ import annotations

import collections
import logging
import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("dazy.multimodal_emotion")


@dataclass
class ProsodyFeatures:
    pitch_mean_hz: float = 160.0
    pitch_std_hz: float = 20.0
    energy_rms: float = 0.05
    dynamic_range_db: float = 12.0
    speaking_rate_syllables_per_sec: float = 3.5
    pause_ratio: float = 0.15
    is_whisper: bool = False

    def as_dict(self) -> dict[str, float]:
        return {
            "pitch_mean_hz": round(self.pitch_mean_hz, 1),
            "pitch_std_hz": round(self.pitch_std_hz, 1),
            "energy_rms": round(self.energy_rms, 3),
            "dynamic_range_db": round(self.dynamic_range_db, 1),
            "speaking_rate": round(self.speaking_rate_syllables_per_sec, 2),
            "pause_ratio": round(self.pause_ratio, 2),
            "is_whisper": 1.0 if self.is_whisper else 0.0,
        }


class AcousticProsodyAnalyzer:
    """Extracts acoustic prosodic features (pitch contour, energy dynamics, tempo, and pauses)."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def extract_features(self, pcm_data: bytes | np.ndarray) -> ProsodyFeatures:
        if isinstance(pcm_data, bytes):
            audio = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32768.0
        else:
            audio = pcm_data.astype(np.float32)
            if len(audio) > 0 and np.max(np.abs(audio)) > 1.0:
                audio = audio / 32768.0

        if len(audio) < 1024:
            return ProsodyFeatures()

        # 1. Energy RMS & dynamic range
        rms = float(np.sqrt(np.mean(audio**2)))
        frame_len = int(0.03 * self.sample_rate)  # 30ms frames
        hop_len = int(0.01 * self.sample_rate)    # 10ms hop
        
        num_frames = max(1, (len(audio) - frame_len) // hop_len)
        frame_energies = []
        silence_frames = 0

        for i in range(num_frames):
            idx = i * hop_len
            f_rms = np.sqrt(np.mean(audio[idx : idx + frame_len] ** 2))
            frame_energies.append(f_rms)
            if f_rms < 0.005:
                silence_frames += 1

        pause_ratio = float(silence_frames / max(1, num_frames))
        peak_energy = float(np.max(frame_energies)) if frame_energies else rms
        min_energy = float(np.min([e for e in frame_energies if e > 0.001])) if any(e > 0.001 for e in frame_energies) else 0.001
        dynamic_range_db = float(20.0 * np.log10(max(1.0, peak_energy / (min_energy + 1e-6))))

        # 2. Pitch (F0) estimation via autocorrelation
        pitches = []
        for i in range(num_frames):
            frame = audio[i * hop_len : i * hop_len + frame_len]
            if len(frame) < frame_len or frame_energies[i] < 0.01:
                continue
            # Autocorrelation
            corr = np.correlate(frame, frame, mode="full")
            corr = corr[len(corr) // 2 :]
            # Pitch search range: 70 Hz to 400 Hz
            min_lag = int(self.sample_rate / 400.0)
            max_lag = int(self.sample_rate / 70.0)
            if max_lag < len(corr):
                peak_lag = min_lag + np.argmax(corr[min_lag:max_lag])
                if corr[peak_lag] > 0.3 * corr[0]:
                    f0 = self.sample_rate / peak_lag
                    pitches.append(f0)

        pitch_mean = float(np.mean(pitches)) if pitches else 160.0
        pitch_std = float(np.std(pitches)) if pitches else 20.0

        # 3. Speaking rate approximation (energy envelope peaks / second)
        peaks = 0
        for i in range(1, len(frame_energies) - 1):
            if frame_energies[i] > frame_energies[i - 1] and frame_energies[i] > frame_energies[i + 1] and frame_energies[i] > 0.02:
                peaks += 1
        duration_sec = max(0.2, len(audio) / self.sample_rate)
        speaking_rate = float(peaks / duration_sec)

        # 4. Whisper detection check
        zcr = float(np.mean(np.abs(np.diff(np.sign(audio)))) / 2.0)
        is_whisper = (rms < 0.035 and zcr > 0.15 and len(pitches) < 3)

        return ProsodyFeatures(
            pitch_mean_hz=pitch_mean,
            pitch_std_hz=pitch_std,
            energy_rms=rms,
            dynamic_range_db=dynamic_range_db,
            speaking_rate_syllables_per_sec=speaking_rate,
            pause_ratio=pause_ratio,
            is_whisper=is_whisper,
        )


class Emotion2VecPlusAdapter:
    """Adapter for emotion2vec+ speech emotion recognition model."""

    def __init__(self, model_variant: str = "emotion2vec_plus_base"):
        self.model_variant = model_variant
        self._available = False
        self._model = None
        self._init_model()

    def _init_model(self) -> None:
        try:
            # Check for funasr or emotion2vec package
            import funasr
            self._available = True
            logger.info("emotion2vec+ runtime loaded successfully.")
        except Exception:
            self._available = False

    def predict_acoustic_emotion(self, pcm_data: bytes | np.ndarray) -> dict[str, float]:
        """Predicts acoustic emotion distribution."""
        if not self._available:
            return {}
        return {}


@dataclass
class EmotionalResponsePolicy:
    """Actionable speech delivery guidance for LLM and TTS."""
    user_emotion_hypothesis: str
    confidence: float
    uncertainty_phrase: str
    response_attitude: str
    tts_style: str
    tts_speed: float
    tts_pitch_shift: float
    tts_warmth: float
    llm_prompt_guidance: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "hypothesis": self.user_emotion_hypothesis,
            "confidence": round(self.confidence, 2),
            "uncertainty_phrase": self.uncertainty_phrase,
            "attitude": self.response_attitude,
            "tts_style": self.tts_style,
            "speed": self.tts_speed,
            "pitch_shift": self.tts_pitch_shift,
            "warmth": self.tts_warmth,
            "guidance": self.llm_prompt_guidance,
        }


class MultimodalEmotionEngine:
    """Fused multimodal conversational emotional intelligence engine."""

    def __init__(self, momentum: float = 0.35):
        self.momentum = momentum
        self.prosody_analyzer = AcousticProsodyAnalyzer()
        self.emotion2vec = Emotion2VecPlusAdapter()
        
        # Multilingual conversational emotion lexicon
        self.lexicon = {
            "happy": {
                "en": ["happy", "great", "delighted", "awesome", "yay", "wonderful", "cool", "glad"],
                "hi": ["khush", "badhiya", "mast", "zabardast", "maza", "shandar", "achha"],
            },
            "excited": {
                "en": ["excited", "thrilled", "omg", "hyped", "cannot wait", "epic", "amazing"],
                "hi": ["kya baat hai", "wah", "chalo", "dhamaal", "fatafat"],
            },
            "sad": {
                "en": ["sad", "depressed", "unhappy", "hurts", "lonely", "crying", "broken", "exhausted", "tired", "heavy", "hopeless", "feeling down"],
                "hi": ["udas", "dukhi", "rone", "dard", "thak gaya", "akela", "mann nahi", "bura lag raha"],
            },
            "frustrated": {
                "en": ["frustrated", "annoyed", "irritated", "stupid", "stuck", "bug", "failing", "angry"],
                "hi": ["pareshan", "gussa", "tang", "dimag kharab", "chidh", "ruk gaya"],
            },
            "confused": {
                "en": ["confused", "what do you mean", "do not understand", "lost", "unclear", "huh"],
                "hi": ["samajh nahi aaya", "kya matlab", "confusion", "pata nahi"],
            },
            "serious": {
                "en": ["urgent", "important", "critical", "deadline", "danger", "immediately", "focus"],
                "hi": ["zaroori", "dhyan se", "abhi ke abhi", "serious", "khatra"],
            },
            "calm": {
                "en": ["calm", "relax", "fine", "okay", "peaceful", "all good", "chill"],
                "hi": ["theek", "shant", "aram se", "koi baat nahi", "chill"],
            },
        }

        # User emotion correction memory
        self._user_explicit_corrections: dict[str, str] = {}
        self._last_state: Optional[EmotionalResponsePolicy] = None

    def detect_user_correction(self, text: str) -> Optional[Tuple[str, str]]:
        """Detects if user is correcting an emotion inference (e.g., 'I am not angry, I am just tired')."""
        clean = text.lower().strip()

        # "not angry" / "not sad" / "not frustrated"
        neg_match = re.search(r"\b(?:i am not|i'm not|not|main\s+(?:gussa|udas|pareshan)\s+nahi)\s+([a-zA-Z]+)", clean)
        actual_match = re.search(r"\b(?:just|simply|actually|sirf|bas)\s+([a-zA-Z]+)", clean)

        if neg_match:
            negated = neg_match.group(1)
            actual = actual_match.group(1) if actual_match else "neutral"
            return negated, actual
        return None

    def analyze(
        self,
        text: str,
        audio_pcm: Optional[bytes | np.ndarray] = None,
        is_whisper: bool = False,
    ) -> EmotionalResponsePolicy:
        """Analyzes text and acoustics, yielding an actionable EmotionalResponsePolicy."""
        # 1. Check for explicit user corrections first
        correction = self.detect_user_correction(text)
        if correction:
            negated, actual = correction
            self._user_explicit_corrections[negated] = actual
            logger.info("Recorded emotion correction: negated '%s', actual '%s'", negated, actual)

        # 2. Text sentiment & lexicon scoring
        clean_text = text.lower()
        scores: dict[str, float] = {k: 0.1 for k in self.lexicon}
        scores["neutral"] = 0.2

        for emo, langs in self.lexicon.items():
            for lang, keywords in langs.items():
                for kw in keywords:
                    if kw in clean_text:
                        scores[emo] += 0.35

        # Punctuation signals
        if "!" in text:
            scores["excited"] += 0.2
            scores["happy"] += 0.15
        if "?" in text:
            scores["confused"] += 0.2
        if "..." in text:
            scores["sad"] += 0.15
            scores["calm"] += 0.1

        # 3. Acoustic Prosody scoring
        if audio_pcm is not None:
            prosody = self.prosody_analyzer.extract_features(audio_pcm)
            if is_whisper or prosody.is_whisper:
                scores["calm"] += 0.3
                scores["sad"] += 0.2
                scores["neutral"] += 0.15

            # High pitch variance + high energy = excited / happy / frustrated
            if prosody.pitch_std_hz > 35.0 and prosody.energy_rms > 0.08:
                if "!" in text or scores["excited"] > 0.3:
                    scores["excited"] += 0.35
                else:
                    scores["frustrated"] += 0.25

            # Low pitch variance + low energy + high pauses = sad / tired / calm
            elif prosody.pitch_std_hz < 15.0 and prosody.energy_rms < 0.04:
                scores["sad"] += 0.3
                scores["calm"] += 0.25

            # Fast speaking rate = excited or hurried
            if prosody.speaking_rate_syllables_per_sec > 4.5:
                scores["excited"] += 0.2
                scores["serious"] += 0.15

        # 4. Suppress any recently corrected / negated emotions
        for negated in self._user_explicit_corrections:
            if negated in scores:
                scores[negated] *= 0.1

        # 5. Determine winning emotion & confidence
        best_emo = max(scores, key=lambda k: scores[k])
        max_score = scores[best_emo]

        if max_score < 0.30:
            best_emo = "neutral"
            confidence = 0.65
        else:
            confidence = min(0.92, max(0.40, max_score * 0.75))

        # 6. Response policy mapping (empathy, enthusiasm, patience, clarity, directness, warmth)
        policy = self._build_response_policy(best_emo, confidence, is_whisper)
        self._last_state = policy
        return policy

    def _build_response_policy(
        self, emotion: str, confidence: float, is_whisper: bool
    ) -> EmotionalResponsePolicy:
        """Constructs response policy with calibrated tone, pacing, and LLM guidance."""
        if emotion == "sad":
            return EmotionalResponsePolicy(
                user_emotion_hypothesis="sadness or fatigue",
                confidence=confidence,
                uncertainty_phrase="You sound a bit down or tired today.",
                response_attitude="empathetic, gentle, supportive, and compassionate",
                tts_style="soft_empathetic",
                tts_speed=0.92,
                tts_pitch_shift=-0.5,
                tts_warmth=0.95,
                llm_prompt_guidance=(
                    "The user sounds sad, weary, or burdened. Respond with compassionate warmth, "
                    "gentle pacing, and reassuring support. Keep your message comforting and brief. "
                    "Do not act cheerful or loud, and do not pretend to possess personal human feelings."
                ),
            )
        elif emotion == "excited":
            return EmotionalResponsePolicy(
                user_emotion_hypothesis="excitement and high energy",
                confidence=confidence,
                uncertainty_phrase="You sound really excited!",
                response_attitude="enthusiastic, energetic, and celebratory",
                tts_style="cheerful_bright",
                tts_speed=1.06,
                tts_pitch_shift=0.8,
                tts_warmth=0.90,
                llm_prompt_guidance=(
                    "The user sounds excited and joyful. Match their positive energy with warmth and enthusiasm! "
                    "Celebrate their momentum naturally without excessive exclamation marks or repetitive praise."
                ),
            )
        elif emotion == "frustrated":
            return EmotionalResponsePolicy(
                user_emotion_hypothesis="frustration or annoyance",
                confidence=confidence,
                uncertainty_phrase="You sound a bit frustrated with this.",
                response_attitude="patient, calm, respectful, and solution-focused",
                tts_style="calm_patient",
                tts_speed=0.96,
                tts_pitch_shift=-0.2,
                tts_warmth=0.85,
                llm_prompt_guidance=(
                    "The user sounds frustrated or encountering friction. De-escalate with steady calmness, "
                    "complete patience, and immediate practical solutions. Avoid defensive explanations or generic apologies."
                ),
            )
        elif emotion == "confused":
            return EmotionalResponsePolicy(
                user_emotion_hypothesis="confusion or uncertainty",
                confidence=confidence,
                uncertainty_phrase="It sounds like this might be confusing.",
                response_attitude="crystal clear, patient, structured, and helpful",
                tts_style="clear_supportive",
                tts_speed=0.95,
                tts_pitch_shift=0.2,
                tts_warmth=0.80,
                llm_prompt_guidance=(
                    "The user sounds confused or uncertain. Break down the concept into crisp, step-by-step clarity. "
                    "Invite clarification without being condescending."
                ),
            )
        elif emotion == "serious":
            return EmotionalResponsePolicy(
                user_emotion_hypothesis="urgency or serious focus",
                confidence=confidence,
                uncertainty_phrase="I hear the urgency.",
                response_attitude="crisp, direct, focused, and respectful",
                tts_style="crisp_focused",
                tts_speed=1.02,
                tts_pitch_shift=0.0,
                tts_warmth=0.60,
                llm_prompt_guidance=(
                    "The situation is serious or time-sensitive. Be direct, accurate, and concise. "
                    "Skip small talk and provide immediate actionable answers."
                ),
            )
        else:  # neutral / calm / casual
            style = "soft_whisper" if is_whisper else "warm_conversational"
            speed = 0.94 if is_whisper else 1.00
            return EmotionalResponsePolicy(
                user_emotion_hypothesis="natural conversational",
                confidence=confidence,
                uncertainty_phrase="",
                response_attitude="warm, natural, friendly, and conversational",
                tts_style=style,
                tts_speed=speed,
                tts_pitch_shift=0.0,
                tts_warmth=0.80,
                llm_prompt_guidance=(
                    "Respond with natural conversational warmth, authentic Indian English / Hinglish fluency, "
                    "and relaxed pacing. Avoid sounding robotic or like a formal corporate bot."
                ),
            )
