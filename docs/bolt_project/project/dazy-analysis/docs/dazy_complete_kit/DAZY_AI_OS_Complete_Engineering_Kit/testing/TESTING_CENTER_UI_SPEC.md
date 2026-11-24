# DAZY Testing Center — Main UI Specification

Add a dedicated **Testing Center** navigation item and a compact dashboard card.

## Overview
- Last full test run.
- Pass/fail/blocked/not-run counts.
- Build SHA and environment.
- Live vs mocked integration coverage.
- Critical open defects.
- Resource impact of the test suite.

## Sections
1. Quick Health Check — backend, database, queue, profile, model gateway.
2. User Journeys — Playwright web and Tauri desktop flows.
3. Integration Lab — providers, APIs, calendar/email/task integrations.
4. Agent Evaluation — datasets, tool choice, safety, cost and latency.
5. Tools / Skills — schemas, permission tests and execution traces.
6. MCP Inspector — server connections, capability discovery and invocation history.
7. Repo Radar Tests — metadata, license, dependency and sandbox review.
8. Memory — write/retrieve/provenance/retention/privacy.
9. 3D Brain — graph parity, event streaming, WebGL and leak tests.
10. Security — SAST, secret, dependency, DAST and RBAC.
11. Performance — resource baseline, k6, build profiles and soak.
12. Desktop — install/launch/tray/shortcut/IPC/notifications/reconnect.
13. Release Gate — blocking failures and evidence checklist.

## Real-use controls
- Run selected test.
- Run safe smoke suite.
- Select staging account alias.
- Select real integration connection (show scopes first).
- View request/response with secrets redacted.
- Download report.
- Cancel run.
- Require approval for destructive or side-effecting tests.

Every result carries:
- REAL / MOCKED / SIMULATED / NOT TESTED label.
- Environment and account alias.
- Timestamp and build version.
- Correlation ID.
- Logs and trace link.
- Expected vs actual.
- Evidence artifact.
