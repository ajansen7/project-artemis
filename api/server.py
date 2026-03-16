import os
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
