# Project Artemis

**An autonomous job hunting system powered by Claude Code.** Artemis scouts for jobs, manages your pipeline, generates tailored application materials, coaches you for interviews, manages your networking, monitors your inbox and calendar, browses LinkedIn, and helps you build a personal brand through blogging.

---

## Quick Start

### Prerequisites

- **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)**
- **Supabase** project (free tier works)
- **Claude Code** (`npm install -g @anthropic-ai/claude-code`)
- **LibreOffice** for PDF generation: `brew install --cask libreoffice`
- **tmux** for parallel task execution: `brew install tmux`

### Optional MCP Integrations

These unlock additional capabilities but are not required to get started:

- **Gmail MCP** — enables the `/inbox` skill to scan for recruiter emails and interview scheduling
- **Google Calendar MCP** — enables interview loop tracking and scheduling awareness
- **Claude in Chrome** — enables the `/linkedin` and `/blogger` skills for LinkedIn browsing and content publishing
- **Supabase MCP** — lets Claude apply migrations and query your database directly

### 1. Clone and install

```bash
git clone <repo-url> project-artemis
cd project-artemis
git submodule update --init    # clones the interview-coach skill
uv sync
cd frontend && npm install && cd ..
```

### 2. Configure Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Run the SQL migrations in order via the Supabase SQL Editor (`db/migrations/001_*.sql` through `014_*.sql`)
3. Copy and fill in your credentials:

```bash
cp .env.example .env
# edit .env with your SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
```

Verify the connection:

```bash
uv run python .claude/tools/db.py status
```

### 3. Launch

```bash
cd project-artemis
claude
```

Artemis is a **project-level agent** -- all skills, memory, and hooks are self-contained in this directory. Just opening Claude Code here is all you need. The `artemis-orchestrator` agent is auto-discovered from `.claude/agents/` and the session hooks fire automatically.

To invoke the orchestrator explicitly, say **"Start Artemis"** or **"Act as Artemis"** at the start of your session. You can also select it from Claude Code's agent picker with `/agents`.

### 4. First run -- profile setup

On a fresh clone, the session hook detects that no candidate profile exists and prompts you immediately. Artemis will:

1. Check whether the **interview-coach submodule** is cloned and offer to initialize it if not
2. Ask whether you want to run the **interview-coach kickoff first** (recommended -- it does a deep background capture, resume analysis, and storybank initialization that Artemis can learn from)
3. Walk you through the **Artemis setup wizard** to build your candidate profile, search preferences, resume master, and application form defaults

You can also trigger this manually at any time: just say **"Set me up"** or **"Run setup"**.

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

### Workflow 7: Daily Routine (all integrations)

A power-user daily workflow that covers everything:

```
Morning:
  "Check my inbox"                    # New recruiter emails, interview confirmations
  "Any interviews today?"             # Calendar check
  "Review engagement drafts"          # Approve yesterday's drafted comments

Midday:
  "Scout for new jobs"                # Fresh postings
  "Review my pipeline"                # Triage new finds
  "Who should I reach out to?"        # Networking actions

Afternoon:
  "Generate application for ..."      # Applications for top picks
  "Prep me for tomorrow's interview"  # If you have one coming up
  "Draft a post about ..."            # Content creation
```

---

## Skills & Commands

| Skill | Commands | What it does |
|-------|----------|-------------|
| **hunt** | `/scout`, `/sync`, `/review`, `/status` | Discover jobs, maintain pipeline, triage |
| **apply** | `/analyze`, `/generate`, `/submit` | Evaluate fit, generate application materials, mark submitted |
| **connect** | `/network` | Manage contacts, draft outreach, track status |
| **profile** | `/context`, `/prep` | Build candidate context cache, interview prep |
| **interview-coach** | `/kickoff`, `/practice`, `/mock`, `/debrief` | Coaching, storybank, drills (git submodule) |
| **inbox** | `/inbox` | Monitor Gmail + Calendar for job search activity |
| **linkedin** | `/linkedin` | Browse LinkedIn for jobs, contacts, engagement |
| **blogger** | `/blogger` | Generate blog ideas, draft posts, publish content |
| **artemis-setup** | `/setup` | One-time setup wizard for new users |

### `/scout` -- Find Jobs

> *"Scout for jobs"* or *"Find AI product manager roles"*

Reads your profile and search preferences, searches the web, scores each posting for fit, saves to Supabase.

### `/review` -- Review Pipeline

> *"Review my pipeline"*

Shows pipeline grouped by status. Triage: advance, mark not interested, or delete.

### `/analyze <url>` -- Analyze a Posting

> *"Analyze this posting: https://..."*

Deep fit analysis: score (0-100), matched requirements, gaps with severity, story recommendations, red flags, go/no-go recommendation.

### `/generate <job_id>` -- Generate Application Materials

> *"Generate application for job 1c1682a7"*

Creates four tailored files, saves to Supabase, builds a styled PDF, opens the folder in Finder:

| File | Purpose |
|------|---------|
| `resume.md` | Tailored resume (bullets from `resume_master.md`, never fabricated) |
| `cover_letter.md` | Authentic cover letter in the candidate's voice |
| `form_fills.md` | Pre-written answers: why this company, why this role, short bio, salary |
| `primer.md` | Cheat sheet combining gap analysis + interview strategy |

### `/submit <job_id>` -- Mark Submitted

> *"Submit job 1c1682a7"* (after you've applied externally)

Marks the application as submitted in Supabase, advances job to `applied`.

### `/network` -- Networking Pipeline

> *"Show my networking pipeline"* or *"Who should I reach out to today?"*

Surfaces contacts ready for outreach, tracks status, resyncs from DB.

### `/inbox` -- Monitor Gmail + Calendar

> *"Check my inbox"* or *"Any interviews this week?"*

Scans Gmail for recruiter emails, LinkedIn job alert notifications, interview scheduling, and networking responses. Routes new leads into the pipeline and updates existing job statuses.

### `/linkedin` -- LinkedIn Browsing + Engagement

> *"Browse LinkedIn for jobs"* or *"Find contacts at Anthropic"*

Uses Chrome MCP to actively browse LinkedIn. Saves discovered jobs to the pipeline, identifies contacts at target companies, and drafts engagement actions (likes, comments, connection requests) for your approval.

### `/blogger` -- Content Creation

> *"Draft a post about agentic AI"* or *"What should I write about?"*

Generates blog post ideas aligned with your positioning and target roles. Writes drafts in your voice. Manages the full lifecycle: idea, draft, review, published. Can publish to LinkedIn via Chrome MCP.

### `/context` -- Refresh Profile Cache

> *"Refresh my context"*

Rebuilds `candidate_context.md` from coaching state, resume, and preferences.

### `/prep <company>` -- Interview Prep

> *"Prep me for Anthropic"*

Company research, anticipated questions with story deployments, questions to ask, stories to drill.

### `/status` -- Dashboard

> *"Show my status"*

Quick pipeline counts by status and target companies.

### `/sync` -- Refresh & Re-score Pipeline

Re-evaluates all active jobs against current preferences, prunes dead postings, batch updates scores.

### `/setup` -- Initial Setup

> *"Set me up"* (first time using Artemis)

Interactive wizard that walks you through building your candidate profile, search preferences, resume master, and application form defaults. On a fresh clone this runs automatically.

---

## How It Works

Artemis is built around an **orchestrator agent** that coordinates focused skills, each owning a distinct workflow. Skills invoke shared **tools** (Python CLI scripts) for database and file operations. A **sync layer** keeps data consistent across skills -- insights from coaching update your resume, new leads from email get added to the pipeline, and engagement actions flow through an approval queue.

A **two-tier memory system** keeps context compact: hot memory loads every session, extended memory loads on demand.

```
                        Artemis Orchestrator
                   .claude/agents/artemis-orchestrator.md
                    Routes intent to the right skill
         ┌──────────┬──────────┬──────────┬──────────────────┐
         |          |          |          |                  |
       hunt       apply     connect    profile      interview-coach
     /scout      /analyze   /network   /context        /kickoff
     /sync       /generate             /prep           /practice
     /review     /submit                               /mock
     /status                                           /debrief
         |          |          |          |                  |
         ├──────────┴──────────┴──────────┤                  |
         |          Sync Layer            |                  |
         |   shared context + hooks       |                  |
         ├──────────┬──────────┬──────────┤                  |
         |          |          |          |                  |
       inbox     linkedin   blogger      |                  |
     /inbox      /linkedin  /blogger     |                  |
         |          |          |          |                  |
         └──────────┴──────────┴──────────┴──────────────────┘
                           Shared Tools
                     .claude/tools/db.py
                     .claude/tools/generate_resume_docx.py
                     .claude/tools/sync_contacts.py
                                |
                            Supabase
           jobs . companies . contacts . applications
           engagement_log . blog_posts
```

### Data Flow Between Skills

Artemis skills are designed to share information through Supabase and shared context files:

- **Inbox** scans Gmail and routes new job leads into `jobs`, recruiter replies update job status
- **LinkedIn** saves discovered jobs and contacts to the database, drafts engagement to `engagement_log`
- **Blogger** captures ideas from any skill interaction, manages lifecycle in `blog_posts`
- **Interview Coach** insights feed back into the master resume and candidate profile
- **Connect** picks up contacts discovered by LinkedIn or Inbox skills
- **Apply** uses the latest candidate context, which includes coaching insights

---

## Architecture

### Memory (two tiers)

**Hot memory** (`.claude/memory/hot/`) loads every session via hooks. Kept compact (~70 lines):
- `identity.md` -- candidate name, headline, positioning, search status
- `voice.md` -- tone rules for all communications
- `active_loops.md` -- current interview loops and time-sensitive items
- `lessons.md` -- operational best practices that evolve over time

**Extended memory** lives in skill `references/` dirs and loads on demand:
- `candidate_context.md` -- full cached profile (hunt skill)
- `resume_master.md` -- verified resume bullets (apply skill)
- `apply_lessons.md` -- feedback from past applications (apply skill)
- `preferences.md` -- target roles, companies, deal-breakers (hunt skill)
- `coaching_state.md` -- full coaching state (interview-coach)

### Hooks (`.claude/hooks/`)

| Hook | Event | What it does |
|------|-------|-------------|
| `load-hot-memory.sh` | SessionStart | Injects hot memory; detects fresh install and surfaces setup prompt |
| `check-context.sh` | PreToolUse | Warns if `candidate_context.md` is stale |
| `sync-extended.sh` | Stop | Syncs contacts from DB, cleans up temp files |

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

**Terminal 1 -- API:**
```bash
uv run uvicorn api.server:app --reload
```

**Terminal 2 -- Frontend:**
```bash
cd frontend && npm run dev
```

Opens at `http://localhost:5173`. The dashboard has four tabs:

| Tab | What it shows |
|-----|---------------|
| **Pipeline** | All jobs by status, match scores, gap analysis, application generation |
| **Networking** | Contacts grouped by company, outreach status, interaction history |
| **Engagement** | LinkedIn/blog engagement queue with approve/post/skip workflow |
| **Blog** | Blog post lifecycle from idea through published, with tags and platform |

Attach to tmux (`tmux attach -t artemis`) to watch Claude work.

---

## DB Helper CLI

All Supabase operations go through `.claude/tools/db.py`:

```bash
# Jobs
uv run python .claude/tools/db.py add-job --title "Senior AI PM" --company "Anthropic" --url "https://..." --source "scout"
uv run python .claude/tools/db.py list-jobs
uv run python .claude/tools/db.py list-jobs --status scouted
uv run python .claude/tools/db.py get-job --id "uuid"
uv run python .claude/tools/db.py update-job --id "uuid" --status "to_review"

# Applications
uv run python .claude/tools/db.py save-application --id "uuid" --resume "output/applications/.../resume.md" --cover-letter "..." --primer "..." --form-fills "..."
uv run python .claude/tools/db.py mark-submitted --id "uuid"

# Companies
uv run python .claude/tools/db.py add-company --name "Anthropic" --domain "anthropic.com" --careers-url "https://..." --why "..." --priority high
uv run python .claude/tools/db.py list-companies

# Pipeline
uv run python .claude/tools/db.py status

# Resume PDF
uv run python .claude/tools/generate_resume_docx.py --job-id "uuid"

# Contacts sync
uv run python .claude/tools/sync_contacts.py          # write
uv run python .claude/tools/sync_contacts.py --check  # diff only
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

### Job Statuses

`scouted` -> `to_review` -> `applied` -> `recruiter_engaged` -> `interviewing` -> `offer`

Side statuses: `not_interested` (with reason), `rejected`, `deleted`

---

## Project Structure

```
project-artemis/
  .claude/
    agents/
      artemis-orchestrator.md         # Orchestrator -- routes to skills
    skills/
      hunt/                           # Pipeline discovery + management
        SKILL.md
        references/
          candidate_context.md        # Cached profile (generated)
          preferences.md              # Target roles, companies, deal-breakers
      apply/                          # Application materials
        SKILL.md
        references/
          resume_master.md            # Verified resume bullets (source of truth)
          apply_lessons.md            # Lessons from past corrections
          resume_template.docx        # Noto Sans DOCX template
          form_defaults.md            # Standard form field answers
      connect/                        # Networking pipeline
        SKILL.md
      profile/                        # Candidate context + interview prep
        SKILL.md
      inbox/                          # Gmail + Calendar monitoring
        SKILL.md
      linkedin/                       # LinkedIn browsing + engagement
        SKILL.md
      blogger/                        # Content creation + publishing
        SKILL.md
      artemis-setup/                  # One-time setup wizard
        SKILL.md
      interview-coach/                # Git submodule -- coaching, storybank, drills
        SKILL.md
        coaching_state.md
    tools/
      db.py                           # Supabase CRUD CLI
      generate_resume_docx.py         # Resume markdown to DOCX/PDF
      sync_contacts.py                # DB to contacts markdown
    hooks/
      load-hot-memory.sh              # SessionStart: inject hot memory + fresh-install check
      check-context.sh                # PreToolUse: context freshness check
      sync-extended.sh                # Stop: sync contacts, cleanup
    memory/
      hot/
        identity.md                   # Candidate identity + positioning (gitignored)
        voice.md                      # Tone rules for communications (gitignored)
        active_loops.md               # Current interview loops (gitignored)
        lessons.md                    # Operational best practices (gitignored)
        *.example.md                  # Templates for new users (committed)
  output/                             # All generated artifacts (gitignored)
    applications/                     # Per-job: resume, cover letter, primer, form fills, PDF
    blog/drafts/                      # Blog post markdown drafts
    contacts_pipeline.md              # Generated contacts view
  api/
    server.py                         # FastAPI -- task management + PDF generation
  frontend/src/                       # React dashboard (Pipeline, Networking, Engagement, Blog)
  db/migrations/                      # Supabase SQL migrations (001-014)
  CLAUDE.md                           # Python env + project layout instructions
  pyproject.toml                      # Python dependencies
  .env                                # Supabase credentials (not committed)
```

---

## Forking for Your Own Use

Artemis is designed to be forked. All personal data lives outside the committed codebase:

1. **Fork and clone** the repo
2. **Run `/setup`** -- the wizard builds your personal profile, preferences, and resume from scratch
3. **Hot memory files** (`.claude/memory/hot/*.md`) are gitignored -- your identity never leaks into the repo
4. **`.env`** holds your Supabase credentials (also gitignored)
5. **`output/`** is gitignored -- your applications, PDFs, and blog drafts stay local

The only thing you commit is the system itself. Your data stays yours.

---

## Updating the Interview Coach

The `interview-coach` skill is a git submodule:

```bash
git submodule update --remote .claude/skills/interview-coach
git add .claude/skills/interview-coach
git commit -m "chore: update interview-coach submodule"
```

---

## Archived Code

The original full-stack implementation is on `archive/full-stack-v1`:
LangGraph orchestration, Next.js Kanban, ChromaDB embeddings, Gemini function-calling.

`git checkout archive/full-stack-v1`
