# backend/app/core/logging.py

"""
Structured Logging Configuration
=================================

WHY THIS FILE EXISTS
---------------------
Python has a built-in `logging` module, but it needs to be configured
before it does anything useful. Without this file:

  - There are no timestamps on log messages
  - You can't filter by severity (DEBUG vs ERROR)
  - You don't know which module the log came from
  - You can't route logs to files, Datadog, or CloudWatch

This file does 3 things:
  1. Configures the root logger once for the whole application
  2. Sets the log level from settings (so it's different in dev/prod)
  3. Exports a `setup_logging()` function called on app startup
  4. Exports `get_logger()` so every module gets a named logger

LOG FORMAT EXPLAINED
---------------------
  2026-08-12 16:30:00,123 | INFO     | app.routers.jobs | message here
  └── timestamp ─────────┘ └─ level ┘ └── module name ──┘ └── message ─┘

WHY NAMED LOGGERS (`get_logger(__name__)`)?
---------------------------------------------
  logger = get_logger(__name__)

  `__name__` is Python's automatic module identifier.
  In `app/routers/jobs.py` it becomes "app.routers.jobs".
  This tells you exactly which file produced the log — without guessing.

REQUEST LOGGING MIDDLEWARE
---------------------------
  The `RequestLoggingMiddleware` class wraps every HTTP request:
    → Logs when the request ARRIVES (method + path)
    ← Logs when the response LEAVES (status code + duration in ms)

  This answers: "Was this endpoint hit? How fast did it respond?"
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import settings

# ==========================================================
# Log Format
# ==========================================================
# %(asctime)s        → "2026-08-12 16:30:00,123" — when it happened
# %(levelname)-8s    → "INFO    " padded to 8 chars — severity
# %(name)s           → "app.routers.jobs" — which module logged it
# %(message)s        → the actual log message
# ==========================================================
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    """
    Configure the root Python logger for the entire application.

    Called ONCE on app startup in main.py.

    Why call it only once?
    If you call basicConfig() in multiple files, Python creates multiple
    handlers. This causes every log message to print multiple times.
    One central setup, called once — clean and correct.
    """

    # Convert string "DEBUG" / "INFO" / "WARNING" to Python's int constants
    # logging.getLevelName("DEBUG") returns 10
    # logging.getLevelName("INFO")  returns 20
    log_level = logging.getLevelName(settings.LOG_LEVEL.upper())

    # ── Silence noisy libraries BEFORE basicConfig ────────────────
    # These must be set before basicConfig so propagation doesn't
    # override them. We don't want SQLAlchemy SQL queries or uvicorn
    # access logs buried in our application logs.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.basicConfig(
        level=log_level,  # Minimum level to record
        format=LOG_FORMAT,  # How each line looks
        datefmt=DATE_FORMAT,  # How the timestamp looks
    )

    # Get the root app logger to confirm startup
    logger = get_logger(__name__)
    logger.info(
        "Logging configured | environment=%s | level=%s",
        settings.ENVIRONMENT,
        settings.LOG_LEVEL.upper(),
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger for any module in the application.

    Usage in any file:
        from app.core.logging import get_logger
        logger = get_logger(__name__)

        logger.info("User created: user_id=%s", user.id)
        logger.warning("Attempt to access forbidden resource")
        logger.error("Database connection failed: %s", str(e))

    `__name__` = the Python module path, e.g. "app.routers.jobs"
    This appears in every log line so you know exactly where it came from.
    """
    return logging.getLogger(name)


# ==========================================================
# Request Logging Middleware
# ==========================================================


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every incoming HTTP request and its response.

    WHY MIDDLEWARE?
    Middleware wraps EVERY request — you don't need to add logging
    to each router individually. One class handles all routes.

    WHAT IT LOGS:
      → Incoming:  "→ GET /jobs/ | client=192.168.1.1"
      ← Outgoing:  "← 200 GET /jobs/ | 45ms"

    This answers two critical production questions:
      1. Which endpoints are being hit and by whom?
      2. Which endpoints are slow and need optimization?

    HOW STARLETTE MIDDLEWARE WORKS:
      `async def dispatch(self, request, call_next)` is called for
      every request. `call_next(request)` calls the next layer
      (router → service → database → back). Everything BEFORE
      call_next runs on the way IN. Everything AFTER runs on the way OUT.
    """

    def __init__(self, app):
        super().__init__(app)
        # Use a dedicated logger named "app.middleware.request"
        self.logger = get_logger("app.middleware.request")

    async def dispatch(self, request: Request, call_next):
        # ── INCOMING ──────────────────────────────────────────
        # Record the exact time the request arrived
        start_time = time.perf_counter()

        # Extract client IP — check X-Forwarded-For first (reverse proxy)
        client_ip = request.headers.get(
            "x-forwarded-for", request.client.host if request.client else "unknown"
        )

        self.logger.info(
            "→ %s %s | client=%s",
            request.method,  # GET, POST, PATCH, DELETE
            request.url.path,  # /jobs/, /auth/login
            client_ip,  # 192.168.1.1 or "unknown"
        )

        # ── ROUTE HANDLER RUNS HERE ───────────────────────────
        response = await call_next(request)

        # ── OUTGOING ──────────────────────────────────────────
        # Calculate how long the whole request took
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Choose log level based on status code
        # 4xx/5xx errors are logged as WARNING/ERROR for easy filtering
        if response.status_code >= 500:
            log_fn = self.logger.error
        elif response.status_code >= 400:
            log_fn = self.logger.warning
        else:
            log_fn = self.logger.info

        log_fn(
            "← %s %s %s | %.1fms",
            response.status_code,  # 200, 201, 404, 500
            request.method,  # GET, POST
            request.url.path,  # /jobs/
            duration_ms,  # 45.3
        )

        return response
