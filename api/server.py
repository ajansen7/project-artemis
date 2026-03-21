import os
import shlex
import shutil
import subprocess
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="Artemis Local Copilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
TMUX_SESSION = "artemis"
TASK_LOG_DIR = "/tmp/artemis-tasks"
TMUX_BIN = os.environ.get("TMUX_BIN", shutil.which("tmux") or "/opt/homebrew/bin/tmux")
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", shutil.which("claude") or "claude")
UV_BIN = os.environ.get("UV_BIN", shutil.which("uv") or "uv")

# ─── Task Manager ────────────────────────────────────────────────


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
                 "-p", "-J", "-e"],
                capture_output=True, text=True,
            )
            pane_lines = result.stdout.splitlines()
            # Strip trailing blank lines
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


# ─── Task Endpoints ───────────────────────────────────────────────


@app.get("/api/tasks")
async def list_tasks():
    tasks = task_manager.list_all()
    return {"tasks": [_task_to_dict(t) for t in tasks]}


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    task = task_manager.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_dict(task, include_output=True)


@app.delete("/api/tasks/{task_id}")
async def kill_task(task_id: str):
    task_manager.kill(task_id)
    return {"status": "killed"}


# ─── Application Generation ──────────────────────────────────────


class GenerateRequest(BaseModel):
    job_id: str
    company_name: str | None = None


@app.post("/api/generate-application")
async def generate_application(req: GenerateRequest):
    """
    Starts a headless Claude CLI task in tmux to run `/generate` for the given job.
    Returns a task_id immediately — poll /api/tasks/{task_id} for status.
    """
    if not req.job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    target_str = f"Job ID: {req.job_id}"
    if req.company_name:
        target_str += f" at {req.company_name}"

    prompt = (
        f"Follow the instructions for the `/generate` command in the apply skill's SKILL.md "
        f"to generate application materials for '{target_str}'."
    )

    command = [
        CLAUDE_BIN, "-p", prompt,
        "--verbose",
        "--dangerously-skip-permissions",
        "--add-dir", os.path.join(PROJECT_ROOT, ".claude", "skills", "interview-coach"),
    ]
    portfolio_path = os.environ.get("PORTFOLIO_PATH")
    if portfolio_path:
        command.extend(["--add-dir", portfolio_path])

    name = f"Generate Application — {req.company_name or req.job_id[:8]}"
    task_id = task_manager.start(name, command)

    return {"task_id": task_id, "status": "started", "name": name}


# ─── PDF Generation ──────────────────────────────────────────────

TEMPLATE_REL_PATH = ".claude/skills/apply/references/resume_template.docx"


@app.get("/api/check-template")
async def check_template():
    """Check whether the resume template DOCX exists."""
    template_path = os.path.join(PROJECT_ROOT, TEMPLATE_REL_PATH)
    exists = os.path.isfile(template_path)
    return {
        "exists": exists,
        "path": TEMPLATE_REL_PATH,
        "message": None if exists else (
            "Resume template not found. Place your styled .docx template at "
            f"{TEMPLATE_REL_PATH} — see README for setup instructions."
        ),
    }


class GeneratePdfRequest(BaseModel):
    job_id: str


@app.post("/api/generate-pdf")
async def generate_pdf(req: GeneratePdfRequest):
    """
    Generates a styled PDF resume synchronously (fast — ~30s via LibreOffice).
    """
    if not req.job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    try:
        process = subprocess.Popen(
            [
                UV_BIN, "run", "python",
                ".claude/tools/generate_resume_docx.py",
                "--job-id", req.job_id,
            ],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            # Surface actionable messages from known errors
            if "TEMPLATE_MISSING" in stderr:
                raise HTTPException(status_code=422, detail=f"Resume template not found. Place your styled .docx at {TEMPLATE_REL_PATH}")
            if "No resume_md found" in stderr:
                raise HTTPException(status_code=400, detail="No resume found for this job. Generate application materials first.")
            if "not found" in stderr.lower() and "job" in stderr.lower():
                raise HTTPException(status_code=404, detail="Job not found in database.")
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {stderr.strip().splitlines()[-1] if stderr.strip() else 'unknown error'}")

        pdf_path = None
        for line in stdout.splitlines():
            if "PDF written to:" in line:
                pdf_path = line.split("PDF written to:", 1)[1].strip()
                break

        return {"status": "success", "pdf_path": pdf_path, "output": stdout}

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="uv not found in PATH.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Document Save / Learn ───────────────────────────────────────


class SaveDocumentRequest(BaseModel):
    job_id: str
    doc_type: Literal["resume", "cover_letter", "primer"]
    content: str


@app.post("/api/save-document")
async def save_document(req: SaveDocumentRequest):
    """Saves edited markdown directly to the applications table in Supabase."""
    col_map = {
        "resume":       "resume_md",
        "cover_letter": "cover_letter_md",
        "primer":       "primer_md",
    }
    col = col_map[req.doc_type]

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured.")

    try:
        from supabase import create_client
        sb = create_client(supabase_url, supabase_key)
        res = sb.table("applications").update({col: req.content}).eq("job_id", req.job_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail=f"No application found for job {req.job_id}")
        return {"status": "success", "updated_field": col}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class LearnFromEditRequest(BaseModel):
    job_id: str
    doc_type: Literal["resume", "cover_letter", "primer"]
    original_content: str
    edited_content: str


@app.post("/api/learn-from-edit")
async def learn_from_edit(req: LearnFromEditRequest):
    """
    Extracts lessons from manual edits and appends to apply_lessons.md.
    Runs synchronously (short Claude task — lesson extraction only).
    """
    if req.doc_type == "primer":
        return {"status": "skipped", "message": "Primers are job-specific; no lessons to extract."}

    if req.original_content.strip() == req.edited_content.strip():
        return {"status": "skipped", "message": "No changes detected."}

    doc_label = "resume" if req.doc_type == "resume" else "cover letter"
    lessons_path = ".claude/skills/apply/references/apply_lessons.md"
    prompt = (
        f"The user manually corrected their AI-generated {doc_label}. "
        f"Your job is NOT to patch the document — it is to extract the reusable lessons "
        f"behind the corrections so future drafts don't make the same mistakes.\n\n"
        f"Study the diff between the original and edited versions. For each meaningful change, "
        f"ask: what *principle* or *pattern* does this correction teach? "
        f"Think about things like: framing (leading with impact vs. activity), "
        f"structural choices (splitting vs. combining roles), tone, specificity, "
        f"what to omit, ordering, or anything else that generalises beyond this one document.\n\n"
        f"Then append those lessons to `{lessons_path}` using this format:\n\n"
        f"```\n## Lesson — <short title> (<today's date>)\n"
        f"**Observed:** <what the original did wrong>\n"
        f"**Correction:** <what the user changed it to>\n"
        f"**Lesson:** <the generalised principle to apply next time>\n"
        f"**Apply when:** <the situation where this lesson is relevant>\n```\n\n"
        f"Create the file if it doesn't exist. Only write lessons that generalise — skip "
        f"trivial fixes like correcting a typo or a one-off factual detail that belongs "
        f"only in resume_master.md. After writing, list the lessons you added.\n\n"
        f"--- ORIGINAL ---\n{req.original_content}\n\n"
        f"--- EDITED ---\n{req.edited_content}"
    )

    try:
        process = subprocess.Popen(
            [CLAUDE_BIN, "-p", prompt, "--dangerously-skip-permissions"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Agent update failed: {stderr}")
        return {"status": "success", "message": "Agent updated from your corrections.", "output": stdout}
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="claude CLI not found in PATH.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Mark Submitted ──────────────────────────────────────────────


class MarkSubmittedRequest(BaseModel):
    job_id: str


@app.post("/api/mark-submitted")
async def mark_submitted(req: MarkSubmittedRequest):
    """Sets submitted_at on the application record and advances job status to 'applied'."""
    if not req.job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured.")

    try:
        from supabase import create_client
        sb = create_client(supabase_url, supabase_key)
        now = datetime.now(timezone.utc).isoformat()

        app_res = sb.table("applications").update({"submitted_at": now}).eq("job_id", req.job_id).execute()
        if not app_res.data:
            sb.table("applications").insert({"job_id": req.job_id, "submitted_at": now}).execute()

        sb.table("jobs").update({"status": "applied"}).eq("id", req.job_id).execute()
        return {"status": "success", "message": f"Application {req.job_id} marked submitted."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Blog Post Content ────────────────────────────────────────────


@app.get("/api/blog-post-content/{post_id}")
async def get_blog_post_content(post_id: str):
    """Returns the markdown content of a blog post.
    Prefers the content column in the DB; falls back to reading from draft_path on disk."""
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured.")

    try:
        from supabase import create_client
        sb = create_client(supabase_url, supabase_key)
        res = sb.table("blog_posts").select("title,content,draft_path").eq("id", post_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Blog post not found.")
        post = res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Prefer DB content column
    content = post.get("content")
    if content:
        return {"title": post["title"], "content": content, "draft_path": post.get("draft_path")}

    # Fallback: read from disk via draft_path
    draft_path = post.get("draft_path")
    if not draft_path:
        raise HTTPException(status_code=404, detail="No content available for this post.")

    full_path = Path(PROJECT_ROOT) / draft_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"Draft file not found: {draft_path}")

    content = full_path.read_text(encoding="utf-8")
    return {"title": post["title"], "content": content, "draft_path": draft_path}


# ─── Generic Skill Runner ─────────────────────────────────────────


class RunSkillRequest(BaseModel):
    skill: str
    target: str | None = None


@app.post("/api/run-skill")
async def run_skill(req: RunSkillRequest):
    """
    Starts a headless Claude CLI task in tmux for a generic skill command.
    Returns a task_id immediately — poll /api/tasks/{task_id} for status + output.
    """
    if not req.skill:
        raise HTTPException(status_code=400, detail="skill is required")

    skill_cmd = f"/{req.skill.lstrip('/')}"
    if req.target:
        prompt = f"Follow the instructions for the `{skill_cmd}` command in SKILL.md for '{req.target}'."
    else:
        prompt = f"Follow the instructions for the `{skill_cmd}` command in SKILL.md."

    command = [
        CLAUDE_BIN, "-p", prompt,
        "--verbose",
        "--dangerously-skip-permissions",
        "--add-dir", os.path.join(PROJECT_ROOT, ".claude", "skills", "interview-coach"),
    ]
    portfolio_path = os.environ.get("PORTFOLIO_PATH")
    if portfolio_path:
        command.extend(["--add-dir", portfolio_path])

    name = f"{req.skill.capitalize()}{' — ' + req.target[:40] if req.target else ''}"
    task_id = task_manager.start(name, command)

    return {"task_id": task_id, "status": "started", "name": name}


# To run: uv run uvicorn api.server:app --reload
