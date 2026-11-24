# DAZY Master AI Operating System — Consolidated Execution Roadmap

**Generated:** 2026-11-25  
**Target Repository:** `Mark-LVII` (`https://github.com/tarikk786786/DAZY-ai-new.git`)  
**Owner:** Tarik (@tarikk786786)  
**Architecture Baseline:** Sovereign DAZY Master OS (LangGraph + Starlette + Durable DAG + SQLite)

---

## 1. Consolidated Root-Cause Audit & Requirement Synthesis

All prior user directives, uploaded artifacts (`DAZY_UI_Visual_Reference_Links.md`, screen recording `20261124-1906-06.7506150.mp4`), codebase state, and runtime logs were consolidated into this unified engineering plan:

### Resolved Conflicts & Design Decisions
1. **Single Sovereign Orchestrator:** DAZY remains the exclusive controller. GodMode-Team DAG scheduling, NEURON.ONE development checklists/skills, and smol-ai Multi-AI Arena operate strictly as modular subsystems within DAZY's core (`core/ai_os/`), never competing as separate daemon loops.
2. **Hinglish Voice Consistency:** `en-IN-NeerjaNeural` (Microsoft Edge TTS) + Groq Whisper `whisper-large-v3-turbo` with Roman Hinglish prompt biasing + strict LLM system language guard. Never allow Turkish, Arabic, or generic English defaults unless explicitly asked.
3. **Browser vs. Desktop Audio Separation:** Desktop engine runs STT/LLM/TTS cleanly with hardware echo guards. Browser dashboard does NOT emit duplicate speech or loop `SpeechRecognition` toast spam.
4. **Layout Root Fix:** Frame-by-frame analysis of the user's video revealed an unclosed/mismatched `</div>` inside `#page-overview` (`app.html:526`) that fractured `.workspace` grid nesting, shoving `<aside class="right-rail">` below `<main>` and causing massive vertical black voids. Additionally, `recognition.onstart` fired duplicate `"Continuous Listening active"` toasts on every silence timeout restart, piling 16+ toasts over the screen.

---

## 2. Systematic Dependency-Ordered Execution Roadmap

### Phase 1: Existing Project Audit, Architecture & Formal Specs
- [x] **1.1** Codebase & Architecture Audit across `core/`, `providers/`, `dashboard/`, `memory/`, `tests/`.
- [x] **1.2** Formal Engineering Documentation Suite: C4 DSL, DBML, OpenAPI 3.1.0, ADRs, 26-Stage Workflow Catalog, PRD, Tool/MCP Registry, Security Audit, Deployment Guide.
- [x] **1.3** Live Video Frame Inspection (`media_1795547207591_cc47bb3e.mp4`) & `DAZY_UI_Visual_Reference_Links.md` Design Alignment.

### Phase 2: Complete Hinglish Voice, Listening, Speaking & Personality Repair
- [x] **2.1** Calibrate Desktop Pipeline VAD thresholds (`_VAD_ABSOLUTE_MIN = 0.0055`, `_VAD_FLOOR_MARGIN = 2.8`, `_VAD_MIN_SPEECH_MS = 350`) to eliminate background fan/noise false triggers.
- [x] **2.2** Fix FSM Transition (`FOLLOW_UP_LISTENING -> SPEAKING / THINKING`) and wire half-duplex acoustic self-echo suppression (`vsm.is_assistant_speaking_or_echo()`).
- [x] **2.3** Upgrade `providers/stt_whisper.py`: Add acoustic energy RMS gate before API calls, Roman Hinglish prompt conditioning for `whisper-large-v3-turbo` to stop Turkish/Arabic hallucinations, and reject silence artifacts (`< 0.35s`).
- [ ] **2.4** Harden Adult Indian Female Hinglish Personality across `main.py`, `core/dazy_persona.py`, and `providers/llm_openai.py`: Warm, affectionate, witty companion voice in Roman Hinglish with strict anti-Turkish / anti-random-language guard.
- [ ] **2.5** Voice Preview & Settings Backend API (`POST /api/voice-preview`, `POST /api/voice-settings`, `GET /api/suggestions`, `GET /api/os/memory`) backed by live `EdgeTTSProvider` and SQLite memory.
- [ ] **2.6** Real-Speech Hinglish Round-Trip Verification (STT + LLM + TTS audio bytes test with mixed Hinglish phrases).

### Phase 3: UI/UX Redesign, Bug Repair & Multi-Screen Command Center (`dashboard/static/app.html`)
- [ ] **3.1** Fix structural HTML nesting bug (remove stray closing `</div>` & duplicate `#orbCaption` in `page-overview`) restoring the exact 3-Column `.workspace` Grid.
- [ ] **3.2** Build Toast Notification Engine Overhaul: Deduplication, max 3-toast queue, 3.5s auto-expiry, zero `onstart` loop spam, replaced with single persistent listening status badge.
- [ ] **3.3** Fix Browser Speech Recognition Lifecycle: Set `en-IN` Hinglish default recognition, block input while assistant speaks (preventing browser self-echo loop), and enforce explicit clean Voice State Machine (`IDLE`, `LISTENING`, `TRANSCRIBING`, `THINKING`, `SPEAKING`, `MUTED`, `ERROR`).
- [ ] **3.4** Implement DAZY Design System Tokens & 3-Column Main Command Center:
  - **Left Column:** Brand, Reactor Status / Voice Core mini-monitor, compact controls, clean categorized navigation across all screens.
  - **Center Column:** Conversational Onboarding ("Hey! Main DAZY hoon...") with Hinglish suggestions & "What can I say?" drawer, proper responsive message bubbles (`max-width: min(82%, 720px)`), live streaming, persistent transcript banner, intelligent composer.
  - **Right Column:** Contextual Memory & Reminders (live `/api/os/memory`), Active Tasks & Workers, System Health vitals, Quick Controls.
- [ ] **3.5** Dedicated Advanced DAZY Screens wired to real backend APIs:
  - Home Command Center (`overview`)
  - Conversation & Voice Assistant (`chat`)
  - Live Brain 3D (`brain`)
  - Workers & Agents (`workers`)
  - Tasks & Workflow Manager (`command`)
  - Memory Center & Knowledge Graph (`memory`)
  - Tools & MCP Registry (`tools`)
  - PC Control & System Health (`system`)
  - Logs, Traces & Self-Repair (`logs`)
  - Testing Center (`testing`)
  - Multi-AI Arena (`arena`)
  - Files & Knowledge (`files`)
  - Activity (`activity`)
  - Voice, Personality & Mic Settings (`diagnostics` & `settings` with live voice preview button!)

### Phase 4: AI Brain, Orchestrator, Tools, Security & Testing Verification
- [ ] **4.1** Verify LangGraph real execution & SQLite Checkpoints + Kahn's DAG orchestration.
- [ ] **4.2** Verify Gemini / Groq / DeepSeek / OpenRouter / NVIDIA / AI/ML API connectivity & fallback ladder.
- [ ] **4.3** Execute Full Playwright Visual & Functional E2E Suite covering every route, button, voice control, notification limit, and responsive breakpoint (1440px, 1024px, 390px) with 0 console errors.
- [ ] **4.4** Capture high-resolution Before-vs-After screenshots and verify visual perfection.
- [ ] **4.5** Execute Full Pytest Suite (137+ tests) confirming 100% pass rate (Exit Code 0).
- [ ] **4.6** Final Commit & Push to `https://github.com/tarikk786786/DAZY-ai-new.git` (`dazy-transformation` & `main`).
