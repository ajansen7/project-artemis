#!/usr/bin/env python3
"""
Backfill user_id for multi-tenant migration.

One-time operation: assigns all existing rows (with NULL user_id) to the
first user in the system. Run this BEFORE migration 021 makes user_id NOT NULL.

Usage:
    uv run python tools/backfill_user_id.py --dry-run    # preview what will change
    uv run python tools/backfill_user_id.py              # apply backfill
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

sb = create_client(os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""))

TABLES = [
    "companies", "jobs", "contacts", "contact_job_links", "contact_interactions",
    "anecdotes", "applications", "cost_log", "engagement_log", "blog_posts",
    "scheduled_jobs", "task_queue", "user_state"
]


def get_first_user():
    """Get the first user from auth.users (or prompt to create one)."""
    try:
        # Try admin.list_users()
        res = sb.auth.admin.list_users()
        if res and len(res.users) > 0:
            user = res.users[0]
            return user.id, user.email
    except Exception as e:
        pass

    # Fallback: query auth.users directly
    try:
        res = sb.from_("auth.users").select("id, email").limit(1).execute()
        if res.data and len(res.data) > 0:
            user = res.data[0]
            return user["id"], user["email"]
    except Exception:
        pass

    # No users found
    print("❌ No users found in auth.users")
    print("Please create a user first. Example:")
    print("  supabase auth users create --email user@example.com --password ...")
    sys.exit(1)


def backfill_dry_run(user_id: str):
    """Show what would be changed without making changes."""
    total_rows = 0
    table_counts = {}

    for table in TABLES:
        try:
            res = sb.table(table).select("id", count="exact").is_("user_id", "null").execute()
            count = len(res.data) if res.data else 0
            if count > 0:
                table_counts[table] = count
                total_rows += count
        except Exception as e:
            print(f"⚠️  Could not check {table}: {e}")

    if total_rows == 0:
        print("✅ No rows need backfilling — all user_id columns already populated")
        return

    print(f"\nWould backfill {total_rows} row(s) across {len(table_counts)} table(s):")
    for table, count in sorted(table_counts.items()):
        print(f"  {table:25s} {count:4d} row(s)")

    print(f"\nTarget user: {user_id}")


def backfill_apply(user_id: str):
    """Actually backfill the rows."""
    total_rows = 0
    table_results = {}

    for table in TABLES:
        try:
            res = sb.table(table).update({"user_id": user_id}).is_("user_id", "null").execute()
            count = len(res.data) if res.data else 0
            if count > 0:
                table_results[table] = count
                total_rows += count
        except Exception as e:
            print(f"❌ Error backfilling {table}: {e}")

    if total_rows == 0:
        print("✅ No rows to backfill — all user_id columns already populated")
        return

    print(f"✅ Backfilled {total_rows} row(s):")
    for table, count in sorted(table_results.items()):
        print(f"  {table:25s} {count:4d} row(s)")


def main():
    parser = argparse.ArgumentParser(description="Backfill user_id for multi-tenant migration")
    parser.add_argument("--user-id", default=None, help="User ID to assign (defaults to first user)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    args = parser.parse_args()

    if args.user_id:
        user_id = args.user_id
        print(f"Using specified user: {user_id}")
    else:
        user_id, email = get_first_user()
        print(f"Using first user: {email} ({user_id})")

    print()

    if args.dry_run:
        backfill_dry_run(user_id)
    else:
        backfill_apply(user_id)


if __name__ == "__main__":
    main()
