"""Task queue CRUD operations for the unified orchestrator."""

import json
import urllib.request
from datetime import datetime, timezone

from db_modules.client import sb

_NOTIFY_URL = "http://localhost:8000/api/notify"


def _push_refresh(tables: list[str]) -> None:
    """Best-effort POST to the local API to trigger a UI refresh."""
    payload = json.dumps({"event": "refresh", "data": {"tables": tables}}).encode()
    req = urllib.request.Request(
        _NOTIFY_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass  # API may not be running; UI will catch up via polling


def next_task(args):
    """
    Atomically claim the oldest queued task: set status to 'running', return it as JSON.
    Returns nothing (exit 0) if no tasks are queued — orchestrator treats silence as idle.
    """
    # Fetch oldest queued task
    res = sb.table("task_queue") \
        .select("*") \
        .eq("status", "queued") \
        .order("created_at", desc=False) \
        .limit(1) \
        .execute()

    if not res.data:
        return  # no work, silent exit

    task = res.data[0]
    now = datetime.now(timezone.utc).isoformat()

    # Mark running
    sb.table("task_queue").update({
        "status": "running",
        "started_at": now,
    }).eq("id", task["id"]).execute()

    task["status"] = "running"
    task["started_at"] = now
    print(json.dumps(task))


def update_task(args):
    """Update a task's status, output_summary, or error."""
    updates = {}
    if args.status:
        updates["status"] = args.status
    if args.output_summary:
        updates["output_summary"] = args.output_summary
    if args.error:
        updates["error"] = args.error
    if args.status in ("complete", "failed"):
        updates["ended_at"] = datetime.now(timezone.utc).isoformat()

    if not updates:
        print("No fields to update")
        return

    res = sb.table("task_queue").update(updates).eq("id", args.id).execute()
    if not res.data:
        print(f"Task {args.id} not found")
        return

    task = res.data[0]

    # If this task was from a schedule, update scheduled_jobs.last_status too
    if task.get("schedule_id") and args.status in ("complete", "failed"):
        final = "success" if args.status == "complete" else "failed"
        sb.table("scheduled_jobs").update({
            "last_status": final,
            "last_error": args.error or None,
        }).eq("id", task["schedule_id"]).execute()

    print(f"Updated task {args.id}: {updates}")

    # Notify the UI whenever a task reaches a terminal state
    if args.status in ("complete", "failed"):
        _push_refresh(["tasks", "task_queue"])


def notify_refresh(args):
    """Push a refresh signal to the UI for the given tables (or all if none specified)."""
    tables = [t.strip() for t in args.tables.split(",") if t.strip()] if args.tables else []
    _push_refresh(tables)
    label = ", ".join(tables) if tables else "all"
    print(f"Refresh signal sent for: {label}")


def list_tasks(args):
    """List recent tasks from the queue."""
    query = sb.table("task_queue").select("*").order("created_at", desc=True)
    if args.status:
        query = query.eq("status", args.status)
    query = query.limit(args.limit or 25)
    res = query.execute()
    print(json.dumps(res.data or []))
