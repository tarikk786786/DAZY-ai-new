# DAZY AI OS — Reference Architecture

## 1. Architecture principles
- Audit first; extend rather than rewrite.
- One backend source of truth for web, 3D visualization and desktop.
- Event-driven observability with correlation IDs.
- Capability-aware model and tool routing.
- Persistent, idempotent jobs.
- Least-privilege execution.
- Human approval for high-risk changes.
- Explicit distinction between live, cached, stale, demo and unavailable data.

## 2. Logical architecture

```text
                 ┌─────────────────────────────┐
                 │ Web Dashboard (React)       │
                 │ 2D panels + 3D graph        │
                 └──────────────┬──────────────┘
                                │ HTTPS + WS/SSE
                 ┌──────────────▼──────────────┐
                 │ API Gateway / BFF           │
                 │ Auth • RBAC • Validation    │
                 └──────────────┬──────────────┘
                                │
     ┌──────────────────────────┼──────────────────────────┐
     │                          │                          │
┌────▼─────┐              ┌─────▼──────┐             ┌─────▼─────┐
│ Control  │              │ Runtime    │             │ Telemetry │
│ Plane    │              │ Plane      │             │ Plane     │
│ Registry │              │ Orchestr.  │             │ Logs      │
│ Policies │              │ Agents     │             │ Metrics   │
│ Approval │              │ Workers    │             │ Traces    │
└────┬─────┘              └─────┬──────┘             └─────┬─────┘
     │                          │                          │
     └──────────────────────────┼──────────────────────────┘
                                │
       ┌────────────────────────▼────────────────────────┐
       │ PostgreSQL • pgvector • Redis/Queue • Blob Store│
       └────────────────────────┬────────────────────────┘
                                │
       ┌────────────────────────▼────────────────────────┐
       │ Model Gateway • Tool/Skill Gateway • MCP Gateway│
       │ APIs • Providers • Repositories • Knowledge     │
       └─────────────────────────────────────────────────┘

                 ┌─────────────────────────────┐
                 │ Tauri Desktop Companion     │
                 │ Secure authenticated API   │
                 └─────────────────────────────┘
```

## 3. Control plane vs runtime plane
**Control plane:** users, roles, integration configuration, capability registry, policy, approvals, schedules, repair allowlists and system configuration.

**Runtime plane:** model calls, agent execution, worker processes, tools, MCP requests, task state, memory access and workflow execution.

The UI must not directly call providers or execute tools. It calls the authenticated backend, which enforces policy and records telemetry.

## 4. 3D graph data
The 3D scene is a projection of a backend graph:
- Nodes: registered components and runtime actors.
- Edges: configured dependencies, permitted connections and observed execution relationships.
- Events: telemetry events that animate edges and update node state.

Keep static topology separate from transient activity. Use server-issued node IDs and event IDs. Provide a graph snapshot endpoint plus incremental event stream. On reconnect, fetch a fresh snapshot before applying later events.

## 5. Model routing
The Model Gateway should maintain:
- Provider adapters.
- Model catalog.
- Capability metadata (text, vision, audio, tool calling, structured output, context limits).
- Availability and rate-limit state.
- Cost metadata.
- Policy constraints.
- Approved fallback chains.

Routing order: task requirements → capability match → policy/permission check → availability → budget/rate limit → selection. Record the routing reason. Do not assume model interchangeability.

## 6. Worker lifecycle
`created → ready → assigned → running → waiting → completed | failed | cancelled`
Support heartbeat, lease/lock, bounded retry, checkpoint, idempotency and graceful shutdown. A worker that misses heartbeat becomes `suspected_unhealthy` before being declared failed.

## 7. Repair architecture
Health signal → incident → evidence collection → diagnosis → risk classification → repair proposal → approval/policy gate → execution in isolated context → verification → close or rollback.

Automatic allowlist examples: retry transient request with backoff, reconnect a known MCP session, restart a stateless worker, route to an approved compatible fallback. All actions must be bounded and reversible where possible.

Approval-required examples: code changes, database migrations, credential rotation, permission changes, deleting data, publishing, sending messages, production deployments.

## 8. Desktop architecture
Tauri shell with:
- Webview UI or compact React view.
- OS tray and notifications.
- Configurable global shortcut.
- Secure IPC for OS-specific functions.
- Authenticated HTTPS/WebSocket communication with backend.
- No embedded provider secrets.
- Explicit confirmation for global stop and privileged actions.

## 9. Deployment topology
Start with a modular monolith or the existing deployment pattern plus separate durable workers. Split services only when required by independent scaling, security isolation or deployment needs.

Suggested components:
- Web frontend.
- API/backend.
- Worker process.
- PostgreSQL.
- Redis or existing durable queue.
- Object storage for artifacts.
- OpenTelemetry collector and metrics/log backend.

For local development, use Docker Compose if the repository already supports containers. For production, document secrets, backups, migrations, health checks and restore procedures.
