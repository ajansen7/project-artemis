"""
Supabase CRM tools — CRUD operations for jobs, companies, contacts, and anecdotes.
"""

from __future__ import annotations

from supabase import create_client, Client
import structlog

from agents.config import settings

logger = structlog.get_logger()

_client: Client | None = None


def get_supabase_client() -> Client:
    """Lazy-initialize and return the Supabase client."""
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _client


# ─── Jobs ───────────────────────────────────────────────────────


async def upsert_job(
    *,
    company_name: str,
    title: str,
    url: str,
    description_md: str,
    status: str = "scouted",
    match_score: int | None = None,
    gap_analysis: dict | None = None,
) -> dict:
    """Insert or update a job record. Returns the upserted row."""
    client = get_supabase_client()

    # Ensure company exists
    company = await _ensure_company(company_name)

    data = {
        "company_id": company["id"],
        "title": title,
        "url": url,
        "description_md": description_md,
        "status": status,
        "match_score": match_score,
        "gap_analysis_json": gap_analysis,
    }

    result = client.table("jobs").upsert(data, on_conflict="url").execute()
    logger.info("supabase.upsert_job", title=title, status=status)
    return result.data[0] if result.data else {}


async def update_job_status(job_id: str, status: str) -> dict:
    """Update the status of an existing job."""
    client = get_supabase_client()
    result = client.table("jobs").update({"status": status}).eq("id", job_id).execute()
    logger.info("supabase.update_status", job_id=job_id, status=status)
    return result.data[0] if result.data else {}


async def get_jobs_by_status(status: str) -> list[dict]:
    """Retrieve all jobs with a given status."""
    client = get_supabase_client()
    result = client.table("jobs").select("*").eq("status", status).execute()
    return result.data or []


# ─── Companies ──────────────────────────────────────────────────


async def _ensure_company(name: str) -> dict:
    """Find or create a company by name."""
    client = get_supabase_client()
    result = client.table("companies").select("*").eq("name", name).execute()
    if result.data:
        return result.data[0]

    insert = client.table("companies").insert({"name": name}).execute()
    return insert.data[0] if insert.data else {}


# ─── Contacts ──────────────────────────────────────────────────


async def upsert_contact(
    *,
    company_id: str,
    name: str,
    title: str = "",
    linkedin_url: str = "",
    email: str = "",
    relationship_type: str = "unknown",
) -> dict:
    """Insert or update a contact record."""
    client = get_supabase_client()
    data = {
        "company_id": company_id,
        "name": name,
        "title": title,
        "linkedin_url": linkedin_url,
        "email": email,
        "relationship_type": relationship_type,
    }
    result = client.table("contacts").upsert(data, on_conflict="linkedin_url").execute()
    return result.data[0] if result.data else {}


# ─── Anecdotes ──────────────────────────────────────────────────


async def save_anecdote(
    *,
    title: str,
    situation: str,
    task: str,
    action: str,
    result_text: str,
    tags: list[str] | None = None,
    source: str = "user_input",
) -> dict:
    """Save a STAR-format anecdote."""
    client = get_supabase_client()
    data = {
        "title": title,
        "situation": situation,
        "task": task,
        "action": action,
        "result": result_text,
        "tags": tags or [],
        "source": source,
    }
    insert = client.table("anecdotes").insert(data).execute()
    logger.info("supabase.save_anecdote", title=title)
    return insert.data[0] if insert.data else {}
