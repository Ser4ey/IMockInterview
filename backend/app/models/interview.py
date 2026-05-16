import enum

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class InterviewStatus(str, enum.Enum):
    ACTIVE = "active"
    FINISHED = "finished"


class InterviewStage(str, enum.Enum):
    CREATED = "created"
    INTRO = "intro"
    SELF_PRESENTATION = "self_presentation"
    TECHNICAL = "technical"
    PRACTICE = "practice"
    SOFT_SKILLS = "soft_skills"
    FEEDBACK = "feedback"
    FINISHED = "finished"


class InterviewType(str, enum.Enum):
    FULL = "full"
    THEORY = "theory"
    SELF_PRESENTATION = "self_presentation"
    TECHNICAL = "technical"


class MessageSender(str, enum.Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    specialization = Column(String, nullable=False)
    level = Column(String, nullable=False)
    interview_type = Column(String, nullable=False, default=InterviewType.FULL.value)
    status = Column(String, nullable=False, default=InterviewStatus.ACTIVE.value)
    stage = Column(String, nullable=False, default=InterviewStage.CREATED.value)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("app.models.user.User", back_populates="interview_sessions")
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
    sender = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("app.models.interview.InterviewSession", back_populates="messages")


class InterviewResult(Base):
    __tablename__ = "interview_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False, unique=True, index=True)
    score = Column(Float, nullable=False, default=0.0)
    correctness = Column(Float, nullable=False, default=0.0)
    completeness = Column(Float, nullable=False, default=0.0)
    depth = Column(Float, nullable=False, default=0.0)
    communication = Column(Float, nullable=False, default=0.0)
    recommendations = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("app.models.interview.InterviewSession", back_populates="result")


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    interview_type = Column(String, nullable=False)
    level = Column(String, nullable=False)
    system_prompt = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ExternalContextSource(Base):
    __tablename__ = "external_context_sources"

    id = Column(Integer, primary_key=True, index=True)
    specialization = Column(String, nullable=False, index=True)
    source_type = Column(String, nullable=False, default="local")
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TariffLimit(Base):
    __tablename__ = "tariff_limits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    daily_limit = Column(Integer, nullable=False, default=20)
    used_today = Column(Integer, nullable=False, default=0)
    reset_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("app.models.user.User", back_populates="tariff_limit")
