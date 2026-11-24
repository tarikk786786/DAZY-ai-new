# ADR-0005: Calibrated Dual-Threshold Voice Activity Detection (VAD)

* **Status:** Accepted
* **Deciders:** Principal Audio Engineer, Systems Architect
* **Date:** 2026-11-24

## Context and Problem Statement
In `providers/engine_pipeline.py`, the energy-based VAD minimum threshold was hardcoded to `_VAD_ABSOLUTE_MIN = 0.006` in float32 ($\approx 196.6$ int16 RMS). On real laptop hardware, normal conversational speech measured at laptop distance averages RMS 25 to 120 (0.0008 to 0.0036 in float32). Because speech never breached 0.006, the buffer trimmed itself continuously and discarded all human voice input.

## Decision Drivers
* Reliable speech capture at conversational speaking distances.
* Avoid clipping quiet utterances or the start of sentences.
* Prevent room ambient hiss from triggering false turns.

## Considered Options
1. **Calibrated Adaptive Noise Floor with Tuned Absolute Floor**:
   - `_VAD_ABSOLUTE_MIN = 0.0008` (int16 RMS ~26)
   - `_VAD_FLOOR_MARGIN = 2.2`
   - Floor adapts downwards instantly and upwards slowly (factor 0.002).
2. Pure high-threshold energy VAD (caused complete assistant deafness).
3. Heavy ML model on every frame (adds latency on non-GPU systems).

## Decision Outcome
Chosen option: **Calibrated Adaptive Noise Floor with Tuned Absolute Floor**.
The floor tracks background noise dynamically while guaranteeing that speech above RMS 26 is detected. Combined with Silero VAD on segment endpoints, this eliminates both clipping and phantom speech.

### Positive Consequences
* Natural conversational speech triggers VAD immediately.
* Quiet talkers and soft voices are captured cleanly.
* Background fans or room noise do not trigger false turns.
