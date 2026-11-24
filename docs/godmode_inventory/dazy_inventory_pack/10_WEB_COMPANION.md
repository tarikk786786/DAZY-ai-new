# 10 — DAZY-web complete source inventory

Repository: https://github.com/tarikk786786/DAZY-web  
Observed ref: `main` at `0f8803261c69377379587745c21942c68935d26a`.

## Source files

- `src/App.tsx` — application shell, chat UI, emotion badge display, voice toggle, status panels.
- `src/hud.tsx` — reactor, waveform, system status, memory panel, reminders panel, toasts, India clock and chat auto-scroll.
- `src/useDazy.ts` — conversation boot, message writes, memory/reminder fetch, reminder polling, spoken alerts, Edge Function requests, interruption.
- `src/useVoiceInput.ts` — browser speech recognition, Hindi locale, continuous/interim recognition, restart timer, permission error handling.
- `src/lib/speech.ts` — voice selection (Neerja/Indian English/Hindi/default), browser speech synthesis, stop speaking and generated send/alert chimes.
- `src/lib/supabase.ts` — Supabase client using Vite environment variables.
- `src/lib/types.ts` — Memory, Conversation, ChatMessage, Reminder, DazyEmotion, DazyState and DazyReply types.
- `src/main.tsx` — React entry.
- `src/index.css` — interface styling.
- `supabase/config.toml` — Edge Function config; `verify_jwt = false` in inspected file.
- `supabase/functions/dazy-chat/index.ts` — provider ladder, persona prompt, context lookup, response parsing and memory/reminder writes.
- `index.html`, `vite.config.ts`, `tsconfig.json`, `package.json`, `package-lock.json`.

## Direct npm packages

Production: `@supabase/supabase-js`, `react`, `react-dom`.  
Development: `@types/react`, `@types/react-dom`, `@vitejs/plugin-react`, `typescript`, `vite`.

No separately installed voice, emotion, MCP, agent, vector database or automation packages appear in the direct web dependency list.

## Browser-native interfaces

- Web Speech Recognition / `webkitSpeechRecognition`.
- `speechSynthesis`, `SpeechSynthesisUtterance`.
- Web Audio `AudioContext`, oscillator and gain nodes.
- Fetch, DOM, timer APIs and locale/timezone formatting.

These capabilities depend on browser support, microphone permission, device selection and network conditions. Web Speech recognition is not equivalent to a fully controlled local ASR engine.

## Database operations in client/source

Tables referenced include `conversations`, `messages`, `memories`, `reminders`. Exact schema, migrations and RLS policies were not included in the returned tracked tree, so their definitions must be checked in the Supabase dashboard/migration source.

## Security observations

- `src/useDazy.ts` sends the Supabase anon key as a Bearer token to `dazy-chat`.
- Edge Function has `verify_jwt = false` in `supabase/config.toml`; inspect actual user authentication model and enforce per-user access before treating this as production-safe.
- CORS is wildcard `*` in the Edge Function.
- Request body accepts `groq_api_key`; it should not accept provider secrets from the browser.
- Edge Function uses service-role client to read `provider_secrets`, while also creating an anon client with forwarded Authorization for user data. Validate that RLS and user identity checks prevent cross-user reads/writes.
- No provider health dashboard, MCP system, skills registry or desktop-control bridge was found in this web tree.

## Not yet implemented in web repo

Gemini primary provider, provider health dashboard, model metadata, explicit failover telemetry, full desktop agent/worker system, complete local ASR/TTS pipeline, external MCP servers, and unified desktop/web user identity/memory contracts.
