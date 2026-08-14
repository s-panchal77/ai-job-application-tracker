# backend/app/schemas/__init__.py

# Central import point for all schemas.
# Lets us write: from app.schemas import UserCreate
# instead of: from app.schemas.user import UserCreate

from app.schemas.job import JobCreate, JobResponse, JobUpdate
from app.schemas.user import UserCreate, UserLogin, UserResponse
