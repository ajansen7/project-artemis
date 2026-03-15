# 🏹 Project Artemis

A multi-agent orchestration system designed to automate, optimize, and curate the job hunting and career development lifecycle.

## Architecture

Artemis uses a **LangGraph StateGraph** to orchestrate specialized agents:

| Agent | Role | Phase |
|-------|------|-------|
| **Orchestrator** | Workflow routing & HITL interactions | 1 |
| **Analyst** | Job matching & gap analysis | 1 |
| **Artisan** | Resume & cover letter generation | 1 |
| **Scout** | Continuous job discovery | 2 |
| **Networker** | Connection mapping & outreach | 2 |
| **Diplomat** | Communication tracking & follow-ups | 3 |

## Tech Stack

- **Orchestration**: LangGraph (Python)
- **LLM**: Google Gemini 2.5 Pro
- **Vector DB**: ChromaDB
- **Database**: Supabase (PostgreSQL)
- **API**: FastAPI
- **Frontend**: Next.js Command Center
- **Notifications**: Discord Bot

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv) (recommended)

### Setup

```bash
# Clone & enter the project
cd project-artemis

# Copy environment template and fill in your API keys
cp .env.example .env

# Start all services (backend + ChromaDB + frontend)
docker compose up -d

# Or run locally with uv
uv sync

# Run the ingestion pipeline
uv run python scripts/run_ingest.py --all

# Run tests
uv run pytest

# Start the API server
uv run uvicorn agents.api:app --reload --port 8080
```

### List Available Models

To see all available Gemini models you can run:

```bash
uv run python scripts/list_models.py
```

You can set your preferred model in your `.env` file using the `GEMINI_MODEL` variable (e.g., `GEMINI_MODEL=gemini-2.0-flash-exp`).

### Analyze a Job

```bash
# Via CLI for Orchestrator/Analyst
uv run python scripts/run_agents.py --job-url "https://example.com/job/123"

# Via CLI to run the continuous Scout agent directly
uv run python scripts/run_scout.py

# Via API
curl -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"job_url": "https://example.com/job/123"}'
```

## Project Structure

```
project-artemis/
├── agents/             # LangGraph agent backend
│   ├── nodes/          # One module per agent
│   ├── tools/          # Supabase, ChromaDB, scraping, Google APIs
│   ├── prompts/        # System prompts per agent
│   ├── api.py          # FastAPI application
│   ├── graph.py        # LangGraph StateGraph
│   ├── state.py        # Shared AgentState
│   └── config.py       # Settings from .env
├── ingestion/          # Data ingestion pipeline
├── db/migrations/      # Supabase schema
├── frontend/           # Next.js Command Center
├── bot/                # Discord bot
├── tests/              # pytest test suite
└── scripts/            # CLI entry points
```

## Implementation Phases

1. **Phase 1 — MVP**: CRM + Analyst (manual job input → match score + gap analysis)
2. **Phase 2 — Automation**: Scout + Networker (automated discovery + daily briefings)
3. **Phase 3 — Full Orchestration**: Diplomat + Growth loop (Gmail integration + continuous skill building)

## License

MIT
