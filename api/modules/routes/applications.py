import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.modules.config import PROJECT_ROOT, _get_supabase

_CLAUDE_BIN = os.environ.get("CLAUDE_BIN", shutil.which("claude") or "claude")
_UV_BIN = os.environ.get("UV_BIN", shutil.which("uv") or "uv")

router = APIRouter()

TEMPLATE_REL_PATH = ".claude/skills/apply/references/resume_template.docx"


class GenerateRequest(BaseModel):
    job_id: str
    company_name: str | None = None


@router.post("/api/generate-application")
async def generate_application(req: GenerateRequest):
    """
    Queues a generate task for the orchestrator to execute.
    Returns a task_id immediately — poll /api/tasks/{task_id} for status.
    """
    if not req.job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    target_str = f"Job ID: {req.job_id}"
    if req.company_name:
        target_str += f" at {req.company_name}"

    name = f"generate — {req.company_name or req.job_id[:8]}"
    sb = _get_supabase()
    res = sb.table("task_queue").insert({
        "name": name,
        "skill": "generate",
        "skill_args": target_str,
        "source": "api",
    }).execute()

    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to queue task")

    return {"task_id": res.data[0]["id"], "status": "queued", "name": name}


@router.get("/api/check-template")
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


@router.post("/api/generate-pdf")
async def generate_pdf(req: GeneratePdfRequest):
    """
    Generates a styled PDF resume synchronously (fast — ~30s via LibreOffice).
    """
    if not req.job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    try:
        process = subprocess.Popen(
            [
                _UV_BIN, "run", "python",
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


class SaveDocumentRequest(BaseModel):
    job_id: str
    doc_type: Literal["resume", "cover_letter", "primer"]
    content: str


@router.post("/api/save-document")
async def save_document(req: SaveDocumentRequest):
    """Saves edited markdown directly to the applications table in Supabase."""
    col_map = {
        "resume":       "resume_md",
        "cover_letter": "cover_letter_md",
        "primer":       "primer_md",
    }
    col = col_map[req.doc_type]

    try:
        sb = _get_supabase()
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


@router.post("/api/learn-from-edit")
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
            [_CLAUDE_BIN, "-p", prompt, "--dangerously-skip-permissions"],
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


class MarkSubmittedRequest(BaseModel):
    job_id: str


@router.post("/api/mark-submitted")
async def mark_submitted(req: MarkSubmittedRequest):
    """Sets submitted_at on the application record and advances job status to 'applied'."""
    if not req.job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    try:
        sb = _get_supabase()
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
