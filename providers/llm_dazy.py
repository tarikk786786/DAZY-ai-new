"""providers/llm_dazy.py — DAZY conversational brain provider (Sarvam & Qwen & Indic LLMs).

Specialized LLM provider for DAZY:
- Bundles the DAZY persona, Indian cultural knowledge, and emotional response guidance
- Native support for Sarvam AI models (Sarvam-2B, Sarvam-M) and Qwen models
- Supports standard /v1/chat/completions (Ollama, vLLM, Sarvam API, Groq, OpenRouter)
- Preserves full Mark-LVII tool-calling and desktop automation capabilities.
"""
from __future__ import annotations

import asyncio
from importlib.util import find_spec
from typing import Any, AsyncIterator, Optional

from core.dazy_persona import build_dazy_system_prompt
from memory.dazy_preferences import load_dazy_preferences
from .base import DEFAULT_CAPS, Field, FunctionCall
from .llm_openai import OpenAILLM


class DazyLLM(OpenAILLM):
    """Augments OpenAILLM with DAZY's personality prompt injection and Hinglish routing."""

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        self.include_dazy_prompt = bool(cfg.get("include_dazy_prompt", True))

    async def chat(self, messages: list[dict], tools: list[dict] | None = None,
                   *, stream: bool = True) -> AsyncIterator[dict]:
        """Injects DAZY's system prompt if enabled and delegates to OpenAILLM."""
        msgs = list(messages)
        if self.include_dazy_prompt and msgs:
            prefs = load_dazy_preferences()
            if msgs[0].get("role") == "system":
                existing_sys = msgs[0].get("content", "")
                msgs[0] = {
                    "role": "system",
                    "content": build_dazy_system_prompt(existing_sys, user_preferences=prefs)
                }
            else:
                msgs.insert(0, {
                    "role": "system",
                    "content": build_dazy_system_prompt("", user_preferences=prefs)
                })

        async for chunk in super().chat(msgs, tools, stream=stream):
            yield chunk


def _make(cfg: dict) -> DazyLLM:
    return DazyLLM(cfg)


PROVIDER = {
    "id": "dazy_brain",
    "kind": "llm",
    "label": "DAZY Conversational Brain (Sarvam / Qwen)",
    "hint": "Indian conversational intelligence with native Hinglish and emotion planning",
    "requires": (),
    "install": "httpx",
    "catalog": (
        {
            "id": "sarvam_cloud",
            "label": "Sarvam AI (Cloud)",
            "note": "Leading Indian conversational models with deep Indic understanding",
            "local": False,
            "values": {
                "base_url": "https://api.sarvam.ai/v1",
                "model": "sarvam-2b",
            },
        },
        {
            "id": "qwen_indic",
            "label": "Qwen 2.5 (Local or Cloud)",
            "note": "High reasoning performance with fluent Hinglish and Urdu",
            "local": True,
            "values": {
                "base_url": "http://127.0.0.1:11434/v1",
                "model": "qwen2.5:7b",
            },
        },
    ),
    "needs": (
        Field("base_url", "API address", default="https://api.sarvam.ai/v1",
              hint="Ollama, vLLM, Sarvam API, Groq, or OpenRouter"),
        Field("model", "Model name", default="sarvam-2b"),
        Field("api_key", "API key", kind="secret", default="", required=False),
        Field("include_dazy_prompt", "Inject DAZY Persona", kind="bool", default=True, advanced=True),
    ),
    "caps": {"tools": True, "tool_format": "openai", "max_tools": 16},
    "factory": _make,
}


def available() -> bool:
    return find_spec("httpx") is not None
