from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.interview import InterviewStage, InterviewStatus, InterviewType, MessageSender


class InterviewSessionCreate(BaseModel):
    specialization: str = Field(min_length=2, max_length=120)
    level: str = Field(min_length=2, max_length=40)
    interview_type: InterviewType = InterviewType.FULL


class InterviewSessionRead(BaseModel):
    id: int
    user_id: int
    specialization: str
    level: str
    interview_type: InterviewType
    status: InterviewStatus
    stage: InterviewStage
    started_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class MessageRead(BaseModel):
    id: int
    session_id: int
    sender: MessageSender
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewResultRead(BaseModel):
    id: int
    session_id: int
    score: float
    correctness: float
    completeness: float
    depth: float
    communication: float
    recommendations: str
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewTurnRead(BaseModel):
    session: InterviewSessionRead
    messages: list[MessageRead]
    result: Optional[InterviewResultRead] = None


class ProgressRead(BaseModel):
    total_interviews: int
    completed_interviews: int
    average_score: float
    weak_criteria: list[str]
    daily_limit: int
    used_today: int
    remaining_today: int
    reset_at: datetime
