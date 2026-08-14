# backend/app/routers/jobs.py

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.job import ApplicationStatus
from app.models.user import User
from app.schemas.job import JobCreate, JobResponse, JobStatsResponse, JobUpdate
from app.services import job_service
from app.services.auth_service import get_current_user

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


# ==========================================================
# Create Job
# ==========================================================


@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new job application.
    """
    return job_service.create_job(db, job, current_user)


# ==========================================================
# Get All Jobs
# ==========================================================


@router.get(
    "/",
    response_model=list[JobResponse],
    status_code=status.HTTP_200_OK,
)
def list_jobs(
    status: Optional[ApplicationStatus] = Query(
        default=None,
        description="Filter by application status",
    ),
    search: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Search by company or job title",
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Records to skip",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Maximum records to return",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all jobs of the current user.
    """

    return job_service.get_all_jobs(
        db=db,
        current_user=current_user,
        status=status,
        search=search,
        skip=skip,
        limit=limit,
    )


# ==========================================================
# Get Job Stats  (MUST be before /{job_id} to avoid route collision)
# ==========================================================


@router.get(
    "/stats",
    response_model=JobStatsResponse,
    status_code=status.HTTP_200_OK,
)
def get_job_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return per-status application counts for the current user.
    """
    return job_service.get_job_stats(db, current_user)


# ==========================================================
# Get Single Job
# ==========================================================


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a job by its ID.
    """

    return job_service.get_job_by_id(
        db,
        job_id,
        current_user,
    )


# ==========================================================
# Update Job
# ==========================================================


@router.patch(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
)
def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a job application.
    """

    return job_service.update_job(
        db,
        job_id,
        job_data,
        current_user,
    )


# ==========================================================
# Delete Job
# ==========================================================


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a job application.
    """

    job_service.delete_job(
        db,
        job_id,
        current_user,
    )

    return None
