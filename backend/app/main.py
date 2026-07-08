# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401

from app.core.config import settings
from app.db.database import Base, engine
from app.routers import auth, jobs, users, resumes


# ==========================================================
# Create Database Tables
# ==========================================================

Base.metadata.create_all(bind=engine)


# ==========================================================
# FastAPI Application
# ==========================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for AI-powered Job Application Tracking",
)


# ==========================================================
# CORS Configuration
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# Register Routers
# ==========================================================

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(resumes.router)

# ==========================================================
# Routes
# ==========================================================

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }