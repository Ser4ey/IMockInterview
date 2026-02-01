from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.chat_repository import chat_repo, message_repo
from app.services.yandex_gpt import YandexGPTService
from app.models.chat import Chat, Message, MessageRole, ChatStatus
from app.schemas.chat import ChatCreate

class InterviewService:
    def __init__(self):
        self.ai_service = YandexGPTService()

    async def start_interview(self, db: AsyncSession, user_id: int, chat_in: ChatCreate) -> Chat:
        # 1. Create Chat
        chat_data = chat_in.dict()
        chat_data["user_id"] = user_id
        chat = await chat_repo.create(db, obj_in=chat_data)

        # 2. Generate initial greeting/questions
        # Note: We can make this async background task if it takes too long, 
        # but for now let's do it inline to ensure user sees something immediately.
        # Or better: Just a system greeting, and then user says "Hello" or "Ready".
        # BUT the plan says: "Создание чата: генерация приветствия от ИИ."
        
        greeting = f"Здравствуйте! Я ваш интервьюер на позицию {chat_in.position} ({chat_in.level}). Мы можем начать, когда вы будете готовы. Расскажите немного о себе."
        
        await message_repo.create(db, obj_in={
            "chat_id": chat.id,
            "role": MessageRole.AI,
            "content": greeting
        })
        
        return chat

    async def process_user_message(self, db: AsyncSession, chat_id: int, content: str):
        # 1. Save User Message
        await message_repo.create(db, obj_in={
            "chat_id": chat_id,
            "role": MessageRole.USER,
            "content": content
        })

        # 2. Get History
        history_msgs = await message_repo.get_multi_by_chat(db, chat_id=chat_id)
        chat_history = [{"role": msg.role, "content": msg.content} for msg in history_msgs]

        # 3. Call AI
        ai_response_text = await self.ai_service.conduct_interview_step(chat_history, content)

        # 4. Save AI Response
        await message_repo.create(db, obj_in={
            "chat_id": chat_id,
            "role": MessageRole.AI,
            "content": ai_response_text
        })

    async def generate_ai_response_task(self, db: AsyncSession, chat_id: int, user_message: str):
        """
        Wrapper for background task to ensure DB session is handled if needed.
        Actually, FastAPI BackgroundTasks runs after the response, so the original session might be closed.
        We need a new session or pass the session if we are sure it stays open (Dependency injection usually closes it).
        Best practice: create a new session inside the background task.
        """
        from app.db.session import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
             # We need to re-fetch/save using this new session
             # But wait, we already saved the user message in the main request.
             # So we just need to fetch history and save AI response.
             
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

interview_service = InterviewService()
