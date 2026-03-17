# Project Artemis — Claude Instructions

## Python Environment

This project uses **[uv](https://docs.astral.sh/uv/)** for dependency management. Always run Python scripts with `uv run`:

```bash
uv run python .claude/tools/db.py get-job --id "..."
uv run python .claude/tools/generate_resume_docx.py --job-id "..."
uv run python .claude/tools/sync_contacts.py
uv run uvicorn api.server:app --reload
```

`uv run` automatically activates the project's virtual environment — never call `.venv/bin/python` directly or `source .venv/bin/activate`.

To add a new dependency:
```bash
uv add <package>
```

To sync the environment after pulling changes:
```bash
uv sync
```

Dependencies are declared in `pyproject.toml`. The `requirements.txt` file is a legacy artifact — ignore it.

## Project Layout

```
.claude/
  skills/         # Workflow skills (hunt, apply, connect, profile, interview-coach)
  tools/          # Shared Python CLI tools (db.py, generate_resume_docx.py, sync_contacts.py)
  hooks/          # Session lifecycle hooks (hot memory, context check, sync)
  memory/hot/     # Hot memory files loaded every session via hooks
  agents/         # Orchestrator agent definition
output/           # All generated artifacts (applications, PDFs, pipeline snapshots)
api/              # FastAPI backend (task management, PDF generation)
frontend/         # React dashboard
db/migrations/    # Supabase schema migrations
```

## Data Handling Rules

- Never hardcode PII in scripts. Build extensible CLI tools and pipe data via stdin at runtime.
- CLI commands must be single-line. Strip newlines from text fields before passing as args.
- Supabase is the source of truth for structured data. Local markdown files are caches/views.
- Batch operations via JSON stdin are preferred over individual CLI calls for multiple items.
