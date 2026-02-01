from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.chat_repository import chat_repo, message_repo
from app.services.yandex_gpt import YandexGPTService
from app.models.chat import Chat, Message, MessageRole, ChatStatus
from app.models.user import User
from app.schemas.chat import ChatCreate

class InterviewService:
    def __init__(self):
        self.ai_service = YandexGPTService()

    async def start_interview(self, db: AsyncSession, user_id: int, chat_in: ChatCreate) -> Chat:
        # 1. Create Chat
        chat_data = chat_in.dict()
        chat_data["user_id"] = user_id
        chat = await chat_repo.create(db, obj_in=chat_data)

        # 2. Generate initial greeting
        greeting = f"Здравствуйте! Я ваш интервьюер на позицию {chat_in.position} ({chat_in.level}). Мы можем начать, когда вы будете готовы. Расскажите немного о себе."
        
        await message_repo.create(db, obj_in={
            "chat_id": chat.id,
            "role": MessageRole.AI,
            "content": greeting
        })
        
        return chat

    async def finish_interview(self, db: AsyncSession, chat_id: int) -> Chat:
        # 1. Get Chat
        chat = await chat_repo.get(db, id=chat_id)
        if not chat:
            return None 
            
        # 2. Get History
        history_msgs = await message_repo.get_multi_by_chat(db, chat_id=chat_id)
        chat_history = [{"role": msg.role, "content": msg.content} for msg in history_msgs]
        
        # 3. Analyze
        feedback = await self.ai_service.analyze_interview(chat_history)
        
        # 4. Update Chat
        chat.feedback = feedback
        chat.status = ChatStatus.COMPLETED
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        
        return chat

    async def generate_ai_response_task(self, db: AsyncSession, chat_id: int, user_message: str, user_id: int):
        """
        Wrapper for background task to ensure DB session is handled if needed.
        """
        from app.db.session import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
             # Re-fetch history
             history_msgs = await message_repo.get_multi_by_chat(session, chat_id=chat_id)
             chat_history = [{"role": msg.role, "content": msg.content} for msg in history_msgs]
             
             # Call AI
             ai_response_text = await self.ai_service.conduct_interview_step(chat_history, user_message)
             
             # Save AI Response
             await message_repo.create(session, obj_in={
                "chat_id": chat_id,
                "role": MessageRole.AI,
                "content": ai_response_text
             })

             # Increment User Usage
             result = await session.execute(select(User).filter(User.id == user_id))
             user = result.scalars().first()
             if user:
                 user.requests_count += 1
                 session.add(user)
                 await session.commit()


interview_service = InterviewService()
