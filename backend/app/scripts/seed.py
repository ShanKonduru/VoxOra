"""
seed.py — Seed development database with sample data.

Creates:
  - 1 active survey with 5 questions
  - 10 participants with unique invite tokens

Usage:
    python -m app.scripts.seed
"""
from __future__ import annotations

import asyncio
import secrets
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.database import AsyncSessionLocal
from app.models.participant import Participant
from app.models.question import Question
from app.models.survey import Survey


SAMPLE_SURVEY = {
    "title": "Voxora Dev Sample Survey",
    "description": "A sample survey for development and testing purposes.",
}

SAMPLE_QUESTIONS = [
    {
        "order_index": 1,
        "question_text": "How satisfied are you with your current work-life balance?",
        "question_type": "scale",
        "expected_topics": ["work", "balance", "satisfaction"],
        "follow_up_text": "Could you elaborate on what factors contribute most to that rating?",
    },
    {
        "order_index": 2,
        "question_text": "What do you find most challenging about remote work?",
        "question_type": "open_ended",
        "expected_topics": ["remote", "challenges", "productivity"],
        "follow_up_text": None,
    },
    {
        "order_index": 3,
        "question_text": "Do you feel your organization supports your professional development?",
        "question_type": "yes_no",
        "expected_topics": ["development", "organization", "support"],
        "follow_up_text": "Can you share a specific example?",
    },
    {
        "order_index": 4,
        "question_text": "How would you rate the effectiveness of communication within your team?",
        "question_type": "scale",
        "expected_topics": ["communication", "team", "effectiveness"],
        "follow_up_text": "What tools or processes help or hinder team communication?",
    },
    {
        "order_index": 5,
        "question_text": "What one change would most improve your work experience?",
        "question_type": "open_ended",
        "expected_topics": ["improvement", "change", "experience"],
        "follow_up_text": None,
    },
]

SAMPLE_PARTICIPANTS = [
    {"email": f"participant{i:02d}@example.com", "name": f"Test User {i:02d}"}
    for i in range(1, 11)
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # Create survey
        survey = Survey(**SAMPLE_SURVEY, created_by="seed-script")
        db.add(survey)
        await db.flush()

        for q_data in SAMPLE_QUESTIONS:
            question = Question(survey_id=survey.id, **q_data)
            db.add(question)

        for p_data in SAMPLE_PARTICIPANTS:
            invite_token = secrets.token_urlsafe(32)
            participant = Participant(
                survey_id=survey.id,
                email=p_data["email"],
                name=p_data["name"],
                invite_token=invite_token,
            )
            db.add(participant)

        await db.commit()
        await db.refresh(survey)
        print(f"[OK] Created survey: {survey.title} (id={survey.id})")
        print(f"[OK] Created {len(SAMPLE_QUESTIONS)} questions")
        print(f"[OK] Created {len(SAMPLE_PARTICIPANTS)} participants")


if __name__ == "__main__":
    asyncio.run(seed())
