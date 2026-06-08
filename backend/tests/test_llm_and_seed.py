import asyncio

from sqlalchemy import func, select

from app.core.config import settings
from app.core.security import verify_password
from app.models.interview import InterviewType, Question
from app.models.user import User
from app.services.admin_bootstrap import ensure_admin_user
from app.services.demo_seed import seed_demo_data
from app.services.llm_client import (
    LLMInterviewerReply,
    MockLLMClient,
    YandexAIStudioAgentsClient,
    get_llm_client,
)
from app.services.prompt_builder import PromptBuilder
from tests.utils import ApiTestCase


class LLMAndSeedTest(ApiTestCase):
    def test_admin_bootstrap_creates_and_updates_admin_from_env(self):
        old_email = settings.ADMIN_EMAIL
        old_password = settings.ADMIN_PASSWORD
        old_full_name = settings.ADMIN_FULL_NAME
        try:
            settings.ADMIN_EMAIL = "admin@example.com"
            settings.ADMIN_PASSWORD = "123"
            settings.ADMIN_FULL_NAME = "Production Admin"

            async def run_bootstrap():
                async with self.SessionLocal() as session:
                    await ensure_admin_user(session)
                async with self.SessionLocal() as session:
                    user = await session.scalar(select(User).where(User.email == "admin@example.com"))
                    count = await session.scalar(select(func.count(User.id)).where(User.email == "admin@example.com"))
                    return user, count

            user, count = asyncio.run(run_bootstrap())
            self.assertEqual(count, 1)
            self.assertEqual(user.role, "admin")
            self.assertTrue(user.is_superuser)
            self.assertTrue(user.is_active)
            self.assertEqual(user.full_name, "Production Admin")
            self.assertTrue(verify_password("123", user.hashed_password))

            settings.ADMIN_PASSWORD = "changed123"
            user, count = asyncio.run(run_bootstrap())
            self.assertEqual(count, 1)
            self.assertTrue(verify_password("changed123", user.hashed_password))
        finally:
            settings.ADMIN_EMAIL = old_email
            settings.ADMIN_PASSWORD = old_password
            settings.ADMIN_FULL_NAME = old_full_name

    def test_mock_question_generation_returns_structured_questions(self):
        interview_type = InterviewType(
            title="Backend Java-разработчик",
            role="Backend Java-разработчик",
            technology_stack="Java, Spring",
            description="",
        )

        async def run():
            return await MockLLMClient().generate_question_bank(interview_type, "junior", 3)

        questions = asyncio.run(run())
        self.assertEqual(len(questions), 3)
        self.assertTrue(questions[0].question_text)
        self.assertTrue(questions[0].evaluation_criteria)

    def test_prompt_builder_demands_json_for_question_generation(self):
        interview_type = InterviewType(
            title="Frontend React-разработчик",
            role="Frontend React-разработчик",
            technology_stack="React, TypeScript",
            description="",
        )
        messages = PromptBuilder().build_question_generation_messages(interview_type, "middle", 5)
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("JSON", messages[0]["text"])
        self.assertIn("Frontend React-разработчик", messages[1]["text"])

    def test_llm_mode_supports_only_mock_and_yandex_agents(self):
        old_mode = settings.LLM_MODE
        try:
            settings.LLM_MODE = "mock"
            self.assertIsInstance(get_llm_client(), MockLLMClient)
            settings.LLM_MODE = "yandex_agents"
            self.assertIsInstance(get_llm_client(), YandexAIStudioAgentsClient)
            settings.LLM_MODE = "yandex"
            with self.assertRaises(RuntimeError):
                get_llm_client()
        finally:
            settings.LLM_MODE = old_mode

    def test_yandex_agents_parser_accepts_structured_payloads(self):
        client = YandexAIStudioAgentsClient()
        questions = client._parse_question_bank(
            {
                "output_text": """
                {
                  "questions": [
                    {
                      "question_text": "Explain REST API design for backend services",
                      "level": "junior",
                      "tags": ["REST", "Backend"],
                      "expected_answer": "Candidate should explain resources, HTTP methods, statuses and stateless communication.",
                      "evaluation_criteria": ["resources and methods", "status codes and statelessness"],
                      "source_title": "AI Studio Web Search",
                      "source_url": null
                    }
                  ]
                }
                """
            }
        )
        self.assertEqual(len(questions.questions), 1)
        reply = client._parse_interviewer_reply(
            {
                "output": [
                    {
                        "content": [
                            {
                                "text": '{"message":"Уточните пример.","should_ask_follow_up":true,"covered_criteria":[],"missing_criteria":["пример"]}'
                            }
                        ]
                    }
                ]
            }
        )
        self.assertIsInstance(reply, LLMInterviewerReply)
        self.assertTrue(reply.should_ask_follow_up)
        evaluation = client._parse_evaluation(
            '{"score":80,"correctness":80,"completeness":75,"depth":70,"communication":85,"strengths":["структура"],"weaknesses":["мало примеров"],"recommendations":"Добавить примеры.","summary":"Хорошо."}'
        )
        self.assertEqual(evaluation.score, 80)

    def test_yandex_agents_parser_rejects_invalid_json(self):
        client = YandexAIStudioAgentsClient()
        with self.assertRaises(ValueError):
            client._parse_evaluation("not-json")
        with self.assertRaises(ValueError):
            client._parse_question_bank('{"question_text": "not an array"}')
        with self.assertRaises(ValueError):
            client._parse_question_bank('{"questions":[{"question_text":"short"}]}')
        with self.assertRaises(ValueError):
            client._parse_interviewer_reply(
                '{"message":"ok","should_ask_follow_up":false,"covered_criteria":[],"missing_criteria":[],"extra":"nope"}'
            )

    def test_yandex_agents_rejects_non_completed_response_status(self):
        client = YandexAIStudioAgentsClient()
        with self.assertRaises(RuntimeError):
            client._ensure_completed_response({"status": "failed", "error": {"message": "bad key"}})
        with self.assertRaises(RuntimeError):
            client._ensure_completed_response({"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}})

    def test_seed_is_idempotent_and_creates_defense_data(self):
        async def run():
            async with self.SessionLocal() as session:
                first = await seed_demo_data(session)
                second = await seed_demo_data(session)
                type_count = await session.scalar(select(func.count(InterviewType.id)))
                question_count = await session.scalar(select(func.count(Question.id)))
                hashed_question_count = await session.scalar(
                    select(func.count(Question.id)).where(Question.question_hash.is_not(None))
                )
                backend = await session.scalar(select(InterviewType).where(InterviewType.title == "Backend Java-разработчик"))
                return first, second, type_count, question_count, hashed_question_count, backend

        first, second, type_count, question_count, hashed_question_count, backend = asyncio.run(run())
        self.assertEqual(first["admin_email"], "admin@example.com")
        self.assertEqual(second["user_email"], "user@example.com")
        self.assertEqual(type_count, 2)
        self.assertEqual(question_count, 18)
        self.assertEqual(hashed_question_count, 18)
        self.assertEqual(backend.role, "Backend Java-разработчик")
