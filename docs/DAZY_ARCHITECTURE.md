# DAZY — Architecture & System Blueprint
### Designed & Customised by Tarik
*Based on the Mark-LVII foundation by FatihMakes (Licensed under CC BY-NC 4.0)*

---

## 1. Executive Summary

**DAZY** is an original Indian female-voice, emotionally intelligent, multilingual desktop AI assistant and companion. Built upon the robust engineering foundation of Mark-LVII, DAZY combines:
- Real-time bidirectional voice streaming (Gemini Live & modular Indian speech pipelines).
- Expressive Indian voice synthesis (Svara TTS v1 with emotion tags, DhVaani 0.5 Indic fallback, and Piper).
- Indian multilingual speech recognition (BharatGen Shrutam2, SraVaani 1.0, and Whisper).
- Emotion understanding across 10 core emotional states with conversational momentum and decay.
- Cultural and religious knowledge collections (Islamic authentic sources & Indo-Islamic heritage).
- Model Context Protocol (MCP) tool integration and dynamic agent skills.
- Full local desktop control, task checkpointing, and background research agents.

---

## 2. Architectural Blueprint

```mermaid
flowchart TD
    subgraph UI_Thread["Qt Main Thread (GUI)"]
        UI["ui.py / JarvisUI"]
        HUD["gui/hud.py — DAZY Reactor & Visemes"]
        Window["gui/window.py — DAZY Navigation & Drawers"]
        ProvidersPanel["gui/providers_panel.py — Engine Selector"]
    end

    subgraph Voice_Thread["Asyncio Loop (Voice Engine)"]
        Session["main.py — DAZY Session Controller"]
        Mic["sounddevice InputStream"]
        Speaker["sounddevice OutputStream"]
        
        GeminiLive["Gemini Live Multimodal API (Low Latency)"]
        
        subgraph Modular_Pipeline["DAZY Modular Pipeline"]
            ASR["STT: Shrutam2 / SraVaani / Whisper"]
            Brain["LLM: Sarvam AI / Qwen / Gemini"]
            Emotion["core/dazy/emotion_controller.py"]
            Planner["core/dazy/response_planner.py"]
            TTS["TTS: Svara TTS v1 / DhVaani / Piper"]
        end
    end

    subgraph Extensions["Capabilities & Tools"]
        Actions["actions/*.py — Desktop Control"]
        Plugins["plugins/*.py — Modular Tools"]
        Skills["agents/skills/* — Agent Skills"]
        MCP["core/mcp/* — External MCP Servers"]
        Tasks["core/tasks/* — Background Agents"]
    end

    subgraph Knowledge["Memory & Knowledge Base"]
        Memory["memory/memory_manager.py"]
        Prefs["memory/dazy_preferences.py"]
        KB_Indian["knowledge/indian/"]
        KB_Islamic["knowledge/islamic/"]
        KB_Languages["knowledge/languages/"]
    end

    Mic --> ASR
    ASR --> Emotion
    Emotion --> Brain
    Brain --> Planner
    Planner --> TTS
    TTS --> Speaker
    Speaker --> HUD
    
    Session --> GeminiLive
    Session --> Modular_Pipeline
    Brain <--> Actions & Plugins & Skills & MCP
    Brain <--> Knowledge
```

---

## 3. Core Architectural Invariants

1. **Strict UI-Thread Invariant**:
   - `actions/`, `plugins/`, `core/tasks/`, and `core/mcp/` execute on background worker threads.
   - Workers never instantiate or mutate Qt widgets directly. All UI notifications travel through thread-safe `pyqtSignal` methods on `player` (`JarvisUI`).

2. **Dual-Path Voice Engine**:
   - **Gemini Live Path**: Sub-second multimodal streaming for ultra-low latency.
   - **DAZY Modular Pipeline**: Deep Indian code-switching (Shrutam2) → Emotional Planning → Svara/DhVaani synthesis with native emotion tags.

3. **Background Agent Boundaries**:
   - Research sub-agents are strictly isolated with read-only tools and cannot trigger destructive desktop modifications.

4. **Lazy Import Discipline**:
   - Heavy machine learning libraries (Torch, OpenVINO, Faster-Whisper, MCP SDK) are loaded lazily on first invocation, guaranteeing instant startup.

5. **Verified Tool Execution**:
   - Destructive actions (shutdown, restart, wifi toggle, file removal) pass through `core/confirm.py` and `core/undo.py`.
