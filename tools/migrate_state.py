#!/usr/bin/env python3
"""Migrate Artemis state files from legacy .claude/ locations to consolidated state/ directory.

Usage:
    uv run python tools/migrate_state.py              # Run migration
    uv run python tools/migrate_state.py --dry-run     # Preview without changes
    uv run python tools/migrate_state.py --cleanup     # Remove old files after migration
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

# Project root is one level up from tools/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
CLAUDE_DIR = PROJECT_ROOT / ".claude"

# Migration map: (old_path_relative_to_project, new_path_relative_to_state)
MIGRATION_MAP = [
    # Hot memory -> state/
    (".claude/memory/hot/identity.md", "identity.md"),
    (".claude/memory/hot/voice.md", "voice.md"),
    (".claude/memory/hot/active_loops.md", "active_loops.md"),
    (".claude/memory/hot/lessons.md", "lessons.md"),
    (".claude/memory/hot/sync_manifest.json", "sync_manifest.json"),
    # Hunt references -> state/
    (".claude/skills/hunt/references/preferences.md", "preferences.md"),
    (".claude/skills/hunt/references/candidate_context.md", "candidate_context.md"),
    # Apply references -> state/
    (".claude/skills/apply/references/resume_master.md", "resume_master.md"),
    (".claude/skills/apply/references/form_defaults.md", "form_defaults.md"),
    (".claude/skills/apply/references/apply_lessons.md", "apply_lessons.md"),
    # Interview coach -> state/
    (".claude/skills/interview-coach/coaching_state.md", "coaching_state.md"),
    # Blogger references -> state/
    (".claude/skills/blogger/references/blog_archive.md", "blog_archive.md"),
    # Inbox references -> state/
    (".claude/skills/inbox/references/inbox_state.json", "inbox_state.json"),
]

# Example files migration
EXAMPLE_MAP = [
    (".claude/memory/hot/identity.example.md", "examples/identity.example.md"),
    (".claude/memory/hot/voice.example.md", "examples/voice.example.md"),
    (".claude/memory/hot/active_loops.example.md", "examples/active_loops.example.md"),
    (".claude/memory/hot/lessons.example.md", "examples/lessons.example.md"),
    (".claude/memory/hot/sync_manifest.example.json", "examples/sync_manifest.example.json"),
    (".claude/skills/hunt/references/preferences.example.md", "examples/preferences.example.md"),
    (".claude/skills/apply/references/resume_master.example.md", "examples/resume_master.example.md"),
    (".claude/skills/apply/references/form_defaults.example.md", "examples/form_defaults.example.md"),
]


def migrate(dry_run: bool = False, cleanup: bool = False) -> None:
    print(f"{'DRY RUN: ' if dry_run else ''}Migrating state files to {STATE_DIR}\n")

    STATE_DIR.mkdir(exist_ok=True)
    (STATE_DIR / "examples").mkdir(exist_ok=True)

    migrated = []
    skipped = []
    missing = []

    all_maps = MIGRATION_MAP + EXAMPLE_MAP

    for old_rel, new_name in all_maps:
        old_path = PROJECT_ROOT / old_rel
        new_path = STATE_DIR / new_name

        if not old_path.exists():
            missing.append((old_rel, new_name))
            continue

        if new_path.exists():
            # Compare modification times — only overwrite if old is newer
            old_mtime = old_path.stat().st_mtime
            new_mtime = new_path.stat().st_mtime
            if old_mtime <= new_mtime:
                skipped.append((old_rel, new_name, "state/ version is same age or newer"))
                continue

        if not dry_run:
            shutil.copy2(str(old_path), str(new_path))
        migrated.append((old_rel, new_name))

    # Report
    if migrated:
        print("MIGRATED:")
        for old, new in migrated:
            print(f"  {old} -> state/{new}")
    else:
        print("No files needed migration.")

    if skipped:
        print(f"\nSKIPPED ({len(skipped)}):")
        for old, new, reason in skipped:
            print(f"  {old} ({reason})")

    if missing:
        print(f"\nNOT FOUND ({len(missing)}):")
        for old, new in missing:
            print(f"  {old} (expected at state/{new})")

    # Cleanup old files if requested
    if cleanup and not dry_run and migrated:
        print("\nCLEANUP:")
        for old_rel, _ in migrated:
            old_path = PROJECT_ROOT / old_rel
            if old_path.exists():
                old_path.unlink()
                print(f"  Removed: {old_rel}")

    print(f"\nSummary: {len(migrated)} migrated, {len(skipped)} skipped, {len(missing)} not found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate Artemis state files")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    parser.add_argument("--cleanup", action="store_true", help="Remove old files after migration")
    args = parser.parse_args()
    migrate(dry_run=args.dry_run, cleanup=args.cleanup)
