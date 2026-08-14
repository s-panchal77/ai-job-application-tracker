# backend/app/core/exceptions.py

import traceback

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings

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


def unauthorized_exception(
    detail: str = "Incorrect email or password",
) -> HTTPException:
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


# ==========================================================
# GLOBAL EXCEPTION HANDLERS
# ==========================================================
# These functions are registered in main.py with:
#   app.add_exception_handler(HTTPException, http_exception_handler)
#
# FastAPI calls them automatically when matching exceptions are raised
# ANYWHERE in the application — routers, services, dependencies.
#
# WHY ADD HANDLERS FOR HTTPException WHEN FASTAPI ALREADY HANDLES IT?
# ─────────────────────────────────────────────────────────────────────
# FastAPI's default handler works but:
#   1. It doesn't LOG the error — you're blind in production
#   2. The response format can differ slightly across versions
#   3. You can't add custom fields (e.g., "path", "method") easily
#
# By overriding it, you get logging + consistent format + control.
# ==========================================================


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handles all HTTPException instances raised anywhere in the app.

    This includes:
      - 400 Bad Request     (bad_request_exception)
      - 401 Unauthorized    (credentials_exception, unauthorized_exception)
      - 403 Forbidden       (forbidden_exception)
      - 404 Not Found       (not_found_exception)
      - 429 Too Many Requests (rate limiter)

    HOW IT WORKS:
      When any code does `raise HTTPException(...)`, FastAPI
      catches it and calls this function instead of the default handler.
      We log it, then return a consistent JSON response.

    LOGGING STRATEGY:
      - 4xx errors: WARNING (user error, not our fault)
      - 5xx errors: ERROR (server error, our fault)
    """
    # Import here to avoid circular import (logging imports config, exceptions imports logging)
    from app.core.logging import get_logger

    logger = get_logger("app.exceptions")

    # Choose log level: 4xx are warnings, 5xx are errors
    if exc.status_code >= 500:
        logger.error(
            "HTTP %s | %s %s | %s",
            exc.status_code,
            request.method,
            request.url.path,
            exc.detail,
        )
    else:
        logger.warning(
            "HTTP %s | %s %s | %s",
            exc.status_code,
            request.method,
            request.url.path,
            exc.detail,
        )

    # Return consistent JSON — same format for every error in the app
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        # Preserve auth challenge headers (e.g. WWW-Authenticate: Bearer)
        headers=dict(exc.headers) if exc.headers else None,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handles Pydantic validation errors from request bodies and query params.

    WHEN THIS FIRES:
      When a client sends a request body that fails Pydantic validation.
      Example: POST /jobs/ with missing required field "company_name"

    DEFAULT FASTAPI BEHAVIOR (without this handler):
      Returns 422 with Pydantic's full internal error format.
      It works, but it's verbose and inconsistent with our other errors.

    OUR BEHAVIOR:
      Returns 422 with a clean list of which fields failed and why.
      Example response:
        {
          "detail": "Validation failed",
          "errors": [
            {
              "field": "body → company_name",
              "message": "Field required"
            }
          ]
        }
    """
    from app.core.logging import get_logger

    logger = get_logger("app.exceptions")

    # Build a simplified list of field errors
    # exc.errors() returns a list of dicts from Pydantic
    errors = []
    for error in exc.errors():
        # error["loc"] is a tuple: ("body", "company_name") or ("query", "limit")
        # We join it as "body → company_name" for readability
        field_path = " → ".join(str(loc) for loc in error["loc"])
        errors.append(
            {
                "field": field_path,
                "message": error[
                    "msg"
                ],  # "Field required", "value is not a valid integer"
            }
        )

    logger.warning(
        "Validation error | %s %s | %d field(s) failed",
        request.method,
        request.url.path,
        len(errors),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation failed",
            "errors": errors,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches ALL other exceptions that were NOT deliberately raised as HTTPException.

    WHEN THIS FIRES:
      - Database connection dropped mid-request
      - An AI service call raised an unexpected error
      - A bug in service code (AttributeError, KeyError, etc.)
      - Any Python error we forgot to handle

    CRITICAL PRODUCTION RULE:
      NEVER send the raw Python traceback to the client.
      Traceback contains: file paths, variable names, internal logic.
      An attacker can use this to understand your system and find weaknesses.

    WHAT WE DO:
      - Log the FULL traceback on the server (so we can debug it)
      - Send the client a generic "Internal server error" message

    IN DEVELOPMENT:
      If settings.DEBUG is True, we include the exception type in the
      response to help with faster local debugging.
      In production (DEBUG=False), clients see only the generic message.
    """
    from app.core.logging import get_logger

    logger = get_logger("app.exceptions")

    # Log full traceback on the server — this is what you search in logs
    logger.error(
        "Unhandled exception | %s %s\n%s",
        request.method,
        request.url.path,
        traceback.format_exc(),  # Full Python traceback with file + line numbers
    )

    # Build client response — hide internals in production
    if settings.DEBUG:
        # Development: show exception type to speed up debugging
        # Still NOT the full traceback — just the type
        detail = f"Internal server error: {type(exc).__name__}: {str(exc)}"
    else:
        # Production: generic message, no internal info
        detail = "An unexpected internal server error occurred."

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail},
    )
