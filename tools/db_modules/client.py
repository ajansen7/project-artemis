"""Supabase client factory — dual-mode auth (user JWT or service-role)."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# Load .env from project root (tools/db_modules/ is 2 levels below root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL:
    print("ERROR: SUPABASE_URL must be set in .env")
    sys.exit(1)

CREDS_FILE = Path.home() / ".artemis" / "credentials.json"


def _load_creds() -> dict:
    """Load stored user credentials, or return empty dict."""
    if CREDS_FILE.exists():
        try:
            return json.loads(CREDS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _is_token_expired(expires_at: int) -> bool:
    """Check if token has expired."""
    return datetime.fromtimestamp(expires_at, tz=timezone.utc) < datetime.now(timezone.utc)


def _refresh_token_if_needed(creds: dict) -> dict:
    """Refresh expired token automatically."""
    if not creds.get("refresh_token"):
        return creds

    expires_at = creds.get("expires_at", 0)
    if not _is_token_expired(expires_at):
        return creds

    # Token expired — try to refresh
    try:
        sb = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        res = sb.auth.refresh_session(creds["refresh_token"])
        session = res.session
        if session and session.access_token:
            creds.update({
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "expires_at": session.expires_at,
            })
            CREDS_FILE.parent.mkdir(parents=True, exist_ok=True)
            CREDS_FILE.write_text(json.dumps(creds, indent=2))
            return creds
    except Exception:
        pass

    return creds


def get_client():
    """
    Get a Supabase client with the appropriate auth mode:
    - If user is signed in (~/.artemis/credentials.json), use user JWT (RLS applies)
    - Otherwise, use service-role key (admin access, no RLS)
    """
    creds = _load_creds()
    if creds.get("access_token"):
        # User is signed in — use JWT with automatic refresh
        creds = _refresh_token_if_needed(creds)
        # Only use user JWT if the token is still valid after refresh attempt.
        # If refresh failed (rotated/expired refresh token), fall through to service role.
        if creds.get("access_token") and not _is_token_expired(creds.get("expires_at", 0)):
            sb = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            # Don't pass refresh_token — _refresh_token_if_needed already handled rotation.
            # Passing it here causes set_session to attempt another refresh, which fails
            # with 400 if the token was already rotated by another session.
            sb.auth.set_session(
                access_token=creds["access_token"],
                refresh_token=creds.get("refresh_token", ""),
            )
            return sb

    # Fallback to service role (admin/migrations/internal tools)
    if not SUPABASE_SERVICE_ROLE_KEY:
        print("ERROR: No user signed in and SUPABASE_SERVICE_ROLE_KEY not set in .env")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def get_current_user_id() -> str | None:
    """Get the current user's ID from credentials, or None if not signed in."""
    creds = _load_creds()
    return creds.get("user_id")


# Deprecated: Use get_client() instead
# sb = get_client()  # Don't evaluate at import time
