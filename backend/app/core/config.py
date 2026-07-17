# backend/app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    All configuration loaded from .env file.
    """

    APP_NAME: str = "AI Job Application Tracker"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/jobtracker"

    SECRET_KEY: str = "your-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── AI Integration Settings (NEW) ────────────────────────
    # "mock" = use fake local logic, no external API calls, free, instant
    # "openai" = call the real OpenAI API — requires OPENAI_API_KEY
    #
    # This single setting is what lets us swap providers without
    # touching any route or service code.
    AI_PROVIDER: str = "mock"

    OPENAI_API_KEY: str = ""                  # Only required if AI_PROVIDER=openai
    OPENAI_MODEL: str = "gpt-4o-mini"          # Cheap, fast model — good default
    OPENAI_API_URL: str = "https://api.openai.com/v1/chat/completions"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()