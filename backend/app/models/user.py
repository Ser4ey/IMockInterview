from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    role = Column(String, default="user", nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    tariff = Column(String, default="free")
    requests_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chats = relationship("app.models.chat.Chat", back_populates="user")
    interview_sessions = relationship(
        "app.models.interview.InterviewSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    tariff_limit = relationship(
        "app.models.interview.TariffLimit",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
