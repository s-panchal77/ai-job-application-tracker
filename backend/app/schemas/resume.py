# backend/app/schemas/resume.py

from datetime import datetime

from pydantic import BaseModel


# ==========================================================
# Response Schema
# ==========================================================

class ResumeResponse(BaseModel):
    """
    Resume information returned to the client.
    """

    id: int
    user_id: int
    original_filename: str
    file_size: int
    version_label: str | None = None
    is_active: bool
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ==========================================================
# List Response Schema
# ==========================================================

class ResumeListResponse(BaseModel):
    """
    Response for listing all resumes.
    """

    total: int
    resumes: list[ResumeResponse]