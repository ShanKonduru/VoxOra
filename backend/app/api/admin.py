from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.participant import Participant, ParticipantStatus
from app.models.response import Response as QuestionResponse
from app.models.session import Session as VoiceSession
from app.models.survey import Survey
from app.schemas.admin import (
    AdminStats,
    FlaggedSessionListResponse,
    ReminderRequest,
    ReminderResultResponse,
)
from app.security.auth import get_current_admin
from app.security.rate_limiter import limiter
from app.services.reminder_service import reminder_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminStats:
    total_surveys = (await db.execute(select(func.count()).select_from(Survey))).scalar_one()
    total_participants = (
        await db.execute(select(func.count()).select_from(Participant))
    ).scalar_one()
    completed = (
        await db.execute(
            select(func.count()).select_from(Participant).where(
                Participant.status == ParticipantStatus.COMPLETED
            )
        )
    ).scalar_one()
    in_progress = (
        await db.execute(
            select(func.count()).select_from(Participant).where(
                Participant.status == ParticipantStatus.IN_PROGRESS
            )
        )
    ).scalar_one()
    flagged = (
        await db.execute(
            select(func.count()).select_from(VoiceSession).where(
                VoiceSession.is_flagged == True  # noqa: E712
            )
        )
    ).scalar_one()

    return AdminStats(
        total_surveys=total_surveys,
        total_participants=total_participants,
        completed_participants=completed,
        in_progress_participants=in_progress,
        flagged_sessions=flagged,
    )


@router.get("/sessions/{session_id}/responses")
async def get_session_responses(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> list:
    result = await db.execute(
        select(QuestionResponse)
        .where(QuestionResponse.session_id == session_id)
        .order_by(QuestionResponse.created_at.asc())
    )
    return list(result.scalars().all())


@router.get("/flagged", response_model=FlaggedSessionListResponse)
async def list_flagged_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> dict:
    total = (
        await db.execute(
            select(func.count()).select_from(VoiceSession).where(
                VoiceSession.is_flagged == True  # noqa: E712
            )
        )
    ).scalar_one()
    q = (
        select(VoiceSession)
        .where(VoiceSession.is_flagged == True)  # noqa: E712
        .order_by(VoiceSession.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(q)
    return {"items": list(result.scalars().all()), "total": total, "page": page, "page_size": page_size}


@router.post("/reminders", response_model=ReminderResultResponse)
@limiter.limit("20/minute")
async def send_reminders(
    request: Request,
    body: ReminderRequest,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> ReminderResultResponse:
    """Send reminder emails to a list of pending participants."""
    results = []
    for pid in body.participant_ids:
        result = await db.execute(select(Participant).where(Participant.id == pid))
        participant: Participant | None = result.scalar_one_or_none()
        if not participant or not participant.email:
            continue
        invite_url = f"{body.base_url}/survey/{participant.invite_token}"
        r = await reminder_service.send_reminder(
            email=participant.email,
            name=participant.name,
            invite_url=invite_url,
            custom_message=body.custom_message,
            participant_id=str(participant.id),
        )
        if r.success:
            participant.reminder_count = (participant.reminder_count or 0) + 1
        results.append(r)
    await db.commit()
    successful = sum(1 for r in results if r.success)
    return ReminderResultResponse(sent=successful, total=len(results))
