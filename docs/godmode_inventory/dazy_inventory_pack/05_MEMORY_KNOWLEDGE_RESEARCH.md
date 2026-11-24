# 05 — Memory, knowledge, retrieval and research

## Desktop memory components

Relevant source paths:

- `memory/memory_manager.py` — primary memory operations, prompt formatting, update/search and session summary helpers.
- `memory/dazy_memory.py` — DAZY memory façade/logic.
- `memory/dazy_preferences.py` + `memory/dazy_preferences.json` — preference storage.
- `memory/config_manager.py` — settings persistence.
- `memory/supabase_sync.py` — Supabase synchronization path.
- `memory/routines.json` — routine state/data.
- `memory/pronunciation_dict.json` — pronunciation dictionary.
- `memory/voice_profiles/` — enrolled speaker voice profile data.
- `core/vector_memory.py` — vector memory subsystem.
- `core/ai_os/memory.py` — AI OS memory abstraction.
- `knowledge/` — curated Markdown knowledge.

Architecture docs describe a 3-layer memory model: transient working context, short-term event memory with TTL, and long-term memory with SQLite FTS5 full-text search; cloud synchronization uses Supabase. Verify actual deployed schema and local data files before relying on this description.

## Web memory and chat persistence

`DAZY-web/src/useDazy.ts` uses Supabase tables named `conversations`, `messages`, `memories` and `reminders`. The web client loads a recent conversation, messages, memories and pending reminders, writes new user/assistant messages, refreshes memories, deletes an individual memory and clears the current conversation. The Edge Function builds context from recent messages and memories, and may save one memory or create a reminder from parsed model JSON.

## Knowledge collections

- Indian culture: `knowledge/indian/culture.md`
- Indian Muslim heritage: `knowledge/islamic/indian_muslim_heritage.md`
- Islamic references: `knowledge/islamic/islamic_references.md`
- Hinglish vocabulary: `knowledge/languages/hinglish_lexicon.md`
- Urdu terminology: `knowledge/languages/urdu_terminology.md`
- Personal context: `knowledge/personal/user_context.md`
- Quran integration: `integrations/knowledge/quran.py`
- Wikipedia integration: `integrations/research/wikipedia.py`

## Research/search implementation

- `actions/web_search.py` — web/news search action.
- `actions/flight_finder.py` — flight-finding action.
- `actions/youtube_video.py` — YouTube action.
- `actions/file_processor.py` — file/document processing.
- `core/tasks/research.py`, `core/tasks/web.py` — research and web task logic.
- `integrations/api_discovery.py` — API discovery integration.
- `integrations/research/wikipedia.py` — Wikipedia integration.
- `plugins/public_apis.py` — weather, Wikipedia and Quran lookups.

## Candidate memory/knowledge libraries — not integrated by this audit

- Mem0: https://github.com/mem0ai/mem0
- Cognee: https://github.com/topoteretes/cognee
- Graphiti: https://github.com/getzep/graphiti
- Letta: https://github.com/letta-ai/letta
- LangMem: https://github.com/langchain-ai/langmem
- LlamaIndex: https://github.com/run-llama/llama_index
- Haystack: https://github.com/deepset-ai/haystack
- txtai: https://github.com/neuml/txtai
- pgvector: https://github.com/pgvector/pgvector
- Qdrant: https://github.com/qdrant/qdrant
- Chroma: https://github.com/chroma-core/chroma
- Milvus: https://github.com/milvus-io/milvus
- Weaviate: https://github.com/weaviate/weaviate
- FAISS: https://github.com/facebookresearch/faiss
- LanceDB: https://github.com/lancedb/lancedb

Do not add another database without measuring the current Supabase/Postgres + SQLite implementation first. A memory layer needs data ownership, user controls, provenance, deduplication, retention and deletion semantics—not only embeddings.
