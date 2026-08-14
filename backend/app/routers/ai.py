# backend/app/routers/ai.py
# NO CHANGES FROM PHASE 9 — shown for reference only

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.ai import AIMatchRequest, AIMatchResponse
from app.services import ai_service
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/match", response_model=AIMatchResponse, status_code=status.HTTP_200_OK)
async def match_resume(
    request: AIMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze resume-to-job match. Provider (mock/openai) is decided
    entirely inside ai_service — this router has zero knowledge of it.
    """
    return await ai_service.match_resume_to_job(
        db=db,
        job_id=request.job_id,
        resume_id=request.resume_id,
        current_user=current_user,
    )
