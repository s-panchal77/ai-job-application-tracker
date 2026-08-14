# backend/tests/conftest.py

"""
conftest.py — The Heart of pytest Fixtures
============================================

What is conftest.py?
---------------------
pytest automatically discovers and imports this file before running any test.
Every fixture defined here is AUTOMATICALLY available to ALL test files in the
same directory and its subdirectories — no import needed.

Think of conftest.py as the "shared setup" file for your entire test suite.

Why do we need it?
------------------
Every test needs a clean database, a logged-in user, and a test HTTP client.
Instead of copy-pasting setup code into every test, we define it ONCE here
as fixtures and pytest injects them wherever needed.

Fixture Lifecycle (scope):
---------------------------
  scope="function"  -> Fresh setup + teardown for EVERY individual test (default)
  scope="module"    -> Setup once for all tests in one file
  scope="session"   -> Setup once for the entire pytest run

We use scope="session" for the engine (expensive to create) and
scope="function" for the database session (must be clean per test).
"""

import io
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, hash_password
from app.db.database import Base, get_db
# Import our own app modules
from app.main import app
from app.models.job import ApplicationStatus, JobApplication
from app.models.user import User

# =============================================================
# STEP 1: TESTING DATABASE URL
# =============================================================
# WHY a separate test database?
# ─────────────────────────────
# Tests CREATE, UPDATE, and DELETE real records.
# If tests run against your production database:
#   x You could delete real user data
#   x Dummy records pollute the database
#   x Tests might fail due to leftover data from previous runs
#   x Parallel CI/CD runs would corrupt each other's data
#
# We use SQLite in-memory database for tests because:
#   v No PostgreSQL server required - tests run anywhere
#   v Each test session starts with a perfectly empty database
#   v Extremely fast - entire DB lives in RAM
#   v Automatic cleanup - disappears when Python process ends
#   v Zero configuration for CI/CD pipelines
#
# "check_same_thread=False" is required for SQLite + FastAPI because
# FastAPI's dependency injection can access the session from a
# different thread than it was created in.
# =============================================================

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")


# =============================================================
# STEP 2: CREATE TEST ENGINE (session-scoped - created ONCE)
# =============================================================


@pytest.fixture(scope="session")
def test_engine():
    """
    Creates the SQLAlchemy engine pointing at the test SQLite database.
    Session-scoped: this expensive object is created exactly ONCE per
    pytest run, then reused by all tests.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,  # Set True to see SQL queries during debugging
    )

    # Create all tables in the test database
    Base.metadata.create_all(bind=engine)

    yield engine  # provide the engine to tests

    # TEARDOWN: drop all tables after ALL tests finish
    Base.metadata.drop_all(bind=engine)


# =============================================================
# STEP 3: TEST SESSION FACTORY (function-scoped - fresh per test)
# =============================================================


@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    Yields a fresh, isolated SQLAlchemy session for ONE test.

    HOW ISOLATION WORKS:
    ─────────────────────
    We wrap each test in a transaction and ROLL IT BACK at the end.
    This means:
      1. Test runs and writes records to the DB
      2. After the test: all changes are rolled back (as if they never happened)
      3. Next test starts with a perfectly clean slate

    This is MUCH faster than dropping and recreating all tables between tests.
    Rolling back a transaction is an O(1) operation; recreating tables is O(n).
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    # Open a connection and begin an outer transaction
    connection = test_engine.connect()
    transaction = connection.begin()

    # Bind the session to this specific connection
    session = TestingSessionLocal(bind=connection)

    yield session  # <- Test runs here, using this session

    # TEARDOWN: Rollback everything the test did
    session.close()
    transaction.rollback()
    connection.close()


# =============================================================
# STEP 4: DEPENDENCY OVERRIDE + TestClient
# =============================================================
#
# WHAT IS A DEPENDENCY OVERRIDE?
# ────────────────────────────────
# FastAPI's Dependency Injection system allows you to SWAP any
# dependency at runtime. This is the key pattern for testing.
#
# Normally:  route -> Depends(get_db) -> real PostgreSQL session
# In tests:  route -> Depends(get_db) -> test SQLite session  <- OVERRIDE
#
# We tell FastAPI: "For this test, whenever any route asks for get_db,
# give them my test session instead of the real one."
#
# This means our routes run EXACTLY as they do in production,
# but they talk to a safe, isolated test database.
# =============================================================


@pytest.fixture(scope="function")
def client(db_session):
    """
    Creates a FastAPI TestClient with the database dependency overridden.

    WHAT IS TestClient?
    ────────────────────
    TestClient wraps your FastAPI app and lets you make HTTP requests
    (GET, POST, etc.) WITHOUT starting a real server.

    It's powered by httpx under the hood and talks to your app
    entirely in-process (in the same Python process). This makes tests:
      v Extremely fast (no network overhead)
      v Fully isolated (no port conflicts)
      v Easy to debug (full stack traces)
    """

    def override_get_db():
        """
        This function REPLACES get_db for every test.
        Instead of creating a new PostgreSQL session, it yields
        our already-created test SQLite session.
        """
        try:
            yield db_session
        finally:
            pass  # Don't close - managed by db_session fixture above

    # Register the override
    app.dependency_overrides[get_db] = override_get_db

    # Create the test client
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client

    # CLEANUP: Remove all overrides so other test modules start fresh
    app.dependency_overrides.clear()


# =============================================================
# STEP 5: USER FIXTURES
# =============================================================


@pytest.fixture(scope="function")
def test_user(db_session):
    """
    Creates a real User record in the test database.

    WHY create a real user?
    ────────────────────────
    Many tests need an existing user:
      - Login tests need a user to authenticate
      - Job tests need a user to own the jobs
      - Resume tests need a user to own the resumes

    The password is stored in plain_password attribute
    so login tests can use the raw password.
    """
    user = User(
        email="testuser@example.com",
        hashed_password=hash_password("TestPass123!"),
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Store plain password for login tests
    user.plain_password = "TestPass123!"
    return user


@pytest.fixture(scope="function")
def second_user(db_session):
    """
    A second user - used to test AUTHORIZATION.

    Example: User A should NOT be able to delete User B's jobs.
    We test this by having User A try to access User B's resources.
    """
    user = User(
        email="seconduser@example.com",
        hashed_password=hash_password("SecondPass123!"),
        full_name="Second User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    user.plain_password = "SecondPass123!"
    return user


# =============================================================
# STEP 6: AUTH TOKEN FIXTURES
# =============================================================


@pytest.fixture(scope="function")
def auth_token(test_user):
    """
    Creates a valid JWT access token for test_user.

    WHY create tokens directly?
    ────────────────────────────
    Protected routes require 'Authorization: Bearer <token>' header.
    Instead of going through the login API in every test (slow, fragile),
    we directly call create_access_token() to forge a valid token.

    This tests token VALIDATION logic without depending on the
    login ENDPOINT working correctly. Each concern is tested independently.
    """
    token = create_access_token(data={"sub": str(test_user.id)})
    return token


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """
    Returns the Authorization header dict ready to use in requests.

    Usage:
        response = client.get("/jobs/", headers=auth_headers)
    """
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
def second_user_auth_headers(second_user):
    """Auth headers for the second user (used for authorization tests)."""
    token = create_access_token(data={"sub": str(second_user.id)})
    return {"Authorization": f"Bearer {token}"}


# =============================================================
# STEP 7: SAMPLE DATA FIXTURES
# =============================================================


@pytest.fixture(scope="function")
def sample_job(db_session, test_user):
    """
    Creates a JobApplication record owned by test_user.

    WHY pre-create a job?
    ──────────────────────
    Tests for GET, UPDATE, DELETE need an existing job record.
    Instead of creating one via the API in every test (which
    would depend on POST /jobs/ working), we create it directly
    in the database. This makes each test independent.
    """
    job = JobApplication(
        user_id=test_user.id,
        company_name="Google",
        job_title="Backend Engineer",
        job_description="Looking for Python FastAPI expert with 3+ years experience",
        location="Remote",
        status=ApplicationStatus.APPLIED,
        notes="Applied via LinkedIn",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture(scope="function")
def sample_pdf_file():
    """
    Creates an in-memory fake PDF file for upload tests.

    WHY fake a PDF?
    ────────────────
    File upload tests need a real file object. We don't need a real
    PDF - we just need bytes that look like a PDF to bypass basic
    file type checks. We use BytesIO to create an in-memory file
    without touching the filesystem.

    '%PDF-1.4' is the magic bytes at the start of every real PDF file.
    """
    pdf_content = b"%PDF-1.4 fake pdf content for testing purposes only"
    return io.BytesIO(pdf_content)


@pytest.fixture(scope="function")
def sample_text_file():
    """A non-PDF file - used to test invalid file type rejection."""
    return io.BytesIO(b"This is plain text, not a PDF")
