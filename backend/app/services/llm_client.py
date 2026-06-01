import json
import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.core.config import settings
from app.models.interview import InterviewSession, InterviewType, Message, Question
from app.services.prompt_builder import prompt_builder

logger = logging.getLogger(__name__)


QUESTION_BANK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["questions"],
    "additionalProperties": False,
    "properties": {
        "questions": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "question_text",
                    "level",
                    "tags",
                    "expected_answer",
                    "evaluation_criteria",
                    "source_title",
                    "source_url",
                ],
                "additionalProperties": False,
                "properties": {
                    "question_text": {"type": "string", "minLength": 12},
                    "level": {"type": "string", "enum": ["junior", "middle", "senior"]},
                    "tags": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "expected_answer": {"type": "string", "minLength": 20},
                    "evaluation_criteria": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                    },
                    "source_title": {"type": "string", "minLength": 1},
                    "source_url": {"type": ["string", "null"]},
                },
            },
        }
    },
}

INTERVIEWER_REPLY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["message", "should_ask_follow_up", "covered_criteria", "missing_criteria"],
    "additionalProperties": False,
    "properties": {
        "message": {"type": "string", "minLength": 1},
        "should_ask_follow_up": {"type": "boolean"},
        "covered_criteria": {"type": "array", "items": {"type": "string"}},
        "missing_criteria": {"type": "array", "items": {"type": "string"}},
    },
}

EVALUATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "score",
        "correctness",
        "completeness",
        "depth",
        "communication",
        "strengths",
        "weaknesses",
        "recommendations",
        "summary",
    ],
    "additionalProperties": False,
    "properties": {
        "score": {"type": "number", "minimum": 0, "maximum": 100},
        "correctness": {"type": "number", "minimum": 0, "maximum": 100},
        "completeness": {"type": "number", "minimum": 0, "maximum": 100},
        "depth": {"type": "number", "minimum": 0, "maximum": 100},
        "communication": {"type": "number", "minimum": 0, "maximum": 100},
        "strengths": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "weaknesses": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "recommendations": {"type": "string", "minLength": 1},
        "summary": {"type": "string"},
    },
}


class LLMEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0, le=100)
    correctness: float = Field(ge=0, le=100)
    completeness: float = Field(ge=0, le=100)
    depth: float = Field(ge=0, le=100)
    communication: float = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list, min_length=1)
    weaknesses: list[str] = Field(default_factory=list, min_length=1)
    recommendations: str = Field(min_length=1)
    summary: str = Field(default="")


class GeneratedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_text: str = Field(min_length=12)
    level: str
    tags: list[str] = Field(default_factory=list, min_length=1)
    expected_answer: str = Field(min_length=20)
    evaluation_criteria: list[str] = Field(min_length=2)
    source_title: str = Field(default="LLM generation", min_length=1)
    source_url: str | None = None

    @field_validator("level")
    @classmethod
    def normalize_level(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"junior", "middle", "senior"}:
            raise ValueError("level must be junior, middle or senior")
        return normalized

    @field_validator("tags", "evaluation_criteria")
    @classmethod
    def reject_empty_strings(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        if len(cleaned) != len(value):
            raise ValueError("list values must not be empty")
        return cleaned


class AgentQuestionBankResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[GeneratedQuestion] = Field(min_length=1)


class LLMInterviewerReply(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)
    should_ask_follow_up: bool
    covered_criteria: list[str] = Field(default_factory=list)
    missing_criteria: list[str] = Field(default_factory=list)


class BaseLLMClient(ABC):
    provider = "unknown"
    input_tokens: int = 0
    output_tokens: int = 0

    @abstractmethod
    async def generate_question_bank(
        self,
        interview_type: InterviewType,
        level: str,
        requested_count: int,
    ) -> list[GeneratedQuestion]:
        raise NotImplementedError

    @abstractmethod
    async def generate_interviewer_reply(
        self,
        session: InterviewSession,
        question: Question,
        history: list[Message],
    ) -> LLMInterviewerReply:
        raise NotImplementedError

    @abstractmethod
    async def evaluate_interview(
        self,
        session: InterviewSession,
        questions: list[Question],
        history: list[Message],
    ) -> LLMEvaluation:
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    provider = "mock"

    async def generate_question_bank(
        self,
        interview_type: InterviewType,
        level: str,
        requested_count: int,
    ) -> list[GeneratedQuestion]:
        templates = _mock_questions_for(interview_type, level)
        questions = []
        for index in range(requested_count):
            item = templates[index % len(templates)]
            questions.append(GeneratedQuestion(level=level, **item))
        self.input_tokens = 0
        self.output_tokens = 0
        return questions

    async def generate_interviewer_reply(
        self,
        session: InterviewSession,
        question: Question,
        history: list[Message],
    ) -> LLMInterviewerReply:
        user_answers = [message for message in history if message.sender == "user"]
        should_follow_up = bool(user_answers and len(user_answers[-1].content.strip()) < 120)
        message = (
            "Ответ пока раскрыт не полностью. Уточните, пожалуйста: какие практические ограничения, "
            "риски или компромиссы вы бы учли в реальном проекте?"
            if should_follow_up
            else "Хорошо, ответ можно принять. Перейдём к следующему вопросу."
        )
        return LLMInterviewerReply(
            message=message,
            should_ask_follow_up=should_follow_up,
            covered_criteria=[],
            missing_criteria=[],
        )

    async def evaluate_interview(
        self,
        session: InterviewSession,
        questions: list[Question],
        history: list[Message],
    ) -> LLMEvaluation:
        user_answers = [message for message in history if message.sender == "user"]
        answered_questions = {message.question_id for message in user_answers if message.question_id}
        base = 58 + len(answered_questions) * 9 + min(len(user_answers), 5) * 3
        score = min(96.0, float(base))
        return LLMEvaluation(
            score=score,
            correctness=max(0.0, min(100.0, score - 4)),
            completeness=max(0.0, min(100.0, score - 1)),
            depth=max(0.0, min(100.0, score - 7)),
            communication=max(0.0, min(100.0, score + 3)),
            strengths=[
                "Ответы достаточно структурированы и связаны с практическими задачами.",
                "Кандидат понимает базовые принципы выбранной роли и уровня.",
            ],
            weaknesses=[
                "Стоит чаще раскрывать ограничения выбранных решений.",
                "Полезно добавлять больше конкретных примеров из опыта или учебных проектов.",
            ],
            recommendations=(
                "Повторите темы из банка вопросов, заранее готовьте примеры по схеме: задача, "
                "решение, компромиссы, результат."
            ),
            summary="Mock-оценка сформирована локальным LLM-режимом.",
        )


class YandexAIStudioAgentsClient(BaseLLMClient):
    provider = "yandex_agent"

    def __init__(self) -> None:
        self.api_key = settings.YANDEX_API_KEY
        self.folder_id = settings.YANDEX_FOLDER_ID
        self.base_url = settings.YANDEX_AI_STUDIO_BASE_URL.rstrip("/")
        self.timeout = settings.YANDEX_AGENTS_TIMEOUT_SECONDS
        self.store_responses = settings.YANDEX_AGENT_STORE_RESPONSES
        self.question_model = settings.YANDEX_QUESTION_AGENT_MODEL
        self.interview_model = settings.YANDEX_INTERVIEW_AGENT_MODEL
        self.review_model = settings.YANDEX_REVIEW_AGENT_MODEL
        self.input_tokens = 0
        self.output_tokens = 0

    async def generate_question_bank(
        self,
        interview_type: InterviewType,
        level: str,
        requested_count: int,
    ) -> list[GeneratedQuestion]:
        messages = prompt_builder.build_question_generation_messages(interview_type, level, requested_count)
        payload = await self._create_response(
            model=self.question_model,
            instructions=messages[0]["text"],
            input_text=messages[1]["text"],
            schema_name="imock_question_bank",
            schema=QUESTION_BANK_SCHEMA,
            temperature=0.25,
            max_output_tokens=4000,
        )
        return self._parse_question_bank(payload).questions

    async def generate_interviewer_reply(
        self,
        session: InterviewSession,
        question: Question,
        history: list[Message],
    ) -> LLMInterviewerReply:
        messages = prompt_builder.build_interviewer_reply_messages(session, question, history)
        payload = await self._create_response(
            model=self.interview_model,
            instructions=messages[0]["text"],
            input_text=messages[1]["text"],
            schema_name="imock_interviewer_reply",
            schema=INTERVIEWER_REPLY_SCHEMA,
            temperature=0.35,
            max_output_tokens=900,
        )
        return self._parse_interviewer_reply(payload)

    async def evaluate_interview(
        self,
        session: InterviewSession,
        questions: list[Question],
        history: list[Message],
    ) -> LLMEvaluation:
        messages = prompt_builder.build_evaluation_messages(session, questions, history)
        payload = await self._create_response(
            model=self.review_model,
            instructions=messages[0]["text"],
            input_text=messages[1]["text"],
            schema_name="imock_interview_review",
            schema=EVALUATION_SCHEMA,
            temperature=0.2,
            max_output_tokens=1800,
        )
        return self._parse_evaluation(payload)

    async def _create_response(
        self,
        model: str,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict[str, Any],
        temperature: float,
        max_output_tokens: int,
    ) -> dict[str, Any]:
        self._ensure_configured(model)
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
            "x-folder-id": self.folder_id,
        }
        request_body = {
            "model": model,
            "input": input_text,
            "instructions": instructions,
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "store": self.store_responses,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                }
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/responses", headers=headers, json=request_body)
                response.raise_for_status()
        except httpx.HTTPError:
            logger.exception("Yandex AI Studio agent request failed")
            raise
        data = response.json()
        self._ensure_completed_response(data)
        usage = data.get("usage") or {}
        self.input_tokens = int(usage.get("input_tokens") or 0)
        self.output_tokens = int(usage.get("output_tokens") or 0)
        return data

    def _ensure_completed_response(self, data: dict[str, Any]) -> None:
        status = data.get("status")
        if not status or status == "completed":
            return
        detail = data.get("error") or data.get("incomplete_details") or {}
        raise RuntimeError(f"Yandex AI Studio response was not completed: status={status}, detail={detail}")

    def _ensure_configured(self, model: str) -> None:
        if not self.api_key:
            raise RuntimeError("YANDEX_API_KEY is not configured")
        if not self.folder_id:
            raise RuntimeError("YANDEX_FOLDER_ID is not configured")
        if not model:
            raise RuntimeError("Yandex AI Studio agent model is not configured")

    def _parse_question_bank(self, response_payload: dict[str, Any] | str) -> AgentQuestionBankResponse:
        payload = self._load_response_json(response_payload)
        try:
            return AgentQuestionBankResponse.model_validate(payload)
        except (TypeError, ValidationError) as exc:
            raise ValueError("Question agent returned invalid JSON schema") from exc

    def _parse_interviewer_reply(self, response_payload: dict[str, Any] | str) -> LLMInterviewerReply:
        payload = self._load_response_json(response_payload)
        try:
            return LLMInterviewerReply.model_validate(payload)
        except (TypeError, ValidationError) as exc:
            raise ValueError("Interviewer agent returned invalid JSON schema") from exc

    def _parse_evaluation(self, response_payload: dict[str, Any] | str) -> LLMEvaluation:
        payload = self._load_response_json(response_payload)
        try:
            return LLMEvaluation.model_validate(payload)
        except (TypeError, ValidationError) as exc:
            raise ValueError("Review agent returned invalid JSON schema") from exc

    def _load_response_json(self, response_payload: dict[str, Any] | str) -> Any:
        raw_text = response_payload if isinstance(response_payload, str) else self._extract_output_text(response_payload)
        cleaned = raw_text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError("Agent returned invalid JSON") from exc

    def _extract_output_text(self, response_payload: dict[str, Any]) -> str:
        output_text = response_payload.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text

        output_items = response_payload.get("output") or []
        for item in output_items:
            for content in item.get("content") or []:
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    return text
        raise ValueError("Agent response does not contain output text")


def get_llm_client() -> BaseLLMClient:
    mode = settings.LLM_MODE.lower()
    if mode == "mock":
        return MockLLMClient()
    if mode == "yandex_agents":
        return YandexAIStudioAgentsClient()
    raise RuntimeError("Unsupported LLM_MODE. Use 'mock' or 'yandex_agents'.")


def _mock_questions_for(interview_type: InterviewType, level: str) -> list[dict[str, Any]]:
    stack = interview_type.technology_stack.lower()
    if "react" in stack or "frontend" in interview_type.role.lower():
        return _frontend_questions(level)
    if "java" in stack:
        return _java_questions(level)
    return _generic_backend_questions(level)


def _java_questions(level: str) -> list[dict[str, Any]]:
    data = {
        "junior": [
            (
                "Чем отличается ArrayList от LinkedList в Java?",
                "Кандидат объясняет хранение данных, доступ по индексу, вставку, удаление и типичные сценарии применения.",
                ["понимание массивов и связных списков", "знание сложности операций", "умение выбрать коллекцию под задачу"],
                ["Java", "Collections"],
            ),
            (
                "Что такое интерфейс в Java и зачем он нужен?",
                "Кандидат объясняет контракт, полиморфизм, реализацию несколькими классами и отличие от класса.",
                ["понимание абстракции", "знание implements", "пример практического использования"],
                ["Java", "OOP"],
            ),
            (
                "Что такое REST API?",
                "Кандидат описывает ресурсы, HTTP-методы, статусы ответов и stateless-подход.",
                ["ресурсная модель", "HTTP methods", "коды статусов"],
                ["REST", "Backend"],
            ),
        ],
        "middle": [
            (
                "Как работает Spring IoC container?",
                "Кандидат объясняет inversion of control, DI, bean lifecycle, scopes и конфигурацию контекста.",
                ["DI и IoC", "bean lifecycle", "scope и конфигурация"],
                ["Java", "Spring"],
            ),
            (
                "Чем optimistic locking отличается от pessimistic locking?",
                "Кандидат сравнивает подходы к конкурентному доступу, версии записей, блокировки и сценарии применения.",
                ["конкурентный доступ", "version column", "trade-off производительности"],
                ["Database", "Transactions"],
            ),
            (
                "Как устроена обработка транзакций в Spring?",
                "Кандидат объясняет @Transactional, propagation, isolation, rollback rules и proxy-механику.",
                ["@Transactional", "isolation/propagation", "rollback и proxy"],
                ["Spring", "Transactions"],
            ),
        ],
        "senior": [
            (
                "Как спроектировать отказоустойчивый сервис обработки заказов?",
                "Кандидат описывает очереди, идемпотентность, outbox, ретраи, мониторинг и деградацию.",
                ["устойчивость", "идемпотентность", "наблюдаемость"],
                ["Architecture", "Reliability"],
            ),
            (
                "Как диагностировать деградацию производительности backend-сервиса?",
                "Кандидат объясняет метрики, tracing, profiling, анализ БД, пулов, очередей и внешних зависимостей.",
                ["observability", "profiling", "root cause analysis"],
                ["Performance", "Backend"],
            ),
            (
                "Какие компромиссы есть у микросервисной архитектуры?",
                "Кандидат сравнивает независимость поставки, сложность distributed systems, данные, сеть и эксплуатацию.",
                ["границы сервисов", "distributed systems", "операционная сложность"],
                ["Microservices", "Architecture"],
            ),
        ],
    }
    return [_question_tuple_to_dict(item) for item in data[level]]


def _frontend_questions(level: str) -> list[dict[str, Any]]:
    data = {
        "junior": [
            (
                "Чем controlled component отличается от uncontrolled component в React?",
                "Кандидат объясняет управление значением через state, ref и сценарии применения.",
                ["React state", "forms", "controlled/uncontrolled"],
                ["React", "Forms"],
            ),
            (
                "Зачем нужен useEffect?",
                "Кандидат объясняет сайд-эффекты, зависимости, cleanup и типичные ошибки.",
                ["effects", "dependency array", "cleanup"],
                ["React", "Hooks"],
            ),
            (
                "Что такое props и state в React?",
                "Кандидат различает входные данные компонента и внутреннее состояние.",
                ["props", "state", "component data flow"],
                ["React", "Basics"],
            ),
        ],
        "middle": [
            (
                "Как избежать лишних ререндеров в React-приложении?",
                "Кандидат объясняет memo, useMemo, useCallback, структуру state и профилирование.",
                ["render model", "memoization", "profiling"],
                ["React", "Performance"],
            ),
            (
                "Как организовать работу с серверным состоянием во frontend?",
                "Кандидат описывает кеш, invalidation, loading/error states и optimistic updates.",
                ["server state", "cache invalidation", "UX states"],
                ["Frontend", "API"],
            ),
            (
                "Какие риски есть при использовании useEffect для загрузки данных?",
                "Кандидат говорит о race conditions, abort, повторных запросах и обработке ошибок.",
                ["async effects", "race conditions", "error handling"],
                ["React", "Hooks"],
            ),
        ],
        "senior": [
            (
                "Как спроектировать frontend-архитектуру большого React-приложения?",
                "Кандидат описывает границы модулей, state management, дизайн-систему, тесты и delivery.",
                ["architecture", "module boundaries", "maintainability"],
                ["React", "Architecture"],
            ),
            (
                "Как выстроить стратегию производительности для сложного интерфейса?",
                "Кандидат говорит о метриках, profiling, bundle splitting, rendering и UX budgets.",
                ["web vitals", "bundle", "render performance"],
                ["Performance", "Frontend"],
            ),
            (
                "Как обеспечить качество frontend-продукта в команде?",
                "Кандидат объясняет тестовую пирамиду, code review, дизайн-систему, мониторинг и процессы.",
                ["quality", "testing", "team process"],
                ["Frontend", "Engineering"],
            ),
        ],
    }
    return [_question_tuple_to_dict(item) for item in data[level]]


def _generic_backend_questions(level: str) -> list[dict[str, Any]]:
    return _java_questions(level)


def _question_tuple_to_dict(item: tuple[str, str, list[str], list[str]]) -> dict[str, Any]:
    question_text, expected_answer, evaluation_criteria, tags = item
    return {
        "question_text": question_text,
        "expected_answer": expected_answer,
        "evaluation_criteria": evaluation_criteria,
        "tags": tags,
        "source_title": "IMock mock question bank",
        "source_url": None,
    }


llm_client = get_llm_client()
