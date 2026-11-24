# Recommended Tools, Libraries and Agent Skills

This is a compatibility-first recommendation list, not an instruction to install everything. Inspect the existing project and reuse working equivalents.

## Frontend and visualization
- React / Next.js: dashboard framework, only if compatible with the current project.
- TypeScript: typed contracts and safer UI state.
- Tailwind CSS + shadcn/ui: component system where already suitable.
- Three.js + React Three Fiber + Drei: interactive 3D graph.
- Framer Motion: restrained UI transitions.
- ECharts or Recharts: operational charts.
- TanStack Query: server state and cache, if appropriate.
- Playwright: end-to-end UI tests.
- Vitest: frontend unit tests.

## Desktop
- Tauri: Windows desktop shell, tray, global shortcut and notifications.
- Secure IPC: allowlisted commands only; no arbitrary shell execution from UI.
- OS credential store: use supported secure storage for desktop session tokens if required.

## Backend and orchestration
- Keep the current backend if healthy.
- FastAPI: optional Python API framework if the existing backend is Python or a justified service boundary is needed.
- PostgreSQL: structured operational state.
- pgvector: semantic memory where it adds value.
- Redis + Celery/RQ/Arq or existing durable queue: only if compatible with current architecture.
- OpenTelemetry: traces, metrics and context propagation.
- Sentry: frontend/backend exception monitoring, optional.
- Prometheus + Grafana: optional metrics stack.
- Docker Compose: local development if repository supports it.

## Protocols and integration standards
- OAuth 2.0 / PKCE where appropriate.
- MCP client/server SDKs compatible with the protocol version in use.
- OpenAPI for HTTP APIs.
- JSON Schema or typed models for tool inputs and outputs.
- SSE or WebSockets for live events.
- Secret manager or encrypted environment/secret references; never store plaintext API keys in application tables.

## Testing and quality
- Pytest or the existing backend test framework.
- Vitest/Jest for frontend unit tests.
- Playwright for browser flows.
- Contract tests for provider, tool and MCP adapters.
- Fault-injection tests for timeouts, rate limits, expired credentials and worker crashes.
- Dependency/security scanning already approved by the project.

## Suggested specialist agent skills
1. Repository Auditor — maps code, dependencies, entry points, tests and deployment.
2. Product Architect — maintains requirements, architecture decisions and contracts.
3. Frontend Design Engineer — builds responsive command center and accessible components.
4. 3D Visualization Engineer — builds telemetry-driven graph, node inspection and fallback.
5. Backend Platform Engineer — APIs, schemas, auth, persistence and migrations.
6. Agent Orchestration Engineer — primary brain, routing, delegation and worker lifecycle.
7. Integration Engineer — provider, API, OAuth, MCP, tools and skills adapters.
8. Memory Engineer — memory scopes, provenance, retrieval and retention.
9. Observability Engineer — logs, metrics, traces, dashboards and alerting.
10. Reliability / Repair Engineer — health checks, incident diagnosis, safe repair and rollback.
11. Desktop Engineer — Tauri packaging, tray, shortcuts, notifications and secure IPC.
12. QA / Security Engineer — tests, threat modeling, permissions, redaction and release gates.
13. Documentation Engineer — setup, operations, troubleshooting and recovery runbooks.

## Subagent operating contract
Each subagent receives:
- A bounded task and acceptance criteria.
- Exact files/directories it may modify.
- Shared API/schema contract version.
- Required tests.
- Explicit forbidden actions.
- A concise handoff report with files changed, tests run and blockers.

One integrator owns shared contracts, dependency changes, migrations and final merges. Avoid concurrent edits to the same files.
