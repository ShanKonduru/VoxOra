import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QuestionCreate(BaseModel):
    order_index: int = Field(..., ge=1)
    question_text: str = Field(..., min_length=10, max_length=2000)
    question_type: str = Field(
        default="open_ended", pattern="^(open_ended|scale|yes_no)$"
    )
    expected_topics: Optional[List[str]] = None
    follow_up_text: Optional[str] = Field(default=None, max_length=500)


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = Field(default=None, min_length=10, max_length=2000)
    question_type: Optional[str] = Field(
        default=None, pattern="^(open_ended|scale|yes_no)$"
    )
    expected_topics: Optional[List[str]] = None
    follow_up_text: Optional[str] = Field(default=None, max_length=500)
    order_index: Optional[int] = Field(default=None, ge=1)


class QuestionResponse(BaseModel):
    id: uuid.UUID
    survey_id: uuid.UUID
    order_index: int
    question_text: str
    question_type: str
    expected_topics: Optional[List[str]]
    follow_up_text: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class SurveyCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    questions: List[QuestionCreate] = Field(default_factory=list)


class SurveyUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    is_active: Optional[bool] = None


class SurveyResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    is_active: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    questions: List[QuestionResponse] = []

    model_config = {"from_attributes": True}


class SurveyListItem(BaseModel):
    id: uuid.UUID
    title: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
