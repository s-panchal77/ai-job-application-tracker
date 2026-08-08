# backend/app/models/__init__.py

# Import all models here so SQLAlchemy's Base knows about them.
# If you skip this, create_all() won't create the tables.
#
# Think of this as a "model registry" — every model must be listed here.

from app.models.user import User
from app.models.job import JobApplication
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis

# When new models are created (resume, interview, etc.),
# add their imports here too.