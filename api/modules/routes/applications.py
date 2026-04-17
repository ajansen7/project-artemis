import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from api.modules.channel import notify_task
from api.modules.config import PROJECT_ROOT, _get_supabase, run_db, get_user_id_from_request

_CLAUDE_BIN = os.environ.get("CLAUDE_BIN", shutil.which("claude") or "claude")
_UV_BIN = os.environ.get("UV_BIN", shutil.which("uv") or "uv")

router = APIRouter()

class GenerateRequest(BaseModel):
    job_id: str
    company_name: str | None = None


@router.post("/api/generate-application")
async def generate_application(req: GenerateRequest, request: Request):
    """
    Queues a generate task for the orchestrator to execute.
    Returns a task_id immediately — poll /api/tasks/{task_id} for status.
    """
    if not req.job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    user_id = get_user_id_from_request(request)
    target_str = f"Job ID: {req.job_id}"
    if req.company_name:
        target_str += f" at {req.company_name}"

    name = f"generate — {req.company_name or req.job_id[:8]}"
    sb = _get_supabase()
    res = await run_db(lambda: sb.table("task_queue").insert({
        "name": name,
        "skill": "generate",
        "skill_args": target_str,
        "source": "api",
        "user_id": user_id,
    }).execute())

    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to queue task")

    await notify_task(res.data[0])
    return {"task_id": res.data[0]["id"], "status": "queued", "name": name}


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
                "tools/generate_resume_docx.py",
                "--job-id", req.job_id,
            ],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
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
        res = await run_db(lambda: sb.table("applications").update({col: req.content}).eq("job_id", req.job_id).execute())
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
    lessons_path = "state/apply_lessons.md"
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

        app_res = await run_db(lambda: sb.table("applications").update({"submitted_at": now}).eq("job_id", req.job_id).execute())
        if not app_res.data:
            await run_db(lambda: sb.table("applications").insert({"job_id": req.job_id, "submitted_at": now}).execute())

        await run_db(lambda: sb.table("jobs").update({"status": "applied"}).eq("id", req.job_id).execute())
        return {"status": "success", "message": f"Application {req.job_id} marked submitted."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')


@router.get("/api/applications/{job_id}/download/{file_type}")
async def download_application_file(
    job_id: str,
    file_type: Literal["pdf", "docx", "cover_letter", "primer"],
    request: Request,
):
    """Download an application artifact (PDF, DOCX, or markdown)."""
    user_id = get_user_id_from_request(request)
    sb = _get_supabase()

    # Fetch application data and job info for filename
    app_res = await run_db(lambda: (
        sb.table("applications")
        .select("resume_pdf_path, resume_pdf_path_storage, resume_docx_path, cover_letter_md, primer_md, jobs(title, companies(name))")
        .eq("job_id", job_id)
        .maybe_single()
        .execute()
    ))

    if not app_res.data:
        raise HTTPException(status_code=404, detail="No application found for this job.")

    app = app_res.data
    job_info = app.get("jobs") or {}
    company_info = job_info.get("companies") or {}
    company_name = company_info.get("name", "company")
    job_title = job_info.get("title", "position")
    slug_prefix = f"{_slugify(company_name)}_{_slugify(job_title)}"

    if file_type in ("pdf", "docx"):
        # Try Supabase Storage first, fall back to local filesystem
        storage_col = "resume_pdf_path_storage" if file_type == "pdf" else "resume_docx_path"
        storage_path = app.get(storage_col)
        local_col = "resume_pdf_path" if file_type == "pdf" else None
        local_path = app.get(local_col) if local_col else None

        file_bytes = None

        if storage_path:
            # Verify the file belongs to the requesting user
            if f"/users/{user_id}/" not in storage_path and not storage_path.startswith(f"users/{user_id}/"):
                raise HTTPException(status_code=403, detail="Access denied.")
            try:
                file_bytes = await run_db(lambda: sb.storage.from_("artifacts").download(storage_path))
            except Exception:
                pass  # Fall through to local path

        if file_bytes is None and local_path:
            # Resolve local path relative to project root
            abs_path = Path(PROJECT_ROOT) / local_path
            if abs_path.is_file():
                file_bytes = abs_path.read_bytes()

        if file_bytes is None:
            hint = "Try regenerating the PDF from the application modal." if file_type == "pdf" else "DOCX not available for this application."
            raise HTTPException(status_code=404, detail=f"No {file_type.upper()} found. {hint}")

        if file_type == "pdf":
            media_type = "application/pdf"
            filename = f"{slug_prefix}_resume.pdf"
        else:
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"{slug_prefix}_resume.docx"

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    else:
        # Markdown downloads (cover_letter, primer)
        col = "cover_letter_md" if file_type == "cover_letter" else "primer_md"
        content = app.get(col)

        if not content:
            label = "cover letter" if file_type == "cover_letter" else "primer"
            raise HTTPException(status_code=404, detail=f"No {label} found. Generate application materials first.")

        label = "cover_letter" if file_type == "cover_letter" else "primer"
        filename = f"{slug_prefix}_{label}.md"

        return Response(
            content=content.encode("utf-8"),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
