# ADR-0002: Dual-Engine Conversational Architecture

* **Status:** Accepted
* **Deciders:** Principal Architect, Voice Systems Engineer
* **Date:** 2026-11-24

## Context and Problem Statement
DAZY must provide low-latency voice interaction while also functioning when cloud quotas expire, when offline, or when privacy requires local compute. Relying exclusively on Gemini Live creates external single-point-of-failure and quota vulnerability. Conversely, relying exclusively on a local STT $\to$ LLM $\to$ TTS pipeline introduces higher turn latency (1.5s–3.0s vs. 300ms–600ms).

## Decision Drivers
* Real-time conversational responsiveness (< 600ms target in primary mode).
* Graceful offline and private execution.
* Seamless abstraction where UI, lip-sync, tools, and actions cannot tell which engine is active.

## Considered Options
1. **Unified Dual-Engine Strategy**: Primary Gemini Live WebSocket (`models/gemini-3.1-flash-live-preview`) with seamless fallback to Pipeline Engine (`WhisperSTT` $\to$ OpenAI-compat/Local LLM $\to$ `EdgeTTS`).
2. Gemini Live only.
3. Local Pipeline only.

## Decision Outcome
Chosen option: **Unified Dual-Engine Strategy**.
Both engines conform to an identical asynchronous event-streaming interface (`receive()` yielding audio chunks, transcripts, tool calls). `main.py` switches engines without mutating downstream audio playback, tool dispatch, or visual rendering.

### Positive Consequences
* Sub-600ms bidirectional streaming over WebSockets when online.
* Uninterrupted voice assistance via Whisper + Qwen/Gemini-Flash + EdgeTTS during API quota downtime or offline operation.
* Unified tool calling and viseme extraction across both backends.
