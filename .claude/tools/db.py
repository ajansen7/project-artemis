#!/usr/bin/env python3
"""
Artemis DB Helper — Supabase CRUD operations for the job hunting pipeline.

CLI interface for Artemis Supabase database.
Called by Claude via `uv run python .claude/tools/db.py <command>`.

This is a thin shim that forwards to the db_modules package.
"""

import sys
from pathlib import Path

# Add the tools directory to sys.path so db_modules is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from db_modules.cli import main

if __name__ == "__main__":
    main()
