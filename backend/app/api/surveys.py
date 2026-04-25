from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.question import Question
from app.models.survey import Survey
from app.schemas.survey import (
    QuestionCreate,
    QuestionResponse,
    SurveyCreate,
    SurveyListItem,
    SurveyResponse,
    SurveyUpdate,
    QuestionUpdate,
)
from app.security.auth import get_current_admin
from app.security.rate_limiter import limiter

router = APIRouter(prefix="/api/surveys", tags=["surveys"])


# ── List all surveys ──────────────────────────────────────────────────────────

@router.get("/", response_model=List[SurveyListItem])
async def list_surveys(
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> List[SurveyListItem]:
    result = await db.execute(select(Survey).order_by(Survey.created_at.desc()))
    return list(result.scalars().all())


# ── Get survey detail ─────────────────────────────────────────────────────────

@router.get("/{survey_id}", response_model=SurveyResponse)
async def get_survey(
    survey_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> Survey:
    survey = await _get_or_404(db, survey_id)
    return survey


# ── Create survey ─────────────────────────────────────────────────────────────

@router.post("/", response_model=SurveyResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_survey(
    request: Request,
    body: SurveyCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> Survey:
    survey = Survey(
        title=body.title,
        description=body.description,
        created_by=str(admin.id),
    )
    db.add(survey)
    await db.flush()  # get the survey.id before creating questions

    for q in body.questions:
        question = Question(
            survey_id=survey.id,
            order_index=q.order_index,
            question_text=q.question_text,
            question_type=q.question_type,
            expected_topics=q.expected_topics or [],
            follow_up_text=q.follow_up_text,
        )
        db.add(question)

    await db.commit()
    await db.refresh(survey)
    return survey


# ── Update survey ─────────────────────────────────────────────────────────────

@router.put("/{survey_id}", response_model=SurveyResponse)
@limiter.limit("30/minute")
async def update_survey(
    request: Request,
    survey_id: uuid.UUID,
    body: SurveyUpdate,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> Survey:
    survey = await _get_or_404(db, survey_id)
    if body.title is not None:
        survey.title = body.title
    if body.description is not None:
        survey.description = body.description
    if body.is_active is not None:
        survey.is_active = body.is_active
    await db.commit()
    await db.refresh(survey)
    return survey


# ── Delete survey (soft delete) ───────────────────────────────────────────────

@router.delete("/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_survey(
    request: Request,
    survey_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> None:
    survey = await _get_or_404(db, survey_id)
    survey.is_active = False
    await db.commit()


# ── Add question to existing survey ──────────────────────────────────────────

@router.post(
    "/{survey_id}/questions",
    response_model=SurveyResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
async def add_question(
    request: Request,
    survey_id: uuid.UUID,
    body: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> Survey:
    survey = await _get_or_404(db, survey_id)
    question = Question(
        survey_id=survey.id,
        order_index=body.order_index,
        question_text=body.question_text,
        question_type=body.question_type,
        expected_topics=body.expected_topics or [],
        follow_up_text=body.follow_up_text,
    )
    db.add(question)
    await db.commit()
    await db.refresh(survey)
    return survey


# ── Delete question ───────────────────────────────────────────────────────────

@router.delete("/{survey_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_question(
    request: Request,
    survey_id: uuid.UUID,
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> None:
    result = await db.execute(
        select(Question).where(
            Question.id == question_id,
            Question.survey_id == survey_id,
        )
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    deleted_index = question.order_index
    await db.delete(question)
    await db.flush()
    # Rebalance order_index for remaining questions in this survey atomically
    await db.execute(
        update(Question)
        .where(Question.survey_id == survey_id, Question.order_index > deleted_index)
        .values(order_index=Question.order_index - 1)
    )
    await db.commit()


# ── Update question ───────────────────────────────────────────────────────────

@router.put(
    "/{survey_id}/questions/{question_id}",
    response_model=QuestionResponse,
)
@limiter.limit("30/minute")
async def update_question(
    request: Request,
    survey_id: uuid.UUID,
    question_id: uuid.UUID,
    body: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> Question:
    """Update one or more fields of an existing question."""
    result = await db.execute(
        select(Question).where(Question.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    if question.survey_id != survey_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Question does not belong to this survey")
    if body.question_text is not None:
        question.question_text = body.question_text
    if body.question_type is not None:
        question.question_type = body.question_type
    if body.expected_topics is not None:
        question.expected_topics = body.expected_topics
    if body.follow_up_text is not None:
        question.follow_up_text = body.follow_up_text
    if body.order_index is not None:
        question.order_index = body.order_index
    await db.commit()
    await db.refresh(question)
    return question


# ── Helper ────────────────────────────────────────────────────────────────────

async def _get_or_404(db: AsyncSession, survey_id: uuid.UUID) -> Survey:
    result = await db.execute(select(Survey).where(Survey.id == survey_id))
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    return survey
