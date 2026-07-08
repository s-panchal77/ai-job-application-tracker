# backend/app/services/resume_service.py

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import not_found_exception
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import ResumeListResponse
from app.utils.file_utils import (
    delete_file_from_disk,
    generate_unique_filename,
    save_file_to_disk,
    validate_pdf_file,
)


# ==========================================================
# Helper Function
# ==========================================================

def _get_resume_owned_by_user(
    db: Session,
    resume_id: int,
    current_user: User,
) -> Resume:
    """
    Fetch a resume and ensure it belongs to the current user.
    """

    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id)
        .first()
    )

    if not resume or resume.user_id != current_user.id:
        raise not_found_exception("Resume", resume_id)

    return resume


# ==========================================================
# Upload Resume
# ==========================================================

async def upload_resume(
    db: Session,
    file: UploadFile,
    current_user: User,
    version_label: str | None = None,
) -> Resume:
    """
    Upload a resume and make it the active version.
    """

    contents = await validate_pdf_file(file)

    stored_filename = generate_unique_filename(
        current_user.id,
        file.filename,
    )

    file_path = save_file_to_disk(
        contents,
        stored_filename,
    )

    # Deactivate previous active resume
    (
        db.query(Resume)
        .filter(
            Resume.user_id == current_user.id,
            Resume.is_active == True,   # noqa: E712
        )
        .update({"is_active": False})
    )

    resume = Resume(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_size=len(contents),
        version_label=version_label,
        is_active=True,
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return resume


# ==========================================================
# Get All Resumes
# ==========================================================

def get_all_resumes(
    db: Session,
    current_user: User,
) -> ResumeListResponse:
    """
    Return all resumes of the current user.
    """

    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .all()
    )

    return ResumeListResponse(
        total=len(resumes),
        resumes=resumes,
    )


# ==========================================================
# Get Resume
# ==========================================================

def get_resume_by_id(
    db: Session,
    resume_id: int,
    current_user: User,
) -> Resume:
    """
    Return a single resume.
    """

    return _get_resume_owned_by_user(
        db,
        resume_id,
        current_user,
    )


# ==========================================================
# Set Active Resume
# ==========================================================

def set_active_resume(
    db: Session,
    resume_id: int,
    current_user: User,
) -> Resume:
    """
    Set a resume as the active version.
    """

    resume = _get_resume_owned_by_user(
        db,
        resume_id,
        current_user,
    )

    (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .update({"is_active": False})
    )

    resume.is_active = True

    db.commit()
    db.refresh(resume)

    return resume


# ==========================================================
# Delete Resume
# ==========================================================

def delete_resume(
    db: Session,
    resume_id: int,
    current_user: User,
) -> None:
    """
    Delete a resume and its file.
    """

    resume = _get_resume_owned_by_user(
        db,
        resume_id,
        current_user,
    )

    file_path = resume.file_path

    db.delete(resume)
    db.commit()

    delete_file_from_disk(file_path)