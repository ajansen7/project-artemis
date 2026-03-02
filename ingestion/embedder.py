"""
Shared embedding logic — chunking and vector store insertion.

All ingestion modules use this to process their raw text into
chunks with metadata before upserting into ChromaDB.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import structlog

from agents.tools.vector_tools import upsert_chunks

logger = structlog.get_logger()

# ─── Configuration ──────────────────────────────────────────────

DEFAULT_CHUNK_SIZE = 1000  # characters
DEFAULT_CHUNK_OVERLAP = 200  # characters


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks.

    Uses a simple character-based sliding window. For production,
    consider switching to a semantic chunker (e.g., by paragraph
    or sentence boundaries).
    """
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - chunk_overlap

    return chunks


def generate_chunk_id(source: str, index: int, content: str) -> str:
    """Generate a deterministic ID for a chunk based on source and content."""
    hash_input = f"{source}:{index}:{content[:100]}"
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


async def embed_and_store(
    text: str,
    source: str,
    content_type: str,
    tags: list[str] | None = None,
    timestamp: str | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> int:
    """Chunk text, generate IDs and metadata, and upsert into ChromaDB.

    Args:
        text: Raw text content to embed.
        source: Origin identifier (e.g., "github:Pointing-Magnifier").
        content_type: Type label (e.g., "readme", "article", "anecdote").
        tags: Optional tags for filtering.
        timestamp: ISO timestamp for recency bias. Defaults to now.
        chunk_size: Characters per chunk.
        chunk_overlap: Overlap between adjacent chunks.

    Returns:
        Number of chunks stored.
    """
    chunks = chunk_text(text, chunk_size, chunk_overlap)
    if not chunks:
        return 0

    ts = timestamp or datetime.now(timezone.utc).isoformat()

    ids = [generate_chunk_id(source, i, c) for i, c in enumerate(chunks)]
    metadatas = [
        {
            "source": source,
            "content_type": content_type,
            "timestamp": ts,
            "tags": ",".join(tags or []),
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]

    await upsert_chunks(ids=ids, documents=chunks, metadatas=metadatas)
    logger.info("embed.stored", source=source, chunks=len(chunks))
    return len(chunks)
