import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class ParticipantCreate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(default=None, max_length=255)


class ParticipantBulkCreate(BaseModel):
    survey_id: uuid.UUID
    participants: List[ParticipantCreate] = Field(..., min_length=1, max_length=1000)


class ParticipantStatusUpdate(BaseModel):
    status: str = Field(
        ..., pattern="^(PENDING|IN_PROGRESS|COMPLETED|FLAGGED|EXPIRED)$"
    )


class ParticipantResponse(BaseModel):
    id: uuid.UUID
    survey_id: uuid.UUID
    email: Optional[str]
    name: Optional[str]
    status: str
    invite_token: str
    invite_sent_at: Optional[datetime]
    reminder_count: int
    last_reminded_at: Optional[datetime]
    created_at: datetime
    invite_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ParticipantListResponse(BaseModel):
    items: List[ParticipantResponse]
    total: int
    page: int
    per_page: int
    pages: int
