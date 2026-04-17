# Project Artemis -- Claude Instructions

## Overview

Project Artemis is a Claude Code plugin for AI-powered job search orchestration. It provides skills for job scouting, application generation, networking, interview coaching, and content creation.

## Python Environment

This project uses **[uv](https://docs.astral.sh/uv/)** for dependency management. Always run Python scripts with `uv run`:

```bash
uv run uvicorn api.server:app --reload
```

CLI tools are available via bin/ wrappers when the plugin is loaded:
```bash
artemis-db get-job --id "..."
artemis-resume --job-id "..."
artemis-sync
artemis-telegram summary --job-name "X" --status success --body "..."
```

Dependencies are declared in `pyproject.toml`. Run `uv sync` after pulling changes.

## Project Layout

```
project-artemis/                    # Plugin root
├── .claude-plugin/
│   └── plugin.json                 # Plugin manifest (name: "artemis")
├── skills/                         # All skills
│   ├── scout/SKILL.md              # Job scouting & pipeline management
│   ├── apply/SKILL.md              # Application materials generation
│   ├── network/SKILL.md            # Networking pipeline
│   ├── profile/SKILL.md            # Candidate context & interview prep
│   ├── coach/                      # Interview coaching (full system)
│   │   ├── SKILL.md
│   │   └── references/             # Coaching methodology & commands
│   ├── inbox/SKILL.md              # Gmail & Calendar monitoring
│   ├── linkedin/SKILL.md           # LinkedIn browsing & engagement
│   ├── blog/SKILL.md               # Content creation & publishing
│   ├── maintain/SKILL.md           # Pipeline hygiene (dedupe, cull)
│   └── setup/SKILL.md              # One-time setup wizard
├── agents/
│   └── orchestrator.md             # Telegram + task queue orchestrator
├── hooks/
│   ├── hooks.json                  # Plugin hook configuration
│   ├── session-start.sh            # Load hot state on session start
│   └── session-stop.sh             # Auto-sync on session end
├── bin/                            # CLI tools (added to PATH by plugin)
│   ├── artemis-db                  # Supabase CRUD operations
│   ├── artemis-sync                # Contacts DB -> markdown sync
│   ├── artemis-resume              # Resume markdown -> DOCX/PDF
│   └── artemis-telegram            # Telegram notifications
├── tools/                          # Python CLI source
│   ├── db.py                       # Thin CLI shim -> db_modules/
│   ├── db_modules/                 # Modular Supabase CRUD
│   ├── sync_contacts.py
│   ├── sync_state.py               # Data freshness checks
│   ├── generate_resume_docx.py
│   ├── push_to_telegram.py
│   └── migrate_state.py            # Migration from legacy .claude/ layout
├── state/                          # User state files (gitignored)
│   ├── examples/                   # Templates for new users (committed)
│   ├── coaching_state.md           # Master coaching state
│   ├── identity.md                 # Candidate profile (hot-loaded)
│   ├── voice.md                    # Tone rules (hot-loaded)
│   ├── active_loops.md             # Interview loops (hot-loaded)
│   ├── preferences.md              # Job search preferences
│   ├── resume_master.md            # Canonical resume bullets
│   └── ...                         # See state/examples/ for full list
├── templates/
│   └── resume_template.docx        # Resume formatting template
├── rules/                          # Auto-loaded rules
│   ├── data-handling.md
│   └── pipeline-workflow.md
├── .mcp.json                       # MCP servers (artemis-channel)
├── settings.json                   # Plugin default settings
├── nginx/                          # Reverse proxy config
│   ├── artemis.conf                # nginx site config (HTTPS, WebSocket, SSE)
│   └── ssl/                        # Self-signed certs (gitignored)
├── scripts/                        # Infrastructure management
│   ├── setup.sh                    # New user setup wizard
│   ├── setup-nginx.sh              # Generate SSL certs + install nginx config
│   ├── start.sh                    # Start all services in tmux
│   └── stop.sh                     # Stop services
├── api/                            # FastAPI backend (scheduler, tasks, PDF, admin, terminal)
├── frontend/                       # React dashboard
├── channels/                       # MCP channel bridge
│   └── artemis-channel/            # Push event bridge (Bun, port 8790)
├── db/migrations/                  # Supabase schema (001-023)
└── pyproject.toml
```

## Skills & Routing

**Quick reference -- scout vs apply:**
- **scout** = managing the job *pipeline* (finding jobs, syncing sources, reviewing the queue, checking status). Use it when you're thinking about the list of jobs.
- **apply** = working a *specific job* (analyzing a posting, generating resume + cover letter + primer, submitting). Use it once you've picked a job to pursue.

| Skill | Commands | When to use it |
|-------|----------|----------------|
| **scout** | `/artemis:scout`, `/artemis:sync`, `/artemis:review`, `/artemis:status` | Finding jobs, updating the pipeline, triaging what came in |
| **apply** | `/artemis:analyze`, `/artemis:generate`, `/artemis:submit` | Working a specific posting -- analysis, resume/cover letter, submission |
| **network** | `/artemis:network` | Managing contacts, drafting outreach, tracking follow-ups |
| **profile** | `/artemis:context`, `/artemis:prep` | Building candidate context cache, interview prep for a company |
| **coach** | `/artemis:kickoff`, `/artemis:practice`, `/artemis:mock`, `/artemis:debrief` | Coaching, storybank, drills, interview analysis |
| **inbox** | `/artemis:inbox`, `/artemis:schedule`, `/artemis:draft` | Monitoring Gmail + Calendar for recruiter emails and scheduling |
| **linkedin** | `/artemis:linkedin-scout`, `/artemis:linkedin-people`, `/artemis:linkedin-engage` | Browsing LinkedIn for jobs, contacts, engagement (Chrome MCP) |
| **blog** | `/artemis:blog-ideas`, `/artemis:blog-write`, `/artemis:blog-publish`, `/artemis:blog-status` | Content creation + publishing |
| **maintain** | `/artemis:dedupe`, `/artemis:cull` | Deduplicating jobs, culling stale/low-value entries |
| **setup** | `/artemis:setup` | One-time setup wizard for new users |

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
| `user_profiles` | User management: role (admin/user), status (pending/approved/blocked) |

### Job Statuses

`scouted` -> `to_review` -> `applied` -> `recruiter_engaged` -> `interviewing` -> `offer`

Side statuses: `not_interested`, `rejected`, `deleted`

## State (Two Tiers)

All state files live in `state/` (gitignored). Templates in `state/examples/`.

**Hot state** (loaded every session via hooks):
- `identity.md` -- candidate name, headline, positioning, search status
- `voice.md` -- tone rules for all communications
- `active_loops.md` -- current interview loops and time-sensitive items
- `lessons.md` -- operational best practices

**Extended state** (loaded on demand by skills):
- `coaching_state.md` -- master coaching state (storybank, scores, intelligence, strategy)
- `preferences.md` -- target roles, companies, deal-breakers
- `resume_master.md` -- verified resume bullets (source of truth)
- `form_defaults.md` -- standard form answers
- `apply_lessons.md` -- feedback from past applications
- `blog_archive.md` -- blog post analysis
- `candidate_context.md` -- cached profile (generated by `/artemis:context`)

## User Management & Admin Approval

New accounts require admin approval before accessing the dashboard. The first user to sign up is automatically granted the `admin` role.

**Roles:** `admin` (full access + user management + terminal), `user` (standard access)

**Statuses:** `pending` (awaiting approval), `approved` (active), `blocked` (denied)

- A database trigger on `auth.users` auto-creates a `user_profiles` row on signup
- The first user gets `role: admin, status: approved`; subsequent users get `role: user, status: pending`
- `ApprovalMiddleware` in `api/modules/middleware.py` gates all `/api/` endpoints (except auth, profile, and events)
- Admins manage users via the "Users" tab in the dashboard or `GET/PUT /api/admin/users`
- Admins cannot demote or block themselves

**Frontend flow:**
- Unapproved users see a "Pending Approval" or "Account Blocked" screen
- Admin users see "Users" and "Terminal" tabs in the navigation

## Remote Access (nginx)

nginx provides HTTPS reverse proxy with self-signed TLS certificates for remote access over IP (no domain required).

**Setup:**
```bash
brew install nginx          # macOS (or apt install nginx on Linux)
./scripts/setup-nginx.sh    # generate certs + install config
```

**What it does:**
- Generates a self-signed certificate with SAN entries for `localhost` + your local IP
- Installs `nginx/artemis.conf` into the platform-appropriate nginx config directory
- Proxies HTTPS :443 to the Vite frontend (:5173) and API (:8000)
- Supports WebSocket upgrade for the terminal (`/api/terminal`)
- Supports SSE for real-time events (`/api/events`)
- HTTP :80 redirects to HTTPS

**Regenerate certs** (e.g., after IP change):
```bash
./scripts/setup-nginx.sh --regen
```

**For remote access over the internet**, forward port 443 on your router to this machine's local IP. Browsers will show a self-signed cert warning (click through it).

The start script (`scripts/start.sh`) automatically detects and reloads nginx if the Artemis config is installed.

## Terminal Session

Admin users can access a full xterm.js terminal in the dashboard that connects to the running tmux orchestrator session.

**Architecture:**
- Frontend: xterm.js with FitAddon (auto-resize) and WebLinksAddon (clickable URLs)
- Backend: WebSocket endpoint at `/api/terminal` spawns a pty attached to `tmux attach-session -t artemis:orchestrator`
- Auth: First WebSocket message sends the JWT token; server validates admin + approved status
- Resize: Terminal resize events are forwarded via JSON messages and applied with TIOCSWINSZ

**Key files:**
- `api/modules/routes/terminal.py` — WebSocket pty bridge
- `frontend/src/hooks/useTerminal.ts` — WebSocket + xterm.js lifecycle
- `frontend/src/components/TerminalPanel.tsx` — UI component

## MCP Integrations (Optional)

These unlock additional skills but are not required for core functionality:

- **Gmail MCP** -- enables `/artemis:inbox` (recruiter emails, interview scheduling)
- **Google Calendar MCP** -- enables interview loop tracking
- **Claude in Chrome** -- enables `/artemis:linkedin-*` and `/artemis:blog-publish`
- **Supabase MCP** -- enables direct DB access for migrations and queries

## Running Artemis

First-time setup:
```bash
./scripts/setup.sh
```

Optional — enable HTTPS remote access:
```bash
brew install nginx                # macOS (or apt install nginx on Linux)
./scripts/setup-nginx.sh          # generate self-signed certs + install config
```

Start all services (API, frontend, Telegram handler) in a single tmux session:
```bash
./scripts/start.sh          # start everything
./scripts/start.sh --no-frontend   # skip the React frontend
./scripts/stop.sh            # stop services
./scripts/stop.sh --kill     # kill entire tmux session
```

For Claude Desktop (without CLI orchestrator):
```bash
./scripts/start.sh --no-orchestrator   # start API + frontend only
# Then load plugin in Claude Desktop
```

Services:
- **API:** `http://localhost:8000` (FastAPI backend, scheduler)
- **Dashboard:** `http://localhost:5173` (React frontend)
- **HTTPS:** `https://localhost` (via nginx, if configured)
- **Telegram:** Long-running Claude session with orchestrator agent

**First login:** The first user to sign in becomes admin automatically. Subsequent users land on a "Pending Approval" screen until an admin approves them via the Users tab.
