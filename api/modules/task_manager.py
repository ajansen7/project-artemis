import os
import shlex
import subprocess
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from api.modules.config import (
    CLAUDE_BIN, PROJECT_ROOT, TASK_LOG_DIR, TMUX_BIN, TMUX_SESSION,
)


@dataclass
class Task:
    id: str
    name: str
    status: str  # "running" | "complete" | "failed"
    started_at: str
    ended_at: str | None = None
    sentinel_path: str = ""  # file written on exit: contains the exit code

    def _read_sentinel(self) -> str | None:
        """Returns the raw exit-code string if the sentinel file exists, else None."""
        try:
            with open(self.sentinel_path, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    def tail_output(self, lines: int = 30) -> str:
        """
        Best-effort: capture recent output via `tmux capture-pane`.
        Falls back to empty string if the window is gone.
        """
        try:
            result = subprocess.run(
                [TMUX_BIN, "capture-pane", "-t", f"{TMUX_SESSION}:{self.id}",
                 "-p", "-J", "-S", "-"],
                capture_output=True, text=True,
            )
            pane_lines = result.stdout.splitlines()
            # Strip trailing blank lines
            while pane_lines and not pane_lines[-1].strip():
                pane_lines.pop()
            # Strip the Claude CLI prompt/status bar lines at the end
            while pane_lines and (pane_lines[-1].startswith("❯") or pane_lines[-1].startswith("─") or pane_lines[-1].lstrip().startswith("⏵")):
                pane_lines.pop()
            while pane_lines and not pane_lines[-1].strip():
                pane_lines.pop()
            return "\n".join(pane_lines[-lines:])
        except Exception:
            return ""


class TaskManager:
    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._lock = threading.Lock()

    def _ensure_session(self):
        """Create the tmux session if it doesn't exist."""
        result = subprocess.run(
            [TMUX_BIN, "has-session", "-t", TMUX_SESSION],
            capture_output=True,
        )
        if result.returncode != 0:
            subprocess.run(
                [TMUX_BIN, "new-session", "-d", "-s", TMUX_SESSION, "-x", "220", "-y", "50"],
                capture_output=True,
            )

    def start(self, name: str, command: list[str]) -> str:
        """
        Run `command` in a new tmux window. Returns a task_id immediately.

        Claude runs directly against the tmux PTY — no pipes — so output streams
        in real time when you `tmux attach -t artemis`. Completion is detected via
        a tiny sentinel file written after the command exits.
        """
        task_id = uuid.uuid4().hex[:8]
        os.makedirs(TASK_LOG_DIR, exist_ok=True)
        sentinel_path = f"{TASK_LOG_DIR}/{task_id}.exit"

        self._ensure_session()

        # Create a dedicated window for this task
        subprocess.run(
            [TMUX_BIN, "new-window", "-t", TMUX_SESSION, "-n", task_id, "-d"],
            capture_output=True,
        )

        # Run the command directly (no pipes) so Claude gets a real PTY and
        # streams output live. Write only the exit code to the sentinel file.
        cmd_str = shlex.join(command)
        shell_cmd = (
            f"cd {shlex.quote(PROJECT_ROOT)} && "
            f"{cmd_str}; "
            f'echo $? > {shlex.quote(sentinel_path)}'
        )

        subprocess.run(
            [TMUX_BIN, "send-keys", "-t", f"{TMUX_SESSION}:{task_id}", shell_cmd, "Enter"],
        )

        task = Task(
            id=task_id,
            name=name,
            status="running",
            started_at=datetime.now(timezone.utc).isoformat(),
            sentinel_path=sentinel_path,
        )

        with self._lock:
            self._tasks[task_id] = task

        return task_id

    def get(self, task_id: str) -> Task | None:
        with self._lock:
            task = self._tasks.get(task_id)
        if task is None:
            return None

        if task.status == "running":
            exit_code = task._read_sentinel()
            if exit_code is not None:
                task.status = "complete" if exit_code == "0" else "failed"
                task.ended_at = datetime.now(timezone.utc).isoformat()

        return task

    def list_all(self) -> list[Task]:
        with self._lock:
            ids = list(self._tasks.keys())
        return [t for tid in ids if (t := self.get(tid)) is not None]

    def kill(self, task_id: str):
        task = self._tasks.get(task_id)
        if task and task.status == "running":
            subprocess.run(
                [TMUX_BIN, "kill-window", "-t", f"{TMUX_SESSION}:{task_id}"],
                capture_output=True,
            )
            task.status = "failed"
            task.ended_at = datetime.now(timezone.utc).isoformat()


task_manager = TaskManager()


def _task_to_dict(task: Task, include_output: bool = False) -> dict:
    return {
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "started_at": task.started_at,
        "ended_at": task.ended_at,
        "tmux_window": f"{TMUX_SESSION}:{task.id}",
        **({"output": task.tail_output(50)} if include_output else {}),
    }
