from datetime import datetime, timezone

from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.modules.config import _get_supabase
from api.modules.scheduler import _register_schedule, _unregister_schedule

router = APIRouter()


class ScheduleCreateRequest(BaseModel):
    name: str
    skill: str
    skill_args: str | None = None
    cron_expr: str
    enabled: bool = False
    notes: str | None = None


class ScheduleUpdateRequest(BaseModel):
    name: str | None = None
    skill: str | None = None
    skill_args: str | None = None
    cron_expr: str | None = None
    enabled: bool | None = None
    notes: str | None = None


@router.get("/api/schedules")
async def list_schedules():
    sb = _get_supabase()
    res = sb.table("scheduled_jobs").select("*").order("created_at").execute()
    return {"schedules": res.data or []}


@router.post("/api/schedules")
async def create_schedule(req: ScheduleCreateRequest):
    # Validate cron expression
    try:
        CronTrigger.from_crontab(req.cron_expr)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: {exc}")

    sb = _get_supabase()
    row = {
        "name": req.name,
        "skill": req.skill,
        "skill_args": req.skill_args,
        "cron_expr": req.cron_expr,
        "enabled": req.enabled,
        "notes": req.notes,
    }
    res = sb.table("scheduled_jobs").insert(row).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create schedule")

    created = res.data[0]
    if created["enabled"]:
        _register_schedule(created)

    return created


@router.put("/api/schedules/{schedule_id}")
async def update_schedule(schedule_id: str, req: ScheduleUpdateRequest):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Validate cron if changing
    if "cron_expr" in updates:
        try:
            CronTrigger.from_crontab(updates["cron_expr"])
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid cron expression: {exc}")

    sb = _get_supabase()
    res = sb.table("scheduled_jobs").update(updates).eq("id", schedule_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Schedule not found")

    updated = res.data[0]

    # Sync APScheduler: unregister old, re-register if enabled
    _unregister_schedule(schedule_id)
    if updated["enabled"]:
        _register_schedule(updated)

    return updated


@router.delete("/api/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    _unregister_schedule(schedule_id)

    sb = _get_supabase()
    res = sb.table("scheduled_jobs").delete().eq("id", schedule_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return {"status": "deleted"}


@router.post("/api/schedules/{schedule_id}/run-now")
async def run_schedule_now(schedule_id: str):
    """Immediately queue a scheduled job for the orchestrator to execute."""
    sb = _get_supabase()
    res = sb.table("scheduled_jobs").select("*").eq("id", schedule_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Schedule not found")

    row = res.data[0]

    sb.table("scheduled_jobs").update({
        "last_status": "queued",
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "last_error": None,
    }).eq("id", schedule_id).execute()

    task_res = sb.table("task_queue").insert({
        "name": row["name"],
        "skill": row["skill"].lstrip("/"),
        "skill_args": row.get("skill_args"),
        "source": "schedule",
        "schedule_id": schedule_id,
    }).execute()

    if not task_res.data:
        raise HTTPException(status_code=500, detail="Failed to queue task")

    task = task_res.data[0]
    return {"task_id": task["id"], "status": "queued", "name": row["name"]}
