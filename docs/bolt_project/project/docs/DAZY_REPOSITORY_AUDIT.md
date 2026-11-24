# DAZY Repository Audit — 2026-11-24

Scope: `DAZY-web` web app (this repo, React/TS + Supabase edge functions) and the
`dazy-analysis/` desktop source drop (Python, MARK XL lineage). Written from code
actually read and live-tested in this session; each claim is verified or marked otherwise.

## 1. Current architecture

### DAZY-web (this repo)
| Layer | Implementation | Status |
|---|---| independence |
| Frontend | React 18 + TS, custom hooks (`useDazy`, `useVoiceInput`), glass HUD (`hud.tsx`, `index.css`) | Working, build green |
| Brain | `supabase/functions/dazy-chat` — provider ladder Gemini→Groq→OpenRouter→DeepSeek, bounded retries, honest metadata (`provider_used`, `model_used`, `latency_ms`, `request_id`) | Working, live-verified |
| Status | `supabase/functions/dazy-status` — real deep probes, 24h stats from `provider_health` | Working, live-verified |
| Database | Supabase Postgres: `conversations`, `messages`, `memories`, `reminders`, `chat_rate_limit`, `provider_health`, `app_config` | Working, RLS on |
| Voice | Web Speech API (hi-IN, Neerja-first), echo pause, Web Audio chimes | Working (browser-dependent) |

### dazy-analysis (desktop, source drop)
- Python monolith (`main.py`, `ui.py`) with Ollama/OpenAI-compatible local LLM client
  (`core/llm_client.py`), TTS provider zoo (`providers/tts_*.py`, 10+ engines incl.
  EdgeTTS), STT (Whisper/Compact/STT-Sravaani), wake word, diarization, emotional TTS,
  desktop automation actions (`actions/*.py`), skills/agents markdown prompts
  (`agents/skills/*.md`), Playwright dashboard, import-linter enforced architecture,
  ADRs. Includes `docs/dazy_complete_kit/` engineering kit (PRD, test matrix, install
  scripts) and a pre-existing `install.ps1`/PowerShell kit in the complete-kit docs.
- **Not integrated** with the web app: separate persona files, separate memory, no
  shared backend. The `dazy-analysis` tree is a source drop, not a package the web app
  imports.

## 2. Working features (verified this session)
- Chat with honest provider metadata, live-verified Gemini primary
  (`gemini-3.5-flash-lite`, ~700–1200 ms).
- Provider failover ladder with bounded retries (2/provider, backoff, 30 s timeout),
  outcome taxonomy (auth/not_found/rate_limited/server/network/empty/malformed).
- Real provider health telemetry (`provider_health` table, service-role only, 24h stats).
- Real status endpoint (cheap/deep modes), 401 without credentials.
- Memory save/edit/forget, reminders (set/complete/snooze/rename/delete) — DB-confirmed.
- Conversation history, new conversation, clear-with-confirmation.
- Rate limiting (30 turns / 300 s) — hit and verified during testing.
- Secret-leak guards (memory saves, logs, bundle scan clean).

## 3. Broken / degraded
| Item | Detail | Unblocks when |
|---|---|---|
| Groq fallback | 401 auth — key dead | User rotates key in edge secret store |
| OpenRouter fallback | 402 payment — account out of credit | User adds credit |
| DeepSeek fallback | 401 auth — key dead | User rotates key |
| GitHub push | Old token 401s | User provides fresh token with repo scope |

## 4. Incomplete / missing (web app)
- No local (offline) mode: everything requires Supabase + internet.
- No multi-agent orchestration, task engine, skills/MCP registry, desktop control —
  the web app is a companion + memory + reminders product, not an agent OS.
- No 3D brain; reactor/waveform are 2D CSS.
- Voice is STT/TTS only; no wake word, no always-on desktop listening.

## 5. Duplicate implementations
- Persona: web edge function `PERSONA` vs `dazy-analysis/core/dazy_persona.py` +
  `config/dazy_persona.md` + `agents/dazy_companion.md` — three persona sources.
- Memory: Supabase `memories` table vs `dazy-analysis/memory/*` JSON/SQLite.
- Provider logic: edge ladder vs `core/llm_client.py` (Ollama/OpenAI-compat) vs
  `providers/llm_*.py`. Same problem solved three ways.

## 6. Security posture (verified)
- Edge-only keys (browser never holds provider keys); browser key path removed.
- `provider_health` and `app_config` service-role only, zero public grants.
- RLS on all tables, single-tenant `anon` policies, secret-leak regex guards.
- Outstanding: all keys shared in chat must be rotated (they were pasted in plaintext);
  `.env` is git-ignored; history for the future GitHub push must be sanitized.

## 7. Dependencies & external services
- Web: React 18, Vite 5, `@supabase/supabase-js` 2, lucide icon svg inline, Outfit +
  JetBrains Mono fonts, Tailwind not used.
- Cloud: Supabase (Postgres + Edge Functions), Gemini/Groq/OpenRouter/DeepSeek APIs.
- Desktop drop: Ollama or OpenAI-compatible local server, EdgeTTS, Whisper, ~40 actions.

## 8. Recommended path (matches the v1 milestone)
1. **Local-first backend** (new `backend/`, Python 3.11+, FastAPI + SQLite) exposing
   the same contracts the web app already uses (chat with provider metadata, memory,
   reminders, status). Supabase becomes an optional sync adapter, not a dependency.
2. **Model gateway**: port the proven edge-function ladder (Gemini→Groq→OpenRouter→
   DeepSeek + optional local Ollama/OpenAI-compat) with health log in SQLite.
3. **Reuse the desktop drop**: `llm_client.py` patterns (KV warmup, OpenAI-compat),
  EdgeTTS/Whisper provider files, action registry — via explicit interfaces, not copy-paste.
4. **Task engine + workers** on SQLite (durable queue, retries, dead-letter) — phase 2.
5. **Frontend**: keep the existing command-center UI; add a backend selector
   (cloud/local) rather than a rewrite.

## 9. What must NOT be touched
- The working edge-function chat path and its honest-metadata contract.
- The HUD components just rebuilt (Reactor/ProviderPanel/MemoryPanel/RemindersPanel/
  HistoryDrawer/ConfirmDialog) — verified build + live E2E this session.
- Existing migrations (append-only policy).
