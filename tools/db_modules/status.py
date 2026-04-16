"""Pipeline status dashboard."""

from db_modules.client import get_client


def status(args):
    """Show pipeline dashboard."""
    sb = get_client()
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
