#!/usr/bin/env python3
"""
Artemis State Sync — bidirectional sync between local state/ files and Supabase.

Enables multi-machine sync: any machine with the right .env gets the same state.

Usage:
    uv run python tools/state_sync.py --pull     # DB → local (newer wins)
    uv run python tools/state_sync.py --push     # local → DB (newer wins)
    uv run python tools/state_sync.py --seed     # force-push all local state to DB
    uv run python tools/state_sync.py --check    # report sync status
    uv run python tools/state_sync.py --auto     # pull, then sync contacts pipeline
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

sb = create_client(os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""))

STATE_DIR = PROJECT_ROOT / "state"

# Files to sync — keys match filenames in state/
SYNC_FILES = [
    "identity.md",
    "voice.md",
    "active_loops.md",
    "lessons.md",
    "coaching_state.md",
    "resume_master.md",
    "preferences.md",
    "form_defaults.md",
    "apply_lessons.md",
    "blog_archive.md",
    "inbox_state.json",
]


def _get_user_id():
    """Get current user's ID from ~/.artemis/credentials.json, or None if not logged in."""
    creds_file = Path.home() / ".artemis" / "credentials.json"
    if creds_file.exists():
        try:
            creds = json.loads(creds_file.read_text())
            return creds.get("user_id")
        except Exception:
            pass
    return None


def _claim_null_rows(user_id):
    """Claim any existing rows with no user_id (first-time migration for this user)."""
    if not user_id:
        return
    try:
        null_rows = sb.table("user_state").select("id").is_("user_id", "null").execute()
        if null_rows.data:
            ids = [r["id"] for r in null_rows.data]
            sb.table("user_state").update({"user_id": user_id}).in_("id", ids).execute()
            print(f"Claimed {len(ids)} existing state row(s) for this user")
    except Exception as e:
        print(f"WARNING: Could not claim null rows: {e}", file=sys.stderr)


def _local_mtime(path):
    """Get file mtime as a timezone-aware datetime, or None if missing."""
    if path.exists():
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return None


def _db_rows():
    """Fetch all user_state rows for current user, keyed by filename."""
    try:
        user_id = _get_user_id()
        query = sb.table("user_state").select("key, content, updated_at")
        if user_id:
            query = query.eq("user_id", user_id)
        res = query.execute()
        return {row["key"]: row for row in (res.data or [])}
    except Exception as e:
        print(f"WARNING: Could not reach Supabase: {e}", file=sys.stderr)
        return None


def _parse_ts(ts_str):
    """Parse an ISO timestamp from Supabase into a timezone-aware datetime."""
    if not ts_str:
        return None
    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


def pull():
    """Pull state from DB where DB is newer than local."""
    user_id = _get_user_id()

    # On first login, claim any existing rows with no user_id
    if user_id:
        _claim_null_rows(user_id)

    db = _db_rows()
    if db is None:
        return  # offline — silently use local cache

    pulled = []
    for key in SYNC_FILES:
        if key not in db:
            continue
        row = db[key]
        local_path = STATE_DIR / key
        local_mt = _local_mtime(local_path)
        db_mt = _parse_ts(row["updated_at"])

        if local_mt is None or (db_mt and db_mt > local_mt):
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_text(row["content"])
            # Set mtime to match DB so future comparisons work
            if db_mt:
                ts = db_mt.timestamp()
                os.utime(local_path, (ts, ts))
            pulled.append(key)

    if pulled:
        print(f"Pulled {len(pulled)} file(s) from DB: {', '.join(pulled)}")


def push():
    """Push local state to DB where local is newer."""
    user_id = _get_user_id()
    db = _db_rows()
    if db is None:
        print("WARNING: Supabase unreachable — push deferred.", file=sys.stderr)
        return

    pushed = []
    for key in SYNC_FILES:
        local_path = STATE_DIR / key
        if not local_path.exists():
            continue

        content = local_path.read_text()
        local_mt = _local_mtime(local_path)
        row = db.get(key)

        payload = {
            "key": key,
            "content": content,
            "updated_at": local_mt.isoformat() if local_mt else datetime.now(timezone.utc).isoformat(),
        }
        if user_id:
            payload["user_id"] = user_id

        if row is None:
            # New file — insert via upsert with user_id-aware conflict resolution
            on_conflict = "user_id,key" if user_id else "key"
            sb.table("user_state").upsert(payload, on_conflict=on_conflict).execute()
            pushed.append(key)
        else:
            db_mt = _parse_ts(row["updated_at"])
            if local_mt and db_mt and local_mt > db_mt:
                sb.table("user_state").update({
                    "content": content,
                    "updated_at": local_mt.isoformat(),
                }).eq("key", key).execute()
                pushed.append(key)

    if pushed:
        print(f"Pushed {len(pushed)} file(s) to DB: {', '.join(pushed)}")


def seed():
    """Force-push all local state files to DB (first-time upload)."""
    user_id = _get_user_id()
    seeded = []
    for key in SYNC_FILES:
        local_path = STATE_DIR / key
        if not local_path.exists():
            continue

        content = local_path.read_text()
        local_mt = _local_mtime(local_path)
        payload = {
            "key": key,
            "content": content,
            "updated_at": local_mt.isoformat() if local_mt else datetime.now(timezone.utc).isoformat(),
        }
        if user_id:
            payload["user_id"] = user_id

        on_conflict = "user_id,key" if user_id else "key"
        sb.table("user_state").upsert(payload, on_conflict=on_conflict).execute()
        seeded.append(key)

    print(f"Seeded {len(seeded)} file(s) to DB: {', '.join(seeded)}")


def check():
    """Report which files are ahead, behind, or in sync."""
    db = _db_rows()
    if db is None:
        print("Cannot check — Supabase unreachable.")
        return

    for key in SYNC_FILES:
        local_path = STATE_DIR / key
        local_mt = _local_mtime(local_path)
        row = db.get(key)
        db_mt = _parse_ts(row["updated_at"]) if row else None

        if not local_path.exists() and not row:
            status = "missing"
        elif not local_path.exists():
            status = "DB only (pull to restore)"
        elif not row:
            status = "local only (push to upload)"
        elif local_mt and db_mt and local_mt > db_mt:
            status = "local ahead"
        elif local_mt and db_mt and db_mt > local_mt:
            status = "DB ahead"
        else:
            status = "in sync"

        print(f"  {key:25s} {status}")


def auto():
    """Pull state, then sync contacts pipeline."""
    pull()

    sync_script = PROJECT_ROOT / "tools" / "sync_contacts.py"
    if sync_script.exists():
        try:
            subprocess.run(
                ["uv", "run", "python", str(sync_script)],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                timeout=15,
            )
        except (subprocess.TimeoutExpired, OSError):
            pass


def main():
    parser = argparse.ArgumentParser(description="Artemis State Sync")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--pull", action="store_true", help="DB → local (newer wins)")
    group.add_argument("--push", action="store_true", help="Local → DB (newer wins)")
    group.add_argument("--seed", action="store_true", help="Force-push all local state to DB")
    group.add_argument("--check", action="store_true", help="Report sync status")
    group.add_argument("--auto", action="store_true", help="Pull, then sync contacts pipeline")
    args = parser.parse_args()

    if args.pull:
        pull()
    elif args.push:
        push()
    elif args.seed:
        seed()
    elif args.check:
        check()
    elif args.auto:
        auto()
    else:
        check()


if __name__ == "__main__":
    main()
