from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "IMock"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: str = (
        "http://localhost:5173,"
        "http://localhost:5174,"
        "http://localhost:15190,"
        "http://127.0.0.1:5173,"
        "http://127.0.0.1:5174,"
        "http://127.0.0.1:15190"
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./imock.db"
    
    # Security
    SECRET_KEY: str = "changeme_in_production_please_secret_key_for_jwt"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""
    ADMIN_FULL_NAME: str = "Администратор IMock"
    
    # LLM / Yandex AI Studio Agents
    LLM_MODE: str = "mock"
    YANDEX_FOLDER_ID: str = ""
    YANDEX_API_KEY: str = ""
    YANDEX_AI_STUDIO_BASE_URL: str = "https://ai.api.cloud.yandex.net/v1"
    YANDEX_QUESTION_AGENT_MODEL: str = ""
    YANDEX_INTERVIEW_AGENT_MODEL: str = ""
    YANDEX_REVIEW_AGENT_MODEL: str = ""
    YANDEX_AGENTS_TIMEOUT_SECONDS: float = 60.0
    YANDEX_AGENT_STORE_RESPONSES: bool = False

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

settings = Settings()
