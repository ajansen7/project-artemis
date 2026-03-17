import os
import subprocess
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="Artemis Local Copilot API")

# Configure CORS so the Vite frontend (React) can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    job_id: str
    company_name: str | None = None

@app.post("/api/generate-application")
async def generate_application(req: GenerateRequest):
    """
    Triggers the headless Claude Code CLI to run the `/apply` command for a given job.
    """
    if not req.job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    # We need to explicitly pass the job_id to prevent ambiguity when there are multiple roles at the same company.
    target_str = f"Job ID: {req.job_id}"
    if req.company_name:
        target_str += f" at {req.company_name}"
    
    print(f"Triggering application generation for: {target_str}")

    try:
        # Build the command string. Since `-p` doesn't support slash commands natively,
        # we tell Claude exactly what to do using natural language. Use the /scout prefix
        # to ensure it strictly maps to our custom skill.
        prompt = f"Follow the instructions for the `/scout apply` command in SKILL.md to generate application materials for '{target_str}'."
        
        process = subprocess.Popen(
            [
                "claude", 
                "-p", 
                prompt,
                "--dangerously-skip-permissions",
                "--add-dir", "/Users/alexjansen/Dev/project-artemis/.claude/skills/interview-coach",
                "--add-dir", "/Users/alexjansen/Dev/alex-s-lens"
            ],
            cwd="/Users/alexjansen/Dev/project-artemis",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"claude CLI error: {stderr}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {stderr}")
            
        print(f"claude CLI output: {stdout}")
        
        return {
            "status": "success", 
            "message": f"Application materials generated for {target_str}.",
            "output": stdout
        }

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="The 'claude' CLI command was not found in PATH.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


class GeneratePdfRequest(BaseModel):
    job_id: str

@app.post("/api/generate-pdf")
async def generate_pdf(req: GeneratePdfRequest):
    """
    Generates a styled PDF resume from the resume_md stored in the DB for the given job.
    Runs generate_resume_pdf.py headlessly and returns the output PDF path.
    """
    if not req.job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    print(f"Generating PDF resume for job: {req.job_id}")

    try:
        process = subprocess.Popen(
            [
                ".venv/bin/python",
                ".claude/skills/scout/scripts/generate_resume_pdf.py",
                "--job-id", req.job_id,
            ],
            cwd="/Users/alexjansen/Dev/project-artemis",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"PDF generation error: {stderr}")
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {stderr}")

        print(f"PDF generation output: {stdout}")

        # Parse the output path from stdout ("✅ PDF written to: <path>")
        pdf_path = None
        for line in stdout.splitlines():
            if "PDF written to:" in line:
                pdf_path = line.split("PDF written to:", 1)[1].strip()
                break

        return {
            "status": "success",
            "message": f"PDF generated for job {req.job_id}.",
            "pdf_path": pdf_path,
            "output": stdout,
        }

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Python venv not found. Run: pip install -r requirements.txt")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


class SaveDocumentRequest(BaseModel):
    job_id: str
    doc_type: Literal['resume', 'cover_letter', 'primer']
    content: str

@app.post("/api/save-document")
async def save_document(req: SaveDocumentRequest):
    """
    Saves edited markdown directly to the applications table in Supabase.
    No Claude needed — direct DB write.
    """
    col_map = {
        'resume':       'resume_md',
        'cover_letter': 'cover_letter_md',
        'primer':       'primer_md',
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
    doc_type: Literal['resume', 'cover_letter', 'primer']
    original_content: str
    edited_content: str

@app.post("/api/learn-from-edit")
async def learn_from_edit(req: LearnFromEditRequest):
    """
    Extracts reusable writing and presentation lessons from the user's manual edits
    and appends them to apply_lessons.md so future /apply runs benefit from them.
    """
    if req.doc_type == 'primer':
        return {"status": "skipped", "message": "Primers are job-specific; no lessons to extract."}

    if req.original_content.strip() == req.edited_content.strip():
        return {"status": "skipped", "message": "No changes detected."}

    doc_label = "resume" if req.doc_type == "resume" else "cover letter"
    lessons_path = ".claude/skills/scout/references/apply_lessons.md"
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
            ["claude", "-p", prompt, "--dangerously-skip-permissions"],
            cwd="/Users/alexjansen/Dev/project-artemis",
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


class RunSkillRequest(BaseModel):
    skill: str
    target: str | None = None

@app.post("/api/run-skill")
async def run_skill(req: RunSkillRequest):
    """
    Triggers the headless Claude Code CLI to run a generic skill command (e.g. /sync, /review, /analyze).
    """
    if not req.skill:
        raise HTTPException(status_code=400, detail="skill is required")

    print(f"Triggering skill: {req.skill} for target: {req.target}")
    
    # Construct prompt
    # We prefix with /scout to avoid conflation with built-in Claude commands (like /sync)
    skill_cmd = f"/scout {req.skill.lstrip('/')}"
    if req.target:
        prompt = f"Follow the instructions for the `{skill_cmd}` command in SKILL.md for '{req.target}'."
    else:
        prompt = f"Follow the instructions for the `{skill_cmd}` command in SKILL.md."

    try:
        process = subprocess.Popen(
            [
                "claude", 
                "-p", 
                prompt,
                "--dangerously-skip-permissions",
                "--add-dir", "/Users/alexjansen/Dev/project-artemis/.claude/skills/interview-coach",
                "--add-dir", "/Users/alexjansen/Dev/alex-s-lens"
            ],
            cwd="/Users/alexjansen/Dev/project-artemis",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"claude CLI error: {stderr}")
            raise HTTPException(status_code=500, detail=f"Skill execution failed: {stderr}")
            
        out_str = str(stdout) if stdout else ""
        print(f"claude CLI output snippet (first 200 chars): {out_str[:200]}")
        
        return {
            "status": "success", 
            "message": f"Skill {req.skill} executed.",
            "output": out_str
        }

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="The 'claude' CLI command was not found in PATH.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# To run: uv run uvicorn api.server:app --reload
