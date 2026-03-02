"""
Google Drive ingestion — pull master resume, anecdotes, and performance reviews.
"""

from __future__ import annotations

import structlog

from agents.tools.google_tools import list_drive_files, download_drive_file
from ingestion.embedder import embed_and_store

logger = structlog.get_logger()


async def ingest_drive(folder_id: str | None = None) -> int:
    """Fetch and embed documents from Google Drive.

    Targets: master resume, STAR anecdotes, performance reviews.

    Returns:
        Total number of chunks stored.
    """
    logger.info("drive.ingest.start", folder_id=folder_id)

    files = await list_drive_files(folder_id)
    total_chunks = 0

    for file_info in files:
        file_id = file_info.get("id", "")
        file_name = file_info.get("name", "unknown")
        mime_type = file_info.get("mimeType", "")

        # Only process text-based documents
        if not any(
            t in mime_type
            for t in ["text/", "document", "spreadsheet", "presentation"]
        ):
            logger.debug("drive.ingest.skip", name=file_name, mime=mime_type)
            continue

        content = await download_drive_file(file_id)
        if not content:
            continue

        # Determine content type from filename
        content_type = "document"
        tags = ["google_drive"]
        if "resume" in file_name.lower():
            content_type = "resume"
            tags.append("resume")
        elif "anecdote" in file_name.lower() or "star" in file_name.lower():
            content_type = "anecdote"
            tags.append("anecdote")
        elif "review" in file_name.lower() or "performance" in file_name.lower():
            content_type = "performance_review"
            tags.append("review")

        chunks = await embed_and_store(
            text=content,
            source=f"drive:{file_name}",
            content_type=content_type,
            tags=tags,
        )
        total_chunks += chunks
        logger.info("drive.ingest.file", name=file_name, chunks=chunks)

    logger.info("drive.ingest.complete", total_chunks=total_chunks)
    return total_chunks
