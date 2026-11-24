# 02 — AI brains, LLM providers and routing

## Desktop: observed model architecture

- `main.py` imports `google.genai` and has a Gemini Live conversation session path.
- `core/gemini.py` centralizes one-shot Gemini operations, model selection, timeout/fallback/cooldown logic and uses a centralized FAST / SMART / SEARCH intent class. Its comments explain why grounded search stays on REST rather than Live.
- `providers/base.py` defines a provider contract that adapts alternatives to the Live-shaped interface used by the main app.
- `providers/registry.py` uses an explicit lazy module registry; it does not indiscriminately import every provider at startup.
- `providers/llm_openai.py` is the OpenAI-compatible provider module.
- `providers/llm_dazy.py` is a DAZY LLM adapter.

### Model/provider names found in source, config or docs

| Name | Evidence | Classification |
|---|---|---|
| Google Gemini / Gemini Live | `main.py`, `core/gemini.py`, `google-genai` requirement | Main live conversational path, subject to key/quota |
| OpenRouter | `config/dazy_config.json`, docs, provider architecture | Configured default text provider in checked-in JSON; runtime config can override |
| OpenAI-compatible endpoints | `providers/llm_openai.py`, provider docs | Adapter supports compatible services; inspect catalog/config for exact enabled endpoint |
| Groq | `.agent/PROJECT_STATE.md`, provider docs / OpenAI-compatible routing | Project log reports a successful Groq response in a previous session; not live-verified here |
| DeepSeek | provider docs | Documented compatible provider |
| Sarvam AI | `docs/PROVIDERS.md` | Documented Indic LLM endpoint/model options |
| Qwen 2.5 | `docs/PROVIDERS.md` | Documented local Ollama/vLLM option |
| Mistral, xAI, Together, OpenRouter | desktop README/provider docs | Described compatible API choices; per-key availability unverified |
| Ollama, LM Studio, llama.cpp, vLLM | README/requirements comments | Optional local inference runtimes; user preference/config may exclude these, but source documents them |

### Checked-in default configuration

`config/dazy_config.json` records `default_llm_provider: openrouter` and `default_llm_model: openai/gpt-4o-mini`. This is a tracked template/config file, not proof of current machine selection. `config/api_keys.json` is ignored and contains machine-local secrets/settings; do not include it in exports.

### Provider registry details

The explicit registry in `providers/registry.py` groups:

- LLM: `llm_openai`, `llm_dazy`
- STT: `stt_whisper`, `stt_shrutam2`, `stt_sravaani`
- TTS: `tts_kokoro`, `tts_sherpa`, `tts_edge`, `tts_svara`, `tts_dhvaani`, `tts_higgs`, `tts_system`, `tts_piper`, `tts_elevenlabs`
- Engine: `engine_pipeline`

Provider files also present but not in that explicit TTS registry list include `tts_chatterbox`, `tts_mithi`, and `tts_volt`. They should be treated as source adapters not proven selectable through the current registry.

### Web: current provider order in source

The Edge Function's `buildProviders()` currently builds providers in this order:

1. Optional request-supplied `groq_api_key` (`groq-user`) — this is a security concern and should be removed.
2. Stored/env Groq.
3. OpenRouter.
4. DeepSeek.

It uses the OpenAI Chat Completions request/response shape. The currently implemented models are `qwen/qwen3.8-27b`, `openai/gpt-4o-mini`, and `deepseek-chat` respectively. Gemini is **not** in this web function yet.

### User-requested future direction, not yet committed

Proposed web ladder: Gemini primary → Groq → OpenRouter → DeepSeek. Proposed server-side secrets: `GEMINI_API_KEY` and `GEMINI_MODEL`. Configure secrets through Supabase Edge Function secrets; never paste them into frontend source, chat, GitHub or this ZIP. This is a plan, not an implemented change.
