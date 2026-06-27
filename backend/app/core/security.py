# backend/app/core/security.py

from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─────────────────────────────────────────────────────────────
# PASSWORD HASHING
# ─────────────────────────────────────────────────────────────
def hash_password(plain_password: str) -> str:
    """Hashes a plain text password using bcrypt. One-way — cannot be reversed."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Returns True if plain_password matches the stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

# ─────────────────────────────────────────────────────────────
# JWT TOKEN CREATION
# ─────────────────────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    """
    Creates a signed JWT token.
    Adds expiry claim automatically from settings.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# ─────────────────────────────────────────────────────────────
# JWT TOKEN VERIFICATION
# ─────────────────────────────────────────────────────────────
def decode_access_token(token: str) -> dict | None:
    """
    Verifies token signature and expiry, returns payload if valid.
    Returns None for any failure — invalid, tampered, or expired.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None