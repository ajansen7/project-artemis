"""
Admin routes — user profile management.

Endpoints:
  GET  /api/profile/me           — current user's profile (any authenticated user)
  GET  /api/admin/users          — list all user profiles (admin only)
  PUT  /api/admin/users/{uid}    — update user status/role (admin only)
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from api.modules.config import _get_supabase, get_user_id_from_request, get_user_profile, run_db

router = APIRouter()


# ─── Current user profile ────────────────────────────────────────

@router.get("/api/profile/me")
async def get_my_profile(request: Request):
    """Get the current user's profile. Works for pending users too."""
    user_id = get_user_id_from_request(request)
    profile = await get_user_profile(user_id)
    if not profile:
        return {"status": "pending", "role": "user", "message": "Profile not yet created"}
    return profile


# ─── Admin helpers ────────────────────────────────────────────────

async def _require_admin(request: Request) -> str:
    """Extract user_id and verify they are an admin. Raises 403 if not."""
    user_id = get_user_id_from_request(request)
    profile = await get_user_profile(user_id)
    if not profile or profile["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


# ─── List users ───────────────────────────────────────────────────

@router.get("/api/admin/users")
async def list_users(request: Request):
    """List all user profiles. Admin only."""
    await _require_admin(request)
    sb = _get_supabase()
    res = await run_db(
        lambda: sb.table("user_profiles")
        .select("user_id, email, role, status, created_at, updated_at")
        .order("created_at", desc=False)
        .execute()
    )
    return {"users": res.data or []}


# ─── Update user ──────────────────────────────────────────────────

class UserUpdate(BaseModel):
    status: str | None = None  # "approved" | "blocked" | "pending"
    role: str | None = None    # "admin" | "user"

@router.put("/api/admin/users/{user_id}")
async def update_user(user_id: str, body: UserUpdate, request: Request):
    """Update a user's status or role. Admin only."""
    admin_id = await _require_admin(request)

    # Prevent admin from demoting/blocking themselves
    if user_id == admin_id:
        if body.role and body.role != "admin":
            raise HTTPException(status_code=400, detail="Cannot demote yourself")
        if body.status and body.status != "approved":
            raise HTTPException(status_code=400, detail="Cannot block yourself")

    # Validate values
    if body.status and body.status not in ("pending", "approved", "blocked"):
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")
    if body.role and body.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail=f"Invalid role: {body.role}")

    updates = {}
    if body.status:
        updates["status"] = body.status
    if body.role:
        updates["role"] = body.role

    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")

    updates["updated_at"] = "now()"

    sb = _get_supabase()
    res = await run_db(
        lambda: sb.table("user_profiles")
        .update(updates)
        .eq("user_id", user_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")

    return {"ok": True, "user": res.data[0]}
