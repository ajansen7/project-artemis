import threading

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.modules.scheduler import _build_skill_command, _poll_and_notify
from api.modules.task_manager import task_manager

router = APIRouter()


class RunSkillRequest(BaseModel):
    skill: str
    target: str | None = None


@router.post("/api/run-skill")
async def run_skill(req: RunSkillRequest):
    """
    Starts a Claude CLI task in tmux for a generic skill command.
    Interactive skills (inbox, schedule, etc.) run without -p to inherit OAuth MCPs.
    Returns a task_id immediately — poll /api/tasks/{task_id} for status + output.
    """
    if not req.skill:
        raise HTTPException(status_code=400, detail="skill is required")

    command = _build_skill_command(req.skill, req.target or None)
    skill_name = req.skill.lstrip("/")
    name = f"{req.skill.capitalize()}{' — ' + req.target[:40] if req.target else ''}"
    task_id = task_manager.start(name, command)

    # Poll for completion and fire webhook in background thread
    threading.Thread(
        target=_poll_and_notify,
        args=(task_id, name, skill_name),
        daemon=True,
    ).start()

    return {"task_id": task_id, "status": "started", "name": name}
