"""Initial curated taxonomy + entries. Everything unverified stays 'unknown' until
the GitHub engine verifies it live. Nothing here is fabricated: repo URLs are the
well-known upstream projects; licence/cost/maintenance come only from verification."""
from . import db, github_verify

CATEGORIES = [
    ("01-ai-brains", "AI Brains & Models", "LLMs, model gateways, routing, fallback, embeddings"),
    ("02-emotions", "Emotions & Personality", "Emotion classification, sentiment, empathy, tone, prosody"),
    ("03-language", "Language & NLP", "Hindi, Hinglish, NER, intent, transliteration, translation"),
    ("04-voice", "Voice & Audio", "ASR, TTS, VAD, wake word, diarization, barge-in"),
    ("05-vision", "Vision & Media", "OCR, image/video understanding and processing"),
    ("06-memory", "Memory & Knowledge", "Vector, graph, episodic and procedural memory, RAG"),
    ("07-agents", "Agents & Workers", "Planning, delegation, orchestration, verification"),
    ("08-skills-mcp", "Skills & MCP", "Skill packs, MCP servers, tool registries"),
    ("09-research", "Research & APIs", "Search, crawling, extraction, public datasets"),
    ("10-automation", "Automation & Integrations", "Schedules, queues, workflows, connectors"),
    ("11-coding", "Coding & Computer Use", "Git, browser automation, desktop control, execution"),
    ("12-security", "Security & Permissions", "Auth, secrets, sandboxing, audit, scanning"),
    ("13-testing", "Testing & Diagnostics", "Evaluation, tracing, health checks, repair"),
    ("14-infra", "Infrastructure", "Databases, storage, queues, networking"),
    ("15-ui", "UI & Experience", "Dashboards, animation, charts, accessibility"),
]

# (name, category, capability, repo_url, entry_type, description, languages)
SEEDS = [
    # 01 — brains & gateways
    ("LiteLLM", "01-ai-brains", "Unified model gateway with fallback", "https://github.com/BerriAI/litellm", "library", "Proxy + SDK unifying 100+ LLM providers with routing and fallbacks", "en"),
    ("LangGraph", "01-ai-brains", "Stateful agent workflows", "https://github.com/langchain-ai/langgraph", "framework", "Graph-based stateful orchestration for agents", "en"),
    ("Pydantic AI", "01-ai-brains", "Typed agents with structured output", "https://github.com/pydantic/pydantic-ai", "framework", "Type-safe agent framework from the Pydantic team", "en"),
    ("smolagents", "01-ai-brains", "Lightweight tool-using agents", "https://github.com/huggingface/smolagents", "library", "Minimal HF agents with code-in-thought loops", "en"),
    # 02 — emotions & affect
    ("pysentimiento", "02-emotions", "Sentiment and emotion classification", "https://github.com/pysentimiento/pysentimiento", "library", "Transformer-based sentiment/emotion/hate-speech classifiers", "en,es,pt,it"),
    ("VADER", "02-emotions", "Rule-based sentiment", "https://github.com/cjhutto/vaderSentiment", "library", "Lexicon-and-rule sentiment for social text", "en"),
    ("NRCLex", "02-emotions", "Lexicon emotion analysis", "https://github.com/metalcorebear/NRCLex", "library", "NRC emotion-lexicon based text emotion scoring", "en"),
    ("GoEmotions", "02-emotions", "Fine-grained emotion dataset", "https://github.com/google-research/google-research/tree/master/goemotions", "dataset", "58k Reddit comments with 27 emotion labels", "en"),
    ("librosa", "02-emotions", "Audio and prosody feature extraction", "https://github.com/librosa/librosa", "library", "Audio signal analysis: pitch, rhythm, intensity", ""),
    ("openSMILE", "02-emotions", "Vocal acoustic features", "https://github.com/audeering/opensmile", "library", "Standard openSMILE feature extraction for speech emotion", ""),
    # 03 — language (Hinglish focus)
    ("Indic NLP Library", "03-language", "Indian-language NLP", "https://github.com/anoopkunchukuttan/indic_nlp_library", "library", "Tokenization, transliteration, normalization for Indic languages", "hi,en,+"),
    ("IndicTrans2", "03-language", "Indic translation", "https://github.com/AI4Bharat/IndicTrans2", "model", "AI4Bharat MT models covering 22 Indian languages", "hi,en,+"),
    ("spaCy", "03-language", "Industrial NLP pipeline", "https://github.com/explosion/spaCy", "library", "Tokenizer, POS, NER, dependencies; multilingual models", "en,hi,+"),
    ("Stanza", "03-language", "Multilingual NLP", "https://github.com/stanfordnlp/stanza", "library", "Stanford neural pipeline across 60+ languages", "en,hi,+"),
    ("sentence-transformers", "03-language", "Semantic similarity and embeddings", "https://github.com/UKPLab/sentence-transformers", "library", "Embedding models for semantic search and clustering", "en,hi,+"),
    ("Presidio", "03-language", "PII detection and redaction", "https://github.com/microsoft/presidio", "library", "Detect and mask personal data in text/images", "en,+"),
    # 04 — voice & audio
    ("faster-whisper", "04-voice", "Fast speech recognition", "https://github.com/SYSTRAN/faster-whisper", "library", "CTranslate2 Whisper re-implementation, streaming-capable", "hi,en,+"),
    ("WhisperX", "04-voice", "Aligned transcription", "https://github.com/m-bain/whisperX", "library", "Whisper + forced alignment + diarization hooks", "hi,en,+"),
    ("Silero VAD", "04-voice", "Voice activity detection", "https://github.com/snakers4/silero-vad", "model", "Tiny production VAD model, streaming", ""),
    ("openWakeWord", "04-voice", "Wake-word detection", "https://github.com/dscripka/openWakeWord", "library", "Open wake-word models with custom phrase training", "en"),
    ("pyannote-audio", "04-voice", "Speaker diarization", "https://github.com/pyannote/pyannote-audio", "library", "Diarization, segmentation, speaker embeddings", ""),
    ("Kokoro", "04-voice", "Open-weight TTS", "https://github.com/hexgrad/kokoro", "model", "Small high-quality TTS model family", "en"),
    ("Piper", "04-voice", "Local lightweight TTS", "https://github.com/rhasspy/piper", "library", "Fast on-device neural TTS for Raspberry Pi-class hardware", "en,hi,+"),
    ("sherpa-onnx", "04-voice", "On-device streaming speech", "https://github.com/k2-fsa/sherpa-onnx", "library", "Streaming ASR/TTS/VAD runtime, C++/Python/JS bindings", "hi,en,+"),
    ("RNNoise", "04-voice", "Noise suppression", "https://github.com/xiph/rnnoise", "library", "Real-time recurrent noise reduction (Xiph)", ""),
    ("Coqui TTS", "04-voice", "TTS toolkit", "https://github.com/coqui-ai/TTS", "library", "Multi-model TTS toolkit; check per-model licences", "en,hi,+"),
    # 06 — memory & knowledge
    ("Mem0", "06-memory", "Agent memory layer", "https://github.com/mem0ai/mem0", "library", "Extract/retrieve user memories with an API surface", "en"),
    ("Graphiti", "06-memory", "Temporal knowledge graphs", "https://github.com/getzep/graphiti", "library", "Time-aware KG built for agent memory", "en"),
    ("txtai", "06-memory", "Embeddings + semantic search", "https://github.com/neuml/txtai", "library", "All-in-one embeddings DB, RAG and workflows", "en"),
    ("LlamaIndex", "06-memory", "Document ingestion + RAG", "https://github.com/run-llama/llama_index", "framework", "Connectors, chunking, indexes, query engines", "en,+"),
    ("pgvector", "06-memory", "Vector search in Postgres", "https://github.com/pgvector/pgvector", "library", "Vector similarity inside PostgreSQL", ""),
    ("Chroma", "06-memory", "Embedding database", "https://github.com/chroma-core/chroma", "library", "Open-source embedding + vector store", "en"),
    # 07 — agents & orchestration
    ("CrewAI", "07-agents", "Collaborative agent teams", "https://github.com/crewAIInc/crewAI", "framework", "Role-based multi-agent collaboration", "en"),
    ("Agno", "07-agents", "Multi-agent systems", "https://github.com/agno-agi/agno", "framework", "Fast multi-agent framework with tool support", "en"),
    ("LangMem", "07-agents", "Long-term memory management", "https://github.com/langchain-ai/langmem", "library", "Memory extraction/consolidation for LangGraph agents", "en"),
    # 08 — skills & MCP
    ("MCP Python SDK", "08-skills-mcp", "MCP server/client SDK", "https://github.com/modelcontextprotocol/python-sdk", "library", "Official Model Context Protocol Python SDK", "en"),
    ("MCP TypeScript SDK", "08-skills-mcp", "MCP server/client SDK", "https://github.com/modelcontextprotocol/typescript-sdk", "library", "Official MCP TypeScript SDK", "en"),
    ("GitHub MCP Server", "08-skills-mcp", "GitHub automation", "https://github.com/github/github-mcp-server", "tool", "Official GitHub MCP server: repos, issues, PRs", "en"),
    ("Playwright MCP", "08-skills-mcp", "Browser automation via MCP", "https://github.com/microsoft/playwright-mcp", "tool", "Microsoft's Playwright-powered MCP browser", "en"),
    ("anthropics/skills", "08-skills-mcp", "Agent skill examples", "https://github.com/anthropics/skills", "skill", "Reference SKILL.md packages for agent skills", "en"),
    # 09 — research & public APIs
    ("Crawl4AI", "09-research", "AI-friendly web crawling", "https://github.com/unclecode/crawl4ai", "library", "Crawler producing LLM-ready output", "en,+"),
    ("trafilatura", "09-research", "Article extraction", "https://github.com/adbar/trafilatura", "library", "Readable-content extraction + metadata", "en,+"),
    ("MarkItDown", "09-research", "Documents to Markdown", "https://github.com/microsoft/markitdown", "tool", "Convert PDF/Office/HTML to Markdown for LLMs", "en"),
    ("SearXNG", "09-research", "Self-hosted metasearch", "https://github.com/searxng/searxng", "tool", "Privacy metasearch aggregator, self-hostable", "en,+"),
    ("Open-Meteo", "09-research", "Weather forecast API", "https://github.com/open-meteo/open-meteo", "api", "Free, no-key weather API for non-commercial use", "en"),
    ("OpenAlex", "09-research", "Scholarly metadata API", "https://github.com/ourresearch/openalex", "api", "Fully open index of papers, authors, institutions", "en"),
    ("Wikimedia APIs", "09-research", "Encyclopedia knowledge", "https://www.mediawiki.org/wiki/API:Main_page", "api", "MediaWiki Action API family for wiki content", "en,hi,+"),
    # 10 — automation
    ("n8n", "10-automation", "Workflow automation", "https://github.com/n8n-io/n8n", "tool", "Node-based workflow automation, self-hostable", "en"),
    ("Activepieces", "10-automation", "Open-source automation", "https://github.com/activepieces/activepieces", "tool", "No-code workflow builder, MCP-friendly", "en"),
    ("Celery", "10-automation", "Distributed task queue", "https://github.com/celery/celery", "library", "Python distributed task execution", "en"),
    ("Temporal", "10-automation", "Durable workflows", "https://github.com/temporalio/temporal", "tool", "Fault-tolerant durable execution engine", "en"),
    # 11 — coding & computer use
    ("Playwright", "11-coding", "Browser automation", "https://github.com/microsoft/playwright", "library", "Cross-browser automation and testing", "en"),
    ("github-mcp-server (see MCP)", "11-coding", "Repository operations", "https://github.com/github/github-mcp-server", "tool", "Official GitHub MCP integration", "en"),
    ("Semgrep", "11-coding", "Static analysis", "https://github.com/semgrep/semgrep", "tool", "Fast multi-language SAST with custom rules", "en"),
    # 12 — security
    ("Gitleaks", "12-security", "Secret detection in git", "https://github.com/gitleaks/gitleaks", "tool", "Scan repos/history for leaked credentials", "en"),
    ("Trivy", "12-security", "Vulnerability scanning", "https://github.com/aquasecurity/trivy", "tool", "Containers, filesystems, repos, licences", "en"),
    ("Bandit", "12-security", "Python SAST", "https://github.com/PyCQA/bandit", "tool", "Security-oriented static analysis for Python", "en"),
    ("OWASP Cheat Sheet Series", "12-security", "Security guidance", "https://github.com/OWASP/CheatSheetSeries", "tool", "Authoritative OWASP implementation guidance", "en"),
    # 13 — testing & observability
    ("Langfuse", "13-testing", "LLM tracing and evaluation", "https://github.com/langfuse/langfuse", "tool", "Open LLM engineering: traces, evals, prompts", "en"),
    ("Promptfoo", "13-testing", "Prompt/model testing", "https://github.com/promptfoo/promptfoo", "tool", "Test LLM prompts/models with assertions", "en"),
    ("DeepEval", "13-testing", "LLM evaluation", "https://github.com/confident-ai/deepeval", "library", "Pytest-style LLM evaluation framework", "en"),
    ("OpenTelemetry", "13-testing", "Standard telemetry", "https://github.com/open-telemetry/opentelemetry-python", "library", "Vendor-neutral traces/metrics/logs (Python)", "en"),
    ("pytest", "13-testing", "Python testing", "https://github.com/pytest-dev/pytest", "tool", "The standard Python test framework", "en"),
    # 14 — infra
    ("SQLite", "14-infra", "Embedded database", "https://github.com/sqlite/sqlite", "tool", "The embedded SQL database (public domain)", ""),
    ("DuckDB", "14-infra", "Analytical SQL", "https://github.com/duckdb/duckdb", "library", "In-process analytical OLAP database", "en"),
    ("Qdrant", "14-infra", "Vector database", "https://github.com/qdrant/qdrant", "tool", "Rust vector similarity search engine", "en"),
    ("FAISS", "14-infra", "Similarity search", "https://github.com/facebookresearch/faiss", "library", "Dense vector similarity search library", "en"),
    ("LanceDB", "14-infra", "Embedded vector DB", "https://github.com/lancedb/lancedb", "library", "Embedded vector DB on columnar storage", "en"),
    # 15 — UI
    ("React", "15-ui", "Component UI framework", "https://github.com/facebook/react", "library", "UI component framework powering DAZY-web", "en"),
    ("Chart.js", "15-ui", "Charts", "https://github.com/chartjs/Chart.js", "library", "Simple canvas charts with tree-shaking", "en"),
    ("Recharts", "15-ui", "React charts", "https://github.com/recharts/recharts", "library", "Composable React charting components", "en"),
]


def seed() -> dict[str, int]:
    for cid, name, desc in CATEGORIES:
        db.execute(
            "INSERT INTO categories (id, name, description) VALUES (?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET name=excluded.name, description=excluded.description",
            (cid, name, desc),
        )
    added = 0
    for name, cat, cap, url, etype, desc, langs in SEEDS:
        before = db.one("SELECT id FROM entries WHERE id=?", (name.lower().replace(" ", "-"),))
        github_verify.add_entry(name, cap, cat, url, entry_type=etype, description=desc, languages=langs)
        if not before:
            added += 1
    return {"categories": len(CATEGORIES), "entries_added": added, "entries_total": len(SEEDS)}
