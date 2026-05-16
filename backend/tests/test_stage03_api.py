import asyncio

from app.core.security import get_password_hash
from app.models.user import User
from tests.utils import ApiTestCase


class ApiContractTest(ApiTestCase):
    def test_auth_me_health_and_progress_endpoints(self):
        headers = self.register_and_login()

        me_response = self.client.get("/api/v1/users/me", headers=headers)
        self.assertEqual(me_response.status_code, 200, me_response.text)
        self.assertEqual(me_response.json()["email"], "demo@example.com")

        health_response = self.client.get("/api/v1/admin/health")
        self.assertEqual(health_response.status_code, 200)
        self.assertEqual(health_response.json()["status"], "ok")

        progress_response = self.client.get("/api/v1/progress", headers=headers)
        self.assertEqual(progress_response.status_code, 200, progress_response.text)
        self.assertEqual(progress_response.json()["total_interviews"], 0)

    def test_interview_history_and_owner_access(self):
        owner_headers = self.register_and_login(email="owner@example.com")
        other_headers = self.register_and_login(email="other@example.com")

        create_response = self.client.post(
            "/api/v1/interviews",
            headers=owner_headers,
            json={
                "specialization": "Backend-разработчик",
                "level": "Junior",
                "interview_type": "full",
            },
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        interview_id = create_response.json()["id"]

        list_response = self.client.get("/api/v1/interviews", headers=owner_headers)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        messages_response = self.client.get(f"/api/v1/interviews/{interview_id}/messages", headers=owner_headers)
        self.assertEqual(messages_response.status_code, 200, messages_response.text)
        self.assertEqual(messages_response.json()[0]["sender"], "ai")

        forbidden_response = self.client.get(f"/api/v1/interviews/{interview_id}", headers=other_headers)
        self.assertEqual(forbidden_response.status_code, 403)

    def test_auth_me_does_not_fail_on_legacy_local_demo_email(self):
        async def create_legacy_user():
            async with self.SessionLocal() as session:
                session.add(
                    User(
                        email="demo@imock.local",
                        hashed_password=get_password_hash("demo12345"),
                        full_name="Legacy Demo",
                        role="user",
                        tariff="free",
                        is_active=True,
                    )
                )
                await session.commit()

        asyncio.run(create_legacy_user())

        login_response = self.client.post(
            "/api/v1/auth/login/access-token",
            data={"username": "demo@imock.local", "password": "demo12345"},
        )
        self.assertEqual(login_response.status_code, 200, login_response.text)

        me_response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
        )
        self.assertEqual(me_response.status_code, 200, me_response.text)
        self.assertEqual(me_response.json()["email"], "demo@imock.local")
