#!/usr/bin/env python3
"""
export_personal.py — bundle all personal/gitignored Artemis state into a
portable archive that can be imported on another machine.

Usage:
    uv run python .claude/tools/export_personal.py [--out PATH]

Output:
    artemis-personal-YYYYMMDD-HHMMSS.tar.gz  (or --out destination)

The archive preserves relative paths from the project root so the importer
can restore files to the right places without any guesswork.
"""

import argparse
import os
import sys
import tarfile
from datetime import datetime
from pathlib import Path

# Resolve project root (two levels up from this script)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# ── Files / globs to include ─────────────────────────────────────────────────
# Add new entries here whenever personal state grows into new locations.
PERSONAL_PATHS = [
    # Secrets / env
    ".env",
    "frontend/.env.local",
    # Local Claude config (personal overrides)
    ".claude/CLAUDE.local.md",
    # Hot memory (all non-example files)
    ".claude/memory/hot",
    # Extended memory index + extras
    ".claude/memory/MEMORY.md",
    ".claude/memory/project_active_loops.md",
    # Skill references — personal content
    ".claude/skills/hunt/references/candidate_context.md",
    ".claude/skills/hunt/references/preferences.md",
    ".claude/skills/apply/references/resume_master.md",
    ".claude/skills/apply/references/apply_lessons.md",
    ".claude/skills/apply/references/resume_template.docx",
    ".claude/skills/apply/references/form_defaults.md",
    ".claude/skills/interview-coach/coaching_state.md",
    ".claude/skills/blogger/references",
    # Channel settings
    "channels/.claude/settings.local.json",
]

EXCLUDE_SUFFIXES = {".example.md", ".example.json"}


def should_skip(path: Path) -> bool:
    return any(path.name.endswith(s) for s in EXCLUDE_SUFFIXES)


def collect_files(root: Path) -> list[Path]:
    """Return all real files to include, relative to root."""
    collected: list[Path] = []
    for rel in PERSONAL_PATHS:
        target = root / rel
        if target.is_file():
            if not should_skip(target):
                collected.append(target.relative_to(root))
        elif target.is_dir():
            for f in sorted(target.rglob("*")):
                if f.is_file() and not should_skip(f):
                    collected.append(f.relative_to(root))
        # silently skip missing paths — they just haven't been created yet
    return collected


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Artemis personal state")
    parser.add_argument(
        "--out",
        metavar="PATH",
        help="Output archive path (default: artemis-personal-TIMESTAMP.tar.gz in cwd)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be included without creating the archive",
    )
    args = parser.parse_args()

    files = collect_files(PROJECT_ROOT)

    if not files:
        print("No personal files found — nothing to export.", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(f"Files that would be exported ({len(files)}):")
        for f in files:
            print(f"  {f}")
        return

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = Path(args.out) if args.out else Path(f"artemis-personal-{timestamp}.tar.gz")

    with tarfile.open(out_path, "w:gz") as tar:
        for rel in files:
            abs_path = PROJECT_ROOT / rel
            tar.add(abs_path, arcname=str(rel))
            print(f"  + {rel}")

    size_kb = out_path.stat().st_size // 1024
    print(f"\nExported {len(files)} files → {out_path}  ({size_kb} KB)")
    print("\nShare this archive, then on the target machine run:")
    print(f"  uv run python .claude/tools/import_personal.py {out_path.name}")


if __name__ == "__main__":
    main()
