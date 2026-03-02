"""
Substack ingestion — parse RSS feed and embed articles.
"""

from __future__ import annotations

import feedparser
import structlog

from ingestion.embedder import embed_and_store

logger = structlog.get_logger()

SUBSTACK_FEED_URL = "https://thetechnicalpmlab.substack.com/feed"


async def ingest_substack(feed_url: str = SUBSTACK_FEED_URL) -> int:
    """Fetch and embed all Substack articles via RSS.

    Returns:
        Total number of chunks stored.
    """
    logger.info("substack.ingest.start", feed_url=feed_url)

    feed = feedparser.parse(feed_url)
    total_chunks = 0

    for entry in feed.entries:
        title = entry.get("title", "Untitled")
        published = entry.get("published", "")
        content = ""

        # feedparser stores content in 'content' or 'summary'
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].get("value", "")
        elif hasattr(entry, "summary"):
            content = entry.summary

        if not content:
            logger.warning("substack.ingest.empty", title=title)
            continue

        # Strip HTML tags for clean embedding
        from bs4 import BeautifulSoup

        clean_text = BeautifulSoup(content, "html.parser").get_text(
            separator="\n", strip=True
        )

        article_text = f"Title: {title}\nPublished: {published}\n\n{clean_text}"

        chunks = await embed_and_store(
            text=article_text,
            source=f"substack:{title}",
            content_type="article",
            tags=["substack", "thought_leadership"],
            timestamp=published,
        )
        total_chunks += chunks
        logger.info("substack.ingest.article", title=title, chunks=chunks)

    logger.info("substack.ingest.complete", total_chunks=total_chunks)
    return total_chunks
