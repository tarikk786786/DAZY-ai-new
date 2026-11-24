# DAZY C4 Architecture Models & Dynamic Execution Flows

This document details the architectural models for the **DAZY AI Assistant** using the C4 model standard and Mermaid visual specifications.

---

## 1. C4 Level 1: System Context Diagram

```mermaid
flowchart TB
    subgraph Users [Users]
        Owner["Owner / Primary User (Tarik)"]
        Companion["Companion / Guest (Priya)"]
    end

    subgraph DAZY_Boundary [DAZY System Boundary]
        DAZY["DAZY AI Assistant<br/>(Desktop HUD, Voice Engine & Web Dashboard)"]
    end

    subgraph External_Services [Cloud Voice & Intelligence Backends]
        Gemini["Google Gemini Live<br/>(Bidirectional Realtime Voice WSS)"]
        Groq["Groq Cloud API<br/>(WhisperSTT & Low-Latency LLM)"]
        EdgeTTS["Microsoft Edge Neural TTS<br/>(en-IN-NeerjaNeural Speech Synthesis)"]
    end

    Owner -->|"Voice speech, keyboard shortcuts, HUD interactions"| DAZY
    Companion -->|"Voice speech (scoped permissions)"| DAZY
    DAZY -->|"Stream 16kHz PCM audio & receive 24kHz speech"| Gemini
    DAZY -->|"Transcribe speech & prompt LLM completions"| Groq
    DAZY -->|"Synthesize normalized conversational text"| EdgeTTS
```

---

## 2. C4 Level 2: Container Diagram

```mermaid
flowchart TB
    subgraph Presentation_Layer [Presentation Layer]
        HUD["Desktop HUD GUI<br/>(PyQt6)<br/>Renders avatar, visemes, and audio bars"]
        WebDash["Remote Web Dashboard<br/>(HTML5 / WebSockets)<br/>Mobile control, metrics, phone audio relay"]
    end

    subgraph Core_Daemon [DAZY Core Execution Daemon (Python 3.14 AsyncIO)]
        Orchestrator["Core Orchestrator<br/>(main.py)<br/>Event loop, device routing, tool dispatch"]
        VoiceManager["Voice Session Manager<br/>(core/voice_session_manager.py)<br/>Atomic single-voice & playback transactions"]
        DualEngine["Dual-Engine Subsystem<br/>(Gemini Live & Pipeline Engine)"]
        WebServer["Starlette ASGI Server<br/>(dashboard/server.py :8080)<br/>REST APIs, token auth, WebSockets"]
    end

    subgraph Storage [Persistence Layer]
        Config["Memory Ledger<br/>(config_manager.py / api_keys.json)"]
        Profiles["Voice Profiles & Pronunciation Dict<br/>(enrolled_speakers.json / pronunciation_dict.json)"]
    end

    HUD <-->|"Events & Queue Bridges"| Orchestrator
    WebDash <-->|"REST & Secure WSS (AES-256-GCM)"| WebServer
    WebServer <-->|"Metrics & Commands"| VoiceManager
    Orchestrator --> VoiceManager
    Orchestrator --> DualEngine
    Orchestrator <--> Storage
```

---

## 3. C4 Level 3: Component Diagram (Core Orchestrator & Audio Path)

```mermaid
flowchart TD
    subgraph Input_Processing [Audio Ingestion & Diarization]
        Mic["Microphone Array (Intel Smart Sound)"] -->|16kHz PCM| PA["PortAudio InputStream (sounddevice)"]
        PA --> Callback["_listen_audio Callback (1024 samples)"]
        Callback --> EchoGuard{"EchoGuard & Half-Duplex Guard"}
        EchoGuard -->|Assistant Speech?| Suppress["Suppress / Interruption Barge-In"]
        EchoGuard -->|Human Voice| SpkId["SpeakerIdentifier (64-dim MFCC)"]
        SpkId -->|"Identify: Tarik vs Priya vs Unknown"| Attribution["Set Active Speaker Attribution"]
    end

    subgraph Dual_Engine [Dual-Engine Execution]
        Attribution --> ModeSwitch{"Active Engine Mode"}
        
        ModeSwitch -->|"Mode = Live"| LiveConn["Gemini Live WebSocket Client<br/>(models/gemini-3.1-flash-live-preview)"]
        LiveConn -->|Bi-directional WSS| LiveAudioOut["audio_in_queue (24kHz PCM)"]
        
        ModeSwitch -->|"Mode = Pipeline"| VAD["Adaptive Energy VAD<br/>(floor=0.0008, margin=2.2)"]
        VAD --> STT["WhisperSTT (whisper-large-v3-turbo)"]
        STT --> LLM["LLM Router (gemini-2.5-flash / Qwen)"]
        LLM --> Tools["Action Dispatcher (desktop, browser, system)"]
        LLM --> Pronounce["PronunciationEngine (normalize_text_for_speech)"]
        Pronounce --> TTS["EdgeTTSProvider (en-IN-NeerjaNeural)"]
        TTS --> PipelineAudioOut["audio_in_queue (24kHz PCM)"]
    end

    subgraph Atomic_Output [Atomic Audio Output]
        LiveAudioOut --> AtomicPlayer["AtomicTTSPlayer Singleton"]
        PipelineAudioOut --> AtomicPlayer
        AtomicPlayer --> SoundOut["Sounddevice OutputStream (Speakers/Headphones)"]
    end
```

---

## 4. Dynamic Flow: End-to-End Turn Execution

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Tarik)
    participant Mic as Hardware Mic (DirectSound 13)
    participant Core as main.py Callback
    participant VSM as VoiceSessionManager
    participant Spk as SpeakerIdentifier
    participant Engine as Engine (Live / Pipeline)
    participant TTS as AtomicTTSPlayer
    participant Speaker as Output Speakers (Realtek)

    User->>Mic: "Namaste DAZY!"
    Mic->>Core: 1024-sample PCM frames (16kHz)
    Core->>VSM: record_input_callback(1024)
    Core->>VSM: should_suppress_mic_input(indata)?
    VSM-->>Core: False (not echoing assistant speech)
    Core->>Spk: identify_speaker(indata)
    Spk-->>Core: ("Tarik", 0.88 confidence, verified=True)
    Core->>Engine: Queue PCM audio block
    Engine->>Engine: Process turn & resolve actions
    Engine->>VSM: start_playback_transaction(turn_id, provider)
    VSM->>TTS: Lock atomic playback mutex
    Engine->>TTS: Stream 24kHz PCM audio slices (2400 bytes)
    TTS->>Speaker: Play audio to user
    TTS->>Spk: register_assistant_playback(pcm) [Anti-Echo Fingerprint]
    TTS->>VSM: finish_playback_transaction()
    VSM-->>Core: Mark speaking ended + arm tail margin
```
