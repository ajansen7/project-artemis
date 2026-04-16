"""Job pipeline CRUD operations."""

import json

from db_modules.client import get_client, get_current_user_id
from db_modules.helpers import _ensure_company


TERMINAL_STATUSES = {"rejected", "not_interested", "deleted"}


def add_job(args):
    """Add a job to the pipeline."""
    sb = get_client()
    user_id = get_current_user_id()

    # Check for duplicate URL (filter by user)
    if args.url:
        query = sb.table("jobs").select("id, status").eq("url", args.url)
        if user_id:
            query = query.eq("user_id", user_id)
        existing = query.execute()
        if existing.data:
            existing_status = existing.data[0].get("status", "")
            if existing_status in TERMINAL_STATUSES:
                print(f"⚠️  Job already exists with status '{existing_status}' (id: {existing.data[0]['id']}) — not re-adding")
            else:
                print(f"⚠️  Job already exists with this URL (id: {existing.data[0]['id']}, status: {existing_status})")
            return

    # No URL — check by company+title to prevent duplicate entries
    if args.company and args.title:
        companies_q = sb.table("companies").select("id").ilike("name", f"%{args.company}%")
        if user_id:
            companies_q = companies_q.eq("user_id", user_id)
        companies_res = companies_q.execute()
        company_ids = [c["id"] for c in (companies_res.data or [])]
        if company_ids:
            existing_q = (
                sb.table("jobs")
                .select("id, title, status")
                .in_("company_id", company_ids)
                .ilike("title", f"%{args.title[:40]}%")
            )
            if user_id:
                existing_q = existing_q.eq("user_id", user_id)
            existing_q = existing_q.execute()
            if existing_q.data:
                match = existing_q.data[0]
                if match["status"] in TERMINAL_STATUSES:
                    print(f"⚠️  Job '{match['title']}' at {args.company} already exists with status '{match['status']}' — not re-adding")
                    return
                else:
                    print(f"⚠️  Job '{match['title']}' at {args.company} already in pipeline (id: {match['id']}, status: {match['status']}) — not re-adding")
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
    if user_id:
        data["user_id"] = user_id

    result = sb.table("jobs").insert(data).execute()
    if result.data:
        job = result.data[0]
        print(f"✅ Saved: {args.title} at {args.company or 'Unknown'} (id: {job['id']}, status: {job['status']})")
    else:
        print("❌ Failed to insert job")


def list_jobs(args):
    """List all jobs, optionally filtered by status."""
    sb = get_client()
    user_id = get_current_user_id()

    query = sb.table("jobs").select("id, title, url, status, match_score, source, created_at, companies(name)")
    if user_id:
        query = query.eq("user_id", user_id)
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
    sb = get_client()
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
    sb = get_client()
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
    sb = get_client()
    user_id = get_current_user_id()

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
    query = sb.table("applications").select("id").eq("job_id", args.id)
    if user_id:
        query = query.eq("user_id", user_id)
    existing = query.execute()

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
        if user_id:
            content["user_id"] = user_id
        insert_res = sb.table("applications").insert(content).execute()
        if insert_res.data:
            print(f"✅ Created new application record with materials for job {args.id}")
        else:
            print(f"❌ Failed to insert application for job {args.id}")


def mark_submitted(args):
    """Mark an application as submitted: set submitted_at and advance job status to 'applied'."""
    sb = get_client()
    user_id = get_current_user_id()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    # Update application submitted_at
    app_res = sb.table("applications").update({"submitted_at": now}).eq("job_id", args.id).execute()
    if app_res.data:
        print(f"✅ Application marked submitted at {now}")
    else:
        # Application row may not exist yet — create a minimal one
        data = {"job_id": args.id, "submitted_at": now}
        if user_id:
            data["user_id"] = user_id
        sb.table("applications").insert(data).execute()
        print(f"✅ Created application record with submitted_at={now}")

    # Advance job status to 'applied'
    job_res = sb.table("jobs").update({"status": "applied"}).eq("id", args.id).execute()
    if job_res.data:
        print(f"✅ Job {args.id} status → applied")


def find_job(args):
    """Search for existing jobs by company name and/or title fragment.

    Returns a JSON array so callers can check before adding.
    Includes all statuses — the caller must decide what to do with rejected/deleted matches.
    """
    sb = get_client()
    import json

    company_ids = []
    if args.company:
        companies = sb.table("companies").select("id, name").ilike("name", f"%{args.company}%").execute()
        company_ids = [c["id"] for c in (companies.data or [])]
        if not company_ids:
            # Company not in DB at all → no matching jobs
            print(json.dumps([]))
            return

    query = sb.table("jobs").select("id, title, status, source, url, company_id, companies(name)")

    if company_ids:
        if len(company_ids) == 1:
            query = query.eq("company_id", company_ids[0])
        else:
            query = query.in_("company_id", company_ids)

    if getattr(args, "title", None):
        query = query.ilike("title", f"%{args.title}%")

    result = query.order("created_at", desc=True).execute()
    jobs = result.data or []

    output = [
        {
            "id": j["id"],
            "title": j["title"],
            "company": (j.get("companies") or {}).get("name", "Unknown"),
            "status": j["status"],
            "source": j.get("source", ""),
            "url": j.get("url", ""),
        }
        for j in jobs
    ]
    print(json.dumps(output, indent=2))


def score_job(args):
    """Set match score for a job (convenience for batch scoring)."""
    sb = get_client()
    score = max(0, min(100, args.score))
    result = sb.table("jobs").update({"match_score": score}).eq("id", args.id).execute()
    if result.data:
        print(f"✅ Scored job {args.id}: {score}/100")
    else:
        print(f"❌ Job {args.id} not found")


def merge_jobs(args):
    """Merge two jobs: keep one, absorb the other's data, then mark the duplicate as deleted.

    Combines sources, fills empty fields on the keeper from the duplicate,
    re-points contact_job_links and transfers applications if needed.
    """
    sb = get_client()
    keep_id = args.keep
    merge_id = args.merge

    # Fetch both jobs
    keep_res = sb.table("jobs").select("*, companies(name)").eq("id", keep_id).execute()
    merge_res = sb.table("jobs").select("*, companies(name)").eq("id", merge_id).execute()

    if not keep_res.data:
        print(f"❌ Keeper job {keep_id} not found")
        return
    if not merge_res.data:
        print(f"❌ Merge job {merge_id} not found")
        return

    keeper = keep_res.data[0]
    duplicate = merge_res.data[0]

    # Build update for keeper: fill empty fields, combine sources, keep higher score
    update = {}

    # Combine sources
    keep_source = keeper.get("source") or ""
    dup_source = duplicate.get("source") or ""
    if dup_source and dup_source not in keep_source:
        combined = f"{keep_source}, {dup_source}" if keep_source else dup_source
        update["source"] = combined

    # Fill empty description
    if not keeper.get("description_md") and duplicate.get("description_md"):
        update["description_md"] = duplicate["description_md"]

    # Keep higher match score
    keep_score = keeper.get("match_score")
    dup_score = duplicate.get("match_score")
    if dup_score is not None:
        if keep_score is None or dup_score > keep_score:
            update["match_score"] = dup_score

    # Fill empty URL
    if not keeper.get("url") and duplicate.get("url"):
        update["url"] = duplicate["url"]

    # Combine notes
    keep_notes = keeper.get("notes") or ""
    dup_notes = duplicate.get("notes") or ""
    if dup_notes and dup_notes not in keep_notes:
        combined_notes = f"{keep_notes}\n{dup_notes}".strip() if keep_notes else dup_notes
        update["notes"] = combined_notes

    # Fill gap analysis
    if not keeper.get("gap_analysis_json") and duplicate.get("gap_analysis_json"):
        update["gap_analysis_json"] = duplicate["gap_analysis_json"]

    # Apply keeper updates
    if update:
        sb.table("jobs").update(update).eq("id", keep_id).execute()

    # Re-point contact_job_links from duplicate to keeper
    dup_links = sb.table("contact_job_links").select("id, contact_id").eq("job_id", merge_id).execute()
    links_moved = 0
    for link in (dup_links.data or []):
        # Check if keeper already has this contact linked
        existing = sb.table("contact_job_links") \
            .select("id").eq("contact_id", link["contact_id"]).eq("job_id", keep_id).execute()
        if existing.data:
            # Already linked — just delete the duplicate link
            sb.table("contact_job_links").delete().eq("id", link["id"]).execute()
        else:
            # Re-point to keeper
            sb.table("contact_job_links").update({"job_id": keep_id}).eq("id", link["id"]).execute()
            links_moved += 1

    # Transfer applications if keeper has none
    keeper_apps = sb.table("applications").select("id").eq("job_id", keep_id).execute()
    dup_apps = sb.table("applications").select("id").eq("job_id", merge_id).execute()
    apps_transferred = 0
    if not keeper_apps.data and dup_apps.data:
        sb.table("applications").update({"job_id": keep_id}).eq("job_id", merge_id).execute()
        apps_transferred = len(dup_apps.data)
    elif dup_apps.data:
        # Keeper already has apps — delete duplicate's
        sb.table("applications").delete().eq("job_id", merge_id).execute()

    # Mark duplicate as deleted
    sb.table("jobs").update({
        "status": "deleted",
        "notes": f"Merged into {keep_id}",
    }).eq("id", merge_id).execute()

    # Summary
    keeper_company = (keeper.get("companies") or {}).get("name", "Unknown")
    dup_company = (duplicate.get("companies") or {}).get("name", "Unknown")
    print(f"✅ Merged jobs:")
    print(f"  Kept:    {keeper['title']} at {keeper_company} ({keep_id})")
    print(f"  Deleted: {duplicate['title']} at {dup_company} ({merge_id})")
    if update:
        print(f"  Fields updated on keeper: {', '.join(update.keys())}")
    if links_moved:
        print(f"  Contact links moved: {links_moved}")
    if apps_transferred:
        print(f"  Applications transferred: {apps_transferred}")
