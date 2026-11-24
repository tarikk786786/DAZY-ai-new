"""core/emotion_controller.py — Emotion analysis, tracking, and fusion for DAZY.

Classifies emotional states from textual, contextual, and acoustic features,
producing validated emotional states and intensities for expressive voice synthesis.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

EMOTIONS = (
    "neutral",
    "affection",
    "happy",
    "playful",
    "empathetic",
    "curious",
    "excited",
    "sad",
    "serious",
    "confident",
)

# Multilingual keywords and cues for emotion scoring across English, Hindi, Hinglish & Urdu
_EMOTION_LEXICON: dict[str, dict[str, list[str]]] = {
    "affection": {
        "en": ["love", "dear", "care", "sweet", "miss you", "precious", "darling", "adore", "heart"],
        "hi_hinglish": ["pyaar", "mohabbat", "khayal", "apna", "shukriya", "pyara", "pyari", "pyare", "sweet", "meri jaan", "yaad"],
        "ur": ["mohabbat", "ishq", "ulfat", "pyar", "inayat", "nawazish", "kareeb", "dillagi"]
    },
    "happy": {
        "en": ["happy", "glad", "great", "wonderful", "awesome", "good", "delighted", "yay", "smile"],
        "hi_hinglish": ["khush", "badhiya", "mast", "maza", "zabardast", "acha", "bohot acha", "badhaai"],
        "ur": ["khush", "musarrat", "shadaab", "mubarak", "lutf", "rahat"]
    },
    "playful": {
        "en": ["tease", "joke", "funny", "haha", "lol", "kidding", "silly", "wink", "mischief"],
        "hi_hinglish": ["masti", "mazaak", "chhedna", "pagal", "chup", "naughty", "dramebaaz", "hasna"],
        "ur": ["shokhi", "mazaq", "shokh", "chhed", "muskurahat", "shararat"]
    },
    "empathetic": {
        "en": ["sorry", "understand", "feel you", "here for you", "hard", "tough", "take care", "breathe"],
        "hi_hinglish": ["samajh sakti hoon", "koi baat nahi", "fikr mat karo", "chinta mat karo", "dhyan rakho", "sab theek ho jayega"],
        "ur": ["ghamzada", "tasalli", "saboor", "dard", "afsos", "fikr na karein", "hosla"]
    },
    "curious": {
        "en": ["why", "how", "what", "curious", "wonder", "really?", "tell me more", "explain", "interesting"],
        "hi_hinglish": ["kyun", "kaise", "kya", "sach me", "aur batao", "jan-na", "kya baat hai"],
        "ur": ["kyun", "kaise", "maloomat", "tajassus", "haqeeqat", "bataiye"]
    },
    "excited": {
        "en": ["omg", "wow", "amazing", "let's go", "cannot wait", "thrilled", "epic", "hyped"],
        "hi_hinglish": ["kya baat hai", "wah", "chalo", "zabardast", "jaldi", "dhamaal", "fatafat"],
        "ur": ["subhanallah", "khoob", "zabardast", "josh", "walwala"]
    },
    "sad": {
        "en": ["sad", "unhappy", "depressed", "lonely", "crying", "hurt", "broke", "tired", "down"],
        "hi_hinglish": ["udas", "dukhi", "rone", "dard", "thak gaya", "akela", "mann nahi hai", "bura lag raha"],
        "ur": ["udas", "ranj", "gham", "mayoos", "tanhai", "dard", "pareshan"]
    },
    "serious": {
        "en": ["urgent", "important", "critical", "focus", "immediately", "deadline", "careful", "error", "fail"],
        "hi_hinglish": ["zaroori", "dhyan se", "abhi ke abhi", "serious", "problem", "kharaab", "jaldi karo"],
        "ur": ["zaroori", "sanjeeda", "khatra", "fauri", "tavajjoh", "hushyar"]
    },
    "confident": {
        "en": ["sure", "definitely", "absolutely", "easy", "done", "got this", "trust me", "no problem"],
        "hi_hinglish": ["pakka", "bilkul", "ho jayega", "chinta mat lo", "aasaani se", "main hoon na"],
        "ur": ["yaqeen", "laazmi", "bilkul", "itmenan", "koi masla nahi"]
    }
}


@dataclass
class EmotionState:
    primary: str = "neutral"
    intensity: float = 0.5        # 0.0 to 1.0
    confidence: float = 0.8
    scores: dict[str, float] = field(default_factory=dict)
    delivery: str = "warm_conversational"

    def as_dict(self) -> dict[str, Any]:
        return {
            "emotion": self.primary,
            "intensity": round(self.intensity, 2),
            "confidence": round(self.confidence, 2),
            "delivery": self.delivery,
            "scores": {k: round(v, 2) for k, v in self.scores.items() if v > 0.05}
        }


class EmotionController:
    """Tracks and fuses multi-turn conversational emotion for DAZY."""

    def __init__(self, momentum: float = 0.35):
        self.momentum = max(0.0, min(0.9, momentum))
        self.current_state = EmotionState(primary="neutral", intensity=0.5, confidence=0.7)
        self.history: list[EmotionState] = []

    def analyze_text(self, text: str) -> EmotionState:
        """Classifies emotion from utterance text using multilingual lexicons and patterns."""
        if not text or not text.strip():
            return EmotionState(primary="neutral", intensity=0.3, confidence=0.5)

        clean = text.lower()
        scores: dict[str, float] = {e: 0.0 for e in EMOTIONS}
        scores["neutral"] = 0.15   # base neutral prior

        # Lexicon pattern matching
        for emo, lang_dict in _EMOTION_LEXICON.items():
            for lang, keywords in lang_dict.items():
                for kw in keywords:
                    if " " in kw:
                        if kw in clean:
                            scores[emo] += 0.4
                    else:
                        # word boundary matching
                        if re.search(r"\b" + re.escape(kw) + r"\b", clean):
                            scores[emo] += 0.25

        # Punctuation & casing signals
        if "!" in text:
            scores["excited"] += 0.2
            scores["happy"] += 0.1
        if "?" in text:
            scores["curious"] += 0.25
        if text.isupper() and len(text) > 4:
            scores["serious"] += 0.3
            scores["excited"] += 0.2

        # Find maximum scored emotion
        best_emo = max(scores, key=lambda k: scores[k])
        max_score = scores[best_emo]

        if max_score < 0.25:
            best_emo = "neutral"
            intensity = 0.4
            confidence = 0.6
        else:
            intensity = min(1.0, max(0.35, max_score * 0.8))
            confidence = min(0.95, 0.5 + (max_score * 0.3))

        # Delivery style mapping
        delivery_map = {
            "neutral": "conversational",
            "affection": "warm_gentle",
            "happy": "cheerful_bright",
            "playful": "teasing_lively",
            "empathetic": "gentle_reassuring",
            "curious": "attentive_inquisitive",
            "excited": "energetic_enthusiastic",
            "sad": "soft_sympathetic",
            "serious": "crisp_focused",
            "confident": "assured_firm"
        }

        return EmotionState(
            primary=best_emo,
            intensity=intensity,
            confidence=confidence,
            scores=scores,
            delivery=delivery_map.get(best_emo, "conversational")
        )

    def analyze_acoustics(self, pcm_samples: Optional[list[float]] = None, energy: Optional[float] = None) -> dict[str, float]:
        """Heuristic acoustic analysis (pitch/energy/tempo variance) when raw audio is provided."""
        acoustic_bias: dict[str, float] = {}
        if energy is not None:
            if energy > 0.3:
                acoustic_bias["excited"] = 0.3
                acoustic_bias["happy"] = 0.2
            elif energy < 0.05:
                acoustic_bias["sad"] = 0.25
                acoustic_bias["empathetic"] = 0.2
                acoustic_bias["neutral"] = 0.15
        return acoustic_bias

    def step(self, user_text: str, audio_features: Optional[dict] = None) -> EmotionState:
        """Fuses text, acoustic features, and previous emotional momentum into the active state."""
        new_text_state = self.analyze_text(user_text)

        # Apply acoustic adjustments
        if audio_features:
            for emo, boost in audio_features.items():
                if emo in new_text_state.scores:
                    new_text_state.scores[emo] += boost

        # Smooth transition with conversation momentum
        if self.current_state and self.current_state.primary != "neutral":
            # If incoming is neutral, decay previous emotion gently rather than snapping
            if new_text_state.primary == "neutral":
                decayed_intensity = self.current_state.intensity * (1.0 - self.momentum)
                if decayed_intensity > 0.25:
                    new_text_state.primary = self.current_state.primary
                    new_text_state.intensity = decayed_intensity
                    new_text_state.delivery = self.current_state.delivery
                    new_text_state.confidence = 0.65

        self.history.append(self.current_state)
        if len(self.history) > 20:
            self.history.pop(0)

        self.current_state = new_text_state
        return self.current_state
