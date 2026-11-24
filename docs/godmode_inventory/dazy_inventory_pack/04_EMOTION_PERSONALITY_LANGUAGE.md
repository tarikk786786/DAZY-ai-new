# 04 — Emotion, personality, dialogue and language

## Configured DAZY emotions

The checked-in desktop config and emotion controller use ten states:

`neutral`, `affection`, `happy`, `playful`, `empathetic`, `curious`, `excited`, `sad`, `serious`, `confident`.

The web UI maps these states into visible emotion badges; its model response schema also asks for an emotion string.

## Emotion implementation found in desktop source

- `core/emotion_controller.py` — lexicon/pattern-based text emotion estimates, intensity, confidence, scores and delivery style.
- `core/dazy/emotion_controller.py` — re-export of the main emotion controller.
- `core/multimodal_emotion.py` — acoustic prosody features (pitch mean/std, RMS, dynamic range, speaking-rate approximation, pause ratio, whisper heuristic), emotion2vec adapter shell, and an emotional response policy with uncertainty.
- `core/dazy/response_planner.py`, `core/response_planner.py` — delivery/response planning components.
- `core/dazy/voice_style.py`, `core/voice_style.py` — voice style controls.
- `agents/skills/emotional-intelligence/SKILL.md` — emotion tracking and empathetic calibration instructions.
- `tests/test_emotion.py`, `tests/test_hearing_emotion_speech_suite.py` — emotion-related tests.

**Important partial implementation:** `Emotion2VecPlusAdapter` in `core/multimodal_emotion.py` checks for `funasr`, but the inspected `predict_acoustic_emotion()` returns `{}`. Do not report a trained acoustic emotion model as active based on this adapter alone.

## Personality and communication

Checked-in `config/dazy_config.json` records personality parameters for warmth, friendliness, playfulness, humour, empathy, confidence and formality. `config/dazy_persona.md`, `core/dazy/persona.py`, `core/dazy_persona.py`, `core/prompt.txt`, and `agents/skills/dazy-personality/SKILL.md` hold persona/prompt logic.

The Web Edge Function has a separate `PERSONA` prompt for natural Hinglish responses, shorter spoken replies, memory capture and reminders. This is currently a different prompt implementation from desktop.

## Language capability

- Default configured language: Hinglish.
- Primary labels: Hindi (`hi`), English (`en`), Hinglish (`hi-en`).
- Secondary configured labels: Urdu (`ur`), Bengali (`bn`), Odia (`or`), Telugu (`te`), Tamil (`ta`), Marathi (`mr`), Gujarati (`gu`).
- `core/language_router.py`, `core/dazy/language_router.py`, `agents/skills/indian-languages/SKILL.md`.
- `knowledge/languages/hinglish_lexicon.md`, `knowledge/languages/urdu_terminology.md`.
- Indic language packages/models are referenced in provider docs but not all are in base requirements.

## Capability catalogue for future fine-grained emotion work

A richer emotional taxonomy should include joy, sadness, anger, fear, surprise, disgust, trust, anticipation, calm, amusement, affection, gratitude, pride, relief, hope, curiosity, confusion, disappointment, loneliness, embarrassment, shame, guilt, jealousy, envy, anxiety, nervousness, overwhelm, boredom, irritation, resentment, grief, nostalgia, admiration, awe, compassion, sympathy, determination and contentment.

Supporting dimensions: valence, arousal, intensity, confidence, modality, timestamp, temporal trend and uncertainty. Treat these as hypotheses about language/audio signals, not facts about a person's internal state or medical condition. A user correction must override model assumptions.

## Candidate emotion resources (not integrated dependencies)

- GoEmotions dataset: https://github.com/google-research/google-research/tree/master/goemotions
- pysentimiento: https://github.com/pysentimiento/pysentimiento
- VADER: https://github.com/cjhutto/vaderSentiment
- NRCLex: https://github.com/metalcorebear/NRCLex
- Hugging Face Transformers: https://github.com/huggingface/transformers
- Sentence Transformers: https://github.com/UKPLab/sentence-transformers
- DeepFace: https://github.com/serengil/deepface
- EmotiEffLib: https://github.com/sb-ai-lab/EmotiEffLib
- OpenFace: https://github.com/TadasBaltrusaitis/OpenFace
- openSMILE: https://github.com/audeering/opensmile
- librosa: https://github.com/librosa/librosa
- SpeechBrain: https://github.com/speechbrain/speechbrain
- pyannote.audio: https://github.com/pyannote/pyannote-audio
- MediaPipe: https://github.com/google-ai-edge/mediapipe

Dataset candidates requiring individual licence/consent review: MELD, CMU-MOSEI, IEMOCAP, RAVDESS, CREMA-D, EmoDB, AffectNet and SEMAINE.
