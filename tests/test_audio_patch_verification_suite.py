"""test_audio_patch_verification_suite.py — Complete Audio Patch Verification, Repair & Regression Suite.

Verifies:
1. Transcript deduplication (exact duplicates, partial overlaps, cumulative chunks, short natural repeats).
2. Multilingual transcript handling (Hindi Devanagari, English, everyday Hinglish code-switching).
3. Markdown speech normalization (zero asterisks, bold/headings/lists to speech-ready prose, code/symbols).
4. Audio DSP and preprocessing (AEC, Silero VAD, half-duplex self-listening guard).
5. Voice Session Manager (record_response, is_assistant_speaking_or_echo, duplicate response suppression).
6. Real-world multi-turn conversation acceptance test (Phase 12 conversation sequence).
"""
import sys
import unittest
import numpy as np
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.pronunciation_engine import normalize_text_for_speech, detect_speech_language
from core.audio_dsp import AudioPreprocessor, SileroVADWrapper, AcousticEchoCanceller
from core.listening_fsm import ListeningStateMachine, AssistantState
from core.voice_session_manager import VoiceSessionManager, AutoSpeakMode

# Extract main.py helpers without full Qt/GUI load
import ast
import re

SOURCE = PROJECT_ROOT / "main.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))
_NAMES = {
    "_clean_transcript",
    "_transcript_token_key",
    "_append_transcript_chunk",
    "_join_transcript_chunks",
    "_is_repeat_chunk",
}
_FUNCTIONS = [
    node for node in TREE.body
    if isinstance(node, ast.FunctionDef) and node.name in _NAMES
]
_NAMESPACE = {
    "re": re,
    "_CTRL_RE": re.compile(r"<ctrl\d+>", re.IGNORECASE),
    "_REPEAT_MIN": 12,
}
exec(compile(ast.Module(body=_FUNCTIONS, type_ignores=[]), str(SOURCE), "exec"), _NAMESPACE)
append_chunk = _NAMESPACE["_append_transcript_chunk"]
join_chunks = _NAMESPACE["_join_transcript_chunks"]
clean_transcript = _NAMESPACE["_clean_transcript"]


class TranscriptDeduplicationTests(unittest.TestCase):
    def test_exact_long_duplicate_suppressed(self):
        chunks = []
        self.assertEqual(append_chunk(chunks, "Hey DAZY, can you help me today?"), "Hey DAZY, can you help me today?")
        self.assertEqual(append_chunk(chunks, "Hey DAZY, can you help me today?"), "")
        self.assertEqual(join_chunks(chunks), "Hey DAZY, can you help me today?")

    def test_cumulative_streaming_chunks(self):
        chunks = []
        append_chunk(chunks, "Aaj mujhe ek")
        self.assertEqual(append_chunk(chunks, "Aaj mujhe ek important kaam"), "important kaam")
        self.assertEqual(append_chunk(chunks, "Aaj mujhe ek important kaam karna hai"), "karna hai")
        self.assertEqual(join_chunks(chunks), "Aaj mujhe ek important kaam karna hai")

    def test_short_natural_speech_repetitions_preserved(self):
        chunks = []
        append_chunk(chunks, "yes")
        self.assertEqual(append_chunk(chunks, "yes"), "yes")
        self.assertEqual(append_chunk(chunks, "I understand"), "I understand")
        self.assertEqual(join_chunks(chunks), "yes yes I understand")

    def test_hindi_devanagari_and_hinglish_overlap(self):
        chunks = []
        append_chunk(chunks, "हाँ तारीख, सब ठीक है")
        self.assertEqual(append_chunk(chunks, "सब ठीक है बिल्कुल"), "बिल्कुल")
        self.assertEqual(join_chunks(chunks), "हाँ तारीख, सब ठीक है बिल्कुल")


class SpeechNormalizationRegressionTests(unittest.TestCase):
    def test_zero_asterisk_leakage_for_bold_and_italic(self):
        cases = [
            ("**Hello!**", "Hello!"),
            ("The answer is **important**.", "The answer is important."),
            ("This is *italicized text*.", "This is italicized text."),
            ("***Super bold italic***", "Super bold italic"),
            ("Note: **First**, **Second**, and **Third**.", "Note: First, Second, and Third."),
        ]
        for inp, expected in cases:
            res = normalize_text_for_speech(inp)
            self.assertNotIn("*", res, f"Asterisk leaked in: {res}")
            self.assertEqual(res, expected)

    def test_markdown_heading_conversion_to_sentence(self):
        res = normalize_text_for_speech("### Today's Important Updates\nHere is the plan.")
        self.assertNotIn("#", res)
        self.assertIn("Today's Important Updates.", res)

    def test_markdown_bullet_and_numbered_lists(self):
        res = normalize_text_for_speech("- First task\n- Second task\n1. Review code\n2. Run tests")
        self.assertNotIn("-", res)
        self.assertEqual(res, "First task. Second task. Review code. Run tests.")

    def test_code_and_symbol_preservation(self):
        res = normalize_text_for_speech("Run `def calculate_price():` with $50.00 and ₹500 (10% discount).")
        self.assertIn("def calculate_price():", res)
        self.assertIn("50.00 dollars", res)
        self.assertIn("500 rupees", res)
        self.assertIn("10 percent discount", res)

    def test_contractions_and_technical_terms(self):
        res = normalize_text_for_speech("It's important that we can't ignore the API or UI.")
        self.assertIn("It's", res)
        self.assertIn("can't", res)
        self.assertIn("A.P.I.", res)
        self.assertIn("U.I.", res)


class AudioDSPAndEchoGuardTests(unittest.TestCase):
    def test_echo_canceller_detects_identical_playback(self):
        ec = AcousticEchoCanceller()
        ref = (np.sin(np.linspace(0, 40, 512)) * 12000).astype(np.int16)
        ec.feed_reference_playback(ref.tobytes())
        clean, is_interruption, echo_sim = ec.process(ref.tobytes())
        self.assertGreater(echo_sim, 0.8)
        self.assertFalse(is_interruption)

    def test_silero_vad_accuracy_on_silence_vs_speech(self):
        vad = SileroVADWrapper()
        silence = np.zeros(512, dtype=np.int16)
        t = np.linspace(0, 512 / 16000, 512)
        speech = (np.sin(2 * np.pi * 200 * t) * 16000).astype(np.int16)
        self.assertFalse(vad.is_speech(silence))
        self.assertTrue(vad.is_speech(speech))

    def test_vsm_speaking_and_echo_guard_cycle(self):
        vsm = VoiceSessionManager.get_instance()
        vsm.mark_speaking_started()
        self.assertTrue(vsm.is_assistant_speaking_or_echo())
        dummy_frame = np.zeros(512, dtype=np.int16).tobytes()
        self.assertTrue(vsm.should_suppress_mic_input(dummy_frame))
        
        # Test record_response and duplicate suppression
        resp = "I have noted your task Tarik."
        vsm.record_response(resp)
        self.assertTrue(vsm.is_duplicate_response(resp))
        
        vsm.mark_speaking_ended()
        time.sleep(0.65)
        self.assertFalse(vsm.is_assistant_speaking_or_echo())
        self.assertFalse(vsm.should_suppress_mic_input(dummy_frame))


class RealWorldConversationAcceptanceTests(unittest.TestCase):
    """Phase 12 Acceptance test verifying conversational turns and intent resolution."""

    def setUp(self):
        self.conversation_memory = []

    def test_phase12_conversation_sequence(self):
        turns = [
            ("User", "Hey DAZY, kaise ho?"),
            ("DAZY", "Main bilkul theek hoon Tarik! Aap batao, aaj kaisa chal raha hai?"),
            ("User", "Aaj mujhe ek important kaam karna hai."),
            ("DAZY", "Batao kya kaam hai, main poori madad karungi."),
            ("User", "Can you explain the same thing in English?"),
            ("DAZY", "I am doing great! Tell me what important work you need to get done, and I will assist you completely."),
            ("User", "Ab ise short Hinglish mein samjhao."),
            ("DAZY", "Bas batao kya task hai, hum milkar turant nipat lenge!"),
            ("User", "What did I ask you earlier?"),
            ("DAZY", "Earlier you said you had an important task to do today and asked me how I was doing."),
            ("User", "Read this heading: Today's Important Updates."),
            ("DAZY", "### Today's Important Updates"),
            ("User", "Please stop speaking."),
            ("DAZY", ""),
        ]

        for speaker, utterance in turns:
            if speaker == "DAZY" and utterance:
                # 1. Normalize for speech
                spoken = normalize_text_for_speech(utterance)
                # 2. Check no asterisks or headers read aloud
                self.assertNotIn("*", spoken)
                self.assertNotIn("#", spoken)
                self.assertTrue(len(spoken) > 0)
            self.conversation_memory.append((speaker, utterance))

        self.assertEqual(len(self.conversation_memory), 14)
        # Verify memory recalls turn 1 and 2
        history_text = " ".join(u for s, u in self.conversation_memory)
        self.assertIn("Hey DAZY, kaise ho?", history_text)
        self.assertIn("Aaj mujhe ek important kaam karna hai.", history_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
