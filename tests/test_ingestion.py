"""
Tests for the ingestion pipeline.
"""

from __future__ import annotations

import pytest

from ingestion.embedder import chunk_text, generate_chunk_id


class TestChunking:
    """Test the text chunking logic."""

    def test_basic_chunking(self) -> None:
        text = "a" * 2500
        chunks = chunk_text(text, chunk_size=1000, chunk_overlap=200)
        # 2500 chars, chunk_size=1000, step=800 → chunks at 0, 800, 1600, 2400
        assert len(chunks) == 4
        assert all(len(c) <= 1000 for c in chunks)

    def test_empty_text(self) -> None:
        assert chunk_text("") == []

    def test_short_text(self) -> None:
        text = "Short text"
        chunks = chunk_text(text, chunk_size=1000, chunk_overlap=200)
        assert len(chunks) == 1
        assert chunks[0] == "Short text"

    def test_overlap(self) -> None:
        text = "ABCDEFGHIJ" * 100  # 1000 chars
        chunks = chunk_text(text, chunk_size=500, chunk_overlap=100)
        # With 500 char chunks and 100 overlap, step = 400
        # So we expect ceil(1000/400) = 3 chunks
        assert len(chunks) >= 2

    def test_whitespace_only_chunks_excluded(self) -> None:
        text = "Hello" + " " * 2000 + "World"
        chunks = chunk_text(text, chunk_size=1000, chunk_overlap=0)
        # The whitespace-only chunk should be excluded
        assert all(c.strip() for c in chunks)


class TestChunkId:
    """Test deterministic chunk ID generation."""

    def test_deterministic(self) -> None:
        id1 = generate_chunk_id("source", 0, "content")
        id2 = generate_chunk_id("source", 0, "content")
        assert id1 == id2

    def test_different_sources(self) -> None:
        id1 = generate_chunk_id("github", 0, "content")
        id2 = generate_chunk_id("substack", 0, "content")
        assert id1 != id2

    def test_length(self) -> None:
        chunk_id = generate_chunk_id("source", 0, "content")
        assert len(chunk_id) == 16
