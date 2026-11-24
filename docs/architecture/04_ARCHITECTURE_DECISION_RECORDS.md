# Architecture Decision Records (ADRs) — DAZY AI OS

---

## ADR-001: Sovereign Single-Orchestrator Architecture
- **Status**: Approved
- **Context**: The open-source multi-agent ecosystem features competing orchestrators (GodMode-Team, NEURON.ONE, CrewAI, AutoGen). Running multiple independent frameworks causes memory bloat, competing thread loops, and split source of truth.
- **Decision**: DAZY remains the sole master orchestrator. Background subagents are dispatched asynchronously as worker tasks rather than running autonomous competitive loops.
- **Consequences**: Zero process collisions, unified memory in local SQLite, and clean user authorization.

---

## ADR-002: LangGraph Stateful Workflows with SQLite Checkpointing
- **Status**: Approved
- **Context**: Multi-step reasoning tasks need cycle detection, human approval gates, and persistence across process restarts without losing conversation state.
- **Decision**: Adopt LangGraph `StateGraph` with a custom `SQLiteCheckpointManager` (`memory/langgraph_checkpoints.db`). Replace all placeholder mocks with real tool execution (`TaskTools`, `search_memory`, `notes`, `diagnostics`).
- **Consequences**: Background goals resume seamlessly if DAZY is rebooted or network hiccups occur.

---

## ADR-003: Multi-Model Gateway & Dynamic Failover Ladder
- **Status**: Approved
- **Context**: Cloud AI services enforce strict free-tier rate limits (e.g. Groq 8,000 TPM / 200,000 TPD). A single rate-limit error must never crash the voice conversation.
- **Decision**: Implement a multi-provider fallback ladder:
  $$\text{Groq (Qwen / GPT-OSS)} \longrightarrow \text{Gemini 2.5 Flash} \longrightarrow \text{AI/ML API} \longrightarrow \text{OpenRouter} \longrightarrow \text{Local}$$
  Enforce prompt-budget compression ($\le 3,500$ characters) on free tiers.
- **Consequences**: 99.9% conversation availability even when individual cloud providers experience outages or quotas.

---

## ADR-004: Holographic 3-Column HUD with Web Audio Waveform
- **Status**: Approved
- **Context**: Visual references ([DAZY_UI_Visual_Reference_Links.md](file:///c:/Users/tarik/Downloads/DAZY_UI_Visual_Reference_Links.md)) demand a futuristic JARVIS-style HUD without sacrificing functional ergonomics.
- **Decision**: Adopt a fixed 3-column layout:
  - **Left**: Multi-ring pulsing Reactor Core, real Web Audio API Canvas waveform, voice selector.
  - **Center**: Conversation timeline, interim live transcription banner, tool activity.
  - **Right**: System vitals rail, memory facts ledger, reminders panel, quick controls.
- **Consequences**: Restrained, modern glassmorphism UI where every visual animation reflects live audio or telemetry buffers.

---

## ADR-005: Security Isolation & PIN Protection
- **Status**: Approved
- **Context**: Personal assistants have access to local file systems, shell commands, and private data.
- **Decision**: Require session bearer token authentication for dashboard APIs, lock destructive OS tools behind PIN `786786`, and enforce SSRF cloud metadata IP blocks (`169.254.169.254`).
- **Consequences**: Protection against unauthorized network access or prompt injection attacks.
