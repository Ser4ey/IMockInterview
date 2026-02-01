import json
import httpx
from typing import List, Dict, Any
from app.core.config import settings
from app.services.ai_service import AIService

class YandexGPTService(AIService):
    def __init__(self):
        self.api_key = settings.YANDEX_API_KEY
        self.folder_id = settings.YANDEX_FOLDER_ID
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        # Use yandexgpt/latest.
        self.model_uri = f"gpt://{self.folder_id}/yandexgpt/latest"

    async def generate_completion(self, messages: List[Dict[str, str]], temperature: float = 0.5, max_tokens: int = 1000) -> str:
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": str(max_tokens)
            },
            "messages": messages
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.base_url, json=data, headers=headers, timeout=30.0)
                response.raise_for_status()
                result = response.json()
                return result["result"]["alternatives"][0]["message"]["text"]
            except httpx.HTTPStatusError as e:
                # Log error or re-raise
                print(f"YandexGPT API Error: {e.response.text}")
                raise e
            except Exception as e:
                print(f"Error calling YandexGPT: {e}")
                raise e

    async def generate_interview_questions(self, position: str, level: str) -> List[str]:
        system_prompt = (
            "Ты — опытный технический интервьюер. Твоя задача — составить список из 5 вопросов для собеседования. "
            f"Позиция: {position}. Уровень: {level}. "
            "Верни только JSON массив строк, без лишнего текста. Пример: [\"Вопрос 1\", \"Вопрос 2\"]"
        )
        
        messages = [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": "Сгенерируй вопросы."}
        ]
        
        try:
            response_text = await self.generate_completion(messages, temperature=0.3)
            
            # Clean up Markdown code blocks if present
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            
            questions = json.loads(clean_text)
            if isinstance(questions, list):
                return questions
            return []
        except Exception as e:
            print(f"Failed to generate questions: {e}")
            return ["Расскажите о себе", "Ваш опыт работы?"] # Fallback

    async def conduct_interview_step(self, chat_history: List[Dict[str, Any]], message: str) -> str:
        system_prompt = (
            "Ты — строгий, но справедливый технический интервьюер. Ты проводишь собеседование. "
            "Твоя цель — проверить знания кандидата, но не валить его. "
            "Задавай вопросы по одному. Жди ответа кандидата. "
            "После ответа кандидата, дай краткий комментарий (верно/неверно/нужно уточнить) и задай СЛЕДУЮЩИЙ вопрос. "
            "Веди диалог естественно."
        )

        messages = [{"role": "system", "text": system_prompt}]
        
        for msg in chat_history:
             # Map internal roles to YandexGPT roles
             role = "assistant" if msg.get("role") == "ai" else "user"
             content = msg.get("content", "")
             messages.append({"role": role, "text": content})
        
        messages.append({"role": "user", "text": message})

        return await self.generate_completion(messages, temperature=0.6)

    async def analyze_interview(self, chat_history: List[Dict[str, Any]]) -> str:
        system_prompt = (
            "Ты — аналитик технических собеседований. Проанализируй весь диалог и дай развернутую обратную связь. "
            "Структура отчета:\n"
            "1. Общее впечатление.\n"
            "2. Сильные стороны.\n"
            "3. Слабые стороны / Пробелы в знаниях.\n"
            "4. Рекомендация по грейду (Junior/Middle/Senior).\n"
            "5. План развития (что почитать/изучить)."
        )

        messages = [{"role": "system", "text": system_prompt}]
        
        for msg in chat_history:
             role = "assistant" if msg.get("role") == "ai" else "user"
             content = msg.get("content", "")
             messages.append({"role": role, "text": content})
             
        messages.append({"role": "user", "text": "Подведи итоги собеседования."})

        return await self.generate_completion(messages, temperature=0.5, max_tokens=2000)
