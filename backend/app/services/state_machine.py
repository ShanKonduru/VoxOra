from __future__ import annotations

import json
import uuid
from enum import Enum
from typing import List

import redis.asyncio as aioredis

SESSION_STATE_TTL = 7200  # 2 hours


class SessionState(str, Enum):
    GREETING = "GREETING"
    ASKING = "ASKING"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    LOGGING = "LOGGING"
    CLOSING = "CLOSING"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"


# Defines which transitions are valid from each state
VALID_TRANSITIONS: dict[SessionState, List[SessionState]] = {
    SessionState.GREETING:   [SessionState.ASKING],
    SessionState.ASKING:     [SessionState.LISTENING, SessionState.PROCESSING],
    SessionState.LISTENING:  [SessionState.PROCESSING],
    SessionState.PROCESSING: [SessionState.LOGGING, SessionState.ASKING],
    SessionState.LOGGING:    [SessionState.ASKING, SessionState.CLOSING],
    SessionState.CLOSING:    [SessionState.COMPLETED],
    SessionState.COMPLETED:  [],
    SessionState.TERMINATED: [],
}


class InvalidTransitionError(Exception):
    pass


class SurveyStateMachine:
    def __init__(
        self,
        session_id: uuid.UUID,
        total_questions: int,
        current_state: SessionState = SessionState.GREETING,
        current_question_index: int = 0,
    ) -> None:
        self.session_id = str(session_id)
        self.total_questions = total_questions
        self.current_state = current_state
        self.current_question_index = current_question_index

    # ── Redis persistence ─────────────────────────────────────────────────────

    def _redis_key(self) -> str:
        return f"session_state:{self.session_id}"

    async def save(self, redis: aioredis.Redis) -> None:
        payload = {
            "state": self.current_state.value,
            "question_index": self.current_question_index,
            "total_questions": self.total_questions,
        }
        await redis.setex(self._redis_key(), SESSION_STATE_TTL, json.dumps(payload))

    @classmethod
    async def load(
        cls, session_id: uuid.UUID, redis: aioredis.Redis
    ) -> "SurveyStateMachine | None":
        raw = await redis.get(f"session_state:{session_id}")
        if not raw:
            return None
        data = json.loads(raw)
        return cls(
            session_id=session_id,
            total_questions=data["total_questions"],
            current_state=SessionState(data["state"]),
            current_question_index=data["question_index"],
        )

    # ── State management ──────────────────────────────────────────────────────

    def transition(self, new_state: SessionState) -> None:
        allowed = VALID_TRANSITIONS.get(self.current_state, [])
        if new_state not in allowed:
            raise InvalidTransitionError(
                f"Invalid transition: {self.current_state} → {new_state}"
            )
        self.current_state = new_state

    def advance(self) -> bool:
        """
        Move to the next question.
        Returns True if more questions remain, False if entering CLOSING.
        """
        self.current_question_index += 1
        if self.current_question_index >= self.total_questions:
            self.current_state = SessionState.CLOSING
            return False
        self.current_state = SessionState.ASKING
        return True

    def skip_question(self) -> bool:
        """Skip the current question and advance."""
        return self.advance()

    def terminate(self, reason: str = "unknown") -> None:  # noqa: ARG002
        self.current_state = SessionState.TERMINATED

    def is_terminal(self) -> bool:
        return self.current_state in (
            SessionState.COMPLETED,
            SessionState.TERMINATED,
        )
