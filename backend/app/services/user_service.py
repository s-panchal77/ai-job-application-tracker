# backend/app/services/user_service.py

from sqlalchemy.orm import Session

from app.core.exceptions import bad_request_exception, not_found_exception
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


# ─────────────────────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────────────────────
def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Creates a new user.
    Raises 400 if email already exists.
    """
    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        # BEFORE: raise HTTPException(status_code=400, detail="A user with this email already exists")
        # AFTER:  clean, readable, consistent
        raise bad_request_exception("A user with this email already exists")

    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ─────────────────────────────────────────────────────────────
# READ — single user
# ─────────────────────────────────────────────────────────────
def get_user_by_id(db: Session, user_id: int) -> User:
    """
    Fetches a single user by ID.
    Raises 404 if not found.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        # BEFORE: raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
        # AFTER:
        raise not_found_exception("User", user_id)

    return user


# ─────────────────────────────────────────────────────────────
# READ — all users with pagination
# ─────────────────────────────────────────────────────────────
def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """
    Returns paginated list of all users.
    """
    return db.query(User).offset(skip).limit(limit).all()


# ─────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────
def update_user(db: Session, user_id: int, full_name: str | None) -> User:
    """
    Updates a user's full name.
    Raises 404 if user not found (via get_user_by_id).
    """
    user = get_user_by_id(db, user_id)  # 404 handled inside here

    if full_name is not None:
        user.full_name = full_name

    db.commit()
    db.refresh(user)

    return user


# ─────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────
def delete_user(db: Session, user_id: int) -> None:
    """
    Deletes a user permanently.
    Raises 404 if user not found (via get_user_by_id).
    """
    user = get_user_by_id(db, user_id)  # 404 handled inside here

    db.delete(user)
    db.commit()
