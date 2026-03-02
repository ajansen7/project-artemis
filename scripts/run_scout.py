#!/usr/bin/env python3
"""
CLI script to manually trigger the autonomous Scout Agent.

Usage:
    uv run python scripts/run_scout.py
"""

import asyncio
import structlog

structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer(),
    ],
)

from agents.nodes.scout import scout_jobs


async def main():
    print("\n🔍 Running Project Artemis Scout Agent (Autonomous Mode)...")
    print("   The agent will search, reason, and follow leads autonomously.\n")

    result = await scout_jobs({})

    leads = result.get("scouted_count", 0)
    companies = result.get("target_companies_added", 0)
    calls = result.get("tool_calls", 0)

    print(f"\n{'='*60}")
    print(f"✅ Scout complete!")
    print(f"   Tool calls used:      {calls}")
    print(f"   Job leads saved:      {leads}")
    print(f"   Target companies:     {companies}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
