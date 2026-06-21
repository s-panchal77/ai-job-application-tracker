# backend/app/core/security.py

from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.core.config import settings


# ─────────────────────────────────────────────────────────────
# PASSWORD HASHING SETUP
# ─────────────────────────────────────────────────────────────
# CryptContext manages which hashing algorithm(s) we use.
# "bcrypt" is the scheme — industry standard for password hashing.
# deprecated="auto" means: if we ever change schemes later,
# passlib automatically flags old hashes for re-hashing on next login.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Converts a plain text password into a bcrypt hash.
    This is a ONE-WAY operation — there is no way to reverse it.

    Example:
        hash_password("SecurePass123")
        → "$2b$12$KIXxPfZ9wZ3v..../some.long.hash.string"
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain text password matches a stored bcrypt hash.

    Used during login: we never decrypt the stored hash —
    instead we hash the INPUT and let bcrypt compare them safely.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ─────────────────────────────────────────────────────────────
# JWT TOKEN CREATION
# ─────────────────────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    """
    Creates a signed JWT access token.

    'data' is the payload — typically {"sub": str(user.id)}
    'sub' (subject) is the JWT-standard claim name for "who this token is about"

    We add an 'exp' (expiry) claim automatically.
    """
    to_encode = data.copy()

    # Calculate expiry timestamp
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})

    # jwt.encode() creates the actual signed token string
    # Uses our SECRET_KEY and ALGORITHM (HS256) from settings
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


# ─────────────────────────────────────────────────────────────
# JWT TOKEN VERIFICATION
# ─────────────────────────────────────────────────────────────
def decode_access_token(token: str) -> dict | None:
    """
    Verifies a JWT's signature and decodes its payload.

    Returns the payload dict if valid.
    Returns None if the token is invalid, tampered with, or expired —
    jwt.decode() raises JWTError in all those cases, which we catch.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        # Covers: invalid signature, malformed token, AND expired token
        # (python-jose checks 'exp' automatically during decode)
        return None