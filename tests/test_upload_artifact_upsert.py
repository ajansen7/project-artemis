"""Unit tests for _upload_artifact_to_storage.

We patch the Supabase client so we can inspect exactly how `.upload(...)` is
called and simulate storage-side failures without needing a live bucket.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set minimal .env values to prevent early exit in client.py
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "fake-anon-key")

from tools import generate_resume_docx as gen  # noqa: E402


def _fake_client_calls(upload_side_effect=None):
    """Build a fake supabase client where .storage.from_().upload returns a mock
    whose behavior we control. Returns (client, upload_mock)."""
    upload_mock = MagicMock()
    if upload_side_effect is not None:
        upload_mock.side_effect = upload_side_effect
    bucket = MagicMock()
    bucket.upload = upload_mock
    storage = MagicMock()
    storage.from_ = MagicMock(return_value=bucket)
    client = MagicMock()
    client.storage = storage
    return client, upload_mock


@patch("supabase.create_client")
@patch("tools.db_modules.client.get_current_user_id", return_value="user-123")
def test_upload_passes_upsert_true(_user_id, mock_create_client, tmp_path):
    """The upload call must include file_options={'upsert': 'true'}."""
    client, upload_mock = _fake_client_calls()
    mock_create_client.return_value = client

    pdf = tmp_path / "resume.pdf"
    pdf.write_bytes(b"fake pdf bytes")

    path = gen._upload_artifact_to_storage(
        job_id="job-1", file_path=str(pdf), company="Acme", title="PM"
    )

    assert path is not None
    assert upload_mock.call_count == 1
    _args, kwargs = upload_mock.call_args
    assert kwargs.get("file_options") == {"upsert": "true"}, (
        f"upsert flag missing — got kwargs={kwargs}"
    )


class _FakeStorageError(Exception):
    pass


@patch("supabase.create_client")
@patch("tools.db_modules.client.get_current_user_id", return_value="user-123")
def test_upload_failure_propagates(_user_id, mock_create_client, tmp_path):
    """A Supabase upload error must surface as an exception, not a silent None."""
    client, _ = _fake_client_calls(upload_side_effect=_FakeStorageError("409 conflict"))
    mock_create_client.return_value = client

    pdf = tmp_path / "resume.pdf"
    pdf.write_bytes(b"fake pdf bytes")

    with pytest.raises(_FakeStorageError):
        gen._upload_artifact_to_storage(
            job_id="job-1", file_path=str(pdf), company="Acme", title="PM"
        )
