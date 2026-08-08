# backend/app/models/resume_analysis.py

import enum
from typing import Optional, List, Any

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class AnalysisStatus(str, enum.Enum):
    """
    Possible states for a background resume analysis job.
    """
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ResumeAnalysis(Base):
    """
    One-to-one analysis result for a Resume.

    - Created immediately when a resume is uploaded with a job_id (status=PENDING).
    - Updated asynchronously by a background task:
        * status=COMPLETED → match_score, matched_skills, missing_skills, suggestions filled.
        * status=FAILED → error_message filled.

    Because each new upload creates a new Resume row (versioning), this model
    automatically keeps a full history of all analyses – no separate history table needed.
    """
    __tablename__ = "resume_analyses"

    # ─── Primary key ────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)

    # ─── Foreign keys (one-to-one with Resume, one-to-many with Job) ──
    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,        # enforces one-to-one
        index=True,
    )
    job_id = Column(
        Integer,
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ─── Status and result fields ──────────────────────────────────────
    status = Column(
        Enum(AnalysisStatus),
        default=AnalysisStatus.PENDING,
        nullable=False,
    )

    # Only filled when status == COMPLETED
    match_score = Column(Integer, nullable=True)
    matched_skills = Column(JSON, nullable=True)   # list of strings
    missing_skills = Column(JSON, nullable=True)   # list of strings
    suggestions = Column(JSON, nullable=True)      # list of strings

    # Only filled when status == FAILED
    error_message = Column(Text, nullable=True)

    # ─── Timestamps ────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)   # set when analysis finishes

    # ─── Relationships ─────────────────────────────────────────────────
    resume = relationship("Resume", back_populates="analysis")

    # ─── String representation ────────────────────────────────────────
    def __repr__(self) -> str:
        return f"<ResumeAnalysis id={self.id} resume_id={self.resume_id} status={self.status}>"