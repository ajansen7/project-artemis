"""Integration tests for POST /api/redraft-resume.

Requires the API running locally (default http://localhost:8000) and a valid
auth token cached in ~/.artemis/credentials.json. Mirrors the pattern used in
tests/test_admin_approval.py.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest

API_URL = os.environ.get("ARTEMIS_API_URL", "http://localhost:8000")
CREDENTIALS = Path.home() / ".artemis" / "credentials.json"


def _token() -> str:
    if not CREDENTIALS.exists():
        pytest.skip("No credentials.json — skipping API integration test")
    return json.loads(CREDENTIALS.read_text())["access_token"]


@pytest.fixture(scope="module")
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token()}"}


@pytest.fixture(scope="module")
def any_job_id(auth_headers) -> str:
    """Grab any job id from the jobs list so we can enqueue a re-draft against it."""
    r = httpx.get(f"{API_URL}/api/jobs", headers=auth_headers, timeout=10.0)
    r.raise_for_status()
    jobs = r.json()
    if not jobs:
        pytest.skip("No jobs in DB to test against")
    return jobs[0]["id"]


def test_redraft_resume_requires_job_id(auth_headers):
    r = httpx.post(
        f"{API_URL}/api/redraft-resume",
        headers=auth_headers,
        json={"job_id": ""},
        timeout=10.0,
    )
    assert r.status_code == 400


def test_redraft_resume_queues_task(auth_headers, any_job_id):
    r = httpx.post(
        f"{API_URL}/api/redraft-resume",
        headers=auth_headers,
        json={"job_id": any_job_id},
        timeout=10.0,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "queued"
    assert body["task_id"]
    assert body["name"].startswith("redraft-resume —")


def test_redraft_resume_with_note_packs_skill_args(auth_headers, any_job_id):
    """Note should be appended to skill_args on the queued task row."""
    r = httpx.post(
        f"{API_URL}/api/redraft-resume",
        headers=auth_headers,
        json={"job_id": any_job_id, "note": "lean more into AI eval work"},
        timeout=10.0,
    )
    assert r.status_code == 200, r.text
    task_id = r.json()["task_id"]
    # Fetch the queued task and verify skill_args
    t = httpx.get(f"{API_URL}/api/tasks/{task_id}", headers=auth_headers, timeout=10.0)
    assert t.status_code == 200
    task = t.json()
    assert task["skill"] == "redraft-resume"
    assert "Job ID:" in task["skill_args"]
    assert "lean more into AI eval work" in task["skill_args"]
