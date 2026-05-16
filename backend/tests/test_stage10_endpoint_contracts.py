import app.services.interview_engine as interview_engine_module
from app.models.chat import ChatStatus
from app.models.interview import InterviewStatus
from app.services.interview_service import interview_service
from tests.utils import ApiTestCase


class EndpointContractTest(ApiTestCase):
    def test_auth_endpoints_cover_registration_login_and_current_user(self):
        register_response = self.client.post(
            "/api/v1/auth/register",
            json={"email": "student@test", "password": "secret123", "full_name": "Student User"},
        )
        self.assertEqual(register_response.status_code, 200, register_response.text)
        self.assertEqual(register_response.json()["email"], "student@test")
        self.assertNotIn("hashed_password", register_response.json())

        duplicate_response = self.client.post(
            "/api/v1/auth/register",
            json={"email": "student@test", "password": "secret123", "full_name": "Student User"},
        )
        self.assertEqual(duplicate_response.status_code, 400)

        invalid_response = self.client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "secret123", "full_name": "Bad Email"},
        )
        self.assertEqual(invalid_response.status_code, 422)

        login_response = self.client.post(
            "/api/v1/auth/login/access-token",
            data={"username": "student@test", "password": "secret123"},
        )
        self.assertEqual(login_response.status_code, 200, login_response.text)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        alias_login_response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "student@test", "password": "secret123"},
        )
        self.assertEqual(alias_login_response.status_code, 200, alias_login_response.text)

        auth_me_response = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(auth_me_response.status_code, 200, auth_me_response.text)
        self.assertEqual(auth_me_response.json()["email"], "student@test")

        users_me_response = self.client.get("/api/v1/users/me", headers=headers)
        self.assertEqual(users_me_response.status_code, 200, users_me_response.text)
        self.assertEqual(users_me_response.json()["email"], "student@test")

        bad_login_response = self.client.post(
            "/api/v1/auth/login/access-token",
            data={"username": "student@test", "password": "wrong-password"},
        )
        self.assertEqual(bad_login_response.status_code, 400)

    def test_admin_health_endpoint(self):
        response = self.client.get("/api/v1/admin/health")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "ok")

    def test_progress_endpoint_returns_usage_summary_for_authenticated_user(self):
        headers = self.register_and_login(email="progress-contract@test")

        response = self.client.get("/api/v1/progress", headers=headers)

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["total_interviews"], 0)
        self.assertEqual(payload["completed_interviews"], 0)
        self.assertEqual(payload["daily_limit"], 20)
        self.assertEqual(payload["remaining_today"], 20)

    def test_interview_endpoints_cover_crud_messages_finish_result_and_permissions(self):
        owner_headers = self.register_and_login(email="interview-owner@test")
        other_headers = self.register_and_login(email="interview-other@test")

        create_response = self.client.post(
            "/api/v1/interviews",
            headers=owner_headers,
            json={"specialization": "Python Backend", "level": "Junior", "interview_type": "technical"},
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        interview = create_response.json()
        interview_id = interview["id"]
        self.assertEqual(interview["stage"], "intro")
        self.assertEqual(interview["status"], "active")

        list_response = self.client.get("/api/v1/interviews", headers=owner_headers)
        self.assertEqual(list_response.status_code, 200, list_response.text)
        self.assertEqual(len(list_response.json()), 1)

        read_response = self.client.get(f"/api/v1/interviews/{interview_id}", headers=owner_headers)
        self.assertEqual(read_response.status_code, 200, read_response.text)
        self.assertEqual(read_response.json()["id"], interview_id)

        forbidden_response = self.client.get(f"/api/v1/interviews/{interview_id}", headers=other_headers)
        self.assertEqual(forbidden_response.status_code, 403)

        missing_response = self.client.get("/api/v1/interviews/999999", headers=owner_headers)
        self.assertEqual(missing_response.status_code, 404)

        messages_response = self.client.get(f"/api/v1/interviews/{interview_id}/messages", headers=owner_headers)
        self.assertEqual(messages_response.status_code, 200, messages_response.text)
        self.assertEqual(messages_response.json()[0]["sender"], "ai")

        empty_message_response = self.client.post(
            f"/api/v1/interviews/{interview_id}/messages",
            headers=owner_headers,
            json={"content": ""},
        )
        self.assertEqual(empty_message_response.status_code, 422)

        turn_response = self.client.post(
            f"/api/v1/interviews/{interview_id}/messages",
            headers=owner_headers,
            json={"content": "Готов отвечать"},
        )
        self.assertEqual(turn_response.status_code, 200, turn_response.text)
        self.assertEqual(turn_response.json()["messages"][0]["sender"], "user")
        self.assertEqual(turn_response.json()["messages"][1]["sender"], "ai")

        result_before_finish_response = self.client.get(
            f"/api/v1/interviews/{interview_id}/result",
            headers=owner_headers,
        )
        self.assertEqual(result_before_finish_response.status_code, 404)

        finish_response = self.client.post(f"/api/v1/interviews/{interview_id}/finish", headers=owner_headers)
        self.assertEqual(finish_response.status_code, 200, finish_response.text)
        self.assertEqual(finish_response.json()["session"]["status"], InterviewStatus.FINISHED.value)

        result_response = self.client.get(f"/api/v1/interviews/{interview_id}/result", headers=owner_headers)
        self.assertEqual(result_response.status_code, 200, result_response.text)
        self.assertGreaterEqual(result_response.json()["score"], 0)

        late_message_response = self.client.post(
            f"/api/v1/interviews/{interview_id}/messages",
            headers=owner_headers,
            json={"content": "Поздний ответ"},
        )
        self.assertEqual(late_message_response.status_code, 400)

    def test_legacy_chat_endpoints_cover_chat_lifecycle_without_external_ai(self):
        headers = self.register_and_login(email="chat-contract@test")

        async def fake_generate_ai_response_task(*args, **kwargs):
            return None

        async def fake_analyze_interview(chat_history):
            return "Тестовая обратная связь"

        original_generate_task = interview_service.generate_ai_response_task
        original_analyze = interview_service.ai_service.analyze_interview
        interview_service.generate_ai_response_task = fake_generate_ai_response_task
        interview_service.ai_service.analyze_interview = fake_analyze_interview
        try:
            create_response = self.client.post(
                "/api/v1/chats/",
                headers=headers,
                json={"position": "Backend", "level": "Junior", "topic": "FastAPI"},
            )
            self.assertEqual(create_response.status_code, 200, create_response.text)
            chat = create_response.json()
            chat_id = chat["id"]
            self.assertEqual(chat["status"], ChatStatus.ACTIVE.value)

            list_response = self.client.get("/api/v1/chats/", headers=headers)
            self.assertEqual(list_response.status_code, 200, list_response.text)
            self.assertEqual(len(list_response.json()), 1)

            read_response = self.client.get(f"/api/v1/chats/{chat_id}", headers=headers)
            self.assertEqual(read_response.status_code, 200, read_response.text)
            self.assertEqual(len(read_response.json()["messages"]), 1)

            wait_for_ai_response = self.client.post(
                f"/api/v1/chats/{chat_id}/messages",
                headers=headers,
                json={"content": "Первый ответ"},
            )
            self.assertEqual(wait_for_ai_response.status_code, 200, wait_for_ai_response.text)
            self.assertEqual(wait_for_ai_response.json()["role"], "user")

            second_message_response = self.client.post(
                f"/api/v1/chats/{chat_id}/messages",
                headers=headers,
                json={"content": "Второй ответ без AI"},
            )
            self.assertEqual(second_message_response.status_code, 400)

            retry_response = self.client.post(f"/api/v1/chats/{chat_id}/retry", headers=headers)
            self.assertEqual(retry_response.status_code, 200, retry_response.text)
            self.assertEqual(retry_response.json()["status"], "ok")

            messages_response = self.client.get(f"/api/v1/chats/{chat_id}/messages", headers=headers)
            self.assertEqual(messages_response.status_code, 200, messages_response.text)
            self.assertEqual(len(messages_response.json()), 2)

            finish_response = self.client.post(f"/api/v1/chats/{chat_id}/finish", headers=headers)
            self.assertEqual(finish_response.status_code, 200, finish_response.text)
            self.assertEqual(finish_response.json()["status"], ChatStatus.COMPLETED.value)
            self.assertEqual(finish_response.json()["feedback"], "Тестовая обратная связь")

            completed_message_response = self.client.post(
                f"/api/v1/chats/{chat_id}/messages",
                headers=headers,
                json={"content": "После завершения"},
            )
            self.assertEqual(completed_message_response.status_code, 400)

            missing_response = self.client.get("/api/v1/chats/999999", headers=headers)
            self.assertEqual(missing_response.status_code, 404)
        finally:
            interview_service.generate_ai_response_task = original_generate_task
            interview_service.ai_service.analyze_interview = original_analyze

    def test_legacy_chat_owner_permissions(self):
        owner_headers = self.register_and_login(email="chat-owner@test")
        other_headers = self.register_and_login(email="chat-other@test")

        create_response = self.client.post(
            "/api/v1/chats/",
            headers=owner_headers,
            json={"position": "Backend", "level": "Junior"},
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        chat_id = create_response.json()["id"]

        forbidden_read = self.client.get(f"/api/v1/chats/{chat_id}", headers=other_headers)
        self.assertEqual(forbidden_read.status_code, 400)

        forbidden_messages = self.client.get(f"/api/v1/chats/{chat_id}/messages", headers=other_headers)
        self.assertEqual(forbidden_messages.status_code, 400)

    def test_interview_message_returns_system_message_when_ai_generation_fails(self):
        headers = self.register_and_login(email="ai-failure@test")
        create_response = self.client.post(
            "/api/v1/interviews",
            headers=headers,
            json={"specialization": "Python Backend", "level": "Junior", "interview_type": "full"},
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        interview_id = create_response.json()["id"]

        original_generate = interview_engine_module.llm_client.generate_stage_prompt

        async def broken_generate(*args, **kwargs):
            raise RuntimeError("AI service unavailable")

        interview_engine_module.llm_client.generate_stage_prompt = broken_generate
        try:
            response = self.client.post(
                f"/api/v1/interviews/{interview_id}/messages",
                headers=headers,
                json={"content": "Готов начать"},
            )
        finally:
            interview_engine_module.llm_client.generate_stage_prompt = original_generate

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["messages"][0]["sender"], "user")
        self.assertEqual(payload["messages"][1]["sender"], "system")
        self.assertIn("Не удалось получить ответ AI", payload["messages"][1]["content"])
