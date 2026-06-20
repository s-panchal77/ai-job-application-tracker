# backend/app/routers/users.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services import user_service


# ─────────────────────────────────────────────────────────────
# APIRouter — a "mini FastAPI app" that we plug into main.py
# ─────────────────────────────────────────────────────────────
# prefix="/users" means every route below is actually
# /users/, /users/{id}, etc. — we don't repeat "/users" each time
#
# tags=["Users"] groups these routes together in Swagger docs (/docs)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# ─────────────────────────────────────────────────────────────
# CREATE — POST /users/
# ─────────────────────────────────────────────────────────────
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user entry."""
    return user_service.create_user(db, user)


# ─────────────────────────────────────────────────────────────
# READ — GET /users/{user_id}
# ─────────────────────────────────────────────────────────────
@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Fetch a single user profile by ID."""
    return user_service.get_user_by_id(db, user_id)


# ─────────────────────────────────────────────────────────────
# LIST — GET /users/
# ─────────────────────────────────────────────────────────────
@router.get("/", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List users with support for pagination bounds."""
    return user_service.get_all_users(db, skip, limit)


# ─────────────────────────────────────────────────────────────
# UPDATE — PATCH /users/{user_id}
# ─────────────────────────────────────────────────────────────
@router.patch("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def update_user(user_id: int, full_name: str | None = None, db: Session = Depends(get_db)):
    """Partially update a user's full name."""
    return user_service.update_user(db, user_id, full_name)


# ─────────────────────────────────────────────────────────────
# DELETE — DELETE /users/{user_id}
# ─────────────────────────────────────────────────────────────
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Permanently delete an existing user account."""
    user_service.delete_user(db, user_id)
    return None
