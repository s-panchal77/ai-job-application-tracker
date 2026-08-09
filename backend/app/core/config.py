# backend/app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    All configuration loaded from .env file.
    Pydantic validates every value at startup.
    """

    # ==========================================================
    # Application
    # ==========================================================
    APP_NAME: str = "AI Job Application Tracker"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ==========================================================
    # Database
    # ==========================================================
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/jobtracker"

    # ==========================================================
    # JWT Authentication
    # ==========================================================
    SECRET_KEY: str = "jobtracker_backend_secret_key_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


    # ==========================================================
    # ─── AI Integration Settings ──────────────────────────────
    # AI_PROVIDER decides which AI logic runs. Only two valid values:
    #
    #   "mock"   → free, instant, keyword-based fake analysis (default)
    #   "gemini" → real analysis via Google Gemini REST API
    # ==========================================================
    AI_PROVIDER: str = "mock"

    # ==========================================================
    # Google Gemini
    # ==========================================================
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()