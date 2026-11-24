# DAZY Project State

**Project**: DAZY — Multimodal, Voice-First AI Companion (Mark-LVII)
**Target Hardware / OS**: Windows 11 64-bit (Intel SST Microphone Array & Realtek Speakers)
**Active Git Branch**: `dazy-transformation` (ahead of origin by 1 commit: `2e38d29`)
**Environment**: Python 3.14.4 64-bit (`C:\Users\tarik\AppData\Local\Python\pythoncore-3.14-64\python.exe`)
**Dashboard Server**: FastAPI + Uvicorn on `http://localhost:8080` (PID 44732 / 19732 / Daemon background)
**Master Security PIN**: `786786` (configured in `server.py`)

---

## Architecture Blueprint

```
                      ┌──────────────────────────────────────────────┐
                      │               Microphone Input               │
                      │  (Web Audio 16kHz Worklet / USB Audio Card)  │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │          Voice Activity Detection            │
                      │     (Silero Neural VAD v5 + Energy RMS)      │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │        Indian Speech Recognition (STT)       │
                      │   (BharatGen Shrutam2 / Faster-Whisper ASR)  │
                      │     Hindi · English · Hinglish Code-Mixed    │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │             Multimodal AI Brain              │
                      │   (Groq Low-Latency Engine / OSS-20B / Qwen) │
                      │     Understands context, emotion & Hinglish  │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │         Neural Indian Speech (TTS)           │
                      │    (Svara TTS v1 / Swara & Neerja Neural)    │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │       Barge-in & Interactive Playback        │
                      │   (Instant click-to-interrupt & speech VAD)  │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │      State-Driven Glowing Orb & Waves        │
                      │  IDLE ➔ LISTENING ➔ DETECTING ➔ TRANSCRIBING │
                      │          ➔ THINKING ➔ SPEAKING ➔ BARGE-IN    │
                      └──────────────────────────────────────────────┘
```

---

## Active Component Status
1. **Frontend Dashboard (`dashboard/static/app.html`)**:
   - Central Glowing Orb with 8 animated states (`idle`, `listening`, `speech_detected`, `transcribing`, `thinking`, `speaking`, `interrupted`, `error`).
   - Waveform Canvas visualizers (`#orbWaveform` and `#micWaveCanvas`).
   - Live transcription banner (`#liveTranscriptBanner`).
   - Self-test telemetry card (`#selfTestCard`) and button (`#runSelfTestBtn`).
   - Touch/click-to-interrupt barge-in controls.
2. **Backend Engine (`main.py` & `dashboard/server.py`)**:
   - WebSocket `/ws` real-time state broadcast and `/ws/phone-audio` 16kHz PCM streaming.
   - Bounded FIFO backpressure queue with drop-oldest frame policy (`_safe_put_out_queue`).
   - Non-fatal microphone error recovery with exponential backoff (1s - 16s).
   - `/api/voice-self-test` diagnostic endpoint.
3. **AI Provider Configuration (`config/api_keys.json`)**:
   - STT: Faster-Whisper / Shrutam2 (`whisper-large-v3-turbo` on Groq).
   - LLM: `openai/gpt-oss-20b` via Groq API (`gsk_KjLz...`, status 200, low latency).
   - TTS: EdgeTTS / Svara (`en-IN-NeerjaNeural`, `hi-IN-SwaraNeural`).
   - VAD: Silero Neural VAD v5 + Adaptive Web Audio RMS VAD.
