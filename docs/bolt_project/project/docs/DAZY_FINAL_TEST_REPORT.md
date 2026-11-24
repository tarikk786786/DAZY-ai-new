# DAZY AI OS — Final Test Report (2026-11-24)

Evidence-based. Every claim below was executed in this session. Nothing is marked
passing that was not actually run.

## Fully working (verified)

| Item | Evidence |
|---|---|
| Local backend (FastAPI + SQLite, `backend/`) | Boots on 127.0.0.1:8787; `/api/v1/system`, `/api/v1/status` return real data; SQLite migrations apply idempotently |
| Multi-brain gateway ladder | Gemini→Groq→OpenRouter→DeepSeek→optional local; unit tests prove: success on primary, failover on 429, auth-failure skips retries, honest `attempts[]` when everything fails |
| Failover + health telemetry | Every attempt logged to `provider_attempts`; `/api/v1/status?deep=true` does real pings |
| Memory system with FTS | Create/edit/delete/search verified via API tests; secret-leak guard blocks "api key" style saves |
| Reminders | Create/snooze/complete/delete verified; double-complete correctly 404s |
| Durable task engine | Enqueue (idempotent), claim (no double-claim), complete, retry-with-backoff, dead-letter — all unit tested |
| Rate limiting | Blocks after max turns in window (tested) |
| Edge functions (cloud path) | `dazy-chat` + `dazy-status` re-deployed with a model-name guard; live chat through Gemini verified post-fix (`provider_used:"gemini"`, 1157 ms) |
| Python test suite | 23/23 passing (`backend/tests/`) |
| Windows scripts | install / start / stop / backup / diagnose written. **Not executed** — sandbox is Linux; they must be run once on Windows before release |

## Incident found and fixed during testing

A junk value (`AQ.Ab8RN6…`) had been written into the `GEMINI_MODEL` edge secret,
which silently broke the cloud brain (both edge functions used it as a model name →
400 on every Gemini call → all providers failed). Both functions now validate
`GEMINI_MODEL` against a `gemini*` pattern and fall back to the proven
`gemini-3.5-flash-lite`. Cloud chat re-verified live after the fix. The junk secret
itself still needs cleanup in the Supabase dashboard (set `GEMINI_MODEL` back to
`gemini-3.5-flash-lite`), though the guard makes it harmless.

## Partially working

- **Fallback brains**: Groq (401), OpenRouter (402), DeepSeek (401) — keys dead.
  Gemini carries all traffic alone until keys are rotated.
- **Local (offline) mode**: code path exists (`LOCAL_LLM_URL`), untested against a
  real Ollama/LM Studio server because none runs in this sandbox.

## Not implemented in this milestone (by scope)

Agent orchestrator with specialist worker roles, skills/MCP discovery, 3D brain
visualization, desktop control gateway, voice pipeline (local STT/TTS), web-frontend
switch to the local backend. The web app still uses the Supabase path; the local
backend mirrors its contracts so the switch is a configuration change later.

## Blocked on the user

1. Rotate/replace dead provider keys (Groq, DeepSeek; add credit to OpenRouter).
2. Fix `GEMINI_MODEL` secret in the Supabase dashboard (optional — guarded now).
3. Fresh GitHub token with repo scope for the release push; old token 401s.
4. Run `install.ps1` → `start-dazy.ps1` once on Windows and report results.

## Honest summary

Local-first backend core: **built and tested (23/23)**. Cloud path: **live-verified
after an incident fix**. Windows scripts: **written, not executed here**. The bigger
AI-OS scope (workers, MCP, skills, 3D) remains a planned next milestone, not done.
