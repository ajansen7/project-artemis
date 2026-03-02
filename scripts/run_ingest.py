"""
CLI script to run the full ingestion pipeline.

Usage:
    uv run python scripts/run_ingest.py --all
    uv run python scripts/run_ingest.py --source github
    uv run python scripts/run_ingest.py --source substack
    uv run python scripts/run_ingest.py --source portfolio --json-path ./data/portfolio.json
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import structlog

structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer(),
    ],
)
logger = structlog.get_logger()


async def main(args: argparse.Namespace) -> None:
    """Run ingestion for the specified sources."""
    sources = args.source if args.source != "all" else [
        "github", "substack", "portfolio", "drive", "claude"
    ]
    if isinstance(sources, str):
        sources = [sources]

    total = 0

    for source in sources:
        logger.info("ingest.start", source=source)
        try:
            if source == "github":
                from ingestion.github_ingest import ingest_github
                total += await ingest_github()

            elif source == "substack":
                from ingestion.substack_ingest import ingest_substack
                total += await ingest_substack()

            elif source == "portfolio":
                from ingestion.portfolio_ingest import ingest_portfolio
                total += await ingest_portfolio(json_path=args.json_path)

            elif source == "drive":
                from ingestion.drive_ingest import ingest_drive
                total += await ingest_drive(folder_id=args.drive_folder)

            elif source == "claude":
                from ingestion.claude_ingest import ingest_claude_coach
                if not args.claude_export:
                    logger.error("claude.missing_path", hint="Use --claude-export")
                    continue
                total += await ingest_claude_coach(export_path=args.claude_export)

            else:
                logger.warning("ingest.unknown_source", source=source)

        except Exception as e:
            logger.error("ingest.error", source=source, error=str(e))

    logger.info("ingest.complete", total_chunks=total)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Artemis ingestion pipeline")
    parser.add_argument(
        "--source",
        default="all",
        help="Source to ingest: github, substack, portfolio, drive, claude, or all",
    )
    parser.add_argument("--json-path", help="Path to portfolio JSON export")
    parser.add_argument("--drive-folder", help="Google Drive folder ID")
    parser.add_argument("--claude-export", help="Path to Claude Interview Coach export")

    args = parser.parse_args()
    asyncio.run(main(args))
