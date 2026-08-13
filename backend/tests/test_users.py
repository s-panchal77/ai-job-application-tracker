# backend/tests/test_users.py

"""
test_users.py — User Management Tests
========================================

PURPOSE:
  Tests all endpoints in /users — CRUD operations matching the actual router.

ACTUAL ROUTER DESIGN:
  POST   /users/              → Create user (no auth — handled by /auth/register too)
  GET    /users/{user_id}     → Get user by ID
  GET    /users/              → List all users
  PATCH  /users/{user_id}     → Update user's full_name
  DELETE /users/{user_id}     → Delete user

NOTE:
  The /users router does NOT require authentication (no Depends(get_current_user)).
  Authentication is handled by /auth/register and /auth/login.
  /auth/me is the protected "current user" endpoint.

  This means our user tests focus on:
    - Correct CRUD behavior
    - Validation (wrong types, missing fields)
    - 404 for missing IDs
    - Correct status codes
"""

# =============================================================
# SECTION 1: CREATE USER TESTS
# =============================================================

class TestCreateUser:
    """Tests for POST /users/"""

    def test_create_user_success(self, client):
        """
        WHAT: Create a user with valid data.
        EXPECT: 201 + user data, no password in response.
        """
        response = client.post("/users/", json={
            "email": "createuser@example.com",
            "password": "ValidPass123!",
            "full_name": "New User",
        })

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "createuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data
        assert "password" not in data

    def test_create_user_duplicate_email(self, client, test_user):
        """
        WHAT: Create user with email that already exists.
        EXPECT: 400 — email already registered.
        """
        response = client.post("/users/", json={
            "email": test_user.email,  # Already taken
            "password": "AnotherPass123!",
        })
        assert response.status_code == 400

    def test_create_user_missing_required_fields(self, client):
        """EXPECT: 422 — email and password are required."""
        response = client.post("/users/", json={})
        assert response.status_code == 422

    def test_create_user_invalid_email(self, client):
        """EXPECT: 422 — EmailStr validation rejects bad format."""
        response = client.post("/users/", json={
            "email": "not-valid",
            "password": "ValidPass123!",
        })
        assert response.status_code == 422

    def test_create_user_short_password(self, client):
        """EXPECT: 422 — password min_length=8."""
        response = client.post("/users/", json={
            "email": "test@example.com",
            "password": "abc",  # Too short
        })
        assert response.status_code == 422


# =============================================================
# SECTION 2: GET USER BY ID TESTS
# =============================================================

class TestGetUser:
    """Tests for GET /users/{user_id}"""

    def test_get_user_success(self, client, test_user):
        """
        WHAT: Get existing user by their database ID.
        EXPECT: 200 + correct user data.
        """
        response = client.get(f"/users/{test_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert "hashed_password" not in data

    def test_get_user_not_found(self, client):
        """
        WHAT: Request a user ID that doesn't exist.
        EXPECT: 404.
        """
        response = client.get("/users/99999999")
        assert response.status_code == 404

    def test_get_user_invalid_id_type(self, client):
        """
        WHAT: Send a string where an integer ID is expected.
        EXPECT: 422 — FastAPI rejects non-integer path parameter.
        """
        response = client.get("/users/not-an-id")
        assert response.status_code == 422


# =============================================================
# SECTION 3: LIST USERS TESTS
# =============================================================

class TestListUsers:
    """Tests for GET /users/"""

    def test_list_users_empty(self, client):
        """EXPECT: 200 + empty list when no users exist."""
        response = client.get("/users/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_users_returns_created_user(self, client, test_user):
        """
        WHAT: List users after one was created.
        EXPECT: 200 + list contains at least the test_user.
        """
        response = client.get("/users/")
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 1
        emails = [u["email"] for u in users]
        assert test_user.email in emails

    def test_list_users_pagination(self, client):
        """
        WHAT: Use skip and limit pagination parameters.
        EXPECT: 200.
        """
        response = client.get("/users/?skip=0&limit=10")
        assert response.status_code == 200


# =============================================================
# SECTION 4: UPDATE USER TESTS
# =============================================================

class TestUpdateUser:
    """Tests for PATCH /users/{user_id}"""

    def test_update_full_name_success(self, client, test_user):
        """
        WHAT: Update user's full_name via query parameter.
        EXPECT: 200 + updated full_name in response.

        NOTE: The /users/PATCH endpoint takes full_name as a QUERY PARAM,
        not a JSON body — this is how the actual router is designed.
        PATCH /users/{user_id}?full_name=NewName
        """
        response = client.patch(
            f"/users/{test_user.id}",
            params={"full_name": "Updated Full Name"},
        )

        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Full Name"

    def test_update_user_not_found(self, client):
        """
        WHAT: Update a user ID that doesn't exist.
        EXPECT: 404.
        """
        response = client.patch(
            "/users/99999999",
            params={"full_name": "Ghost"},
        )
        assert response.status_code == 404

    def test_update_user_no_full_name(self, client, test_user):
        """
        WHAT: PATCH without providing full_name.
        EXPECT: 200 — full_name is optional (None means no change).
        """
        response = client.patch(f"/users/{test_user.id}")
        assert response.status_code == 200


# =============================================================
# SECTION 5: DELETE USER TESTS
# =============================================================

class TestDeleteUser:
    """Tests for DELETE /users/{user_id}"""

    def test_delete_user_success(self, client, test_user):
        """
        WHAT: Delete a user by their ID.
        EXPECT: 204 No Content.

        THEN verify: GET for that user returns 404.
        """
        # Delete
        delete_response = client.delete(f"/users/{test_user.id}")
        assert delete_response.status_code == 204
        assert delete_response.content == b""

        # Verify gone
        get_response = client.get(f"/users/{test_user.id}")
        assert get_response.status_code == 404

    def test_delete_user_not_found(self, client):
        """EXPECT: 404 — cannot delete a non-existent user."""
        response = client.delete("/users/99999999")
        assert response.status_code == 404
