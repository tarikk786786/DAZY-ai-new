# ADR-0004: Dual-Speaker Diarization & Synthetic Echo Disqualification

* **Status:** Accepted
* **Deciders:** Principal Architect, Audio DSP Engineer
* **Date:** 2026-11-24

## Context and Problem Statement
When two human speakers interact with the assistant, or when the assistant's own voice bleeds into the microphone, conventional systems confuse the speakers or mistake the assistant's voice for user instructions (causing echo loops).

## Decision Drivers
* Distinguish Speaker A (Owner: Tarik) and Speaker B (Companion: Priya) with individual permissions.
* Never falsely attribute synthetic assistant speech to a human speaker.
* Never classify uncertain voices as enrolled users (default to `unknown`).

## Considered Options
1. **Calibrated 64-dimensional Acoustic Spectral Embeddings + Echo Fingerprinting**: Extract normalized MFCC/FFT feature vectors for human speaker classification, and register synthesized speech embeddings in a rolling FIFO queue (`_assistant_echo_fingerprints`) to reject echo at the capture stage.
2. Cloud-based diarization API (adds 1–2s latency).
3. Single generic user model.

## Decision Outcome
Chosen option: **Calibrated 64-dimensional Acoustic Spectral Embeddings + Echo Fingerprinting**.
Implemented in `core/speaker_id.py` with enrollment vectors saved to `memory/voice_profiles/enrolled_speakers.json`. If incoming audio matches recent assistant speech above 0.85 cosine similarity, it is tagged as `assistant_echo` and discarded before LLM or engine dispatch.

### Positive Consequences
* Zero self-triggering loops.
* Role-based command execution (e.g., owner-only system commands).
* Low CPU overhead (< 2ms per 1024-sample block).
