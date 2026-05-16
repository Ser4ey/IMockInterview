import asyncio
import tempfile
import unittest

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api import deps
from app.db.base import Base
from app.main import app


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self._db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._db_file.close()
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{self._db_file.name}")
        self.SessionLocal = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

        async def prepare_database():
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        asyncio.run(prepare_database())

        async def override_get_db():
            async with self.SessionLocal() as session:
                yield session

        app.dependency_overrides[deps.get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()

        async def close_engine():
            await self.engine.dispose()

        asyncio.run(close_engine())

    def register_and_login(self, email="demo@example.com", password="secret123", full_name="Demo User"):
        register_response = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )
        self.assertEqual(register_response.status_code, 200, register_response.text)
        login_response = self.client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )
        self.assertEqual(login_response.status_code, 200, login_response.text)
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
