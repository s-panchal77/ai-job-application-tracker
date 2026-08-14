# backend/tests/test_jobs.py

"""
test_jobs.py — Job Application CRUD Tests
==========================================

PURPOSE:
  Tests all endpoints in /jobs — Create, Read, Update, Delete.

CRUD TESTING STRATEGY:
  For each operation we test:
    1. SUCCESS case   — the "happy path" that should work
    2. FAILURE cases  — edge cases, invalid input, auth failures
    3. AUTH cases     — unauthenticated + wrong-user access

WHY test CRUD so extensively?
  CRUD bugs are the most common in real applications:
    - Missing authorization checks (User A reads User B's data)
    - Missing validation (negative IDs, wrong types)
    - Wrong status codes (200 instead of 201 for creation)
    - Silent failures (update returns 200 but didn't actually update)

All tests use fixtures from conftest.py (injected by pytest).
"""


# =============================================================
# SECTION 1: CREATE JOB TESTS
# =============================================================


class TestCreateJob:
    """
    Tests for POST /jobs/

    The job creation endpoint:
      - Requires authentication (JWT token)
      - Validates request body (company_name, job_title required)
      - Creates a job owned by the current user
      - Returns 201 with the created job
    """

    # Reusable valid job payload
    VALID_JOB = {
        "company_name": "OpenAI",
        "job_title": "ML Engineer",
        "job_description": "Build language models and APIs",
        "location": "San Francisco, CA",
        "notes": "Saw on LinkedIn",
    }

    def test_create_job_success(self, client, auth_headers):
        """
        WHAT: Create a job with all valid fields.
        EXPECT: HTTP 201 + job data in response.

        ASSERTIONS:
          - status_code == 201   → "Created" (not 200 "OK")
          - data["id"] exists    → DB assigned an auto-increment ID
          - company/title match  → Data was saved correctly
          - status == "Applied"  → Default status when not specified
          - user_id is set       → Job is owned by our test user
        """
        response = client.post("/jobs/", json=self.VALID_JOB, headers=auth_headers)

        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["company_name"] == "OpenAI"
        assert data["job_title"] == "ML Engineer"
        assert data["status"] == "Applied"  # Default status
        assert data["user_id"] is not None  # Owned by our user

    def test_create_job_with_custom_status(self, client, auth_headers):
        """
        WHAT: Create a job with status = "Interview" (not the default).
        EXPECT: 201 + status reflects what we sent.
        """
        response = client.post(
            "/jobs/",
            json={
                **self.VALID_JOB,
                "status": "Interview",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        assert response.json()["status"] == "Interview"

    def test_create_job_only_required_fields(self, client, auth_headers):
        """
        WHAT: Create a job with only the 2 required fields.
        EXPECT: 201 — all optional fields default to None.
        """
        response = client.post(
            "/jobs/",
            json={
                "company_name": "Minimal Corp",
                "job_title": "Developer",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["location"] is None  # Optional, not provided
        assert data["notes"] is None  # Optional, not provided
        assert data["job_url"] is None  # Optional, not provided

    def test_create_job_missing_company_name(self, client, auth_headers):
        """
        WHAT: Omit the required 'company_name' field.
        EXPECT: HTTP 422 — Pydantic validation error.
        """
        response = client.post(
            "/jobs/",
            json={
                "job_title": "Engineer",  # No company_name!
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_job_missing_job_title(self, client, auth_headers):
        """
        WHAT: Omit the required 'job_title' field.
        EXPECT: HTTP 422.
        """
        response = client.post(
            "/jobs/",
            json={
                "company_name": "SomeCorp",  # No job_title!
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_job_empty_company_name(self, client, auth_headers):
        """
        WHAT: Send company_name as empty string "".
        EXPECT: HTTP 422 — min_length=1 validation fails.

        WHERE is this defined?
        ─────────────────────
        schemas/job.py:
            company_name: str = Field(min_length=1, max_length=255, ...)
        """
        response = client.post(
            "/jobs/",
            json={
                "company_name": "",  # Empty string - violates min_length=1
                "job_title": "Engineer",
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_job_invalid_status(self, client, auth_headers):
        """
        WHAT: Send an invalid status value not in the enum.
        EXPECT: HTTP 422 — Pydantic rejects unknown enum value.

        Valid values: "Applied", "OA Scheduled", "Interview", "Rejected", "Selected"
        """
        response = client.post(
            "/jobs/",
            json={
                "company_name": "Corp",
                "job_title": "Dev",
                "status": "FLYING",  # Not a valid ApplicationStatus
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_job_unauthenticated(self, client):
        """
        WHAT: Try to create a job WITHOUT an auth token.
        EXPECT: HTTP 401 — authentication required.

        WHY this is critical:
        ──────────────────────
        If this returns 201, anyone on the internet can create jobs
        in your database without logging in. Security test!
        """
        response = client.post("/jobs/", json=self.VALID_JOB)  # No headers!

        assert response.status_code == 401


# =============================================================
# SECTION 2: READ JOBS TESTS
# =============================================================


class TestReadJobs:
    """
    Tests for GET /jobs/ (list) and GET /jobs/{id} (single job)
    """

    def test_get_all_jobs_empty(self, client, auth_headers):
        """
        WHAT: Get all jobs when the user has no jobs yet.
        EXPECT: HTTP 200 + empty list.

        IMPORTANT: This test relies on database isolation.
        Each test gets a rolled-back DB, so there are 0 jobs here
        even though test_create_job_success creates one.
        """
        response = client.get("/jobs/", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []  # Empty list

    def test_get_all_jobs_returns_only_own_jobs(
        self,
        client,
        db_session,
        test_user,
        second_user,
        auth_headers,
        second_user_auth_headers,
    ):
        """
        WHAT: User A's job list should NOT include User B's jobs.
        EXPECT: Each user only sees their own jobs.

        WHY this is critical:
        ──────────────────────
        Data isolation between users is a core security requirement.
        If User A can see User B's job applications, it's a data leak.

        HOW we test it:
        ────────────────
        1. Create a job for test_user (via API with auth_headers)
        2. Create a job for second_user (via API with second_user_auth_headers)
        3. Assert test_user only sees 1 job (their own)
        4. Assert second_user only sees 1 job (their own)
        """
        # Create job for test_user
        client.post(
            "/jobs/",
            json={
                "company_name": "UserA Corp",
                "job_title": "UserA Job",
            },
            headers=auth_headers,
        )

        # Create job for second_user
        client.post(
            "/jobs/",
            json={
                "company_name": "UserB Corp",
                "job_title": "UserB Job",
            },
            headers=second_user_auth_headers,
        )

        # test_user should only see their own job
        response_a = client.get("/jobs/", headers=auth_headers)
        jobs_a = response_a.json()
        assert len(jobs_a) == 1
        assert jobs_a[0]["company_name"] == "UserA Corp"

        # second_user should only see their own job
        response_b = client.get("/jobs/", headers=second_user_auth_headers)
        jobs_b = response_b.json()
        assert len(jobs_b) == 1
        assert jobs_b[0]["company_name"] == "UserB Corp"

    def test_get_all_jobs_unauthenticated(self, client):
        """EXPECT: 401 — list endpoint also requires auth."""
        response = client.get("/jobs/")
        assert response.status_code == 401

    def test_get_single_job_success(self, client, sample_job, auth_headers):
        """
        WHAT: Get a specific job by its ID.
        EXPECT: 200 + correct job data.

        HOW sample_job works:
        ──────────────────────
        sample_job is a fixture that creates a real JobApplication in the DB.
        sample_job.id is the real auto-generated ID.
        We use that ID to make the GET request.
        """
        response = client.get(f"/jobs/{sample_job.id}", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert data["id"] == sample_job.id
        assert data["company_name"] == sample_job.company_name
        assert data["job_title"] == sample_job.job_title

    def test_get_single_job_not_found(self, client, auth_headers):
        """
        WHAT: Request a job ID that doesn't exist.
        EXPECT: HTTP 404 Not Found.

        99999999 is an ID that will never exist in our test DB.
        """
        response = client.get("/jobs/99999999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_single_job_wrong_user(
        self, client, sample_job, second_user_auth_headers
    ):
        """
        WHAT: User B tries to read User A's job.
        EXPECT: HTTP 404 (or 403).

        WHY 404 instead of 403?
        ────────────────────────
        We intentionally return 404 (not 403 Forbidden) to hide the
        existence of the resource. If we return 403, the attacker
        knows the job EXISTS but they can't access it.
        If we return 404, they can't tell if the job exists at all.
        This is called "security through obscurity at the HTTP level."
        """
        # second_user tries to read test_user's job
        response = client.get(
            f"/jobs/{sample_job.id}",
            headers=second_user_auth_headers,  # Wrong user!
        )

        assert response.status_code in [403, 404]  # Either is acceptable

    def test_get_job_stats(self, client, auth_headers, sample_job):
        """
        WHAT: Get job statistics for the current user.
        EXPECT: 200 + stats dict with counts per status.
        """
        response = client.get("/jobs/stats", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "applied" in data
        assert "interview" in data
        assert "rejected" in data
        assert data["total"] >= 1  # We have sample_job
        assert data["applied"] >= 1  # sample_job has status "Applied"


# =============================================================
# SECTION 3: UPDATE JOB TESTS
# =============================================================


class TestUpdateJob:
    """
    Tests for PATCH /jobs/{job_id}

    PATCH = Partial update — only send the fields you want to change.
    Unlike PUT which requires the entire object, PATCH only needs
    the fields you're modifying.
    """

    def test_update_job_success(self, client, sample_job, auth_headers):
        """
        WHAT: Update company_name and status of an existing job.
        EXPECT: 200 + updated fields reflected in response.
        """
        response = client.patch(
            f"/jobs/{sample_job.id}",
            json={
                "company_name": "Updated Corp",
                "status": "Interview",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["company_name"] == "Updated Corp"  # Updated!
        assert data["status"] == "Interview"  # Updated!
        assert data["job_title"] == sample_job.job_title  # Unchanged!

    def test_update_job_partial_fields(self, client, sample_job, auth_headers):
        """
        WHAT: Update only ONE field (PATCH is partial).
        EXPECT: 200 + only that field changes, others stay the same.
        """
        original_title = sample_job.job_title

        response = client.patch(
            f"/jobs/{sample_job.id}",
            json={"notes": "Updated note"},  # Only notes
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated note"  # Changed
        assert data["job_title"] == original_title  # Unchanged

    def test_update_job_not_found(self, client, auth_headers):
        """
        WHAT: Update a job ID that doesn't exist.
        EXPECT: HTTP 404.
        """
        response = client.patch(
            "/jobs/99999999",
            json={"notes": "ghost update"},
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_update_job_wrong_user(self, client, sample_job, second_user_auth_headers):
        """
        WHAT: User B tries to update User A's job.
        EXPECT: 404 (or 403) — authorization check.

        SECURITY: This verifies that job ownership is enforced.
        Without this check, any logged-in user could modify anyone's data.
        """
        response = client.patch(
            f"/jobs/{sample_job.id}",
            json={"notes": "hacked!"},
            headers=second_user_auth_headers,  # Wrong user!
        )

        assert response.status_code in [403, 404]

    def test_update_job_unauthenticated(self, client, sample_job):
        """EXPECT: 401 — update requires auth."""
        response = client.patch(
            f"/jobs/{sample_job.id}",
            json={"notes": "no auth"},
        )

        assert response.status_code == 401

    def test_update_job_invalid_status(self, client, sample_job, auth_headers):
        """
        WHAT: Update status to an invalid enum value.
        EXPECT: 422 — Pydantic rejects it.
        """
        response = client.patch(
            f"/jobs/{sample_job.id}",
            json={"status": "INVALID_STATUS"},
            headers=auth_headers,
        )

        assert response.status_code == 422


# =============================================================
# SECTION 4: DELETE JOB TESTS
# =============================================================


class TestDeleteJob:
    """
    Tests for DELETE /jobs/{job_id}

    DELETE returns 204 No Content (success with no body).
    204 means: "I did it, there's nothing to return."
    """

    def test_delete_job_success(self, client, sample_job, auth_headers):
        """
        WHAT: Delete an existing job.
        EXPECT: HTTP 204 No Content (success, no response body).

        THEN verify: Trying to GET the deleted job returns 404.
        This is the full delete lifecycle test.
        """
        # Step 1: Delete the job
        delete_response = client.delete(
            f"/jobs/{sample_job.id}",
            headers=auth_headers,
        )

        assert delete_response.status_code == 204  # No Content
        assert delete_response.content == b""  # Truly empty body

        # Step 2: Verify it's gone
        get_response = client.get(
            f"/jobs/{sample_job.id}",
            headers=auth_headers,
        )

        assert get_response.status_code == 404  # Cannot find deleted job

    def test_delete_job_not_found(self, client, auth_headers):
        """
        WHAT: Delete a job ID that doesn't exist.
        EXPECT: HTTP 404.
        """
        response = client.delete("/jobs/99999999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_job_wrong_user(self, client, sample_job, second_user_auth_headers):
        """
        WHAT: User B tries to delete User A's job.
        EXPECT: 404 (or 403) — authorization check.
        """
        response = client.delete(
            f"/jobs/{sample_job.id}",
            headers=second_user_auth_headers,  # Wrong user!
        )

        assert response.status_code in [403, 404]

    def test_delete_job_unauthenticated(self, client, sample_job):
        """EXPECT: 401 — delete requires auth."""
        response = client.delete(f"/jobs/{sample_job.id}")

        assert response.status_code == 401
