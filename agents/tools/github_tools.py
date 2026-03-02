"""
GitHub API tools — repository and commit data fetching.
"""

from __future__ import annotations

import httpx
import structlog

from agents.config import settings

logger = structlog.get_logger()

GITHUB_API_BASE = "https://api.github.com"


async def get_user_repos() -> list[dict]:
    """Fetch all public repos for the configured GitHub user."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/users/{settings.github_username}/repos",
            headers=_auth_headers(),
            params={"sort": "updated", "per_page": 100},
            timeout=15.0,
        )
        response.raise_for_status()
        repos = response.json()
        logger.info("github.repos", count=len(repos))
        return repos


async def get_repo_readme(repo_name: str) -> str:
    """Fetch the README content for a specific repo."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{settings.github_username}/{repo_name}/readme",
            headers={**_auth_headers(), "Accept": "application/vnd.github.raw+json"},
            timeout=15.0,
        )
        if response.status_code == 404:
            return ""
        response.raise_for_status()
        return response.text


async def get_repo_languages(repo_name: str) -> dict[str, int]:
    """Fetch language breakdown (bytes) for a repo."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{settings.github_username}/{repo_name}/languages",
            headers=_auth_headers(),
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()


async def get_recent_commits(repo_name: str, limit: int = 20) -> list[dict]:
    """Fetch recent commit messages for a repo."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{settings.github_username}/{repo_name}/commits",
            headers=_auth_headers(),
            params={"per_page": limit},
            timeout=15.0,
        )
        response.raise_for_status()
        commits = response.json()
        return [
            {
                "sha": c["sha"][:7],
                "message": c["commit"]["message"],
                "date": c["commit"]["author"]["date"],
            }
            for c in commits
        ]


def _auth_headers() -> dict[str, str]:
    """Build auth headers if a GitHub token is configured."""
    headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers
