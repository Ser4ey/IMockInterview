from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.models.chat import ChatStatus, MessageRole

# Message Schemas
class MessageBase(BaseModel):
    role: MessageRole
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    chat_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Chat Schemas
class ChatBase(BaseModel):
    position: str
    level: str
    topic: Optional[str] = None

class ChatCreate(ChatBase):
    pass

class Chat(ChatBase):
    id: int
    user_id: int
    status: ChatStatus
    created_at: datetime
    feedback: Optional[str] = None

    class Config:
        from_attributes = True

class ChatWithMessages(Chat):
    messages: List[Message] = []
