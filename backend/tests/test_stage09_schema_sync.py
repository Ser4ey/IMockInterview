import asyncio
import tempfile
import unittest

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.schema_sync import prepare_database


class SchemaSyncTest(unittest.TestCase):
    def test_prepare_database_adds_missing_user_columns_to_existing_sqlite_db(self):
        db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_file.close()
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_file.name}")

        async def run_check():
            async with engine.begin() as conn:
                await conn.execute(
                    text(
                        """
                        CREATE TABLE users (
                            id INTEGER PRIMARY KEY,
                            email VARCHAR NOT NULL,
                            hashed_password VARCHAR NOT NULL,
                            is_active BOOLEAN,
                            tariff VARCHAR,
                            requests_count INTEGER,
                            full_name VARCHAR,
                            is_superuser BOOLEAN
                        )
                        """
                    )
                )

            await prepare_database(engine)

            async with engine.begin() as conn:
                result = await conn.execute(text("PRAGMA table_info(users)"))
                return {row[1] for row in result.fetchall()}

        column_names = asyncio.run(run_check())
        asyncio.run(engine.dispose())

        self.assertIn("role", column_names)
        self.assertIn("created_at", column_names)
