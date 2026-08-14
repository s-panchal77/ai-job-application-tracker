# backend/app/schemas/resume_analysis.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AnalysisStatusResponse(BaseModel):
    """
    Response for GET /resumes/{resume_id}/analysis

    Fields other than resume_id/job_id/status are None until the
    background task finishes (or if it failed, only error_message
    is populated).
    """

    resume_id: int
    job_id: int
    status: str  # "pending" | "completed" | "failed"
    match_score: Optional[int] = None
    matched_skills: Optional[list[str]] = None
    missing_skills: Optional[list[str]] = None
    suggestions: Optional[list[str]] = None
    error_message: Optional[str] = None
    analyzed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
