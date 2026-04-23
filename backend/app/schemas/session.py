import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PersonaSchema(BaseModel):
    name: str
    gender: str
    accent: str
    voice_id: str
    greeting_style: str


class SessionInitRequest(BaseModel):
    invite_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SessionInitResponse(BaseModel):
    session_id: uuid.UUID
    session_token: str
    persona: PersonaSchema
    survey_title: str
    participant_name: Optional[str]
    total_questions: int
    current_question_index: int
    state: str


class SessionStateResponse(BaseModel):
    session_id: uuid.UUID
    state: str
    current_question_index: int
    total_questions: int
    persona: PersonaSchema
    started_at: datetime
    is_flagged: bool

    model_config = {"from_attributes": True}
