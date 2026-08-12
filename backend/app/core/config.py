# backend/app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    All configuration loaded from .env file.
    Pydantic validates every value at startup.

    ENVIRONMENT rules:
      "development" → DEBUG logs, relaxed CORS, verbose errors
      "production"  → INFO logs, strict CORS, sanitized errors
    """

    # ==========================================================
    # Application
    # ==========================================================
    APP_NAME: str = "AI Job Application Tracker"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ──────────────────────────────────────────────────────────
    # ENVIRONMENT
    # Controls log verbosity, error detail, and feature flags.
    # Values: "development" | "production"
    # ──────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"

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
    # CORS (Cross-Origin Resource Sharing)
    # ──────────────────────────────────────────────────────────
    # Stored as a plain string so pydantic-settings does NOT try to
    # JSON-decode it. The @property below parses it on access.
    #
    # In .env:   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
    # At runtime: settings.allowed_origins → ["http://localhost:3000", ...]
    #
    # WHY NOT list[str] directly?
    # pydantic-settings 2.x intercepts list fields from .env and tries
    # to JSON-parse them (expects ["...","..."]). A bare comma-separated
    # string fails that JSON decode. Using str + @property bypasses this.
    # ==========================================================
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def allowed_origins(self) -> list[str]:
        """
        Parses ALLOWED_ORIGINS string into a Python list.

        Example:
            "http://localhost:3000,http://localhost:5173"
            → ["http://localhost:3000", "http://localhost:5173"]

        Use `settings.allowed_origins` (lowercase) everywhere in code.
        """
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    # ==========================================================
    # Logging
    # ──────────────────────────────────────────────────────────
    # LOG_LEVEL controls how verbose the application logs are:
    #   DEBUG    → every request detail (development)
    #   INFO     → normal operation info (production)
    #   WARNING  → only problems (high-traffic production)
    # ==========================================================
    LOG_LEVEL: str = "DEBUG"

    # ==========================================================
    # Rate Limiting
    # ──────────────────────────────────────────────────────────
    # RATE_LIMIT_PER_MINUTE: max requests per IP per 60 seconds.
    # Prevents brute-force, DoS, and abuse.
    #
    # Example: 60 = 1 request per second average.
    # Set higher in development so you can test freely.
    # ==========================================================
    RATE_LIMIT_PER_MINUTE: int = 60

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