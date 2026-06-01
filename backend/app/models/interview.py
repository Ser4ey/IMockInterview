import enum

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class InterviewStatus(str, enum.Enum):
    ACTIVE = "active"
    FINISHED = "finished"


class InterviewStage(str, enum.Enum):
    CREATED = "created"
    INTRO = "intro"
    QUESTION = "question"
    FOLLOW_UP = "follow_up"
    FEEDBACK = "feedback"
    FINISHED = "finished"


class MessageSender(str, enum.Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"


class QuestionGenerationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class InterviewType(Base):
    __tablename__ = "interview_types"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, unique=True, index=True)
    role = Column(String, nullable=False, index=True)
    technology_stack = Column(Text, nullable=False, default="")
    description = Column(Text, nullable=False, default="")
    levels = Column(Text, nullable=False, default='["junior", "middle", "senior"]')
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    questions = relationship("app.models.interview.Question", back_populates="interview_type")
    sessions = relationship("app.models.interview.InterviewSession", back_populates="interview_type")
    generation_jobs = relationship("app.models.interview.QuestionGenerationJob", back_populates="interview_type")


class QuestionSource(Base):
    __tablename__ = "question_sources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    url = Column(Text, nullable=True)
    source_type = Column(String, nullable=False, default="llm")
    retrieved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    questions = relationship("app.models.interview.Question", back_populates="source")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    interview_type_id = Column(Integer, ForeignKey("interview_types.id"), nullable=False, index=True)
    level = Column(String, nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_hash = Column(String, nullable=True, index=True)
    expected_answer = Column(Text, nullable=False, default="")
    evaluation_criteria = Column(Text, nullable=False, default="[]")
    tags = Column(Text, nullable=False, default="[]")
    source_id = Column(Integer, ForeignKey("question_sources.id"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    interview_type = relationship("app.models.interview.InterviewType", back_populates="questions")
    source = relationship("app.models.interview.QuestionSource", back_populates="questions")
    messages = relationship("app.models.interview.Message", back_populates="question")


class QuestionGenerationJob(Base):
    __tablename__ = "question_generation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    interview_type_id = Column(Integer, ForeignKey("interview_types.id"), nullable=False, index=True)
    level = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default=QuestionGenerationStatus.PENDING.value)
    requested_count = Column(Integer, nullable=False, default=0)
    generated_count = Column(Integer, nullable=False, default=0)
    skipped_count = Column(Integer, nullable=False, default=0)
    provider = Column(String, nullable=False, default="mock")
    context_used = Column(Boolean, nullable=False, default=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    raw_response_preview = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

    interview_type = relationship("app.models.interview.InterviewType", back_populates="generation_jobs")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    interview_type_id = Column(Integer, ForeignKey("interview_types.id"), nullable=False, index=True)
    level = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default=InterviewStatus.ACTIVE.value)
    stage = Column(String, nullable=False, default=InterviewStage.CREATED.value)
    current_question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    question_index = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("app.models.user.User", back_populates="interview_sessions")
    interview_type = relationship("app.models.interview.InterviewType", back_populates="sessions")
    current_question = relationship("app.models.interview.Question", foreign_keys=[current_question_id])
    messages = relationship("app.models.interview.Message", back_populates="session", cascade="all, delete-orphan")
    result = relationship(
        "app.models.interview.InterviewResult",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Message(Base):
    __tablename__ = "interview_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)
    sender = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("app.models.interview.InterviewSession", back_populates="messages")
    question = relationship("app.models.interview.Question", back_populates="messages")


class InterviewResult(Base):
    __tablename__ = "interview_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False, unique=True, index=True)
    score = Column(Float, nullable=False, default=0.0)
    correctness = Column(Float, nullable=False, default=0.0)
    completeness = Column(Float, nullable=False, default=0.0)
    depth = Column(Float, nullable=False, default=0.0)
    communication = Column(Float, nullable=False, default=0.0)
    strengths = Column(Text, nullable=False, default="[]")
    weaknesses = Column(Text, nullable=False, default="[]")
    recommendations = Column(Text, nullable=False, default="")
    summary = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("app.models.interview.InterviewSession", back_populates="result")


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="default")
    purpose = Column(String, nullable=False, default="interview")
    system_prompt = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UsageLimit(Base):
    __tablename__ = "usage_limits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    daily_limit = Column(Integer, nullable=False, default=20)
    used_today = Column(Integer, nullable=False, default=0)
    reset_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("app.models.user.User", back_populates="usage_limit")
