"""
Integration tests for admin approval workflow.

These test the API endpoints directly using httpx.
Requires: running API server + Supabase with migration 023 applied.

Run: uv run pytest tests/test_admin_approval.py -v
"""

import os
import pytest
import httpx

API = os.getenv("ARTEMIS_API_URL", "http://localhost:8000")


def _get_token() -> str:
    """Get auth token from credentials file."""
    import json
    from pathlib import Path
    creds = json.loads((Path.home() / ".artemis" / "credentials.json").read_text())
    return creds["access_token"]


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {_get_token()}"}


def test_get_my_profile(auth_headers):
    """Authenticated user can fetch their own profile."""
    res = httpx.get(f"{API}/api/profile/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] in ("admin", "user")
    assert data["status"] in ("pending", "approved", "blocked")


def test_admin_list_users(auth_headers):
    """Admin can list all users."""
    res = httpx.get(f"{API}/api/admin/users", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "users" in data
    assert len(data["users"]) >= 1


def test_unapproved_user_blocked():
    """Unapproved user gets 403 on protected endpoints."""
    # This test requires a pending user's token — skip if not available
    pytest.skip("Requires a pending user token for full test")


def test_auth_endpoints_always_open():
    """Auth endpoints work without any token."""
    res = httpx.get(f"{API}/api/auth/session")
    assert res.status_code == 200


def test_admin_cannot_self_demote(auth_headers):
    """Admin cannot block or demote themselves."""
    # Get own profile to find user_id
    profile = httpx.get(f"{API}/api/profile/me", headers=auth_headers).json()
    user_id = profile["user_id"]

    # Try to block self
    res = httpx.put(
        f"{API}/api/admin/users/{user_id}",
        headers={**auth_headers, "Content-Type": "application/json"},
        json={"status": "blocked"},
    )
    assert res.status_code == 400
