# DAZY AI OS — Product Requirements Document
**Version:** 1.0  
**Prepared:** 24 November 2026  
**Target platforms:** Web dashboard + Windows desktop companion  
**Visualization:** Full interactive 3D brain and infrastructure map  
**Repair policy:** Automatic low-risk recovery; human approval for risky changes

## 1. Product vision
DAZY AI OS is a unified, observable, controllable AI operations environment. It brings models, agents, workers, co-workers, memory, tasks, tools, skills, MCP servers, APIs, repositories, knowledge sources, diagnostics and desktop controls into one coherent product.

The product must be operational, not merely a collection of attractive dashboards. Every status shown in the UI must come from actual backend state or be explicitly labeled as demo, simulated, stale, unavailable or unverified.

## 2. Product goals
1. Give the user a trustworthy overview of DAZY health and activity.
2. Show how a request travels through the primary orchestrator, models, agents, workers, memory and tools.
3. Manage providers, credentials, APIs, tools, skills, MCP servers, repositories and knowledge sources.
4. Make task and worker execution inspectable, resumable and recoverable.
5. Provide traceable memory access and provenance.
6. Detect failures, diagnose root causes and safely recover from predefined low-risk incidents.
7. Provide a responsive web dashboard and a secure Windows desktop companion.
8. Offer a rich, interactive 3D visualization backed by real telemetry, with a 2D fallback.

## 3. Non-goals
- Do not replace the existing DAZY architecture before auditing it.
- Do not claim that every model supports every tool or modality.
- Do not execute arbitrary code or modify production systems without policy checks.
- Do not silently send messages, publish content, delete data, change credentials or alter permissions.
- Do not present mock values as live metrics.
- Do not make the 3D view the only way to operate the system.

## 4. User roles
- Owner / Administrator: configures providers, permissions, repair policies and system controls.
- Operator: monitors runs, tasks, agents and integrations; may approve permitted actions.
- Viewer: read-only access to dashboards and traces.
- Agent / Worker identity: machine principal with narrowly scoped tool and data permissions.

## 5. Information architecture
### Overview
- Command Center
- Daily Briefing
- Alerts and Activity Feed

### Intelligence
- Live 3D Brain
- Primary Brain / Orchestrator
- Secondary Brains and Model Routing
- Agents
- Workers and Co-workers
- Memory and Knowledge
- Tasks and Workflows

### Connections
- LLM Providers and Models
- APIs and Credentials
- Tools
- Skills
- MCP Servers
- Repositories
- Knowledge Sources
- Integrations

### Operations
- Live Monitoring
- Logs and Distributed Traces
- Diagnostics
- Auto Repair
- Usage and Costs
- Security and Permissions
- Settings

### Desktop
- Quick Control
- System Tray
- Notifications
- Global Shortcut
- Emergency Stop

## 6. Core functional requirements

### FR-01 Command Center
Show current system state, active workers, running jobs, queue depth, success/failure rates, provider health, recent incidents, usage and pending approvals. Every metric must include a source, time window, last-updated timestamp and data-quality state.

### FR-02 Live 3D Brain
Render a selectable graph of actual registered components and runtime relationships:
- Primary orchestrator
- Secondary model endpoints
- Agents and workers
- Memory stores
- Tools and skills
- MCP servers
- APIs and providers
- Databases and queues
- Repositories and knowledge sources

Show live execution paths and data-flow events. Node color and animation must reflect backend state. Support search, filters, zoom, pan, node details, graph minimap, time-window replay and 2D fallback. Never invent nodes, edges or activity.

### FR-03 Primary and Secondary Brains
Show routing decisions, selected model, provider, capability constraints, fallback chain, latency, context/token usage, error state and reason for selection. The primary orchestrator owns task planning and delegation; specialized agents perform bounded work.

### FR-04 Workers and Co-workers
Show identity, role, parent, collaborators, assigned task, status, model, capabilities, tools, permissions, memory scopes, execution history, usage, errors and heartbeat. Support pause, resume, cancel and retry according to worker state and permissions.

### FR-05 Integration Registry
Manage provider endpoints, API connections, OAuth connections, MCP servers, repositories, tools, skills and knowledge sources. Each connection has configuration, credential reference, capabilities, permissions, health, last test, last successful use, rate limits, errors and dependent workers. Secrets must never be returned to the browser after saving.

### FR-06 Memory
Support working, short-term, long-term, episodic, semantic, procedural and project memory where the existing design requires them. Track owner, scope, source, timestamp, retention, sensitivity classification, retrieval reason and task association. Provide inspect, search, export and user-controlled deletion/retention workflows.

### FR-07 Tasks and Workflows
Support queued, scheduled, running, waiting, paused, completed, failed, cancelled and approval-required states. Persist task state, dependencies, attempts, checkpoints, outputs, artifacts and trace IDs. Support restart recovery and idempotency.

### FR-08 Observability
Capture structured logs, metrics and distributed traces. Correlate user request → orchestration → model call → agent/worker → memory → tool/MCP/API → output → verification. Redact credentials and sensitive payloads.

### FR-09 Diagnostics and Repair
Detect provider outages, authentication failures, rate limits, quota exhaustion, MCP disconnects, tool failures, worker crashes, queue stalls, database problems and resource exhaustion. Diagnose using evidence. Offer a repair plan, risk score, expected impact, rollback plan and verification tests.

Automatic repair is allowed only for explicitly allowlisted low-risk actions, such as bounded retry, reconnect, restart of a stateless worker, or switching to a pre-approved fallback. Approval is required for code changes, schema changes, credential rotation, permission changes, destructive actions, data migrations and production deployments.

### FR-10 Usage and Cost
Attribute model tokens, API requests, tool invocations, task duration and estimated or actual cost to provider, model, worker, task and project. Clearly distinguish provider-reported billing from estimates.

### FR-11 Desktop Companion
Build a Windows companion using Tauri if compatible with the audited project. Provide system tray, configurable global shortcut, authenticated local control channel, notifications, mini dashboard, voice entry point if the existing voice stack supports it, pause/resume, task cancellation and emergency stop. Desktop controls must invoke backend APIs and reflect confirmed backend responses.

### FR-12 Daily Briefing
On startup, show cached state immediately and refresh asynchronously. Summarize scheduled tasks, events, deadlines, overdue work, important alerts, news sources and recommended priorities when corresponding integrations are connected. Show missing permissions and data freshness.

## 7. Non-functional requirements
- Security: least privilege, encrypted secrets, OAuth where applicable, RBAC, audit trail, CSRF protections, secure desktop IPC and strict origin checks.
- Reliability: persistent jobs, idempotency keys, bounded retries, dead-letter handling, checkpoints and restart recovery.
- Performance: lazy-load heavy 3D assets; target smooth interaction on supported hardware; provide reduced-motion and 2D modes.
- Accessibility: keyboard navigation, visible focus, semantic controls, contrast and screen-reader labels.
- Maintainability: typed contracts, modular services, migrations, automated tests and documented runbooks.
- Privacy: explicit scopes, retention controls, redaction and no indiscriminate ingestion of all user content.

## 8. Data and state model
Core entities:
- User, Role, Permission, Session
- Provider, Model, Capability, CredentialReference
- Integration, APIConnection, MCPServer, Repository, KnowledgeSource
- Tool, Skill, ToolExecution
- Agent, Worker, WorkerRelationship, WorkerHeartbeat
- Task, Workflow, TaskDependency, TaskAttempt, Checkpoint, Artifact
- MemoryItem, MemoryCollection, MemoryAccessEvent
- Incident, DiagnosticRun, RepairPlan, RepairExecution, Approval
- LogEvent, MetricSample, Trace, CostRecord, Notification

Use stable IDs and timestamps. Store timestamps in UTC; render in the user's configured timezone. Prefer append-only audit and event records for sensitive operations.

## 9. Backend service boundaries
1. API Gateway / Backend-for-Frontend
2. Identity and Authorization
3. Orchestrator
4. Model Gateway and Capability Registry
5. Agent / Worker Runtime
6. Task and Workflow Service
7. Integration and Credential Registry
8. Tool / Skill Registry and Execution Gateway
9. MCP Gateway
10. Memory Service
11. Observability Pipeline
12. Health and Diagnostics Service
13. Repair Policy and Execution Service
14. Usage and Cost Service
15. Notification Service
16. Desktop Control API

Do not split into microservices solely for fashion. Preserve the existing deployment shape unless scale, isolation or ownership requires separation.

## 10. Real-time event contract
Use WebSocket or SSE for typed events such as:
- system.health.changed
- provider.health.changed
- worker.status.changed
- worker.heartbeat
- task.created / task.started / task.progress / task.completed / task.failed
- model.call.started / model.call.completed
- tool.call.started / tool.call.completed / tool.call.failed
- memory.retrieval / memory.write
- integration.test.completed
- incident.created / incident.updated
- repair.proposed / repair.approval_required / repair.started / repair.verified / repair.rolled_back

Every event should include event ID, timestamp, tenant/user scope, correlation ID, source component and schema version.

## 11. Acceptance criteria
- Every displayed connection state is backed by a real test or health result, or labeled demo/unverified.
- A task can be followed end-to-end by one correlation ID.
- Worker state survives backend restart or is accurately reconciled.
- 3D graph nodes and edges match the backend registry and runtime telemetry.
- Failed integrations show actionable diagnostics, not generic green status.
- A fallback model is used only if capability and policy checks pass.
- Safe repairs are allowlisted, bounded, logged and verified.
- Risky repairs require explicit approval.
- Rollback is tested for supported repair classes.
- Desktop controls require authentication and reflect actual backend results.
- Critical flows have automated tests and documented manual verification.
- No secrets appear in logs, traces, browser payloads or screenshots.

## 12. Demo data policy
The supplied images are visual references only. Build a demo mode with clearly marked synthetic data. Demo mode must be isolated from production state and must never make simulated activity look live.
