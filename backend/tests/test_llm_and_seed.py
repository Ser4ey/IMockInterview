import asyncio

from sqlalchemy import func, select

from app.models.interview import InterviewType, Question
from app.services.demo_seed import seed_demo_data
from app.services.external_context import MockExternalContextProvider
from app.services.llm_client import MockLLMClient, YandexLLMClient
from app.services.prompt_builder import PromptBuilder
from tests.utils import ApiTestCase


class LLMAndSeedTest(ApiTestCase):
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

    def test_mock_external_context_returns_sources_for_question_generation(self):
        interview_type = InterviewType(
            title="Backend Java-разработчик",
            role="Backend Java-разработчик",
            technology_stack="Java, Spring",
            description="",
        )

        async def run():
            return await MockExternalContextProvider().collect(interview_type, "junior", 2)

        sources = asyncio.run(run())
        self.assertEqual(len(sources), 1)
        self.assertIn("Java", sources[0].snippet)
        self.assertEqual(sources[0].source_type, "mock_context")

    def test_yandex_parser_rejects_invalid_json(self):
        client = YandexLLMClient()
        with self.assertRaises(ValueError):
            client._parse_evaluation("not-json")
        with self.assertRaises(ValueError):
            client._parse_generated_questions('{"question_text": "not an array"}')
        with self.assertRaises(ValueError):
            client._parse_generated_questions('[{"question_text": "short"}]')

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
