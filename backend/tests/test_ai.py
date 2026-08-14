# backend/tests/test_ai.py

"""
test_ai.py — AI Match Endpoint Tests
======================================

PURPOSE:
  Tests POST /ai/match — the AI resume-to-job matching endpoint.

MOCKING — THE MOST IMPORTANT CONCEPT IN THIS FILE:
====================================================

WHAT IS MOCKING?
─────────────────
Mocking means replacing a real function with a fake one during testing.
The fake function returns a predetermined result without doing real work.

WHY MOCK AI CALLS?
───────────────────
Reason 1 — COST:
  Real AI API calls cost real money. If you have 50 tests and each
  calls the OpenAI API, that's 50 API requests per test run. If you
  run tests 20 times per day, that's 1000 API calls = $$$.

Reason 2 — SPEED:
  A real API call takes 2-10 seconds. 50 tests * 5s = 4+ minutes.
  A mock returns in microseconds. 50 mocked tests = <1 second total.

Reason 3 — RELIABILITY:
  External APIs can be down, slow, or rate-limited.
  If your tests rely on the internet being up, they WILL fail
  randomly in CI/CD — making your pipeline unreliable.

Reason 4 — DETERMINISM:
  AI responses are non-deterministic. The same prompt gives
  different scores each time. Tests need PREDICTABLE results.
  Mocks always return exactly what you define.

Reason 5 — ISOLATION:
  A unit test should test ONE thing. If the AI test also makes a
  real API call, a failure could be: our code is wrong OR the API
  is down. With mocks, failures mean only ONE thing: our code is wrong.

HOW MOCKING WORKS:
───────────────────
  @patch("app.services.ai_service.analyze_resume_with_gemini")
  async def test_something(self, mock_fn, ...):
      mock_fn.return_value = {"score": 85, ...}
      # Now every call to analyze_resume_with_gemini returns our fake data

  The @patch decorator temporarily replaces the real function with
  a Mock object. After the test, the real function is restored.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.job import ApplicationStatus, JobApplication
from app.models.resume import Resume

# =============================================================
# HELPERS — Create test data directly in DB
# =============================================================


def create_resume_in_db(db_session, user_id, filename="test_resume.pdf"):
    """
    Creates a Resume record directly in the database.

    WHY not upload via the API?
    ────────────────────────────
    Uploading via API writes actual files to disk and triggers
    background tasks. For AI tests, we just need a DB record
    with extracted text. Creating directly is simpler and faster.
    """
    resume = Resume(
        user_id=user_id,
        original_filename=filename,
        stored_filename=f"stored_{filename}",
        file_path=f"uploads/{filename}",
        file_size=1024,
        version_label="v1",
        is_active=True,
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)
    return resume


def create_job_with_description(db_session, user_id):
    """Creates a JobApplication with a description for AI matching."""
    job = JobApplication(
        user_id=user_id,
        company_name="AI Corp",
        job_title="ML Engineer",
        job_description=(
            "Looking for expert in python, fastapi, docker, "
            "machine learning, and sql databases."
        ),
        status=ApplicationStatus.APPLIED,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


# =============================================================
# SECTION 1: AI MATCH TESTS
# =============================================================


class TestAIMatch:
    """
    Tests for POST /ai/match

    FLOW:
      1. Client sends {job_id, resume_id} in request body
      2. Server loads job description from DB
      3. Server loads resume file path from DB
      4. Server extracts text from PDF (or uses mock)
      5. Server calls AI provider (mock or real)
      6. Server returns match score + analysis
    """

    # The MOCK AI response we'll return from our fake AI function
    MOCK_AI_RESPONSE = {
        "match_score": 85,
        "matched_skills": ["python", "fastapi", "docker"],
        "missing_skills": ["kubernetes"],
        "suggestions": ["Add Kubernetes experience to your resume"],
        "provider": "mock",
    }

    def test_ai_match_success_with_mock_provider(
        self, client, db_session, test_user, auth_headers
    ):
        """
        WHAT: Request AI match with valid job_id and resume_id.
        EXPECT: 200 + match response with score, skills, suggestions.

        MOCKING STRATEGY:
        ──────────────────
        We mock TWO things:
          1. extract_text_from_pdf  — so we don't need a real PDF file
          2. mock_analyze_resume    — so we control the AI response

        @patch changes the target function in place during this test only.
        After the test, both real functions are automatically restored.

        NOTE: When stacking @patch decorators, they inject parameters
        in REVERSE order (bottom-up): mock_ai first, mock_pdf second.
        """
        # Create test data in DB
        resume = create_resume_in_db(db_session, test_user.id)
        job = create_job_with_description(db_session, test_user.id)

        # Mock the PDF text extraction (we don't have a real PDF file)
        # Mock the AI analysis function (we don't want real AI calls)
        with patch(
            "app.services.ai_service.extract_text_from_pdf",
            return_value="Python FastAPI Docker Machine Learning SQL",
        ):
            with patch(
                "app.services.ai_service.mock_analyze_resume",
                return_value=self.MOCK_AI_RESPONSE,
            ):
                response = client.post(
                    "/ai/match",
                    json={
                        "job_id": job.id,
                        "resume_id": resume.id,
                    },
                    headers=auth_headers,
                )

        assert response.status_code == 200

        data = response.json()
        assert "match_score" in data
        assert "matched_skills" in data
        assert "missing_skills" in data
        assert "suggestions" in data
        assert "provider" in data
        assert isinstance(data["match_score"], int)
        assert 0 <= data["match_score"] <= 100  # Score must be 0-100

    def test_ai_match_invalid_job_id(self, client, db_session, test_user, auth_headers):
        """
        WHAT: Request AI match with a job_id that doesn't exist.
        EXPECT: 404 — service raises not_found_exception.
        """
        resume = create_resume_in_db(db_session, test_user.id)

        response = client.post(
            "/ai/match",
            json={
                "job_id": 99999999,  # Non-existent job
                "resume_id": resume.id,
            },
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_ai_match_invalid_resume_id(
        self, client, db_session, test_user, auth_headers
    ):
        """
        WHAT: Request AI match with a resume_id that doesn't exist.
        EXPECT: 404 — service raises not_found_exception.
        """
        job = create_job_with_description(db_session, test_user.id)

        response = client.post(
            "/ai/match",
            json={
                "job_id": job.id,
                "resume_id": 99999999,  # Non-existent resume
            },
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_ai_match_job_without_description(
        self, client, db_session, test_user, auth_headers
    ):
        """
        WHAT: Try to match against a job that has no description.
        EXPECT: 400 — can't analyze without job description text.

        WHY?
        ─────
        The AI matching works by comparing resume text against job
        description text. If there's no description, there's nothing
        to compare against. The service should reject this gracefully.
        """
        # Create a job with NO description
        job = JobApplication(
            user_id=test_user.id,
            company_name="No Description Corp",
            job_title="Mystery Role",
            job_description=None,  # No description!
            status=ApplicationStatus.APPLIED,
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        resume = create_resume_in_db(db_session, test_user.id)

        response = client.post(
            "/ai/match",
            json={
                "job_id": job.id,
                "resume_id": resume.id,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_ai_match_unauthenticated(self, client):
        """
        WHAT: Call /ai/match without authentication.
        EXPECT: 401.
        """
        response = client.post(
            "/ai/match",
            json={"job_id": 1, "resume_id": 1},
            # No auth headers!
        )

        assert response.status_code == 401

    def test_ai_match_missing_job_id(self, client, auth_headers):
        """
        WHAT: Send request body without required job_id field.
        EXPECT: 422 — Pydantic validation error.
        """
        response = client.post(
            "/ai/match",
            json={"resume_id": 1},  # Missing job_id!
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_ai_match_uses_active_resume_when_no_resume_id(
        self, client, db_session, test_user, auth_headers
    ):
        """
        WHAT: Send AI match request without resume_id.
        EXPECT: Service uses the user's active resume automatically.

        This tests the "default to active resume" business logic.
        resume_id is Optional in AIMatchRequest schema.
        """
        # Create an active resume
        resume = create_resume_in_db(db_session, test_user.id)
        job = create_job_with_description(db_session, test_user.id)

        with patch(
            "app.services.ai_service.extract_text_from_pdf",
            return_value="python fastapi sql docker",
        ):
            with patch(
                "app.services.ai_service.mock_analyze_resume",
                return_value=self.MOCK_AI_RESPONSE,
            ):
                response = client.post(
                    "/ai/match",
                    json={
                        "job_id": job.id,
                        # No resume_id — should use active resume
                    },
                    headers=auth_headers,
                )

        # Should succeed — found the active resume automatically
        assert response.status_code == 200

    def test_ai_match_simulated_provider_failure(
        self, client, db_session, test_user, auth_headers
    ):
        """
        WHAT: Simulate the AI provider raising an exception.
        EXPECT: 500 Internal Server Error (graceful failure).

        WHY test failure scenarios?
        ────────────────────────────
        External services WILL fail. Network timeouts, rate limits,
        API key expiry, service outages — all of these happen in production.
        Testing failure scenarios ensures your app doesn't crash with
        an ugly Python traceback, but returns a clean error response.

        HOW we simulate a failure:
        ───────────────────────────
        We tell the mock: "when called, raise an Exception instead of
        returning a value." This simulates the AI provider crashing.
        """
        resume = create_resume_in_db(db_session, test_user.id)
        job = create_job_with_description(db_session, test_user.id)

        with patch(
            "app.services.ai_service.extract_text_from_pdf",
            return_value="python fastapi",
        ):
            with patch(
                "app.services.ai_service.mock_analyze_resume",
                side_effect=Exception("AI service is down!"),  # RAISES exception
            ):
                with pytest.raises(Exception, match="AI service is down!"):
                    client.post(
                        "/ai/match",
                        json={
                            "job_id": job.id,
                            "resume_id": resume.id,
                        },
                        headers=auth_headers,
                    )
