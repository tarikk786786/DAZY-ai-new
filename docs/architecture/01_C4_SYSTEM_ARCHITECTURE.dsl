workspace "DAZY AI OS" "Sovereign Personal AI Companion & Agentic Operating System" {

    model {
        user = person "Tarik" "Primary Owner and Exclusive User"

        dazySystem = softwareSystem "DAZY AI OS" "Local-first sovereign AI companion and agentic workstation." {
            
            # Containers
            desktopEngine = container "Desktop Core Engine" "Manages voice pipeline, STT/TTS hardware, and half-duplex conversation loop." "Python 3.14 (AsyncIO, SoundDevice, PyTorch)"
            
            aiOsSubsystem = container "AI OS Control Plane" "Durable task scheduler, worker registry, repair engine, and 3D graph projection." "Python (Pydantic v2, SQLite)"
            
            langGraphEngine = container "LangGraph Workflow Engine" "Stateful multi-step task execution with SQLite checkpointing." "LangGraph, Python"
            
            dashboardServer = container "Dashboard Gateway & HTTP/WS Server" "FastAPI HTTP API and WebSocket broadcaster for real-time telemetry." "FastAPI, Uvicorn, WebSockets"
            
            webHud = container "Holographic Web HUD" "Interactive 3-column dashboard: Reactor Core, Live 3D Brain, Command Center, and Multi-AI Arena." "HTML5, CSS Glassmorphism, Web Audio API, Canvas"
            
            localDatabase = container "Local SQLite Ledger" "Stores memories, routines, DAG tasks, incidents, and execution checkpoints." "SQLite 3"
        }

        # External Systems
        groqApi = softwareSystem "Groq Cloud" "Ultra-low latency LLM inference (Qwen 27B, GPT-OSS 120B)."
        geminiApi = softwareSystem "Google Gemini" "Multimodal LLM & Gemini Live voice API."
        openRouterApi = softwareSystem "OpenRouter" "Aggregated multi-provider LLM endpoint."
        deepSeekApi = softwareSystem "DeepSeek API" "High-reasoning code and analysis models."
        aimlApi = softwareSystem "AI/ML API" "Universal AI gateway covering 200+ open-source models."
        supabaseCloud = softwareSystem "Supabase Cloud" "Optional cloud database & edge function sync."

        # Relationships
        user -> webHud "Interacts via voice, text, and 3D visual controls"
        webHud -> dashboardServer "HTTP REST calls & WebSocket real-time events" "JSON / WSS"
        dashboardServer -> aiOsSubsystem "Dispatches durable tasks & queries system state"
        dashboardServer -> langGraphEngine "Invokes stateful workflows"
        desktopEngine -> dashboardServer "Broadcasts audio transcriptions & assistant speech"
        desktopEngine -> localDatabase "Reads / writes memories and speaker profiles"
        aiOsSubsystem -> localDatabase "Persists tasks, workers, incidents, and telemetry"
        langGraphEngine -> localDatabase "Stores step checkpoints"
        desktopEngine -> groqApi "Fast conversational streaming" "HTTPS"
        desktopEngine -> geminiApi "Fallback & Multimodal queries" "HTTPS"
        dashboardServer -> groqApi "Multi-AI Arena benchmarking" "HTTPS"
        dashboardServer -> geminiApi "Multi-AI Arena benchmarking" "HTTPS"
        dashboardServer -> openRouterApi "Multi-AI Arena benchmarking" "HTTPS"
        dashboardServer -> deepSeekApi "Multi-AI Arena benchmarking" "HTTPS"
        dashboardServer -> aimlApi "Multi-AI Arena benchmarking" "HTTPS"
        dashboardServer -> supabaseCloud "Optional companion synchronization" "HTTPS"
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

        styles {
            element "Person" {
                shape Person
                background #00f0ff
                color #0a0e14
            }
            element "Software System" {
                background #0e1526
                color #ffffff
                stroke #00f0ff
            }
            element "Container" {
                background #111a33
                color #ffffff
                stroke #7928ca
            }
        }
    }
}
