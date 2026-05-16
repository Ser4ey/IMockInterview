import asyncio
import unittest

from app.models.interview import InterviewSession, InterviewStage, Message, MessageSender
from app.services.llm_client import MockLLMClient, YandexLLMClient
from app.services.prompt_builder import PromptBuilder


class LLMLayerTest(unittest.TestCase):
    def test_prompt_builder_includes_session_context_and_history(self):
        session = InterviewSession(
            id=1,
            user_id=1,
            specialization="Backend",
            level="Junior",
            interview_type="full",
            stage="technical",
        )
        history = [
            Message(session_id=1, sender=MessageSender.AI.value, content="Первый вопрос"),
            Message(session_id=1, sender=MessageSender.USER.value, content="Мой ответ"),
        ]

        messages = PromptBuilder().build_stage_messages(session, InterviewStage.TECHNICAL, history)

        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Backend", messages[1]["text"])
        self.assertIn("technical", messages[1]["text"])
        self.assertIn("Кандидат: Мой ответ", messages[1]["text"])

    def test_mock_client_returns_valid_question_and_evaluation(self):
        session = InterviewSession(
            id=1,
            user_id=1,
            specialization="Python",
            level="Middle",
            interview_type="theory",
            stage="technical",
        )
        history = [Message(session_id=1, sender=MessageSender.USER.value, content="Answer")]

        async def run_check():
            client = MockLLMClient()
            prompt = await client.generate_stage_prompt(session, InterviewStage.TECHNICAL, history)
            evaluation = await client.evaluate_interview(session, history)
            return prompt, evaluation

        prompt, evaluation = asyncio.run(run_check())

        self.assertIn("Python", prompt)
        self.assertGreaterEqual(evaluation.score, 0)
        self.assertLessEqual(evaluation.score, 100)
        self.assertTrue(evaluation.recommendations)

    def test_yandex_evaluation_parser_rejects_invalid_json(self):
        client = YandexLLMClient()

        with self.assertRaises(ValueError):
            client._parse_evaluation("not-json")
