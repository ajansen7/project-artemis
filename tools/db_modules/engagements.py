"""Engagement log CRUD operations."""

from datetime import datetime, timezone

from db_modules.client import get_client, get_current_user_id


def add_engagement(args):
    """Add an engagement action (LinkedIn like/comment, blog post, etc.)."""
    sb = get_client()
    user_id = get_current_user_id()
    data = {
        "platform": args.platform or "linkedin",
        "action_type": args.action_type,
        "status": args.status or "drafted",
    }
    if user_id:
        data["user_id"] = user_id
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
    sb = get_client()
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
    sb = get_client()
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
