# DAZY — Speech & Model Providers Guide

## 1. Text-To-Speech (TTS) Providers

### A. Svara TTS v1 (Primary Expressive Indian Voice)
* **Model Checkpoint**: `kenpath/svara-tts-v1`
* **Licence**: Apache-2.0
* **Languages**: 19 Indian languages + Indian English
* **Hardware Deployments**:
  * **Intel OpenVINO INT4 (`kenpath/svara-tts-v1-openvino-int4`)**:
    * Size: ~1.94 GB.
    * Target: Intel Iris Xe Graphics, Intel Core i7 12th Gen CPU, and NPU.
    * Runs locally with zero cloud API dependencies.
  * **API Backend**: Connects to Svara HTTP inference server.
* **Emotion Tags**: Native tags formatted as `<happy>`, `<sad>`, `<anger>`, `<fear>`.
  * Example: `"Achha! Yeh toh bahut achhi news hai. <happy>"`

### B. DhVaani 0.5 (Secondary Indic Voice)
* **Model Checkpoint**: `ARTPARK-IISc/DhVaani-0.5`
* **Licence**: Apache-2.0 (gated model card)
* **Languages**: 27 Indian languages (especially strong for Urdu, Odia, Bengali, Hindi)
* **Features**: Zero-shot voice cloning using reference speaker audio (`dazy_original_female`), 24 kHz synthesis.

### C. Piper (Lightweight Fallback)
* Ultra-fast local synthesis on CPU.

---

## 2. Speech Recognition (ASR) Providers

### A. BharatGen Shrutam2 (Primary Indian ASR)
* **Model Checkpoint**: `bharatgenai/Shrutam-2`
* **Specialty**: Mid-sentence Hinglish and Urdu code-switching across 12 Indian languages.
* **Input**: 16 kHz mono microphone PCM.

### B. SraVaani 1.0 (Secondary Multilingual ASR)
* **Model Checkpoint**: `ARTPARK-IISc/SraVaani-1.0`
* **Licence**: MIT (430M parameters, ~900 MB FP16)
* **Specialty**: Broad coverage of 65 Indian dialects.

### C. Faster-Whisper (Universal Local Fallback)
* CPU-friendly local transcription with automatic language identification.

---

## 3. Conversational Brains (LLM)

### A. DAZY Conversational Brain
* Pre-configured with DAZY's identity, warmth, and Hinglish guidelines.
* Connects to:
  * **Sarvam AI** (`sarvam-2b`, `sarvam-m`) via `https://api.sarvam.ai/v1`
  * **Qwen 2.5** (7B / 14B) via local Ollama (`http://127.0.0.1:11434/v1`) or vLLM
  * OpenAI, Groq, DeepSeek, and OpenRouter endpoints.
