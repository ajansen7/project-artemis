#!/usr/bin/env python3
"""
Sync contacts DB → local memory file.

DB is the single source of truth. This script regenerates the markdown
pipeline file from Supabase so the two never drift.

Usage:
  uv run python .claude/tools/sync_contacts.py          # write
  uv run python .claude/tools/sync_contacts.py --check  # diff only
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

# .claude/tools/ is 2 levels below project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

sb = create_client(os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""))

MEMORY_FILE = str(PROJECT_ROOT / "output" / "contacts_pipeline.md")

NEXT_ACTION = {
    "identified":        "Identify outreach angle",
    "draft_ready":       "Send connection request + note",
    "sent":              "Follow up if no response in 5–7 days",
    "connected":         "Send follow-up message",
    "responded":         "Schedule a call",
    "meeting_scheduled": "Prepare for meeting",
    "warm":              "Maintain relationship",
}


def fetch_contacts():
    res = sb.table("contacts").select(
        "id, name, title, linkedin_url, priority, outreach_status, is_personal_connection, "
        "notes, mutual_connection_notes, last_contacted_at, "
        "companies(name), "
        "contact_job_links(jobs(title))"
    ).order("priority").order("outreach_status").execute()
    return res.data or []


def group_by_company(contacts):
    groups = {}
    for c in contacts:
        company = (c.get("companies") or {}).get("name", "Unknown")
        groups.setdefault(company, []).append(c)
    return groups


def render_table(contacts):
    rows = []
    for c in contacts:
        name = c["name"]
        if c.get("is_personal_connection"):
            name += " ★"
        title = c.get("title") or "—"
        linkedin = c.get("linkedin_url") or "—"
        priority = (c.get("priority") or "—").upper()
        status = c.get("outreach_status", "identified")
        next_action = NEXT_ACTION.get(status, "—")
        rows.append(f"| {name} | {title} | {linkedin} | {priority} | {status} | {next_action} |")
    header = "| Name | Title | LinkedIn | Priority | Status | Next Action |"
    sep    = "|------|-------|----------|----------|--------|-------------|"
    return "\n".join([header, sep] + rows)


def render_md(groups):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "---",
        "name: LinkedIn Contact Pipeline",
        "description: All identified LinkedIn contacts per target company with outreach status, priority ranking, and notes",
        "type: project",
        "---",
        "",
        f"# LinkedIn Contact Pipeline — {now}",
        "",
        "**Why:** Track networking contacts so Artemis can manage follow-up timing, avoid duplicate outreach, and build on warm signals across sessions.",
        "**How to apply:** Check before any new outreach session. Update status after Alex sends messages or receives responses.",
        "**Source of truth:** Supabase `contacts` table. Edit status there; run `sync_contacts.py` to regenerate this file.",
        "",
        "---",
        "",
    ]

    for company, contacts in sorted(groups.items()):
        lines.append(f"## {company}")
        lines.append("")
        lines.append(render_table(contacts))

        # Append any notes
        for c in contacts:
            note = c.get("mutual_connection_notes") or c.get("notes")
            if note:
                lines.append(f"\n> **{c['name']}:** {note}")

        lines.append("")
        lines.append("---")
        lines.append("")

    lines += [
        "## Status Legend",
        "- `identified` — contact found, not yet messaged",
        "- `draft_ready` — outreach copy ready, not yet sent",
        "- `sent` — connection request or InMail sent",
        "- `connected` — connection accepted",
        "- `responded` — received a reply",
        "- `meeting_scheduled` — call or meeting booked",
        "- `warm` — ongoing relationship established",
        "",
        "★ = personal connection",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Diff only, don't write")
    args = parser.parse_args()

    contacts = fetch_contacts()
    groups = group_by_company(contacts)
    new_content = render_md(groups)

    memory_path = os.path.abspath(MEMORY_FILE)

    if args.check:
        try:
            with open(memory_path, "r") as f:
                old = f.read()
            if old == new_content:
                print("✅ In sync — no drift detected.")
            else:
                old_lines = set(old.splitlines())
                new_lines = set(new_content.splitlines())
                added = new_lines - old_lines
                removed = old_lines - new_lines
                print(f"⚠️  Drift detected: {len(added)} lines added, {len(removed)} lines removed.")
                print("   Run without --check to resync.")
        except FileNotFoundError:
            print("⚠️  Memory file not found — will be created on next sync.")
        return

    os.makedirs(os.path.dirname(memory_path), exist_ok=True)
    with open(memory_path, "w") as f:
        f.write(new_content)

    print(f"✅ Synced {len(contacts)} contacts → {memory_path}")
    by_status = {}
    for c in contacts:
        s = c.get("outreach_status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
    for s, n in sorted(by_status.items()):
        print(f"   {s:20s} {n}")


if __name__ == "__main__":
    main()
