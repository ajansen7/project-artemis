"""
CLI script to run the Artemis agent graph.

Usage:
    uv run python scripts/run_agents.py --job-url "https://example.com/job/123"
    uv run python scripts/run_agents.py --job-text "Senior PM role at Acme Corp..."
"""

from __future__ import annotations

import argparse
import asyncio

import structlog

from agents.graph import artemis_graph
from agents.state import AgentState

structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer(),
    ],
)
logger = structlog.get_logger()


async def main(args: argparse.Namespace) -> None:
    """Run the Artemis agent graph for a single job."""

    initial_state: AgentState = {}

    if args.job_url:
        initial_state["job_url"] = args.job_url
    elif args.job_text:
        initial_state["job_description_md"] = args.job_text
    else:
        logger.error("No job input provided. Use --job-url or --job-text.")
        return

    logger.info("graph.start", job_url=args.job_url or "(text input)")

    result = await artemis_graph.ainvoke(initial_state)

    match_result = result.get("match_result")
    if match_result:
        logger.info(
            "graph.result",
            match_score=match_result.match_score,
            gaps=len(match_result.gaps),
            recommendations=len(match_result.recommended_actions),
        )
    else:
        logger.warning("graph.no_result")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Artemis agent graph")
    parser.add_argument("--job-url", help="URL of the job posting to analyze")
    parser.add_argument("--job-text", help="Raw job description text")

    args = parser.parse_args()
    asyncio.run(main(args))
