from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.base import Base


SQLITE_COLUMNS: dict[str, dict[str, str]] = {
    "users": {
        "role": "VARCHAR NOT NULL DEFAULT 'user'",
        "created_at": "DATETIME",
    },
}


async def prepare_database(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        dialect_name = conn.dialect.name
        if dialect_name != "sqlite":
            return

        for table_name, columns in SQLITE_COLUMNS.items():
            existing_columns = await conn.execute(text(f"PRAGMA table_info({table_name})"))
            existing_names = {row[1] for row in existing_columns.fetchall()}

            for column_name, column_sql in columns.items():
                if column_name not in existing_names:
                    await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"))
