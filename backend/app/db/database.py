from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# STEP 1: CREATE ENGINE
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
)

# STEP 2: CREATE SESSION FACTORY
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# STEP 3: MODERN DECLARATIVE BASE (SQLAlchemy 2.0+)
class Base(DeclarativeBase):
    """
    Parent class for all database models.
    Replaces the deprecated declarative_base().
    """

    pass


# DATABASE DEPENDENCY
def get_db():
    """
    Yields a database session per request and guarantees cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Guaranteed to execute, preventing connection leaks.
