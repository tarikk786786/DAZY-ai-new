# DAZY AI OS — Real-Use Testing & Verification Stack

**Target:** Existing DAZY repository, Web + Windows desktop, 8 GB RAM  
**Purpose:** Verify real user flows, actual configured providers, agents, workers, memory, tools, skills, MCP, repositories, automation, repair, telemetry and resource use.

## 1. Recommended stack (do not install everything as a permanent service)

| Layer | Recommended tool | What it verifies | Run policy |
|---|---|---|---|
| Frontend unit/component | Vitest + Testing Library | Components, state, hooks, error states | Local, fast |
| Backend tests | pytest (Python) / existing project test runner | Business logic, agents, memory, workers | Local, fast |
| Web E2E | Playwright | Real browser journeys, screenshots, network, console | Local/CI, one worker on 8 GB |
| Desktop E2E | WebdriverIO + `@wdio/tauri-service` | Actual Tauri app, IPC, notifications, frontend/backend logs | Windows test machine/CI |
| API manual + collections | Bruno | Human-driven and repeatable real API calls | Developer workstation |
| API schema/property tests | Schemathesis | OpenAPI edge cases, response/schema failures, multi-step API behavior | Staging or disposable test DB |
| MCP | MCP Inspector (Web/CLI/TUI) | Connect, list tools/resources/prompts, invoke with test data, inspect errors | On demand |
| LLM / agent evals | Promptfoo | Golden datasets, model comparisons, regressions, red-team tests | CI or small local batches |
| LLM traces/evaluation UI | Langfuse **or** existing telemetry platform | Prompt/model/tool traces, datasets, scoring, experiments | Prefer hosted/existing service; do not add another local stack unnecessarily |
| Distributed observability | OpenTelemetry SDK + existing OTLP collector/backend | Correlated traces, metrics and logs across DAZY | Minimal instrumentation always on |
| Load/performance | Grafana k6 | API latency, throughput, error rates, thresholds, soak | Staging/CI; tiny smoke only on 8 GB PC |
| Accessibility | axe-core + Playwright; manual Accessibility Insights | Labels, focus, contrast and WCAG-related issues | CI + manual release pass |
| Web performance | Lighthouse CI | Web vitals and bundle/performance budgets | CI; one browser run locally |
| Static code security | Semgrep | Source patterns and insecure coding patterns | CI / pre-commit |
| Dependency/container/filesystem security | Trivy | Vulnerabilities, misconfiguration and exposed secrets | CI / release |
| Secret scan | Gitleaks | Accidental tokens in files and Git history | Pre-commit + CI |
| Dynamic web security | OWASP ZAP | Passive/active web and API security checks | Staging only; active scan with approval |
| Python coverage | coverage.py + pytest-cov | Line/branch coverage and report | CI |
| Windows resource profiling | Task Manager, Resource Monitor, Process Explorer, Performance Monitor | Real per-process RAM/CPU/disk and process tree | Manual on actual 8 GB PC |
| Python profiling | cProfile + tracemalloc; py-spy where supported | Hot functions, allocation growth, leaks | On demand |
| Node profiling | Node CPU/heap profiles + Chrome DevTools | CPU hot paths, heap growth, retained objects | On demand |
| 3D/WebGL debugging | Browser DevTools + WebGL diagnostics/Spector.js | Draw calls, textures, shaders, frame timing, context loss | On demand |

### Minimum recommended install set
Start with the test tools that fit the actual DAZY stack:
- Playwright for web end-to-end.
- Existing JS unit test runner (Vitest if Vite/React).
- pytest if Python backend; otherwise keep the current backend test framework.
- Bruno for API collections.
- MCP Inspector when testing MCP connections.
- Promptfoo for reproducible agent/model evaluation.
- OpenTelemetry instrumentation for traces.
- Trivy + Semgrep + Gitleaks for code/dependency/security gates.

Add k6, ZAP, Langfuse, desktop WebDriver and full system metrics only when the related milestone needs them.

## 2. Why these choices
- Playwright runs browser E2E tests across Chromium, Firefox and WebKit and provides trace/screenshot/debug tooling. Use Chromium-only for the local 8 GB test loop. See official docs: https://playwright.dev/docs/intro and https://playwright.dev/docs/trace-viewer
- Tauri's official test guidance recommends WebdriverIO with `@wdio/tauri-service` for native desktop E2E; this can test Tauri commands and capture frontend/backend logs. See https://tauri.app/develop/tests/ and https://tauri.app/develop/tests/webdriver/
- MCP Inspector supports browser, CLI and TUI inspection of MCP servers. See https://modelcontextprotocol.io/docs/tools/inspector and https://github.com/modelcontextprotocol/inspector
- Schemathesis generates API tests from OpenAPI/GraphQL schemas, including edge cases and chained workflows. See https://schemathesis.readthedocs.io/
- Promptfoo supports repeatable LLM eval and red-team workflows. See https://www.promptfoo.dev/docs/guides/
- Langfuse evaluations can combine traces, datasets, online scoring and offline experiments. See https://langfuse.com/docs/evaluation/overview
- OpenTelemetry standardizes traces, metrics and logs. See https://opentelemetry.io/docs/concepts/signals/
- k6 supports load tests and threshold-based pass/fail criteria. See https://grafana.com/docs/k6/latest/ and https://grafana.com/docs/k6/latest/using-k6/thresholds/
- axe-core can automate detection of common accessibility problems, but manual accessibility review remains necessary. See https://playwright.dev/docs/accessibility-testing
- Trivy scans filesystems for vulnerabilities, misconfiguration and secrets; Semgrep provides static analysis; OWASP ZAP provides automated dynamic scans. See links in `TOOL_LINKS.md`.

## 3. Required test environments
Create three isolated environments:
1. **Local Dev:** mock services, test database, disposable files, no production credentials.
2. **Integration/Staging:** actual configured provider accounts and integrations with minimum scopes; synthetic test data; no live destructive actions.
3. **Production Read-only Smoke:** only safe health/read operations. Never run fuzzing, load tests, destructive actions or active ZAP scans against production.

Use a dedicated DAZY test user and separate test workspace. Do not impersonate the real user's account. Keep the production profile name Tarik; use explicit fixture accounts for test identities.

## 4. Real connection testing: the correct status model
Every connection must have separate outcomes:
- CONFIGURED
- REACHABLE
- AUTHENTICATED
- CAPABILITIES_DISCOVERED
- PERMISSIONS_VERIFIED
- FUNCTIONAL_SMOKE_PASSED
- DEGRADED
- RATE_LIMITED
- FAILED
- NOT_TESTED

A green "connected" label is permitted only after required stages pass. Distinguish MOCKED from REAL TESTED. Store test timestamp, account/tenant label, endpoint host, scopes (not tokens), version, test case ID, correlation ID and sanitized evidence.

## 5. Test layers
1. Unit: deterministic functions, profile resolution, policy rules, state reducers.
2. Component: UI widgets, loading/empty/error/offline and permission states.
3. Contract: API schemas, tool schemas, MCP input/output schemas, adapter request/response.
4. Integration: database, queue, providers, memory store, tools and real sandbox integrations.
5. E2E: complete user journeys through web and desktop.
6. Evaluation: LLM/agent answer quality, tool choice, safety and task completion.
7. Reliability: timeouts, rate limits, expired credentials, worker crash/restart, DB unavailable.
8. Security: auth, RBAC, secrets, injection, SSRF, file access and audit.
9. Performance: CPU/RAM/GPU/DB, latency and throughput.
10. UAT: real human checks against acceptance criteria.

## 6. 8 GB execution rule
Do not run all suites simultaneously.
- Developer loop: unit tests + changed backend tests.
- Web pass: Playwright, one worker, Chromium only.
- Integration pass: one integration group at a time.
- Security pass: Trivy/Semgrep/Gitleaks sequentially.
- LLM eval pass: small dataset, concurrency 1.
- Performance pass: small k6 smoke locally; larger load tests on a separate CI/staging runner.
- Desktop pass: only when building the Tauri milestone.
- Do not keep Langfuse, Grafana, Prometheus, Loki, Jaeger, ZAP, n8n and databases all running locally. Use an existing hosted/remote test backend or start individual tools only when needed.

## 7. Release gate
A feature is not "verified" unless:
- Expected behavior is tested.
- Failure path is tested.
- Permission path is tested.
- Evidence is saved.
- No critical security issue remains.
- Resource impact is measured for expensive features.
- Human UAT passes for the primary workflow.

Code coverage is supporting evidence, not proof of quality. Focus on high-risk paths and branch behavior rather than chasing a vanity percentage.
