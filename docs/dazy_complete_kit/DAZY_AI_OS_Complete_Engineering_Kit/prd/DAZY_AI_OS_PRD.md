# DAZY AI OS — Product Requirements Document

## 1. Product vision

DAZY AI OS is a single, lightweight, extensible personal AI command center that brings the user's profile, daily briefing, primary orchestrator, optional specialist runtimes, models, agents, workers, co-workers, memory, tasks, tools, skills, MCP servers, APIs, GitHub repositories, diagnostics and desktop controls into one coherent product.

It must be operational rather than decorative. The web dashboard, desktop companion and 3D brain must all reflect the same backend source of truth. Expensive components must be demand-loaded for an 8 GB Windows computer.

## 2. Fixed user decisions

- Platforms: web + Windows desktop companion.
- 3D: full interactive 3D brain and infrastructure graph, with 2D fallback.
- Repair: safe, allowlisted repairs may run automatically; risky repairs require approval.
- Hardware: 8 GB RAM; low-resource profile enabled by default.
- Display name: Tarik. Do not show “John”, “Alex” or any placeholder identity in a real user's dashboard.
- Supplied projects: Nanobot, AgenticSeek, OpenManus and n8n are candidates to evaluate as optional integrations, not four mandatory always-on services.

## 3. Goals

1. Correctly identify and address the authenticated user as Tarik.
2. Provide an accurate command center for all DAZY components.
3. Discover and evaluate repositories, tools, skills, MCP servers and automation projects.
4. Integrate external agent runtimes behind stable adapters.
5. Keep one primary orchestrator and one shared backend per DAZY instance.
6. Keep 8 GB hardware usable through bounded concurrency and demand-loaded components.
7. Make all execution paths, memory access, tool calls, errors, usage and repairs inspectable.
8. Maintain safe, user-approved automation and self-repair.

## 4. Non-goals

- Do not install or run all candidate repositories by default.
- Do not embed n8n source into DAZY without license review.
- Do not combine GPL-3.0 AgenticSeek code into a DAZY distribution without a proper compatibility review.
- Do not run local heavyweight LLMs by default on an 8 GB system.
- Do not run duplicate orchestrators, duplicate databases or duplicate worker pools.
- Do not treat decorative 3D animation as live telemetry.
- Do not silently delete files, change credentials, send messages, publish, or deploy.

## 5. Main navigation

### Home
- Command Center
- Daily Briefing
- Notifications / Approval Inbox

### Intelligence
- Live 3D Brain
- Primary Brain / Orchestrator
- Secondary Brains / Specialist Runtimes
- Workers & Co-workers
- Memory & Knowledge
- Tasks & Schedules

### Ecosystem
- LLMs & Models
- APIs & Connections
- Tools
- Skills
- MCP Servers
- Repositories
- **Repo Radar / Discover Projects**
- Library & Knowledge Sources
- Workflow Automation

### Operations
- Resource Monitor
- Logs & Traces
- Diagnostics
- Auto Repair
- Usage & Costs
- Security & Permissions
- Settings

### Desktop
- Quick Controls
- System Tray
- Notifications
- Global Shortcut

## 6. Identity and personalization requirements

- Authenticated account identity is the canonical identity source.
- Store an editable `displayName` in the user's DAZY profile.
- For this installation, the intended display name is `Tarik`.
- Resolution precedence: user-editable DAZY profile display name → verified identity-provider display name → neutral greeting (“Welcome back”) until setup is complete.
- Never use a static fallback such as John, Alex, User 1 or Demo User in production.
- Separate `displayName`, `legalName`, `email`, `providerSubject`, `avatarUrl` and `timezone`. Do not infer email or legal name.
- Profile editing must update the canonical profile API, not only frontend local state.
- On login, refresh, token renewal, desktop launch, web launch and worker prompt construction, load the same user profile.
- Keep demo identities only in isolated demo fixtures and visibly label Demo Mode.
- The main UI header, greeting, assistant prompt context, notification templates and desktop tray must all use the canonical profile value.

## 7. Main dashboard requirements

### Top bar
- DAZY logo and environment badge.
- Global search / command palette.
- System connectivity state.
- Local date/time and configured timezone.
- Notifications and approvals.
- User avatar and **Tarik** display name, bound to profile data.
- Resource-pressure indicator.

### Summary cards
- Active workers.
- Running / queued tasks.
- Primary model status.
- Integration health.
- RAM / CPU / GPU / disk pressure.
- Estimated/actual usage and cost.

### Main canvas
- Interactive 3D brain graph, loaded only after the user opens it or enables a compact preview.
- 2D graph alternative.
- Node inspector and execution-path trace.
- Current task timeline.

### Right rail
- Live activity.
- Upcoming tasks and deadlines.
- Connection alerts.
- Repair proposals awaiting approval.
- Current resource warnings.

### Lower panels
- Integration manager.
- Tasks and workflow list.
- Usage analytics.
- Memory activity.
- Repo Radar / new project discoveries.
- Diagnostics and recent incidents.

## 8. Repo Radar requirements

Repo Radar is inspired by the workflow of discovering and curating useful AI/agent projects from GitHub and public developer feeds, including the user's Tom Dörr reference. It is a first-class main UI feature.

Features:
- Accept pasted GitHub repository URLs.
- Search connected GitHub repositories with the GitHub integration.
- Maintain a user-curated watchlist of sources and creators. Do not scrape X or other platforms without an allowed API/feed and user permission.
- Show repository description, primary language, license, default branch, last update, latest release, archived status, open issues/PR activity and official links.
- Show capabilities: agent runtime, browser automation, MCP, scheduler, memory, tools, skills, UI, API, workflow engine.
- Analyze Python/Node dependencies, installation steps, Docker requirements, optional services and model requirements.
- Produce a resource classification: suitable for local 8 GB evaluation, remote-only, or not recommended without benchmarking. Never invent exact RAM consumption.
- Perform static analysis and license review before proposing installation.
- Offer sandboxed, one-at-a-time evaluation with explicit user approval.
- Show adapter options: built-in adapter, external service adapter, optional worker, link-only reference, or reject.
- Track provenance, fetched date, source revision and evaluation status.
- Do not clone or install automatically from an X post.

## 9. Agent and runtime requirements

DAZY owns a single primary orchestrator. Specialist systems are adapters with bounded capabilities. No imported project may quietly become a second primary brain.

### Runtime adapters
- Nanobot adapter: personal-agent capabilities, memory/tool/automation concepts and optional Python SDK/runtime bridge.
- OpenManus adapter: on-demand complex task execution.
- AgenticSeek adapter: optional isolated browser/coding runtime, preferably remote or separate machine if local resource pressure is high.
- n8n adapter: external workflow service through API/webhooks; no always-on local n8n requirement.

Every adapter includes connection test, capability discovery, permission list, health, version, resource policy, usage, logs and disable/uninstall instructions.

## 10. 8 GB operating requirements

- Low-resource profile enabled by default.
- One backend instance shared by web and desktop.
- One shared worker pool; initial concurrency one, increase to two only after measurements prove safe.
- Use hosted API models by default; local models disabled unless a small model is explicitly selected and profiled.
- Specialist runtimes start only for assigned tasks.
- MCP and API connections connect on demand where possible and close idle sessions.
- 3D scene lazy loaded, capped/adaptive frame rate and paused when hidden.
- Memory retrieval is scoped and paginated.
- Logs, caches and artifacts have configurable retention.
- Database and queue instances are shared; do not start duplicate services.
- Resource pressure suspends nonessential work safely, not active user data.
- 2D fallback remains functional.

## 11. Repair and security

- Every incident includes evidence, scope, impact, confidence and correlation ID.
- Safe allowlisted actions: bounded retry with backoff, reconnect a known session, restart a stateless worker, choose a pre-approved compatible model fallback.
- Approval required: code changes, database migrations, credential rotation, permission changes, deletion, external publication, sending communications, production deployment, destructive cleanup.
- Repair runner uses least privilege and isolated execution.
- Back up before supported risky actions; verify and rollback.
- Never echo secrets in logs or frontend.
- Repositories are untrusted input. Never follow README commands blindly or run post-install scripts outside a sandbox.

## 12. Acceptance criteria

1. Real UI shows Tarik from the canonical profile; tests assert no production greeting says John/Alex.
2. Web and desktop show identical profile and system state.
3. Web and desktop do not launch duplicate backends.
4. Repo Radar can inspect a repository without cloning it.
5. Repository license and source links are visible before install.
6. Each external runtime can be enabled/disabled independently.
7. No optional runtime starts automatically on an 8 GB machine.
8. A request has one trace from primary orchestration through adapter and tool calls.
9. The 3D brain matches backend graph snapshots and telemetry.
10. Resource pressure reduces nonessential work and does not lose task state.
11. Risky repairs wait for explicit approval.
12. Demo data is always visibly marked and cannot contaminate real user profile or telemetry.
