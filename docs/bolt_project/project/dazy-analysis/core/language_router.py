"""core/language_router.py — Language identification, routing, and Hinglish normalizer.

Ensures seamless code-switching between Hindi, English, Urdu, and regional languages
while preserving English technical terms, app names, file paths, and command tokens.
"""
from __future__ import annotations

import re

# Common technical and command tokens to protect from transliteration/mangling
PROTECTED_TOKENS = {
    "chrome", "firefox", "edge", "safari", "browser", "youtube", "whatsapp",
    "spotify", "terminal", "powershell", "cmd", "vscode", "vs code", "python",
    "git", "github", "discord", "slack", "zoom", "file", "folder", "desktop",
    "windows", "linux", "macos", "task", "restart", "shutdown", "sleep",
    "volume", "mute", "unmute", "brightness", "wifi", "bluetooth", "camera",
    "microphone", "battery", "cpu", "ram", "gpu", "download", "upload", "url",
    "http", "https", "mark", "dazy", "jarvis"
}

# Indic Unicode ranges
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
_URDU_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
_BENGALI_RE = re.compile(r"[\u0980-\u09FF]")
_ODIA_RE = re.compile(r"[\u0B00-\u0B7F]")
_TELUGU_RE = re.compile(r"[\u0C00-\u0C7F]")
_TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")

# Roman Hinglish marker words
_HINGLISH_MARKERS = {
    "karo", "karna", "karein", "hai", "hain", "hoon", "nahi", "tha", "thi",
    "raha", "rahi", "rahe", "kaise", "kyun", "kya", "batao", "bataiye", "mera",
    "meri", "mere", "aap", "tum", "hum", "yeh", "woh", "acha", "theek", "shukriya",
    "dhanyawad", "zaroor", "sun", "dekho", "chalo", "ab", "abhi", "bohot", "thoda"
}


def detect_language(text: str) -> str:
    """Identifies the dominant language or code-switching mode of the text.

    Returns:
        "hi"      — Devanagari Hindi
        "ur"      — Urdu script
        "bn"      — Bengali
        "or"      — Odia
        "te"      — Telugu
        "ta"      — Tamil
        "hi-en"   — Roman Hinglish (Hindi + English)
        "en"      — English
    """
    if not text or not text.strip():
        return "en"

    # 1. Script checks
    if _URDU_ARABIC_RE.search(text):
        return "ur"
    if _DEVANAGARI_RE.search(text):
        return "hi"
    if _BENGALI_RE.search(text):
        return "bn"
    if _ODIA_RE.search(text):
        return "or"
    if _TELUGU_RE.search(text):
        return "te"
    if _TAMIL_RE.search(text):
        return "ta"

    # 2. Romanized checks
    words = [re.sub(r"[^\w]", "", w.lower()) for w in text.split()]
    hinglish_count = sum(1 for w in words if w in _HINGLISH_MARKERS)

    if hinglish_count >= 1:
        return "hi-en"

    return "en"


def normalize_hinglish(text: str) -> str:
    """Normalizes Roman Hinglish text for synthesis while preserving technical names.

    - Protects English command words, software names, and paths.
    - Standardizes frequent informal spellings (e.g. 'plz' -> 'please', 'u' -> 'you').
    - Cleans duplicate exclamation marks/stretches ('masttt' -> 'mast').
    """
    if not text:
        return ""

    tokens = text.split()
    normalized_tokens = []

    slang_map = {
        "plz": "please",
        "pls": "please",
        "thx": "thanks",
        "ty": "thank you",
        "u": "you",
        "r": "are",
        "yrr": "yaar",
        "bhaiya": "bhaiya",
    }

    for token in tokens:
        # Separate trailing punctuation
        m = re.match(r"^([\w'-]+)([^\w]*)$", token, re.UNICODE)
        if not m:
            normalized_tokens.append(token)
            continue

        word, punct = m.group(1), m.group(2)
        lower_word = word.lower()

        # If it's a protected token (e.g. "Chrome", "VS Code"), keep exact casing
        if lower_word in PROTECTED_TOKENS:
            normalized_tokens.append(f"{word}{punct}")
            continue

        # Replace standard web slang
        if lower_word in slang_map:
            replacement = slang_map[lower_word]
            normalized_tokens.append(f"{replacement}{punct}")
            continue

        # Collapse excessive letter repeats (e.g., 'achhaaaaa' -> 'achha')
        collapsed = re.sub(r"(.)\1{2,}", r"\1\1", word)
        normalized_tokens.append(f"{collapsed}{punct}")

    return " ".join(normalized_tokens)
