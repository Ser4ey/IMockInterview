from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.models.chat import Chat, Message

class ChatRepository(BaseRepository[Chat]):
    async def get_multi_by_user(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Chat]:
        result = await db.execute(
            select(Chat)
            .filter(Chat.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Chat.created_at.desc())
        )
        return result.scalars().all()

class MessageRepository(BaseRepository[Message]):
    async def get_multi_by_chat(
        self, db: AsyncSession, *, chat_id: int, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        result = await db.execute(
            select(Message)
            .filter(Message.chat_id == chat_id)
            .offset(skip)
            .limit(limit)
            .order_by(Message.created_at.asc())
        )
        return result.scalars().all()

    async def get_last_message(self, db: AsyncSession, *, chat_id: int) -> Optional[Message]:
        result = await db.execute(
            select(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(1)
        )
        return result.scalars().first()

chat_repo = ChatRepository(Chat)
message_repo = MessageRepository(Message)
