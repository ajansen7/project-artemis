#!/usr/bin/env python3
"""
Artemis User Data Migration — reassign all rows from one user to another.

This tool migrates all database rows from one user_id to another, useful for:
- Claiming existing data after creating a new account
- Merging or reassigning user accounts

Usage:
    uv run python tools/migrate_user.py --from-user-id OLD_UUID --dry-run
    uv run python tools/migrate_user.py --from-user-id OLD_UUID --to-user-id NEW_UUID
    uv run python tools/migrate_user.py --from-user-id OLD_UUID  # defaults to current user
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

sb = create_client(os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""))

# All tables with user_id column (from migrations 020-021)
# Keep in sync with tools/backfill_user_id.py
TABLES = [
    "companies", "jobs", "contacts", "contact_job_links", "contact_interactions",
    "anecdotes", "applications", "cost_log", "engagement_log", "blog_posts",
    "scheduled_jobs", "task_queue", "user_state"
]


def _get_current_user_id() -> str:
    """Get the current signed-in user ID from ~/.artemis/credentials.json."""
    creds_file = Path.home() / ".artemis" / "credentials.json"
    if creds_file.exists():
        try:
            creds = json.loads(creds_file.read_text())
            return creds.get("user_id", "")
        except (json.JSONDecodeError, OSError):
            pass
    return ""


def migrate_dry_run(from_user_id: str, to_user_id: str):
    """Show what would be changed without making changes."""
    print(f"\nMigrating FROM: {from_user_id}")
    print(f"Migrating TO:   {to_user_id}\n")

    if from_user_id == to_user_id:
        print("❌ Source and target user IDs are the same")
        sys.exit(1)

    total_rows = 0
    table_counts = {}

    for table in TABLES:
        try:
            res = sb.table(table).select("id", count="exact").eq("user_id", from_user_id).execute()
            count = len(res.data) if res.data else 0
            if count > 0:
                table_counts[table] = count
                total_rows += count
        except Exception as e:
            print(f"⚠️  Could not check {table}: {e}")

    if total_rows == 0:
        print(f"No rows found with user_id = {from_user_id}")
        return

    print(f"Would migrate {total_rows} row(s) across {len(table_counts)} table(s):")
    print()
    for table, count in sorted(table_counts.items()):
        print(f"  {table:25s} {count:4d} row(s)")

    print()
    print("⚠️  This will permanently reassign all data.")
    print("    Run without --dry-run to apply.")


def migrate_apply(from_user_id: str, to_user_id: str):
    """Actually migrate the rows."""
    print(f"\nMigrating FROM: {from_user_id}")
    print(f"Migrating TO:   {to_user_id}\n")

    if from_user_id == to_user_id:
        print("❌ Source and target user IDs are the same")
        sys.exit(1)

    total_rows = 0
    table_results = {}
    failed_tables = []

    for table in TABLES:
        try:
            res = sb.table(table).update({"user_id": to_user_id}).eq("user_id", from_user_id).execute()
            count = len(res.data) if res.data else 0
            if count > 0:
                table_results[table] = count
                total_rows += count
        except Exception as e:
            print(f"❌ Error migrating {table}: {e}")
            failed_tables.append(table)

    if failed_tables:
        print(f"\n❌ Migration failed on {len(failed_tables)} table(s):")
        for table in failed_tables:
            print(f"  - {table}")
        print("\n⚠️  Partial migration occurred. Some rows may have been migrated.")
        sys.exit(1)

    if total_rows == 0:
        print(f"No rows found with user_id = {from_user_id}")
        return

    print(f"✅ Migrated {total_rows} row(s):")
    print()
    for table, count in sorted(table_results.items()):
        print(f"  {table:25s} {count:4d} row(s)")

    print()
    print("✅ Data migration complete.")
    print("")
    print("Next step: refresh your local state files:")
    print("  uv run python tools/state_sync.py --pull")


def main():
    parser = argparse.ArgumentParser(description="Artemis User Data Migration")
    parser.add_argument("--from-user-id", required=True, help="User ID to migrate FROM (required)")
    parser.add_argument("--to-user-id", default=None, help="User ID to migrate TO (defaults to current user)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    args = parser.parse_args()

    from_user_id = args.from_user_id

    # Resolve target user
    if args.to_user_id:
        to_user_id = args.to_user_id
    else:
        to_user_id = _get_current_user_id()
        if not to_user_id:
            print("❌ No target user specified and not signed in")
            print("   Either: 1) pass --to-user-id, or")
            print("           2) run 'artemis-login login' first")
            sys.exit(1)
        print(f"Using current user as target: {to_user_id}")

    if args.dry_run:
        migrate_dry_run(from_user_id, to_user_id)
    else:
        migrate_apply(from_user_id, to_user_id)


if __name__ == "__main__":
    main()
