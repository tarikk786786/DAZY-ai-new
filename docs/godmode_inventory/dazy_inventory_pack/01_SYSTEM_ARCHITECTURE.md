# 01 — System architecture and technology stack

## Desktop architecture

The desktop assistant is a Python/Qt application with a Gemini Live conversation path and an optional modular provider path. Main entry point: [`main.py`](https://github.com/tarikk786786/DAZY-ai-new/blob/main/main.py); UI: [`ui.py`](https://github.com/tarikk786786/DAZY-ai-new/blob/main/ui.py); GUI modules: [`gui/`](https://github.com/tarikk786786/DAZY-ai-new/tree/main/gui).

| Layer | Technology/code | Role | Evidence/status |
|---|---|---|---|
| Desktop UI | PyQt6, `ui.py`, `gui/*` | Window, panels, widgets, HUD | Declared in requirements; source present |
| Core runtime | Python, asyncio, threads, queues | Conversation session, real-time loop and background operations | Source present |
| Primary live AI path | `google-genai`, Gemini Live | Streaming voice conversation and tool interaction | Source and dependency present; quota/credentials are machine-specific |
| One-shot AI | `core/gemini.py` | Centralized short AI calls, model ladder, timeout/caching logic | Source present |
| Optional model engines | `providers/*` | Alternative LLM/STT/TTS engines | Source present; lazy-loaded/configurable |
| Audio input/output | sounddevice, NumPy | Microphone and speaker streams | Declared and used in source |
| Speech pipeline | `core/stt.py`, `core/streaming_asr.py`, `core/tts.py`, `providers/*` | ASR, TTS, language stabilization | Source present; optional engines have extra dependencies |
| Computer/browser | Playwright, PyAutoGUI, OS APIs | Browser, keyboard, mouse, screen and window controls | Declared; runtime permissions and browser install required |
| Memory | Local JSON/SQLite-oriented code and `memory/*` | Preferences, summaries, search, routines, voice data | Source present; data files are partly ignored/runtime-local |
| Cloud sync | Supabase integration | Remote memory synchronization/device context | Code/docs present; credentials and schema need validation |
| API backend | FastAPI, Uvicorn, Docker | Remote dashboard/backend service | Source/dependencies present |
| Dashboard | HTML/CSS/JS + server/WebSocket | Phone-accessible command center and telemetry | Source present |
| MCP | Custom `core/mcp/*` | Connect external MCP servers and mount tools | Framework present; server list/active connection unverified |
| Skill/capability registry | `core/capabilities/*`, `agents/skills/*` | Discover actions, plugins, skills and MCP tools | Source present |
| Monitoring | `core/ambient/*`, `actions/system_monitor.py` | Resource governor, task/screen observer, alerts | Source present |
| Testing | pytest-style `tests/*` | Voice, architecture, integrations, emotion, UI and regression checks | Test files present; historic pass claims not independently re-run |

## Web architecture

The web twin is a separate React/TypeScript app backed by Supabase Postgres and one Supabase Edge Function. It currently implements a simpler chat/memory/reminder/voice experience rather than the full desktop tool ecosystem.

| Layer | Technology | Role |
|---|---|---|
| Frontend | React 18 + TypeScript | Chat interface and state |
| Build/dev server | Vite 5 | Build and local dev |
| Backend/data SDK | `@supabase/supabase-js` | Postgres reads/writes and Edge Function calls |
| Backend | Supabase Edge Function, Deno | `dazy-chat` provider call and side effects |
| Browser voice input | Web Speech API | Continuous recognition toggle, interim/final transcript |
| Browser voice output | SpeechSynthesis API | Local browser voice playback |
| Sound effects | Web Audio API | Send/reminder chimes |
| Styling/UI | CSS | Reactor core, waveform, glass panels, chat and status |

Web entry points: [`src/App.tsx`](https://github.com/tarikk786786/DAZY-web/blob/main/src/App.tsx), [`src/useDazy.ts`](https://github.com/tarikk786786/DAZY-web/blob/main/src/useDazy.ts), [`src/useVoiceInput.ts`](https://github.com/tarikk786786/DAZY-web/blob/main/src/useVoiceInput.ts), [`supabase/functions/dazy-chat/index.ts`](https://github.com/tarikk786786/DAZY-web/blob/main/supabase/functions/dazy-chat/index.ts).

## Shared product capabilities vs shared implementation

The two repositories share DAZY persona goals (Hinglish, emotional tone, voice, memory and reminders), but they do not share one runtime brain, one capability registry or one common tool bus today. Treat them as two application surfaces until an explicit shared backend/API contract is implemented.
