import unittest

from app.core.config import settings


class FoundationTest(unittest.TestCase):
    def test_default_local_settings_are_safe_for_development(self):
        self.assertEqual(settings.API_V1_STR, "/api/v1")
        self.assertTrue(settings.DATABASE_URL.startswith("sqlite+aiosqlite:///"))
        self.assertTrue(settings.SECRET_KEY)


if __name__ == "__main__":
    unittest.main()
