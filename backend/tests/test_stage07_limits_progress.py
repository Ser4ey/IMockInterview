import asyncio

from app.models.interview import TariffLimit
from tests.utils import ApiTestCase


class LimitsProgressTest(ApiTestCase):
    def test_progress_includes_local_daily_limit_status(self):
        headers = self.register_and_login(email="limits-progress@example.com")

        response = self.client.get("/api/v1/progress", headers=headers)

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["daily_limit"], 20)
        self.assertEqual(payload["used_today"], 0)
        self.assertEqual(payload["remaining_today"], 20)
        self.assertIn("reset_at", payload)

    def test_message_limit_blocks_when_daily_quota_is_exhausted(self):
        headers = self.register_and_login(email="limit-block@example.com")
        me = self.client.get("/api/v1/users/me", headers=headers).json()

        async def set_exhausted_limit():
            async with self.SessionLocal() as session:
                session.add(TariffLimit(user_id=me["id"], daily_limit=1, used_today=1))
                await session.commit()

        asyncio.run(set_exhausted_limit())

        create_response = self.client.post(
            "/api/v1/interviews",
            headers=headers,
            json={
                "specialization": "Backend",
                "level": "Junior",
                "interview_type": "theory",
            },
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        interview_id = create_response.json()["id"]

        blocked_response = self.client.post(
            f"/api/v1/interviews/{interview_id}/messages",
            headers=headers,
            json={"content": "I am ready"},
        )

        self.assertEqual(blocked_response.status_code, 402)
