"""
GitHub ingestion — fetch repos, READMEs, languages, and commits from ajansen7.
"""

from __future__ import annotations

import structlog

from agents.tools.github_tools import (
    get_user_repos,
    get_repo_readme,
    get_repo_languages,
    get_recent_commits,
)
from ingestion.embedder import embed_and_store

logger = structlog.get_logger()


async def ingest_github() -> int:
    """Fetch and embed all GitHub data for the configured user.

    Returns:
        Total number of chunks stored.
    """
    repos = await get_user_repos()
    total_chunks = 0

    for repo in repos:
        repo_name = repo["name"]
        logger.info("github.ingest.repo", name=repo_name)

        # ── README ──────────────────────────────────────────────
        readme = await get_repo_readme(repo_name)
        if readme:
            chunks = await embed_and_store(
                text=readme,
                source=f"github:{repo_name}:readme",
                content_type="readme",
                tags=[repo_name, "github"],
                timestamp=repo.get("updated_at", ""),
            )
            total_chunks += chunks

        # ── Languages ───────────────────────────────────────────
        languages = await get_repo_languages(repo_name)
        if languages:
            lang_text = (
                f"Repository: {repo_name}\n"
                f"Description: {repo.get('description', 'N/A')}\n"
                f"Languages: {', '.join(languages.keys())}\n"
                f"Language breakdown (bytes): {languages}"
            )
            chunks = await embed_and_store(
                text=lang_text,
                source=f"github:{repo_name}:languages",
                content_type="repo_metadata",
                tags=[repo_name, "github", "languages"],
                timestamp=repo.get("updated_at", ""),
            )
            total_chunks += chunks

        # ── Recent commits ──────────────────────────────────────
        commits = await get_recent_commits(repo_name, limit=20)
        if commits:
            commit_text = f"Recent commits for {repo_name}:\n" + "\n".join(
                f"- [{c['sha']}] ({c['date']}): {c['message']}" for c in commits
            )
            chunks = await embed_and_store(
                text=commit_text,
                source=f"github:{repo_name}:commits",
                content_type="commit_history",
                tags=[repo_name, "github", "commits"],
                timestamp=commits[0]["date"] if commits else "",
            )
            total_chunks += chunks

    logger.info("github.ingest.complete", total_chunks=total_chunks)
    return total_chunks
