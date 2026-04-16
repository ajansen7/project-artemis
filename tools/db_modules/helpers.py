"""Shared helper functions for db_modules."""

from db_modules.client import get_client, get_current_user_id


def _ensure_company(name, job_score=None):
    """Find or create a company, return its ID. Auto-targets if job_score >= 80."""
    sb = get_client()
    user_id = get_current_user_id()

    # Filter by current user
    result = sb.table("companies").select("id, is_target").eq("name", name)
    if user_id:
        result = result.eq("user_id", user_id)
    result = result.execute()

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
    if user_id:
        data["user_id"] = user_id

    if job_score is not None and job_score >= 80:
        priority = "high" if job_score >= 90 else "medium"
        data["is_target"] = True
        data["scout_priority"] = priority
        print(f"🌟 Created and auto-targeted company '{name}' (priority: {priority}) due to high job score ({job_score}).")

    insert = sb.table("companies").insert(data).execute()
    return insert.data[0]["id"] if insert.data else None


def _resolve_job_prefix(prefix):
    """Match a job by ID prefix (first 8 chars). Returns (id, title) or (None, None)."""
    sb = get_client()
    res = sb.table("jobs").select("id, title").execute()
    for row in (res.data or []):
        if row["id"].replace("-", "").startswith(prefix.replace("-", "")):
            return row["id"], row["title"]
    return None, None


def _upsert_contact(data):
    """Insert or update a contact. Deduplicates on linkedin_url if present."""
    sb = get_client()
    user_id = get_current_user_id()

    linkedin = data.get("linkedin_url")
    if linkedin:
        query = sb.table("contacts").select("id").eq("linkedin_url", linkedin)
        if user_id:
            query = query.eq("user_id", user_id)
        existing = query.execute()
        if existing.data:
            cid = existing.data[0]["id"]
            sb.table("contacts").update(
                {k: v for k, v in data.items() if k != "linkedin_url"}
            ).eq("id", cid).execute()
            return cid, "updated"

    # Ensure user_id is set for new contacts
    if user_id and "user_id" not in data:
        data["user_id"] = user_id

    res = sb.table("contacts").insert(data).execute()
    if res.data:
        return res.data[0]["id"], "inserted"
    return None, "failed"


def _link_contact_job(contact_id, job_id, notes=None):
    """Create a contact_job_links row if it doesn't already exist."""
    if not contact_id or not job_id:
        return
    sb = get_client()
    existing = sb.table("contact_job_links") \
        .select("id").eq("contact_id", contact_id).eq("job_id", job_id).execute()
    if existing.data:
        return
    sb.table("contact_job_links").insert({
        "contact_id": contact_id,
        "job_id": job_id,
        "notes": notes,
    }).execute()
