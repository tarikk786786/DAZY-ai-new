"""tests/test_speech_evaluation_suite.py — 50-Sentence Hindi, Hinglish & English Speech Quality Suite.

Tests speech normalization, language detection, pronunciation consistency,
emotion tag stripping, emoji removal, and absence of stutter markers.
"""
import pytest
from core.pronunciation_engine import PronunciationEngine, normalize_text_for_speech, detect_speech_language


TEST_SUITE_50_SENTENCES = [
    # ── Mandatory 6 Sentences ────────────────────────────────────────────────
    "Hey Tarik, main aapki settings check kar rahi hoon.",
    "Aapka system bilkul smooth chal raha hai, koi issue nahi hai.",
    "Maine backup create kar diya hai, don't worry.",
    "Python script run ho chuki hai and saare tests pass ho gaye.",
    "Aaj ka schedule kaafi busy hai, kya hum meetings review karein?",
    "Tarik, aapka database connect ho gaya hai.",

    # ── Technical & Hinglish Inquiries ───────────────────────────────────────
    "Server port 8080 par active hai aur dashboard ready hai.",
    "Tarik, maine naya API token securely store kar diya hai.",
    "Aapka CPU usage 15% hai aur RAM bilkul free hai.",
    "Humne UI components ko optimize kar diya hai for 60 FPS animation.",
    "Database migration complete ho gaya hai, zero errors found.",
    "Kya aap chahte hain ki main background worker restart karun?",
    "WebSocket connection establish ho chuka hai, real-time telemetry live hai.",
    "Tarik, aapke 154 unit tests pass ho chuke hain successfully.",
    "Git repository clean hai, ready for commit and push.",
    "Audio buffer sample rate 24 kHz par configure ho gaya hai.",

    # ── Number, Currency & Time Normalization ────────────────────────────────
    "Meeting subah 10:30 AM par scheduled hai Google Meet par.",
    "Evening status call 5:00 PM par start hogi.",
    "Total balance ₹5000 hai aur monthly subscription $50 hai.",
    "Har ek batch 100% complete ho chuka hai.",
    "Aapko Rs. 1500 ka refund receive ho gaya hai.",
    "Battery level 85% par hai aur Wi-Fi signal strong hai.",
    "File download size 250 MB hai aur available storage 120 GB hai.",
    "Latency 45 ms hai, jo ki real-time voice streaming ke liye perfect hai.",

    # ── Emojis, Emotion Tags & Markdown Stripping ────────────────────────────
    "*smiles warmly* Good morning Tarik, how can I assist you today? 😊✨",
    "[laughs softly] Ye to bahut badhiya idea hai Tarik!",
    "**Important Notice:** System reboot scheduled at 2:00 AM.",
    "# Project Update\n- Voice pipeline updated\n- 0 errors reported.",
    "Check out this code snippet: `console.log('DAZY Live')` in your console.",
    "*giggles* Aap hamesha creative solutions dhund lete ho! ❤️",
    "Don't worry Tarik! [reassuring tone] Sab theek ho jayega. 👍",

    # ── Stutter & Repetition Guard ───────────────────────────────────────────
    "Hello..... Hello? Tarik, kya aap meri aawaz sun pa rahe hain?",
    "Checking status--- Everything is running smoothly.",
    "Tarik... Tarik... System is completely online.",
    "Wait-- let me check that API response for you.",
    "Yes!! All configurations have been successfully validated??",

    # ── Conversational Rapport & Companion Style ────────────────────────────
    "Tarik, main hamesha yahan hoon agar aapko koi bhi help chahiye.",
    "Aapne kaafi mehnat ki hai aaj, thoda break lena chahiye.",
    "Mujhe aapke projects par kaam karke bohot maza aata hai.",
    "Aapka vision sach mein futuristic hai, DAZY is proud of you.",
    "Dinner ka time ho gaya hai, kya aapne khana khaya?",
    "Main aapke personal tasks aur reminders manage kar sakti hoon.",

    # ── System Control & Commands ───────────────────────────────────────────
    "Screen capture ready hai, kya main screenshot analyze karun?",
    "Microphone sensitivity adjust ho chuki hai to prevent background noise.",
    "Speaker identification enabled: Speaker A Tarik confirmed.",
    "Unknown speaker detected, voice access restricted.",
    "Pronunciation dictionary updated: custom pronunciation applied for Tarik.",
    "Silent mode deactivated, voice synthesis active.",
    "Continuous conversation mode enabled, ready for follow-up turns.",
    "DAZY AI companion is fully operational and waiting for your command."
]


class TestSpeechEvaluationSuite:
    """Rigorous evaluation of the 50-sentence speech normalization & phonetics suite."""

    @pytest.fixture(autouse=True)
    def setup_engine(self):
        self.engine = PronunciationEngine.get_instance()
        assert self.engine is not None

    def test_total_sentence_count(self):
        assert len(TEST_SUITE_50_SENTENCES) == 50

    def test_mandatory_six_sentences_normalization(self):
        for idx in range(6):
            orig = TEST_SUITE_50_SENTENCES[idx]
            norm = self.engine.normalize_for_speech(orig)
            assert norm, f"Sentence {idx+1} normalized to empty"
            if "Tarik" in orig:
                assert "Tarik" in norm or "तारीक" in norm or "tarik" in norm.lower()
            assert not any(c in norm for c in ["*", "#", "`", "_", "😊", "✨"])

    def test_emoji_and_emotion_tag_removal(self):
        sample = "*smiles warmly* Good morning Tarik, how can I assist you today? 😊✨"
        norm = self.engine.normalize_for_speech(sample)
        assert "smiles warmly" not in norm
        assert "😊" not in norm
        assert "✨" not in norm
        assert "Good morning Tarik" in norm

    def test_codeblocks_and_markdown_removal(self):
        sample = "Check out this code snippet: `console.log('DAZY Live')` in your console."
        norm = self.engine.normalize_for_speech(sample)
        assert "`" not in norm
        assert "console" in norm

        bullet_sample = "# Project Update\n- Voice pipeline updated\n- 0 errors reported."
        norm_bullet = self.engine.normalize_for_speech(bullet_sample)
        assert "#" not in norm_bullet
        assert "-" not in norm_bullet
        assert "Voice pipeline updated" in norm_bullet

    def test_currencies_and_percentages_expansion(self):
        sample = "Total balance is ₹5000 and subscription is $50 with 100% discount."
        norm = self.engine.normalize_for_speech(sample)
        assert "5000 rupees" in norm
        assert "50 dollars" in norm
        assert "100 percent" in norm
        assert "₹" not in norm
        assert "$" not in norm
        assert "%" not in norm

    def test_time_normalization(self):
        sample = "Meeting at 10:30 AM and call at 5:00 PM."
        norm = self.engine.normalize_for_speech(sample)
        assert "10 30 AM" in norm
        assert "5 PM" in norm
        assert "5:00" not in norm

    def test_technical_acronym_spacing(self):
        sample = "Test AI, API, UI, CPU, and RAM on your OS."
        norm = self.engine.normalize_for_speech(sample)
        assert "A.I." in norm
        assert "A.P.I." in norm
        assert "U.I." in norm
        assert "C.P.U." in norm
        assert "O.S." in norm

    def test_stutter_marks_eliminated(self):
        sample = "Hello..... Hello? Tarik... Checking status--- all good."
        norm = self.engine.normalize_for_speech(sample)
        assert "....." not in norm
        assert "..." not in norm
        assert "---" not in norm

    def test_language_detection_hinglish_and_english(self):
        hinglish = "Hey Tarik, main aapki settings check kar rahi hoon."
        lang_h = self.engine.detect_language(hinglish)
        assert lang_h in ("hinglish", "hindi")

        english = "System performance is optimal with 100 percent uptime."
        lang_e = self.engine.detect_language(english)
        assert lang_e == "english"

    def test_all_50_sentences_normalize_cleanly(self):
        for idx, sentence in enumerate(TEST_SUITE_50_SENTENCES):
            norm = self.engine.normalize_for_speech(sentence)
            assert norm, f"Sentence {idx+1} failed normalization"
            # Must not contain unrendered markup
            for forbidden in ["***", "```", "###", "[]", "()", "undefined"]:
                assert forbidden not in norm, f"Forbidden '{forbidden}' in normalized text: {norm}"
            # Must end with clean punctuation
            assert norm[-1] in ".!?।", f"Missing clean ending punctuation: {norm}"
