# backend/app/services/user_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate


# ─────────────────────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────────────────────
def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user if the email does not already exist."""
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    new_user = User(
        email=user_data.email,
        hashed_password=user_data.password,
        full_name=user_data.full_name,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ─────────────────────────────────────────────────────────────
# READ — Get one user by ID
# ─────────────────────────────────────────────────────────────
def get_user_by_id(db: Session, user_id: int) -> User:
    """Fetch a single user by ID or raise a 404 error."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )
    return user


# ─────────────────────────────────────────────────────────────
# READ — Get all users (with pagination)
# ─────────────────────────────────────────────────────────────
def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """Fetch a paginated list of users."""
    return db.query(User).offset(skip).limit(limit).all()


# ─────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────
def update_user(db: Session, user_id: int, full_name: str | None) -> User:
    """Update an existing user's full name."""
    user = get_user_by_id(db, user_id)
    if full_name is not None:
        user.full_name = full_name

    db.commit()
    db.refresh(user)
    return user


# ─────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────
def delete_user(db: Session, user_id: int) -> None:
    """Delete a user permanently from the database."""
    user = get_user_by_id(db, user_id)
    db.delete(user)
    db.commit()
