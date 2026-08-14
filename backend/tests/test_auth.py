# backend/tests/test_auth.py

"""
test_auth.py — Authentication Tests
======================================

PURPOSE:
  Tests all endpoints in /auth — registration, login, and protected routes.

WHAT WE TEST:
  1. POST /auth/register
     - Successful registration
     - Duplicate email rejection
     - Missing required fields
     - Invalid email format
     - Password too short

  2. POST /auth/login
     - Successful login returns JWT token
     - Wrong password
     - Non-existing user
     - Missing credentials

  3. GET /auth/me
     - Valid token -> returns user data
     - Missing token -> 401
     - Invalid token -> 401

HOW PYTEST FIXTURES WORK HERE:
  Functions that take 'client', 'test_user', 'auth_headers' as arguments
  are NOT calling those functions — pytest INJECTS them automatically
  from conftest.py. This is called Dependency Injection (same concept
  as FastAPI's Depends() but for tests).
"""


# =============================================================
# SECTION 1: REGISTRATION TESTS
# =============================================================


class TestRegistration:
    """
    Tests for POST /auth/register

    WHY use a class?
    ─────────────────
    Grouping related tests in a class makes output cleaner:
      test_auth.py::TestRegistration::test_register_success PASSED
      test_auth.py::TestRegistration::test_duplicate_email FAILED
    Also allows shared setup with setup_method() if needed.
    """

    def test_register_success(self, client):
        """
        WHAT: A new user registers with valid data.
        EXPECT: HTTP 201 Created + user data in response body.

        ASSERTIONS EXPLAINED:
          - status_code == 201  → Created (not 200)
          - "id" in data        → DB assigned an ID
          - data["email"] == .. → The email was saved correctly
          - "password" not in.. → We NEVER send hashed password back
          - "is_active" == True → New users are active by default
        """
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User",
            },
        )

        assert response.status_code == 201

        data = response.json()
        assert "id" in data  # Got a real DB ID
        assert data["email"] == "newuser@example.com"  # Email saved correctly
        assert data["full_name"] == "New User"  # Name saved correctly
        assert data["is_active"] is True  # Active by default
        assert "password" not in data  # Password NEVER in response
        assert "hashed_password" not in data  # Hash NEVER in response

    def test_register_without_full_name(self, client):
        """
        WHAT: Register with only required fields (email + password).
        EXPECT: 201 — full_name is optional.
        """
        response = client.post(
            "/auth/register",
            json={
                "email": "noname@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["full_name"] is None  # Optional field is null

    def test_register_duplicate_email(self, client, test_user):
        """
        WHAT: Try to register with an email that already exists.
        EXPECT: HTTP 400 Bad Request (not 500 — we handle this gracefully).

        WHY test_user fixture?
        ──────────────────────
        test_user creates a user with email 'testuser@example.com'.
        We then try to register again with that same email.
        The service should detect the conflict and raise 400.
        """
        response = client.post(
            "/auth/register",
            json={
                "email": "testuser@example.com",  # Already exists (from test_user)
                "password": "AnotherPass123!",
            },
        )

        # 400 Bad Request: "email already registered"
        assert response.status_code == 400
        assert (
            "already" in response.json()["detail"].lower()
            or "email" in response.json()["detail"].lower()
        )

    def test_register_invalid_email(self, client):
        """
        WHAT: Send a badly formatted email address.
        EXPECT: HTTP 422 Unprocessable Entity — Pydantic validation fails.

        WHY 422 (not 400)?
        ───────────────────
        422 is FastAPI/Pydantic's standard response for validation errors.
        The request was received correctly (400 would mean bad request syntax),
        but the DATA inside it failed validation rules.
        "not-an-email" doesn't match EmailStr's validation pattern.
        """
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 422  # Validation error
        # Our custom validation handler wraps errors — check the full response body
        body = response.json()
        # Handle both Pydantic default format (list) and custom format (str/dict)
        body_str = str(body).lower()
        assert "email" in body_str or "value" in body_str or "valid" in body_str

    def test_register_password_too_short(self, client):
        """
        WHAT: Send a password shorter than 8 characters.
        EXPECT: HTTP 422 — Pydantic's min_length=8 validation fails.

        WHERE is the validation?
        ─────────────────────────
        In schemas/user.py:
            password: str = Field(min_length=8, max_length=72, ...)
        Pydantic enforces this BEFORE the route handler runs.
        """
        response = client.post(
            "/auth/register",
            json={
                "email": "shortpass@example.com",
                "password": "abc",  # Only 3 chars, min is 8
            },
        )

        assert response.status_code == 422

    def test_register_missing_email(self, client):
        """
        WHAT: Send registration request with no email field.
        EXPECT: HTTP 422 — required field missing.
        """
        response = client.post(
            "/auth/register",
            json={
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 422

    def test_register_missing_password(self, client):
        """
        WHAT: Send registration request with no password field.
        EXPECT: HTTP 422 — required field missing.
        """
        response = client.post(
            "/auth/register",
            json={
                "email": "nopassword@example.com",
            },
        )

        assert response.status_code == 422

    def test_register_empty_body(self, client):
        """
        WHAT: Send completely empty JSON body.
        EXPECT: HTTP 422 — all required fields are missing.
        """
        response = client.post("/auth/register", json={})
        assert response.status_code == 422


# =============================================================
# SECTION 2: LOGIN TESTS
# =============================================================


class TestLogin:
    """
    Tests for POST /auth/login

    NOTE: This endpoint uses OAuth2PasswordRequestForm, which means:
      - Content-Type must be: application/x-www-form-urlencoded
      - Fields are 'username' and 'password' (NOT email)
      - The TestClient's `data={}` parameter sends form data (not JSON)
    """

    def test_login_success(self, client, test_user):
        """
        WHAT: Login with correct credentials.
        EXPECT: HTTP 200 + access_token in response.

        ASSERTIONS EXPLAINED:
          - status_code == 200      → OK
          - "access_token" in data  → JWT token was issued
          - data["token_type"] == "bearer" → Correct OAuth2 token type
          - len(access_token) > 10  → It's a real token, not an empty string
        """
        response = client.post(
            "/auth/login",
            data={
                "username": test_user.email,  # OAuth2 calls it 'username'
                "password": test_user.plain_password,
            },
        )

        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 10  # Is a real token

    def test_login_wrong_password(self, client, test_user):
        """
        WHAT: Login with correct email but wrong password.
        EXPECT: HTTP 401 Unauthorized.

        SECURITY NOTE:
        ──────────────
        The error message should be generic ("Incorrect email or password")
        NOT specific ("Wrong password" or "User not found").
        This prevents "user enumeration" attacks where a hacker tests
        if an email exists by checking different error messages.
        """
        response = client.post(
            "/auth/login",
            data={
                "username": test_user.email,
                "password": "WrongPassword999!",
            },
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """
        WHAT: Login with an email that doesn't exist in the database.
        EXPECT: HTTP 401 — same error as wrong password (no enumeration).
        """
        response = client.post(
            "/auth/login",
            data={
                "username": "ghost@example.com",
                "password": "AnyPassword123!",
            },
        )

        assert response.status_code == 401

    def test_login_missing_password(self, client, test_user):
        """
        WHAT: Send login form without the password field.
        EXPECT: HTTP 422 — required form field missing.
        """
        response = client.post(
            "/auth/login", data={"username": test_user.email}  # No password
        )

        assert response.status_code == 422

    def test_login_missing_username(self, client):
        """
        WHAT: Send login form without the username field.
        EXPECT: HTTP 422 — required form field missing.
        """
        response = client.post(
            "/auth/login", data={"password": "SomePassword123!"}  # No username
        )

        assert response.status_code == 422

    def test_login_empty_form(self, client):
        """
        WHAT: Send completely empty login form.
        EXPECT: HTTP 422.
        """
        response = client.post("/auth/login", data={})
        assert response.status_code == 422

    def test_login_returns_jwt_structure(self, client, test_user):
        """
        WHAT: Verify the JWT token has the correct structure.
        EXPECT: Token has 3 parts separated by dots (header.payload.signature).

        JWT FORMAT:
        ───────────
        A JWT looks like: xxxxx.yyyyy.zzzzz
          - Part 1: Header (algorithm type, base64 encoded)
          - Part 2: Payload (user data, expiry, base64 encoded)
          - Part 3: Signature (HMAC verification, base64 encoded)
        """
        response = client.post(
            "/auth/login",
            data={
                "username": test_user.email,
                "password": test_user.plain_password,
            },
        )

        token = response.json()["access_token"]
        parts = token.split(".")

        assert len(parts) == 3  # Must have exactly 3 parts


# =============================================================
# SECTION 3: PROTECTED ROUTE TESTS (GET /auth/me)
# =============================================================


class TestGetCurrentUser:
    """
    Tests for GET /auth/me — a protected route.

    This also tests JWT authentication as a whole because
    get_current_user dependency is used by ALL protected routes.
    """

    def test_get_me_with_valid_token(self, client, test_user, auth_headers):
        """
        WHAT: Access /auth/me with a valid JWT token.
        EXPECT: HTTP 200 + user's data.

        HOW auth_headers works:
        ────────────────────────
        auth_headers = {"Authorization": "Bearer eyJ0..."}
        TestClient sends this header with every request.
        FastAPI's oauth2_scheme extracts the token from it.
        get_current_user() decodes it and loads the user from DB.
        """
        response = client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert "hashed_password" not in data  # Security: never expose

    def test_get_me_without_token(self, client):
        """
        WHAT: Access /auth/me with NO Authorization header.
        EXPECT: HTTP 401 Unauthorized.

        This proves the route is ACTUALLY protected.
        If this returns 200, authentication is broken.
        """
        response = client.get("/auth/me")  # No headers!

        assert response.status_code == 401

    def test_get_me_with_invalid_token(self, client):
        """
        WHAT: Access /auth/me with a fake/tampered token.
        EXPECT: HTTP 401 — JWT signature verification fails.

        WHY this matters:
        ──────────────────
        If a hacker crafts a fake JWT with "sub": "1" (admin user ID),
        the signature check MUST catch it. An invalid signature means
        the token was not signed by our SECRET_KEY.
        """
        fake_headers = {"Authorization": "Bearer this.is.fake"}
        response = client.get("/auth/me", headers=fake_headers)

        assert response.status_code == 401

    def test_get_me_with_malformed_token(self, client):
        """
        WHAT: Send 'Bearer' but with garbage as the token.
        EXPECT: HTTP 401.
        """
        headers = {"Authorization": "Bearer not_even_a_jwt"}
        response = client.get("/auth/me", headers=headers)

        assert response.status_code == 401

    def test_get_me_with_expired_token(self, client, test_user):
        """
        WHAT: Access /auth/me with an already-expired token.
        EXPECT: HTTP 401 — expired tokens must be rejected.

        HOW we create expired tokens for testing:
        ───────────────────────────────────────────
        We use python-jose to manually build a token with
        an expiry time in the PAST. Real decode_access_token()
        will see it's expired and return None, causing 401.
        """
        from datetime import datetime, timedelta, timezone

        from jose import jwt

        from app.core.config import settings

        # Create a token that expired 1 hour ago
        expired_payload = {
            "sub": str(test_user.id),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # PAST!
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/auth/me", headers=headers)

        assert response.status_code == 401

    def test_get_me_with_wrong_secret(self, client, test_user):
        """
        WHAT: Token signed with a DIFFERENT secret key.
        EXPECT: HTTP 401 — signature verification fails.

        This is the core security test: even if someone knows the JWT
        format, they cannot forge a token without our SECRET_KEY.
        """
        from jose import jwt

        from app.core.config import settings

        # Sign with a DIFFERENT key
        fake_payload = {"sub": str(test_user.id)}
        bad_token = jwt.encode(
            fake_payload,
            "completely_wrong_secret_key",  # NOT our real key
            algorithm=settings.ALGORITHM,
        )

        headers = {"Authorization": f"Bearer {bad_token}"}
        response = client.get("/auth/me", headers=headers)

        assert response.status_code == 401
