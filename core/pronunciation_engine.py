"""core/pronunciation_engine.py — Language-Aware Text Normalizer and Pronunciation Engine.

Engineered for DAZY AI Assistant.
Provides:
1. Markdown and formatting cleanup (strips code, emotions, asterisks, bullet points).
2. Emoji and unicode symbol stripping (prevents TTS reading emoji names).
3. Number, currency, symbol, and time normalization.
4. Language-aware Hinglish / Indian English / Hindi tokenization.
5. Editable pronunciation dictionary (memory/pronunciation_dict.json).
6. Elimination of repetitive stutter markers, ellipses, and garbled symbols.
7. Guarantees zero asterisk ("asterisk, asterisk") speech leakage to TTS.
"""
from __future__ import annotations

import json
import logging
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("dazy.pronunciation")

_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DICT_PATH = _ROOT / "memory" / "pronunciation_dict.json"

# Common emojis and symbols regex
_EMOJI_RE = re.compile(
    r"[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf\ufe0f\u200d\u2300-\u23ff]",
    flags=re.UNICODE,
)

# Roleplay and stage action markers (explicit verbs only, preserving regular parentheses)
_EMOTION_TAG_RE = re.compile(
    r"\*(?:smiles|smiling|laughs|laughing|chuckles|chuckling|sighs|sighing|giggles|giggling|winks|winking|nods|nodding|blushes|blushing|pauses|whispers|whispering)(?:\s+[\w]+)?\*|"
    r"\[(?:smiles|smiling|laughs|laughing|chuckles|chuckling|sighs|sighing|giggles|giggling|winks|winking|nods|nodding|blushes|blushing|pauses|whispers|whispering)(?:\s+[\w]+)?\]",
    flags=re.IGNORECASE,
)

# Markdown elements
_MD_CODEBLOCK_RE = re.compile(r"```[\s\S]*?```")
_MD_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_HEADER_RE = re.compile(r"^\s*#{1,6}\s+(.+)$", flags=re.MULTILINE)
_MD_BULLET_RE = re.compile(r"^\s*[-*+]\s+(.+)$", flags=re.MULTILINE)
_MD_NUM_LIST_RE = re.compile(r"^\s*\d+\.\s+(.+)$", flags=re.MULTILINE)

# Stuttering / repeated symbol patterns
_MULTI_DOT_RE = re.compile(r"\.{2,}")
_MULTI_PUNCT_RE = re.compile(r"([!?,-])\1+")

# Hinglish lexical markers
_HINGLISH_WORDS = {
    "aap", "aapka", "aapki", "aapke", "tum", "tera", "meri", "mera", "mere",
    "hai", "hain", "hoon", "tha", "thi", "the", "kya", "kyun", "kaise",
    "karo", "karein", "raha", "rahi", "rahe", "nahi", "nahin", "bilkul",
    "theek", "shukriya", "accha", "achha", "bahut", "kaafi", "saare",
    "hum", "karenge", "dekh", "suno", "samajh", "batao", "chahiye", "hoga"
}


class PronunciationEngine:
    """Authoritative pronunciation and text normalization engine."""

    _instance: Optional["PronunciationEngine"] = None
    _lock = threading.Lock()

    def __init__(self, dict_path: Optional[Path] = None):
        self._dict_path = dict_path or _DEFAULT_DICT_PATH
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._compiled_replacements: List[Tuple[re.Pattern, str]] = []
        self._load_lock = threading.Lock()
        self.load_dictionary()

    @classmethod
    def get_instance(cls, dict_path: Optional[Path] = None) -> "PronunciationEngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(dict_path)
            return cls._instance

    def load_dictionary(self) -> None:
        """Load pronunciation rules from memory/pronunciation_dict.json."""
        with self._load_lock:
            self._entries.clear()
            if self._dict_path.is_file():
                try:
                    with open(self._dict_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self._entries = data.get("entries", {})
                except Exception as exc:
                    logger.warning("Failed to load pronunciation dict: %s", exc)

            # Ensure minimum default critical entries
            if "Tarik" not in self._entries:
                self._entries["Tarik"] = {
                    "spoken": "Tarik",
                    "phonetic": "तारीक",
                    "lang": "hinglish",
                    "note": "Owner name explicit pronunciation",
                }
            if "DAZY" not in self._entries:
                self._entries["DAZY"] = {
                    "spoken": "Daisy",
                    "phonetic": "Daisy",
                    "lang": "en",
                    "note": "Assistant identity",
                }

            self._recompile_patterns()

    def _recompile_patterns(self) -> None:
        """Compile regex patterns sorted by key length descending."""
        self._compiled_replacements.clear()
        sorted_keys = sorted(self._entries.keys(), key=len, reverse=True)
        for key in sorted_keys:
            info = self._entries[key]
            replacement = info.get("spoken") or info.get("phonetic") or key
            pattern = re.compile(rf"\b{re.escape(key)}\b", flags=re.IGNORECASE)
            self._compiled_replacements.append((pattern, replacement))

    def save_dictionary(self) -> bool:
        """Persist dictionary to disk."""
        with self._load_lock:
            try:
                self._dict_path.parent.mkdir(parents=True, exist_ok=True)
                data = {
                    "version": 1,
                    "description": "User-editable pronunciation dictionary for DAZY speech synthesis",
                    "entries": self._entries,
                }
                with open(self._dict_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self._recompile_patterns()
                return True
            except Exception as exc:
                logger.error("Failed to save pronunciation dict: %s", exc)
                return False

    def get_dictionary(self) -> Dict[str, Dict[str, Any]]:
        """Return a copy of the dictionary entries."""
        with self._load_lock:
            return dict(self._entries)

    def set_entry(self, word: str, spoken: str, phonetic: str = "", lang: str = "hinglish", note: str = "") -> bool:
        """Add or update an entry in the dictionary."""
        word = word.strip()
        if not word:
            return False
        with self._load_lock:
            self._entries[word] = {
                "spoken": spoken.strip() or word,
                "phonetic": phonetic.strip() or spoken.strip(),
                "lang": lang,
                "note": note,
            }
        return self.save_dictionary()

    def remove_entry(self, word: str) -> bool:
        """Delete an entry from the dictionary."""
        with self._load_lock:
            if word in self._entries:
                del self._entries[word]
                return self.save_dictionary()
        return False

    def detect_language(self, text: str) -> str:
        """Detect language category: 'hindi', 'hinglish', or 'english'."""
        if not text:
            return "english"
        if re.search(r"[\u0900-\u097F]", text):
            return "hindi"

        tokens = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
        hinglish_hits = tokens.intersection(_HINGLISH_WORDS)
        if len(hinglish_hits) >= 2 or (len(tokens) <= 4 and len(hinglish_hits) >= 1):
            return "hinglish"

        return "english"

    def normalize_for_speech(self, text: str) -> str:
        """Complete, multi-stage normalization pipeline for neural TTS.

        Guarantees zero markdown formatting, zero raw asterisks, and speech-ready prose.
        """
        if not text:
            return ""

        raw = str(text)

        # 1. Strip markdown links first (keeping label), then standalone URLs and code blocks
        raw = _MD_LINK_RE.sub(r"\1", raw)
        raw = re.sub(r"https?://\S+", "link", raw)
        raw = _MD_CODEBLOCK_RE.sub(" ", raw)
        raw = re.sub(r"\|", " ", raw)  # Strip markdown table pipes while preserving cell text
        raw = _MD_INLINE_CODE_RE.sub(r"\1", raw)

        # 2. Convert markdown headers: '# Header' -> 'Header.'
        raw = _MD_HEADER_RE.sub(r"\1.", raw)

        # 3. Convert markdown lists to punctuated items: '- Item' -> 'Item.'
        raw = _MD_BULLET_RE.sub(r"\1.", raw)
        raw = _MD_NUM_LIST_RE.sub(r"\1.", raw)

        # 4. Strip markdown bold formatting FIRST (before any emotion tag processing)
        raw = re.sub(r"\*\*([^*]+)\*\*", r"\1", raw)
        raw = re.sub(r"__([^_]+)__", r"\1", raw)

        # 5. Emotion / stage directions
        raw = _EMOTION_TAG_RE.sub("", raw)

        # 6. Strip markdown italics (*text* or _text_)
        raw = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", raw)
        raw = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"\1", raw)
        raw = re.sub(r"~~([^~]+)~~", r"\1", raw)

        # 7. Strip Emojis
        raw = _EMOJI_RE.sub("", raw)

        # 8. Expand symbols and currencies
        raw = re.sub(r"\$(\d+(?:\.\d+)?)", r"\1 dollars", raw)
        raw = re.sub(r"₹\s*(\d+(?:\.\d+)?)", r"\1 rupees", raw)
        raw = re.sub(r"\bRs\.?\s*(\d+(?:\.\d+)?)", r"\1 rupees", raw, flags=re.IGNORECASE)
        raw = re.sub(r"(\d+)%", r"\1 percent", raw)
        raw = re.sub(r"&", " and ", raw)
        raw = re.sub(r"@", " at ", raw)
        raw = re.sub(r"#", " ", raw)

        # 9. Time normalization
        raw = re.sub(r"(\b\d{1,2}):00\s*(AM|PM|am|pm)\b", r"\1 \2", raw)
        raw = re.sub(r"(\b\d{1,2}):(\d{2})\s*(AM|PM|am|pm)\b", r"\1 \2 \3", raw)

        # 10. Technical acronyms
        acronyms = {
            r"\bAI\b": "A.I.",
            r"\bAPI\b": "A.P.I.",
            r"\bAPIs\b": "A.P.I.s",
            r"\bUI\b": "U.I.",
            r"\bUX\b": "U.X.",
            r"\bOS\b": "O.S.",
            r"\bURL\b": "U.R.L.",
            r"\bSQL\b": "S.Q.L.",
            r"\bJSON\b": "Jason",
            r"\bHTML\b": "H.T.M.L.",
            r"\bCSS\b": "C.S.S.",
            r"\bRAM\b": "ram",
            r"\bCPU\b": "C.P.U.",
            r"\bGPU\b": "G.P.U.",
            r"\bGB\b": "gigabytes",
            r"\bMB\b": "megabytes",
            r"\bKB\b": "kilobytes",
            r"\bkHz\b": "kilohertz",
            r"\bms\b": "milliseconds",
        }
        for pat, rep in acronyms.items():
            raw = re.sub(pat, rep, raw)

        # 11. Apply pronunciation dictionary replacements
        for pattern, replacement in self._compiled_replacements:
            raw = pattern.sub(replacement, raw)

        # 12. Strip ANY stray asterisks (never speak "asterisk" aloud)
        raw = re.sub(r"\*+", "", raw)

        # 13. Strip outer quotes while preserving contractions (' inside words)
        raw = re.sub(r'["“”«»]', '', raw)
        raw = re.sub(r"(?<!\w)'|'(?!\w)", "", raw)

        # 14. Clean repetitive punctuation and stuttering triggers
        raw = _MULTI_DOT_RE.sub(". ", raw)
        raw = _MULTI_PUNCT_RE.sub(r"\1 ", raw)
        raw = re.sub(r"[-–—]{2,}", " ", raw)

        # 15. Fix double periods and natural sentence spacing
        raw = re.sub(r"\.\s*\.", ".", raw)
        raw = re.sub(r"\s+([,.;:!?\u0964\u0965])", r"\1", raw)
        raw = re.sub(r"\s+", " ", raw).strip()

        return raw


# Module level convenience functions
def normalize_text_for_speech(text: str) -> str:
    return PronunciationEngine.get_instance().normalize_for_speech(text)


def detect_speech_language(text: str) -> str:
    return PronunciationEngine.get_instance().detect_language(text)
