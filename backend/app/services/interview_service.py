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
        chat_data = chat_in.model_dump()
        chat_data["user_id"] = user_id
        chat = await chat_repo.create(db, obj_in=chat_data)

        greeting = (
            f"Здравствуйте! Я ваш интервьюер на позицию {chat_in.position} ({chat_in.level}). "
            "Мы можем начать, когда вы будете готовы. Расскажите немного о себе."
        )

        await message_repo.create(db, obj_in={
            "chat_id": chat.id,
            "role": MessageRole.AI,
            "content": greeting,
        })

        return chat

    async def finish_interview(self, db: AsyncSession, chat_id: int) -> Chat:
        chat = await chat_repo.get(db, id=chat_id)
        if not chat:
            return None

        history_msgs = await message_repo.get_multi_by_chat(db, chat_id=chat_id)
        chat_history = [{"role": msg.role, "content": msg.content} for msg in history_msgs]

        try:
            feedback = await self.ai_service.analyze_interview(chat_history)
        except Exception as e:
            print(f"AI Analysis failed: {e}")
            feedback = (
                "Не удалось сгенерировать отзыв из-за ошибки AI-сервиса. "
                "Проверьте API-ключ или повторите попытку позже."
            )

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
            history_msgs = await message_repo.get_multi_by_chat(session, chat_id=chat_id)
            chat_history = [{"role": msg.role, "content": msg.content} for msg in history_msgs]

            try:
                ai_response_text = await self.ai_service.conduct_interview_step(chat_history, user_message)
                role = MessageRole.AI
            except Exception as e:
                print(f"AI Generation Error: {e}")
                ai_response_text = (
                    "Ошибка: не удалось сгенерировать ответ. "
                    f"Попробуйте повторить запрос. Детали: {str(e)}"
                )
                role = MessageRole.SYSTEM

            await message_repo.create(session, obj_in={
                "chat_id": chat_id,
                "role": role,
                "content": ai_response_text,
            })

            result = await session.execute(select(User).filter(User.id == user_id))
            user = result.scalars().first()
            if user:
                user.requests_count += 1
                session.add(user)
                await session.commit()


interview_service = InterviewService()
