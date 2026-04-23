from __future__ import annotations

import uuid
from typing import List

from pydantic import BaseModel


class AdminStats(BaseModel):
    total_surveys: int
    total_participants: int
    completed_participants: int
    in_progress_participants: int
    flagged_sessions: int


class FlaggedSessionListResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


class ReminderRequest(BaseModel):
    participant_ids: List[uuid.UUID]
    base_url: str
    custom_message: str = "We wanted to remind you that your survey is still waiting to be completed."


class ReminderResultResponse(BaseModel):
    sent: int
    total: int
