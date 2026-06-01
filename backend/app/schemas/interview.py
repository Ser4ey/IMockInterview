from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.interview import (
    InterviewStage,
    InterviewStatus,
    MessageSender,
    QuestionGenerationStatus,
)


ALLOWED_LEVELS = {"junior", "middle", "senior"}


def normalize_level(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in ALLOWED_LEVELS:
        raise ValueError("Уровень должен быть junior, middle или senior")
    return normalized


class InterviewTypeBase(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    role: str = Field(min_length=2, max_length=120)
    technology_stack: str = Field(default="", max_length=1000)
    description: str = Field(default="", max_length=3000)
    levels: list[str] = Field(default_factory=lambda: ["junior", "middle", "senior"])
    is_active: bool = True

    @field_validator("levels")
    @classmethod
    def validate_levels(cls, value: list[str]) -> list[str]:
        normalized = []
        for level in value:
            item = normalize_level(level)
            if item not in normalized:
                normalized.append(item)
        if not normalized:
            raise ValueError("Нужно указать хотя бы один уровень")
        return normalized


class InterviewTypeCreate(InterviewTypeBase):
    auto_generate_questions: bool = False
    questions_per_level: int = Field(default=3, ge=1, le=20)


class InterviewTypeUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=160)
    role: Optional[str] = Field(default=None, min_length=2, max_length=120)
    technology_stack: Optional[str] = Field(default=None, max_length=1000)
    description: Optional[str] = Field(default=None, max_length=3000)
    levels: Optional[list[str]] = None
    is_active: Optional[bool] = None

    @field_validator("levels")
    @classmethod
    def validate_levels(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return value
        return InterviewTypeBase.validate_levels(value)


class InterviewTypeRead(InterviewTypeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    question_counts: dict[str, int] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class QuestionSourceRead(BaseModel):
    id: int
    title: str
    url: Optional[str] = None
    source_type: str
    retrieved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionBase(BaseModel):
    interview_type_id: int
    level: str
    question_text: str = Field(min_length=5, max_length=5000)
    question_hash: Optional[str] = None
    expected_answer: str = Field(default="", max_length=10000)
    evaluation_criteria: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source_id: Optional[int] = None
    is_active: bool = True

    @field_validator("level")
    @classmethod
    def validate_level(cls, value: str) -> str:
        return normalize_level(value)


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    level: Optional[str] = None
    question_text: Optional[str] = Field(default=None, min_length=5, max_length=5000)
    expected_answer: Optional[str] = Field(default=None, max_length=10000)
    evaluation_criteria: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    source_id: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator("level")
    @classmethod
    def validate_level(cls, value: Optional[str]) -> Optional[str]:
        return normalize_level(value) if value is not None else value


class QuestionRead(QuestionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    interview_type_title: Optional[str] = None
    source: Optional[QuestionSourceRead] = None

    class Config:
        from_attributes = True


class QuestionGenerationRequest(BaseModel):
    level: str
    requested_count: int = Field(default=3, ge=1, le=30)

    @field_validator("level")
    @classmethod
    def validate_level(cls, value: str) -> str:
        return normalize_level(value)


class QuestionGenerationJobRead(BaseModel):
    id: int
    interview_type_id: int
    interview_type_title: Optional[str] = None
    level: str
    status: QuestionGenerationStatus
    requested_count: int
    generated_count: int
    skipped_count: int = 0
    provider: str = "mock"
    context_used: bool = False
    input_tokens: int
    output_tokens: int
    raw_response_preview: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InterviewSessionCreate(BaseModel):
    interview_type_id: int
    level: str

    @field_validator("level")
    @classmethod
    def validate_level(cls, value: str) -> str:
        return normalize_level(value)


class InterviewSessionRead(BaseModel):
    id: int
    user_id: int
    interview_type_id: int
    interview_type_title: str
    role: str
    technology_stack: str
    level: str
    status: InterviewStatus
    stage: InterviewStage
    current_question_id: Optional[int] = None
    question_index: int
    started_at: datetime
    finished_at: Optional[datetime] = None


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class MessageRead(BaseModel):
    id: int
    session_id: int
    question_id: Optional[int] = None
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
    strengths: list[str]
    weaknesses: list[str]
    recommendations: str
    summary: str
    created_at: datetime


class InterviewTurnRead(BaseModel):
    session: InterviewSessionRead
    messages: list[MessageRead]
    result: Optional[InterviewResultRead] = None


class ProgressRead(BaseModel):
    total_interviews: int
    completed_interviews: int
    average_score: float
    weak_criteria: list[str]
    technical_daily_limit: int
    technical_used_today: int
    technical_remaining_today: int
    technical_reset_at: datetime
