<div align="center">

# 🤖 AI Job Application Tracker

**A production-grade, full-stack web application to track job applications, manage resumes, and get AI-powered resume-to-job match analysis.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini_AI-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

[Features](#-features) • [Tech Stack](#-tech-stack) • [Architecture](#-system-architecture) • [Quickstart](#-quickstart) • [Docker Setup](#-docker-setup) • [API Reference](#-api-reference) • [Environment Variables](#-environment-variables)

</div>

---

## 📌 Overview

The **AI Job Application Tracker** is a full-stack application that solves a real problem for job seekers: keeping track of dozens of applications, resumes, and interview rounds — all in one place.

The standout feature is **AI-powered resume analysis**: upload your resume alongside a job description, and the Gemini AI engine returns a **match score**, **matched skills**, **missing skills**, and **actionable improvement suggestions** — instantly.

> Built as a learning-focused, production-quality project covering REST APIs, JWT auth, ORM, PDF processing, async background tasks, AI integration, and Docker containerization.

---

## ✨ Features

### 🔐 Authentication & Security
- Secure user registration and login
- **JWT Bearer Token** authentication (HS256)
- Password hashing with **bcrypt** via Passlib
- Protected routes — both backend (FastAPI `Depends`) and frontend (React `ProtectedRoute`)
- Token-based session management with configurable expiry

### 📋 Job Application Management
- Create, view, update, and delete job applications
- Rich application fields: company, title, location, job URL, job description, notes
- **5 application statuses**: `Applied` → `OA Scheduled` → `Interview` → `Selected` / `Rejected`
- Filter by status and search by company or job title
- Interview scheduling with date and round tracking
- Per-user dashboard statistics (total, pending, selected, rejected counts)

### 📄 Resume Management
- Upload resumes as **PDF files** (up to 5 MB)
- Version labeling to track multiple resume versions
- Set any resume as the **active** resume
- Download resumes directly from the app
- AI match analysis triggered automatically on upload if a `job_id` is provided

### 🤖 AI Resume Matching (Google Gemini)
- **Provider-agnostic architecture** — swap between `mock` and `gemini` via a single `.env` variable
- **Mock Provider**: Instant keyword-based analysis — no API key needed, great for development
- **Gemini Provider**: Real AI analysis via Google Gemini REST API
- Returns structured JSON: match score (0–100), matched skills, missing skills, and suggestions
- Background task processing — upload returns immediately; analysis runs asynchronously
- Full async error handling: timeout, connection errors, invalid API key, rate limits

### 📊 Dashboard Analytics

| Metric | Description |
|--------|-------------|
| Total Applications | All job applications created by the user |
| Applied | Applications submitted, awaiting response |
| Interviews Scheduled | Active interview pipeline |
| Selected | Offers received |
| Rejected | Applications closed |
| Active Resume | Currently active resume version |

---

## Screenshots

### Login

![Login](assets/login.png)

---

### Dashboard

![Dashboard](assets/dashboard.png)

---

### Swagger API

![Swagger](assets/swagger.png)

---

## 🛠 Tech Stack

### Backend

| Technology | Version | Purpose |
|---|---|---|
| **FastAPI** | 0.111.0 | REST API framework |
| **SQLAlchemy** | 2.0.30 | ORM & database abstraction |
| **PostgreSQL** | 16 | Relational database |
| **Alembic** | 1.13.1 | Database migrations |
| **Pydantic v2** | 2.7.1 | Data validation & settings |
| **python-jose** | 3.3.0 | JWT token generation & verification |
| **Passlib + bcrypt** | 1.7.4 | Password hashing |
| **pypdf** | 4.2.0 | PDF text extraction |
| **httpx** | 0.27.0 | Async HTTP client for AI API calls |
| **Uvicorn** | 0.29.0 | ASGI server |

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| **React** | 18.3.1 | UI library |
| **React Router DOM** | 6.26.0 | Client-side routing |
| **Axios** | 1.7.4 | HTTP client |
| **Tailwind CSS** | 3.4.7 | Utility-first styling |
| **Vite** | 5.3.4 | Build tool & dev server |

### DevOps & Infrastructure

| Technology | Purpose |
|---|---|
| **Docker** | Container runtime |
| **Docker Compose** | Multi-container orchestration |
| **Nginx** | Frontend static file serving & reverse proxy |
| **Docker Volumes** | Persistent storage for DB and uploaded files |

### AI

| Provider | Mode | Description |
|---|---|---|
| **Google Gemini** | `gemini` | Real AI analysis via `gemini-3.6-flash` |
| **Mock Engine** | `mock` | Keyword-based analysis, no API key needed |

---

## System Architecture

```text
        React Frontend
               │
               ▼
        FastAPI Backend
               │
      ┌────────┴────────┐
      ▼                 ▼
 PostgreSQL         Gemini AI
```

---

## 🏗 System Architecture

```text
┌────────────────────────────────────────────────────────────┐
│                        Browser                             │
└──────────────────────────┬─────────────────────────────────┘
                           │  HTTP (port 5173)
┌──────────────────────────▼─────────────────────────────────┐
│               React Frontend (Vite + Tailwind)             │
│   Pages: Login · Register · Dashboard · Jobs ·            │
│          Resumes · ResumeUpload · AIResult                 │
│   Served via Nginx inside Docker container                 │
└──────────────────────────┬─────────────────────────────────┘
                           │  REST API calls (port 8000)
┌──────────────────────────▼─────────────────────────────────┐
│                   FastAPI Backend                          │
│                                                            │
│  Routers:  /auth  /users  /jobs  /resumes  /ai            │
│  Services: auth · user · job · resume · ai                │
│  Models:   User · JobApplication · Resume · Analysis      │
│  Core:     Config · Security · Exceptions                 │
│                                                            │
│  Background Tasks: AI analysis on resume upload           │
│  PDF Processing:   pypdf text extraction                  │
└───────────┬──────────────────────────┬─────────────────────┘
            │                          │
            │ SQLAlchemy ORM           │ httpx async HTTP
            │ (port 5432)              │
┌───────────▼──────────┐   ┌──────────▼───────────────────┐
│   PostgreSQL 16      │   │     Google Gemini API        │
│   jobtracker DB      │   │   (gemini-3.6-flash model)   │
│   Docker Volume      │   └──────────────────────────────┘
└──────────────────────┘

Docker Containers:
  ├── jobtracker_db        → PostgreSQL 16 (Alpine)
  ├── jobtracker_backend   → FastAPI + Uvicorn (Python 3.11 Slim)
  └── jobtracker_frontend  → React + Nginx
```

---

## 📁 Folder Structure

```text
jobtracker/
│
├── backend/                          # FastAPI Application
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py             # Pydantic settings (loads .env)
│   │   │   ├── security.py           # JWT token logic
│   │   │   └── exceptions.py         # Reusable HTTP exception helpers
│   │   │
│   │   ├── db/
│   │   │   └── database.py           # SQLAlchemy engine & session factory
│   │   │
│   │   ├── models/                   # SQLAlchemy ORM models (tables)
│   │   │   ├── __init__.py           # Imports all models for Base.metadata
│   │   │   ├── user.py               # User model
│   │   │   ├── job.py                # JobApplication model + ApplicationStatus enum
│   │   │   ├── resume.py             # Resume model
│   │   │   └── resume_analysis.py    # ResumeAnalysis model
│   │   │
│   │   ├── schemas/                  # Pydantic v2 request/response schemas
│   │   │   ├── user.py
│   │   │   ├── job.py
│   │   │   ├── resume.py
│   │   │   ├── resume_analysis.py
│   │   │   └── ai.py
│   │   │
│   │   ├── routers/                  # FastAPI route handlers
│   │   │   ├── auth.py               # POST /auth/register, /auth/login
│   │   │   ├── users.py              # GET/PATCH /users/me
│   │   │   ├── jobs.py               # CRUD /jobs
│   │   │   ├── resumes.py            # CRUD /resumes + upload + download
│   │   │   └── ai.py                 # POST /ai/match
│   │   │
│   │   ├── services/                 # Business logic layer
│   │   │   ├── auth_service.py       # Token validation, get_current_user
│   │   │   ├── user_service.py
│   │   │   ├── job_service.py
│   │   │   ├── resume_service.py     # Upload, analysis background task
│   │   │   ├── ai_service.py         # Provider selector + orchestrator
│   │   │   └── gemini_provider.py    # Google Gemini API integration
│   │   │
│   │   ├── utils/
│   │   │   └── pdf_utils.py          # pypdf text extraction
│   │   │
│   │   └── main.py                   # App factory, middleware, router registration
│   │
│   ├── uploads/resumes/              # Uploaded PDF files (volume-mounted)
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                         # React Application
│   ├── src/
│   │   ├── api/                      # Axios instance configuration
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── Toast.jsx
│   │   │   ├── Loader.jsx
│   │   │   └── ProtectedRoute.jsx    # Auth guard wrapper
│   │   │
│   │   ├── context/
│   │   │   └── AuthContext.jsx       # Global auth state (React Context)
│   │   │
│   │   ├── hooks/                    # Custom React hooks
│   │   ├── layouts/                  # Layout wrappers
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── Dashboard.jsx         # Stats overview
│   │   │   ├── Jobs.jsx              # Job CRUD + filters + search
│   │   │   ├── Resumes.jsx           # Resume list + set-active + delete
│   │   │   ├── ResumeUpload.jsx      # Upload form + optional job link
│   │   │   └── AIResult.jsx          # AI match score + skills display
│   │   │
│   │   ├── services/                 # API call functions per resource
│   │   ├── App.jsx                   # Router + protected route setup
│   │   └── main.jsx
│   │
│   ├── nginx.conf                    # Nginx config for SPA routing
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── Dockerfile
│
├── docker-compose.yml                # Orchestrates all 3 containers
├── .env                              # Root-level env vars (DB credentials)
└── README.md
```

---

## 🚀 Quickstart

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **PostgreSQL 16** (or use Docker)
- **Git**

---

### 1. Clone the Repository

```bash
git clone https://github.com/s-panchal77/ai-job-application-tracker.git
cd ai-job-application-tracker
```

---

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Create `backend/.env`:

```env
# Application
APP_NAME=AI Job Application Tracker
APP_VERSION=1.0.0
DEBUG=True

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/jobtracker

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Provider — use "mock" (no key needed) or "gemini"
AI_PROVIDER=mock

# Google Gemini (only needed if AI_PROVIDER=gemini)
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-3.6-flash
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

- Backend API: `http://localhost:8000`
- Interactive Docs: `http://localhost:8000/docs`

---

### 3. Frontend Setup

```bash
cd frontend

npm install
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Start the dev server:

```bash
npm run dev
```

Frontend: `http://localhost:5173`

---

## 🐳 Docker Setup

The entire application (database, backend, frontend) can be started with a single command.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 1. Configure Environment Variables

Create a `.env` file in the **project root**:

```env
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=securepassword
POSTGRES_DB=jobtracker

# Frontend build-time variable
VITE_API_BASE_URL=http://localhost:8000
```

### 2. Start All Containers

```bash
docker compose up --build
```

This command:
1. Pulls `postgres:16-alpine` image
2. Builds the FastAPI backend image from `./backend/Dockerfile`
3. Builds the React + Nginx frontend image from `./frontend/Dockerfile`
4. Starts all 3 containers with health checks and dependency ordering

### 3. Access the Application

| Service | URL |
|---|---|
| **Frontend** | `http://localhost:5173` |
| **Backend API** | `http://localhost:8000` |
| **API Docs (Swagger)** | `http://localhost:8000/docs` |
| **PostgreSQL** | `localhost:5432` |

### 4. Container Management

```bash
# Run in background
docker compose up -d --build

# View running containers
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop all containers
docker compose down

# Stop and remove volumes (wipes database!)
docker compose down -v
```

### Docker Architecture

```text
Docker Compose Network
├── jobtracker_db        (postgres:16-alpine)
│   ├── Port: 5432:5432
│   ├── Volume: postgres_data → /var/lib/postgresql/data
│   └── Health check: pg_isready
│
├── jobtracker_backend   (python:3.11-slim)
│   ├── Port: 8000:8000
│   ├── Volume: resume_uploads → /app/uploads
│   ├── Env: DATABASE_URL → db:5432
│   └── Depends on: db (healthy)
│
└── jobtracker_frontend  (node → nginx:alpine)
    ├── Port: 5173:80
    └── Depends on: backend
```

### Persistent Volumes

| Volume | Purpose |
|---|---|
| `postgres_data` | PostgreSQL database files survive container restarts |
| `resume_uploads` | Uploaded PDF resumes persist across deployments |

---

## 📡 API Reference

All protected endpoints require the `Authorization: Bearer <token>` header.

### 🔐 Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | ❌ | Register a new user |
| `POST` | `/auth/login` | ❌ | Login and receive JWT token |

**Register Request:**

```json
{
  "full_name": "Sarthak Panchal",
  "email": "sarthak@example.com",
  "password": "SecurePass123"
}
```

**Login Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 💼 Jobs

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/jobs/` | ✅ | Create a new job application |
| `GET` | `/jobs/` | ✅ | List all jobs (filterable, searchable, paginated) |
| `GET` | `/jobs/stats` | ✅ | Get application counts by status |
| `GET` | `/jobs/{job_id}` | ✅ | Get a single job application |
| `PATCH` | `/jobs/{job_id}` | ✅ | Update a job application |
| `DELETE` | `/jobs/{job_id}` | ✅ | Delete a job application |

**Create Job Request:**

```json
{
  "company_name": "Google",
  "job_title": "Backend Engineer",
  "location": "Bangalore, India",
  "job_url": "https://careers.google.com/jobs/...",
  "job_description": "We are looking for a Python engineer...",
  "status": "Applied",
  "notes": "Referred by a friend",
  "interview_date": "2026-09-15T10:00:00",
  "interview_round": "Round 1 - Technical"
}
```

**Query Parameters for `GET /jobs/`:**

```text
?status=Interview&search=google&skip=0&limit=10
```

**Stats Response:**

```json
{
  "total": 12,
  "applied": 5,
  "oa_scheduled": 2,
  "interview": 3,
  "selected": 1,
  "rejected": 1
}
```

---

### 📄 Resumes

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/resumes/upload` | ✅ | Upload a PDF resume (multipart/form-data) |
| `GET` | `/resumes/` | ✅ | List all resumes |
| `GET` | `/resumes/{resume_id}` | ✅ | Get resume metadata |
| `GET` | `/resumes/{resume_id}/download` | ✅ | Download resume PDF |
| `GET` | `/resumes/{resume_id}/analysis` | ✅ | Get AI analysis result/status |
| `PATCH` | `/resumes/{resume_id}/set-active` | ✅ | Set as active resume |
| `DELETE` | `/resumes/{resume_id}` | ✅ | Delete resume (file + DB record) |

**Upload Resume (multipart/form-data):**

```text
file:          <PDF file, max 5 MB>
version_label: "v2 - Backend Focused"  (optional)
job_id:        42                       (optional — triggers background AI analysis)
```

**Analysis Status Response:**

```json
{
  "status": "completed",
  "match_score": 87,
  "matched_skills": ["python", "fastapi", "postgresql", "docker"],
  "missing_skills": ["kubernetes", "redis"],
  "suggestions": [
    "Strong match — this resume aligns well with the role",
    "Consider adding Redis caching experience"
  ],
  "provider": "gemini"
}
```

---

### 🤖 AI

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/ai/match` | ✅ | Trigger AI resume-to-job match analysis |

**Request:**

```json
{
  "job_id": 42,
  "resume_id": 7
}
```

> If `resume_id` is `null`, the user's active resume is used automatically.

**Response:**

```json
{
  "match_score": 87,
  "matched_skills": ["python", "fastapi", "sqlalchemy", "postgresql", "docker", "rest api"],
  "missing_skills": ["kubernetes", "redis"],
  "suggestions": [
    "Strong match — this resume aligns well with the role",
    "Consider adding Kubernetes orchestration experience"
  ],
  "provider": "gemini"
}
```

---

### ❤️ Health

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/` | ❌ | API welcome + version info |
| `GET` | `/health` | ❌ | Health check |

---

## 🔑 Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Required | Description |
|---|---|---|---|
| `APP_NAME` | `AI Job Application Tracker` | ✅ | Application name |
| `APP_VERSION` | `1.0.0` | ✅ | API version |
| `DATABASE_URL` | — | ✅ | PostgreSQL connection string |
| `SECRET_KEY` | — | ✅ | JWT signing secret — **change in production** |
| `ALGORITHM` | `HS256` | ✅ | JWT hashing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | ✅ | Token validity period |
| `AI_PROVIDER` | `mock` | ✅ | `mock` or `gemini` |
| `GEMINI_API_KEY` | `""` | ⚠️ | Required only when `AI_PROVIDER=gemini` |
| `GEMINI_MODEL` | `gemini-3.6-flash` | ⚠️ | Gemini model name |

### Root (`.env` — used by Docker Compose)

| Variable | Description |
|---|---|
| `POSTGRES_USER` | PostgreSQL username |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_DB` | Database name |
| `VITE_API_BASE_URL` | Frontend API base URL (injected at build time) |

---

## 🤖 AI Integration Guide

### Switching AI Providers

Change a single line in `backend/.env`:

```env
# Free, instant, no API key needed — perfect for development
AI_PROVIDER=mock

# Real Gemini AI analysis — requires GEMINI_API_KEY
AI_PROVIDER=gemini
```

### Getting a Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click **"Get API Key"** → **"Create API Key"**
4. Copy the key into `backend/.env` as `GEMINI_API_KEY`

### How Background Analysis Works

```text
User uploads resume (PDF) + provides job_id
         ↓
FastAPI stores PDF → returns resume record immediately (non-blocking)
         ↓
Background task starts asynchronously
         ↓
pypdf extracts text from PDF
         ↓
Resume text + Job Description sent to Gemini API
         ↓
Gemini returns JSON: match_score, matched_skills, missing_skills, suggestions
         ↓
Analysis saved to resume_analysis table
         ↓
User polls GET /resumes/{resume_id}/analysis for result
```

---

## 📊 Database Schema

```text
users
├── id (PK)
├── full_name
├── email (unique)
├── hashed_password
└── created_at

job_applications
├── id (PK)
├── user_id (FK → users.id CASCADE)
├── company_name
├── job_title
├── job_description
├── job_url
├── location
├── status  (Applied | OA Scheduled | Interview | Selected | Rejected)
├── notes
├── interview_date
├── interview_round
├── applied_date
└── updated_at

resumes
├── id (PK)
├── user_id (FK → users.id)
├── original_filename
├── file_path
├── version_label
├── is_active
└── uploaded_at

resume_analysis
├── id (PK)
├── resume_id (FK → resumes.id)
├── job_id (FK → job_applications.id)
├── match_score
├── matched_skills  (JSON)
├── missing_skills  (JSON)
├── suggestions     (JSON)
├── provider
└── analyzed_at
```

---

## 🧑‍💻 Frontend Pages

| Route | Page | Auth | Description |
|---|---|---|---|
| `/login` | Login | ❌ | Email + password login form |
| `/register` | Register | ❌ | New user registration |
| `/dashboard` | Dashboard | ✅ | Stats overview, quick actions |
| `/jobs` | Jobs | ✅ | Full CRUD with filter, search, pagination |
| `/resumes` | Resumes | ✅ | Resume list, set-active, delete |
| `/resume-upload` | ResumeUpload | ✅ | PDF upload form with optional job linking |
| `/ai-result/:resumeId` | AIResult | ✅ | AI match score, skills visualization |

---

## 📈 Learning Outcomes

| Area | What's Demonstrated |
|---|---|
| **REST API Design** | RESTful endpoints with proper HTTP verbs, status codes, query params |
| **Authentication** | JWT Bearer tokens, bcrypt hashing, protected routes |
| **ORM** | SQLAlchemy 2.0 with mapped columns, relationships, cascade deletes |
| **Database** | PostgreSQL, schema design, foreign keys, enums |
| **Async Python** | `async def`, `await`, `BackgroundTasks`, `httpx.AsyncClient` |
| **AI Integration** | Provider pattern, Gemini REST API, prompt engineering |
| **File Handling** | Multipart upload, disk storage, PDF text extraction |
| **React** | Hooks, Context API, React Router, protected routes |
| **Docker** | Multi-stage builds, Compose, health checks, named volumes |
| **Software Design** | Layered architecture (router → service → model), separation of concerns |

---

## 🔮 Future Improvements

- [ ] Alembic migrations — version-controlled schema changes
- [ ] Global exception handler — centralized error middleware
- [ ] Structured logging — request/response logging with correlation IDs
- [ ] Rate limiting — protect AI endpoints from abuse
- [ ] Email notifications — status change alerts via SMTP
- [ ] CI/CD pipeline — GitHub Actions for test + build + deploy
- [ ] AWS deployment — ECS / EC2 with RDS PostgreSQL
- [ ] Kubernetes — Helm chart for scalable orchestration
- [ ] WebSockets — real-time AI analysis progress updates
- [ ] Application calendar — visual interview timeline view

---

## 📄 Resume Bullet Points

```text
• Built a full-stack AI Job Application Tracker using FastAPI, PostgreSQL, React, and Docker,
  featuring JWT authentication, resume PDF upload, and real-time application status tracking.

• Integrated Google Gemini AI API to perform automated resume-to-job-description matching,
  returning match scores, skill gap analysis, and actionable suggestions via async background tasks.

• Designed a provider-agnostic AI architecture supporting hot-swappable providers (mock/Gemini)
  through a single environment variable, eliminating code changes during provider switching.

• Containerized the full application (FastAPI + PostgreSQL + React/Nginx) using Docker Compose
  with health checks, persistent volumes, and dependency ordering for production-ready deployment.

• Implemented a layered backend architecture (Router → Service → Model) with Pydantic v2
  validation, SQLAlchemy 2.0 ORM, and granular async HTTP error handling for robust reliability.
```

---

## 💼 LinkedIn Project Description

**AI Job Application Tracker** | FastAPI · PostgreSQL · React · Google Gemini · Docker

A production-quality, full-stack web application for managing the entire job application lifecycle.

Key highlights:

- **Backend**: FastAPI REST API with JWT authentication, SQLAlchemy ORM, and async PDF processing
- **AI**: Google Gemini integration that parses resumes, analyzes job descriptions, and returns match scores + skill gap analysis
- **Frontend**: React 18 SPA with Tailwind CSS, protected routes, and a full job/resume management dashboard
- **DevOps**: Fully containerized with Docker Compose — single command to deploy all 3 services (DB, API, Frontend) with persistent volumes

This project demonstrates end-to-end software engineering: API design, database modeling, asynchronous programming, AI integration, and containerized deployment.

---

## 🎯 ATS-Friendly Project Description

**AI Job Application Tracker** — Full-Stack Web Application

- Developed RESTful API backend using FastAPI (Python) with PostgreSQL database and SQLAlchemy ORM; implemented JWT-based authentication with bcrypt password hashing
- Integrated Google Gemini AI API for intelligent resume analysis; built provider-agnostic architecture Currently integrated with Google Gemini API for resume analysis.
- Implemented asynchronous background task processing using FastAPI BackgroundTasks for non-blocking PDF text extraction and AI analysis
- Built React 18 single-page application frontend with Tailwind CSS, React Router v6, and Axios; implemented protected routes and global authentication context
- Containerized application using Docker and Docker Compose with multi-service orchestration (PostgreSQL, FastAPI, Nginx/React), health checks, and persistent volume management
- Designed normalized relational database schema with proper foreign keys, cascade deletes, and enum types for application status tracking

**Technologies**: Python · FastAPI · SQLAlchemy · PostgreSQL · Alembic · JWT · React · Tailwind CSS · Vite · Docker · Docker Compose · Nginx · Google Gemini API · pypdf · httpx · Pydantic v2

---

## 👨‍💻 Author

**Sarthak Panchal**

Final Year Computer Engineering Student | Python Backend Developer

[![GitHub](https://img.shields.io/badge/GitHub-s--panchal77-181717?style=flat-square&logo=github)](https://github.com/s-panchal77)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Sarthak_Panchal-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/sarthak-panchal)

---

<div align="center">

*Built with ❤️ by Sarthak Panchal — 2026*

</div>
