from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.modules.channel import notify_task
from api.modules.config import _get_supabase

router = APIRouter()


class RunSkillRequest(BaseModel):
    skill: str
    target: str | None = None


@router.post("/api/run-skill")
async def run_skill(req: RunSkillRequest):
    """
    Queue a skill for the orchestrator to execute.
    Inserts a row into task_queue — the orchestrator polls and picks it up.
    Returns task_id immediately.
    """
    if not req.skill:
        raise HTTPException(status_code=400, detail="skill is required")

    skill_name = req.skill.lstrip("/")
    name = f"/{skill_name}{' — ' + req.target[:40] if req.target else ''}"

    sb = _get_supabase()
    res = sb.table("task_queue").insert({
        "name": name,
        "skill": skill_name,
        "skill_args": req.target or None,
        "source": "api",
    }).execute()

    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to queue task")

    task = res.data[0]
    await notify_task(task)
    return {"task_id": task["id"], "status": "queued", "name": name}
