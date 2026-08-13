# backend/tests/test_resumes.py

"""
test_resumes.py — Resume Upload & Management Tests
====================================================

PURPOSE:
  Tests all endpoints in /resumes — upload, list, get, download, delete.

FILE UPLOAD TESTING — HOW IT WORKS:
  HTTP file uploads use 'multipart/form-data' format, not JSON.
  TestClient sends files using the 'files' parameter:

    client.post("/resumes/upload", files={"file": ("name.pdf", bytes, "mime")})

  The tuple format is: (filename, file_content, content_type)

  Why is this different from JSON?
  ──────────────────────────────────
  JSON is text-based. File uploads are binary (PDFs contain non-text bytes).
  HTTP uses multipart/form-data to mix binary file data with text form fields.
  FastAPI's UploadFile and Form() expect multipart format, not JSON.

MOCKING FILE SYSTEM:
  Real resume uploads write files to disk (uploads/ directory).
  In tests we want to avoid polluting the filesystem.
  We use unittest.mock.patch to intercept the file write calls.
"""

import io
import os
from unittest.mock import patch, AsyncMock, MagicMock


# =============================================================
# SECTION 1: RESUME UPLOAD TESTS
# =============================================================

class TestResumeUpload:
    """
    Tests for POST /resumes/upload

    The upload endpoint:
      - Requires authentication
      - Validates file type (must be PDF)
      - Validates file size (max 5 MB)
      - Saves file to uploads/ directory
      - Creates a Resume record in database
      - Returns 201 with resume metadata
    """

    def _make_pdf_upload(self, filename="resume.pdf"):
        """
        Helper: Creates a minimal fake PDF upload tuple.

        The tuple format required by TestClient:
            (filename, file_bytes, content_type)
        """
        pdf_bytes = b"%PDF-1.4 test resume content python fastapi docker"
        return (filename, pdf_bytes, "application/pdf")

    def test_upload_resume_success(self, client, auth_headers, tmp_path):
        """
        WHAT: Upload a valid PDF resume.
        EXPECT: 201 + resume metadata in response.

        WHAT IS tmp_path?
        ──────────────────
        pytest's built-in fixture that creates a temporary directory
        that is automatically cleaned up after the test.
        We patch the upload directory to use this temp path so we
        don't write to the real uploads/ folder during tests.

        WHAT IS patch()?
        ─────────────────
        unittest.mock.patch temporarily replaces a function/value
        during a test, then automatically restores it.
        Here we patch the UPLOAD_DIR to point to our temp directory.
        """
        with patch("app.utils.file_utils.UPLOAD_DIR", str(tmp_path)):
            response = client.post(
                "/resumes/upload",
                files={"file": self._make_pdf_upload()},
                headers=auth_headers,
            )

        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["original_filename"] == "resume.pdf"
        assert data["is_active"] is True     # First upload is active by default

    def test_upload_resume_with_version_label(self, client, auth_headers, tmp_path):
        """
        WHAT: Upload a resume with a version label ("v1", "Tech", etc.)
        EXPECT: 201 + version_label saved in response.
        """
        with patch("app.utils.file_utils.UPLOAD_DIR", str(tmp_path)):
            response = client.post(
                "/resumes/upload",
                files={"file": self._make_pdf_upload()},
                data={"version_label": "Software Engineer v2"},  # Form field
                headers=auth_headers,
            )

        assert response.status_code == 201
        assert response.json()["version_label"] == "Software Engineer v2"

    def test_upload_resume_no_file(self, client, auth_headers):
        """
        WHAT: Call upload endpoint without attaching any file.
        EXPECT: 422 — required file field is missing.
        """
        response = client.post(
            "/resumes/upload",
            headers=auth_headers,
            # No 'files' parameter!
        )

        assert response.status_code == 422

    def test_upload_resume_invalid_file_type(self, client, auth_headers, tmp_path):
        """
        WHAT: Upload a .txt file instead of PDF.
        EXPECT: 400 — our service rejects non-PDF files.

        WHERE is this validated?
        ─────────────────────────
        In resume_service.py, the upload_resume function checks
        if the file's content_type is "application/pdf".
        If not, it raises a 400 Bad Request.
        """
        with patch("app.utils.file_utils.UPLOAD_DIR", str(tmp_path)):
            response = client.post(
                "/resumes/upload",
                files={
                    "file": ("document.txt", b"plain text content", "text/plain")
                },
                headers=auth_headers,
            )

        assert response.status_code == 400

    def test_upload_resume_unauthenticated(self, client):
        """EXPECT: 401 — upload requires auth."""
        response = client.post(
            "/resumes/upload",
            files={"file": ("resume.pdf", b"%PDF-1.4", "application/pdf")},
            # No auth headers!
        )

        assert response.status_code == 401


# =============================================================
# SECTION 2: LIST RESUMES TESTS
# =============================================================

class TestListResumes:
    """Tests for GET /resumes/"""

    def test_list_resumes_empty(self, client, auth_headers):
        """
        WHAT: List resumes when user has none.
        EXPECT: 200 + empty result (list or dict with 'resumes' key).
        """
        response = client.get("/resumes/", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        # The endpoint returns ResumeListResponse which has a 'resumes' field
        assert "resumes" in data
        assert data["resumes"] == []

    def test_list_resumes_unauthenticated(self, client):
        """EXPECT: 401."""
        response = client.get("/resumes/")
        assert response.status_code == 401


# =============================================================
# SECTION 3: GET SINGLE RESUME TESTS
# =============================================================

class TestGetResume:
    """Tests for GET /resumes/{resume_id}"""

    def test_get_resume_not_found(self, client, auth_headers):
        """
        WHAT: Request a resume ID that doesn't exist.
        EXPECT: 404.
        """
        response = client.get("/resumes/99999999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_resume_unauthenticated(self, client):
        """EXPECT: 401."""
        response = client.get("/resumes/1")
        assert response.status_code == 401


# =============================================================
# SECTION 4: DELETE RESUME TESTS
# =============================================================

class TestDeleteResume:
    """Tests for DELETE /resumes/{resume_id}"""

    def test_delete_resume_not_found(self, client, auth_headers):
        """
        WHAT: Delete a resume ID that doesn't exist.
        EXPECT: 404.
        """
        response = client.delete("/resumes/99999999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_resume_unauthenticated(self, client):
        """EXPECT: 401."""
        response = client.delete("/resumes/1")
        assert response.status_code == 401
