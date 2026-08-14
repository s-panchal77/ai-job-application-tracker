# backend/app/services/gemini_provider.py

# ─────────────────────────────────────────────────────────────
# WHY THIS FILE EXISTS
# ─────────────────────────────────────────────────────────────
# This file talks to Google Gemini's REST API directly using httpx —
# no Google SDK involved. Keeping this in its own file (rather than
# inside ai_service.py) means ai_service.py doesn't need to know
# ANY Gemini-specific details: no URL shape, no request/response
# structure, no Gemini error codes. It just calls one function
# and gets back a plain dict.
#
# If you ever swap Gemini for Claude, Azure OpenAI, or Ollama,
# you'd create a similar new file and change ONE line in
# ai_service.py's get_ai_analysis() — nothing here would need
# to move or change.
# ─────────────────────────────────────────────────────────────

import json

import httpx
from fastapi import HTTPException, status

from app.core.config import settings

# ─────────────────────────────────────────────────────────────
# GEMINI REST ENDPOINT
# ─────────────────────────────────────────────────────────────
# Gemini's REST API embeds the model name directly in the URL path,
# unlike OpenAI which uses one fixed URL for all models.

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def _build_gemini_url() -> str:
    # Builds the full Gemini API URL using the model name from settings.
    return f"{GEMINI_BASE_URL}/{settings.GEMINI_MODEL}:generateContent"


# ─────────────────────────────────────────────────────────────
# PROMPT BUILDER
# ─────────────────────────────────────────────────────────────
def _build_prompt(resume_text: str, job_description: str) -> str:
    # Truncate to avoid token limits
    resume_snippet = resume_text[:4000]
    jd_snippet = job_description[:2000]

    return f"""You are a resume analysis assistant. Compare the resume to the job description.

Return ONLY valid JSON. No markdown. No code fences. No explanations. No extra text before or after.
The JSON must exactly match this shape:
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
# PUBLIC FUNCTION — the only thing other files should import
# ─────────────────────────────────────────────────────────────
async def analyze_resume_with_gemini(resume_text: str, job_description: str) -> dict:
    """
    Calls Gemini API, returns dict with match_score, matched_skills,
    missing_skills, suggestions, and provider='gemini'.
    Raises HTTPException on any failure.
    """

    # ── Guard: API key must be configured ────────────────────
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI_PROVIDER is set to 'gemini' but GEMINI_API_KEY is not configured in .env",
        )

    prompt = _build_prompt(resume_text, job_description)
    url = _build_gemini_url()

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.3,
        },
    }
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": settings.GEMINI_API_KEY,
    }

    # ── Make the API call ───────────────────────────────────────
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Gemini API took too long to respond. Please try again.",
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not connect to Gemini API. Check your internet connection.",
            )
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            if code == 400:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "Gemini API rejected the request as malformed.",
                )
            elif code == 401:
                raise HTTPException(
                    status.HTTP_401_UNAUTHORIZED,
                    "Gemini API key is invalid or missing.",
                )
            elif code == 403:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    "Gemini API key does not have permission for this request.",
                )
            elif code == 404:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    f"Gemini model '{settings.GEMINI_MODEL}' was not found. Check GEMINI_MODEL in .env",
                )
            elif code == 408:
                raise HTTPException(
                    status.HTTP_408_REQUEST_TIMEOUT, "Gemini API request timed out."
                )
            elif code == 429:
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    "Gemini API rate limit reached. Please wait and try again shortly.",
                )
            elif code >= 500:
                raise HTTPException(
                    status.HTTP_502_BAD_GATEWAY,
                    "Gemini API is currently experiencing issues. Please try again later.",
                )
            else:
                raise HTTPException(
                    status.HTTP_502_BAD_GATEWAY,
                    f"Gemini API returned an unexpected error (status {code}).",
                )

    # ── Handle a completely empty response body ──────────────────
    if not response.content:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Gemini API returned an empty response."
        )

    try:
        response_data = response.json()
    except json.JSONDecodeError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Gemini API response was not valid JSON."
        )

    try:
        candidates = response_data["candidates"]
        if not candidates:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                "Gemini API returned no candidates. The prompt may have been blocked.",
            )
        ai_generated_text = candidates[0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Gemini API response had an unexpected structure.",
        )

    if not ai_generated_text or not ai_generated_text.strip():
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Gemini API returned empty analysis content."
        )

    try:
        result = json.loads(ai_generated_text)
    except json.JSONDecodeError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Gemini API returned analysis in an unparseable format.",
        )

    result["provider"] = "gemini"
    return result
