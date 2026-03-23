"""Artemis Local Copilot API — assembly point.

To run: uv run uvicorn api.server:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.modules.config import logger
from api.modules.scheduler import _load_all_schedules, scheduler
from api.modules.routes.applications import router as applications_router
from api.modules.routes.blog import router as blog_router
from api.modules.routes.relay import router as relay_router
from api.modules.routes.schedules import router as schedules_router
from api.modules.routes.skills import router as skills_router
from api.modules.routes.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)
app.include_router(applications_router)
app.include_router(blog_router)
app.include_router(skills_router)
app.include_router(schedules_router)
app.include_router(relay_router)
