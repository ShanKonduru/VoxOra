from __future__ import annotations

import secrets
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.participant import Participant, ParticipantStatus
from app.models.survey import Survey
from app.schemas.participant import (
    ParticipantBulkCreate,
    ParticipantListResponse,
    ParticipantResponse,
    ParticipantStatusUpdate,
)
from app.security.auth import get_current_admin
from app.security.rate_limiter import limiter

router = APIRouter(prefix="/api/participants", tags=["participants"])


# ── Bulk create participants ──────────────────────────────────────────────────

@router.post(
    "/",
    response_model=List[ParticipantResponse],
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
async def create_participants(
    request: Request,
    body: ParticipantBulkCreate,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> List[Participant]:
    # Verify survey exists
    survey_result = await db.execute(
        select(Survey).where(Survey.id == body.survey_id, Survey.is_active == True)  # noqa: E712
    )
    if not survey_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found or is inactive",
        )

    created: List[Participant] = []
    for p in body.participants:
        invite_token = secrets.token_urlsafe(32)
        participant = Participant(
            survey_id=body.survey_id,
            email=p.email,
            name=p.name,
            invite_token=invite_token,
        )
        db.add(participant)
        created.append(participant)

    await db.commit()
    for p in created:
        await db.refresh(p)
    return created


# ── List participants ─────────────────────────────────────────────────────────

@router.get("/", response_model=ParticipantListResponse)
async def list_participants(
    survey_id: uuid.UUID | None = Query(None),
    status_filter: ParticipantStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> dict:
    query = select(Participant)
    count_query = select(func.count()).select_from(Participant)

    if survey_id:
        query = query.where(Participant.survey_id == survey_id)
        count_query = count_query.where(Participant.survey_id == survey_id)
    if status_filter:
        query = query.where(Participant.status == status_filter)
        count_query = count_query.where(Participant.status == status_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = (
        query.order_by(Participant.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    participants = list(result.scalars().all())

    return {
        "items": participants,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ── Get single participant ────────────────────────────────────────────────────

@router.get("/{participant_id}", response_model=ParticipantResponse)
async def get_participant(
    participant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> Participant:
    return await _get_or_404(db, participant_id)


# ── Update participant status ─────────────────────────────────────────────────

@router.patch("/{participant_id}", response_model=ParticipantResponse)
@limiter.limit("30/minute")
async def update_participant_status(
    request: Request,
    participant_id: uuid.UUID,
    body: ParticipantStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> Participant:
    participant = await _get_or_404(db, participant_id)
    participant.status = body.status
    await db.commit()
    await db.refresh(participant)
    return participant


# ── Helper ────────────────────────────────────────────────────────────────────

async def _get_or_404(db: AsyncSession, participant_id: uuid.UUID) -> Participant:
    result = await db.execute(
        select(Participant).where(Participant.id == participant_id)
    )
    participant = result.scalar_one_or_none()
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found",
        )
    return participant
