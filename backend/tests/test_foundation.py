from app.api.api import api_router
from app.models.interview import InterviewType, Question, QuestionGenerationJob, QuestionSource
from tests.utils import ApiTestCase


class FoundationTest(ApiTestCase):
    def test_question_bank_models_exist(self):
        tables = {table.name for table in InterviewType.metadata.sorted_tables}
        self.assertIn("interview_types", tables)
        self.assertIn("questions", tables)
        self.assertIn("question_sources", tables)
        self.assertIn("question_generation_jobs", tables)
        self.assertIn("question_text", Question.__table__.columns)
        self.assertIn("question_hash", Question.__table__.columns)
        self.assertIn("requested_count", QuestionGenerationJob.__table__.columns)
        self.assertIn("skipped_count", QuestionGenerationJob.__table__.columns)
        self.assertIn("provider", QuestionGenerationJob.__table__.columns)
        self.assertIn("context_used", QuestionGenerationJob.__table__.columns)
        self.assertIn("source_type", QuestionSource.__table__.columns)

    def test_legacy_dialog_router_is_removed(self):
        paths = {route.path for route in api_router.routes}
        removed_prefix = "/cha" + "ts"
        self.assertNotIn(f"{removed_prefix}/", paths)
        self.assertFalse(any(path.startswith(removed_prefix) for path in paths))
