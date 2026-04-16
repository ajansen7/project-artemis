"""
Auth bridge — unifies CLI and browser auth by reading/writing ~/.artemis/credentials.json.

This allows the browser to pick up whoever is logged in via CLI and vice versa.
Endpoints:
  GET /api/auth/session — read current CLI session from disk
  POST /api/auth/logout — sign out and delete CLI credentials
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from supabase import create_client

from api.modules.config import _get_supabase

router = APIRouter()

CREDS_FILE = Path.home() / ".artemis" / "credentials.json"


def _read_creds() -> dict:
    """Load stored credentials, or return empty dict."""
    if CREDS_FILE.exists():
        try:
            return json.loads(CREDS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_creds(creds: dict) -> None:
    """Save credentials to disk."""
    CREDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CREDS_FILE.write_text(json.dumps(creds, indent=2))
    CREDS_FILE.chmod(0o600)


def _refresh_token_if_needed(creds: dict) -> dict:
    """Refresh token if expired. Returns updated creds or original if refresh fails."""
    expires_at = creds.get("expires_at")
    if not expires_at:
        return creds

    try:
        expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if now < expires_dt:
            return creds  # Not expired yet
    except (ValueError, AttributeError):
        return creds

    # Token is expired, try to refresh
    refresh_token = creds.get("refresh_token")
    if not refresh_token:
        return creds

    try:
        sb = create_client(
            os.getenv("SUPABASE_URL", ""),
            os.getenv("SUPABASE_ANON_KEY", "")
        )
        res = sb.auth.refresh_session(refresh_token)
        session = res.session
        if not session or not session.access_token:
            return creds

        # Update creds with new tokens
        creds.update({
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "expires_at": session.expires_at,
        })
        _save_creds(creds)
        return creds
    except Exception:
        return creds


@router.get("/api/auth/session")
async def get_auth_session():
    """Get current auth session from CLI credentials file.

    Returns the active Supabase session if credentials exist and are valid.
    Automatically refreshes expired tokens.
    No auth required — only works if you can reach the local server.
    """
    creds = _read_creds()
    if not creds.get("access_token"):
        return {"signed_in": False}

    # Refresh if needed
    creds = _refresh_token_if_needed(creds)

    return {
        "signed_in": True,
        "access_token": creds.get("access_token"),
        "refresh_token": creds.get("refresh_token"),
        "user_id": creds.get("user_id"),
        "email": creds.get("email"),
        "expires_at": creds.get("expires_at"),
    }


@router.post("/api/auth/logout")
async def logout():
    """Sign out and delete CLI credentials.

    Invalidates the Supabase session and removes the local credentials file.
    No auth required — only works if you can reach the local server.
    """
    creds = _read_creds()
    if creds.get("access_token"):
        try:
            sb = create_client(
                os.getenv("SUPABASE_URL", ""),
                os.getenv("SUPABASE_ANON_KEY", "")
            )
            # Set the user's session so sign_out() invalidates the right token
            sb.auth.set_session(
                access_token=creds["access_token"],
                refresh_token=creds.get("refresh_token", "")
            )
            sb.auth.sign_out()
        except Exception:
            pass  # Best effort — delete file regardless

    if CREDS_FILE.exists():
        CREDS_FILE.unlink()

    return {"ok": True}
