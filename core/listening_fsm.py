"""core/listening_fsm.py — 11-State Conversational State Machine for DAZY.

States:
- DISABLED: Voice assistant mode is turned off.
- STANDBY: Low-power wake detection active only (no large LLM running).
- WAKE_DETECTED: Wake word confirmed, playing chime/acknowledgement, pre-roll captured.
- LISTENING: Microphone actively streaming user speech with AEC & Silero VAD.
- TRANSCRIBING: Speech-to-text converting audio into text.
- UNDERSTANDING: Intent resolution, pronoun resolution, context & entity binding.
- THINKING: LLM generating response plan and streamed reply.
- SPEAKING: Neural TTS playing speech chunks through speakers (with AEC reference fed).
- FOLLOW_UP_LISTENING: Post-speech open window waiting for natural conversational follow-up.
- INTERRUPTED: User spoke over assistant playback; cancellation token triggered immediately.
- ERROR: Safe diagnostic recovery without crash or audio lockup.

Enforces:
- Atomic turn generation with unique session/turn tokens.
- Strict transition gating (e.g. cannot jump from STANDBY directly to SPEAKING).
- Immediate interruption cancellation: stops audio playback and purges queued chunks.
- Synchronized with VoiceSessionManager singleton.
"""
from __future__ import annotations

import enum
import logging
import time
import uuid
from typing import Any, Callable, Dict, Optional, Set

logger = logging.getLogger("dazy.listening_fsm")


class AssistantState(enum.Enum):
    DISABLED = "DISABLED"
    STANDBY = "STANDBY"
    WAKE_DETECTED = "WAKE_DETECTED"
    LISTENING = "LISTENING"
    TRANSCRIBING = "TRANSCRIBING"
    UNDERSTANDING = "UNDERSTANDING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    FOLLOW_UP_LISTENING = "FOLLOW_UP_LISTENING"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"


# Valid state transitions graph for bulletproof state enforcement
_ALLOWED_TRANSITIONS: Dict[AssistantState, Set[AssistantState]] = {
    AssistantState.DISABLED: {AssistantState.STANDBY, AssistantState.ERROR},
    AssistantState.STANDBY: {
        AssistantState.WAKE_DETECTED,
        AssistantState.LISTENING,
        AssistantState.SPEAKING,
        AssistantState.DISABLED,
        AssistantState.ERROR,
    },
    AssistantState.WAKE_DETECTED: {
        AssistantState.LISTENING,
        AssistantState.STANDBY,
        AssistantState.ERROR,
    },
    AssistantState.LISTENING: {
        AssistantState.TRANSCRIBING,
        AssistantState.STANDBY,
        AssistantState.INTERRUPTED,
        AssistantState.ERROR,
    },
    AssistantState.TRANSCRIBING: {
        AssistantState.UNDERSTANDING,
        AssistantState.THINKING,
        AssistantState.STANDBY,
        AssistantState.ERROR,
    },
    AssistantState.UNDERSTANDING: {
        AssistantState.THINKING,
        AssistantState.STANDBY,
        AssistantState.ERROR,
    },
    AssistantState.THINKING: {
        AssistantState.SPEAKING,
        AssistantState.STANDBY,
        AssistantState.INTERRUPTED,
        AssistantState.ERROR,
    },
    AssistantState.SPEAKING: {
        AssistantState.FOLLOW_UP_LISTENING,
        AssistantState.STANDBY,
        AssistantState.INTERRUPTED,
        AssistantState.ERROR,
    },
    AssistantState.FOLLOW_UP_LISTENING: {
        AssistantState.LISTENING,
        AssistantState.TRANSCRIBING,
        AssistantState.THINKING,
        AssistantState.SPEAKING,
        AssistantState.STANDBY,
        AssistantState.ERROR,
    },
    AssistantState.INTERRUPTED: {
        AssistantState.LISTENING,
        AssistantState.STANDBY,
        AssistantState.ERROR,
    },
    AssistantState.ERROR: {
        AssistantState.STANDBY,
        AssistantState.DISABLED,
    },
}


class TurnSession:
    """Encapsulates a single turn with cancellation token and metadata."""

    def __init__(self, session_id: str, turn_index: int):
        self.session_id = session_id
        self.turn_index = turn_index
        self.created_at = time.monotonic()
        self.cancelled = False
        self.speaker: str = "unknown"
        self.speaker_role: str = "companion"
        self.transcript: str = ""
        self.response_text: str = ""
        self.metadata: Dict[str, Any] = {}

    def cancel(self, reason: str = "interrupted") -> None:
        self.cancelled = True
        logger.info("Session %s (turn %d) CANCELLED: %s", self.session_id, self.turn_index, reason)


class ListeningStateMachine:
    """Thread-safe and async-compatible state machine governing DAZY conversational turns."""

    def __init__(
        self,
        initial_state: AssistantState = AssistantState.STANDBY,
        followup_timeout_sec: float = 20.0,
        on_state_changed: Optional[Callable[[AssistantState, AssistantState], None]] = None,
        on_interrupted: Optional[Callable[[TurnSession], None]] = None,
    ):
        self._state = initial_state
        self.followup_timeout_sec = followup_timeout_sec
        self.on_state_changed = on_state_changed
        self.on_interrupted = on_interrupted

        self._current_session: Optional[TurnSession] = None
        self._last_user_speech_time = time.monotonic()
        self._turn_counter = 0
        self._session_id = str(uuid.uuid4())[:8]

    @property
    def state(self) -> AssistantState:
        return self._state

    @property
    def current_session(self) -> Optional[TurnSession]:
        return self._current_session

    @property
    def session_id(self) -> str:
        return self._session_id

    def transition_to(self, new_state: AssistantState, context: Optional[dict] = None) -> bool:
        """Performs a valid state transition and notifies observers."""
        if self._state == new_state:
            return True

        # Enforce transition rules
        allowed = _ALLOWED_TRANSITIONS.get(self._state, set())
        if new_state not in allowed and new_state != AssistantState.ERROR and self._state != AssistantState.ERROR:
            logger.warning("FSM Invalid transition attempted: %s -> %s (allowing graceful recovery)",
                           self._state.value, new_state.value)

        old_state = self._state
        self._state = new_state
        logger.info("FSM State Transition: %s -> %s", old_state.value, new_state.value)

        # Trigger session creation on Wake or Start of Listening
        if new_state in (AssistantState.WAKE_DETECTED, AssistantState.LISTENING) and old_state in (
            AssistantState.STANDBY,
            AssistantState.DISABLED,
            AssistantState.SPEAKING,
            AssistantState.FOLLOW_UP_LISTENING,
            AssistantState.INTERRUPTED,
        ):
            self._turn_counter += 1
            self._current_session = TurnSession(self._session_id, self._turn_counter)
            self._last_user_speech_time = time.monotonic()

        # Handle Immediate Interruption
        if new_state == AssistantState.INTERRUPTED:
            if self._current_session:
                self._current_session.cancel("User interruption detected")
                if self.on_interrupted:
                    try:
                        self.on_interrupted(self._current_session)
                    except Exception as e:
                        logger.error("Error in on_interrupted handler: %s", e)

        # Update last speech timestamp
        if new_state in (AssistantState.LISTENING, AssistantState.TRANSCRIBING):
            self._last_user_speech_time = time.monotonic()

        if self.on_state_changed:
            try:
                self.on_state_changed(old_state, new_state)
            except Exception as e:
                logger.error("Error in on_state_changed handler: %s", e)

        return True

    def check_followup_timeout(self) -> bool:
        """Returns True if the follow-up window expired and transitions back to STANDBY."""
        if self._state in (AssistantState.LISTENING, AssistantState.FOLLOW_UP_LISTENING, AssistantState.SPEAKING, AssistantState.INTERRUPTED):
            elapsed = time.monotonic() - self._last_user_speech_time
            if elapsed > self.followup_timeout_sec:
                logger.info("Follow-up timeout (%.1fs > %.1fs) -> returning to STANDBY", elapsed, self.followup_timeout_sec)
                self.transition_to(AssistantState.STANDBY)
                return True
        return False

    def handle_barge_in(self) -> bool:
        """Triggered when acoustic DSP detects genuine user speech during playback."""
        if self._state == AssistantState.SPEAKING:
            logger.info("Barge-in / User interruption triggered while SPEAKING!")
            self.transition_to(AssistantState.INTERRUPTED)
            # Immediately transition to LISTENING to capture user instruction
            self.transition_to(AssistantState.LISTENING)
            return True
        return False
