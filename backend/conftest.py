# backend/conftest.py  (ROOT-LEVEL — sits next to pytest.ini, not inside tests/)

"""
Root conftest.py — Environment Setup BEFORE App Import
========================================================

WHY this file exists at the ROOT (backend/) level, not inside tests/:
──────────────────────────────────────────────────────────────────────
The core problem we're solving:

  app/main.py line 87:
      Base.metadata.create_all(bind=engine)

  This runs at MODULE IMPORT TIME.
  When pytest imports conftest.py → which imports app.main →
  which imports database.py → which calls create_engine(settings.DATABASE_URL)
  → which immediately tries to connect to PostgreSQL → BOOM!

  We need to override DATABASE_URL to SQLite BEFORE any app code is imported.
  Root-level conftest.py is loaded by pytest FIRST, even before test/ conftest.py.

SOLUTION:
  Set environment variables here, then the app's Settings will pick up
  the test values when pydantic-settings reads them.

HOW IT WORKS:
  1. pytest starts
  2. Loads backend/conftest.py (this file) FIRST
  3. os.environ is patched with test values
  4. Then loads tests/conftest.py
  5. Then loads test files
  6. app.main is imported — reads patched env vars → uses SQLite

This is the standard pattern used in production FastAPI projects.
"""

import os

# =============================================================
# OVERRIDE ENVIRONMENT VARIABLES FOR TESTING
# Must be done BEFORE any app module is imported.
# =============================================================

# Point the app at SQLite instead of PostgreSQL
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

# Disable SQLAlchemy echo during tests (cleaner output)
os.environ["DEBUG"] = "False"

# Use test environment label
os.environ["ENVIRONMENT"] = "testing"

# Use a fixed, known secret key for JWT during tests
# This ensures tokens created in tests are valid within the same run.
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_only_not_for_production"

# Disable AI calls (use mock provider only)
os.environ["AI_PROVIDER"] = "mock"

# Suppress rate limiting during tests (every request goes through)
os.environ["RATE_LIMIT_PER_MINUTE"] = "10000"
