# backend/app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    All configuration loaded from .env file.
    Pydantic validates every value at startup.
    """

    APP_NAME: str = "AI Job Application Tracker"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql://postgres:admin123@localhost:5432/jobtracker"

    SECRET_KEY: str = "admin123"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()