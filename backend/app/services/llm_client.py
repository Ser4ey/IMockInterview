import json
from abc import ABC, abstractmethod
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings
from app.models.interview import InterviewSession, InterviewStage, Message
from app.services.prompt_builder import prompt_builder


class LLMEvaluation(BaseModel):
    score: float = Field(ge=0, le=100)
    correctness: float = Field(ge=0, le=100)
    completeness: float = Field(ge=0, le=100)
    depth: float = Field(ge=0, le=100)
    communication: float = Field(ge=0, le=100)
    recommendations: str = Field(min_length=1)


class BaseLLMClient(ABC):
    @abstractmethod
    async def generate_stage_prompt(
        self,
        session: InterviewSession,
        stage: InterviewStage,
        history: list[Message],
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def evaluate_interview(self, session: InterviewSession, history: list[Message]) -> LLMEvaluation:
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    async def generate_stage_prompt(
        self,
        session: InterviewSession,
        stage: InterviewStage,
        history: list[Message],
    ) -> str:
        stage_questions = {
            InterviewStage.SELF_PRESENTATION: "Расскажите о себе и о проекте, которым вы особенно гордитесь.",
            InterviewStage.TECHNICAL: (
                f"Объясните ключевую техническую тему из области {session.specialization} "
                "и приведите пример из практики."
            ),
            InterviewStage.PRACTICE: (
                "Опишите решение небольшой практической задачи: архитектура, данные, проверки."
            ),
            InterviewStage.SOFT_SKILLS: (
                "Расскажите о сложной командной ситуации и о том, как вы с ней справились."
            ),
            InterviewStage.FEEDBACK: "Что вы хотите добавить перед итоговой оценкой?",
        }
        return stage_questions.get(stage, "Готовы начать? Расскажите кратко о своем опыте.")

    async def evaluate_interview(self, session: InterviewSession, history: list[Message]) -> LLMEvaluation:
        user_answers = [message for message in history if message.sender == "user"]
        score = min(100.0, 55.0 + len(user_answers) * 8.0)
        return LLMEvaluation(
            score=score,
            correctness=min(100.0, score - 3.0),
            completeness=min(100.0, score + 2.0),
            depth=min(100.0, score - 5.0),
            communication=min(100.0, score + 4.0),
            recommendations=(
                "Mock-оценка: структурируйте ответы по схеме ситуация-действие-результат, "
                "добавляйте конкретные технологии, ограничения и измеримые результаты."
            ),
        )


class YandexLLMClient(BaseLLMClient):
    def __init__(self) -> None:
        self.api_key = settings.YANDEX_API_KEY
        self.folder_id = settings.YANDEX_FOLDER_ID
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    async def generate_stage_prompt(
        self,
        session: InterviewSession,
        stage: InterviewStage,
        history: list[Message],
    ) -> str:
        if not self._is_configured:
            return await MockLLMClient().generate_stage_prompt(session, stage, history)
        messages = prompt_builder.build_stage_messages(session, stage, history)
        return await self._complete(messages, temperature=0.45, max_tokens=700)

    async def evaluate_interview(self, session: InterviewSession, history: list[Message]) -> LLMEvaluation:
        if not self._is_configured:
            return await MockLLMClient().evaluate_interview(session, history)

        messages = prompt_builder.build_evaluation_messages(session, history)
        raw_response = await self._complete(messages, temperature=0.2, max_tokens=1200)
        return self._parse_evaluation(raw_response)

    @property
    def _is_configured(self) -> bool:
        return bool(self.api_key and self.folder_id)

    async def _complete(self, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": str(max_tokens),
            },
            "messages": messages,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
        data = response.json()
        return data["result"]["alternatives"][0]["message"]["text"]

    def _parse_evaluation(self, raw_response: str) -> LLMEvaluation:
        cleaned = raw_response.replace("```json", "").replace("```", "").strip()
        try:
            payload: dict[str, Any] = json.loads(cleaned)
            return LLMEvaluation.model_validate(payload)
        except (json.JSONDecodeError, ValidationError, TypeError) as exc:
            raise ValueError("LLM вернул некорректный JSON итоговой оценки") from exc


def get_llm_client() -> BaseLLMClient:
    if settings.LLM_MODE.lower() == "yandex":
        return YandexLLMClient()
    return MockLLMClient()


llm_client = get_llm_client()
