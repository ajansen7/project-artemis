from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.modules.config import PROJECT_ROOT, _get_supabase

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
