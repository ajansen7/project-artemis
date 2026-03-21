#!/usr/bin/env python3
"""
Artemis Sync State — Bidirectional sync checker for cross-skill data freshness.

Checks all sync directions between skills and reports what is stale.
Replaces the single-direction check-context.sh with comprehensive checks.

Usage:
    uv run python .claude/tools/sync_state.py --check    # Report-only
    uv run python .claude/tools/sync_state.py --auto     # Auto-sync safe operations + report
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ─── File paths ──────────────────────────────────────────────────

PATHS = {
    "coaching_state": PROJECT_ROOT / ".claude/skills/interview-coach/coaching_state.md",
    "candidate_context": PROJECT_ROOT / ".claude/skills/hunt/references/candidate_context.md",
    "resume_master": PROJECT_ROOT / ".claude/skills/apply/references/resume_master.md",
    "identity": PROJECT_ROOT / ".claude/memory/hot/identity.md",
    "voice": PROJECT_ROOT / ".claude/memory/hot/voice.md",
    "active_loops": PROJECT_ROOT / ".claude/memory/hot/active_loops.md",
    "preferences": PROJECT_ROOT / ".claude/skills/hunt/references/preferences.md",
    "contacts_pipeline": PROJECT_ROOT / "output/contacts_pipeline.md",
    "sync_manifest": PROJECT_ROOT / ".claude/memory/hot/sync_manifest.json",
}


def _mtime(path):
    """Get file modification time as ISO string, or None if file doesn't exist."""
    if path.exists():
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    return None


def _load_manifest():
    """Load the sync manifest, or return empty state."""
    manifest_path = PATHS["sync_manifest"]
    if manifest_path.exists():
        try:
            return json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_checked": None, "directions": {}}


def _save_manifest(manifest):
    """Save the sync manifest."""
    manifest_path = PATHS["sync_manifest"]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest["last_checked"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


def check_all():
    """Check all sync directions and return a report."""
    issues = []

    # 1. coaching_state.md → candidate_context.md
    coaching_mt = _mtime(PATHS["coaching_state"])
    context_mt = _mtime(PATHS["candidate_context"])

    if not PATHS["candidate_context"].exists() and PATHS["coaching_state"].exists():
        issues.append({
            "direction": "coaching → context",
            "severity": "critical",
            "message": "candidate_context.md does not exist but coaching_state.md does. Run /context to build it.",
        })
    elif coaching_mt and context_mt and coaching_mt > context_mt:
        issues.append({
            "direction": "coaching → context",
            "severity": "critical",
            "message": "candidate_context.md is stale (coaching_state.md updated more recently). Run /context to refresh.",
        })

    # 2. identity.md / voice.md → candidate_context.md
    for name in ("identity", "voice"):
        file_mt = _mtime(PATHS[name])
        if file_mt and context_mt and file_mt > context_mt:
            issues.append({
                "direction": f"{name} → context",
                "severity": "advisory",
                "message": f"{name}.md changed since last context build. Consider running /context.",
            })

    # 3. coaching_state storybank → resume_master (advisory only)
    coaching_mt = _mtime(PATHS["coaching_state"])
    resume_mt = _mtime(PATHS["resume_master"])
    if coaching_mt and resume_mt and coaching_mt > resume_mt:
        issues.append({
            "direction": "storybank → resume",
            "severity": "advisory",
            "message": "coaching_state.md updated since resume_master.md. New stories may suggest stronger resume bullets. Run /context to check.",
        })

    # 4. resume_master → coaching_state (advisory only)
    if resume_mt and coaching_mt and resume_mt > coaching_mt:
        issues.append({
            "direction": "resume → coaching",
            "severity": "advisory",
            "message": "resume_master.md updated since coaching_state.md. Resume positioning changes may not be reflected in coaching.",
        })

    # 5. preferences → candidate_context
    prefs_mt = _mtime(PATHS["preferences"])
    if prefs_mt and context_mt and prefs_mt > context_mt:
        issues.append({
            "direction": "preferences → context",
            "severity": "advisory",
            "message": "preferences.md changed since last context build. Target companies/roles may be out of sync. Run /context.",
        })

    # 6. Contacts pipeline freshness (auto-syncable)
    pipeline_mt = _mtime(PATHS["contacts_pipeline"])
    if pipeline_mt:
        # Check if it's more than 1 hour old
        pipeline_age = datetime.now(timezone.utc) - datetime.fromisoformat(pipeline_mt)
        if pipeline_age.total_seconds() > 3600:
            issues.append({
                "direction": "contacts DB → pipeline.md",
                "severity": "auto",
                "message": "contacts_pipeline.md is over 1 hour old. Can auto-sync.",
            })

    return issues


def auto_sync():
    """Perform safe auto-syncs (DB → markdown views)."""
    synced = []

    # Auto-sync contacts pipeline
    sync_script = PROJECT_ROOT / ".claude/tools/sync_contacts.py"
    if sync_script.exists():
        try:
            subprocess.run(
                ["uv", "run", "python", str(sync_script)],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                timeout=15,
            )
            synced.append("contacts_pipeline.md")
        except (subprocess.TimeoutExpired, OSError):
            pass

    return synced


def main():
    parser = argparse.ArgumentParser(description="Artemis Sync State Checker")
    parser.add_argument("--check", action="store_true", help="Report-only: show stale directions")
    parser.add_argument("--auto", action="store_true", help="Auto-sync safe operations + report")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.check and not args.auto:
        args.check = True

    issues = check_all()
    manifest = _load_manifest()

    # Perform auto-syncs if requested
    auto_synced = []
    if args.auto:
        auto_synced = auto_sync()
        # Remove auto-syncable issues that were resolved
        issues = [i for i in issues if i["severity"] != "auto"]

    # Update manifest
    manifest["last_checked"] = datetime.now(timezone.utc).isoformat()
    for issue in issues:
        manifest["directions"][issue["direction"]] = {
            "severity": issue["severity"],
            "message": issue["message"],
            "checked_at": manifest["last_checked"],
        }
    _save_manifest(manifest)

    if args.json:
        output = {"issues": issues, "auto_synced": auto_synced}
        print(json.dumps(output, indent=2))
        return

    # Human-readable output
    critical = [i for i in issues if i["severity"] == "critical"]
    advisory = [i for i in issues if i["severity"] == "advisory"]

    if not issues and not auto_synced:
        # Silent when everything is in sync — don't clutter the hook output
        return

    if critical:
        for i in critical:
            print(f"SYNC WARNING [{i['direction']}]: {i['message']}")

    if advisory:
        for i in advisory:
            print(f"SYNC NOTE [{i['direction']}]: {i['message']}")

    if auto_synced:
        print(f"Auto-synced: {', '.join(auto_synced)}")


if __name__ == "__main__":
    main()
