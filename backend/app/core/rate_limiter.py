# backend/app/core/rate_limiter.py

"""
Rate Limiting Configuration
=============================

WHY RATE LIMITING EXISTS
--------------------------
Without rate limiting, any IP address can:

  1. BRUTE-FORCE ATTACK:
     Send 100,000 login attempts per second against /auth/login
     until they guess a password. No defense = account takeover.

  2. DENIAL-OF-SERVICE (DoS):
     Flood your API with thousands of requests, using up all your
     server's CPU and memory, making it unavailable to real users.

  3. API ABUSE:
     Call your AI analysis endpoint millions of times, costing you
     money on external API calls (Gemini, OpenAI, etc.).

  4. SCRAPING:
     Extract all your job data or user data programmatically.

Rate limiting solves this by tracking how many requests each IP
sends in a time window, and returning HTTP 429 (Too Many Requests)
when the limit is exceeded.

HOW SLOWAPI WORKS
------------------
slowapi is a FastAPI-compatible rate limiting library built on top
of the `limits` library. It integrates as Starlette middleware.

Flow for every request:
  1. Middleware extracts the client IP address
  2. Increments a counter: "IP 192.168.1.1 has made N requests this minute"
  3. If N <= RATE_LIMIT_PER_MINUTE → allow the request through
  4. If N > RATE_LIMIT_PER_MINUTE → return HTTP 429 immediately,
     never reaching the router or database

STORAGE BACKEND
----------------
By default, slowapi uses IN-MEMORY storage.
  - Perfect for single-server development and testing
  - Limitation: each server instance has its own counter
  - For multi-server production: switch to Redis backend

  # Redis example (production):
  from slowapi import Limiter
  limiter = Limiter(
      key_func=get_remote_address,
      storage_uri="redis://redis:6379",
  )

KEY FUNCTION
------------
`get_remote_address` extracts the real client IP.
It automatically reads X-Forwarded-For header (set by Nginx/load balancers)
before falling back to the raw connection IP.

This is important: behind a reverse proxy, the raw IP would be the
proxy's IP (same for all clients), so everyone would share one limit.
X-Forwarded-For contains the actual client IP.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# ==========================================================
# Limiter Instance
# ==========================================================
# `key_func=get_remote_address`
#   → Rate limit is tracked PER IP ADDRESS
#   → Each unique IP has its own independent counter
#
# `default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"]`
#   → Format: "{count}/{period}"
#   → Period options: second, minute, hour, day
#   → This applies to ALL routes unless a route overrides it
#   → Value is read from settings (set in .env), not hardcoded
# ==========================================================
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)


# ==========================================================
# How to Apply Rate Limits to Specific Routes (Optional)
# ==========================================================
# The global limit above applies to every route automatically
# via the SlowAPIMiddleware registered in main.py.
#
# To apply a STRICTER limit to a specific route (e.g., login):
#
#   from app.core.rate_limiter import limiter
#
#   @router.post("/login")
#   @limiter.limit("5/minute")   ← Override: only 5 login attempts/min
#   async def login(request: Request, ...):
#       ...
#
# NOTE: When using @limiter.limit() on a route, the route function
# MUST accept `request: Request` as a parameter — slowapi needs it
# to extract the client IP. This is the most common beginner mistake.
# ==========================================================
