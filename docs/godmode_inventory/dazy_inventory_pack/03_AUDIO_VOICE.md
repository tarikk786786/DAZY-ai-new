# 03 — Hearing, speech, audio and voice system

## Audio engine foundations

- `sounddevice` — physical microphone and speaker streams.
- `numpy` — PCM buffers, RMS and signal arithmetic.
- `core/audio_devices.py` — device discovery/selection.
- `core/audio_dsp.py` — audio signal processing and VAD-related pipeline support.
- `core/listening_fsm.py` — listening/session state machine.
- `core/voice_session_manager.py` — voice session and auto-speak behaviour.
- `core/echo.py` — assistant self-echo protection.
- `core/wake_word.py` / `core/wake_engine.py` — wake word path.
- `core/viseme.py` / `core/viseme`-related code — mouth/viseme animation timing.
- `tools/audio_diagnostics.py` — audio diagnostics.

## Speech-to-text providers and adapters

| Provider/adapter | Source | What it is intended for | Status note |
|---|---|---|---|
| Gemini Live audio input/transcription | `main.py`, `core/gemini.py` | Realtime bidirectional voice conversation | Core route; requires API/quota |
| Faster Whisper | `providers/stt_whisper.py`, `core/streaming_asr.py` | Local multilingual transcription | Optional install; heavy model download |
| BharatGen Shrutam2 | `providers/stt_shrutam2.py` | Indian-language/code-mixed ASR | Adapter present; model/credentials/runtime not verified |
| SraVaani | `providers/stt_sravaani.py` | Multilingual Indian ASR | Adapter present; runtime not verified |
| WhisperLiveKit adapter | `core/streaming_asr.py` | Streaming Whisper chunks | Uses faster-whisper path when available; no proof that a standalone WhisperLiveKit service is configured |
| IndicConformer adapter | `core/streaming_asr.py` | Indian language ASR | Current inspected adapter initializes `_available=False` and returns empty when unavailable; partial/stub |
| SimulStreaming enum option | `core/streaming_asr.py` | Streaming ASR option | Enum label alone does not prove a complete provider implementation |
| Groq Whisper option | task ledger / project state | Hosted ASR | Historical log reports a Groq Whisper model test; credentials/runtime unverified |

### Hearing features in source

- 16 kHz mono PCM capture/streaming.
- Partial and final transcription events.
- Language stabilization and hysteresis.
- Hindi, English, Hinglish, Urdu, Odia, Bengali, Marathi, Gujarati, Tamil and Telugu labels in the language router/stabilizer.
- Speech segmentation and end-of-turn detection.
- Quiet/whispered speech handling heuristics.
- Voice activity and silence handling.
- Speaker ID/diarization support files and tests.
- Microphone recovery and device re-query path described in execution log.
- Bounded audio queues/backpressure.

## Text-to-speech providers

| Provider | Source | Notes |
|---|---|---|
| Svara TTS | `providers/tts_svara.py`, `docs/PROVIDERS.md` | Documented primary expressive Indian voice; repo docs describe emotion tags |
| DhVaani | `providers/tts_dhvaani.py`, docs | Secondary Indic voice; gated model card is mentioned in docs |
| Piper | `providers/tts_piper.py` | Lightweight local fallback; optional `piper-tts` |
| Kokoro | `providers/tts_kokoro.py` | Neural local voice; optional model download and ML dependencies |
| Sherpa | `providers/tts_sherpa.py` | Provider adapter |
| Edge TTS | `providers/tts_edge.py`, `core/tts.py` | Free online Microsoft Edge speech wrapper described in source; internet required, service terms apply |
| ElevenLabs | `providers/tts_elevenlabs.py` | API-key-backed hosted TTS; paid/quota rules apply |
| Chatterbox | `providers/tts_chatterbox.py` | Source adapter present, not in explicit registry list |
| Higgs | `providers/tts_higgs.py` | Source adapter and registry entry |
| Mithi | `providers/tts_mithi.py` | Source adapter present, not in explicit registry list |
| System TTS | `providers/tts_system.py`, `core/tts.py` | OS speech output |
| Volt | `providers/tts_volt.py` | Source adapter present, not in explicit registry list |

## Voice control and diagnostics

- Push-to-talk setting.
- Optional wake-word mode (“Hey Jarvis” model name in code).
- Always-on/auto-restart microphone flow in web browser app, with limitations of Web Speech API.
- Barge-in/interruption.
- Self-echo disqualification/echo guard.
- Pronunciation dictionary and normalization.
- Speaking rate/pitch/voice selection.
- Voice profiles and enrolled-speaker data file.
- TTS benchmark and speech evaluation tests.
- Dashboard waveform and live transcript visuals.

### Resource/licensing caution

A Python package being available on PyPI does not mean every checkpoint, voice, clone sample or cloud endpoint is free for all uses. Verify model-card licence, gated access, commercial-use rules, speaker consent and hardware needs individually. Some local speech models are large and may exceed an 8GB RAM budget when combined with the rest of the app.
