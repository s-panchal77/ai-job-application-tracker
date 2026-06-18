from datetime import datetime
import enum
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


# ── APPLICATION STATUS ENUM ───────────────────────────────────
class ApplicationStatus(str, enum.Enum):
    """
    Valid statuses for a job application.
    """
    APPLIED = "Applied"
    OA_SCHEDULED = "OA Scheduled"
    INTERVIEW = "Interview"
    REJECTED = "Rejected"
    SELECTED = "Selected"


class JobApplication(Base):
    """
    Represents the 'job_applications' table in PostgreSQL.
    """

    __tablename__ = "job_applications"

    # ── Primary Key ───────────────────────────────────────────
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    # ── Foreign Key ───────────────────────────────────────────
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Job Details ───────────────────────────────────────────
    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    job_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Optional[...] fields automatically evaluate to nullable=True
    job_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    job_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # ── Application Status ────────────────────────────────────
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus),
        default=ApplicationStatus.APPLIED,
        nullable=False,
    )

    # ── Notes ─────────────────────────────────────────────────
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # ── Interview Info ────────────────────────────────────────
    interview_date: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )

    interview_round: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # ── Timestamps ────────────────────────────────────────────
    applied_date: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationship ──────────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User",
        back_populates="job_applications",
    )

    def __repr__(self) -> str:
        return f"<JobApplication id={self.id} company={self.company_name} status={self.status}>"
