# backend/app/core/exceptions.py

from fastapi import HTTPException, status

# ─────────────────────────────────────────────────────────────
# WHY THIS FILE EXISTS
# ─────────────────────────────────────────────────────────────
# Without this file, every service writes its own HTTPException:
#
#   raise HTTPException(status_code=404, detail="User with id 5 not found")
#   raise HTTPException(status_code=404, detail="Job with id 3 not found")
#
# That is the same pattern repeated everywhere.
# This file defines it ONCE. Every service imports and calls it.
#
# Benefits:
# - Consistent error message format across all resources
# - Change the format in one place, it updates everywhere
# - Easier to read in service files (one line instead of three)
# ─────────────────────────────────────────────────────────────


def not_found_exception(resource: str, resource_id: int) -> HTTPException:
    """
    Use this when any resource (User, Job, Resume) is not found by ID.

    Example:
        raise not_found_exception("User", user_id)
        raise not_found_exception("Job", job_id)

    Returns:
        404 Not Found
        {"detail": "User with id 5 not found"}
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} with id {resource_id} not found",
    )


def bad_request_exception(detail: str) -> HTTPException:
    """
    Use this when the request is understood but cannot be processed.
    Example: duplicate email during registration.

    Example:
        raise bad_request_exception("A user with this email already exists")

    Returns:
        400 Bad Request
        {"detail": "A user with this email already exists"}
    """
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )


def credentials_exception() -> HTTPException:
    """
    Use this when a JWT token is missing, invalid, or expired.
    Used inside get_current_user dependency.

    Returns:
        401 Unauthorized
        {"detail": "Could not validate credentials"}
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def unauthorized_exception(detail: str = "Incorrect email or password") -> HTTPException:
    """
    Use this when login credentials are wrong.
    Separate from credentials_exception() — this is for failed login,
    not for invalid tokens.

    Returns:
        401 Unauthorized
        {"detail": "Incorrect email or password"}
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_exception(
    detail: str = "You do not have permission to perform this action",
) -> HTTPException:
    """
    Use this when a user is logged in but tries to access
    something that belongs to someone else.

    Example: User 2 tries to delete User 1's job application.

    This is AUTHORIZATION failure (403), not authentication failure (401).
    401 = we don't know who you are
    403 = we know who you are, but you're not allowed

    Returns:
        403 Forbidden
        {"detail": "You do not have permission to perform this action"}
    """
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )