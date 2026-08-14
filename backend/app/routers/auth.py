# backend/app/routers/auth.py

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse
from app.services import auth_service, user_service

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ─────────────────────────────────────────────────────────────
# REGISTER — POST /auth/register
# ─────────────────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.

    This reuses the SAME service function we built in Phase 4 —
    we didn't duplicate logic, we just moved password hashing
    into it (Step 3 above).
    """
    return user_service.create_user(db, user)


# ─────────────────────────────────────────────────────────────
# LOGIN — POST /auth/login
# ─────────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and issue a JWT access token.

    WHY OAuth2PasswordRequestForm instead of our own schema?
    -----------------------------------------------------------
    This is a FastAPI-provided dependency that expects data in
    'application/x-www-form-urlencoded' format with fields
    'username' and 'password' — NOT JSON.

    This isn't just a style choice — it's the OAuth2 spec standard,
    and it's REQUIRED for Swagger UI's "Authorize" button to work
    correctly out of the box. The form's 'username' field is where
    we put the user's email.
    """
    access_token = auth_service.login_for_access_token(
        db=db,
        email=form_data.username,  # OAuth2 spec calls it "username", we treat it as email
        password=form_data.password,
    )

    return Token(access_token=access_token, token_type="bearer")


# ─────────────────────────────────────────────────────────────
# GET CURRENT USER — GET /auth/me  (a protected route example)
# ─────────────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_me(current_user=Depends(auth_service.get_current_user)):
    """
    Returns the currently logged-in user's data.

    This route PROVES authentication is working:
    - No token / invalid token → 401, this code never runs
    - Valid token → current_user is the actual User object from DB

    This is also the pattern EVERY future protected route will follow.
    """
    return current_user
