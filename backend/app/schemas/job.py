# backend/app/schemas/job.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.job import ApplicationStatus


# ─────────────────────────────────────────────────────────────
# JobCreate — Used when adding a new job application
# ─────────────────────────────────────────────────────────────
class JobCreate(BaseModel):
    """Schema for creating a new job application."""

    company_name: str = Field(
        min_length=1,
        max_length=255,
        description="Name of the company",
        examples=["Google"],
    )
    job_title: str = Field(
        min_length=1,
        max_length=255,
        description="The role/position applied for",
        examples=["Backend Developer Intern"],
    )
    job_description: Optional[str] = Field(
        default=None, description="Full job description text"
    )
    job_url: Optional[str] = Field(
        default=None, max_length=500, description="Link to original job posting"
    )
    location: Optional[str] = Field(
        default=None, max_length=255, examples=["Remote", "Bangalore, India"]
    )
    status: ApplicationStatus = Field(
        default=ApplicationStatus.APPLIED,
        description="Current status of this application",
    )
    notes: Optional[str] = Field(default=None, description="Personal notes")


# ─────────────────────────────────────────────────────────────
# JobUpdate — Used when updating an EXISTING job application
# ─────────────────────────────────────────────────────────────
class JobUpdate(BaseModel):
    """Schema for updating an existing job application via PATCH."""

    company_name: Optional[str] = Field(default=None, max_length=255)
    job_title: Optional[str] = Field(default=None, max_length=255)
    job_description: Optional[str] = Field(default=None)
    job_url: Optional[str] = Field(default=None, max_length=500)
    location: Optional[str] = Field(default=None, max_length=255)
    status: Optional[ApplicationStatus] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    interview_date: Optional[datetime] = Field(default=None)
    interview_round: Optional[str] = Field(default=None, max_length=100)


# ─────────────────────────────────────────────────────────────
# JobResponse — What we send BACK to the client
# ─────────────────────────────────────────────────────────────
class JobResponse(BaseModel):
    """Schema for returning job application data to the client."""

    id: int
    user_id: int
    company_name: str
    job_title: str
    job_description: Optional[str] = None
    job_url: Optional[str] = None
    location: Optional[str] = None
    status: ApplicationStatus
    notes: Optional[str] = None
    interview_date: Optional[datetime] = None
    interview_round: Optional[str] = None
    applied_date: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────
# JobStatsResponse — Aggregated counts returned by GET /jobs/stats
# ─────────────────────────────────────────────────────────────
class JobStatsResponse(BaseModel):
    """Per-status application counts for the current user."""

    total: int = 0
    applied: int = 0
    oa_scheduled: int = 0
    interview: int = 0
    rejected: int = 0
    selected: int = 0
