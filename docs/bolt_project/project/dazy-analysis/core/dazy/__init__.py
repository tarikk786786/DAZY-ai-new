"""core/dazy/ — Core DAZY Intelligence Subsystem.

Houses:
- persona: DAZY identity, warmth, and prompt generation
- emotion_controller: Multilingual emotion tracking, analysis, and fusion
- language_router: Hinglish normalizer and code-switching detection
- response_planner: Structured emotion and delivery response packaging
- voice_style: TTS voice adapter for Svara, DhVaani, Higgs, and Piper
"""
from .persona import build_dazy_system_prompt, load_dazy_config, save_dazy_config
from .emotion_controller import EmotionController, EmotionState, EMOTIONS
from .language_router import detect_language, normalize_hinglish
from .response_planner import ResponsePlanner, ResponsePlan
from .voice_style import (
    format_for_svara, format_for_dhvaani, format_for_higgs, format_for_piper,
    SVARA_EMOTION_MAP, DHVAANI_STYLE_MAP, HIGGS_EMOTION_MAP
)

__all__ = [
    "build_dazy_system_prompt",
    "load_dazy_config",
    "save_dazy_config",
    "EmotionController",
    "EmotionState",
    "EMOTIONS",
    "detect_language",
    "normalize_hinglish",
    "ResponsePlanner",
    "ResponsePlan",
    "format_for_svara",
    "format_for_dhvaani",
    "format_for_higgs",
    "format_for_piper",
    "SVARA_EMOTION_MAP",
    "DHVAANI_STYLE_MAP",
    "HIGGS_EMOTION_MAP",
]
