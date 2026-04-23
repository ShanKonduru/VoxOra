from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.participant import Participant, ParticipantStatus
from app.models.session import Session as VoiceSession
from app.models.survey import Survey
from app.schemas.session import (
    SessionInitRequest,
    SessionInitResponse,
    SessionStateResponse,
)
from app.security.auth import create_access_token, get_current_admin
from app.services.persona_manager import persona_manager
from app.services.state_machine import SessionState, SurveyStateMachine
from app.database import get_redis

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/init", response_model=SessionInitResponse, status_code=status.HTTP_201_CREATED)
async def init_session(
    body: SessionInitRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SessionInitResponse:
    """
    Validate participant invite token, create a voice session, assign a persona.
    Returns a short-lived session JWT used to authenticate the WebSocket connection.
    """
    # Validate invite token
    result = await db.execute(
        select(Participant).where(Participant.invite_token == body.invite_token)
    )
    participant: Participant | None = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite token")

    if participant.status == ParticipantStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Survey already completed")

    if participant.status == ParticipantStatus.EXPIRED:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite token has expired")

    # Load survey + questions
    survey_result = await db.execute(
        select(Survey).where(Survey.id == participant.survey_id, Survey.is_active == True)  # noqa: E712
    )
    survey: Survey | None = survey_result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found or inactive")

    total_questions = len(survey.questions)
    if total_questions == 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Survey has no questions")

    # Assign persona (avoid last 3 recent personas for this participant if retrievable)
    persona = persona_manager.assign_random()

    # Create DB session record
    client_ip = (
        request.headers.get("X-Forwarded-For", request.client.host)
        if request.client
        else None
    )
    session = VoiceSession(
        participant_id=participant.id,
        persona=persona.to_dict(),
        current_question_index=0,
        state=SessionState.GREETING.value,
        ip_address=client_ip,
    )
    db.add(session)
    participant.status = ParticipantStatus.IN_PROGRESS
    await db.commit()
    await db.refresh(session)

    # Initialise state machine in Redis
    redis = await get_redis()
    sm = SurveyStateMachine(
        session_id=session.id,
        total_questions=total_questions,
        current_state=SessionState.GREETING,
        current_question_index=0,
    )
    await sm.save(redis)

    # Create short-lived session token (JWT with session_id as subject)
    session_token = create_access_token(subject=str(session.id))

    return SessionInitResponse(
        session_token=session_token,
        session_id=str(session.id),
        persona=persona.to_dict(),
        survey_title=survey.title,
        total_questions=total_questions,
    )


@router.get("/{session_id}", response_model=SessionStateResponse)
async def get_session_state(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
) -> SessionStateResponse:
    """Retrieve current session state (admin only, for monitoring)."""
    result = await db.execute(
        select(VoiceSession).where(VoiceSession.id == session_id)
    )
    session: VoiceSession | None = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return SessionStateResponse(
        session_id=str(session.id),
        state=session.state,
        current_question_index=session.current_question_index,
        is_flagged=session.is_flagged,
        created_at=session.created_at,
    )
