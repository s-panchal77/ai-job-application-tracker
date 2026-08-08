# backend/app/services/resume_service.py

from datetime import datetime, timezone

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.db.database import SessionLocal

from app.core.exceptions import (
    not_found_exception,
    bad_request_exception,
)

from app.models.user import User
from app.models.resume import Resume
from app.models.job import JobApplication
from app.models.resume_analysis import ResumeAnalysis, AnalysisStatus

from app.schemas.resume import ResumeListResponse

from app.services.ai_service import get_ai_analysis

from app.utils.pdf_utils import extract_text_from_pdf

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
    job_id: int | None = None,
) -> Resume:
    """
    If job_id is provided, we validate it BEFORE touching the disk —
    fail fast on a bad job_id rather than saving a file and then erroring.
    A pending ResumeAnalysis row is created after the Resume is saved;
    the router schedules the actual AI work as a background task.
    """

    if job_id is not None:
        job = db.query(JobApplication).filter(JobApplication.id == job_id).first()
        if not job or job.user_id != current_user.id:
            raise not_found_exception("Job", job_id)
        if not job.job_description:
            raise bad_request_exception(
                "This job application has no job description saved. "
                "Add one before requesting analysis."
            )

    contents = await validate_pdf_file(file)
    stored_filename = generate_unique_filename(current_user.id, file.filename)
    file_path = save_file_to_disk(contents, stored_filename)

    (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id, Resume.is_active == True)  # noqa: E712
        .update({"is_active": False})
    )

    new_resume = Resume(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_size=len(contents),
        version_label=version_label,
        is_active=True,
    )

    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)

    # ── NEW: create the pending analysis row ──────────────────
    if job_id is not None:
        pending_analysis = ResumeAnalysis(
            resume_id=new_resume.id,
            job_id=job_id,
            status=AnalysisStatus.PENDING,
        )
        db.add(pending_analysis)
        db.commit()

    return new_resume


# ==========================================================
# Get All Resumes
# ==========================================================

def get_all_resumes(
    db: Session,
    current_user: User,
) -> ResumeListResponse:
    # Return all resumes of the current user.

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

    resume = _get_resume_owned_by_user(
        db,
        resume_id,
        current_user,
    )

    file_path = resume.file_path

    db.delete(resume)
    db.commit()

    delete_file_from_disk(file_path)

# ==========================================================
# Background Task
# ==========================================================

async def analyze_resume_background(resume_id: int, job_id: int, user_id: int) -> None:
    """
    Runs AI analysis after the upload response is sent.

    Opens a new database session because the request session
    is already closed. Updates analysis status to completed
    or failed and stores the result.
    """
    db = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        analysis = (
            db.query(ResumeAnalysis)
            .filter(ResumeAnalysis.resume_id == resume_id)
            .first()
        )

        # Resume or analysis record no longer exists
        if not resume or not analysis:
            return

        job = db.query(JobApplication).filter(JobApplication.id == job_id).first()

        # Job was deleted
        if not job:
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = "Associated job application not found."
            db.commit()
            return

        try:
            # Extract resume text and run AI analysis
            resume_text = extract_text_from_pdf(resume.file_path)
            result = await get_ai_analysis(resume_text, job.job_description)

            analysis.status = AnalysisStatus.COMPLETED
            analysis.match_score = result.get("match_score")
            analysis.matched_skills = result.get("matched_skills")
            analysis.missing_skills = result.get("missing_skills")
            analysis.suggestions = result.get("suggestions")
            analysis.analyzed_at = datetime.now(timezone.utc)
            analysis.error_message = None

        except HTTPException as e:
            # Known AI/PDF processing error
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(e.detail)

        except Exception as e:
            # Unexpected error
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = f"Unexpected error: {str(e)}"

        db.commit()

    finally:
        # Always close database connection
        db.close()


# ==========================================================
# Get Analysis Result
# ==========================================================

def get_analysis_status(
    db: Session,
    resume_id: int,
    current_user: User
) -> ResumeAnalysis:
    """
    Returns analysis status/result for a resume.
    Ensures the resume belongs to the current user.
    """

    # Ownership check
    get_resume_by_id(db, resume_id, current_user)

    analysis = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.resume_id == resume_id)
        .first()
    )

    if not analysis:
        raise not_found_exception("Analysis", resume_id)

    return analysis