"""Unit tests for DAZY emotion controller, decay, and state transitions."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.emotion_controller import EmotionController, EmotionState, EMOTIONS


def test_emotion_lexicon_detection():
    ctrl = EmotionController()
    
    # Affection in Hinglish
    state_aff = ctrl.analyze_text("Shukriya yaar, tum bohot pyari ho aur mera bohot khayal rakhti ho.")
    assert state_aff.primary == "affection"
    assert state_aff.intensity >= 0.4

    # Happy in Hindi / English
    state_happy = ctrl.analyze_text("Yeh toh bohot mast aur zabardast news hai, I am so happy!")
    assert state_happy.primary in ("happy", "excited")

    # Playful / Masti
    state_play = ctrl.analyze_text("Arrey chup karo, itna mazaak aur masti mat karo!")
    assert state_play.primary == "playful"

    # Serious / Emergency
    state_ser = ctrl.analyze_text("This is an urgent and critical error, fix it immediately!")
    assert state_ser.primary == "serious"

    # Urdu empathy / tasalli
    state_emp = ctrl.analyze_text("Afsos mat karein, sab theek ho jayega, hosla rakhein.")
    assert state_emp.primary in ("empathetic", "sad")


def test_emotion_momentum_decay():
    ctrl = EmotionController(momentum=0.4)
    # Set excited state
    ctrl.step("Wow, this is totally epic and amazing!")
    assert ctrl.current_state.primary in ("excited", "happy")
    prev_emo = ctrl.current_state.primary
    prev_intensity = ctrl.current_state.intensity

    # Send neutral follow up; should decay smoothly, not abruptly vanish
    ctrl.step("Okay.")
    assert ctrl.current_state.primary == prev_emo
    assert ctrl.current_state.intensity < prev_intensity


def test_acoustic_feature_fusion():
    ctrl = EmotionController()
    state = ctrl.step("Hello", audio_features={"excited": 0.4})
    assert state.scores.get("excited", 0) > 0.3
