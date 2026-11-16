from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    SECRET_KEY: str = "super_secret_agent_network_key"

    # Database
    DATABASE_URL: str = "sqlite:///./agent_network.db"

    # Routing Engine Parameters (spec.md Section 3)
    RELEVANCE_THRESHOLD: float = 0.75
    STAGE2_TOP_K: int = 50
    STAGE1_MIN_TRUST_SCORE: float = 0.3

    # AI & Providers
    EMBEDDING_PROVIDER: str = "local"  # 'local' or 'openai'
    LLM_PROVIDER: str = "local"        # 'local' or 'openai'
    OPENAI_API_KEY: Optional[str] = None

    # Feedback Loop Parameters (spec.md Section 6.A)
    FEEDBACK_POSITIVE_ALPHA: float = 0.08
    FEEDBACK_NEGATIVE_BETA: float = 0.05

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

