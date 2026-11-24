# DAZY Unified Personal AI — Master Architecture

**Status:** Initial architecture baseline  
**Branch:** `feat/unified-personal-ai-foundation`  
**Principle:** One assistant identity, one shared intelligence contract, one memory authority, one capability registry, multiple clients and execution environments.

## 1. Product goal

DAZY is a personal AI companion and operator that can converse naturally, understand the user's intent, remember approved information, use permitted capabilities, complete multi-step work, and explain what it did. It must remain useful when the Windows host is offline, while clearly distinguishing cloud-capable features from host-dependent actions.

The system must never claim to have listened, seen, remembered, executed, or completed something unless the corresponding subsystem confirms it.

## 2. Architecture decisions

1. **Modular monolith first.** Keep a single deployable Python backend with explicit modules and interfaces. Split services only when measured scale or isolation requirements justify it.
2. **One canonical intelligence API.** Desktop, web, and mobile clients call the same versioned conversation/task contracts. Provider-specific prompts, memory rules, and tool execution must not be reimplemented independently in each client.
3. **Separate realtime and autonomous workloads.** Voice sessions need low-latency streaming and interruption handling. Research, coding, browser automation, and long-running jobs need durable execution, checkpoints, retries, and audit history.
4. **Local-first execution, cloud-assisted continuity.** Windows owns machine-local capabilities. Cloud services own identity/session sync, shared metadata, notifications, and work that does not require the Windows host.
5. **PostgreSQL is the shared source of truth.** SQLite may remain for local/offline state and caches. Vector indexes are retrieval indexes, never the only copy of a memory.
6. **Provider neutrality.** Models, speech engines, and external services are adapters behind typed interfaces. No application module should depend directly on a vendor SDK unless it is inside that vendor adapter.
7. **Least privilege by default.** Every capability declares its permissions, risk, timeout, and approval requirement. Destructive or externally visible actions require explicit confirmation.
8. **No uncontrolled self-modification.** DAZY may propose improvements, prepare patches, and run tests; applying code changes requires review and an auditable release path.

## 3. Logical system

```text
Windows Desktop ─────┐
Web Companion ───────┼──> Client/API Gateway ──> Conversation Orchestrator
iOS / Android ───────┘             │                       │
                                  │                       ├── Persona + policy
                                  │                       ├── Model router
                                  │                       ├── Agent supervisor
                                  │                       ├── Memory service
                                  │                       └── Capability registry
                                  │                                  │
                                  └── Realtime voice gateway          ├── Native tools
                                                                     ├── MCP tools
                                                                     ├── Skills/workflows
                                                                     └── Device-local bridge

Cloud control plane: PostgreSQL, auth, sync, task metadata, notifications, audit
Windows execution plane: local files/apps/browser/OS, local models, local devices
Observability: structured logs, traces, metrics, evaluation and safety audit
```

## 4. Core boundaries

### 4.1 Client applications

Clients render the conversation, capture user input, display task progress, request permissions, and play responses. They do not own business rules, provider selection, canonical memory, or tool authorization.

### 4.2 API and session gateway

Responsibilities:
- Versioned REST contracts for normal requests and task management.
- WebSocket or WebRTC-compatible session transport for realtime voice/events.
- Device/session identity, authentication, rate limits, request IDs, and schema validation.
- Routing to cloud services or the authenticated Windows device bridge.
- Explicit offline/host-unavailable responses.

### 4.3 Conversation orchestrator

Responsibilities:
- Normalize user input and conversation context.
- Apply DAZY persona, language, tone, and response policies.
- Select model/provider using task, latency, privacy, availability, and cost policy.
- Decide whether a request is conversational, tool-based, or a durable task.
- Invoke the agent supervisor and collect verified results.
- Produce text/audio response events and trace metadata.

The orchestrator must not contain vendor-specific API calls or direct unrestricted operating-system access.

### 4.4 Realtime voice plane

Keep the existing Gemini Live integration behind a provider adapter while it is working. Add explicit interfaces for:
- audio input/output streams;
- voice activity detection and endpointing;
- turn lifecycle and interruption;
- transcript events;
- playback state and echo suppression;
- language and voice selection;
- health, reconnect, and timeout behavior.

A cascaded STT → reasoning → TTS path remains an alternative for offline operation, auditability, or providers that do not support realtime audio. Do not run multiple microphone owners at once.

### 4.5 Autonomous task plane

Long-running work must be represented as a durable task with:
- task ID, owner/device, type, status, priority;
- validated input and output schema;
- idempotency key;
- attempt count, deadline, lease/heartbeat;
- cancellation and approval state;
- append-only task events and result references.

The current SQLite queue can remain during the first migration step, but stale-running recovery, leases, idempotency, and crash-restart tests are required before relying on it for unattended work. Move shared task state to PostgreSQL before introducing multiple independent workers. Evaluate DBOS for durable Python workflows when checkpointing/recovery becomes necessary; use Temporal only if distributed workflow complexity warrants it.

### 4.6 Agent system

Start with one supervisor and a small set of bounded specialist roles:
- research;
- coding;
- computer/browser operation;
- memory and personal knowledge;
- communications;
- verification.

Agents are not separate autonomous authorities. The supervisor owns the task, delegates bounded work, enforces permissions, and requires verification before reporting completion. Use typed tool inputs/outputs. Add graph orchestration only for workflows that genuinely need branching, resumability, or human-in-the-loop checkpoints.

### 4.7 Capability registry

All executable capabilities must be discoverable through one registry, regardless of whether they are native Python functions, MCP tools, external APIs, or approved plugins.

Each manifest must define:
- stable capability ID and version;
- human-readable purpose and input/output schema;
- source and provenance;
- permissions and risk level;
- timeout, retry policy, and idempotency behavior;
- approval policy;
- health/availability and platform requirements.

A skill is instructional content, not automatically an executable tool. Discovery of a repository or skill must never trigger automatic code execution. Inspect provenance, license, dependencies, permissions, and behavior; sandbox and test it; then require approval before installation or activation.

### 4.8 Memory

Use distinct memory classes:
- working/session context;
- user-approved profile and preferences;
- episodic conversation/task summaries;
- semantic facts and relationships;
- procedural knowledge and workflows;
- archival documents/history.

Every memory item needs provenance, creation/update time, confidence, scope, retention policy, and deletion/update path. Store canonical records in relational storage. Add semantic/vector retrieval only as an index with a rebuild path. Memory extraction is a proposal until validated against policy; sensitive facts require stricter handling and explicit user control.

## 5. Data and service contracts

Initial canonical entities:
- `User`, `Device`, `Conversation`, `Message`, `MemoryItem`
- `Task`, `TaskEvent`, `ApprovalRequest`
- `CapabilityManifest`, `CapabilityInvocation`
- `ProviderConfig`, `AuditEvent`

All external API payloads must be validated. Use UTC timestamps in storage and convert to the user's locale only at presentation boundaries. Use stable IDs and idempotency keys for retries.

## 6. Security model

Risk tiers:
- **R0 — Read-only:** scoped retrieval and status checks; allowed within granted scope.
- **R1 — Reversible local change:** allowed only within explicit workspace/device boundaries; undo where possible.
- **R2 — External or sensitive action:** explicit user approval immediately before execution.
- **R3 — Destructive/high-impact action:** explicit confirmation with a clear action summary; stronger checks and audit record.

Required controls:
- device identity and authenticated device bridge;
- secrets in OS credential storage or managed server secrets, never committed to Git;
- filesystem allowlists and command execution sandboxing;
- network egress restrictions for automation workers;
- per-capability permissions and deadlines;
- untrusted-content isolation for web pages, files, and tool outputs;
- redacted structured logs and auditable approvals;
- cancellation, emergency stop, and credential revocation.

## 7. Observability and quality

Every request should be traceable across:
`client → session → orchestrator → model → agent → capability → result → memory`.

Record latency, errors, retries, model/provider, tool outcome, approval decision, and task state transitions. Avoid logging secrets or unnecessary private content.

Quality gates:
- unit tests for contracts, policies, memory, routing, and queue transitions;
- integration tests with mocked providers and tools;
- voice tests for Hindi, English, and Hinglish, noisy environments, silence, interruption, echo, reconnect, and device changes;
- safety tests for prompt injection, permission bypass, destructive actions, and untrusted tool output;
- regression tests for every repaired bug.

## 8. Existing project migration map

Based on the inspected repository snapshot, DAZY already has useful building blocks: a PyQt6 desktop application, Gemini Live session code, action/plugin discovery, memory modules, a dashboard/phone relay, background monitoring, and a separate React/TypeScript/Supabase web companion. The web companion and desktop application currently contain overlapping conversation/persona/provider logic and must be consolidated behind shared API contracts.

Do not delete or replace these modules until their behavior and tests are mapped:
- desktop live session and audio lifecycle;
- existing action/plugin discovery and confirmation/undo gates;
- memory manager and configuration manager;
- dashboard and phone audio relay;
- web chat edge function and local FastAPI backend;
- existing task queue and built-in workers.

The source snapshot shows legacy JARVIS/MARK naming in places. Treat naming cleanup as a separate, low-risk task after behavior is stable.

## 9. Delivery sequence

### Phase 0 — Baseline and safety
- Record exact branch/commit and runtime versions.
- Inventory entry points, configuration, secrets, tests, and active providers.
- Run existing tests and builds without changing behavior.
- Identify secrets in tracked files and rotate any exposed credentials.
- Capture known voice, memory, task, and UI regressions.

### Phase 1 — Shared contracts and architecture seams
- Add typed request/response schemas for conversation, events, tasks, memory, and capability manifests.
- Define provider, memory, task-queue, and capability interfaces.
- Add contract tests and dependency direction rules.
- Do not change the visible UI or replace the working voice path in this phase.

### Phase 2 — Unified backend
- Make the local FastAPI backend the canonical application API.
- Move duplicated web persona/provider/tool logic behind the same service contracts.
- Preserve cloud continuity through authenticated Supabase functions and explicit sync boundaries.
- Add request IDs, structured errors, timeouts, and health checks.

### Phase 3 — Voice reliability
- Isolate audio capture, VAD, turn state, provider streaming, playback, echo control, and reconnect.
- Enforce one microphone owner.
- Add Hinglish and interruption evaluation before tuning personality or adding more voices.

### Phase 4 — Memory and durable tasks
- Normalize memory records and provenance.
- Harden the current queue with leases, recovery, idempotency, cancellation, and tests.
- Move shared task state to PostgreSQL when multi-device/multi-worker behavior is enabled.

### Phase 5 — Agent and capability governance
- Add the supervisor and typed specialist tools.
- Unify native tools, MCP, skills, and plugin metadata in the registry.
- Add sandboxing, approvals, provenance checks, and verification.

### Phase 6 — Mobile and remote device continuity
- Use the same contracts for mobile clients.
- Secure the Windows device bridge; never expose an unauthenticated local API to the public internet.
- Queue host-dependent work while the Windows machine is offline.

### Phase 7 — Evaluation and controlled improvement
- Add trace-based evaluations, regression suites, and release gates.
- Allow DAZY to propose patches and test plans; require human review for code deployment.

## 10. Definition of done

A feature is not complete because a file or button exists. It is complete only when:
1. the capability is reachable through its documented interface;
2. permissions and failure states are enforced;
3. success/failure is reported from actual execution results;
4. tests cover normal, timeout, retry, cancellation, and denial paths;
5. logs/traces make failures diagnosable without leaking secrets;
6. desktop, web, and mobile behavior is consistent where the feature is shared.

---
This document is a target architecture and migration contract, not a claim that every component is already implemented.
