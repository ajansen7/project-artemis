"""Blog post CRUD operations."""

import json
import sys
from datetime import datetime, timezone

from db_modules.client import get_client


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
    if args.content:
        data["content"] = args.content

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
    if args.content:
        data["content"] = args.content

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
    sb = get_client()
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
