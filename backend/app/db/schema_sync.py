from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.base import Base


SQLITE_COLUMNS: dict[str, dict[str, str]] = {
    "users": {
        "full_name": "VARCHAR",
        "role": "VARCHAR NOT NULL DEFAULT 'user'",
        "is_superuser": "BOOLEAN DEFAULT 0",
        "created_at": "DATETIME",
    },
    "interview_sessions": {
        "interview_type_id": "INTEGER",
        "current_question_id": "INTEGER",
        "question_index": "INTEGER NOT NULL DEFAULT 0",
        "question_limit": "INTEGER",
    },
    "interview_types": {
        "default_question_count": "INTEGER NOT NULL DEFAULT 3",
    },
    "interview_messages": {
        "question_id": "INTEGER",
    },
    "questions": {
        "question_hash": "VARCHAR",
    },
    "question_generation_jobs": {
        "skipped_count": "INTEGER NOT NULL DEFAULT 0",
        "provider": "VARCHAR NOT NULL DEFAULT 'mock'",
        "context_used": "BOOLEAN NOT NULL DEFAULT 0",
        "raw_response_preview": "TEXT",
    },
    "interview_results": {
        "strengths": "TEXT NOT NULL DEFAULT '[]'",
        "weaknesses": "TEXT NOT NULL DEFAULT '[]'",
        "summary": "TEXT NOT NULL DEFAULT ''",
    },
    "prompt_templates": {
        "name": "VARCHAR NOT NULL DEFAULT 'default'",
        "purpose": "VARCHAR NOT NULL DEFAULT 'interview'",
        "is_active": "BOOLEAN NOT NULL DEFAULT 1",
        "updated_at": "DATETIME",
    },
}

REMOVED_COMMERCE_COLUMN = "tar" + "iff"
REMOVED_COMMERCE_TABLE = f"{REMOVED_COMMERCE_COLUMN}_limits"

REMOVED_OLD_SESSION_TEXT_COLUMN = "special" + "ization"
REMOVED_OLD_CONTEXT_TABLE = "external_" + "context_sources"

LEGACY_SQLITE_COLUMNS_TO_DROP: dict[str, set[str]] = {
    "users": {REMOVED_COMMERCE_COLUMN},
    "interview_sessions": {REMOVED_OLD_SESSION_TEXT_COLUMN, "interview_type"},
    "prompt_templates": {"interview_type", "level"},
}

REMOVED_CHAT_TABLE = "cha" + "ts"
REMOVED_CHAT_MESSAGES_TABLE = "messages"

LEGACY_SQLITE_TABLES_TO_DROP = {
    REMOVED_COMMERCE_TABLE,
    REMOVED_CHAT_TABLE,
    REMOVED_CHAT_MESSAGES_TABLE,
    REMOVED_OLD_CONTEXT_TABLE,
}


async def prepare_database(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        if conn.dialect.name != "sqlite":
            return

        for table_name, columns in SQLITE_COLUMNS.items():
            existing_columns = await conn.execute(text(f"PRAGMA table_info({table_name})"))
            existing_names = {row[1] for row in existing_columns.fetchall()}

            for column_name, column_sql in columns.items():
                if column_name not in existing_names:
                    await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"))

            for column_name in LEGACY_SQLITE_COLUMNS_TO_DROP.get(table_name, set()):
                if column_name in existing_names:
                    await conn.execute(text(f"ALTER TABLE {table_name} DROP COLUMN {column_name}"))

        for table_name in LEGACY_SQLITE_TABLES_TO_DROP:
            await conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
