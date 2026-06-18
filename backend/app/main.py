from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import engine, Base
import app.models  # Registers models into Base metadata

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.db.database import get_db

# ─────────────────────────────────────────────
# LIFESPAN (STARTUP / SHUTDOWN) EVENTS
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables automatically if they don't exist
    # (Note: In a team environment, you'll eventually switch this to Alembic migrations)
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic goes here if needed (e.g., closing connection pools)


# ─────────────────────────────────────────────
# CREATE THE FASTAPI APPLICATION
# ─────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for AI-powered Job Application Tracking",
    lifespan=lifespan,  # Connect the database table creation lifecycle
)


# ─────────────────────────────────────────────
# CORS MIDDLEWARE
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],     
    allow_headers=["*"],     
)


# ─────────────────────────────────────────────
# ROOT ROUTE — Quick health check
# ─────────────────────────────────────────────
@app.get("/")
def root():
    """
    Root endpoint.
    Used to verify the server is running.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


# ─────────────────────────────────────────────
# HEALTH CHECK ROUTE
# ─────────────────────────────────────────────
@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


# ─────────────────────────────────────────────────────────────
# DATABASE TEST ROUTE
# ─────────────────────────────────────────────────────────────
@app.get("/test-db")
def test_database_connection(db: Session = Depends(get_db)):
    """
    Test endpoint to verify the PostgreSQL connection is active
    and executing queries successfully.
    """
    try:
        # Run a simple query to see if the database responds
        db.execute(text("SELECT 1"))
        
        return {
            "database": "connected",
            "tables_created": True,
            "message": "PostgreSQL is working correctly!"
        }
    except Exception as e:
        # If something is wrong (bad password, db down), return a 500 error
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )
