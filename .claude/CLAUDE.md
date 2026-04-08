# Project Artemis -- Claude Instructions

## Python Environment

This project uses **[uv](https://docs.astral.sh/uv/)** for dependency management. Always run Python scripts with `uv run`:

```bash
uv run python .claude/tools/db.py get-job --id "..."
uv run python .claude/tools/generate_resume_docx.py --job-id "..."
uv run python .claude/tools/sync_contacts.py
uv run uvicorn api.server:app --reload
```

`uv run` automatically activates the project's virtual environment -- never call `.venv/bin/python` directly or `source .venv/bin/activate`.

To add a new dependency:
```bash
uv add <package>
```

To sync the environment after pulling changes:
```bash
uv sync
```

Dependencies are declared in `pyproject.toml`.

## Project Layout

```
.claude/                    # All Claude Code configuration
  CLAUDE.md                 # Project instructions (this file)
  CLAUDE.local.md           # Personal overrides (gitignored)
  settings.json             # Shared permissions & hooks
  settings.local.json       # Personal permission overrides (gitignored)
  agents/                   # Agent definitions
    artemis-orchestrator.md   # Unified orchestrator: Telegram + task executor
  skills/                   # Workflow skills
    hunt/                     # Job scouting, pipeline management
    apply/                    # Application materials generation
    connect/                  # Networking pipeline
    profile/                  # Candidate context + interview prep
    inbox/                    # Gmail + Calendar monitoring
    linkedin/                 # LinkedIn browsing + engagement (Chrome MCP)
    blogger/                  # Content creation + publishing
    maintain/                 # Pipeline hygiene (dedupe, cull)
    artemis-setup/            # One-time setup wizard
    interview-coach/          # Coaching + drills (git submodule)
  tools/                    # Shared Python CLI tools
    db.py                     # Thin CLI shim — forwards to db_modules/
    db_modules/               # Modular Supabase CRUD
    generate_resume_docx.py   # Resume markdown -> DOCX/PDF via LibreOffice
    sync_contacts.py          # DB -> contacts markdown sync
    push_to_telegram.py       # Send formatted messages to Telegram
  hooks/                    # (deprecated — hooks moved to plugin root hooks/)
  rules/                    # Auto-loaded contextual rules
    data-handling.md          # PII, CLI, data source rules
    pipeline-workflow.md      # Job pipeline operational rules
  memory/
    hot/                      # Hot memory loaded every session (gitignored)
.mcp.json                   # MCP server registration (project root)
channels/
  artemis-channel/            # MCP channel: pushes task events into orchestrator
scripts/
  setup.sh                    # New user setup wizard
  start.sh                    # Start all services in tmux
  stop.sh                     # Stop services
output/                     # Generated artifacts (gitignored)
api/                        # FastAPI backend (scheduler, task queue, PDF generation)
frontend/                   # React dashboard
db/migrations/              # Supabase schema migrations (001-017)
docs/                       # Documentation
```

## Skills & Routing

**Quick reference — hunt vs apply:**
- **hunt** = managing the job *pipeline* (finding jobs, syncing sources, reviewing the queue, checking status). Use it when you're thinking about the list of jobs.
- **apply** = working a *specific job* (analyzing a posting, generating resume + cover letter + primer, submitting). Use it once you've picked a job to pursue.

| Skill | Commands | When to use it |
|-------|----------|----------------|
| **hunt** | `/scout`, `/sync`, `/review`, `/status` | Finding jobs, updating the pipeline, triaging what came in |
| **apply** | `/analyze`, `/generate`, `/submit` | Working a specific posting — analysis, resume/cover letter, submission |
| **connect** | `/network` | Managing contacts, drafting outreach, tracking follow-ups |
| **profile** | `/context`, `/prep` | Building candidate context cache, interview prep for a company |
| **interview-coach** | `/kickoff`, `/practice`, `/mock`, `/debrief` | Coaching, storybank, drills (git submodule) |
| **inbox** | `/inbox` | Monitoring Gmail + Calendar for recruiter emails and interview scheduling |
| **linkedin** | `/linkedin` | Browsing LinkedIn for jobs, contacts, engagement (Chrome MCP) |
| **blogger** | `/blog-audit`, `/blog-ideas`, `/blog-write`, `/blog-publish`, `/blog-status` | Content creation + publishing |
| **maintain** | `/dedupe`, `/cull` | Deduplicating jobs, culling stale/low-value entries |
| **artemis-setup** | `/setup` | One-time setup wizard for new users |

## Supabase Schema

| Table | Purpose |
|-------|---------|
| `jobs` | Pipeline: title, URL, status, match score, gap analysis, source |
| `companies` | Company directory + target watchlist |
| `contacts` | Networking contacts with outreach status and source |
| `contact_job_links` | Many-to-many: contacts to job postings |
| `contact_interactions` | Timestamped event log per contact |
| `anecdotes` | STAR-format interview stories |
| `applications` | Generated materials: resume, cover letter, primer, form fills, PDF path |
| `engagement_log` | LinkedIn/blog engagement actions with approval workflow |
| `blog_posts` | Content lifecycle: idea, draft, review, published |
| `scheduled_jobs` | Recurring automation: skill, cron, enabled, run history |

### Job Statuses

`scouted` -> `to_review` -> `applied` -> `recruiter_engaged` -> `interviewing` -> `offer`

Side statuses: `not_interested`, `rejected`, `deleted`

## Memory (Two Tiers)

**Hot memory** (`.claude/memory/hot/`) loads every session via hooks:
- `identity.md` -- candidate name, headline, positioning, search status
- `voice.md` -- tone rules for all communications
- `active_loops.md` -- current interview loops and time-sensitive items
- `lessons.md` -- operational best practices

**Extended memory** lives in skill `references/` dirs and loads on demand:
- `candidate_context.md` -- full cached profile (hunt skill)
- `resume_master.md` -- verified resume bullets (apply skill)
- `apply_lessons.md` -- feedback from past applications (apply skill)
- `preferences.md` -- target roles, companies, deal-breakers (hunt skill)
- `coaching_state.md` -- full coaching state (interview-coach)

## Local Overrides

Use `.claude/CLAUDE.local.md` (gitignored) for machine-specific notes, personal workflow tweaks, or environment-specific instructions. See `.claude/CLAUDE.local.example.md` for the template.

## MCP Integrations (Optional)

These unlock additional skills but are not required for core functionality:

- **Gmail MCP** -- enables `/inbox` skill (recruiter emails, interview scheduling)
- **Google Calendar MCP** -- enables interview loop tracking
- **Claude in Chrome** -- enables `/linkedin` and `/blogger` skills (browsing, engagement, publishing)
- **Supabase MCP** -- enables direct DB access for migrations and queries

## Running Artemis

First-time setup:
```bash
./scripts/setup.sh
```

Start all services (API, frontend, Telegram handler) in a single tmux session:
```bash
./scripts/start.sh          # start everything
./scripts/start.sh --no-frontend   # skip the React frontend
./scripts/stop.sh            # stop services
./scripts/stop.sh --kill     # kill entire tmux session
```

Services:
- **API:** `http://localhost:8000` (FastAPI backend, scheduler)
- **Dashboard:** `http://localhost:5173` (React frontend)
- **Telegram:** Long-running Claude session with Telegram plugin (handles inbound messages, dispatches skills, routes relay replies)
