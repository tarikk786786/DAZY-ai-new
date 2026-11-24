"""Dependency-free tests for the conversation/transcript helpers in main.py.

The complete desktop application imports audio, Qt and provider packages at module
load time. These tests extract only the small pure helper functions from the source
AST so the text-merging logic can be verified without opening the desktop app.
"""
from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "main.py"
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


class TranscriptMergeTests(unittest.TestCase):
    def test_exact_long_duplicate_event_is_ignored(self):
        chunks = []
        self.assertEqual(append_chunk(chunks, "Hello there."), "Hello there.")
        self.assertEqual(append_chunk(chunks, "Hello there."), "")
        self.assertEqual(join_chunks(chunks), "Hello there.")

    def test_phrase_boundary_overlap_is_removed(self):
        chunks = []
        append_chunk(chunks, "Hello there, how are you")
        self.assertEqual(append_chunk(chunks, "how are you today?"), "today?")
        self.assertEqual(join_chunks(chunks), "Hello there, how are you today?")

    def test_cumulative_transcript_event_adds_only_suffix(self):
        chunks = []
        append_chunk(chunks, "I am testing")
        self.assertEqual(append_chunk(chunks, "I am testing the voice today"), "the voice today")
        self.assertEqual(join_chunks(chunks), "I am testing the voice today")

    def test_short_natural_repetition_is_preserved(self):
        chunks = []
        append_chunk(chunks, "yes")
        self.assertEqual(append_chunk(chunks, "yes"), "yes")
        self.assertEqual(join_chunks(chunks), "yes yes")

    def test_hindi_devanagari_overlap_is_removed(self):
        chunks = []
        append_chunk(chunks, "मुझे यह समझ आया")
        self.assertEqual(append_chunk(chunks, "यह समझ आया अब"), "अब")
        self.assertEqual(join_chunks(chunks), "मुझे यह समझ आया अब")

    def test_hinglish_code_switching_is_preserved(self):
        chunks = []
        append_chunk(chunks, "Kal meeting hai, can you remind me")
        self.assertEqual(append_chunk(chunks, "can you remind me at 5 PM?"), "at 5 PM?")
        self.assertEqual(join_chunks(chunks), "Kal meeting hai, can you remind me at 5 PM?")

    def test_partial_overlap_keeps_new_sentence(self):
        chunks = []
        append_chunk(chunks, "I think this is useful.")
        self.assertEqual(
            append_chunk(chunks, "This is useful. Can we continue?"),
            "Can we continue?",
        )
        self.assertEqual(join_chunks(chunks), "I think this is useful. Can we continue?")

    def test_punctuation_spacing_is_normalized(self):
        chunks = []
        append_chunk(chunks, "Hello")
        append_chunk(chunks, ", world !")
        self.assertEqual(join_chunks(chunks), "Hello, world!")

    def test_transport_control_markers_removed_without_losing_multilingual_text(self):
        self.assertEqual(clean_transcript("<ctrl10> 你好  नमस्ते\x00"), "你好 नमस्ते")


class ConversationGuidanceTests(unittest.TestCase):
    def test_guidance_is_injected_into_live_system_instruction(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("_CONVERSATION_GUIDANCE", source)
        self.assertIn("parts.append(_CONVERSATION_GUIDANCE)", source)
        self.assertIn("fluent everyday Hinglish", source)
        self.assertIn("Resolve short follow-ups, pronouns and references", source)

    def test_default_assistant_identity_is_dazy_not_fictional_jarvis(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('self._asst_name     = "DAZY"', source)
        self.assertIn('or "DAZY"', source)
        self.assertNotIn("Tony Stark's AI assistant", source)

    def test_name_and_honorific_are_not_forced_on_every_reply(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("Do not assume a name, title or honorific", source)
        self.assertIn("Use it sparingly", source)
        self.assertNotIn('"sir" in English', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
