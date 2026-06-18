from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration class.
    All values are loaded from the .env file automatically.
    """

    # Safe Defaults (Okay to keep in code)
    APP_NAME: str = "AI Job Application Tracker"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Sensitive Secrets (NO defaults allowed -> must come from .env)
    DATABASE_URL: str
    SECRET_KEY: str

    # Modern Pydantic v2 Configuration
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore"
    )


# Singleton instance
settings = Settings()
