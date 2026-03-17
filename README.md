# Project Artemis

**An autonomous job hunting system powered by Claude Code.** Artemis scouts for jobs, manages your pipeline, generates tailored application materials, preps you for interviews, and coordinates your networking — end to end.

---

## How It Works

Artemis is built around an **agent orchestrator** that coordinates two peer skills:

```
┌─────────────────────────────────────────────────────────────┐
│                    Artemis Orchestrator                      │
│           .claude/agents/artemis-orchestrator.md            │
│  Central intelligence — coordinates the full job search     │
│  campaign: scouting → pipeline → applications → networking  │
├────────────────────────┬────────────────────────────────────┤
│      Scout Skill       │      Interview Coach Skill         │
│  .claude/skills/       │   .claude/skills/                  │
│    scout/SKILL.md      │     interview-coach/SKILL.md       │
│                        │                                    │
│  Job scouting          │  Interview prep & drills           │
│  Pipeline management   │  Story bank management             │
│  Resume & cover letter │  Behavioral coaching               │
│  Company profiles      │  Mock interviews                   │
│  Networking pipeline   │  Offer negotiation                 │
├────────────────────────┴────────────────────────────────────┤
│                        Supabase                             │
│       jobs · companies · contacts · applications            │
│              (persistent CRM — pipeline state)              │
├─────────────────────────────────────────────────────────────┤
│                 Vite React + FastAPI Backend                 │
│         (Dashboard and headless skill execution)            │
└─────────────────────────────────────────────────────────────┘
```

Open the project in Claude Code and talk to it naturally. The orchestrator decides which skill to invoke.

```
You:     "Scout for AI PM jobs"
Artemis: reads your profile → searches the web → saves to Supabase → reports back

You:     "Analyze this posting: https://..."
Artemis: reads the posting → compares to your profile → scores fit → flags gaps

You:     "Prep me for my Anthropic interview"
Artemis: delegates to Interview Coach → researches company → maps stories → generates talking points
```

---

## Setup

### Prerequisites

- **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)** (Python package manager)
- **Supabase** project (free tier works)
- **Claude Code**
- **LibreOffice** (for PDF resume generation via `soffice` headless)
- **tmux** — `brew install tmux` (used to run Claude tasks in parallel with live output)

### 1. Clone and install dependencies

```bash
git clone <repo-url> project-artemis
cd project-artemis

# Initialize the interview-coach submodule
git submodule update --init

# Install Python backend dependencies
uv sync

# Install Node frontend dependencies
cd frontend && npm install && cd ..
```

### 2. Set up Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Run the SQL migrations in order via the Supabase SQL Editor:

```
db/migrations/001_initial_schema.sql        # Core tables: jobs, companies, contacts, anecdotes
db/migrations/002_allow_anon.sql            # Allow anonymous access for dev
db/migrations/003_optional_company.sql      # Make company_id optional on jobs
db/migrations/004_job_management.sql        # Add not_interested/deleted statuses
db/migrations/005_relax_rls.sql             # Relax RLS for local dev
db/migrations/006_target_companies.sql      # Target company watchlist fields
db/migrations/007_application_markdown.sql  # Dedicated application artifacts table
db/migrations/008_applications_rls.sql      # Relax RLS on applications for local dev
db/migrations/009_networking.sql            # Networking: outreach status, contact-job links, interaction log
db/migrations/010_contacts_rls.sql          # Relax RLS on contacts for local dev
db/migrations/011_add_pdf_path.sql          # Add resume_pdf_path to applications
db/migrations/012_applications_anon_full.sql # Grant anon full access to applications table
db/migrations/013_add_form_fills.sql        # Add form_fills_md to applications
```

3. Copy your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Supabase URL and service role key:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### 3. Verify the DB connection

```bash
uv run python .claude/skills/scout/scripts/db.py status
```

You should see a pipeline status dashboard (all zeros if fresh).

### 4. Connected projects (optional but recommended)

The skills read from a sibling project for candidate context:

| Project | What it provides | Expected path |
|---------|-----------------|---------------|
| `alex-s-lens` | `public/resume.json` (structured resume data) | `~/Dev/alex-s-lens/` |

If this project exists at that path, the skills will read from it directly. If not, you'll be prompted to provide context manually.

### 5. Start the Web Dashboard

Artemis includes a local UI (Vite + React) and a FastAPI bridge that triggers Claude headlessly to run skills from the browser.

**Window 1: Start the API bridge**
```bash
uv run uvicorn api.server:app --reload
```

**Window 2: Start the React frontend**
```bash
cd frontend && npm run dev
```

Opens at `http://localhost:5173`.

**Window 3 (optional): Watch Claude work**
```bash
tmux attach -t artemis
```

Every headless Claude task runs in its own named tmux window. Attach any time to watch tool calls stream live, or switch between windows to monitor parallel tasks.

---

## Commands

Open the project in Claude Code and use natural language, or invoke commands directly.

### `/scout` — Find Jobs

> *"Scout for jobs"* or *"Find AI product manager roles"*

Reads your profile and search preferences, searches the web for job postings, scores each for fit, and saves results to Supabase.

### `/review` — Review Pipeline

> *"Review my pipeline"*

Queries Supabase and presents your pipeline grouped by status. Triage: advance, mark not interested, or delete.

### `/analyze <url>` — Analyze a Posting

> *"Analyze this posting: https://..."*

Deep fit analysis: score (0-100), matched requirements, gaps with severity, story recommendations, red flags, and a go/no-go recommendation.

### `/prep <company>` — Interview Prep

> *"Prep me for Anthropic"*

Delegates to the Interview Coach skill: company research, anticipated questions with story deployments, questions to ask, and stories to drill.

### `/scout apply <job_id>` — Generate Application Materials

> *"Apply to job 1c1682a7"*

Generates four files for the role, saves them to Supabase, builds a styled PDF resume, and opens the applications folder in Finder:

| File | Purpose |
|------|---------|
| `resume.md` | Tailored resume — bullets selected from `resume_master.md`, never fabricated |
| `cover_letter.md` | Authentic cover letter in the candidate's voice |
| `form_fills.md` | Pre-written answers to common form fields: why this company, why this role, short bio, salary, work auth, etc. |
| `primer.md` | Cheat sheet combining gap analysis + interview strategy |

After generation, open the **Application** modal in the dashboard, review materials, apply, then click **Mark Submitted** to advance the job to `applied` in the pipeline.

### `/network` — Networking Pipeline

> *"Show my networking pipeline"* or *"Who should I reach out to today?"*

Surfaces contacts ready for outreach, shows pipeline status across all companies, and resyncs the local memory file from DB.

### `/status` — Dashboard

> *"Show my status"*

Quick pipeline counts by status and target companies being monitored.

### `/sync` — Refresh & Re-score Pipeline

Re-evaluates all active jobs against your current preferences, checks for dead postings, and updates scores.

---

## Web Dashboard

The React dashboard (`http://localhost:5173`) provides a visual interface over the same Supabase pipeline.

**Job pipeline view:**
- Table of all jobs grouped by status with match scores
- Expand any job to see description, details, and gap analysis
- **Start Application** — opens the Application modal for jobs not yet applied to
- **Application** — reopens the modal to review existing materials

**Application modal:**
- Status strip showing which materials have been generated (Resume, Cover Letter, Form Fills, Primer, PDF)
- **Generate Application** button — triggers the Claude CLI headlessly to run `/scout apply`; Finder window opens automatically when complete
- Tabbed viewer for all four generated documents with inline edit + save
- **Mark Submitted** — unlocks once resume and cover letter exist; sets `submitted_at` and advances job status to `applied`

**Networking panel:**
- Full contact pipeline with outreach status, priority, and drafted messages

**Tasks panel (bottom-right floating panel):**
- Appears automatically when any task is running or recently completed
- Pulsing dot = task in progress; click to expand and see a live output tail
- Each task shows name, elapsed time, status, and a kill button
- `tmux attach -t artemis` command with one-click copy to jump to the live view

**All long-running Claude CLI tasks run asynchronously in tmux:**
- UI fires the request and gets a `task_id` back immediately
- Tasks panel polls for completion every 2 seconds
- Multiple tasks can run in parallel in separate tmux windows
- `/scout apply`, `/analyze`, `/sync`, `/scout`, and any other skill invocation all use this flow

**Synchronous operations (direct Supabase writes — no tmux):**
- Save edited documents
- Mark application submitted
- Generate PDF resume (`generate_resume_docx.py`)
- Extract lessons from manual edits (`apply_lessons.md`)

---

## DB Helper CLI

All Supabase operations go through `.claude/skills/scout/scripts/db.py`. Claude calls this automatically, but you can also use it directly:

### Jobs

```bash
# Add a job
uv run python .claude/skills/scout/scripts/db.py add-job \
  --title "Senior AI PM" \
  --company "Anthropic" \
  --url "https://..." \
  --description "Building AI safety tools" \
  --source "scout"

# List all jobs
uv run python .claude/skills/scout/scripts/db.py list-jobs

# List by status
uv run python .claude/skills/scout/scripts/db.py list-jobs --status scouted

# Get full details
uv run python .claude/skills/scout/scripts/db.py get-job --id "uuid-here"

# Update status
uv run python .claude/skills/scout/scripts/db.py update-job --id "uuid" --status "to_review"

# Mark not interested with reason
uv run python .claude/skills/scout/scripts/db.py update-job --id "uuid" --status "not_interested" --reason "Too junior"
```

### Applications

```bash
# Save generated materials to DB
uv run python .claude/skills/scout/scripts/db.py save-application \
  --id "uuid" \
  --resume "applications/company-role/resume.md" \
  --cover-letter "applications/company-role/cover_letter.md" \
  --primer "applications/company-role/primer.md" \
  --form-fills "applications/company-role/form_fills.md"

# Mark submitted (sets submitted_at + advances job status → applied)
uv run python .claude/skills/scout/scripts/db.py mark-submitted --id "uuid"

# Generate styled PDF from resume_md in DB
uv run python .claude/skills/scout/scripts/generate_resume_docx.py --job-id "uuid"
```

### Companies

```bash
# Add a target company
uv run python .claude/skills/scout/scripts/db.py add-company \
  --name "Anthropic" \
  --domain "anthropic.com" \
  --careers-url "https://anthropic.com/careers" \
  --why "AI safety leader, strong product culture" \
  --priority high

# List target companies
uv run python .claude/skills/scout/scripts/db.py list-companies
```

### Pipeline

```bash
uv run python .claude/skills/scout/scripts/db.py status
```

### Networking

```bash
# Resync DB → local memory file (run after any contact status changes)
uv run python .claude/skills/scout/scripts/sync_contacts.py

# Check for drift without writing
uv run python .claude/skills/scout/scripts/sync_contacts.py --check
```

**Source of truth:** Supabase `contacts` table. The local memory file (`.claude/agent-memory/artemis-orchestrator/project_contact_pipeline.md`) is a generated view — never edit it directly.

---

## Project Structure

```
project-artemis/
├── .claude/
│   ├── agents/
│   │   └── artemis-orchestrator.md       # Orchestrator — coordinates the full job search campaign
│   └── skills/
│       ├── scout/                        # Scout skill (job scouting, pipeline, applications)
│       │   ├── SKILL.md                  # Skill definition — commands, context refs, instructions
│       │   ├── applications/             # Generated per-job: resume.md, cover_letter.md, form_fills.md, primer.md, resume.pdf
│       │   ├── references/
│       │   │   ├── candidate_context.md  # Cached candidate profile (generated — do not edit)
│       │   │   ├── resume_master.md      # Verified resume bullets (source of truth — human-approved)
│       │   │   ├── apply_lessons.md      # Lessons extracted from past corrections (improves future drafts)
│       │   │   ├── preferences.md        # Target roles, companies, deal-breakers, salary
│       │   │   └── resume_template.docx  # Noto Sans styled DOCX template for PDF generation
│       │   └── scripts/
│       │       ├── db.py                 # Supabase CRUD CLI (jobs, companies, contacts, applications)
│       │       ├── generate_resume_docx.py # resume.md → DOCX → PDF via LibreOffice
│       │       ├── sync_contacts.py      # Regenerate contacts memory file from DB
│       │       └── seed_contacts.py      # One-time seed of networking contacts to DB
│       └── interview-coach/              # Interview Coach skill (git submodule)
│           ├── SKILL.md                  # Full coaching skill instructions
│           ├── coaching_state.md         # Candidate profile, storybank, interview history
│           └── references/               # Rubrics, calibration engine, command references
├── api/
│   └── server.py                         # FastAPI bridge — headless Claude skill execution + direct Supabase writes
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── JobTable.tsx              # Job pipeline table with expandable rows
│       │   ├── JobDetail.tsx             # Expanded job panel — description, analysis, action buttons
│       │   ├── ApplicationModal.tsx      # Tabbed application modal — materials, generate, mark submitted
│       │   ├── MarkdownModal.tsx         # Reusable markdown viewer/editor with save + extract lessons
│       │   ├── NetworkingPanel.tsx       # Contacts pipeline UI
│       │   └── StatusBadge.tsx           # Pipeline status pill
│       ├── hooks/
│       │   └── useJobs.ts                # Supabase job fetching + status update hook
│       └── types.ts                      # TypeScript interfaces (Job, Contact, etc.)
├── db/migrations/                        # Supabase SQL migrations (001–013)
├── CLAUDE.md                             # Python env instructions (uv run, dependencies)
├── AGENT.md                              # Project-level agent instructions
├── pyproject.toml                        # Python dependencies
└── .env                                  # Supabase credentials (not committed)
```

---

## Supabase Schema

| Table | Purpose |
|-------|---------|
| `jobs` | Pipeline — title, URL, status, match score, gap analysis, source |
| `companies` | Company directory + target watchlist (`is_target`, `why_target`, `priority`) |
| `contacts` | Networking contacts — name, title, LinkedIn, outreach status, priority, draft message |
| `contact_job_links` | Many-to-many join between contacts and specific job postings |
| `contact_interactions` | Timestamped event log per contact (messages sent, responses, meetings) |
| `anecdotes` | STAR-format stories |
| `applications` | Application artifacts — `resume_md`, `cover_letter_md`, `form_fills_md`, `primer_md`, `resume_pdf_path`, `submitted_at` |

### Job Statuses

`scouted` → `to_review` → `applied` → `interviewing` → `offer`

Side statuses: `not_interested` (with reason), `rejected`, `deleted`

> Note: the `to_review → applied` transition happens exclusively through the Application modal (Generate → review → Mark Submitted), not via a direct status advance button.

---

## Updating the Interview Coach skill

The `interview-coach` skill is a git submodule. To pull upstream changes:

```bash
git submodule update --remote .claude/skills/interview-coach
git add .claude/skills/interview-coach
git commit -m "chore: update interview-coach submodule"
```

---

## Archived Code

The original full-stack implementation is preserved on the `archive/full-stack-v1` branch:

- LangGraph agent orchestration with StateGraph
- Next.js Kanban frontend with job detail modals
- ChromaDB vector embeddings + ingestion pipelines
- Gemini function-calling Scout agent with Serper.dev integration
- FastAPI server + Discord bot stubs

To access: `git checkout archive/full-stack-v1`
