"""Artemis Local Copilot API — assembly point.

To run: uv run uvicorn api.server:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.modules.middleware import ApprovalMiddleware

from api.modules.config import logger
from api.modules.scheduler import _load_all_schedules, scheduler
from api.modules.routes.admin import router as admin_router
from api.modules.routes.applications import router as applications_router
from api.modules.routes.auth import router as auth_router
from api.modules.routes.blog import router as blog_router
from api.modules.routes.notify import router as notify_router
from api.modules.routes.schedules import router as schedules_router
from api.modules.routes.skills import router as skills_router
from api.modules.routes.tasks import router as tasks_router
from api.modules.routes.terminal import router as terminal_router


async def _cleanup_orphaned_tasks():
    """Mark tasks that were mid-execution (running) when the previous session died as failed.
    Queued tasks are preserved — they haven't been picked up yet and can still run."""
    try:
        from api.modules.config import _get_supabase, run_db
        sb = _get_supabase()
        res = await run_db(
            lambda: sb.table("task_queue")
            .update({"status": "failed", "error": "Orphaned: session ended without completing task"})
            .in_("status", ["running"])
            .execute()
        )
        count = len(res.data or [])
        if count:
            logger.info("Cleaned up %d orphaned running task(s) on startup", count)
    except Exception as exc:
        logger.warning("Could not clean up orphaned tasks: %s", exc)


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    await _cleanup_orphaned_tasks()
    _load_all_schedules()
    scheduler.start()
    logger.info("Scheduler started")
    yield
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


app = FastAPI(title="Artemis Local Copilot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
        "https://localhost", "https://127.0.0.1",
    ],
    # Allow any device on a private LAN (HTTP or HTTPS, any port)
    allow_origin_regex=(
        r"https?://(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+"
        r"|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)(:\d+)?"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ApprovalMiddleware)

app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(applications_router)
app.include_router(blog_router)
app.include_router(notify_router)
app.include_router(skills_router)
app.include_router(schedules_router)
app.include_router(terminal_router)
