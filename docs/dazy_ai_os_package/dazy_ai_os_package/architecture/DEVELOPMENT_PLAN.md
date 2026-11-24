# DAZY AI OS — Development Plan and Release Gates

## Phase 0 — Repository discovery and baseline
**Deliverables:** architecture map, dependency map, feature inventory, current test/build status, security findings, reusable component inventory, risk register.
**Gate:** no implementation begins until current build and existing functionality are understood. Record baseline failures separately from regressions.

## Phase 1 — Product foundation
- Establish design tokens, navigation, layout shell and responsive behavior.
- Define typed API contracts and event schemas.
- Implement authentication, roles and permission checks using the existing auth system.
- Add feature flags and demo-mode isolation.
**Gate:** routes, navigation, permissions and empty/loading/error states tested.

## Phase 2 — Registry and connection manager
- Provider/model registry.
- API and OAuth connection metadata.
- Tools and skills registry.
- MCP server registry.
- Repository and knowledge-source registry.
- Secure credential references and redaction.
- Connection test jobs and capability discovery.
**Gate:** test outcomes accurately distinguish connected, degraded, failed, untested and demo.

## Phase 3 — Orchestration and workers
- Primary orchestrator and model gateway.
- Capability-aware routing.
- Worker lifecycle, heartbeat and leases.
- Durable task queue, idempotency, retries and checkpoints.
- Worker collaboration and delegation records.
**Gate:** end-to-end sample task survives restart and is traceable by correlation ID.

## Phase 4 — Memory and knowledge
- Memory data model and provenance.
- Retrieval/write APIs.
- Scoped access and retention.
- Vector retrieval only where useful.
- Memory activity timeline.
**Gate:** tests prove access boundaries, provenance and retention behavior.

## Phase 5 — Observability
- Structured logs, metrics and traces.
- Correlation IDs across model, worker, memory and tool calls.
- Live WebSocket/SSE stream.
- Usage and cost attribution.
- Alert rules and stale-data detection.
**Gate:** inject a known failure and confirm it is visible across logs, traces and UI.

## Phase 6 — Command Center and 2D operational views
- System overview.
- Workers and co-workers.
- Tasks and workflows.
- Integrations.
- Memory.
- Logs and traces.
- Usage and costs.
- Alerts and approvals.
**Gate:** all visible states are API-backed or explicitly labeled demo/cached/stale.

## Phase 7 — Full 3D Brain
- Graph snapshot and incremental telemetry API.
- 3D nodes and edges.
- Node inspection drawer.
- Search, filters, zoom, pan and minimap.
- Execution-path highlighting and time replay.
- Performance mode and 2D fallback.
**Gate:** automated test compares rendered graph input to backend graph fixture; no fabricated activity.

## Phase 8 — Diagnostics and controlled repair
- Health checks and incident model.
- Root-cause evidence collection.
- Repair proposals with risk classification.
- Allowlisted safe recovery.
- Approval queue for risky actions.
- Verification and rollback.
**Gate:** test safe retry, worker restart, fallback, approval-required repair, failed verification and rollback.

## Phase 9 — Windows desktop companion
- Tauri shell and packaging.
- System tray and notifications.
- Configurable global shortcut.
- Mini control center.
- Authenticated backend connection.
- Pause/resume/cancel and emergency stop.
**Gate:** controls work against real backend state; permissions and confirmation are tested.

## Phase 10 — Hardening and release
- Security review and secret scanning.
- Load and soak tests.
- Accessibility and responsive checks.
- Backup/restore drill.
- Upgrade and migration test.
- Installer and update strategy.
- User documentation and operational runbooks.
**Gate:** release checklist signed off; unresolved issues listed honestly.

## Required execution rules
1. Use parallel subagents only for bounded tasks with clear ownership and file boundaries.
2. One integrator owns shared contracts and merges.
3. Do not let multiple agents edit the same critical files concurrently.
4. Run targeted tests after each change and full regression tests at integration milestones.
5. Never overwrite unrelated working features.
6. Keep a task ledger with status: NOT STARTED, IN PROGRESS, IMPLEMENTED, TESTED, VERIFIED, BLOCKED.
7. IMPLEMENTED is not VERIFIED.
8. Do not claim a phase is complete if its release gate failed.

## Suggested workstreams
- Workstream A: repository audit, architecture and backend contracts.
- Workstream B: design system, navigation and 2D dashboard.
- Workstream C: model/provider/tool/MCP registry.
- Workstream D: orchestrator, task queue and workers.
- Workstream E: memory and knowledge.
- Workstream F: telemetry and observability.
- Workstream G: 3D visualization.
- Workstream H: diagnostics, repair and security.
- Workstream I: Tauri desktop companion.
- Workstream J: QA, integration and release.

## Initial milestone
Do not attempt all features in one giant merge. First deliver a verified repository audit, a working Command Center shell, typed state contracts, a real worker/task event path, and an end-to-end trace. Then expand incrementally.
