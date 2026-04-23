import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class ResponseSchema(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    question_id: uuid.UUID
    question_index: int
    transcript_raw: str
    transcript_clean: Optional[str]
    sentiment_score: Optional[Decimal]
    was_refocused: bool
    refocus_count: int
    moderation_flagged: bool
    moderation_categories: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}
