# backend/app/main.py

"""
Application Entry Point
========================
This file assembles the FastAPI application.

MIDDLEWARE EXECUTION ORDER
--------------------------
Middleware is added in REVERSE order of execution.
The LAST middleware added is the FIRST to run on every request.

Order we add them:         Order they actually run (outermost → innermost):
  1. SlowAPIMiddleware   →   1. RequestLoggingMiddleware   (added last, runs first)
  2. CORSMiddleware      →   2. SlowAPIMiddleware          (rate limiter)
  3. RequestLogging      →   3. CORSMiddleware             (CORS headers)
                         →   4. Router → Service → DB

This means:
  - We log EVERY request, even ones blocked by rate limiting
  - CORS is checked AFTER rate limiting
  - The actual route handler runs last

WHY LOG BEFORE RATE LIMITING?
  Logging happens first so we have a record of every request attempt,
  including the ones that get blocked. This is useful for detecting
  attack patterns even when requests are rejected.

EXCEPTION HANDLER REGISTRATION
--------------------------------
  app.add_exception_handler(ExcType, handler_fn)

  FastAPI/Starlette calls these functions when an exception of that
  type (or subtype) propagates up without being caught.

  Order matters: more specific types first.
    RequestValidationError BEFORE Exception
    HTTPException BEFORE Exception
  (Exception catches everything — if it's first, the others never fire)
"""

import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import RequestLoggingMiddleware, get_logger, setup_logging
from app.core.rate_limiter import limiter
from app.db.database import Base, engine
from app.routers import ai, auth, jobs, resumes, users

import app.models  # noqa: F401 — imports all models so SQLAlchemy registers them


# ==========================================================
# Step 1: Configure Logging
# ==========================================================
# Must be called FIRST before anything else logs.
# This sets log level, format, and silences noisy libraries.
# After this line, every `logger.info(...)` call works correctly.
# ==========================================================
setup_logging()

# Get a logger for this module specifically
logger = get_logger(__name__)


# ==========================================================
# Step 2: Create Database Tables
# ==========================================================
# Creates all tables defined in SQLAlchemy models if they don't exist.
# In production, you'd use Alembic migrations instead.
# We still do it here as a safety net for development.
# ==========================================================
Base.metadata.create_all(bind=engine)


# ==========================================================
# Step 3: Initialize FastAPI Application
# ==========================================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for AI-powered Job Application Tracking",
    # Hide /docs and /redoc in production for security
    # Set to None to disable: docs_url=None, redoc_url=None
    docs_url="/docs",
    redoc_url="/redoc",
)


# ==========================================================
# Step 4: Attach Rate Limiter to App State
# ==========================================================
# SlowAPI needs the limiter instance on app.state.limiter
# so the middleware can find it.
#
# `app.state` is FastAPI's built-in dict-like object for
# storing application-level objects that middleware can access.
# ==========================================================
app.state.limiter = limiter


# ==========================================================
# Step 5: Register Global Exception Handlers
# ==========================================================
# IMPORTANT: Register most specific exceptions FIRST.
# If you register Exception first, it catches everything
# and the more specific handlers never fire.
#
# Handler chain (most specific → least specific):
#   RequestValidationError → HTTPException → RateLimitExceeded → Exception
# ==========================================================

# 422 — Pydantic validation errors (bad request body/query params)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# 4xx/5xx — Our HTTPException helpers (not_found, forbidden, etc.)
from fastapi import HTTPException  # noqa: E402
app.add_exception_handler(HTTPException, http_exception_handler)

# 429 — Rate limit exceeded (from slowapi)
# This is slowapi's built-in handler — it returns a proper 429 JSON response
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 500 — Any unhandled Python exception (bugs, crashes, unexpected errors)
app.add_exception_handler(Exception, unhandled_exception_handler)


# ==========================================================
# Step 6: Register Middleware
# ==========================================================
# Remember: middleware runs in REVERSE ORDER of registration.
# Last added = first to execute on incoming requests.
#
# We want execution order:
#   RequestLogging → SlowAPI (rate limit) → CORS → Router
#
# So we add them in reverse:
#   1. SlowAPI (runs 2nd)
#   2. CORS    (runs 3rd)
#   3. Request Logging (added last → runs FIRST)
# ==========================================================

# Rate Limiting Middleware
# ────────────────────────────────────────────────────────────
# SlowAPIMiddleware intercepts every request, extracts the client IP,
# and checks against the configured rate limit.
# If exceeded, it raises RateLimitExceeded (caught by handler above).
app.add_middleware(SlowAPIMiddleware)

# CORS Middleware
# ────────────────────────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing
# Without this, browsers block JavaScript fetch() calls from
# http://localhost:5173 (React) to http://localhost:8000 (FastAPI)
# because they're on different ports = different "origins".
#
# settings.ALLOWED_ORIGINS comes from ALLOWED_ORIGINS in .env
# (comma-separated string, parsed into a list by the Pydantic validator)
#
# allow_credentials=True  → Required to send cookies or JWT in headers
# allow_methods=["*"]     → GET, POST, PUT, PATCH, DELETE, OPTIONS
# allow_headers=["*"]     → Authorization, Content-Type, etc.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # @property — parsed list from .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Logging Middleware
# ────────────────────────────────────────────────────────────
# Added last = runs FIRST on every request.
# Logs: → GET /jobs/ | client=192.168.1.1
# Logs: ← 200 GET /jobs/ | 45.3ms
app.add_middleware(RequestLoggingMiddleware)


# ==========================================================
# Step 7: Mount Static File Server (Resume Uploads)
# ==========================================================
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
app.mount(
    "/static",
    StaticFiles(directory=os.path.normpath(UPLOAD_DIR)),
    name="static",
)


# ==========================================================
# Step 8: Register Application Routers
# ==========================================================
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(resumes.router)
app.include_router(ai.router)


# ==========================================================
# Step 9: Startup & Shutdown Lifecycle Events
# ==========================================================
# FastAPI runs these functions at app startup and shutdown.
# Useful for: verifying connections, warming up caches,
# gracefully closing resources.
# ==========================================================

@app.on_event("startup")
async def on_startup():
    """
    Called once when the application starts.
    Logs startup configuration so you know exactly what settings are active.
    """
    logger.info("=" * 60)
    logger.info("Application starting up")
    logger.info("  App:         %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("  Environment: %s", settings.ENVIRONMENT)
    logger.info("  Debug mode:  %s", settings.DEBUG)
    logger.info("  Log level:   %s", settings.LOG_LEVEL)
    logger.info("  CORS origins: %s", settings.allowed_origins)
    logger.info("  Rate limit:  %s req/min per IP", settings.RATE_LIMIT_PER_MINUTE)
    logger.info("=" * 60)


@app.on_event("shutdown")
async def on_shutdown():
    """Called when the application shuts down (Ctrl+C or Docker stop)."""
    logger.info("Application shutting down. Goodbye.")


# ==========================================================
# Root Endpoints
# ==========================================================

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    Used by Docker Compose, Kubernetes, and load balancers
    to verify the application is running and responsive.
    Returns 200 when healthy.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }