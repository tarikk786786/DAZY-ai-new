"""core/response_planner.py — Structured emotional response planner for DAZY.

Coordinates language routing, emotion fusion, and response packaging into
a structured plan ready for synthesis.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from core.emotion_controller import EmotionController, EmotionState, EMOTIONS
from core.language_router import detect_language, normalize_hinglish


@dataclass
class ResponsePlan:
    response: str
    language: str = "hi-en"
    emotion: str = "neutral"
    intensity: float = 0.5
    delivery: str = "warm_conversational"
    pace: str = "natural"
    tts_engine: str = "higgs"

    def as_dict(self) -> dict[str, Any]:
        return {
            "response": self.response,
            "language": self.language,
            "emotion": self.emotion,
            "intensity": round(self.intensity, 2),
            "delivery": self.delivery,
            "pace": self.pace,
            "tts_engine": self.tts_engine,
        }


class ResponsePlanner:
    """Plans and structures DAZY's verbal response."""

    def __init__(self, emotion_controller: Optional[EmotionController] = None):
        self.emotion_controller = emotion_controller or EmotionController()

    def parse_raw_llm_output(self, raw_text: str, default_tts: str = "higgs") -> ResponsePlan:
        """Parses model response. If model returned structured JSON, extracts it;

        otherwise performs text emotion analysis and Hinglish normalization.
        """
        if not raw_text or not raw_text.strip():
            return ResponsePlan(response="", tts_engine=default_tts)

        clean = raw_text.strip()

        # Check for JSON code block or raw JSON
        json_candidate = None
        if "{" in clean and "}" in clean:
            start = clean.find("{")
            end = clean.rfind("}") + 1
            chunk = clean[start:end]
            try:
                data = json.loads(chunk)
                if isinstance(data, dict) and "response" in data:
                    json_candidate = data
            except Exception:
                pass

        if json_candidate:
            resp_text = str(json_candidate.get("response") or "").strip()
            emo = str(json_candidate.get("emotion") or "neutral").lower()
            if emo not in EMOTIONS:
                emo = "neutral"
            intensity = float(json_candidate.get("intensity") or 0.5)
            delivery = str(json_candidate.get("delivery") or "warm_conversational")
            lang = str(json_candidate.get("language") or detect_language(resp_text))
            pace = str(json_candidate.get("pace") or "natural")
            tts = str(json_candidate.get("tts_engine") or default_tts)

            normalized = normalize_hinglish(resp_text)
            return ResponsePlan(
                response=normalized,
                language=lang,
                emotion=emo,
                intensity=max(0.1, min(1.0, intensity)),
                delivery=delivery,
                pace=pace,
                tts_engine=tts
            )

        # Fallback: Plain text response from LLM
        # Run emotion analysis and language detection
        emo_state = self.emotion_controller.analyze_text(clean)
        lang = detect_language(clean)
        normalized = normalize_hinglish(clean)

        return ResponsePlan(
            response=normalized,
            language=lang,
            emotion=emo_state.primary,
            intensity=emo_state.intensity,
            delivery=emo_state.delivery,
            pace="natural",
            tts_engine=default_tts
        )

    def plan_response(
        self,
        text: str,
        user_input: str = "",
        tts_engine: str = "higgs"
    ) -> ResponsePlan:
        """Directly plans a response given response text and user context."""
        # Step emotion controller with user's input context
        if user_input:
            self.emotion_controller.step(user_input)

        plan = self.parse_raw_llm_output(text, default_tts=tts_engine)
        return plan
