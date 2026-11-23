"""Unit tests for DAZY structured response planning."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.response_planner import ResponsePlanner, ResponsePlan


def test_response_planner_json():
    planner = ResponsePlanner()
    raw_json = '{"language": "hi-en", "emotion": "affection", "intensity": 0.6, "delivery": "warm_conversational", "response": "Haan bolo, main sun rahi hoon.", "tts_engine": "higgs"}'
    plan = planner.parse_raw_llm_output(raw_json)
    assert plan.emotion == "affection"
    assert plan.intensity == 0.6
    assert "main sun rahi hoon" in plan.response
    assert plan.tts_engine == "higgs"


def test_response_planner_plain_text():
    planner = ResponsePlanner()
    raw_text = "Yeh toh bohot mast idea hai, let's do it right now!"
    plan = planner.parse_raw_llm_output(raw_text)
    assert plan.emotion in ("excited", "happy", "playful")
    assert "mast" in plan.response
