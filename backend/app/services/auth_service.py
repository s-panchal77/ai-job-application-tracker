# backend/app/services/auth_service.py

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.db.database import get_db
from app.models.user import User
from app.core.security import verify_password, create_access_token, decode_access_token


# ─────────────────────────────────────────────────────────────
# OAuth2PasswordBearer
# ─────────────────────────────────────────────────────────────
# This is NOT actual OAuth2 — it's FastAPI's standard way of
# saying "this API expects a Bearer token in the Authorization header."
#
# tokenUrl="auth/login" tells Swagger UI's "Authorize" button
# WHERE to send username/password to get a token. It's only
# used for the interactive docs — doesn't affect actual logic.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ─────────────────────────────────────────────────────────────
# LOGIN LOGIC
# ─────────────────────────────────────────────────────────────
def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Verifies email + password and returns the User if valid.

    Steps:
    1. Find user by email
    2. Verify the plain password against the stored bcrypt hash
    3. Raise 401 if either step fails

    SECURITY NOTE: We deliberately use the SAME error message
    for "user not found" AND "wrong password". If we said
    "user not found" specifically, an attacker could use that
    to discover which emails are registered (user enumeration attack).
    """
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def login_for_access_token(db: Session, email: str, password: str) -> str:
    """
    Full login flow: authenticate, then issue a JWT.
    """
    user = authenticate_user(db, email, password)

    # "sub" (subject) is the JWT-standard claim for identifying the token owner.
    # We store it as a string — JWT spec requires string values for 'sub'.
    access_token = create_access_token(data={"sub": str(user.id)})

    return access_token


# ─────────────────────────────────────────────────────────────
# get_current_user — THE PROTECTED ROUTE DEPENDENCY
# ─────────────────────────────────────────────────────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),   # Extracts token from Authorization header
    db: Session = Depends(get_db),          # Standard DB session dependency
) -> User:
    """
    This is the dependency every protected route will use:

        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            ...

    FastAPI runs this function FIRST, before the route's own code.
    If it raises an exception, the route never executes.

    Flow:
    1. oauth2_scheme extracts the raw token string from:
       "Authorization: Bearer <token>"
    2. decode_access_token() verifies signature + expiry
    3. Extract user_id from the payload's "sub" claim
    4. Look up that user in the database
    5. Return the User object — now available in the route as current_user
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # ── Step 1: Decode and verify the token ──────────────────
    payload = decode_access_token(token)
    if payload is None:
        # Covers: invalid signature, malformed token, expired token
        raise credentials_exception

    # ── Step 2: Extract user_id from payload ─────────────────
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    # ── Step 3: Look up the user in the database ─────────────
    user = db.query(User).filter(User.id == int(user_id_str)).first()
    if user is None:
        # Token is valid, but the user was deleted after the token was issued
        raise credentials_exception

    return user