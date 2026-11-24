workspace "DAZY AI Assistant" "C4 Architecture Model for DAZY Real-Time Conversational AI Workstation" {

    model {
        user = person "User / Owner" "Interacts with DAZY via voice, desktop HUD, or mobile web dashboard." "Primary User"
        guest = person "Companion / Guest" "Secondary enrolled user with scoped permissions." "Secondary User"

        dazySystem = softwareSystem "DAZY AI Assistant" "Real-time AI companion supporting dual-engine streaming, diarization, computer control, and secure dashboard." {
            
            desktopApp = container "Desktop Interface (PyQt6)" "Renders holographic HUD avatar, lip-sync visemes, and audio level meters." "Python / PyQt6"
            webDashboard = container "Remote Web Dashboard" "Single-page dashboard for mobile audio relay, memory browser, and system metrics." "HTML5 / JavaScript / WebSockets"
            
            orchestrator = container "DAZY Core Daemon" "Coordinates audio capture, VAD, diarization, engine dispatch, and action execution." "Python 3.14 AsyncIO" {
                audioCapture = component "PortAudio Mic Ingestion" "Captures 16kHz 16-bit mono PCM from Intel Smart Sound Mic Array." "sounddevice / PortAudio"
                vadModule = component "Adaptive VAD & EchoGuard" "Tracks noise floor, filters self-speech echo, and flags speech transitions." "Energy VAD / Silero"
                speakerId = component "Speaker Identifier" "Extracts 64-dim MFCC embeddings and matches enrolled speaker profiles." "MFCC / Sherpa-ONNX"
                sessionMgr = component "Voice Session Manager" "Thread-safe singleton managing playback transactions and single-voice guarantees." "AtomicTTSPlayer"
                engineRouter = component "Engine Router" "Dispatches conversation turns between Gemini Live and Local Pipeline." "Async Event Router"
                geminiLive = component "Gemini Live Client" "Bidirectional WebSocket connection for sub-600ms streaming speech-to-speech." "Google GenAI SDK"
                pipelineEngine = component "Pipeline Engine" "Fallback pipeline chaining Whisper STT, LLM (OpenAI-compat), and EdgeTTS." "Whisper / Groq / EdgeTTS"
                pronounceEngine = component "Pronunciation Engine" "Normalizes Devanagari, Hinglish, acronyms, and phonetic speech." "Phonetic Dictionary"
                actionDispatcher = component "Action Dispatcher" "Dispatches tool execution across desktop, web search, media, and OS settings." "Action Loader"
                webServer = component "Starlette ASGI Server" "Serves REST APIs and secure WebSockets on port 8080." "Starlette / Uvicorn"
            }

            memoryStore = container "Local Memory Ledger" "Persists user preferences, API keys, conversation history, and voice profiles." "JSON / SQLite"
        }

        # External Systems
        googleGemini = softwareSystem "Google Gemini Live" "Cloud real-time multimodal voice streaming backend." "External SaaS"
        groqApi = softwareSystem "Groq Cloud API" "Low-latency Whisper STT and LLM inference." "External SaaS"
        edgeTts = softwareSystem "Microsoft Edge Neural TTS" "Cloud neural speech synthesis delivering Neerja Indian English/Hindi voice." "External SaaS"

        # Relationships - Context
        user -> dazySystem "Speaks to and issues commands" "Voice / Desktop GUI / Web"
        guest -> dazySystem "Speaks to with constrained permissions" "Voice"
        dazySystem -> googleGemini "Streams audio & transcripts via WebSockets" "WSS / TLS"
        dazySystem -> groqApi "Sends audio for transcription & prompt completions" "HTTPS / REST"
        dazySystem -> edgeTts "Requests neural speech synthesis" "WSS / Protobuf"

        # Relationships - Containers
        user -> desktopApp "Views avatar and triggers Push-To-Talk"
        user -> webDashboard "Controls assistant from phone or browser" "HTTPS / WSS"
        desktopApp -> orchestrator "Sends UI events and queries audio levels" "PyQt Signals / Queues"
        webDashboard -> webServer "Sends commands, phone audio, and queries diagnostics" "HTTPS / WSS (AES-256-GCM)"
        orchestrator -> memoryStore "Reads/writes configuration and voice profiles" "File I/O"
        orchestrator -> googleGemini "Bi-directional streaming" "WebSocket"
        orchestrator -> groqApi "Transcribe audio & chat completions" "REST"
        orchestrator -> edgeTts "Synthesizes speech" "WSS"

        # Relationships - Components
        audioCapture -> vadModule "Pushes 1024-sample PCM frames"
        vadModule -> speakerId "Passes non-echo user speech frames"
        speakerId -> sessionMgr "Sets active speaker attribution"
        sessionMgr -> engineRouter "Signals turn initiation"
        engineRouter -> geminiLive "Routes to Live socket if online"
        engineRouter -> pipelineEngine "Routes to Pipeline fallback"
        pipelineEngine -> pronounceEngine "Normalizes response text"
        pipelineEngine -> actionDispatcher "Executes model tool calls"
        actionDispatcher -> desktopApp "Reflects tool output in HUD log"
        webServer -> sessionMgr "Provides live diagnostic metrics"
    }

    views {
        systemContext dazySystem "SystemContext" {
            include *
            autoLayout lr
        }

        container dazySystem "Containers" {
            include *
            autoLayout lr
        }

        component orchestrator "Components" {
            include *
            autoLayout tb
        }

        styles {
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Component" {
                background #85bbf0
                color #000000
            }
            element "External SaaS" {
                background #999999
                color #ffffff
            }
        }
    }
}
