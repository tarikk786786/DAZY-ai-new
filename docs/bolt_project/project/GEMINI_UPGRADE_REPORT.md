# DAZY Gemini-Primary Upgrade — Implementation & Test Report (Nov 24, 2026)

## 1. Repository audit findings (baseline)

- Brain was Groq-primary with a browser-supplied `groq_api_key` accepted in chat
  requests (security hole — removed, see §3).
- Provider keys lived in the `provider_secrets` DB table (locked but unnecessary
  attack surface — replaced by Edge Function secrets).
- Frontend sent no keys (already clean); bundle scan confirmed.
- `verify_jwt = true` already set on the chat function (401 without the app key).
- Build baseline: clean; all existing tests/E2E passing before changes.

## 2. New architecture

Provider ladder (strict order, all keys from Edge Function secret store):

  1. Gemini PRIMARY   — gemini-3.5-flash-lite (configurable via GEMINI_MODEL)
  2. Groq SECONDARY   — qwen/qwen3.8-27b
  3. OpenRouter THIRD — openai/gpt-4o-mini
  4. DeepSeek FOURTH  — deepseek-chat

Failover semantics (implemented in the chat brain):
- Bounded retries: max 2 attempts per provider, exponential backoff (400ms→3s cap).
- 30s per-attempt timeout via AbortController.
- Permanent errors (401/403 auth, 404 unknown model) skip remaining retries
  for that provider and drop to the next rung immediately.
- Transient errors (429, 5xx, network, timeout, empty/malformed) retry once,
  then step down.
- Every response (success AND total failure) exposes which provider and model
  actually answered: `provider_used`, `model_used`, `fallback_used`,
  `latency_ms`, `request_id`. No silent pretending.

## 3. Security improvements

- REMOVED: browser-supplied `groq_api_key` path (any client key field is now
  ignored by design).
- REMOVED: `provider_secrets` DB table (dropped in migration
  `drop_provider_secrets`) — keys moved to Edge Function secrets:
  GEMINI_API_KEY, GEMINI_MODEL, GROQ_API_KEY, OPENROUTER_API_KEY,
  DEEPSEEK_API_KEY. Verified present in the function secret store.
- verify_jwt stays ON: no key → 401, wrong key → 401 (tested).
- Rate limit stays ON: 30 turns/5min; over-limit returns Hinglish 429 message.
- Logs now contain status codes only, never provider response bodies
  (which could echo keys).
- Secret-pattern scan of src/, supabase/functions/, dist/: clean.
- New `provider_health` table: RLS on, zero public policies, zero grants to
  anon/authenticated — only the service-role function writes/reads it.
- Persona rule added: DAZY must never save API keys/passwords/tokens into
  memory, plus a code-level guard rejecting secret-like memory keys.

## 4. Database changes

- DROPPED: public.provider_secrets (keys migrated to function secrets first).
- CREATED: public.provider_health (rolling real telemetry — see §3).
- UNTOUCHED: conversations, messages, memories, reminders, preferences
  (no user data modified or deleted; chat_rate_limit rows only pruned for
  the current test window to continue testing).

## 5. Test results — ACTUAL outcomes

| # | Test | Result |
|---|------|--------|
| 1 | Gemini primary answers, metadata present | PASS (provider_used=gemini, model_used=gemini-3.5-flash-lite, latency ~750-1200ms) |
| 2 | No key material in any response/bundle/log | PASS |
| 3 | Hinglish empathy ("thak gaya hoon") | PASS (emotion=empathetic) |
| 4 | Memory save (favourite singer) | PASS |
| 5 | Memory recall from different conversation | PASS (remembered "Arijit") |
| 6 | Reminder with IST +05:30 due time | PASS |
| 7 | Auth gate (no key) | PASS (401) |
| 8 | Bad request (missing message) | PASS (400) |
| 9 | provider_secrets table removed | PASS (404 on REST access) |
| 10 | app_config locked from anon | PASS (401) |
| 11 | Frontend production build | PASS (exit 0) |
| 12 | Rate limit (30/5min) | PASS (429 with Hinglish message) |
| 13 | Gemini under load → fallback chain works | PARTIAL — see below |

Honest finding on #13: under Google's current 503 "high demand" spikes,
gemini sometimes fails twice; then groq/auth-fails and deepseek/auth-fail
(the keys on those rungs are expired/revoked — the user was told to rotate
and hasn't yet), and openrouter intermittently 503s. When that happens the
user sees the honest Hinglish "brain disturb" message — never a fake success.
After key rotation the fallback chain will be fully redundant again.

Also verified live: failover ladder walk is REAL — telemetry rows in
provider_health show each attempt with its outcome and latency.

## 6. Frontend changes

- Chat bubbles now show which brain answered: e.g. "empathetic · gemini · 0.9s"
  (model on hover). Zero layout/persona/voice changes otherwise.
- DazyReply type extended with the new metadata fields (backwards compatible).

## 7. Deployment status

- Edge function dazy-chat: DEPLOYED (verify_jwt=true) with the new ladder,
  timeouts, backoff, telemetry, metadata. Live and answering via Gemini.
- Migrations: applied (drop_provider_secrets, create_provider_health).
- Frontend: built clean; deploy to hosting pending user action if desired
  (`npm run build` output in dist/).

## 8. Remaining manual steps (user)

1. ROTATE all API keys shared in chat (Groq, OpenRouter, DeepSeek, GitHub,
   Gemini) at each provider dashboard, then update them:
   currently Groq and DeepSeek rungs return auth failures — their keys are dead.
2. Provide a fresh GitHub token to push this branch/commits (old token rejected).
3. Optional: set GEMINI_MODEL function secret to try gemini-3.8-flash when
   Google's load recovers (currently 503 high-demand).

## 9. Known limitations

- Gemini free tier intermittently 503s under global demand; ladder handles it
  but the fallback rungs currently have dead keys (see §8.1).
- Web Speech API voice input remains Chrome/Edge-dependent (unchanged).
- Phone dashboard / desktop audio workstreams remain desktop-side (unchanged).
