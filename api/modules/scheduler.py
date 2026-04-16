import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from api.modules.channel import notify_task_sync
from api.modules.config import _get_supabase, logger

scheduler = AsyncIOScheduler()
_schedule_job_ids: dict[str, str] = {}  # DB id -> APScheduler job id


def _run_scheduled_job(schedule_id: str, name: str, skill: str, skill_args: str | None):
    """
    APScheduler callback. Inserts a task into task_queue for the orchestrator to pick up.
    """
    try:
        sb = _get_supabase()

        # Get the user_id from the scheduled_jobs row
        schedule_res = sb.table("scheduled_jobs").select("user_id").eq("id", schedule_id).execute()
        if not schedule_res.data:
            logger.error("Scheduled job not found: %s", schedule_id)
            return
        user_id = schedule_res.data[0]["user_id"]

        sb.table("scheduled_jobs").update({
            "last_status": "queued",
            "last_run_at": datetime.now(timezone.utc).isoformat(),
            "last_error": None,
        }).eq("id", schedule_id).execute()

        res = sb.table("task_queue").insert({
            "name": name,
            "skill": skill.lstrip("/"),
            "skill_args": skill_args or None,
            "source": "schedule",
            "schedule_id": schedule_id,
            "user_id": user_id,
        }).execute()

        if res.data:
            notify_task_sync(res.data[0])

        logger.info("Queued scheduled job: %s (%s)", name, skill)
    except Exception as exc:
        logger.error("Failed to queue scheduled job %s (%s): %s", name, skill, exc)
        try:
            sb = _get_supabase()
            sb.table("scheduled_jobs").update({
                "last_status": "failed",
                "last_error": str(exc),
            }).eq("id", schedule_id).execute()
        except Exception:
            pass


def _register_schedule(row: dict):
    """Register a single DB row with APScheduler."""
    schedule_id = row["id"]
    try:
        trigger = CronTrigger.from_crontab(row["cron_expr"], timezone="America/Denver")
    except ValueError as exc:
        logger.warning("Invalid cron for schedule %s: %s", schedule_id, exc)
        return

    job = scheduler.add_job(
        _run_scheduled_job,
        trigger=trigger,
        args=[schedule_id, row["name"], row["skill"], row.get("skill_args")],
        id=f"schedule_{schedule_id}",
        replace_existing=True,
    )
    _schedule_job_ids[schedule_id] = job.id


def _unregister_schedule(schedule_id: str):
    """Remove a schedule from APScheduler."""
    job_id = _schedule_job_ids.pop(schedule_id, None)
    if job_id:
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass


def _load_all_schedules():
    """Load all enabled schedules from Supabase into APScheduler."""
    try:
        sb = _get_supabase()
        res = sb.table("scheduled_jobs").select("*").eq("enabled", True).execute()
        for row in res.data or []:
            _register_schedule(row)
        logger.info("Loaded %d enabled schedules", len(res.data or []))
    except Exception as exc:
        logger.warning("Could not load schedules: %s", exc)
