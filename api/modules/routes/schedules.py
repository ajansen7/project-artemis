import threading
from datetime import datetime, timezone

from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.modules.config import _get_supabase
from api.modules.scheduler import (
    _build_skill_command, _poll_and_notify,
    _register_schedule, _unregister_schedule,
)
from api.modules.task_manager import task_manager

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
    """Immediately trigger a scheduled job (regardless of enabled state)."""
    sb = _get_supabase()
    res = sb.table("scheduled_jobs").select("*").eq("id", schedule_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Schedule not found")

    row = res.data[0]
    command = _build_skill_command(row["skill"], row.get("skill_args"), job_name=row["name"])
    task_id = task_manager.start(f"Manual: {row['name']}", command)

    # Update last_run_at + status
    sb.table("scheduled_jobs").update({
        "last_status": "running",
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "last_error": None,
    }).eq("id", schedule_id).execute()

    # Poll for completion and fire webhook in background thread
    threading.Thread(
        target=_poll_and_notify,
        args=(task_id, row["name"], row["skill"]),
        kwargs={"schedule_id": schedule_id},
        daemon=True,
    ).start()

    return {"task_id": task_id, "status": "started", "name": row["name"]}
