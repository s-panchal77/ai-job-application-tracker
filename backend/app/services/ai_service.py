# backend/app/services/ai_service.py

import json

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import bad_request_exception, not_found_exception
from app.models.job import JobApplication
from app.models.resume import Resume
from app.models.user import User
from app.schemas.ai import AIMatchResponse
from app.services.gemini_provider import analyze_resume_with_gemini
from app.utils.pdf_utils import extract_text_from_pdf

# ─────────────────────────────────────────────────────────────
# Same mock skill vocabulary as Phase 9 — unchanged
# ─────────────────────────────────────────────────────────────
COMMON_SKILLS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node",
    "fastapi",
    "django",
    "flask",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "git",
    "rest api",
    "graphql",
    "redis",
    "sqlalchemy",
    "pandas",
    "numpy",
    "machine learning",
    "html",
    "css",
    "tailwind",
    "next.js",
    "express",
    "microservices",
    "ci/cd",
    "jenkins",
    "linux",
    "agile",
    "scrum",
    "testing",
    "pytest",
]


# ─────────────────────────────────────────────────────────────
# MOCK PROVIDER — unchanged from Phase 9
# ─────────────────────────────────────────────────────────────
def mock_analyze_resume(resume_text: str, job_description: str) -> dict:
    """
    Fake AI analysis using keyword matching. No network calls,
    no async needed — this is pure CPU-bound string comparison,
    which is why this function is a normal 'def', not 'async def'.
    """
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()

    jd_skills = {skill for skill in COMMON_SKILLS if skill in jd_lower}
    matched_skills = {skill for skill in jd_skills if skill in resume_lower}
    missing_skills = jd_skills - matched_skills

    if jd_skills:
        score = round((len(matched_skills) / len(jd_skills)) * 100)
    else:
        score = 50

    suggestions = []
    if missing_skills:
        top_missing = list(missing_skills)[:3]
        suggestions.append(
            f"Consider highlighting experience with: {', '.join(top_missing)}"
        )
    if score < 50:
        suggestions.append("Your resume may need significant tailoring for this role")
    elif score < 80:
        suggestions.append("Good foundation — add a few more relevant keywords")
    else:
        suggestions.append("Strong match — this resume aligns well with the role")

    return {
        "match_score": score,
        "matched_skills": sorted(matched_skills),
        "missing_skills": sorted(missing_skills),
        "suggestions": suggestions,
        "provider": "mock",
    }


# ─────────────────────────────────────────────────────────────
# PROMPT BUILDER — unchanged from Phase 9
# ─────────────────────────────────────────────────────────────
def _build_prompt(resume_text: str, job_description: str) -> str:
    """
    Builds the exact instruction sent to OpenAI.
    Truncated inputs control token cost and avoid hitting model limits.
    """
    resume_snippet = resume_text[:4000]
    jd_snippet = job_description[:2000]

    return f"""You are a resume analysis assistant. Compare the resume to the job description.

Respond with ONLY valid JSON in exactly this format, no other text before or after:
{{
  "match_score": <integer between 0 and 100>,
  "matched_skills": [<array of skill strings found in both resume and JD>],
  "missing_skills": [<array of skill strings required by JD but missing from resume>],
  "suggestions": [<array of 2-4 short, specific, actionable improvement suggestions>]
}}

Resume:
{resume_snippet}

Job Description:
{jd_snippet}
"""


# ─────────────────────────────────────────────────────────────
# REAL PROVIDER — UPDATED with granular async error handling
# ─────────────────────────────────────────────────────────────
async def analyze_resume_with_openai(resume_text: str, job_description: str) -> dict:
    """
    Calls the real OpenAI API asynchronously.

    ASYNC FLOW:
    1. This coroutine starts, builds the request
    2. 'await client.post(...)' pauses THIS coroutine
    3. The event loop is FREE to handle other requests during
       the network round-trip (typically 1-5 seconds for OpenAI)
    4. When OpenAI responds, this coroutine resumes exactly
       where it left off

    ERROR HANDLING — each failure mode gets a distinct, clear message.
    This matters because "AI service error" tells a developer nothing,
    but "Invalid API key" tells them exactly what to fix.
    """

    if not settings.OPENAI_API_KEY:
        raise bad_request_exception(
            "AI_PROVIDER is set to 'openai' but OPENAI_API_KEY is not configured in .env"
        )

    prompt = _build_prompt(resume_text, job_description)

    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    # ── Make the async HTTP call with layered error handling ─
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                settings.OPENAI_API_URL,
                headers=headers,
                json=payload,
            )
            # raise_for_status() converts 4xx/5xx into an exception
            # we can catch specifically below
            response.raise_for_status()

        except httpx.TimeoutException:
            # The request took longer than our 30-second limit.
            # Common cause: OpenAI is slow/overloaded, or network is poor.
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI service took too long to respond. Please try again.",
            )

        except httpx.ConnectError:
            # No internet connection, DNS failure, or OpenAI is unreachable.
            # This is DIFFERENT from a timeout — the connection couldn't
            # even be established.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not connect to the AI service. Check your internet connection.",
            )

        except httpx.HTTPStatusError as e:
            # The request reached OpenAI, but OpenAI returned an error status.
            # We branch on the SPECIFIC status code for a clear message.
            status_code = e.response.status_code

            if status_code == 401:
                # Invalid or missing API key
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="AI service rejected our API key. Check OPENAI_API_KEY in .env",
                )
            elif status_code == 429:
                # Rate limit exceeded — too many requests, or quota exhausted
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="AI service rate limit reached. Please wait and try again shortly.",
                )
            elif status_code >= 500:
                # OpenAI's own servers are having issues — not our fault
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="The AI service is currently experiencing issues. Please try again later.",
                )
            else:
                # Catch-all for any other 4xx we didn't specifically handle
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"AI service returned an unexpected error (status {status_code}).",
                )

    # ── Handle an empty response body ────────────────────────
    if not response.content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service returned an empty response.",
        )

    # ── Layer 1 JSON parsing: the outer API response wrapper ─
    try:
        response_data = response.json()
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service response was not valid JSON.",
        )

    try:
        ai_generated_text = response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service response had an unexpected structure.",
        )

    if not ai_generated_text or not ai_generated_text.strip():
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service returned empty analysis content.",
        )

    # ── Layer 2 JSON parsing: the AI-generated content itself ─
    try:
        result = json.loads(ai_generated_text)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service returned analysis in an unparseable format.",
        )

    result["provider"] = "openai"
    return result


# ─────────────────────────────────────────────────────────────
# PROVIDER SELECTOR — NEW in Phase 10
# ─────────────────────────────────────────────────────────────
async def get_ai_analysis(resume_text: str, job_description: str) -> dict:
    """
    Selects and runs the configured AI provider.

    UPDATED: OpenAI removed, Gemini added. This is the ONLY function
    in the entire codebase that changed to make this swap — the router,
    the orchestration function below, and every schema are untouched.
    """
    if settings.AI_PROVIDER == "mock":
        return mock_analyze_resume(resume_text, job_description)

    elif settings.AI_PROVIDER == "gemini":
        return await analyze_resume_with_gemini(resume_text, job_description)

    else:
        raise bad_request_exception(
            f"Unknown AI_PROVIDER '{settings.AI_PROVIDER}'. Use 'mock' or 'gemini'."
        )


# ─────────────────────────────────────────────────────────────
# ORCHESTRATION — same responsibilities as Phase 9, now simpler
# ─────────────────────────────────────────────────────────────
async def match_resume_to_job(
    db: Session,
    job_id: int,
    resume_id: int | None,
    current_user: User,
) -> AIMatchResponse:
    """
    Full orchestration — unchanged responsibilities from Phase 9:
    1. Fetch job (ownership checked)
    2. Fetch resume (ownership checked, or active resume)
    3. Extract resume text
    4. Get AI analysis (provider-agnostic — see get_ai_analysis above)
    5. Return validated AIMatchResponse

    CHANGED: step 4 now calls get_ai_analysis() instead of an
    inline if/else. This function no longer needs to know
    ANYTHING about which providers exist.
    """

    # ── Step 1: Fetch job, verify ownership ──────────────────
    job = db.query(JobApplication).filter(JobApplication.id == job_id).first()
    if not job or job.user_id != current_user.id:
        raise not_found_exception("Job", job_id)

    if not job.job_description:
        raise bad_request_exception(
            "This job application has no job description saved. Add one before matching."
        )

    # ── Step 2: Fetch resume ──────────────────────────────────
    if resume_id is not None:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume or resume.user_id != current_user.id:
            raise not_found_exception("Resume", resume_id)
    else:
        resume = (
            db.query(Resume)
            .filter(
                Resume.user_id == current_user.id, Resume.is_active == True
            )  # noqa: E712
            .first()
        )
        if not resume:
            raise bad_request_exception(
                "You have no active resume. Upload one first via /resumes/upload"
            )

    # ── Step 3: Extract resume text ──────────────────────────
    resume_text = extract_text_from_pdf(resume.file_path)

    # ── Step 4: Get AI analysis (provider-agnostic) ──────────
    result = await get_ai_analysis(resume_text, job.job_description)

    # ── Step 5: Validate and return ──────────────────────────
    return AIMatchResponse(**result)
