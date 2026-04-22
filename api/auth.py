"""Google JWT verification + email whitelist + rate limiter.

Usage in main.py:
    from auth import require_auth, limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.post("/chat")
    @limiter.limit("10/minute")
    async def chat(request: Request, body: dict, user: dict = Depends(require_auth)):
        ...
"""
from fastapi import Header, HTTPException, Request
from google.oauth2 import id_token
from google.auth.transport import requests as g_requests
from slowapi import Limiter
from slowapi.util import get_remote_address
import os

# ---------- Config ----------
GOOGLE_CLIENT_ID = (
    os.getenv("GOOGLE_CLIENT_ID")
    or "507309950334-6o5c75ms28a9bng6e9cq5jkv2spssnt6.apps.googleusercontent.com"
)

# Email whitelist — only these accounts can call protected endpoints.
# NEO_EMAIL_WHITELIST env var AUGMENTS the default (used to do override, but
# that broke shared-access rollouts: a stale env value on Railway was silently
# locking out newly-added emails). Default list is always active.
_DEFAULT_WHITELIST = (
    "pantepante72@gmail.com,"
    "chayangkulkongkavitool@gmail.com,"
    "hariss2549zaza@gmail.com"
)
WHITELIST = {
    e.strip().lower()
    for e in (_DEFAULT_WHITELIST + "," + (os.getenv("NEO_EMAIL_WHITELIST") or "")).split(",")
    if e.strip()
}

# Dev bypass (skip auth) — set NEO_AUTH_DISABLED=1 for local testing without login
AUTH_DISABLED = os.getenv("NEO_AUTH_DISABLED") == "1"

# Shared secret for local hook scripts (PreToolUse / PostToolUse). Pre-seeded
# so it just works on first run; override via env for stricter deployments.
HOOK_TOKEN = os.getenv("NEO_HOOK_TOKEN", "local-hook-dev-only")

_google_req = g_requests.Request()


def require_auth(authorization: str = Header(default="")) -> dict:
    """FastAPI dependency — verifies Google ID token from Bearer header.

    Returns dict {email, name, sub, picture} on success.
    Raises 401 on missing/invalid token or non-whitelisted email.
    """
    if AUTH_DISABLED:
        return {"email": "dev@local", "name": "Dev", "sub": "dev", "picture": ""}

    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing Authorization: Bearer <token>")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="empty token")

    try:
        info = id_token.verify_oauth2_token(token, _google_req, GOOGLE_CLIENT_ID)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"invalid token: {e}")

    email = (info.get("email") or "").lower()
    if not info.get("email_verified"):
        raise HTTPException(status_code=401, detail="email not verified")
    if email not in WHITELIST:
        raise HTTPException(status_code=403, detail=f"email not whitelisted: {email}")

    return {
        "email": email,
        "name": info.get("name", ""),
        "sub": info.get("sub", ""),
        "picture": info.get("picture", ""),
    }


def require_auth_or_hook(
    authorization: str = Header(default=""),
    x_hook_token: str = Header(default=""),
) -> dict:
    """Accepts either a valid Google JWT OR a matching hook token.

    Use on endpoints that local Claude Code hooks write to (/log) — they run
    outside a browser session so they can't carry a Google token.
    """
    if x_hook_token and x_hook_token == HOOK_TOKEN:
        return {"email": "hook@local", "name": "Hook", "sub": "hook", "picture": ""}
    return require_auth(authorization)


# ---------- Rate Limiter ----------
# 10 requests/minute per IP by default — generous enough for normal use
# Tight enough to stop abuse ($$$)
limiter = Limiter(key_func=get_remote_address, default_limits=[])
