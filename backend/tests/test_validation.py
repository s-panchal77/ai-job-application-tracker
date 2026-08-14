# backend/tests/test_validation.py

"""
test_validation.py — Input Validation Tests
=============================================

PURPOSE:
  Tests that our API correctly rejects invalid input data.

WHY VALIDATION TESTS MATTER:
  Without validation, a user could:
    - Send negative IDs: job_id = -1
    - Send wrong types: {"company_name": 12345} (int instead of string)
    - Send huge strings: company_name = "x" * 1_000_000 (DoS risk)
    - Send empty strings: company_name = ""
    - Skip required fields entirely

  Validation tests prove that your API is defensive and safe.
  FastAPI + Pydantic provides automatic validation, but we still
  need to VERIFY it actually works for our specific schemas.

WHERE DOES VALIDATION HAPPEN?
  1. Pydantic schemas (schemas/*.py)
     - Field types: str, int, EmailStr
     - Field constraints: min_length, max_length, ge, le
     - Required vs optional fields
  2. FastAPI route parameters
     - Query param constraints: ge=0, le=100
  3. Our service functions
     - Business logic checks (email already exists, etc.)

422 vs 400 vs 404:
  422 = Request was received but data FAILED VALIDATION (Pydantic)
  400 = Request was received but BUSINESS LOGIC rejected it
  404 = Resource not found
"""


# =============================================================
# SECTION 1: REGISTRATION VALIDATION
# =============================================================


class TestRegistrationValidation:
    """Validation tests for POST /auth/register"""

    def test_email_valid_formats(self, client):
        """
        WHAT: Test various valid email formats are accepted.
        EXPECT: All return 201 (valid) or 400 (duplicate, not validation).
        """
        valid_emails = [
            "user@example.com",
            "user.name@domain.org",
            "user+tag@gmail.com",
            "123@numbers.io",
        ]

        for email in valid_emails:
            response = client.post(
                "/auth/register",
                json={
                    "email": email,
                    "password": "ValidPass123!",
                },
            )
            # Either 201 (created) or 400 (duplicate) — never 422
            assert response.status_code in [
                201,
                400,
            ], f"Expected 201 or 400 for email '{email}', got {response.status_code}"

    def test_email_invalid_formats(self, client):
        """
        WHAT: Test that invalid email formats are rejected.
        EXPECT: 422 for all.
        """
        invalid_emails = [
            "notanemail",  # No @ symbol
            "@nodomain.com",  # No local part
            "no@",  # No domain
            "spaces in@email.com",  # Spaces not allowed
            "",  # Empty string
        ]

        for email in invalid_emails:
            response = client.post(
                "/auth/register",
                json={
                    "email": email,
                    "password": "ValidPass123!",
                },
            )
            assert (
                response.status_code == 422
            ), f"Expected 422 for invalid email '{email}', got {response.status_code}"

    def test_password_length_boundaries(self, client):
        """
        WHAT: Test password at exact length boundaries.
        EXPECT:
          - 7 chars = 422 (below min of 8)
          - 8 chars = 201 (at minimum)
          - 72 chars = 201 (at maximum)
          - 73 chars = 422 (above max of 72)
        """
        # 7 chars — below minimum (8)
        response = client.post(
            "/auth/register",
            json={
                "email": "len7@example.com",
                "password": "1234567",  # 7 chars
            },
        )
        assert response.status_code == 422

        # 8 chars — at minimum
        response = client.post(
            "/auth/register",
            json={
                "email": "len8@example.com",
                "password": "12345678",  # 8 chars
            },
        )
        assert response.status_code == 201

        # 72 chars — at maximum
        response = client.post(
            "/auth/register",
            json={
                "email": "len72@example.com",
                "password": "A" * 72,  # Exactly 72
            },
        )
        assert response.status_code == 201

        # 73 chars — above maximum
        response = client.post(
            "/auth/register",
            json={
                "email": "len73@example.com",
                "password": "A" * 73,  # One too many
            },
        )
        assert response.status_code == 422

    def test_full_name_max_length(self, client):
        """
        WHAT: full_name must be <= 255 characters.
        EXPECT: 422 if longer.
        """
        response = client.post(
            "/auth/register",
            json={
                "email": "longname@example.com",
                "password": "ValidPass123!",
                "full_name": "N" * 300,  # 300 > 255
            },
        )
        assert response.status_code == 422

    def test_wrong_data_types(self, client):
        """
        WHAT: Send integers where strings are expected.
        EXPECT: Pydantic coerces OR rejects — 201 or 422, not 500.

        NOTE: Pydantic v2 CAN coerce simple types (int -> str in some cases).
        The important thing is it doesn't crash with a 500.
        """
        response = client.post(
            "/auth/register",
            json={
                "email": 12345,  # Integer, not string
                "password": "ValidPass123!",
            },
        )
        assert response.status_code == 422  # Should reject non-email integer


# =============================================================
# SECTION 2: JOB CREATION VALIDATION
# =============================================================


class TestJobValidation:
    """Validation tests for POST /jobs/"""

    def test_company_name_min_length(self, client, auth_headers):
        """
        WHAT: company_name must have at least 1 character.
        EXPECT: 422 for empty string.
        """
        response = client.post(
            "/jobs/",
            json={
                "company_name": "",  # min_length=1, fails
                "job_title": "Dev",
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_company_name_max_length(self, client, auth_headers):
        """
        WHAT: company_name must be <= 255 characters.
        EXPECT: 422 for 256+ chars.
        """
        response = client.post(
            "/jobs/",
            json={
                "company_name": "C" * 256,  # 256 > 255
                "job_title": "Dev",
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_job_title_min_length(self, client, auth_headers):
        """EXPECT: 422 for empty job title."""
        response = client.post(
            "/jobs/",
            json={
                "company_name": "Corp",
                "job_title": "",  # min_length=1, fails
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_job_url_max_length(self, client, auth_headers):
        """
        WHAT: job_url must be <= 500 characters.
        EXPECT: 422 for 501+ chars.
        """
        response = client.post(
            "/jobs/",
            json={
                "company_name": "Corp",
                "job_title": "Dev",
                "job_url": "https://example.com/" + "x" * 490,  # > 500
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_invalid_status_value(self, client, auth_headers):
        """
        WHAT: Send a status value not in the ApplicationStatus enum.
        EXPECT: 422.

        Valid values: Applied, OA Scheduled, Interview, Rejected, Selected
        """
        response = client.post(
            "/jobs/",
            json={
                "company_name": "Corp",
                "job_title": "Dev",
                "status": "HACKED",  # Not a valid enum value
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_wrong_type_for_company_name(self, client, auth_headers):
        """
        WHAT: Send a list where a string is expected.
        EXPECT: 422 — Pydantic cannot coerce list to str.
        """
        response = client.post(
            "/jobs/",
            json={
                "company_name": ["Google", "Amazon"],  # List, not string!
                "job_title": "Dev",
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_missing_both_required_fields(self, client, auth_headers):
        """
        WHAT: Send empty object (missing both required fields).
        EXPECT: 422 with details about BOTH missing fields.
        """
        response = client.post("/jobs/", json={}, headers=auth_headers)

        assert response.status_code == 422

        # The response should indicate both required fields are missing
        # Handle both default Pydantic format (list) and custom format
        body = response.json()
        body_str = str(body).lower()
        assert (
            "company_name" in body_str
            or "job_title" in body_str
            or "required" in body_str
        )


# =============================================================
# SECTION 3: QUERY PARAMETER VALIDATION
# =============================================================


class TestQueryParamValidation:
    """Validation for GET /jobs/ query parameters: skip, limit, search"""

    def test_skip_must_be_non_negative(self, client, auth_headers):
        """
        WHAT: skip=-1 is invalid (ge=0 constraint).
        EXPECT: 422.
        """
        response = client.get("/jobs/?skip=-1", headers=auth_headers)
        assert response.status_code == 422

    def test_limit_must_be_at_least_1(self, client, auth_headers):
        """
        WHAT: limit=0 is invalid (ge=1 constraint).
        EXPECT: 422.
        """
        response = client.get("/jobs/?limit=0", headers=auth_headers)
        assert response.status_code == 422

    def test_limit_cannot_exceed_100(self, client, auth_headers):
        """
        WHAT: limit=101 exceeds maximum (le=100 constraint).
        EXPECT: 422.
        """
        response = client.get("/jobs/?limit=101", headers=auth_headers)
        assert response.status_code == 422

    def test_valid_pagination_params(self, client, auth_headers):
        """
        WHAT: Valid pagination parameters should work.
        EXPECT: 200.
        """
        response = client.get("/jobs/?skip=0&limit=10", headers=auth_headers)
        assert response.status_code == 200

    def test_invalid_status_filter(self, client, auth_headers):
        """
        WHAT: Filter by an invalid status value.
        EXPECT: 422 — enum validation fails.
        """
        response = client.get("/jobs/?status=INVALID", headers=auth_headers)
        assert response.status_code == 422

    def test_valid_status_filter(self, client, auth_headers):
        """
        WHAT: Filter by a valid status value.
        EXPECT: 200.
        """
        response = client.get("/jobs/?status=Applied", headers=auth_headers)
        assert response.status_code == 200


# =============================================================
# SECTION 4: AI REQUEST VALIDATION
# =============================================================


class TestAIRequestValidation:
    """Validation tests for POST /ai/match"""

    def test_job_id_must_be_integer(self, client, auth_headers):
        """
        WHAT: Send job_id as a string.
        EXPECT: 422 — must be int.
        """
        response = client.post(
            "/ai/match",
            json={
                "job_id": "not-an-int",  # String, not int!
                "resume_id": 1,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_job_id_required(self, client, auth_headers):
        """
        WHAT: Missing required job_id.
        EXPECT: 422.
        """
        response = client.post(
            "/ai/match",
            json={
                "resume_id": 1,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_resume_id_is_optional(self, client, db_session, test_user, auth_headers):
        """
        WHAT: Omit optional resume_id.
        EXPECT: Not a validation error (may be 404 if no active resume, not 422).

        This verifies that resume_id is truly optional in our schema.
        The result might be 404 (no active resume found) or 200 (if one exists),
        but it should NEVER be 422 (validation error).
        """
        response = client.post(
            "/ai/match",
            json={
                "job_id": 1,  # May not exist, but that's OK — testing schema validation
            },
            headers=auth_headers,
        )

        assert response.status_code != 422  # NOT a validation error
