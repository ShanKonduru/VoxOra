from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.state_machine import (
    InvalidTransitionError,
    SessionState,
    SurveyStateMachine,
)


@pytest.fixture
def sm() -> SurveyStateMachine:
    return SurveyStateMachine(
        session_id=uuid.uuid4(),
        total_questions=3,
        current_state=SessionState.GREETING,
        current_question_index=0,
    )


# ── Valid transitions ─────────────────────────────────────────────────────────

def test_greeting_to_asking(sm: SurveyStateMachine) -> None:
    sm.transition(SessionState.ASKING)
    assert sm.current_state == SessionState.ASKING


def test_asking_to_listening(sm: SurveyStateMachine) -> None:
    sm.transition(SessionState.ASKING)
    sm.transition(SessionState.LISTENING)
    assert sm.current_state == SessionState.LISTENING


def test_listening_to_processing(sm: SurveyStateMachine) -> None:
    sm.transition(SessionState.ASKING)
    sm.transition(SessionState.LISTENING)
    sm.transition(SessionState.PROCESSING)
    assert sm.current_state == SessionState.PROCESSING


def test_processing_to_logging(sm: SurveyStateMachine) -> None:
    sm.transition(SessionState.ASKING)
    sm.transition(SessionState.LISTENING)
    sm.transition(SessionState.PROCESSING)
    sm.transition(SessionState.LOGGING)
    assert sm.current_state == SessionState.LOGGING


def test_logging_to_asking_returns_true(sm: SurveyStateMachine) -> None:
    sm.transition(SessionState.ASKING)
    has_more = sm.advance()
    assert has_more is True
    assert sm.current_question_index == 1
    assert sm.current_state == SessionState.ASKING


def test_advance_to_last_question_returns_false(sm: SurveyStateMachine) -> None:
    sm.transition(SessionState.ASKING)
    sm.advance()  # → index 1
    sm.advance()  # → index 2 (still have more: 2 < 3)
    has_more = sm.advance()  # → index 3 (CLOSING)
    assert has_more is False
    assert sm.current_state == SessionState.CLOSING


def test_closing_to_completed(sm: SurveyStateMachine) -> None:
    sm.transition(SessionState.ASKING)
    sm.advance()
    sm.advance()
    sm.advance()  # → CLOSING
    sm.transition(SessionState.COMPLETED)
    assert sm.current_state == SessionState.COMPLETED


# ── Invalid transitions ───────────────────────────────────────────────────────

def test_invalid_transition_raises(sm: SurveyStateMachine) -> None:
    with pytest.raises(InvalidTransitionError):
        sm.transition(SessionState.COMPLETED)  # GREETING → COMPLETED invalid


def test_completed_is_terminal(sm: SurveyStateMachine) -> None:
    sm.transition(SessionState.ASKING)
    sm.advance()
    sm.advance()
    sm.advance()
    sm.transition(SessionState.COMPLETED)
    assert sm.is_terminal() is True


def test_terminated_is_terminal(sm: SurveyStateMachine) -> None:
    sm.terminate()
    assert sm.is_terminal() is True
    assert sm.current_state == SessionState.TERMINATED


# ── Skip question ─────────────────────────────────────────────────────────────

def test_skip_advances_question_index(sm: SurveyStateMachine) -> None:
    sm.transition(SessionState.ASKING)
    sm.skip_question()
    assert sm.current_question_index == 1


# ── Redis persistence ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_save_and_load_roundtrip() -> None:
    sid = uuid.uuid4()
    sm = SurveyStateMachine(
        session_id=sid,
        total_questions=5,
        current_state=SessionState.ASKING,
        current_question_index=2,
    )

    redis_mock = AsyncMock()
    redis_mock.setex = AsyncMock()
    redis_mock.get = AsyncMock(
        return_value='{"state": "ASKING", "question_index": 2, "total_questions": 5}'
    )

    await sm.save(redis_mock)
    redis_mock.setex.assert_called_once()

    loaded = await SurveyStateMachine.load(sid, redis_mock)
    assert loaded is not None
    assert loaded.current_state == SessionState.ASKING
    assert loaded.current_question_index == 2
    assert loaded.total_questions == 5


@pytest.mark.asyncio
async def test_load_returns_none_on_missing_key() -> None:
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    result = await SurveyStateMachine.load(uuid.uuid4(), redis_mock)
    assert result is None
