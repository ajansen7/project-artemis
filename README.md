# Project Artemis

**An autonomous job hunting system powered by Claude Code.** Artemis scouts for jobs, manages your pipeline, generates tailored application materials, preps you for interviews, and coordinates your networking.

---

## Quick Start

### Prerequisites

- **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)**
- **Supabase** project (free tier works)
- **Claude Code** (`npm install -g @anthropic-ai/claude-code`)
- **LibreOffice** for PDF generation: `brew install --cask libreoffice`
- **tmux** for parallel task execution: `brew install tmux`

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
2. Run the SQL migrations in order via the Supabase SQL Editor (`db/migrations/001_*.sql` through `013_*.sql`)
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

Artemis is a **project-level agent** — all skills, memory, and hooks are self-contained in this directory. Just opening Claude Code here is all you need. The `artemis-orchestrator` agent is auto-discovered from `.claude/agents/` and the session hooks fire automatically.

To invoke the orchestrator explicitly, say **"Start Artemis"** or **"Act as Artemis"** at the start of your session. You can also select it from Claude Code's agent picker with `/agents`.

### 4. First run — profile setup

On a fresh clone, the session hook detects that no candidate profile exists and prompts you immediately. Artemis will:

1. Check whether the **interview-coach submodule** is cloned and offer to initialize it if not
2. Ask whether you want to run the **interview-coach kickoff first** (recommended — it does a deep background capture, resume analysis, and storybank initialization that Artemis can learn from)
3. Walk you through the **Artemis setup wizard** to build your candidate profile, search preferences, resume master, and application form defaults

You can also trigger this manually at any time: just say **"Set me up"** or **"Run setup"**.

---

## How It Works

Artemis is built around an **orchestrator agent** that coordinates focused skills, each owning a distinct workflow. Skills invoke shared **tools** (Python CLI scripts) for database and file operations. A **two-tier memory system** keeps context compact: hot memory loads every session, extended memory loads on demand.

```
                        Artemis Orchestrator
                   .claude/agents/artemis-orchestrator.md
                    Routes intent to the right skill
         ┌──────────┬──────────┬──────────┬──────────────────┐
         │          │          │          │                  │
       hunt       apply     connect    profile      interview-coach
     /scout      /analyze   /network   /context        /kickoff
     /sync       /generate             /prep           /practice
     /review     /submit                               /mock
     /status                                           /debrief
         │          │          │          │                  │
         └──────────┴──────────┴──────────┴──────────────────┘
                           Shared Tools
                     .claude/tools/db.py
                     .claude/tools/generate_resume_docx.py
                     .claude/tools/sync_contacts.py
                                │
                            Supabase
                 jobs . companies . contacts . applications
```

Talk to Artemis naturally:

```
You:     "Scout for AI PM jobs"
Artemis: reads your profile, searches the web, saves to Supabase, reports back

You:     "Analyze this posting: https://..."
Artemis: reads the posting, compares to your profile, scores fit, flags gaps

You:     "Generate application for job 1c1682a7"
Artemis: creates resume, cover letter, primer, form fills, and PDF

You:     "Prep me for my Anthropic interview"
Artemis: researches company, maps stories, generates talking points
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
| **artemis-setup** | `/setup` | One-time setup wizard for new users |

### `/scout` — Find Jobs

> *"Scout for jobs"* or *"Find AI product manager roles"*

Reads your profile and search preferences, searches the web, scores each posting for fit, saves to Supabase.

### `/review` — Review Pipeline

> *"Review my pipeline"*

Shows pipeline grouped by status. Triage: advance, mark not interested, or delete.

### `/analyze <url>` — Analyze a Posting

> *"Analyze this posting: https://..."*

Deep fit analysis: score (0-100), matched requirements, gaps with severity, story recommendations, red flags, go/no-go recommendation.

### `/generate <job_id>` — Generate Application Materials

> *"Generate application for job 1c1682a7"*

Creates four tailored files, saves to Supabase, builds a styled PDF, opens the folder in Finder:

| File | Purpose |
|------|---------|
| `resume.md` | Tailored resume (bullets from `resume_master.md`, never fabricated) |
| `cover_letter.md` | Authentic cover letter in the candidate's voice |
| `form_fills.md` | Pre-written answers: why this company, why this role, short bio, salary |
| `primer.md` | Cheat sheet combining gap analysis + interview strategy |

### `/submit <job_id>` — Mark Submitted

> *"Submit job 1c1682a7"* (after you've applied externally)

Marks the application as submitted in Supabase, advances job to `applied`.

### `/network` — Networking Pipeline

> *"Show my networking pipeline"* or *"Who should I reach out to today?"*

Surfaces contacts ready for outreach, tracks status, resyncs from DB.

### `/context` — Refresh Profile Cache

> *"Refresh my context"*

Rebuilds `candidate_context.md` from coaching state, resume, and preferences.

### `/prep <company>` — Interview Prep

> *"Prep me for Anthropic"*

Company research, anticipated questions with story deployments, questions to ask, stories to drill.

### `/status` — Dashboard

> *"Show my status"*

Quick pipeline counts by status and target companies.

### `/sync` — Refresh & Re-score Pipeline

Re-evaluates all active jobs against current preferences, prunes dead postings, batch updates scores.

### `/setup` — Initial Setup

> *"Set me up"* (first time using Artemis)

Interactive wizard that walks you through building your candidate profile, search preferences, resume master, and application form defaults. On a fresh clone this runs automatically — no need to invoke it manually.

---

## Architecture

### Memory (two tiers)

**Hot memory** (`.claude/memory/hot/`) loads every session via hooks. Kept compact (~70 lines):
- `identity.md` — candidate name, headline, positioning, search status
- `voice.md` — tone rules for all communications
- `active_loops.md` — current interview loops and time-sensitive items
- `lessons.md` — operational best practices that evolve over time

**Extended memory** lives in skill `references/` dirs and loads on demand:
- `candidate_context.md` — full cached profile (hunt skill)
- `resume_master.md` — verified resume bullets (apply skill)
- `apply_lessons.md` — feedback from past applications (apply skill)
- `preferences.md` — target roles, companies, deal-breakers (hunt skill)
- `coaching_state.md` — full coaching state (interview-coach)

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
  contacts_pipeline.md    # generated view of networking contacts
```

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

## Project Structure

```
project-artemis/
  .claude/
    agents/
      artemis-orchestrator.md         # Orchestrator — routes to skills
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
      artemis-setup/                  # One-time setup wizard
        SKILL.md
      interview-coach/                # Git submodule — coaching, storybank, drills
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
    contacts_pipeline.md              # Generated contacts view
  api/
    server.py                         # FastAPI — task management + PDF generation
  frontend/src/                       # React dashboard
  db/migrations/                      # Supabase SQL migrations (001-013)
  CLAUDE.md                           # Python env + project layout instructions
  pyproject.toml                      # Python dependencies
  .env                                # Supabase credentials (not committed)
```

---

## Supabase Schema

| Table | Purpose |
|-------|---------|
| `jobs` | Pipeline: title, URL, status, match score, gap analysis, source |
| `companies` | Company directory + target watchlist |
| `contacts` | Networking contacts: name, title, LinkedIn, outreach status, draft message |
| `contact_job_links` | Many-to-many join: contacts to job postings |
| `contact_interactions` | Timestamped event log per contact |
| `anecdotes` | STAR-format stories |
| `applications` | Artifacts: `resume_md`, `cover_letter_md`, `form_fills_md`, `primer_md`, `resume_pdf_path`, `submitted_at` |

### Job Statuses

`scouted` -> `to_review` -> `applied` -> `interviewing` -> `offer`

Side statuses: `not_interested` (with reason), `rejected`, `deleted`

---

## Updating the Interview Coach

The `interview-coach` skill is a git submodule:

```bash
git submodule update --remote .claude/skills/interview-coach
git add .claude/skills/interview-coach
git commit -m "chore: update interview-coach submodule"
```

---

## Optional: Web Dashboard

**Terminal 1 — API:**
```bash
uv run uvicorn api.server:app --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend && npm run dev
```

Opens at `http://localhost:5173`. Attach to tmux (`tmux attach -t artemis`) to watch Claude work.

---

## Archived Code

The original full-stack implementation is on `archive/full-stack-v1`:
LangGraph orchestration, Next.js Kanban, ChromaDB embeddings, Gemini function-calling.

`git checkout archive/full-stack-v1`
