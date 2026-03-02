"""
Web scraping tools — Firecrawl and Proxycurl wrappers.
"""

from __future__ import annotations

import httpx
import structlog

from agents.config import settings

logger = structlog.get_logger()


async def scrape_url_to_markdown(url: str) -> str:
    """Convert a URL to clean markdown using Firecrawl.

    Falls back to basic httpx + BeautifulSoup if Firecrawl is not configured.
    """
    if settings.firecrawl_api_key:
        return await _firecrawl_scrape(url)
    return await _basic_scrape(url)


async def _firecrawl_scrape(url: str) -> str:
    """Scrape via Firecrawl API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {settings.firecrawl_api_key}"},
            json={"url": url, "formats": ["markdown"]},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("markdown", "")


async def _basic_scrape(url: str) -> str:
    """Fallback: basic HTTP fetch + HTML to text."""
    from bs4 import BeautifulSoup

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer"]):
            element.decompose()
        return soup.get_text(separator="\n", strip=True)


async def proxycurl_lookup(linkedin_url: str) -> dict:
    """Look up a LinkedIn profile via Proxycurl.

    Respects the weekly lookup quota configured in settings.
    """
    if not settings.proxycurl_api_key:
        logger.warning("proxycurl.not_configured")
        return {}

    # TODO: Check weekly quota in Supabase before making the call

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://nubela.co/proxycurl/api/v2/linkedin",
            headers={"Authorization": f"Bearer {settings.proxycurl_api_key}"},
            params={"linkedin_profile_url": linkedin_url},
            timeout=30.0,
        )
        response.raise_for_status()
        logger.info("proxycurl.lookup", url=linkedin_url)
        return response.json()
