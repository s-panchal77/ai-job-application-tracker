# backend/app/services/job_service.py

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import not_found_exception
from app.models.job import ApplicationStatus, JobApplication
from app.models.user import User
from app.schemas.job import JobCreate, JobUpdate


# ==========================================================
# Helper Function
# ==========================================================

def _get_job_owned_by_user(
    db: Session,
    job_id: int,
    current_user: User,
) -> JobApplication:
    """
    Fetch a job and ensure it belongs to the current user.
    Returns 404 if the job doesn't exist or isn't owned by the user.
    """

    job = (
        db.query(JobApplication)
        .filter(JobApplication.id == job_id)
        .first()
    )

    if not job or job.user_id != current_user.id:
        raise not_found_exception("Job", job_id)

    return job


# ==========================================================
# Create Job
# ==========================================================

def create_job(
    db: Session,
    job_data: JobCreate,
    current_user: User,
) -> JobApplication:
    """
    Create a new job application.
    """

    job = JobApplication(
        user_id=current_user.id,
        company_name=job_data.company_name,
        job_title=job_data.job_title,
        job_description=job_data.job_description,
        job_url=job_data.job_url,
        location=job_data.location,
        status=job_data.status,
        notes=job_data.notes,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


# ==========================================================
# Get Single Job
# ==========================================================

def get_job_by_id(
    db: Session,
    job_id: int,
    current_user: User,
) -> JobApplication:
    """
    Return one job by ID.
    """

    return _get_job_owned_by_user(db, job_id, current_user)


# ==========================================================
# Get All Jobs
# ==========================================================

def get_all_jobs(
    db: Session,
    current_user: User,
    status: ApplicationStatus | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[JobApplication]:
    """
    Return all jobs of the current user with
    optional filtering, searching, and pagination.
    """

    query = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    )

    # Filter by application status
    if status:
        query = query.filter(JobApplication.status == status)

    # Search by company name or job title
    if search:
        search_text = f"%{search}%"

        query = query.filter(
            or_(
                JobApplication.company_name.ilike(search_text),
                JobApplication.job_title.ilike(search_text),
            )
        )

    return (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )


# ==========================================================
# Update Job
# ==========================================================

def update_job(
    db: Session,
    job_id: int,
    job_data: JobUpdate,
    current_user: User,
) -> JobApplication:
    """
    Update only the fields sent by the client.
    """

    job = _get_job_owned_by_user(db, job_id, current_user)

    update_data = job_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)

    return job


# ==========================================================
# Delete Job
# ==========================================================

def delete_job(
    db: Session,
    job_id: int,
    current_user: User,
) -> None:
    """
    Delete a job application.
    """

    job = _get_job_owned_by_user(db, job_id, current_user)

    db.delete(job)
    db.commit()


# ==========================================================
# Job Stats
# ==========================================================

def get_job_stats(
    db: Session,
    current_user: User,
) -> dict:
    """
    Return per-status counts for all job applications
    belonging to the current user.
    """
    from sqlalchemy import func

    rows = (
        db.query(
            JobApplication.status,
            func.count(JobApplication.id).label("count"),
        )
        .filter(JobApplication.user_id == current_user.id)
        .group_by(JobApplication.status)
        .all()
    )

    # Build a mapping from status value → count
    status_map = {row.status: row.count for row in rows}

    total = sum(status_map.values())

    return {
        "total": total,
        "applied": status_map.get(ApplicationStatus.APPLIED, 0),
        "oa_scheduled": status_map.get(ApplicationStatus.OA_SCHEDULED, 0),
        "interview": status_map.get(ApplicationStatus.INTERVIEW, 0),
        "rejected": status_map.get(ApplicationStatus.REJECTED, 0),
        "selected": status_map.get(ApplicationStatus.SELECTED, 0),
    }