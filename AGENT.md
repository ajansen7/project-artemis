# Project Artemis Agent Instructions

## SDK Validations
- **ALWAYS** use the `google.genai` package for Google Gen AI integrations (if needed in the future).
- **DO NOT** use the legacy `google.generativeai` package.

## Agent & Skills
This project is orchestrated by the Artemis agent with two peer skills:

- **Orchestrator**: `.claude/agents/artemis-orchestrator.md` — coordinates the end-to-end job search
- **Artemis skill**: `.claude/skills/artemis/SKILL.md` — job scouting, pipeline management, applications
- **Interview Coach skill**: `.claude/skills/interview-coach/SKILL.md` — interview prep, coaching, drills

## Database
All persistent state lives in Supabase. CRUD operations go through:
```
uv run python .claude/skills/artemis/scripts/db.py <command>
```

Run `uv run python .claude/skills/artemis/scripts/db.py --help` to see available commands.

## Archived Code
The original full-stack implementation (LangGraph agents, Next.js frontend, ChromaDB) is preserved on the `archive/full-stack-v1` branch. It includes a Gemini function-calling Scout agent with Serper.dev integration and Google Search grounding experiments.
