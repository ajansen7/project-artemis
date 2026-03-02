"""
Google Workspace tools — Drive and Gmail API wrappers.

OAuth scopes are intentionally limited:
  - Drive: read-only
  - Gmail: read + drafts (no autonomous send)
"""

from __future__ import annotations

import structlog

from agents.config import settings

logger = structlog.get_logger()


# ─── Google Drive ───────────────────────────────────────────────


async def list_drive_files(folder_id: str | None = None) -> list[dict]:
    """List files in a Google Drive folder.

    Phase 1: Used to locate master resume, anecdote docs, etc.
    """
    # TODO: Implement with google-api-python-client
    # Scope: https://www.googleapis.com/auth/drive.readonly
    logger.info("drive.list_files", folder_id=folder_id)
    return []


async def download_drive_file(file_id: str) -> str:
    """Download a Google Drive file as text content."""
    # TODO: Implement with google-api-python-client
    logger.info("drive.download", file_id=file_id)
    return ""


# ─── Gmail ──────────────────────────────────────────────────────


async def search_inbox(query: str, max_results: int = 10) -> list[dict]:
    """Search Gmail inbox with a query string.

    Phase 3: Monitor for recruiter responses.
    Scope: https://www.googleapis.com/auth/gmail.readonly
    """
    # TODO: Implement with google-api-python-client
    logger.info("gmail.search", query=query, max_results=max_results)
    return []


async def create_draft(to: str, subject: str, body: str) -> dict:
    """Create a draft email in Gmail.

    Phase 3: Draft follow-up emails for user review.
    Scope: https://www.googleapis.com/auth/gmail.compose
    """
    # TODO: Implement with google-api-python-client
    logger.info("gmail.create_draft", to=to, subject=subject)
    return {}
