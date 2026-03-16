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
│     Artemis Skill      │      Interview Coach Skill         │
│  .claude/skills/       │   .claude/skills/                  │
│    artemis/SKILL.md    │     interview-coach/SKILL.md       │
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
You:    "Scout for AI PM jobs"
Artemis: reads your profile → searches the web → saves to Supabase → reports back

You:    "Analyze this posting: https://..."
Artemis: reads the posting → compares to your profile → scores fit → flags gaps

You:    "Prep me for my Anthropic interview"
Artemis: delegates to Interview Coach → researches company → maps stories → generates talking points
```

---

## Setup

### Prerequisites

- **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)** (Python package manager)
- **Supabase** project (free tier works)
- **Claude Code**

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
db/migrations/008_applications_rls.sql      # Relax RLS for anonymous application reads
db/migrations/009_networking.sql            # Networking: outreach status, contact-job links, interaction log
db/migrations/010_contacts_rls.sql          # Relax RLS on contacts for local dev
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
uv run python .claude/skills/artemis/scripts/db.py status
```

You should see a pipeline status dashboard (all zeros if fresh).

### 4. Connected projects (optional but recommended)

The skills read from two sibling projects for candidate context:

| Project | What it provides | Expected path |
|---------|-----------------|---------------|
| `alex-s-lens` | `public/resume.json` (structured resume) | `~/Dev/alex-s-lens/` |

If these projects exist at those paths, the skills will read from them directly. If not, you'll be prompted to provide context manually.

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

Opens at `http://localhost:5173`. Trigger `/sync`, `/analyze`, or "Generate Applications" directly from the UI.

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

### `/apply <job_id>` — Generate Application

> *"Generate cover letter for job 1c1682a7"*

Generates tailored `resume.md`, `cover_letter.md`, and `primer.md` for the role. Uses your coaching state to match your authentic voice. Saves artifacts to Supabase.

### `/network` — Networking Pipeline

> *"Show my networking pipeline"* or *"Who should I reach out to today?"*

Surfaces contacts ready for outreach, shows pipeline status across all companies, and resyncs the local memory file from DB.

### `/status` — Dashboard

> *"Show my status"*

Quick pipeline counts by status and target companies being monitored.

### `/sync` — Refresh & Re-score Pipeline

Re-evaluates all active jobs against your current preferences, checks for dead postings, and updates scores.

---

## DB Helper CLI

All Supabase operations go through `.claude/skills/artemis/scripts/db.py`. Claude calls this automatically, but you can also use it directly:

### Jobs

```bash
# Add a job
uv run python .claude/skills/artemis/scripts/db.py add-job \
  --title "Senior AI PM" \
  --company "Anthropic" \
  --url "https://..." \
  --description "Building AI safety tools" \
  --source "scout"

# List all jobs
uv run python .claude/skills/artemis/scripts/db.py list-jobs

# List by status
uv run python .claude/skills/artemis/scripts/db.py list-jobs --status scouted

# Get full details
uv run python .claude/skills/artemis/scripts/db.py get-job --id "uuid-here"

# Update status
uv run python .claude/skills/artemis/scripts/db.py update-job --id "uuid" --status "to_review"

# Mark not interested with reason
uv run python .claude/skills/artemis/scripts/db.py update-job --id "uuid" --status "not_interested" --reason "Too junior"
```

### Companies

```bash
# Add a target company
uv run python .claude/skills/artemis/scripts/db.py add-company \
  --name "Anthropic" \
  --domain "anthropic.com" \
  --careers-url "https://anthropic.com/careers" \
  --why "AI safety leader, strong product culture" \
  --priority high

# List target companies
uv run python .claude/skills/artemis/scripts/db.py list-companies
```

### Pipeline

```bash
uv run python .claude/skills/artemis/scripts/db.py status
```

### Networking

```bash
# Seed initial contacts (run once, or re-run to upsert)
uv run python .claude/skills/artemis/scripts/seed_contacts.py

# Resync DB → local memory file (run after any contact status changes)
uv run python .claude/skills/artemis/scripts/sync_contacts.py

# Check for drift without writing
uv run python .claude/skills/artemis/scripts/sync_contacts.py --check
```

**Source of truth:** Supabase `contacts` table. The local memory file (`.claude/agent-memory/artemis-orchestrator/project_contact_pipeline.md`) is a generated view — never edit it directly.

---

## Project Structure

```
project-artemis/
├── .claude/
│   ├── agents/
│   │   └── artemis-orchestrator.md   # Orchestrator — coordinates the full job search campaign
│   └── skills/
│       ├── artemis/                  # Artemis skill (job scouting, pipeline, applications)
│       │   ├── SKILL.md              # Skill definition — commands, context refs, instructions
│       │   ├── references/
│       │   │   ├── candidate_context.md  # Cached candidate profile (generated — do not edit)
│       │   │   └── preferences.md        # Target roles, companies, deal-breakers
│       │   └── scripts/
│       │       ├── db.py             # Supabase CRUD CLI helper
│       │       ├── seed_contacts.py  # One-time seed of networking contacts to DB
│       │       └── sync_contacts.py  # Regenerate contacts memory file from DB
│       └── interview-coach/          # Interview Coach skill (git submodule — noamseg/interview-coach-skill)
│           ├── SKILL.md              # Full coaching skill instructions
│           ├── coaching_state.md     # Candidate profile, storybank, interview history
│           └── references/           # Rubrics, calibration engine, command references
├── api/server.py                     # FastAPI bridge (headless Claude skill execution)
├── frontend/                         # Vite + React dashboard
│   └── src/components/
│       └── NetworkingPanel.tsx       # Contacts pipeline UI
├── db/migrations/                    # Supabase schema (10 migrations)
├── AGENT.md                          # Project-level agent instructions
├── pyproject.toml                    # Python dependencies
└── .env                              # Supabase credentials (not committed)
```

### Updating the Interview Coach skill

The `interview-coach` skill is maintained as a git submodule from [noamseg/interview-coach-skill](https://github.com/noamseg/interview-coach-skill). To pull upstream changes:

```bash
git submodule update --remote .claude/skills/interview-coach
git add .claude/skills/interview-coach
git commit -m "chore: update interview-coach submodule"
```

### Making skills globally available (optional)

By default, skills are available when this project is open in Claude Code. To make them available globally in any Claude Code session, create symlinks in `~/.claude/skills/`:

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/.claude/skills/artemis" ~/.claude/skills/artemis
ln -s "$(pwd)/.claude/skills/interview-coach" ~/.claude/skills/interview-coach
```

---

## Supabase Schema

| Table | Purpose |
|-------|---------|
| `jobs` | Pipeline — title, URL, status, match score, gap analysis, source |
| `companies` | Company directory + target watchlist (is_target, why_target, priority) |
| `contacts` | Networking contacts — name, title, LinkedIn, outreach status, priority, draft message |
| `contact_job_links` | Many-to-many join between contacts and specific job postings |
| `contact_interactions` | Timestamped event log per contact |
| `anecdotes` | STAR-format stories (situation, task, action, result, tags) |
| `applications` | Application artifacts — tailored resume, cover letter, and primer (markdown) |
| `cost_log` | API usage tracking |

### Job Statuses

`scouted` → `to_review` → `applied` → `interviewing` → `offer`

Side statuses: `not_interested` (with reason), `rejected`, `deleted`

---

## Archived Code

The original full-stack implementation is preserved on the `archive/full-stack-v1` branch:

- LangGraph agent orchestration with StateGraph
- Next.js Kanban frontend with job detail modals
- ChromaDB vector embeddings + ingestion pipelines
- Gemini function-calling Scout agent with Serper.dev integration
- FastAPI server + Discord bot stubs

To access: `git checkout archive/full-stack-v1`

---

## Future Considerations

- **Gemini Google Search Grounding** — if Claude's built-in search isn't sufficient, the `google.genai` SDK supports `tools: [{ googleSearch: {} }]`. Exploration code is on the archive branch.
- **Discord Bot** — push notifications on new scouted jobs or pipeline reminders.
- **Scheduled scouting** — automated periodic runs against target company career pages.
