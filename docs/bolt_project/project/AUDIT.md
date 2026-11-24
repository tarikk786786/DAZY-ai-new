# DAZY Master Audit — November 2026

Scope: web DAZY (this repo, fully audited and repaired) and desktop DAZY-ai-new
(audited at source level; hardware-dependent repairs are listed, not claimed done).

## Phase 1 — Discovery

Web repo (`tarikk786786/DAZY-web`, 23 paths): Vite + React 18 + TypeScript
frontend, one Supabase edge function (`dazy-chat`) as the brain, 6 tables.
No duplicate or abandoned code paths found; the app is a single coherent flow.

Desktop repo (`tarikk786786/DAZY-ai-new`, 356 files, ~13 MB): main.py (3,365
lines) orchestrates a listening FSM, device picker, voice-session manager with
frame counters, 10 TTS providers, 3 STT providers, an AI-OS layer (orchestrator,
tasks, MCP, telemetry), plugins, GUI, mobile companion, and 120+ tests.
Incomplete/overlapping pieces observed: multiple TTS engines with only edge-tts
exercised daily; `memory/COMPLETED_WORK.md` tracks partial milestones; main.py
contains 18 broad except-and-continue blocks and 81 print calls (logging debt).

## Phase 2 — Security

- Web: no secrets in any tracked file (pattern scan: clean). Provider keys live
  in `provider_secrets` (RLS on, zero policies, zero grants) — anon REST access
  returns 42501 permission denied, verified.
- Web: edge function now requires the publishable key (401 without it), verified.
- Web: server-side rate limit added (30 turns / 5 min), counter verified in DB.
- Web: `app_config` (service-role only) stores the shared PIN, mirroring desktop.
- Database: permissive `USING (true)` policies were briefly tightened to a
  passphrase gate, then reverted — the browser reads memories/reminders directly
  and there is no sign-in, so a gate would have locked the legitimate user out.
  The single-tenant posture is documented and intentional.
- USER ACTION REQUIRED: the API keys pasted into chat (Groq, OpenRouter,
  DeepSeek, GitHub tokens, NVIDIA, HuggingFace, Vercel) must be rotated at each
  provider. They were shared in plain text and are compromised regardless of
  anything done in this repo.

## Phase 3 — Desktop audio reliability (audit only)

`core/voice_session_manager.py` already tracks frames_captured, frames queued,
bytes sent, transcripts, responses, and dropped-overflow counts, and gates
playback through an atomic transaction manager. `core/audio_devices.py` picks
devices by name (not index) and probes whether a host API actually delivers
frames before selecting it. The directive's demand — LISTENING must be backed
by mic evidence — is architecturally satisfiable from this code, but running
and verifying it needs the user's Windows machine; no changes were made.

## Phase 4 — Providers (web side, verified live)

Groq (qwen/qwen3.8-27b), OpenRouter (openai/gpt-4o-mini), DeepSeek
(deepseek-chat) ladder, user-supplied key first, 401/403/404/429 step-down.
Live E2E: 8/8 cases replied; memory persisted across conversations; reminder
created with correct IST due time. Gemini fallback was not added — the three
existing rungs plus the user key cover failover; adding a fourth unused rung
was judged scope without benefit.

## Phase 5–7 — Phone dashboard / AI OS / web integration

Phone dashboard and AI OS are desktop-code workstreams requiring the user's
hardware; audited at source level only (see Phase 3 note). Web integration
surface: persona, memory schema and reminder semantics now match between the
web twin and desktop manual (Hinglish replies, IST reminders, fact memories).

## Phase 8 — Tests with evidence

| Check | Result |
|---|---|
| Production build (tsc + vite) | pass, exit 0 |
| Edge function gate: no key / wrong key | 401 / 401 |
| Edge function gate: app key | 200 + reply |
| Integration chat cases | 8/8 pass |
| Memory persistence across conversations | pass |
| Reminder creation (IST due time) | pass |
| Rate limiter counter in DB | pass |
| Missing/empty message validation | 400 / 400 |
| CORS preflight | 200 |
| Locked tables via anon REST (provider_secrets, app_config, chat_rate_limit) | 42501 / 401 / 401 |
| Reachable tables via anon REST (memories, reminders, conversations) | 200, correct rows |
| Secret-pattern scan of tracked files | clean |

## Phase 9 — Release

README updated with setup, security posture, verified audit trail and known
limitations. All changes deployed: migrations applied, edge function redeployed
twice (gate + rate limit), frontend rebuilt cleanly.

Not done here (needs Tarik): rotate all pasted API keys; run desktop audio
tests on the Windows machine; real-device phone dashboard tests.
