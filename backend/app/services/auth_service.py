# backend/app/services/auth_service.py

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import credentials_exception, unauthorized_exception
from app.core.security import (create_access_token, decode_access_token,
                               verify_password)
from app.db.database import get_db
from app.models.user import User

# ↑ Both auth-related exceptions now come from one place


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ─────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────
def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Verifies email and password.
    Raises 401 if either is wrong — same message for both cases
    to prevent user enumeration attacks.
    """
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        # BEFORE: raise HTTPException(status_code=401, detail="Incorrect email or password", headers=...)
        # AFTER:
        raise unauthorized_exception()

    return user


def login_for_access_token(db: Session, email: str, password: str) -> str:
    """
    Authenticates user and returns a signed JWT access token.
    """
    user = authenticate_user(db, email, password)
    access_token = create_access_token(data={"sub": str(user.id)})
    return access_token


# ─────────────────────────────────────────────────────────────
# PROTECTED ROUTE DEPENDENCY
# ─────────────────────────────────────────────────────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency for protected routes.
    Verifies the JWT from Authorization header and returns the User.

    Usage in any protected route:
        current_user: User = Depends(get_current_user)
    """

    # Step 1: Decode and verify the token
    payload = decode_access_token(token)
    if payload is None:
        # BEFORE: raise HTTPException(status_code=401, detail="Could not validate credentials", headers=...)
        # AFTER:
        raise credentials_exception()

    # Step 2: Extract user_id from payload
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception()

    # Step 3: Load user from database
    user = db.query(User).filter(User.id == int(user_id_str)).first()
    if user is None:
        raise credentials_exception()

    return user
