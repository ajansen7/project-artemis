from fastapi import APIRouter, HTTPException

from api.modules.task_manager import task_manager, _task_to_dict

router = APIRouter()


@router.get("/api/tasks")
async def list_tasks():
    tasks = task_manager.list_all()
    return {"tasks": [_task_to_dict(t) for t in tasks]}


@router.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    task = task_manager.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_dict(task, include_output=True)


@router.delete("/api/tasks/{task_id}")
async def kill_task(task_id: str):
    task_manager.kill(task_id)
    return {"status": "killed"}
