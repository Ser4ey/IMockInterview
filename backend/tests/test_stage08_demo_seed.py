import asyncio

from sqlalchemy import func, select

from app.core.security import get_password_hash
from app.models.interview import ExternalContextSource, InterviewResult, InterviewSession, PromptTemplate
from app.models.user import User
from app.services.demo_seed import DEMO_EMAIL, LEGACY_DEMO_EMAIL, seed_demo_data
from tests.utils import ApiTestCase


class DemoSeedTest(ApiTestCase):
    def test_demo_seed_is_idempotent_and_creates_showcase_data(self):
        async def run_seed_twice():
            async with self.SessionLocal() as session:
                first = await seed_demo_data(session)
                second = await seed_demo_data(session)
                user_count = await session.scalar(select(func.count(User.id)).where(User.email == DEMO_EMAIL))
                interview_count = await session.scalar(select(func.count(InterviewSession.id)))
                result_count = await session.scalar(select(func.count(InterviewResult.id)))
                prompt_count = await session.scalar(select(func.count(PromptTemplate.id)))
                source_count = await session.scalar(select(func.count(ExternalContextSource.id)))
                demo_user = await session.scalar(select(User).where(User.email == DEMO_EMAIL))
                return first, second, user_count, interview_count, result_count, prompt_count, source_count, demo_user

        first, second, user_count, interview_count, result_count, prompt_count, source_count, demo_user = asyncio.run(
            run_seed_twice()
        )

        self.assertEqual(first["email"], DEMO_EMAIL)
        self.assertEqual(first["interview_id"], second["interview_id"])
        self.assertEqual(demo_user.full_name, "Александр Петров")
        self.assertEqual(user_count, 1)
        self.assertEqual(interview_count, 4)
        self.assertEqual(result_count, 3)
        self.assertGreaterEqual(prompt_count, 1)
        self.assertGreaterEqual(source_count, 1)

    def test_demo_seed_migrates_legacy_local_email(self):
        async def run_seed_with_legacy_user():
            async with self.SessionLocal() as session:
                session.add(
                    User(
                        email=LEGACY_DEMO_EMAIL,
                        hashed_password=get_password_hash("demo12345"),
                        full_name="Legacy Demo",
                        role="user",
                        tariff="free",
                        is_active=True,
                    )
                )
                await session.commit()

                result = await seed_demo_data(session)
                legacy_count = await session.scalar(select(func.count(User.id)).where(User.email == LEGACY_DEMO_EMAIL))
                migrated_count = await session.scalar(select(func.count(User.id)).where(User.email == DEMO_EMAIL))
                return result, legacy_count, migrated_count

        result, legacy_count, migrated_count = asyncio.run(run_seed_with_legacy_user())

        self.assertEqual(result["email"], DEMO_EMAIL)
        self.assertEqual(legacy_count, 0)
        self.assertEqual(migrated_count, 1)
