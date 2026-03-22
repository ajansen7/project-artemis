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

Dependencies are declared in `pyproject.toml`. The `requirements.txt` file is a legacy artifact -- ignore it.

## Project Layout

```
.claude/
  agents/         # Agent definitions
    artemis-orchestrator.md  # Job hunting orchestrator
    telegram-handler.md      # Persistent Telegram interface
  skills/         # Workflow skills
    hunt/           # Job scouting, pipeline management
    apply/          # Application materials generation
    connect/        # Networking pipeline
    profile/        # Candidate context + interview prep
    inbox/          # Gmail + Calendar monitoring
    linkedin/       # LinkedIn browsing + engagement (Chrome MCP)
    blogger/        # Content creation + publishing
    artemis-setup/  # One-time setup wizard
    interview-coach/  # Coaching + drills (git submodule)
  tools/          # Shared Python CLI tools
    db.py             # Supabase CRUD (jobs, companies, contacts, applications, engagements, blog posts)
    generate_resume_docx.py  # Resume markdown -> DOCX/PDF via LibreOffice
    sync_contacts.py         # DB -> contacts markdown sync
    relay_ask.py             # Telegram relay: ask user a question mid-job, block until reply
    push_to_telegram.py      # Send formatted messages to Telegram (direct Bot API)
  hooks/          # Session lifecycle hooks
    load-hot-memory.sh   # SessionStart: inject hot memory, detect fresh install
    check-context.sh     # PreToolUse: context freshness check
    sync-extended.sh     # Stop: sync contacts, cleanup
  memory/hot/     # Hot memory files loaded every session (gitignored)
channels/
  artemis-webhook/  # (retired) MCP channel — replaced by telegram-handler agent
output/           # All generated artifacts (gitignored)
api/              # FastAPI backend (task management, scheduler, PDF generation)
frontend/         # React dashboard (Pipeline, Networking, Engagement, Blog, Schedules tabs)
db/migrations/    # Supabase schema migrations (001-016)
docs/             # Documentation (automation guide, UI walkthrough)
```

## Skills & Routing

| Skill | Commands | Purpose |
|-------|----------|---------|
| **hunt** | `/scout`, `/sync`, `/review`, `/status` | Discover jobs, maintain pipeline, triage |
| **apply** | `/analyze`, `/generate`, `/submit` | Evaluate fit, generate application materials |
| **connect** | `/network` | Manage contacts, draft outreach, track status |
| **profile** | `/context`, `/prep` | Build candidate context cache, interview prep |
| **interview-coach** | `/kickoff`, `/practice`, `/mock`, `/debrief` | Coaching, storybank, drills (git submodule) |
| **inbox** | `/inbox` | Monitor Gmail + Calendar for job search activity |
| **linkedin** | `/linkedin` | Browse LinkedIn for jobs, contacts, engagement (Chrome MCP) |
| **blogger** | `/blog-audit`, `/blog-ideas`, `/blog-write`, `/blog-publish`, `/blog-status` | Import past blog archive, generate ideas, draft/publish posts |
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

## MCP Integrations (Optional)

These unlock additional skills but are not required for core functionality:

- **Gmail MCP** -- enables `/inbox` skill (recruiter emails, interview scheduling)
- **Google Calendar MCP** -- enables interview loop tracking
- **Claude in Chrome** -- enables `/linkedin` and `/blogger` skills (browsing, engagement, publishing)
- **Supabase MCP** -- enables direct DB access for migrations and queries

## Data Handling Rules

- Never hardcode PII in scripts. Build extensible CLI tools and pipe data via stdin at runtime.
- CLI commands must be single-line. Strip newlines from text fields before passing as args.
- Supabase is the source of truth for structured data. Local markdown files are caches/views.
- Batch operations via JSON stdin are preferred over individual CLI calls for multiple items.
- All engagement actions (likes, comments, posts) go through an approval queue. Nothing gets posted without user sign-off.
- Resume bullets must come verbatim from `resume_master.md`. Never fabricate new ones.

## Running Artemis

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
