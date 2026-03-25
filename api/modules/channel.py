"""Fire-and-forget notification to the local Artemis channel MCP server."""

import logging

import httpx

CHANNEL_URL = "http://127.0.0.1:8790"
logger = logging.getLogger("artemis.api")


async def notify_task(task: dict) -> None:
    """POST task details to the channel so the orchestrator is notified instantly.

    Best-effort: if the channel is down (orchestrator not running), the task
    is still persisted in Supabase task_queue and will be picked up when the
    orchestrator is restarted or checks the queue manually.
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(f"{CHANNEL_URL}/task", json=task)
    except Exception:
        pass  # non-fatal — task remains in DB


def notify_task_sync(task: dict) -> None:
    """Synchronous variant for use in APScheduler callbacks (non-async context)."""
    try:
        with httpx.Client(timeout=2.0) as client:
            client.post(f"{CHANNEL_URL}/task", json=task)
    except Exception:
        pass
