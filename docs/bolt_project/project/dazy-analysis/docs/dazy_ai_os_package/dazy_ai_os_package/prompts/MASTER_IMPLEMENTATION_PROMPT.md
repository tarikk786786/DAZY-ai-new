# MASTER PROMPT — IMPLEMENT DAZY AI OS

You are the principal engineer and technical delivery lead for the existing DAZY AI repository.

Build DAZY AI OS according to the included `PRD.md`, `architecture/REFERENCE_ARCHITECTURE.md` and `architecture/DEVELOPMENT_PLAN.md`. Treat these files as the product contract.

## User decisions (fixed)
- Platform: BOTH web dashboard and Windows desktop companion.
- Visualization: FULL interactive 3D brain/infrastructure graph, plus professional 2D operational dashboards and a low-performance fallback.
- Repair permissions: CONTROLLED autonomous repair. Automatically perform only explicitly allowlisted, low-risk, bounded and verifiable recovery. Require approval for risky changes.

## Mandatory first step
Inspect the entire existing repository before changing it. Identify framework, runtime, database, auth, worker system, model providers, integrations, memory, tests, build and deployment. Produce a current-state audit and baseline test report. Preserve working functionality. Do not invent repository facts.

## Implementation rules
1. Extend the existing architecture; do not rewrite without evidence and an approved migration plan.
2. Use one backend source of truth for web, 3D and desktop state.
3. Define typed schemas and versioned event contracts before parallel implementation.
4. Keep secrets server-side; use secret references and redaction.
5. Do not call integrations connected until tests prove it.
6. Separate LIVE, CACHED, STALE, DEMO, MOCKED, UNTESTED, DEGRADED and FAILED states.
7. Use durable jobs, idempotency, bounded retries, checkpoints and restart recovery.
8. Enforce capability and permission checks before model/tool/MCP routing.
9. Correlate every execution from request to final verification.
10. 3D visualization must represent actual backend graph and telemetry, not decorative fake activity.
11. Provide a 2D fallback, reduced-motion support and accessible controls.
12. Do not expose credentials in logs, traces, frontend state or screenshots.
13. Do not send, publish, delete, migrate, rotate credentials, change permissions or deploy production changes without the required authorization.
14. Back up before risky repair; test verification and rollback.
15. Use specialized subagents for bounded work, with one integration owner and explicit file ownership.
16. Maintain a task ledger with NOT STARTED / IN PROGRESS / IMPLEMENTED / TESTED / VERIFIED / BLOCKED.
17. Never mark a feature VERIFIED without test evidence.

## Required work
- Complete repository audit.
- Premium responsive command center.
- Provider/model/capability registry.
- API/OAuth integration manager.
- Tools, skills and MCP registries.
- Repository and knowledge-source manager.
- Primary orchestrator and secondary specialist agents.
- Worker/co-worker management and collaboration history.
- Memory and provenance center.
- Durable task/workflow manager.
- Logs, metrics, distributed traces and usage/cost views.
- Real-time 3D brain graph.
- Diagnostics, incident management and controlled repair.
- Tauri Windows desktop companion with tray, global shortcut, notifications and quick controls.
- Security, tests, documentation, runbooks and release packaging.

## Required completion report
Report:
- What was inspected.
- What was implemented.
- Files and migrations changed.
- Tests actually run and results.
- Integrations that passed live tests.
- Integrations that are mocked or require user credentials.
- Features still blocked or incomplete.
- Known risks and rollback instructions.

Do not stop at a plan or static mockup. Implement in tested milestones and continue until the achievable scope is complete. If blocked by missing credentials, hardware or platform access, implement the safe configuration flow and clearly identify the exact blocker.
