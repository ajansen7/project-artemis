# Project Artemis Agent Instructions

## SDK Validations
- **ALWAYS** use the `google.genai` package for Google Gen AI integrations (if needed in the future).
- **DO NOT** use the legacy `google.generativeai` package.

## Skill
This project is a Claude Code skill for job hunting. The main skill definition is at:
`agent/skills/artemis/SKILL.md`

Read that file for available commands and how to use them.

## Database
All persistent state lives in Supabase. CRUD operations go through:
```
uv run python agent/skills/artemis/scripts/db.py <command>
```

Run `uv run python agent/skills/artemis/scripts/db.py --help` to see available commands.

## Archived Code
The original full-stack implementation (LangGraph agents, Next.js frontend, ChromaDB) is preserved on the `archive/full-stack-v1` branch. It includes a Gemini function-calling Scout agent with Serper.dev integration and Google Search grounding experiments.
