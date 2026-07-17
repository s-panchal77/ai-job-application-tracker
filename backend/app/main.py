# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.db.database import engine, Base
from app.routers import users, auth, jobs, resumes, ai    # ai added

import app.models  # noqa: F401


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for AI-powered Job Application Tracking",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
app.mount(
    "/static",
    StaticFiles(directory=os.path.normpath(UPLOAD_DIR)),
    name="static",
)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(resumes.router)
app.include_router(ai.router)    # ai added


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
    return {"status": "healthy"}