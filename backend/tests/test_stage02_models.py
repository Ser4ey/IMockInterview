import unittest

from app.db.session import Base
from app.models.interview import (
    ExternalContextSource,
    InterviewResult,
    InterviewSession,
    Message,
    PromptTemplate,
    TariffLimit,
)


class InterviewModelTest(unittest.TestCase):
    def test_target_tables_are_registered_in_metadata(self):
        expected_tables = {
            "interview_sessions",
            "interview_messages",
            "interview_results",
            "prompt_templates",
            "external_context_sources",
            "tariff_limits",
        }
        self.assertTrue(expected_tables.issubset(set(Base.metadata.tables)))

    def test_core_models_have_required_columns(self):
        self.assertIn("stage", InterviewSession.__table__.columns)
        self.assertIn("sender", Message.__table__.columns)
        self.assertIn("recommendations", InterviewResult.__table__.columns)
        self.assertIn("system_prompt", PromptTemplate.__table__.columns)
        self.assertIn("content", ExternalContextSource.__table__.columns)
        self.assertIn("used_today", TariffLimit.__table__.columns)


if __name__ == "__main__":
    unittest.main()
