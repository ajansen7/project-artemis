from fastapi import APIRouter, HTTPException

from api.modules.config import _get_supabase, run_db

router = APIRouter()


@router.get("/api/tasks")
async def list_tasks():
    sb = _get_supabase()
    res = await run_db(lambda: sb.table("task_queue").select("*").order("created_at", desc=True).limit(50).execute())
    return {"tasks": res.data or []}


@router.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    sb = _get_supabase()
    res = await run_db(lambda: sb.table("task_queue").select("*").eq("id", task_id).execute())
    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found")
    return res.data[0]


@router.delete("/api/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Mark a queued or running task as failed (cancelled by user)."""
    sb = _get_supabase()
    res = await run_db(lambda: sb.table("task_queue").update({"status": "failed", "error": "Cancelled by user"})
        .eq("id", task_id).in_("status", ["queued", "running"]).execute())
    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found or already terminal")
    return {"status": "cancelled"}
