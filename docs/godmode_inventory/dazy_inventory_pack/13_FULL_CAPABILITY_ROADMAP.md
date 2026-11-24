# 13 — Full capability map: large systems and small components

This taxonomy is intended to prevent small but important capabilities from being overlooked. It is a checklist, not a claim that each item is currently implemented.

## Brain and reasoning

Intent classification; task decomposition; plan generation; dependency graphs; replanning; tool selection; provider selection; structured output; schema validation; reasoning verification; self-critique; source grounding; confidence calibration; ambiguity detection; clarification; refusal/safety routing; response length; language routing; context budgeting; token counting; summarization; caching; retry; cooldown; circuit breaker; fallback; task state; idempotency.

## Emotion and social understanding

Sentiment; basic emotions; fine-grained emotions; valence; arousal; intensity; confidence; sarcasm; irony; humour; frustration; confusion; curiosity; politeness; formality; empathy strategy; warmth; conversational pacing; topic continuity; social cues; user correction; uncertainty phrasing; emotional trend; voice prosody; pause ratio; vocal intensity; multimodal fusion. Never infer mental health diagnosis or claim certainty about internal state.

## Language and conversation

Language ID; code-switching; Hinglish; Urdu/Hindi/Indic scripts; transliteration; translation; tokenization; normalization; spelling; grammar; stemming; lemmatization; POS tagging; NER; entity resolution; intent; slot filling; topic classification; paraphrase; summarization; question detection; sarcasm; contradiction; coreference; context resolution; follow-up; interruption; turn-taking; backchannel; speaker diarization; dialogue state; response planning.

## Hearing and speaking

Microphone capture; device selection; sample-rate conversion; PCM; clipping detection; normalization; denoising; echo cancellation; VAD; silence detection; wake word; push-to-talk; streaming ASR; batch ASR; partial transcript; final transcript; punctuation restoration; language detection; speaker diarization; speaker identification with consent; sound-event classification; pitch; F0; energy/RMS; speaking-rate; prosody; TTS; streaming TTS; phonemization; pronunciation dictionary; voice profiles; voice selection; interruption; audio buffering; playback queue; output-device recovery; voice diagnostics.

## Vision and media

Screen capture; camera permissions; OCR; object detection; classification; segmentation; tracking; pose/landmark detection; face detection; expression research; scene recognition; image captioning; image embeddings; video frame extraction; scene-boundary detection; subtitles; audio-video sync; media conversion; playback; thumbnail generation; file metadata.

## Memory and knowledge

Working memory; conversation memory; episodic memory; semantic memory; procedural memory; project memory; event memory; preference memory; entity memory; temporal validity; provenance; deduplication; contradiction checks; consolidation; forgetting; retention; deletion; export; vector embeddings; reranking; hybrid search; full-text search; graph traversal; ontology; taxonomy; document ingestion; chunking; citation mapping; knowledge updates.

## Agents and task operations

Supervisor; planner; worker pool; specialist agents; delegation; parallel jobs; task queue; checkpoints; resume; cancellation; deadlines; heartbeats; retries; resource budgets; human approval; result verifier; artifact storage; progress events; notifications; worker crash recovery; audit trail.

## Tools, MCP and skills

Action registry; plugin registry; skill registry; MCP discovery; MCP authentication; stdio/HTTP transports; schema validation; tool metadata; versioning; capability scoring; permissions; read/write scopes; confirmation gate; timeout; output truncation; sandbox; audit log; health status; uninstall/disable; alternatives.

## Research and APIs

Search providers; metasearch; web browsing; extraction; crawling; site policy respect; official-source prioritization; fact-checking; claim extraction; source comparison; citation generation; RSS/news; academic search; APIs; OpenAPI parsing; API key storage; quotas; rate-limit awareness; cache; data freshness; license/provenance; response validation.

## Computer and operating system

App launch/close; window focus; window enumeration; keyboard; mouse; clipboard; screen region; accessibility tree; browser navigation; form filling; download; file picker; filesystem read/write; safe rename; recycle-bin delete; undo; process monitor; service monitor; CPU/RAM/GPU/battery; audio settings; display settings; notifications; shortcuts; OS detection; device pairing; permission prompts.

## Productivity and integrations

Reminders; recurring reminders; calendar; email inbox; email draft; send approval; notes; tasks; routines; alarms; weather; maps; travel lookup; YouTube transcript; messaging; Telegram; Gmail; Home IoT; MQTT; spreadsheets; presentations; PDFs; DOCX; local files; QR pairing; mobile handoff.

## Infrastructure, quality and safety

Authentication; authorization; RLS; secrets; encryption; TLS; CORS; input validation; output validation; rate limiting; abuse controls; dependency scanning; static analysis; secret scanning; supply-chain policy; backups; migrations; observability; logs; metrics; traces; profiling; tests; integration tests; end-to-end tests; load tests; accessibility tests; benchmarks; rollback; health checks; self-repair proposals; approval before repair.

## User experience

Reactor/HUD states; listening indicator; muted state; transcript; waveform; emotion badge; memory panel; reminder panel; provider panel; task dashboard; device panel; logs; diagnostics; notifications; reduced motion; keyboard navigation; screen-reader labels; responsive desktop/tablet/mobile; themes; localization; error recovery UI.

## Capability record schema recommended

Each item should have: stable ID; human name; short description; parent category; input/output type; implementation type (library/API/model/MCP/skill/dataset/action); repository and official docs; licence; cost class; hosting mode; API key requirement; platform; runtime; language; RAM/CPU/GPU estimate; dependencies; model/checkpoint; maintenance date; archived status; security risks; permission scope; test method; alternatives; installation command; verified date; evidence; confidence; activation rule; disable/uninstall path.
