#!/usr/bin/env python3
"""
import_personal.py — restore personal Artemis state from an export archive.

Usage:
    uv run python .claude/tools/import_personal.py <archive.tar.gz> [--dry-run] [--force]

Options:
    --dry-run   Show what would be written without touching the filesystem
    --force     Overwrite existing files without prompting (default: prompt)

The archive must have been created by export_personal.py.  Paths inside are
relative to the project root, so just run this from anywhere in the repo.
"""

import argparse
import sys
import tarfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Sanity-check: only allow paths that look like project-local personal content.
# This prevents a malicious/corrupted archive from writing anywhere on the system.
ALLOWED_PREFIXES = (
    ".env",
    "frontend/.env",
    ".claude/CLAUDE.local.md",
    ".claude/memory/",
    ".claude/skills/hunt/references/",
    ".claude/skills/apply/references/",
    ".claude/skills/interview-coach/",
    ".claude/skills/blogger/references/",
    "channels/.claude/",
)


def is_safe(member_name: str) -> bool:
    """Return True if the archive member path is within an allowed prefix."""
    # Normalise: strip leading "./" literally (not individual chars)
    name = member_name.removeprefix("./")
    return any(name == p.rstrip("/") or name.startswith(p) for p in ALLOWED_PREFIXES)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Artemis personal state")
    parser.add_argument("archive", help="Path to the .tar.gz export archive")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be written without touching the filesystem",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files without prompting",
    )
    args = parser.parse_args()

    archive_path = Path(args.archive)
    if not archive_path.exists():
        print(f"Archive not found: {archive_path}", file=sys.stderr)
        sys.exit(1)

    if not tarfile.is_tarfile(archive_path):
        print(f"Not a valid tar archive: {archive_path}", file=sys.stderr)
        sys.exit(1)

    with tarfile.open(archive_path, "r:gz") as tar:
        members = tar.getmembers()

        # Safety check
        blocked = [m.name for m in members if not is_safe(m.name)]
        if blocked:
            print("Archive contains unexpected paths — aborting for safety:", file=sys.stderr)
            for b in blocked:
                print(f"  {b}", file=sys.stderr)
            sys.exit(1)

        files = [m for m in members if m.isfile()]
        print(f"Archive contains {len(files)} file(s):\n")

        skipped = []
        to_write = []

        for member in files:
            dest = PROJECT_ROOT / member.name
            exists = dest.exists()
            status = "[overwrite]" if exists else "[new]"
            print(f"  {status} {member.name}")
            if exists and not args.force and not args.dry_run:
                skipped.append(member)
            else:
                to_write.append(member)

        if skipped:
            print(
                f"\n{len(skipped)} file(s) already exist.  "
                "Re-run with --force to overwrite, or confirm below."
            )
            answer = input("Overwrite existing files? [y/N] ").strip().lower()
            if answer == "y":
                to_write.extend(skipped)
            else:
                print("Skipping existing files.")

        if args.dry_run:
            print("\nDry run — no files written.")
            return

        if not to_write:
            print("\nNothing to write.")
            return

        written = 0
        for member in to_write:
            dest = PROJECT_ROOT / member.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as src, open(dest, "wb") as dst:
                dst.write(src.read())
            written += 1

        print(f"\nImported {written} file(s) into {PROJECT_ROOT}")
        print("\nNext steps:")
        print("  1. Run `uv sync` to install dependencies")
        print("  2. Start services: ./scripts/start.sh")


if __name__ == "__main__":
    main()
