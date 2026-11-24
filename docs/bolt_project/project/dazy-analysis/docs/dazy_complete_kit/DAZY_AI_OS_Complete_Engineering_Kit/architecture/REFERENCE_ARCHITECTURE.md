# DAZY AI OS — Reference Architecture

## 1. Architecture decision

Use a **modular monolith / single lightweight DAZY host first**, retaining existing DAZY frameworks wherever viable. Use optional isolated processes only for specialist runtimes that cannot be embedded cleanly.

The web dashboard and Tauri desktop companion communicate with the same authenticated DAZY backend. The desktop shell must not start a second copy of the backend if one is already available.

## 2. Logical layers

```text
┌──────────────────────────────────────────────────────────────┐
│ PRESENTATION                                                 │
│ React Web Dashboard │ Tauri Windows Companion │ Mobile Web   │
│ Command Center      │ Quick Controls          │ Responsive   │
│ 2D panels + lazy 3D telemetry graph                            │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTPS + WS/SSE
┌──────────────────────────────▼───────────────────────────────┐
│ DAZY API / BACKEND-FOR-FRONTEND                               │
│ Auth/RBAC │ User Profile │ Dashboard API │ Event Gateway      │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│ CONTROL PLANE                                                 │
│ Integration Registry │ Capability Registry │ Policy Engine    │
│ Tool/Skill Registry  │ MCP Registry         │ Repo Radar       │
│ Approvals            │ Schedules            │ Resource Policy  │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│ RUNTIME PLANE — one primary orchestrator                      │
│ Primary Brain → Planner → Bounded Worker Pool                 │
│ Model Gateway │ Memory Service │ Task State │ Verifier         │
│ Optional Runtime Adapters (not independent primaries)          │
└──────────────┬───────────────┬────────────────┬───────────────┘
               │               │                │
      ┌────────▼─────┐ ┌───────▼────────┐ ┌─────▼────────────┐
      │ NANOBOT      │ │ OPENMANUS      │ │ AGENTICSEEK      │
      │ optional     │ │ optional       │ │ optional isolated│
      │ agent adapter│ │ task adapter   │ │ browser/coding   │
      └──────────────┘ └────────────────┘ └──────────────────┘
               │
      ┌────────▼───────────────────────────────────────────────┐
      │ EXTERNAL WORKFLOW ADAPTER                               │
      │ n8n remote instance via API/webhooks, if user enables it │
      └────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ SHARED DATA / OPERATIONS                                      │
│ Existing DB (prefer reuse) │ File/object store │ Optional queue│
│ Memory vectors if useful   │ Logs/Metrics/Traces               │
└──────────────────────────────────────────────────────────────┘
```

## 3. Key architecture principles

- **One primary brain:** DAZY is the top-level orchestrator. Nanobot/OpenManus/AgenticSeek never silently become parallel primary orchestrators.
- **One source of truth:** profile, tasks, worker status, integration health, resource readings and approvals are backend-owned.
- **Adapter isolation:** external runtimes have stable input/output contracts and explicit permissions.
- **On-demand execution:** optional runtimes, browser automation, MCP sessions and 3D rendering do not start unless required.
- **Existing stack first:** no framework rewrite or new database unless the audit demonstrates a concrete need.
- **8 GB first:** bounded queues, one worker by default, low concurrency, hosted models by default.
- **Observable by default:** every task and integration call has a correlation ID and safe structured events.

## 4. Suggested service boundaries

1. Identity/Profile Service — canonical user profile and greeting data.
2. API Gateway — auth, RBAC, validation and rate limits.
3. Orchestrator — task planning, delegation and model selection.
4. Model Gateway — provider adapters, capability registry and fallback policy.
5. Worker Scheduler — bounded workers, leases, queue and checkpoints.
6. Integration Registry — connection metadata and secret references.
7. Tool/Skill Gateway — validated tool execution.
8. MCP Gateway — lifecycle and capability discovery.
9. Memory Service — scoped retrieval, writes, provenance and retention.
10. Repo Radar — GitHub metadata, source discovery, license and dependency review.
11. Diagnostics — health checks, incidents and root-cause evidence.
12. Repair Service — allowlist, approvals, execution and rollback.
13. Telemetry — logs, metrics, traces and resource readings.
14. Desktop API — authenticated controls and notification routing.

These can remain modules in one backend process initially. Do not create a microservice for every box.

## 5. Shared data stores

- Reuse the existing primary database where healthy.
- PostgreSQL is a recommended target for structured operational state only if no suitable DB exists.
- pgvector is optional; do not add a vector DB just because the product has memory.
- Redis is optional; use it only when the chosen durable queue or cache requires it.
- Store large files/artifacts separately from operational rows.
- Store credentials in an OS credential vault or server-side encrypted secret store.
- Avoid duplicate local Postgres/Redis instances across web, desktop and worker processes.

## 6. Runtime adapters

Each adapter exposes:
- `discoverCapabilities()`
- `healthCheck()`
- `execute(task, context)`
- `cancel(runId)`
- `getRun(runId)`
- `getUsage(runId)`
- `shutdown()`

Every request carries:
- `requestId`
- `taskId`
- `correlationId`
- `userId`
- `profileVersion`
- `permissionScope`
- `resourceBudget`
- `deadline`
- `requestedCapabilities`

Every result carries:
- `runId`
- `status`
- `output`
- `artifacts`
- `usage`
- `events`
- `warnings`
- `sourceRuntime`
- `verification`

Do not pass provider API keys to external runtimes unless strictly required; prefer server-side credential references or narrowly scoped short-lived credentials.

## 7. Model routing

Route by:
1. Required capabilities (text, vision, audio, tool calls, structured outputs).
2. User and task permissions.
3. Provider health.
4. Resource policy (local vs remote).
5. Cost and latency budget.
6. Fallback compatibility.

A fallback must be capability-compatible and explicitly allowlisted. Log the routing reason.

## 8. Event contract

Use WebSocket or SSE typed events:
- `profile.updated`
- `system.resource.sample`
- `integration.health.changed`
- `agent.run.started`
- `worker.heartbeat`
- `worker.status.changed`
- `task.created`, `task.progress`, `task.completed`, `task.failed`
- `model.call.started`, `model.call.completed`
- `tool.call.started`, `tool.call.completed`, `tool.call.failed`
- `memory.retrieved`, `memory.saved`
- `repo.discovered`, `repo.review.completed`
- `incident.created`
- `repair.proposed`, `repair.approval_required`, `repair.verified`, `repair.rolled_back`

Each event includes event ID, schema version, timestamp, user scope, source, correlation ID and safe payload.

## 9. Desktop lifecycle

- Tauri app owns only shell/window/tray/shortcut/notifications.
- It connects to the same backend URL as web.
- If DAZY backend is local, a single-instance lock prevents duplicate service startup.
- If backend is remote, desktop does not spawn local database/worker services.
- Desktop controls must wait for backend confirmation.
- Emergency Stop cancels queued/running work safely and records state; it does not terminate databases or delete data.

## 10. 3D graph architecture

- Node/edge registry is fetched from backend.
- Runtime events update only the affected nodes/edges.
- 3D scene mounts on route entry or user demand.
- Idle or hidden scene stops animation.
- Use a 2D graph when GPU pressure is high.
- Selecting a node opens the same inspector used by the 2D system map.
- Data packets represent actual execution events only.
