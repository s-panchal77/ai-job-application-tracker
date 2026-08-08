# backend/app/routers/resumes.py

import os

from typing import Optional
from app.schemas.resume_analysis import AnalysisStatusResponse

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
    BackgroundTasks,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.resume import ResumeListResponse, ResumeResponse
from app.services import resume_service
from app.services.auth_service import get_current_user


router = APIRouter(
    prefix="/resumes",
    tags=["Resumes"],
)


# ==========================================================
# Upload Resume
# ==========================================================

@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(
        ...,
        description="PDF resume (max 5 MB)",
    ),
    version_label: str | None = Form(
        default=None,
        description="Optional resume version",
    ),
    job_id: Optional[int] = Form(  # NEW
        default=None,
        description="Optional. If provided, AI match analysis runs in the background against this job.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a resume.
    """

    resume = await resume_service.upload_resume(
        db=db,
        file=file,
        current_user=current_user,
        version_label=version_label,
        job_id=job_id,
    )

    # Schedule the background task — this line does NOT run the task now,
    if job_id is not None:
        background_tasks.add_task(
            resume_service.analyze_resume_background,
            resume.id,
            job_id,
            current_user.id,
        )

    return resume   # sent to client NOW — analysis hasn't started yet

# ==========================================================
# Get Resume Analysis
# ==========================================================

@router.get(
    "/{resume_id}/analysis",
    response_model=AnalysisStatusResponse,
    status_code=status.HTTP_200_OK,
)
def get_resume_analysis(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # 🔒 Protected
):
    return resume_service.get_analysis_status(db, resume_id, current_user)

# ==========================================================
# List Resumes
# ==========================================================

@router.get(
    "/",
    response_model=ResumeListResponse,
    status_code=status.HTTP_200_OK,
)
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all resumes of the current user.
    """

    return resume_service.get_all_resumes(
        db,
        current_user,
    )


# ==========================================================
# Get Resume
# ==========================================================

@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    status_code=status.HTTP_200_OK,
)
def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a single resume.
    """

    return resume_service.get_resume_by_id(
        db,
        resume_id,
        current_user,
    )


# ==========================================================
# Download Resume
# ==========================================================

@router.get(
    "/{resume_id}/download",
    status_code=status.HTTP_200_OK,
)
def download_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download a resume PDF.
    """

    resume = resume_service.get_resume_by_id(
        db,
        resume_id,
        current_user,
    )

    file_path = os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            resume.file_path,
        )
    )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=resume.original_filename,
    )


# ==========================================================
# Set Active Resume
# ==========================================================

@router.patch(
    "/{resume_id}/set-active",
    response_model=ResumeResponse,
    status_code=status.HTTP_200_OK,
)
def set_active_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Set a resume as the active version.
    """

    return resume_service.set_active_resume(
        db,
        resume_id,
        current_user,
    )


# ==========================================================
# Delete Resume
# ==========================================================

@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a resume - both database record and file from disk.
    """

    resume_service.delete_resume(
        db,
        resume_id,
        current_user,
    )

    return None