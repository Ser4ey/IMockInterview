from tests.utils import ApiTestCase


class InterviewEngineTest(ApiTestCase):
    def test_full_interview_moves_through_all_managed_stages(self):
        headers = self.register_and_login(email="engine@example.com")
        create_response = self.client.post(
            "/api/v1/interviews",
            headers=headers,
            json={
                "specialization": "Backend developer",
                "level": "Junior",
                "interview_type": "full",
            },
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        interview_id = create_response.json()["id"]
        self.assertEqual(create_response.json()["stage"], "intro")

        expected_stages = [
            "self_presentation",
            "technical",
            "practice",
            "soft_skills",
            "feedback",
            "finished",
        ]
        payload = None
        for expected_stage in expected_stages:
            response = self.client.post(
                f"/api/v1/interviews/{interview_id}/messages",
                headers=headers,
                json={"content": f"Answer for {expected_stage}"},
            )
            self.assertEqual(response.status_code, 200, response.text)
            payload = response.json()
            self.assertEqual(payload["session"]["stage"], expected_stage)
            self.assertEqual(payload["messages"][0]["sender"], "user")
            self.assertEqual(payload["messages"][1]["sender"], "ai")

        self.assertIsNotNone(payload)
        self.assertEqual(payload["session"]["status"], "finished")
        self.assertIsNotNone(payload["result"])
        self.assertGreater(payload["result"]["score"], 0)

        rejected_response = self.client.post(
            f"/api/v1/interviews/{interview_id}/messages",
            headers=headers,
            json={"content": "Late answer"},
        )
        self.assertEqual(rejected_response.status_code, 400)

    def test_theory_interview_uses_shorter_stage_flow(self):
        headers = self.register_and_login(email="theory@example.com")
        create_response = self.client.post(
            "/api/v1/interviews",
            headers=headers,
            json={
                "specialization": "Python",
                "level": "Middle",
                "interview_type": "theory",
            },
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        interview_id = create_response.json()["id"]

        stages = []
        for answer in ["ready", "technical answer", "final note"]:
            response = self.client.post(
                f"/api/v1/interviews/{interview_id}/messages",
                headers=headers,
                json={"content": answer},
            )
            self.assertEqual(response.status_code, 200, response.text)
            stages.append(response.json()["session"]["stage"])

        self.assertEqual(stages, ["technical", "feedback", "finished"])

    def test_finish_endpoint_creates_result_for_active_interview(self):
        headers = self.register_and_login(email="finish@example.com")
        create_response = self.client.post(
            "/api/v1/interviews",
            headers=headers,
            json={
                "specialization": "Frontend",
                "level": "Junior",
                "interview_type": "self_presentation",
            },
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        interview_id = create_response.json()["id"]

        finish_response = self.client.post(f"/api/v1/interviews/{interview_id}/finish", headers=headers)
        self.assertEqual(finish_response.status_code, 200, finish_response.text)
        self.assertEqual(finish_response.json()["session"]["stage"], "finished")
        self.assertEqual(finish_response.json()["session"]["status"], "finished")
        self.assertIsNotNone(finish_response.json()["result"])
