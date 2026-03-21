#!/usr/bin/env python3
"""
Artemis DB Helper — Supabase CRUD operations for the job hunting pipeline.

CLI interface for Artemis Supabase database.
Called by Claude via `uv run python .claude/tools/db.py <command>`.
Reads credentials from .env in the project root.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# Load .env from project root (.claude/tools/ is 2 levels below root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    sys.exit(1)

sb = create_client(SUPABASE_URL, SUPABASE_KEY)


# ─── Jobs ────────────────────────────────────────────────────────


def add_job(args):
    """Add a job to the pipeline."""
    # Check for duplicate URL
    if args.url:
        existing = sb.table("jobs").select("id").eq("url", args.url).execute()
        if existing.data:
            print(f"⚠️  Job already exists with this URL (id: {existing.data[0]['id']})")
            return

    # Ensure company exists and auto-target if score is high
    company_id = None
    if args.company:
        company_id = _ensure_company(args.company, job_score=args.match_score)

    data = {
        "title": args.title,
        "url": args.url or None,
        "description_md": args.description or None,
        "status": args.status or "scouted",
        "source": args.source or "scout",
    }
    if company_id:
        data["company_id"] = company_id
    if args.match_score is not None:
        data["match_score"] = args.match_score

    result = sb.table("jobs").insert(data).execute()
    if result.data:
        job = result.data[0]
        print(f"✅ Saved: {args.title} at {args.company or 'Unknown'} (id: {job['id']}, status: {job['status']})")
    else:
        print("❌ Failed to insert job")


def list_jobs(args):
    """List all jobs, optionally filtered by status."""
    query = sb.table("jobs").select("id, title, url, status, match_score, source, created_at, companies(name)")
    if args.status:
        query = query.eq("status", args.status)
    query = query.order("created_at", desc=True)
    if args.limit:
        query = query.limit(args.limit)

    result = query.execute()
    jobs = result.data or []

    if not jobs:
        print("No jobs found.")
        return

    # Group by status
    by_status = {}
    for j in jobs:
        s = j.get("status", "unknown")
        by_status.setdefault(s, []).append(j)

    for status, status_jobs in by_status.items():
        print(f"\n{'─' * 60}")
        print(f"  {status.upper()} ({len(status_jobs)})")
        print(f"{'─' * 60}")
        for j in status_jobs:
            company = j.get("companies", {})
            company_name = company.get("name", "Unknown") if company else "Unknown"
            score = f" [score: {j['match_score']}]" if j.get("match_score") else ""
            print(f"  • {j['title']} — {company_name}{score}")
            print(f"    id: {j['id']}")
            if j.get("url"):
                print(f"    url: {j['url']}")


def update_job(args):
    """Update a job's status or other fields."""
    data = {}
    if args.status:
        data["status"] = args.status
    if args.match_score is not None:
        data["match_score"] = args.match_score
    if args.reason:
        data["description_md"] = sb.table("jobs").select("description_md").eq("id", args.id).execute().data[0].get("description_md", "") + f"\n\n**Not interested reason:** {args.reason}"
    if getattr(args, "analysis_file", None):
        try:
            with open(args.analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
            data["gap_analysis_json"] = {"markdown": content}
        except Exception as e:
            print(f"❌ Failed to read analysis file: {e}")
            return

    if not data:
        print("Nothing to update. Provide --status, --match-score, or --reason.")
        return

    result = sb.table("jobs").update(data).eq("id", args.id).execute()
    if result.data:
        print(f"✅ Updated job {args.id}: {data}")
    else:
        print(f"❌ Job {args.id} not found")


def get_job(args):
    """Get full details of a specific job."""
    result = sb.table("jobs").select("*, companies(name, domain, careers_url)").eq("id", args.id).execute()
    if not result.data:
        print(f"Job {args.id} not found")
        return

    job = result.data[0]
    company = job.get("companies", {}) or {}
    print(f"\n{'═' * 60}")
    print(f"  {job['title']}")
    print(f"  {company.get('name', 'Unknown Company')}")
    print(f"{'═' * 60}")
    print(f"  Status:      {job['status']}")
    print(f"  Score:       {job.get('match_score', 'not scored')}")
    print(f"  URL:         {job.get('url', 'none')}")
    print(f"  Source:      {job.get('source', 'unknown')}")
    print(f"  Created:     {job.get('created_at', '')}")
    if job.get("description_md"):
        print(f"\n  Description:")
        print(f"  {job['description_md'][:500]}")
    if job.get("gap_analysis_json"):
        print(f"\n  Gap Analysis:")
        print(f"  {json.dumps(job['gap_analysis_json'], indent=2)}")


def save_application(args):
    """Save generated application materials into the applications table."""
    # Read the markdown files
    files = {
        "resume_md": args.resume,
        "cover_letter_md": args.cover_letter,
        "primer_md": args.primer,
        "form_fills_md": getattr(args, "form_fills", None),
    }
    content = {}

    for key, filepath in files.items():
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content[key] = f.read()
            except Exception as e:
                print(f"⚠️ Failed to read {filepath}: {e}")

    if getattr(args, "pdf_path", None):
        content["resume_pdf_path"] = args.pdf_path

    if not content:
        print("❌ No application files provided or found.")
        return

    # Check if an application already exists for this job
    existing = sb.table("applications").select("id").eq("job_id", args.id).execute()

    if existing.data:
        # Update existing
        app_id = existing.data[0]["id"]
        update_res = sb.table("applications").update(content).eq("id", app_id).execute()
        if update_res.data:
            print(f"✅ Updated existing application materials for job {args.id}")
        else:
            print(f"❌ Failed to update application {app_id}")
    else:
        # Insert new
        content["job_id"] = args.id
        insert_res = sb.table("applications").insert(content).execute()
        if insert_res.data:
            print(f"✅ Created new application record with materials for job {args.id}")
        else:
            print(f"❌ Failed to insert application for job {args.id}")


def mark_submitted(args):
    """Mark an application as submitted: set submitted_at and advance job status to 'applied'."""
    now = datetime.now(timezone.utc).isoformat()

    # Update application submitted_at
    app_res = sb.table("applications").update({"submitted_at": now}).eq("job_id", args.id).execute()
    if app_res.data:
        print(f"✅ Application marked submitted at {now}")
    else:
        # Application row may not exist yet — create a minimal one
        sb.table("applications").insert({"job_id": args.id, "submitted_at": now}).execute()
        print(f"✅ Created application record with submitted_at={now}")

    # Advance job status to 'applied'
    job_res = sb.table("jobs").update({"status": "applied"}).eq("id", args.id).execute()
    if job_res.data:
        print(f"✅ Job {args.id} status → applied")


# ─── Companies ───────────────────────────────────────────────────


def add_company(args):
    """Add a target company to the watchlist."""
    existing = sb.table("companies").select("id, is_target").eq("name", args.name).execute()
    if existing.data:
        row = existing.data[0]
        if row.get("is_target"):
            print(f"⚠️  {args.name} is already a target company")
            return
        # Upgrade to target
        update_data = {"is_target": True}
        if args.why:
            update_data["why_target"] = args.why
        if args.priority:
            update_data["scout_priority"] = args.priority
        if args.domain:
            update_data["domain"] = args.domain
        if args.careers_url:
            update_data["careers_url"] = args.careers_url
        sb.table("companies").update(update_data).eq("id", row["id"]).execute()
        print(f"✅ Upgraded {args.name} to target company (priority: {args.priority or 'medium'})")
        return

    data = {
        "name": args.name,
        "domain": args.domain or None,
        "careers_url": args.careers_url or None,
        "is_target": True,
        "why_target": args.why or None,
        "scout_priority": args.priority or "medium",
    }
    result = sb.table("companies").insert(data).execute()
    if result.data:
        print(f"✅ Added {args.name} to target companies (priority: {args.priority or 'medium'})")
    else:
        print(f"❌ Failed to add company")


def list_companies(args):
    """List target companies."""
    query = sb.table("companies").select("id, name, domain, careers_url, why_target, scout_priority, last_scouted_at")
    if not args.all:
        query = query.eq("is_target", True)
    result = query.order("scout_priority").execute()
    companies = result.data or []

    if not companies:
        print("No target companies found.")
        return

    print(f"\n{'─' * 60}")
    print(f"  TARGET COMPANIES ({len(companies)})")
    print(f"{'─' * 60}")
    for c in companies:
        priority = c.get("scout_priority", "?")
        last_scouted = c.get("last_scouted_at", "never")
        print(f"  [{priority}] {c['name']}")
        if c.get("domain"):
            print(f"       domain: {c['domain']}")
        if c.get("careers_url"):
            print(f"       careers: {c['careers_url']}")
        if c.get("why_target"):
            print(f"       why: {c['why_target'][:80]}")
        print()


# ─── Status ──────────────────────────────────────────────────────


def status(args):
    """Show pipeline dashboard."""
    # Count jobs by status
    jobs = sb.table("jobs").select("status").execute()
    counts = {}
    for j in (jobs.data or []):
        s = j.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1

    # Count target companies
    companies = sb.table("companies").select("id").eq("is_target", True).execute()
    target_count = len(companies.data or [])

    print(f"\n{'═' * 40}")
    print(f"  ARTEMIS PIPELINE STATUS")
    print(f"{'═' * 40}")
    total = sum(counts.values())
    print(f"  Total jobs: {total}")
    for s in ["scouted", "to_review", "applied", "recruiter_engaged", "interviewing", "offer", "not_interested", "rejected", "deleted"]:
        if s in counts:
            print(f"    {s:20s} {counts[s]}")
    print(f"\n  Target companies: {target_count}")
    print(f"{'═' * 40}")


# ─── Helpers ─────────────────────────────────────────────────────


def _ensure_company(name, job_score=None):
    """Find or create a company, return its ID. Auto-targets if job_score >= 80."""
    result = sb.table("companies").select("id, is_target").eq("name", name).execute()
    
    if result.data:
        company_id = result.data[0]["id"]
        is_target = result.data[0].get("is_target", False)
        
        if job_score is not None and job_score >= 80 and not is_target:
            priority = "high" if job_score >= 90 else "medium"
            sb.table("companies").update({
                "is_target": True,
                "scout_priority": priority
            }).eq("id", company_id).execute()
            print(f"🌟 Auto-targeted existing company '{name}' (priority: {priority}) due to high job score ({job_score}).")
            
        return company_id

    # Create new company
    data = {"name": name, "is_target": False}
    
    if job_score is not None and job_score >= 80:
        priority = "high" if job_score >= 90 else "medium"
        data["is_target"] = True
        data["scout_priority"] = priority
        print(f"🌟 Created and auto-targeted company '{name}' (priority: {priority}) due to high job score ({job_score}).")

    insert = sb.table("companies").insert(data).execute()
    return insert.data[0]["id"] if insert.data else None


def score_job(args):
    """Set match score for a job (convenience for batch scoring)."""
    score = max(0, min(100, args.score))
    result = sb.table("jobs").update({"match_score": score}).eq("id", args.id).execute()
    if result.data:
        print(f"✅ Scored job {args.id}: {score}/100")
    else:
        print(f"❌ Job {args.id} not found")


def batch_update(args):
    """Batch update multiple jobs from JSON on stdin.

    Expected JSON format (array):
    [
      {"id": "uuid", "status": "to_review", "match_score": 75},
      {"id": "uuid", "status": "deleted", "reason": "Posting removed"},
      {"id": "uuid", "match_score": 60}
    ]
    """
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
            existing = sb.table("jobs").select("id").eq("url", url).execute()
            if existing.data:
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
        if "match_score" in item:
            data["match_score"] = max(0, min(100, int(item["match_score"])))

        result = sb.table("jobs").insert(data).execute()
        if result.data:
            ok += 1
        else:
            fail += 1

    print(f"\n✅ Batch add complete: {ok} added, {skipped} duplicates skipped, {fail} failed (of {len(jobs_data)} total)")


# ─── Contacts ────────────────────────────────────────────────────


def _resolve_job_prefix(prefix):
    """Match a job by ID prefix (first 8 chars). Returns (id, title) or (None, None)."""
    res = sb.table("jobs").select("id, title").execute()
    for row in (res.data or []):
        if row["id"].replace("-", "").startswith(prefix.replace("-", "")):
            return row["id"], row["title"]
    return None, None


def _upsert_contact(data):
    """Insert or update a contact. Deduplicates on linkedin_url if present."""
    linkedin = data.get("linkedin_url")
    if linkedin:
        existing = sb.table("contacts").select("id").eq("linkedin_url", linkedin).execute()
        if existing.data:
            cid = existing.data[0]["id"]
            sb.table("contacts").update(
                {k: v for k, v in data.items() if k != "linkedin_url"}
            ).eq("id", cid).execute()
            return cid, "updated"
    res = sb.table("contacts").insert(data).execute()
    if res.data:
        return res.data[0]["id"], "inserted"
    return None, "failed"


def _link_contact_job(contact_id, job_id, notes=None):
    """Create a contact_job_links row if it doesn't already exist."""
    if not contact_id or not job_id:
        return
    existing = sb.table("contact_job_links") \
        .select("id").eq("contact_id", contact_id).eq("job_id", job_id).execute()
    if existing.data:
        return
    sb.table("contact_job_links").insert({
        "contact_id": contact_id,
        "job_id": job_id,
        "notes": notes,
    }).execute()


def batch_add_contacts(args):
    """Batch add/update contacts from JSON on stdin.

    Expected JSON format (array of contact objects):
    [
      {
        "name": "Rebecca Tang",
        "title": "PM, Google",
        "linkedin_url": "linkedin.com/in/rebeccatang",
        "company": "Google",
        "relationship_type": "referral",
        "outreach_status": "draft_ready",
        "priority": "high",
        "is_personal_connection": true,
        "outreach_message_md": "Subject: ...\\n\\nHey Rebecca...",
        "mutual_connection_notes": "...",
        "notes": "...",
        "jobs": ["4cfb2cb8", "1c1682a7"]
      }
    ]

    Fields:
      name                  (required) Full name
      company               (required) Company name — looked up or auto-created
      title                 Current role title
      linkedin_url          Used as dedup key — updates if already exists
      relationship_type     recruiter | hiring_manager | referral | alumni | unknown
      outreach_status       identified | draft_ready | sent | connected | responded |
                            meeting_scheduled | warm
      priority              high | medium | low
      is_personal_connection  true/false
      outreach_message_md   Full outreach draft (include Subject: line at top)
      mutual_connection_notes  Notes on shared network
      notes                 General notes
      jobs                  Array of job ID prefixes (first 8 chars) to link
    """
    raw = sys.stdin.read().strip()
    if not raw:
        print("ERROR: No JSON provided on stdin")
        sys.exit(1)

    try:
        contacts_data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        sys.exit(1)

    if not isinstance(contacts_data, list):
        contacts_data = [contacts_data]  # accept single object too

    ok_insert, ok_update, fail = 0, 0, 0

    for item in contacts_data:
        name = item.get("name")
        company_name = item.get("company")
        if not name or not company_name:
            print(f"⚠️  Skipping entry missing name or company: {item.get('name', '?')}")
            fail += 1
            continue

        # Resolve company
        company_id = _ensure_company(company_name)
        if not company_id:
            print(f"  ❌ Could not resolve company '{company_name}' for {name}")
            fail += 1
            continue

        # Build contact payload (exclude agent-side keys)
        contact_payload = {
            "company_id": company_id,
            "name": name,
        }
        for field in ("title", "linkedin_url", "relationship_type", "outreach_status",
                      "priority", "is_personal_connection", "outreach_message_md",
                      "mutual_connection_notes", "notes"):
            if field in item:
                contact_payload[field] = item[field]

        contact_id, action = _upsert_contact(contact_payload)
        if not contact_id:
            print(f"  ❌ Failed: {name}")
            fail += 1
            continue

        marker = "✅" if action == "inserted" else "↺ "
        print(f"  {marker} {action.capitalize()}: {name}")

        # Resolve and link jobs
        for prefix in (item.get("jobs") or []):
            job_id, job_title = _resolve_job_prefix(str(prefix))
            if job_id:
                _link_contact_job(contact_id, job_id)
            else:
                print(f"    ⚠️  Job prefix '{prefix}' not found — skipping link")

        if action == "inserted":
            ok_insert += 1
        else:
            ok_update += 1

    total = len(contacts_data)
    print(f"\n✅ batch-add-contacts: {ok_insert} inserted, {ok_update} updated, {fail} failed (of {total} total)")
    print("  Run sync_contacts.py to regenerate the memory file.")


def update_contact(args):
    """Update a contact's outreach status or notes by LinkedIn URL or ID."""
    # Find the contact
    if args.linkedin_url:
        res = sb.table("contacts").select("id, name").eq("linkedin_url", args.linkedin_url).execute()
    elif args.id:
        res = sb.table("contacts").select("id, name").eq("id", args.id).execute()
    else:
        print("ERROR: Provide --linkedin-url or --id")
        sys.exit(1)

    if not res.data:
        print("❌ Contact not found")
        sys.exit(1)

    contact_id = res.data[0]["id"]
    contact_name = res.data[0]["name"]

    data = {}
    if args.status:
        data["outreach_status"] = args.status
    if args.notes:
        data["notes"] = args.notes
    if args.message:
        data["outreach_message_md"] = args.message
    if args.last_contacted:
        data["last_contacted_at"] = args.last_contacted

    if not data:
        print("Nothing to update. Provide --status, --notes, --message, or --last-contacted.")
        return

    sb.table("contacts").update(data).eq("id", contact_id).execute()
    print(f"✅ Updated {contact_name}: {data}")
    print("  Run sync_contacts.py to regenerate the memory file.")


# ─── Engagement Log ──────────────────────────────────────────────


def add_engagement(args):
    """Add an engagement action (LinkedIn like/comment, blog post, etc.)."""
    data = {
        "platform": args.platform or "linkedin",
        "action_type": args.action_type,
        "status": args.status or "drafted",
    }
    if args.target_url:
        data["target_url"] = args.target_url
    if args.target_person:
        data["target_person"] = args.target_person
    if args.content:
        data["content"] = args.content

    result = sb.table("engagement_log").insert(data).execute()
    if result.data:
        print(f"✅ Engagement logged: {args.action_type} on {args.platform} (id: {result.data[0]['id']}, status: {data['status']})")
    else:
        print("❌ Failed to log engagement")


def update_engagement(args):
    """Update an engagement's status or content."""
    data = {}
    if args.status:
        data["status"] = args.status
    if args.content:
        data["content"] = args.content
    if args.status == "posted":
        data["posted_at"] = datetime.now(timezone.utc).isoformat()
    if hasattr(args, "target_person") and args.target_person:
        data["target_person"] = args.target_person

    if not data:
        print("Nothing to update. Provide --status or --content.")
        return

    result = sb.table("engagement_log").update(data).eq("id", args.id).execute()
    if result.data:
        print(f"✅ Updated engagement {args.id}: {data}")
    else:
        print(f"❌ Engagement {args.id} not found")


def list_engagements(args):
    """List engagement actions, optionally filtered by platform or status."""
    query = sb.table("engagement_log").select("*")
    if args.platform:
        query = query.eq("platform", args.platform)
    if args.status:
        query = query.eq("status", args.status)
    query = query.order("created_at", desc=True)
    if args.limit:
        query = query.limit(args.limit)

    result = query.execute()
    entries = result.data or []

    if not entries:
        print("No engagements found.")
        return

    by_status = {}
    for e in entries:
        s = e.get("status", "unknown")
        by_status.setdefault(s, []).append(e)

    for eng_status, items in by_status.items():
        print(f"\n{'─' * 50}")
        print(f"  {eng_status.upper()} ({len(items)})")
        print(f"{'─' * 50}")
        for e in items:
            print(f"  • [{e['platform']}] {e['action_type']}: {(e.get('content') or '')[:80]}")
            print(f"    id: {e['id']}")
            if e.get("target_url"):
                print(f"    url: {e['target_url']}")
            if e.get("target_person"):
                print(f"    person: {e['target_person']}")


# ─── Blog Posts ──────────────────────────────────────────────────


def add_blog_post(args):
    """Add a blog post idea or draft."""
    data = {
        "title": args.title,
        "slug": args.slug,
        "status": args.status or "idea",
    }
    if args.platform:
        data["platform"] = args.platform
    if args.tags:
        data["tags"] = [t.strip() for t in args.tags.split(",")]
    if args.summary:
        data["summary"] = args.summary
    if args.draft_path:
        data["draft_path"] = args.draft_path

    result = sb.table("blog_posts").insert(data).execute()
    if result.data:
        print(f"✅ Blog post added: {args.title} (id: {result.data[0]['id']}, status: {data['status']})")
    else:
        print("❌ Failed to add blog post")


def update_blog_post(args):
    """Update a blog post's status, platform, or published URL."""
    data = {}
    if args.status:
        data["status"] = args.status
    if args.platform:
        data["platform"] = args.platform
    if args.published_url:
        data["published_url"] = args.published_url
        data["published_at"] = datetime.now(timezone.utc).isoformat()
    if args.draft_path:
        data["draft_path"] = args.draft_path
    if args.tags:
        data["tags"] = [t.strip() for t in args.tags.split(",")]

    if not data:
        print("Nothing to update.")
        return

    result = sb.table("blog_posts").update(data).eq("id", args.id).execute()
    if result.data:
        print(f"✅ Updated blog post {args.id}: {data}")
    else:
        print(f"❌ Blog post {args.id} not found")


def batch_import_blog_posts(args):
    """Batch import/upsert blog posts from JSON on stdin.

    Expects a JSON array of objects, each with at minimum: title, slug.
    Optional fields: status, platform, tags (array), summary, published_url,
    published_at (ISO string), draft_path, notes.

    Upserts by slug so re-running a Substack audit never creates duplicates.
    """
    raw = sys.stdin.read().strip()
    if not raw:
        print("ERROR: No JSON provided on stdin")
        sys.exit(1)
    try:
        posts = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        sys.exit(1)

    if not isinstance(posts, list):
        print("ERROR: Expected a JSON array")
        sys.exit(1)

    imported = 0
    skipped = 0
    for post in posts:
        slug = post.get("slug")
        title = post.get("title")
        if not slug or not title:
            print(f"  ⚠️  Skipping entry missing title/slug: {post}")
            skipped += 1
            continue

        data = {
            "title": title,
            "slug": slug,
            "status": post.get("status", "published"),
        }
        if post.get("platform"):
            data["platform"] = post["platform"]
        if post.get("tags"):
            data["tags"] = post["tags"] if isinstance(post["tags"], list) else [t.strip() for t in post["tags"].split(",")]
        if post.get("summary"):
            data["summary"] = post["summary"]
        if post.get("published_url"):
            data["published_url"] = post["published_url"]
        if post.get("published_at"):
            data["published_at"] = post["published_at"]
        if post.get("draft_path"):
            data["draft_path"] = post["draft_path"]
        if post.get("notes"):
            data["notes"] = post["notes"]

        # Upsert by slug
        existing = sb.table("blog_posts").select("id").eq("slug", slug).execute()
        if existing.data:
            sb.table("blog_posts").update(data).eq("slug", slug).execute()
            print(f"  ↻  Updated: {title}")
        else:
            sb.table("blog_posts").insert(data).execute()
            print(f"  ✅ Imported: {title}")
        imported += 1

    print(f"\nDone: {imported} imported/updated, {skipped} skipped.")


def list_blog_posts(args):
    """List blog posts, optionally filtered by status."""
    query = sb.table("blog_posts").select("*")
    if args.status:
        query = query.eq("status", args.status)
    query = query.order("created_at", desc=True)
    if args.limit:
        query = query.limit(args.limit)

    result = query.execute()
    posts = result.data or []

    if not posts:
        print("No blog posts found.")
        return

    by_status = {}
    for p in posts:
        s = p.get("status", "unknown")
        by_status.setdefault(s, []).append(p)

    for post_status, items in by_status.items():
        print(f"\n{'─' * 50}")
        print(f"  {post_status.upper()} ({len(items)})")
        print(f"{'─' * 50}")
        for p in items:
            tags = ", ".join(p.get("tags", []))
            platform = p.get("platform", "unset")
            print(f"  • {p['title']} [{platform}]")
            print(f"    slug: {p['slug']}  |  id: {p['id']}")
            if tags:
                print(f"    tags: {tags}")
            if p.get("summary"):
                print(f"    {p['summary'][:100]}")
            if p.get("published_url"):
                print(f"    published: {p['published_url']}")


# ─── CLI ─────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Artemis DB Helper")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # add-job
    p = subparsers.add_parser("add-job", help="Add a job to the pipeline")
    p.add_argument("--title", required=True)
    p.add_argument("--company", required=True)
    p.add_argument("--url", default="")
    p.add_argument("--description", default="")
    p.add_argument("--status", default="scouted")
    p.add_argument("--source", default="scout")
    p.add_argument("--match-score", type=int, default=None)
    p.set_defaults(func=add_job)

    # list-jobs
    p = subparsers.add_parser("list-jobs", help="List jobs in the pipeline")
    p.add_argument("--status", default=None, help="Filter by status")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=list_jobs)

    # update-job
    p = subparsers.add_parser("update-job", help="Update a job")
    p.add_argument("--id", required=True)
    p.add_argument("--status", default=None)
    p.add_argument("--match-score", type=int, default=None)
    p.add_argument("--reason", default=None, help="Reason for not interested / rejection")
    p.add_argument("--analysis-file", default=None, help="Path to markdown file containing the analysis text")
    p.set_defaults(func=update_job)

    # get-job
    p = subparsers.add_parser("get-job", help="Get full details of a job")
    p.add_argument("--id", required=True)
    p.set_defaults(func=get_job)

    # add-company
    p = subparsers.add_parser("add-company", help="Add a target company")
    p.add_argument("--name", required=True)
    p.add_argument("--domain", default="")
    p.add_argument("--careers-url", default="")
    p.add_argument("--why", default="")
    p.add_argument("--priority", default="medium", choices=["high", "medium", "low"])
    p.set_defaults(func=add_company)

    # list-companies
    p = subparsers.add_parser("list-companies", help="List target companies")
    p.add_argument("--all", action="store_true", help="Show all companies, not just targets")
    p.set_defaults(func=list_companies)

    # score-job (convenience for single scoring)
    p = subparsers.add_parser("score-job", help="Set match score for a job")
    p.add_argument("--id", required=True)
    p.add_argument("--score", type=int, required=True, help="Match score 0-100")
    p.set_defaults(func=lambda args: score_job(args))

    # batch-update (JSON via stdin)
    p = subparsers.add_parser("batch-update", help="Batch update jobs from JSON on stdin")
    p.set_defaults(func=batch_update)

    # batch-add (JSON via stdin)
    p = subparsers.add_parser("batch-add", help="Batch add jobs from JSON on stdin")
    p.set_defaults(func=batch_add)

    # batch-add-contacts (JSON via stdin)
    p = subparsers.add_parser("batch-add-contacts",
                              help="Batch add/update contacts from JSON on stdin. "
                                   "See docstring for full schema.")
    p.set_defaults(func=batch_add_contacts)

    # update-contact
    p = subparsers.add_parser("update-contact", help="Update a contact's status or notes")
    p.add_argument("--id", default=None, help="Contact UUID")
    p.add_argument("--linkedin-url", default=None, help="LinkedIn URL (used as lookup key)")
    p.add_argument("--status", default=None,
                   choices=["identified", "draft_ready", "sent", "connected",
                            "responded", "meeting_scheduled", "warm"],
                   help="New outreach status")
    p.add_argument("--notes", default=None, help="Replace notes field")
    p.add_argument("--message", default=None, help="Replace outreach_message_md field")
    p.add_argument("--last-contacted", default=None, help="ISO timestamp of last contact")
    p.set_defaults(func=update_contact)

    # save-application
    p = subparsers.add_parser("save-application", help="Save application materials to DB")
    p.add_argument("--id", required=True)
    p.add_argument("--resume", help="Path to resume markdown file")
    p.add_argument("--cover-letter", help="Path to cover letter markdown file")
    p.add_argument("--primer", help="Path to primer markdown file")
    p.add_argument("--form-fills", default=None, help="Path to form fills markdown file")
    p.add_argument("--pdf-path", default=None, help="Path to generated resume PDF")
    p.set_defaults(func=save_application)

    # mark-submitted
    p = subparsers.add_parser("mark-submitted", help="Mark application as submitted and advance job to 'applied'")
    p.add_argument("--id", required=True, help="Job UUID")
    p.set_defaults(func=mark_submitted)

    # status
    p = subparsers.add_parser("status", help="Show pipeline dashboard")
    p.set_defaults(func=status)

    # add-engagement
    p = subparsers.add_parser("add-engagement", help="Log an engagement action")
    p.add_argument("--action-type", required=True,
                   help="like, comment, share, connection_request, blog_post")
    p.add_argument("--platform", default="linkedin", help="linkedin, medium, personal_blog")
    p.add_argument("--target-url", default=None)
    p.add_argument("--target-person", default=None)
    p.add_argument("--content", default=None, help="Comment text or share note")
    p.add_argument("--status", default="drafted", choices=["drafted", "approved", "posted", "skipped"])
    p.set_defaults(func=add_engagement)

    # update-engagement
    p = subparsers.add_parser("update-engagement", help="Update an engagement's status")
    p.add_argument("--id", required=True)
    p.add_argument("--status", choices=["drafted", "approved", "posted", "skipped"])
    p.add_argument("--content", default=None)
    p.add_argument("--target-person", default=None)
    p.set_defaults(func=update_engagement)

    # list-engagements
    p = subparsers.add_parser("list-engagements", help="List engagement actions")
    p.add_argument("--platform", default=None)
    p.add_argument("--status", default=None)
    p.add_argument("--limit", type=int, default=25)
    p.set_defaults(func=list_engagements)

    # add-blog-post
    p = subparsers.add_parser("add-blog-post", help="Add a blog post idea or draft")
    p.add_argument("--title", required=True)
    p.add_argument("--slug", required=True, help="URL-friendly slug")
    p.add_argument("--status", default="idea", choices=["idea", "draft", "review", "published"])
    p.add_argument("--platform", default=None, help="linkedin, medium, personal")
    p.add_argument("--tags", default=None, help="Comma-separated tags")
    p.add_argument("--summary", default=None, help="Brief description of the post angle")
    p.add_argument("--draft-path", default=None, help="Path to local draft markdown")
    p.set_defaults(func=add_blog_post)

    # update-blog-post
    p = subparsers.add_parser("update-blog-post", help="Update a blog post")
    p.add_argument("--id", required=True)
    p.add_argument("--status", default=None, choices=["idea", "draft", "review", "published"])
    p.add_argument("--platform", default=None)
    p.add_argument("--published-url", default=None)
    p.add_argument("--draft-path", default=None)
    p.add_argument("--tags", default=None, help="Comma-separated tags")
    p.set_defaults(func=update_blog_post)

    # batch-import-blog-posts
    p = subparsers.add_parser("batch-import-blog-posts", help="Batch import/upsert blog posts from JSON on stdin")
    p.set_defaults(func=batch_import_blog_posts)

    # list-blog-posts
    p = subparsers.add_parser("list-blog-posts", help="List blog posts")
    p.add_argument("--status", default=None)
    p.add_argument("--limit", type=int, default=25)
    p.set_defaults(func=list_blog_posts)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
