# DAZY Tools, Skills, MCP and Integration Catalogue

## 1. Registry design

Use a common registry with separate records for providers, models, tools, skills, MCP servers, runtime adapters, APIs and repository sources.

Every item exposes:
- Stable ID and version.
- Name, description, owner/source and official URL.
- Category and capabilities.
- License / terms reference where applicable.
- Required permissions.
- Configuration schema.
- Credential reference (never secret value).
- Health and last test.
- Enabled / disabled state.
- Resource profile and dependencies.
- Last used and usage counts.
- Compatible workers/agents.
- Logs and error history.
- Install / update / disable / uninstall plan.

## 2. Tool categories

### Core tools
- Clock and timezone.
- Calendar/tasks CRUD with approval rules.
- Search and source fetch.
- Filesystem read/write with scope control.
- Database read/write through approved service.
- Notifications.
- Scheduler.
- GitHub repository metadata and source inspection.
- Diagnostics and resource inventory.

### Research tools
- Search providers.
- RSS/news feed reader.
- GitHub repository search.
- Release/commit/activity checker.
- Documentation crawler.
- Deduplication and source credibility scorer.

### Developer tools
- Git read/status/diff.
- Test runner in sandbox.
- Dependency inventory.
- License scanner.
- Vulnerability scanner.
- Build profiler.
- Repository graph/indexer.

### Desktop tools
- Open dashboard.
- Show notification.
- Read safe system resource counters.
- Pause/resume/cancel DAZY jobs.
- Emergency stop (confirmation).
- No unrestricted shell access exposed to a model.

## 3. Skills catalogue

Skills are versioned, reviewed instruction bundles; they are not automatically trusted code.

Recommended DAZY built-in skills:
1. Daily Briefing — tasks, events, dates, news and priorities.
2. Repository Auditor — source tree, architecture, tests, dependencies.
3. Repo Radar Evaluator — GitHub metadata, license, requirements and risk.
4. Adapter Builder — create typed wrappers to external runtimes.
5. Tool/MCP Inspector — schema, auth, connectivity and permissions.
6. Worker Coordinator — delegation, leases, retries and handoffs.
7. Memory Curator — scoped retrieval, dedupe and provenance.
8. Performance Auditor — RAM/CPU/GPU/disk/build diagnostics.
9. Safe Repair Planner — diagnose, propose, approve, verify, rollback.
10. Test Engineer — unit, integration, contract and end-to-end tests.
11. Source Verifier — citations, dates and duplicate detection.
12. Desktop Companion Operator — tray, shortcut and authenticated controls.

Each skill must specify inputs, outputs, required capabilities, permissions, risk class, version, tests and provenance.

## 4. MCP management

- Discover server tools/resources/prompts.
- Validate JSON schemas.
- Display exact tool names and descriptions.
- Show server health and session lifecycle.
- Connect on demand where possible.
- Close idle sessions according to policy.
- Restrict server filesystem/network access.
- Keep per-user and per-agent authorization scopes.
- Record tool call start/end/error with correlation ID.
- Treat tool outputs as untrusted data, never as privileged instructions.

## 5. Connection test stages

Do not reduce every integration test to a single green tick. Show:
1. Endpoint reachability.
2. TLS/certificate validity.
3. Authentication.
4. Capability discovery.
5. Permission scope.
6. Harmless functional test.
7. Rate limit/quota info if available.
8. Last successful end-to-end use.

Statuses: NOT CONFIGURED, UNTESTED, TESTING, CONNECTED, DEGRADED, AUTH FAILED, RATE LIMITED, UNAVAILABLE, DISABLED, DEMO.

## 6. Security baseline

- Secret values are write-only after save.
- Encrypt credentials at rest.
- Redact authorization headers and tokens.
- Use least privilege.
- Use allowlisted network egress.
- Separate user data scopes.
- Confirm external side effects.
- Record admin actions in append-only audit log.
