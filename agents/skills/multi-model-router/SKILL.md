---
name: multi-model-router
description: Intelligent model routing across Groq, Gemini, OpenRouter, and DeepSeek based on latency, budget, and task complexity.
---

# Multi-Model Router Skill (NEURON.ONE GodMode Edition)

## Routing Matrix

| Task Category | Primary Provider | Fallback Provider | Target Latency | Optimization |
|---|---|---|---|---|
| **Voice / Real-time Chat** | Groq (`qwen/qwen3.8-27b`) | Gemini (`gemini-2.5-flash`) | < 1.2s | Prompt budgeted under 3,500 chars |
| **Deep Reasoning / Coding** | DeepSeek (`deepseek-chat`) | OpenRouter (`openai/gpt-4o-mini`) | 2 - 5s | Multi-step scratchpad |
| **Long Context / Research** | Gemini (`gemini-2.5-flash`) | Groq | 2 - 4s | 1M+ token window support |
| **Local / Offline Fallback** | Local Mock / TinyLlama | Rule-based Engine | < 100ms | Zero internet required |

## Rules
- When a provider returns HTTP 429 (Rate Limit) or 5xx, immediately failover to the next provider in the ladder without crashing the conversation.
- Cache tool definitions and strip empty fields to minimize token consumption per request.
