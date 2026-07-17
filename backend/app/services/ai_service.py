# backend/app/services/ai_service.py

import json
import re
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import not_found_exception, bad_request_exception
from app.models.user import User
from app.models.job import JobApplication
from app.models.resume import Resume
from app.schemas.ai import AIMatchResponse
from app.utils.pdf_utils import extract_text_from_pdf


# ─────────────────────────────────────────────────────────────
# A small predefined skill vocabulary for the mock provider.
# In a real project this might be a much bigger list, or you'd
# skip this entirely once using a real LLM (which doesn't need
# a hardcoded skill list — it "understands" text).
# ─────────────────────────────────────────────────────────────
COMMON_SKILLS = [
    "python", "java", "javascript", "typescript", "react", "node",
    "fastapi", "django", "flask", "sql", "postgresql", "mysql", "mongodb",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "rest api",
    "graphql", "redis", "sqlalchemy", "pandas", "numpy", "machine learning",
    "html", "css", "tailwind", "next.js", "express", "microservices",
    "ci/cd", "jenkins", "linux", "agile", "scrum", "testing", "pytest",
]


# ─────────────────────────────────────────────────────────────
# MOCK PROVIDER — no external calls, instant, free, deterministic
# ─────────────────────────────────────────────────────────────
def mock_analyze_resume(resume_text: str, job_description: str) -> dict:
    """
    Fake AI analysis using simple keyword matching.

    This is NOT real AI — it's a stand-in that returns data in
    EXACTLY the same shape a real AI call would, so the rest of
    the system can be built and tested without needing an API key.

    Algorithm:
    1. Lowercase both texts
    2. Check which COMMON_SKILLS appear in each
    3. matched = skills in both
    4. missing = skills in JD but not in resume
    5. score = percentage of JD skills that were matched
    """
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()

    # Find which known skills appear in the job description
    jd_skills = {skill for skill in COMMON_SKILLS if skill in jd_lower}

    # Find which of those skills also appear in the resume
    matched_skills = {skill for skill in jd_skills if skill in resume_lower}

    missing_skills = jd_skills - matched_skills

    # Calculate score — percentage of required skills that matched
    if jd_skills:
        score = round((len(matched_skills) / len(jd_skills)) * 100)
    else:
        # No recognizable skills found in the JD — return a neutral score
        score = 50

    # Generate simple suggestions based on what's missing
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
# REAL PROVIDER — calls OpenAI's API
# ─────────────────────────────────────────────────────────────
def _build_prompt(resume_text: str, job_description: str) -> str:
    """
    Builds the prompt sent to the AI.

    Prompt design principles applied:
    1. Assign a role — focuses model behavior
    2. Specify EXACT output shape — field names, types, constraints
    3. Explicitly forbid extra text — prevents broken JSON parsing
    4. Truncate long inputs — controls cost and avoids token limits
    """
    # Truncate very long resumes/JDs to control API cost and stay within limits
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


async def analyze_resume_with_openai(resume_text: str, job_description: str) -> dict:
    """
    Calls the real OpenAI API to analyze resume-to-JD match.

    This function is async because httpx.AsyncClient makes a
    non-blocking network call — the server can handle other
    requests while waiting for OpenAI's response.
    """

    if not settings.OPENAI_API_KEY:
        raise bad_request_exception(
            "AI_PROVIDER is set to 'openai' but OPENAI_API_KEY is not configured"
        )

    prompt = _build_prompt(resume_text, job_description)

    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        # Asks the API to guarantee syntactically valid JSON output —
        # a safety net ON TOP OF our prompt instructions, not a replacement for them
        "response_format": {"type": "json_object"},
        "temperature": 0.3,   # Lower = more consistent/deterministic output
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    # ── Make the async HTTP call ─────────────────────────────
    # async with ... as client: ensures the connection is properly
    # closed when we're done, even if an error occurs (same idea
    # as the get_db() session pattern from Phase 2!)
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                settings.OPENAI_API_URL,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()   # Raises an exception for 4xx/5xx responses

        except httpx.TimeoutException:
            raise bad_request_exception("AI service timed out. Please try again.")
        except httpx.HTTPStatusError as e:
            raise bad_request_exception(f"AI service error: {e.response.status_code}")

    # ── Layer 1 JSON parsing: the outer API response wrapper ─
    response_data = response.json()

    try:
        ai_generated_text = response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise bad_request_exception("Unexpected response structure from AI service")

    # ── Layer 2 JSON parsing: the AI-generated content itself ─
    try:
        result = json.loads(ai_generated_text)
    except json.JSONDecodeError:
        raise bad_request_exception("AI service returned an unparseable response")

    # Add provider tag — same as mock does
    result["provider"] = "openai"

    return result


# ─────────────────────────────────────────────────────────────
# ORCHESTRATION — the function routers actually call
# ─────────────────────────────────────────────────────────────
async def match_resume_to_job(
    db: Session,
    job_id: int,
    resume_id: int | None,
    current_user: User,
) -> AIMatchResponse:
    """
    Full orchestration:
    1. Fetch the job (with ownership check)
    2. Fetch the resume — specific one, or the active one if not specified
    3. Extract text from the resume PDF
    4. Call the configured AI provider (mock or openai)
    5. Return a validated AIMatchResponse

    This function doesn't care HOW the AI analysis happens —
    it just calls whichever provider function matches settings.AI_PROVIDER.
    That's the interface pattern in action.
    """

    # ── Step 1: Fetch job, verify ownership ──────────────────
    job = (
        db.query(JobApplication)
        .filter(JobApplication.id == job_id)
        .first()
    )
    if not job or job.user_id != current_user.id:
        raise not_found_exception("Job", job_id)

    if not job.job_description:
        raise bad_request_exception(
            "This job application has no job description saved. Add one before matching."
        )

    # ── Step 2: Fetch resume ──────────────────────────────────
    if resume_id is not None:
        # A specific resume was requested
        resume = (
            db.query(Resume)
            .filter(Resume.id == resume_id)
            .first()
        )
        if not resume or resume.user_id != current_user.id:
            raise not_found_exception("Resume", resume_id)
    else:
        # No resume specified — use the active one
        resume = (
            db.query(Resume)
            .filter(Resume.user_id == current_user.id, Resume.is_active == True)  # noqa: E712
            .first()
        )
        if not resume:
            raise bad_request_exception(
                "You have no active resume. Upload one first via /resumes/upload"
            )

    # ── Step 3: Extract resume text ──────────────────────────
    resume_text = extract_text_from_pdf(resume.file_path)

    # ── Step 4: Call the configured AI provider ──────────────
    if settings.AI_PROVIDER == "mock":
        result = mock_analyze_resume(resume_text, job.job_description)
    else:
        result = await analyze_resume_with_openai(resume_text, job.job_description)

    # ── Step 5: Shape into our response schema ───────────────
    # Pydantic validates the result here — if the AI (mock or real)
    # returned something malformed, this will raise a clear error
    # rather than silently passing bad data to the client.
    return AIMatchResponse(**result)