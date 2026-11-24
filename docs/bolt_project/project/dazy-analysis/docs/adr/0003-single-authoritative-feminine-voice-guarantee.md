# ADR-0003: Single Authoritative Voice Guarantee & Atomic TTS Playback

* **Status:** Accepted
* **Deciders:** Neural Speech Synthesis Engineer, Principal Architect
* **Date:** 2026-11-24

## Context and Problem Statement
Previously, the assistant occasionally sounded like two people simultaneously or switched voices mid-response (e.g. alternating between male/female or primary and secondary providers). This happened when fallback providers were triggered without cancelling the active playback, or when partial streaming chunks collided.

## Decision Drivers
* DAZY must have one consistent, recognizable voice identity (`en-IN-NeerjaNeural`).
* Zero voice mixing or mid-sentence gender/timbre switching.
* Atomic transitions if a primary synthesis provider fails.

## Considered Options
1. **Atomic TTS Player with Transaction Locks**: Dedicated singleton (`AtomicTTSPlayer`) maintaining `current_playback_id` and `current_turn_id`. If primary fails, cancel transaction, clear pending queue, and execute replacement with clean state.
2. Ad-hoc queue flushing in individual TTS classes.
3. Single hardcoded provider with no fallback.

## Decision Outcome
Chosen option: **Atomic TTS Player with Transaction Locks**.
All audio output is serialized through `VoiceSessionManager.player`. Playback cannot overlap. If a failure occurs, `cancel_current()` halts audio hardware immediately, invalidates active chunks, and switches to the secondary provider cleanly.

### Positive Consequences
* Absolute guarantee of one active speaker voice at any instant.
* Immediate sub-50ms interruption / barge-in support.
* Persistent voice profile across app reboots.
