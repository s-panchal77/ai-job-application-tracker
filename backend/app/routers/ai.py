# backend/app/routers/ai.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.ai import AIMatchRequest, AIMatchResponse
from app.services import ai_service
from app.services.auth_service import get_current_user


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@router.post(
    "/match",
    response_model=AIMatchResponse,
    status_code=status.HTTP_200_OK,
)
async def match_resume(
    request: AIMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # 🔒 Protected
):
    """
    Analyze how well a resume matches a job description.

    🔒 Requires authentication.

    Request body:
    - job_id: which job application to match against (required)
    - resume_id: which resume to use (optional — uses your active resume if omitted)

    The actual AI provider used depends on the AI_PROVIDER setting
    in your .env file:
    - "mock"   → instant, free, keyword-based fake analysis (default)
    - "openai" → real analysis via OpenAI API (requires OPENAI_API_KEY)

    Both providers return the exact same response shape.
    """
    return await ai_service.match_resume_to_job(
        db=db,
        job_id=request.job_id,
        resume_id=request.resume_id,
        current_user=current_user,
    )