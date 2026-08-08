# backend/app/models/resume.py

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Resume(Base):
    """
    Resume uploaded by a user.
    Stores file information and supports resume versioning.
    """

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)

    # Owner
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File Information
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)

    # Version Information
    version_label = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)

    # Upload Time
    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    user = relationship("User", back_populates="resumes")
    analysis = relationship("ResumeAnalysis", back_populates="resume", uselist=False)
    
    def __repr__(self):
        return (
            f"<Resume(id={self.id}, "
            f"user_id={self.user_id}, "
            f"file='{self.stored_filename}')>"
        )