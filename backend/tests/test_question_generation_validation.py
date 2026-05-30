import asyncio

from sqlalchemy import func, select

from app.models.interview import InterviewType, Question
from app.services.llm_client import GeneratedQuestion
from app.services.question_generation import QuestionGenerationService
from app.services.question_quality import build_question_hash, normalize_question_text
from tests.utils import ApiTestCase


class QuestionGenerationValidationTest(ApiTestCase):
    def make_question(self, text: str, level: str = "junior") -> GeneratedQuestion:
        return GeneratedQuestion(
            question_text=text,
            level=level,
            tags=["Java", "Backend"],
            expected_answer="Candidate should explain the main idea, practical trade-offs and implementation details.",
            evaluation_criteria=["explains the concept clearly", "mentions practical trade-offs"],
            source_title="Test source",
        )

    def test_question_hash_normalization_is_stable(self):
        first = build_question_hash(1, "junior", " What is REST API? ")
        second = build_question_hash(1, "JUNIOR", "what is rest api")
        self.assertEqual(first, second)
        self.assertEqual(normalize_question_text("  What is REST API?! "), "what is rest api")

    def test_generation_skips_duplicate_questions(self):
        async def run():
            async with self.SessionLocal() as session:
                interview_type = InterviewType(
                    title="Backend Java",
                    role="Backend Java",
                    technology_stack="Java, Spring",
                    description="",
                    levels='["junior"]',
                )
                session.add(interview_type)
                await session.flush()

                service = QuestionGenerationService()
                generated = [
                    self.make_question("Explain the difference between ArrayList and LinkedList in Java?"),
                    self.make_question(" explain the difference between arraylist and linkedlist in java "),
                ]
                saved = await service._save_generated_questions(session, interview_type, "junior", generated)
                await session.commit()
                question_count = await session.scalar(select(func.count(Question.id)))
                question = await session.scalar(select(Question))
                return saved, question_count, question

        saved, question_count, question = asyncio.run(run())
        self.assertEqual(saved, 1)
        self.assertEqual(question_count, 1)
        self.assertTrue(question.question_hash)

    def test_generation_skips_wrong_level_questions(self):
        async def run():
            async with self.SessionLocal() as session:
                interview_type = InterviewType(
                    title="Backend Java",
                    role="Backend Java",
                    technology_stack="Java, Spring",
                    description="",
                    levels='["junior"]',
                )
                session.add(interview_type)
                await session.flush()

                service = QuestionGenerationService()
                generated = [self.make_question("How would you design a resilient order service?", level="senior")]
                saved = await service._save_generated_questions(session, interview_type, "junior", generated)
                await session.commit()
                question_count = await session.scalar(select(func.count(Question.id)))
                return saved, question_count

        saved, question_count = asyncio.run(run())
        self.assertEqual(saved, 0)
        self.assertEqual(question_count, 0)
