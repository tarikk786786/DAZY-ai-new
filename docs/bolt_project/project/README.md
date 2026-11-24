# DAZY — Web Personal AI Companion

A Hinglish-speaking AI girlfriend-companion with a JARVIS-style HUD, persistent memory,
voice conversation, and reminders. The web twin of [DAZY-ai](https://github.com/tarikk786786/DAZY-ai-new) (desktop).

## Features

- Natural Hinglish conversation with emotion-aware replies (10 emotional states)
- Always-listening voice input + Indian English / Hindi female voice output (Neerja)
- Permanent memory — she remembers your preferences, people, plans; delete anything
- Voice-set reminders with spoken pop-up alerts and chime
- Reactor-core HUD with live status, waveform, glass panels
- Provider-ladder brain: Groq (Qwen 3.8 27B) → OpenRouter → DeepSeek → Gemini
  (gemini-3.8-flash), with prompt compression so free tiers never rate-limit
  mid-conversation
- Everything persisted in Supabase (memories, chats, reminders)

## Setup

1. Create a free Supabase project and run the migrations in `supabase/migrations/`.
2. Deploy the edge function in `supabase/functions/dazy-chat/`
   (`supabase/config.toml` already registers it).
3. Add provider keys into the `provider_secrets` table (server-side only, never
   exposed to browsers): rows `groq`, `openrouter`, `deepseek`, `gemini` with your keys.
4. `npm install && npm run dev`
   The frontend reads `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` from `.env`.

## Stack

Vite + React + TypeScript, Supabase (Postgres + Edge Functions),
Groq / OpenRouter / DeepSeek / Gemini, Web Speech API for voice.

## Security notes

- Provider API keys live in the `provider_secrets` table, which has RLS enabled
  with no public policies and no grants — only the edge function (service role)
  can read them. Verified: a browser holding the publishable key gets
  "permission denied" on that table.
- The browser never sees any provider key.
- The edge function requires the Supabase publishable key on every call
  (JWT verification on). Requests without it are rejected with 401.
- Server-side rate limiting: 30 chat turns per rolling 5-minute window
  (`chat_rate_limit` table, service-role only). Over the limit DAZY answers
  "Bas ek minute, sabar karo…" instead of burning provider quota.
- `app_config` (service-role only) holds the shared access PIN, mirroring the
  desktop DAZY's 786786 PIN pattern.

## Verified audit trail (Nov 2026)

- Build: clean production build, zero TypeScript errors.
- Function gate: no key → 401, wrong key → 401, app key → 200 + Hinglish reply.
- Integration: 8/8 chat cases returned valid JSON (response, emotion, language, speak).
- Memory: fact saved in one conversation ("favourite_colour: black") and recalled
  from a different conversation.
- Reminders: "5 minute baad paani" → reminder row created with correct IST due time.
- Rate limiter: turn counter increments per window (verified in DB).
- Negative paths: missing/empty message → 400; CORS preflight → 200.

## Known limitations

- Web Speech API voice input works best in Chrome/Edge; other browsers vary.
- The desktop DAZY (Windows) is a separate repo with its own audio stack.
- Free-tier provider keys can still rate-limit under sustained use — the ladder
  fails over automatically, and the server-side limiter caps abuse.

## License

Personal, non-commercial use. Persona derived from DAZY-ai (CC BY-NC 4.0).
