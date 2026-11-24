# DAZY Real-Use Test Matrix and User Journeys

Use this matrix as the Testing Center catalog. Every test run should record environment, build commit, test user, integration account alias, test ID, correlation ID, start/end time, result and evidence links.

## A. Identity and user profile
- Login as the dedicated DAZY test user.
- Verify `/api/me` returns the right profile.
- For the user's primary profile, verify display name is Tarik.
- Refresh browser; confirm name persists.
- Sign out/in; confirm correct profile reloads.
- Launch Windows desktop; confirm same profile.
- Change display name in settings; verify header, daily briefing, worker prompt and desktop update.
- Empty profile must show neutral welcome, never John.
- Verify one user's profile is never visible to another test account.

## B. Daily briefing, calendar, tasks and dates
- Test timezone Asia/Kolkata and daylight/timezone edge cases.
- Create a test event and read it back.
- Create a task with due date; mark complete.
- Create recurring schedule; pause/resume.
- Verify duplicate event prevention and idempotency.
- Test overdue, upcoming, conflicting and cancelled events.
- Test unavailable provider and expired OAuth.
- Test one real read-only calendar sync using a dedicated test calendar.

## C. LLM provider and routing
- Test each configured provider's credential health.
- Test a small text generation request.
- Test supported structured output.
- Test vision/audio/tool capability only where provider supports it.
- Verify model chosen against capability registry.
- Force a timeout in staging; verify bounded retry.
- Force rate limit; verify cooldown.
- Make preferred model unavailable; verify only approved compatible fallback.
- Verify secrets never appear in trace, UI or logs.
- Record token count, latency and estimated cost where returned.

## D. Agents, workers and co-workers
- Primary orchestrator receives a task and creates a plan.
- Worker assigned with minimum permission.
- Worker heartbeat updates actual status.
- Co-worker collaboration records handoff and result.
- Cancel task during execution; verify graceful stop.
- Crash a disposable worker; verify lease expiry and recovery.
- Restart backend; verify queued/checkpointed jobs recover without duplicate side effects.
- Test max concurrency one under Low Resource Mode.
- Test no worker reads another user's memory or files.

## E. Memory and knowledge
- Save a user-approved memory.
- Verify memory provenance and owner.
- Retrieve by exact keyword and semantic query.
- Verify irrelevant memory is not injected.
- Test retention/expiry and user deletion flow.
- Test memory service unavailable.
- Verify memory access event appears in trace.
- Confirm sensitive content is not automatically stored as long-term memory.

## F. Tools and skills
- Discover tool and schema.
- Validate good input.
- Reject invalid types, missing fields and out-of-scope paths.
- Test timeout and error mapping.
- Test skill trigger and non-trigger cases.
- Verify skill only receives required permissions.
- Verify tool output treated as untrusted data.
- Test tool version mismatch and disabled tool.
- Verify tool usage attributed to run and worker.

## G. MCP servers
- Connect using approved credentials.
- Discover tools/resources/prompts.
- Validate each input schema.
- Execute one harmless read-only tool.
- Test timeout, disconnection and reconnect.
- Test unauthorized tool denied.
- Ensure server-provided prompt/tool description cannot override system policy.
- Close idle connection and verify no resource leak.
- Use MCP Inspector and retain its sanitized output.

## H. Repository Radar
- Search known public repository and paste a URL.
- Verify owner, URL, license, default branch and revision.
- Inspect README and dependency manifests.
- Verify archived state and last activity.
- Verify license warning for GPL-3.0 and n8n Sustainable Use License.
- Ensure resource footprint is marked not benchmarked if not measured.
- Compare repository capabilities with DAZY registry.
- Ensure no clone or install occurs until approval.
- Test malformed URL, private repo without permission, rate limit and inaccessible repo.

## I. Automation and n8n
- Create a test workflow/webhook in a sandbox.
- Validate authentication.
- Send synthetic payload and verify task appears in DAZY.
- Verify idempotency on duplicate webhook.
- Test n8n offline and credential revoked.
- Ensure no external side effect without user approval.
- Test webhook signature/authentication and replay policy.

## J. Browser automation / OpenManus / AgenticSeek
- Use a dedicated test website and dummy login.
- Run one read-only navigation task.
- Run allowed form fill against a mock/sandbox page.
- Block external network destinations by default.
- Attempt disallowed local file access; verify denial.
- Attempt destructive action; verify approval gate.
- Test cancellation, child process cleanup and timeout.
- Verify output artifact, screenshot and trace are attached to task.

## K. 3D Brain and resource UI
- Open brain route; verify graph snapshot nodes match registry.
- Trigger one test task; verify edge animation corresponds to real events.
- Disconnect telemetry; graph shows stale/offline, not live.
- Hide tab; animation loop stops.
- Navigate away/back repeatedly; no unbounded GPU/heap growth.
- Simulate WebGL unavailable/context lost; 2D fallback works.
- Search/filter/select nodes and inspect actual backend metadata.
- Ensure demo graph is explicitly labeled.

## L. Diagnostics and repairs
- Inject transient provider timeout; safe retry only.
- Disconnect test MCP; safe reconnect.
- Crash stateless test worker; safe restart.
- Submit code modification repair; approval required.
- Submit destructive file cleanup; approval required.
- Fail post-repair verification; rollback.
- Verify full audit record includes who/what/why/when/evidence.
- Verify repair agent cannot change its own permissions/policy.

## M. Desktop companion
- Install and launch Windows package.
- Verify it connects to existing backend and does not start duplicate backend.
- Test tray open/close and global shortcut.
- Test notifications.
- Test pause/resume/cancel with backend confirmation.
- Test emergency stop requires confirmation and preserves job state.
- Test backend offline/reconnect behavior.
- Test upgrade/uninstall without deleting user data.

## N. Security and tenancy
- Unauthenticated endpoints return appropriate denial.
- Cross-user access denied.
- RBAC denies unauthorized admin operations.
- CSRF/CORS/SSRF checks.
- File path traversal tests.
- Prompt injection via retrieved webpage/tool output does not bypass policy.
- Secrets redacted.
- Audit log tamper resistance.
- Dependency and container vulnerabilities triaged.
- ZAP only against a permitted staging URL.

## O. Performance and stability
- Baseline idle for 10 minutes.
- Typical use: chat + one worker + one browser tab.
- 3D active for 5 minutes, then idle.
- 25 repeated open/close cycles for 3D route.
- 30-minute integration soak with low concurrency.
- Backend restart while tasks are queued.
- Build clean and incremental; record duration.
- Check storage growth and logs after tests.
- Larger load test on CI/staging runner, not the user's 8 GB workstation.
