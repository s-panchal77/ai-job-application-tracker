from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    """
    Represents the 'users' table in PostgreSQL using modern SQLAlchemy 2.0 syntax.
    """

    __tablename__ = "users"

    # ── Columns ──────────────────────────────────────────────
    id: Mapped[int] = mapped_column(
        primary_key=True, 
        index=True
    )
    
    email: Mapped[str] = mapped_column(
        String, 
        unique=True, 
        index=True, 
        nullable=False
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String, 
        nullable=False
    )
    
    # Optional[] automatically maps to nullable=True in the database
    full_name: Mapped[Optional[str]] = mapped_column(
        String, 
        nullable=True
    )
    
    is_active: Mapped[bool] = mapped_column(
        default=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

    # ── Relationships ─────────────────────────────────────────
    # Fully-typed list relationship. Python now knows user.job_applications is a list.
    job_applications: Mapped[List["JobApplication"]] = relationship(
        "JobApplication",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    resumes: Mapped[List["Resume"]] = relationship(
        "Resume",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation — helpful for debugging in terminal."""
        return f"<User id={self.id} email={self.email}>"
