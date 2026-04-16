"""Company CRUD operations."""

from db_modules.client import get_client


def add_company(args):
    """Add a target company to the watchlist."""
    sb = get_client()
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
    sb = get_client()
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
