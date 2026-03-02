"""
Claude Interview Coach ingestion — parse exported chat history and feedback.
"""

from __future__ import annotations

import json
from pathlib import Path

import structlog

from ingestion.embedder import embed_and_store

logger = structlog.get_logger()


async def ingest_claude_coach(export_path: str) -> int:
    """Parse and embed Claude Interview Coach exports.

    Handles both JSON exports and plain-text chat logs.

    Returns:
        Total number of chunks stored.
    """
    path = Path(export_path)
    if not path.exists():
        logger.warning("claude.ingest.not_found", path=export_path)
        return 0

    total_chunks = 0
    raw = path.read_text(encoding="utf-8")

    # Try JSON first
    try:
        data = json.loads(raw)
        total_chunks = await _ingest_json_export(data)
    except json.JSONDecodeError:
        # Fall back to plain text
        total_chunks = await _ingest_text_export(raw)

    logger.info("claude.ingest.complete", total_chunks=total_chunks)
    return total_chunks


async def _ingest_json_export(data: dict | list) -> int:
    """Ingest structured JSON export from Claude."""
    total_chunks = 0

    # Handle list of conversations
    conversations = data if isinstance(data, list) else [data]

    for i, convo in enumerate(conversations):
        # Extract system prompt if present
        system_prompt = convo.get("system_prompt", "")
        if system_prompt:
            chunks = await embed_and_store(
                text=f"Interview Coach System Prompt:\n{system_prompt}",
                source=f"claude_coach:system_prompt:{i}",
                content_type="system_prompt",
                tags=["claude_coach", "interview_prep"],
            )
            total_chunks += chunks

        # Extract messages / Q&A pairs
        messages = convo.get("messages", convo.get("chat_history", []))
        if messages:
            chat_text = "\n".join(
                f"{m.get('role', 'unknown')}: {m.get('content', '')}" for m in messages
            )
            chunks = await embed_and_store(
                text=chat_text,
                source=f"claude_coach:conversation:{i}",
                content_type="interview_qa",
                tags=["claude_coach", "interview_prep", "qa"],
            )
            total_chunks += chunks

        # Extract feedback / assessment
        feedback = convo.get("feedback", convo.get("assessment", ""))
        if feedback:
            chunks = await embed_and_store(
                text=f"Interview Coach Feedback:\n{feedback}",
                source=f"claude_coach:feedback:{i}",
                content_type="feedback",
                tags=["claude_coach", "interview_prep", "feedback"],
            )
            total_chunks += chunks

    return total_chunks


async def _ingest_text_export(text: str) -> int:
    """Ingest a plain-text chat log."""
    return await embed_and_store(
        text=text,
        source="claude_coach:text_export",
        content_type="interview_qa",
        tags=["claude_coach", "interview_prep"],
    )
