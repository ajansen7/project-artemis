import threading
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.modules.config import PROJECT_ROOT, _get_supabase
from api.modules.scheduler import _build_skill_command
from api.modules.task_manager import task_manager

router = APIRouter()


@router.get("/api/blog-post-content/{post_id}")
async def get_blog_post_content(post_id: str):
    """Returns the markdown content of a blog post.
    Prefers the content column in the DB; falls back to reading from draft_path on disk."""
    try:
        sb = _get_supabase()
        res = sb.table("blog_posts").select("title,content,draft_path").eq("id", post_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Blog post not found.")
        post = res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Prefer DB content column
    content = post.get("content")
    if content:
        return {"title": post["title"], "content": content, "draft_path": post.get("draft_path")}

    # Fallback: read from disk via draft_path
    draft_path = post.get("draft_path")
    if not draft_path:
        raise HTTPException(status_code=404, detail="No content available for this post.")

    full_path = Path(PROJECT_ROOT) / draft_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"Draft file not found: {draft_path}")

    content = full_path.read_text(encoding="utf-8")
    return {"title": post["title"], "content": content, "draft_path": draft_path}


class BlogPostUpdate(BaseModel):
    content: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


@router.put("/api/blog-posts/{post_id}")
async def update_blog_post(post_id: str, body: BlogPostUpdate):
    """Save edits to a blog post's content, notes, and/or status.
    Published posts cannot have their status changed."""
    try:
        sb = _get_supabase()
        res = sb.table("blog_posts").select("id,status,slug").eq("id", post_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Blog post not found.")
        current = res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    updates: dict = {}
    if body.content is not None:
        updates["content"] = body.content
    if body.notes is not None:
        updates["notes"] = body.notes
    if body.status is not None:
        if current["status"] == "published":
            raise HTTPException(status_code=400, detail="Cannot change status of a published post.")
        allowed = {"idea", "draft", "review"}
        if body.status not in allowed:
            raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {allowed}")
        updates["status"] = body.status

    if not updates:
        return {"ok": True, "updated": []}

    try:
        sb.table("blog_posts").update(updates).eq("id", post_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"ok": True, "updated": list(updates.keys())}


@router.post("/api/blog-posts/{post_id}/generate")
async def generate_blog_draft(post_id: str):
    """Dispatch the blogger skill to write a draft for this post.
    Returns a task_id to poll for completion."""
    try:
        sb = _get_supabase()
        res = sb.table("blog_posts").select("id,slug,title,status").eq("id", post_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Blog post not found.")
        post = res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if post["status"] == "published":
        raise HTTPException(status_code=400, detail="Cannot regenerate a published post.")

    slug = post["slug"]
    name = f"blog-write — {post['title'][:50]}"
    command = _build_skill_command("blogger", f"/blog-write {slug}", job_name=name)
    task_id = task_manager.start(name, command)

    threading.Thread(
        target=_poll_task_silent,
        args=(task_id,),
        daemon=True,
    ).start()

    return {"task_id": task_id, "status": "started", "name": name}


@router.post("/api/blog-posts/{post_id}/process-feedback")
async def process_blog_feedback(post_id: str):
    """Dispatch the blogger skill to revise the draft using saved revision notes.
    Extracts voice/tone lessons and flags potential new interview stories."""
    try:
        sb = _get_supabase()
        res = sb.table("blog_posts").select("id,slug,title,status,notes").eq("id", post_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Blog post not found.")
        post = res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if post["status"] == "published":
        raise HTTPException(status_code=400, detail="Cannot revise a published post.")

    slug = post["slug"]
    name = f"blog-revise — {post['title'][:50]}"
    command = _build_skill_command("blogger", f"/blog-revise {slug}", job_name=name)
    task_id = task_manager.start(name, command)

    threading.Thread(
        target=_poll_task_silent,
        args=(task_id,),
        daemon=True,
    ).start()

    return {"task_id": task_id, "status": "started", "name": name}


def _poll_task_silent(task_id: str):
    """Background poller — just waits for task completion with no notification."""
    import time
    for _ in range(360):  # max 30 min
        task = task_manager.get(task_id)
        if task and task.get("status") in ("completed", "failed"):
            return
        time.sleep(5)
