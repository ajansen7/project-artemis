"""Batch job operations (add/update via JSON stdin)."""

import json
import sys

from db_modules.client import get_client, get_current_user_id
from db_modules.helpers import _ensure_company


def batch_update(args):
    """Batch update multiple jobs from JSON on stdin.

    Expected JSON format (array):
    [
      {"id": "uuid", "status": "to_review", "match_score": 75},
      {"id": "uuid", "status": "deleted", "reason": "Posting removed"},
      {"id": "uuid", "match_score": 60}
    ]
    """
    sb = get_client()
    raw = sys.stdin.read().strip()
    if not raw:
        print("ERROR: No JSON provided on stdin")
        sys.exit(1)

    try:
        updates = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        sys.exit(1)

    if not isinstance(updates, list):
        print("ERROR: Expected a JSON array")
        sys.exit(1)

    ok, fail = 0, 0
    for item in updates:
        job_id = item.get("id")
        if not job_id:
            print(f"⚠️  Skipping entry with no 'id': {item}")
            fail += 1
            continue

        data = {}
        if "status" in item:
            data["status"] = item["status"]
        if "match_score" in item:
            data["match_score"] = max(0, min(100, int(item["match_score"])))
        if "reason" in item:
            data["rejection_reason"] = item["reason"]
        if "description" in item:
            data["description_md"] = item["description"]

        if not data:
            print(f"⚠️  No fields to update for {job_id}")
            fail += 1
            continue

        result = sb.table("jobs").update(data).eq("id", job_id).execute()
        if result.data:
            ok += 1
        else:
            print(f"❌ Job {job_id} not found")
            fail += 1

    print(f"\n✅ Batch update complete: {ok} updated, {fail} failed/skipped (of {len(updates)} total)")


def batch_add(args):
    """Batch add multiple jobs from JSON on stdin.

    Expected JSON format (array):
    [
      {"title": "Senior PM", "company": "Anthropic", "url": "https://...", "description": "...", "match_score": 85, "source": "scout"},
      {"title": "PM", "company": "Cursor", "url": "https://...", "match_score": 72}
    ]
    """
    sb = get_client()
    user_id = get_current_user_id()
    raw = sys.stdin.read().strip()
    if not raw:
        print("ERROR: No JSON provided on stdin")
        sys.exit(1)

    try:
        jobs_data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        sys.exit(1)

    if not isinstance(jobs_data, list):
        print("ERROR: Expected a JSON array")
        sys.exit(1)

    TERMINAL_STATUSES = {"rejected", "not_interested", "deleted"}

    ok, skipped, fail = 0, 0, 0
    for item in jobs_data:
        title = item.get("title")
        company = item.get("company")
        if not title or not company:
            print(f"⚠️  Skipping entry missing title or company: {item}")
            fail += 1
            continue

        url = item.get("url", "")
        if url:
            existing = sb.table("jobs").select("id, status").eq("url", url).execute()
            if existing.data:
                existing_status = existing.data[0].get("status", "")
                if existing_status in TERMINAL_STATUSES:
                    print(f"⚠️  Skipping '{title}' at {company} — already exists with status '{existing_status}'")
                skipped += 1
                continue

        # No URL or URL didn't match — check by company+title to avoid duplicates
        companies_res = sb.table("companies").select("id").ilike("name", f"%{company}%").execute()
        company_ids = [c["id"] for c in (companies_res.data or [])]
        if company_ids:
            existing_q = sb.table("jobs").select("id, status").in_("company_id", company_ids).ilike("title", f"%{title[:40]}%").execute()
            if existing_q.data:
                existing_status = existing_q.data[0].get("status", "")
                if existing_status in TERMINAL_STATUSES:
                    print(f"⚠️  Skipping '{title}' at {company} — already exists with status '{existing_status}'")
                else:
                    print(f"ℹ️  Skipping '{title}' at {company} — already in pipeline (status: {existing_status})")
                skipped += 1
                continue

        company_id = _ensure_company(company)
        data = {
            "title": title,
            "url": url or None,
            "description_md": item.get("description"),
            "status": item.get("status", "scouted"),
            "source": item.get("source", "scout"),
        }
        if company_id:
            data["company_id"] = company_id
        if user_id:
            data["user_id"] = user_id
        if "match_score" in item:
            data["match_score"] = max(0, min(100, int(item["match_score"])))

        result = sb.table("jobs").insert(data).execute()
        if result.data:
            ok += 1
        else:
            fail += 1

    print(f"\n✅ Batch add complete: {ok} added, {skipped} duplicates skipped, {fail} failed (of {len(jobs_data)} total)")
