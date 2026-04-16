"""
Middleware that blocks unapproved users from accessing protected endpoints.

Unapproved users can only reach:
  - /api/auth/*         (login/logout/session)
  - /api/profile/me     (check their own status)
  - /api/events         (SSE — harmless, used by frontend)

All other endpoints require status == 'approved'.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.modules.config import get_user_id_from_request, get_user_profile, logger

# Paths that unapproved (or unauthenticated) users can access
OPEN_PATHS = (
    "/api/auth/",
    "/api/profile/me",
    "/api/events",
)


class ApprovalMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Let open paths through unconditionally
        if any(path.startswith(p) for p in OPEN_PATHS):
            return await call_next(request)

        # Non-API paths (frontend static files) pass through
        if not path.startswith("/api/"):
            return await call_next(request)

        # Try to extract user_id from JWT — if no auth header, let the
        # route's own auth check handle it (some routes are unprotected)
        try:
            user_id = get_user_id_from_request(request)
        except Exception:
            return await call_next(request)

        # Check profile status
        profile = await get_user_profile(user_id)

        if not profile:
            return JSONResponse(
                status_code=403,
                content={"detail": "Account pending setup. Please wait for admin approval."},
            )

        if profile["status"] == "blocked":
            return JSONResponse(
                status_code=403,
                content={"detail": "Account has been blocked. Contact administrator."},
            )

        if profile["status"] == "pending":
            return JSONResponse(
                status_code=403,
                content={"detail": "Account pending approval. Please wait for admin approval."},
            )

        # Approved — continue
        return await call_next(request)
