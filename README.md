# Project Artemis

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**An autonomous job hunting system powered by Claude Code.** Artemis scouts for jobs, manages your pipeline, generates tailored application materials, coaches you for interviews, manages your networking, monitors your inbox and calendar, browses LinkedIn, and helps you build a personal brand through blogging.

![Artemis Walkthrough](docs/screenshots/walkthrough.gif)

**[Full UI Walkthrough →](docs/UI_WALKTHROUGH.md)**

---

## Quick Start

### Prerequisites

- **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)**
- **Supabase** project (free tier works)
- **Claude Code** (`npm install -g @anthropic-ai/claude-code`)
- **Node.js 18+** and **[Bun](https://bun.sh)** (for the dashboard and channels)
- **tmux** (`brew install tmux`)
- **LibreOffice** (optional, for PDF generation): `brew install --cask libreoffice`

For the full setup walkthrough (Supabase, MCP integrations, Telegram, scheduled automation), see **[docs/getting-started.md](docs/getting-started.md)**.

### 1. Clone and run setup

```bash
git clone <repo-url> project-artemis
cd project-artemis
./scripts/setup.sh
```

The setup script checks prerequisites, installs all dependencies (Python, Node, Bun), sets up state file templates, configures your `.env`, and verifies the Supabase connection.

### 2. Launch Claude Code

```bash
claude --plugin-dir .
```

Artemis is a **Claude Code plugin** -- all skills, agents, hooks, and tools are self-contained at the project root. The `orchestrator` agent is auto-discovered and session hooks fire automatically.

On a fresh clone, the session hook detects that no candidate profile exists and prompts you immediately. Run `/artemis:setup` to walk through the setup wizard, or just say **"Set me up"**.

### 3. Start all services

```bash
./scripts/start.sh
```

This launches the API server, React dashboard, and orchestrator in a single tmux session. See [docs/getting-started.md](docs/getting-started.md) for details.

---

## Recommended Workflows

These workflows show how to get the most out of Artemis. Start with Workflow 1 and layer on the others as you get comfortable.

### Workflow 1: Core Job Search (start here)

Get your pipeline flowing in a single session.

```
1. "Set me up"                    # Run the setup wizard (first time only)
2. "Scout for AI PM jobs"         # Fills your pipeline with scored postings
3. "Review my pipeline"           # Triage: advance promising roles, skip the rest
4. "Analyze https://..."          # Deep-dive a specific posting
5. "Generate application for ..." # Resume, cover letter, primer, form fills, PDF
6. "Submit job ..."               # After you apply externally, mark it done
```

### Workflow 2: Interview Prep Loop

Once you have active applications, shift into prep mode.

```
1. "Prep me for Anthropic"          # Company research, question mapping, story deployments
2. "Practice the product sense Q"   # Drill a specific question type
3. "Mock interview: system design"  # Full mock with scoring and feedback
4. "Debrief my interview"           # Post-interview analysis, update storybank
```

Insights from coaching feed back into your master resume and candidate profile automatically.

### Workflow 3: Networking + Outreach

Build warm connections at your target companies.

```
1. "Who should I reach out to?"       # Surfaces contacts ranked by relevance
2. "Draft outreach for Sarah at ..."   # Writes a message in your voice
3. "Log: sent connection request"      # Track the interaction
4. "Show my networking pipeline"       # See everyone by status
```

### Workflow 4: Inbox + Calendar Monitoring (requires Gmail + Calendar MCP)

Let Artemis watch your email and calendar for job search activity.

```
1. "Check my inbox"                  # Scans for recruiter replies, LinkedIn notifications
2. "Any interviews this week?"       # Pulls upcoming interviews from calendar
3. "Scan for new job alerts"         # Finds job alert emails from LinkedIn, Indeed, etc.
```

New leads get added to your pipeline automatically. Recruiter responses update job statuses.

### Workflow 5: LinkedIn Engagement (requires Chrome MCP)

Actively browse LinkedIn to discover jobs and build your presence.

```
1. "Browse LinkedIn for PM jobs"      # Searches LinkedIn, saves new postings
2. "Find contacts at Anthropic"       # Discovers people at target companies
3. "Engage with my feed"              # Drafts likes and comments for approval
4. "Review engagement drafts"         # Approve, edit, or skip before posting
```

All engagement goes through an approval queue first. Nothing gets posted without your sign-off.

### Workflow 6: Personal Brand + Blogging (requires Chrome MCP)

Turn job search insights into thought leadership content.

```
1. "What should I write about?"       # Generates post ideas tied to your positioning
2. "Draft a post about ..."           # Writes in your voice, aligned with target roles
3. "Review my blog drafts"            # Edit and approve before publishing
4. "Publish to LinkedIn"              # Posts via Chrome (with your approval)
```

### Workflow 7: Automated Daily Routine + Telegram

Instead of running each skill manually, enable scheduled jobs and interact from your phone:

```
1. Set up Telegram (see docs/getting-started.md)
2. Start services: ./scripts/start.sh
3. Enable schedules in the Dashboard's Schedules tab
4. Interact from Telegram: /scout, /inbox, /status
```

With the scheduler and orchestrator running, Artemis will:
- Scout for new jobs each morning and push results to your phone
- Check your inbox for recruiter emails
- Draft LinkedIn engagement for your approval
- Let you kick off tasks directly from Telegram

The orchestrator is a single long-running Claude session that handles both Telegram messages and scheduled task execution — tasks arrive instantly via a push channel rather than polling.

See **[docs/automation.md](docs/automation.md)** for scheduler details and **[docs/getting-started.md](docs/getting-started.md)** for Telegram setup.

---

## Skills & Commands

| Skill | Commands | What it does |
|-------|----------|-------------|
| **scout** | `/artemis:scout`, `/artemis:sync`, `/artemis:review`, `/artemis:status` | Discover jobs, maintain pipeline, triage |
| **apply** | `/artemis:analyze`, `/artemis:generate`, `/artemis:submit` | Evaluate fit, generate application materials, mark submitted |
| **network** | `/artemis:network` | Manage contacts, draft outreach, track status |
| **profile** | `/artemis:context`, `/artemis:prep` | Build candidate context cache, interview prep |
| **coach** | `/artemis:kickoff`, `/artemis:practice`, `/artemis:mock`, `/artemis:debrief` | Coaching, storybank, drills |
| **inbox** | `/artemis:inbox`, `/artemis:schedule`, `/artemis:draft` | Monitor Gmail + Calendar for job search activity |
| **linkedin** | `/artemis:linkedin-scout`, `/artemis:linkedin-people`, `/artemis:linkedin-engage` | Browse LinkedIn for jobs, contacts, engagement |
| **blog** | `/artemis:blog-ideas`, `/artemis:blog-write`, `/artemis:blog-publish`, `/artemis:blog-status` | Generate blog ideas, draft posts, publish content |
| **maintain** | `/artemis:dedupe`, `/artemis:cull` | Deduplicate jobs, cull stale/low-value pipeline entries |
| **setup** | `/artemis:setup` | One-time setup wizard for new users |

### `/artemis:scout` -- Find Jobs

> *"Scout for jobs"* or *"Find AI product manager roles"*

Reads your profile and search preferences, searches the web, scores each posting for fit, saves to Supabase.

### `/artemis:review` -- Review Pipeline

> *"Review my pipeline"*

Shows pipeline grouped by status. Triage: advance, mark not interested, or delete.

### `/artemis:analyze <url>` -- Analyze a Posting

> *"Analyze this posting: https://..."*

Deep fit analysis: score (0-100), matched requirements, gaps with severity, story recommendations, red flags, go/no-go recommendation.

### `/artemis:generate <job_id>` -- Generate Application Materials

> *"Generate application for job 1c1682a7"*

Creates four tailored files, saves to Supabase, builds a styled PDF, opens the folder in Finder:

| File | Purpose |
|------|---------|
| `resume.md` | Tailored resume (bullets from `resume_master.md`, never fabricated) |
| `cover_letter.md` | Authentic cover letter in the candidate's voice |
| `form_fills.md` | Pre-written answers: why this company, why this role, short bio, salary |
| `primer.md` | Cheat sheet combining gap analysis + interview strategy |

### `/artemis:submit <job_id>` -- Mark Submitted

> *"Submit job 1c1682a7"* (after you've applied externally)

Marks the application as submitted in Supabase, advances job to `applied`.

### `/artemis:network` -- Networking Pipeline

> *"Show my networking pipeline"* or *"Who should I reach out to today?"*

Surfaces contacts ready for outreach, tracks status, resyncs from DB.

### `/artemis:inbox` -- Monitor Gmail + Calendar

> *"Check my inbox"* or *"Any interviews this week?"*

Scans Gmail for recruiter emails, LinkedIn job alert notifications, interview scheduling, and networking responses. Routes new leads into the pipeline and updates existing job statuses.

### `/artemis:linkedin-scout` -- LinkedIn Browsing + Engagement

> *"Browse LinkedIn for jobs"* or *"Find contacts at Anthropic"*

Uses Chrome MCP to actively browse LinkedIn. Saves discovered jobs to the pipeline, identifies contacts at target companies, and drafts engagement actions (likes, comments, connection requests) for your approval.

### `/artemis:blog-write` -- Content Creation

> *"Draft a post about agentic AI"* or *"What should I write about?"*

Generates blog post ideas aligned with your positioning and target roles. Writes drafts in your voice. Manages the full lifecycle: idea, draft, review, published. Can publish to LinkedIn via Chrome MCP.

### `/artemis:context` -- Refresh Profile Cache

> *"Refresh my context"*

Rebuilds `candidate_context.md` from coaching state, resume, and preferences.

### `/artemis:prep <company>` -- Interview Prep

> *"Prep me for Anthropic"*

Company research, anticipated questions with story deployments, questions to ask, stories to drill.

### `/artemis:status` -- Dashboard

> *"Show my status"*

Quick pipeline counts by status and target companies.

### `/artemis:sync` -- Refresh & Re-score Pipeline

Re-evaluates all active jobs against current preferences, prunes dead postings, batch updates scores.

### `/artemis:dedupe` -- Deduplicate Jobs

> *"Dedupe my pipeline"* or *"Find duplicate jobs"*

Scans the pipeline for duplicate postings (same role from different sources, reposted listings, similar titles at the same company). Auto-merges obvious duplicates, combining sources, notes, and contact links. Surfaces ambiguous cases for your review.

### `/artemis:cull` -- Cull Stale Jobs

> *"Cull stale jobs"* or *"Clean up my pipeline"*

Identifies low-value and stale jobs: low match scores, sitting in scouted/to_review for 30+ days with no progress. Presents candidates grouped by reason and culls on your confirmation.

### `/artemis:setup` -- Initial Setup

> *"Set me up"* (first time using Artemis)

Interactive wizard that walks you through building your candidate profile, search preferences, resume master, and application form defaults. On a fresh clone this runs automatically.

---

## How It Works

Artemis is built around a single **long-running orchestrator** that coordinates focused skills, each owning a distinct workflow. Skills invoke shared **tools** (Python CLI scripts) for database and file operations. A **sync layer** keeps data consistent across skills -- insights from coaching update your resume, new leads from email get added to the pipeline, and engagement actions flow through an approval queue.

A **two-tier memory system** keeps context compact: hot memory loads every session, extended memory loads on demand.

```
  Telegram / Dashboard / Scheduler
           │
           ▼
  task_queue (Supabase)
           │
           ▼ (push via artemis-channel MCP)
  ┌─────────────────────────────────────────┐
  │   Artemis Orchestrator (long-running)   │
  │   agents/orchestrator.md                │
  │   Routes intent to the right skill      │
  └──────┬──────┬──────┬──────┬─────────────┘
         |      |      |      |
       scout  apply network profile  coach
     /scout /analyze /network /context  /kickoff
     /sync  /generate         /prep     /practice
     /review /submit                    /mock
     /status                            /debrief
         |
      maintain
     /dedupe /cull
         |      |      |
       inbox linkedin  blog
     /inbox  /linkedin /blog-*
         |
         └──────────────────────────────────┐
                   Shared Tools (bin/)       │
             artemis-db                     │
             artemis-resume                 │
             artemis-sync                   │
             artemis-telegram               │
                       │                   │
                   Supabase ───────────────┘
      jobs . companies . contacts . applications
      engagement_log . blog_posts . task_queue
```

### Data Flow Between Skills

Artemis skills are designed to share information through Supabase and shared context files:

- **Inbox** scans Gmail incrementally (tracks last-check timestamp) and handles two paths: updating active pipeline jobs (rejections, interview scheduling, confirmations) and adding new leads. Always deduplicates — rejected jobs are never re-added regardless of source
- **LinkedIn** saves discovered jobs and contacts to the database, drafts engagement to `engagement_log`
- **Blogger** captures ideas from any skill interaction, manages lifecycle in `blog_posts`
- **Coach** insights feed back into the master resume and candidate profile
- **Network** picks up contacts discovered by LinkedIn or Inbox skills
- **Apply** uses the latest candidate context, which includes coaching insights

---

## Architecture

### State (two tiers)

All state files live in `state/` (gitignored). Templates in `state/examples/`.

**Hot state** loads every session via hooks. Kept compact (~70 lines):
- `identity.md` -- candidate name, headline, positioning, search status
- `voice.md` -- tone rules for all communications
- `active_loops.md` -- current interview loops and time-sensitive items
- `lessons.md` -- operational best practices that evolve over time

**Extended state** loads on demand by skills:
- `coaching_state.md` -- master coaching state (storybank, scores, intelligence, strategy)
- `candidate_context.md` -- cached profile (generated by `/artemis:context`)
- `resume_master.md` -- verified resume bullets (apply skill)
- `apply_lessons.md` -- feedback from past applications (apply skill)
- `preferences.md` -- target roles, companies, deal-breakers (scout skill)

### Hooks (`hooks/`)

| Hook | Event | What it does |
|------|-------|-------------|
| `session-start.sh` | SessionStart | Injects hot state; detects fresh install and surfaces setup prompt |
| `session-stop.sh` | Stop | Syncs contacts from DB, cleans up temp files |

### Output (`output/`)

All generated artifacts land in one gitignored directory:

```
output/
  applications/
    anthropic-pm-claude-code/
      resume.md, resume.pdf, cover_letter.md, primer.md, form_fills.md
    openai-pm-api-agents/
      ...
  blog/
    drafts/                   # Blog post markdown drafts
  contacts_pipeline.md        # Generated view of networking contacts
```

---

## Web Dashboard

The dashboard gives you a visual overview of your entire job search.

![Artemis Pipeline Dashboard](docs/screenshots/01-pipeline-overview.png)

```bash
./scripts/start.sh    # starts API, frontend, and orchestrator
```

Opens at `http://localhost:5173`. The dashboard has five tabs:

| Tab | What it shows |
|-----|---------------|
| **Pipeline** | All jobs by status, match scores, gap analysis, application generation. Sort by score/date/company; group by company; flag duplicates; stale job indicators |
| **Networking** | Contacts grouped by company, outreach status, interaction history |
| **Engagement** | LinkedIn/blog engagement queue with approve/post/skip workflow |
| **Blog** | Blog post lifecycle from idea through published, with tags and platform |
| **Schedules** | Recurring job configuration with enable/disable, cron, and run history |

For a full visual walkthrough of every screen, see **[docs/UI_WALKTHROUGH.md](docs/UI_WALKTHROUGH.md)**.

Attach to tmux (`tmux attach -t artemis`) to watch Claude work.

---

## DB Helper CLI

CLI tools are available via `bin/` wrappers (added to PATH when the plugin is loaded):

```bash
# Jobs
artemis-db add-job --title "Senior AI PM" --company "Anthropic" --url "https://..." --source "scout"
artemis-db list-jobs
artemis-db list-jobs --status scouted
artemis-db get-job --id "uuid"
artemis-db update-job --id "uuid" --status "to_review"
artemis-db find-job --company "Anthropic" --title "PM"  # dedup lookup
artemis-db merge-jobs --keep "keeper-uuid" --merge "duplicate-uuid"

# Applications
artemis-db save-application --id "uuid" --resume "output/applications/.../resume.md" --cover-letter "..." --primer "..." --form-fills "..."
artemis-db mark-submitted --id "uuid"

# Companies
artemis-db add-company --name "Anthropic" --domain "anthropic.com" --careers-url "https://..." --why "..." --priority high
artemis-db list-companies

# Pipeline
artemis-db status

# Task queue (orchestrator execution tracking)
artemis-db list-tasks             # recent tasks
artemis-db list-tasks --status running
artemis-db next-task              # claim oldest queued task
artemis-db update-task --id "uuid" --status complete --output-summary "..."

# Resume PDF
artemis-resume --job-id "uuid"

# Contacts sync
artemis-sync          # write
artemis-sync --check  # diff only
```

---

## Supabase Schema

| Table | Purpose |
|-------|---------|
| `jobs` | Pipeline: title, URL, status, match score, gap analysis, source |
| `companies` | Company directory + target watchlist |
| `contacts` | Networking contacts: name, title, LinkedIn, outreach status, source |
| `contact_job_links` | Many-to-many join: contacts to job postings |
| `contact_interactions` | Timestamped event log per contact |
| `anecdotes` | STAR-format stories |
| `applications` | Artifacts: `resume_md`, `cover_letter_md`, `form_fills_md`, `primer_md`, `resume_pdf_path`, `submitted_at` |
| `engagement_log` | LinkedIn/blog engagement actions with approval workflow |
| `blog_posts` | Content lifecycle: idea, draft, review, published |
| `scheduled_jobs` | Recurring automation: skill, cron schedule, enabled, run history |
| `task_queue` | Execution log: queued/running/complete tasks with skill, args, output, and timing |

### Job Statuses

`scouted` -> `to_review` -> `applied` -> `recruiter_engaged` -> `interviewing` -> `offer`

Side statuses: `not_interested` (with reason), `rejected`, `deleted`

---

## Project Structure

```
project-artemis/                        # Plugin root
  .claude-plugin/
    plugin.json                         # Plugin manifest (name: "artemis")
  skills/                               # All skills
    scout/                              # Pipeline discovery + management
    apply/                              # Application materials
    network/                            # Networking pipeline
    profile/                            # Candidate context + interview prep
    coach/                              # Coaching, storybank, drills
    inbox/                              # Gmail + Calendar monitoring
    linkedin/                           # LinkedIn browsing + engagement
    blog/                               # Content creation + publishing
    maintain/                           # Pipeline hygiene -- dedupe, cull
    setup/                              # One-time setup wizard
  agents/
    orchestrator.md                     # Unified orchestrator: Telegram + task execution
  hooks/
    hooks.json                          # Plugin hook configuration
    session-start.sh                    # Load hot state on session start
    session-stop.sh                     # Auto-sync on session end
  bin/                                  # CLI tools (added to PATH by plugin)
    artemis-db                          # Supabase CRUD operations
    artemis-sync                        # Contacts DB -> markdown sync
    artemis-resume                      # Resume markdown -> DOCX/PDF
    artemis-telegram                    # Telegram notifications
  tools/                                # Python CLI source
    db.py                               # Thin CLI shim (forwards to db_modules/)
    db_modules/                         # Modular Supabase CRUD package
    generate_resume_docx.py             # Resume markdown to DOCX/PDF
    sync_contacts.py                    # DB to contacts markdown
    push_to_telegram.py                 # Send formatted messages to Telegram
    migrate_state.py                    # Migration from legacy .claude/ layout
  state/                                # User state files (gitignored)
    examples/                           # Templates for new users (committed)
  rules/                                # Auto-loaded rules
    data-handling.md                    # PII, CLI, data source rules
    pipeline-workflow.md                # Job pipeline operational rules
  templates/
    resume_template.docx                # Resume formatting template
  .mcp.json                             # MCP server registration (artemis-channel)
  settings.json                         # Plugin default settings
  CLAUDE.md                             # Project instructions
  channels/
    artemis-channel/                    # MCP channel: push task events into orchestrator
  scripts/
    setup.sh                            # New user setup wizard
    start.sh                            # Start all services in tmux
    stop.sh                             # Stop services and clean up
  output/                               # All generated artifacts (gitignored)
  api/
    server.py                           # FastAPI -- scheduler, task queue, PDF generation
  frontend/src/                         # React dashboard
  db/migrations/                        # Supabase SQL migrations (001-017)
  pyproject.toml                        # Python dependencies
  .env                                  # Supabase credentials (gitignored)
```

---

## Forking for Your Own Use

Artemis is designed to be forked. All personal data lives outside the committed codebase:

1. **Fork and clone** the repo
2. **Run `./scripts/setup.sh`** then **`/artemis:setup`** -- the wizard builds your personal profile, preferences, and resume from scratch
3. **State files** (`state/*.md`) are gitignored -- your identity never leaks into the repo
4. **`.env`** holds your Supabase credentials (also gitignored)
5. **`output/`** is gitignored -- your applications, PDFs, and blog drafts stay local

The only thing you commit is the system itself. Your data stays yours.

---

## Archived Code

The original full-stack implementation is on `archive/full-stack-v1`:
LangGraph orchestration, Next.js Kanban, ChromaDB embeddings, Gemini function-calling.

`git checkout archive/full-stack-v1`

---

## License

This project is licensed under the **[MIT License](LICENSE)** — free to use, modify, fork, and build on for any purpose.
