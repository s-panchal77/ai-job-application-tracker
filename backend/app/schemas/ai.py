# backend/app/schemas/ai.py

from pydantic import BaseModel, Field
from typing import Optional


# ─────────────────────────────────────────────────────────────
# REQUEST
# ─────────────────────────────────────────────────────────────
class AIMatchRequest(BaseModel):
    """
    Request body for POST /ai/match

    job_id     → which job application's description to match against
    resume_id  → which resume to use (optional — defaults to your active resume)
    """
    job_id: int = Field(..., description="ID of the job application to match against")
    resume_id: Optional[int] = Field(
        default=None,
        description="ID of the resume to use. If omitted, your active resume is used.",
    )


# ─────────────────────────────────────────────────────────────
# RESPONSE
# ─────────────────────────────────────────────────────────────
class AIMatchResponse(BaseModel):
    """
    Response body for POST /ai/match

    This is the SAME shape regardless of whether the mock or
    real OpenAI provider generated it — that consistency is
    the entire point of the interface pattern.
    """
    match_score: int = Field(..., ge=0, le=100, description="Match score from 0-100")
    matched_skills: list[str] = Field(default_factory=list, description="Skills found in both resume and JD")
    missing_skills: list[str] = Field(default_factory=list, description="Skills in the JD but missing from the resume")
    suggestions: list[str] = Field(default_factory=list, description="Actionable improvement suggestions")
    provider: str = Field(..., description="Which AI provider generated this result: 'mock' or 'openai'")