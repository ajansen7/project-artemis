# Project Artemis — Claude Instructions

## Python Environment

This project uses **[uv](https://docs.astral.sh/uv/)** for dependency management. Always run Python scripts with `uv run`:

```bash
uv run python .claude/skills/scout/scripts/db.py get-job --id "..."
uv run python .claude/skills/scout/scripts/generate_resume_docx.py --job-id "..."
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
