import asyncio

from sqlalchemy import func, select

from app.models.interview import InterviewType, Question, QuestionGenerationJob
from app.models.user import User
from app.services.demo_seed import seed_demo_data
from tests.utils import ApiTestCase


class ApiFlowTest(ApiTestCase):
    def make_admin(self):
        headers = self.register_and_login(email="admin-flow@example.com", full_name="Admin")

        async def promote():
            async with self.SessionLocal() as session:
                user = await session.scalar(select(User).where(User.email == "admin-flow@example.com"))
                user.role = "admin"
                user.is_superuser = True
                await session.commit()

        asyncio.run(promote())
        return headers

    def test_admin_can_create_type_generate_and_manage_questions(self):
        admin_headers = self.make_admin()
        user_headers = self.register_and_login(email="plain-user@example.com")

        denied = self.client.get("/api/v1/admin/interview-types", headers=user_headers)
        self.assertEqual(denied.status_code, 403)

        create_response = self.client.post(
            "/api/v1/admin/interview-types",
            headers=admin_headers,
            json={
                "title": "Backend Java-разработчик",
                "role": "Backend Java-разработчик",
                "technology_stack": "Java, Spring Boot, SQL",
                "description": "Тестовое описание",
                "levels": ["junior", "middle", "senior"],
                "is_active": True,
            },
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        interview_type_id = create_response.json()["id"]

        generation_response = self.client.post(
            f"/api/v1/admin/interview-types/{interview_type_id}/generate-questions",
            headers=admin_headers,
            json={"level": "junior", "requested_count": 2},
        )
        self.assertEqual(generation_response.status_code, 200, generation_response.text)
        self.assertEqual(generation_response.json()["status"], "completed")
        self.assertEqual(generation_response.json()["generated_count"], 2)
        self.assertEqual(generation_response.json()["skipped_count"], 0)
        self.assertEqual(generation_response.json()["provider"], "mock")
        self.assertFalse(generation_response.json()["context_used"])

        questions_response = self.client.get(
            f"/api/v1/admin/questions?interview_type_id={interview_type_id}&level=junior",
            headers=admin_headers,
        )
        self.assertEqual(questions_response.status_code, 200, questions_response.text)
        questions = questions_response.json()
        self.assertEqual(len(questions), 2)
        self.assertTrue(questions[0]["expected_answer"])
        self.assertTrue(questions[0]["question_hash"])
        self.assertTrue(questions[0]["source"])

        disable_response = self.client.patch(
            f"/api/v1/admin/questions/{questions[0]['id']}/disable",
            headers=admin_headers,
        )
        self.assertEqual(disable_response.status_code, 200, disable_response.text)
        self.assertFalse(disable_response.json()["is_active"])

        jobs_response = self.client.get("/api/v1/admin/question-generation-jobs", headers=admin_headers)
        self.assertEqual(jobs_response.status_code, 200, jobs_response.text)
        self.assertEqual(len(jobs_response.json()), 1)
        self.assertEqual(jobs_response.json()[0]["provider"], "mock")

    def test_user_interview_uses_question_bank_and_saves_result(self):
        async def seed():
            async with self.SessionLocal() as session:
                await seed_demo_data(session)
                interview_type = await session.scalar(select(InterviewType).where(InterviewType.title == "Backend Java-разработчик"))
                question_count = await session.scalar(select(func.count(Question.id)).where(Question.interview_type_id == interview_type.id))
                job_count = await session.scalar(select(func.count(QuestionGenerationJob.id)))
                return interview_type.id, question_count, job_count

        interview_type_id, question_count, job_count = asyncio.run(seed())
        self.assertGreaterEqual(question_count, 9)
        self.assertEqual(job_count, 0)

        login_response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "user@example.com", "password": "user123"},
        )
        self.assertEqual(login_response.status_code, 200, login_response.text)
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        types_response = self.client.get("/api/v1/interview-types", headers=headers)
        self.assertEqual(types_response.status_code, 200, types_response.text)
        self.assertGreaterEqual(types_response.json()[0]["question_counts"]["junior"], 3)

        create_response = self.client.post(
            "/api/v1/interviews",
            headers=headers,
            json={"interview_type_id": interview_type_id, "level": "junior", "question_count": 1},
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        interview = create_response.json()
        self.assertEqual(interview["interview_type_title"], "Backend Java-разработчик")
        self.assertEqual(interview["stage"], "question")
        self.assertEqual(interview["question_limit"], 1)

        messages_response = self.client.get(f"/api/v1/interviews/{interview['id']}/messages", headers=headers)
        self.assertEqual(messages_response.status_code, 200, messages_response.text)
        first_message = messages_response.json()[0]
        self.assertIn("Вопрос 1:", first_message["content"])
        self.assertIsNotNone(first_message["question_id"])

        answer_response = self.client.post(
            f"/api/v1/interviews/{interview['id']}/messages",
            headers=headers,
            json={"content": "ArrayList основан на массиве, LinkedList на связном списке, поэтому первый обычно лучше для быстрого доступа по индексу, а второй может быть полезен при частых вставках в середину при наличии ссылки на узел."},
        )
        self.assertEqual(answer_response.status_code, 200, answer_response.text)
        self.assertEqual(answer_response.json()["messages"][0]["sender"], "user")
        self.assertIsNotNone(answer_response.json()["messages"][0]["question_id"])
        self.assertEqual(answer_response.json()["session"]["status"], "finished")
        self.assertTrue(answer_response.json()["result"]["strengths"])

        finish_response = self.client.post(f"/api/v1/interviews/{interview['id']}/finish", headers=headers)
        self.assertEqual(finish_response.status_code, 200, finish_response.text)
        self.assertEqual(finish_response.json()["session"]["status"], "finished")
        self.assertTrue(finish_response.json()["result"]["strengths"])

        progress_response = self.client.get("/api/v1/progress", headers=headers)
        self.assertEqual(progress_response.status_code, 200, progress_response.text)
        self.assertGreaterEqual(progress_response.json()["completed_interviews"], 1)
        self.assertIn("technical_daily_limit", progress_response.json())
        self.assertNotIn("tar" + "iff", str(progress_response.json()).lower())

    def test_interview_cannot_start_without_active_questions(self):
        async def seed_and_disable():
            async with self.SessionLocal() as session:
                await seed_demo_data(session)
                interview_type = await session.scalar(select(InterviewType).where(InterviewType.title == "Backend Java-разработчик"))
                questions = await session.execute(
                    select(Question).where(
                        Question.interview_type_id == interview_type.id,
                        Question.level == "junior",
                    )
                )
                for question in questions.scalars().all():
                    question.is_active = False
                    session.add(question)
                await session.commit()
                return interview_type.id

        interview_type_id = asyncio.run(seed_and_disable())
        login_response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "user@example.com", "password": "user123"},
        )
        self.assertEqual(login_response.status_code, 200, login_response.text)
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        create_response = self.client.post(
            "/api/v1/interviews",
            headers=headers,
            json={"interview_type_id": interview_type_id, "level": "junior"},
        )
        self.assertEqual(create_response.status_code, 400, create_response.text)

    def test_user_cannot_read_another_users_interview(self):
        async def seed():
            async with self.SessionLocal() as session:
                await seed_demo_data(session)
                interview_type = await session.scalar(select(InterviewType).where(InterviewType.title == "Backend Java-разработчик"))
                return interview_type.id

        interview_type_id = asyncio.run(seed())
        first_headers = self.register_and_login(email="owner@example.com")
        second_headers = self.register_and_login(email="other@example.com")

        create_response = self.client.post(
            "/api/v1/interviews",
            headers=first_headers,
            json={"interview_type_id": interview_type_id, "level": "junior"},
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        session_id = create_response.json()["id"]

        forbidden_response = self.client.get(f"/api/v1/interviews/{session_id}", headers=second_headers)
        self.assertEqual(forbidden_response.status_code, 403, forbidden_response.text)
