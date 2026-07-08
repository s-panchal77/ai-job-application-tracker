# backend/app/routers/resumes.py

import os

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
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
    file: UploadFile = File(
        ...,
        description="PDF resume (max 5 MB)",
    ),
    version_label: str | None = Form(
        default=None,
        description="Optional resume version",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a resume.
    """

    return await resume_service.upload_resume(
        db=db,
        file=file,
        current_user=current_user,
        version_label=version_label,
    )


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