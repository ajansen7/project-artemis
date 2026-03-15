# Project Artemis

**A Claude Code skill for autonomous job hunting.** Artemis is an AI copilot that scouts for jobs, manages your pipeline, analyzes postings against your profile, and preps you for interviews — all driven from Claude Code or Claude Cowork.

> No frontend. No custom agents. Claude *is* the agent. Artemis provides the structure, context, and tools.

---

## How It Works

Artemis is a [Claude Code skill](https://docs.anthropic.com/en/docs/claude-code) — a set of instructions, context files, and helper scripts that teach Claude how to be your job hunting copilot. When you open this project in Claude Code, the skill is automatically available.

```
You:    "Scout for AI PM jobs"
Claude: reads your profile → searches the web → saves findings to Supabase → reports back

You:    "Analyze this posting: https://..."
Claude: reads the posting → compares to your profile + storybank → scores fit → identifies gaps

You:    "Prep me for my Anthropic interview"
Claude: researches the company → maps your stories → generates talking points
```

### Architecture

```
┌─────────────────────────────────────────────────┐
│                  Claude Code                     │
│  (headless engine for UI / interactive agent)    │
├─────────────────────────────────────────────────┤
│               Artemis Skill                      │
│  SKILL.md  → instructions + commands             │
│  context/  → search preferences                  │
│  scripts/  → db.py (Supabase CRUD)               │
├──────────────────┬──────────────────────────────┤
│  Interview Coach │  Portfolio (alex-s-lens)       │
│  coaching_state  │  resume.json                   │
│  storybank       │  LinkedIn content              │
│  (source of truth for who you are)                │
├─────────────────────────────────────────────────┤
│                 Supabase                         │
│  jobs · companies · contacts · anecdotes         │
│  (persistent CRM — the pipeline state)           │
├─────────────────────────────────────────────────┤
│           Vite React + FastAPI Backend           │
│  (Custom dashboard and visual interaction layer) │
└─────────────────────────────────────────────────┘
```

---

## Setup

### Prerequisites

- **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)** (Python package manager)
- **Supabase** project (free tier works)
- **Claude Code** or **Claude Cowork**

### 1. Clone and install dependencies

```bash
git clone <repo-url> project-artemis
cd project-artemis

# Install Python backend dependencies
uv sync

# Install Node frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Set up Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Run the SQL migrations in order via the Supabase SQL Editor:

```
db/migrations/001_initial_schema.sql    # Core tables: jobs, companies, contacts, anecdotes
db/migrations/002_allow_anon.sql        # Allow anonymous access for dev
db/migrations/003_optional_company.sql  # Make company_id optional on jobs
db/migrations/004_job_management.sql    # Add not_interested/deleted statuses
db/migrations/005_relax_rls.sql         # Relax RLS for local dev
db/migrations/006_target_companies.sql  # Target company watchlist fields
db/migrations/007_application_markdown.sql  # Dedicated application artifacts table
db/migrations/008_applications_rls.sql  # Relax RLS for anonymous application reads
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
uv run python .agent/skills/artemis/scripts/db.py status
```

You should see a pipeline status dashboard (all zeros if fresh).

### 4. Connected projects (optional but recommended)

Artemis reads from two sibling projects for candidate context:

| Project | What it provides | Expected path |
|---------|-----------------|---------------|
| `interview-coach-skill` | `coaching_state.md` (profile, storybank, interview history) | `~/Dev/interview-coach-skill/` |
| `alex-s-lens` | `public/resume.json` (structured resume) | `~/Dev/alex-s-lens/` |

If these projects exist at those paths, Artemis will read from them directly. If not, the skill still works — you'll just need to provide context manually when asked.

### 5. Start the Web Dashboard

Artemis includes a local UI (built with Vite + React) and a FastAPI bridging server that allows you to trigger Claude headlessly to analyze, generate materials, and sync data directly from the browser.

Open two terminal windows:

**Window 1: Start the generic API bridge**
```bash
# From the project-artemis root directory
uv run uvicorn api.server:app --reload
```
*This server listens on port 8000 and executes the `claude` CLI headlessly to perform skills like generating tailored cover letters and resumes.*

**Window 2: Start the React Frontend**
```bash
cd frontend
npm run dev
```
*This will open the dashboard on `http://localhost:5173`. You can manually trigger `/sync`, `/analyze`, or "Generate Applications" directly from the UI without opening the Claude CLI.*

---

## Commands

Open the project in Claude Code and use natural language. These are the core capabilities:

### `/scout` — Find Jobs

> *"Scout for jobs"* or *"Find AI product manager roles"*

Claude reads your profile and search preferences, then uses its built-in web search to find job postings, career pages, hiring threads, and interesting companies. Results are saved to Supabase.

*Note: If Claude adds a job with a match score of `80` or higher, the parent company is immediately auto-targeted and added to your UI sidebar!*

### `/review` — Review Pipeline

> *"Review my pipeline"* or *"Show me what's been scouted"*

Queries Supabase and presents your job pipeline grouped by status. You can triage: advance jobs, mark as not interested (with a reason), or delete.

### `/analyze <url>` — Analyze a Posting

> *"Analyze this posting: https://..."*

Deep analysis of a specific job against your profile:
- Fit score (0-100)
- Matched requirements with evidence
- Gaps with severity and suggestions
- Story recommendations from your storybank
- Red flags
- Apply / skip / explore recommendation

### `/prep <company>` — Interview Prep

> *"Prep me for Anthropic"* or *"Help me prepare for the Cursor interview"*

Generates tailored interview prep:
- Company overview and recent news
- Anticipated questions with story deployments
- Questions to ask
- Stories to drill with opening lines

### `/apply <job_id>` — Generate Application

> *"Generate cover letter for job `1c1682a7`"*

Generates highly tailored job application artifacts:
- Uses `coaching_state.md` to emulate your authentic voice (not generic AI-speak).
- Reads the specific job description and your resume JSON.
- Creates `resume.md`, `cover_letter.md`, and an interview `primer.md` specifically suited for the target role.
- Automatically saves the markdown to the `applications` table in Supabase so it can be viewed directly in the UI.

### `/status` — Dashboard

> *"Show my status"*

Quick pipeline counts by status and target companies being monitored.

---

## DB Helper CLI

All Supabase operations go through `scripts/db.py`. Claude calls this automatically, but you can also use it directly:

### Jobs

```bash
# Add a job
uv run python .agent/skills/artemis/scripts/db.py add-job \
  --title "Senior AI PM" \
  --company "Anthropic" \
  --url "https://..." \
  --description "Building AI safety tools" \
  --source "scout"

# List all jobs
uv run python .agent/skills/artemis/scripts/db.py list-jobs

# List by status
uv run python .agent/skills/artemis/scripts/db.py list-jobs --status scouted

# Get full details
uv run python .agent/skills/artemis/scripts/db.py get-job --id "uuid-here"

# Update status
uv run python .agent/skills/artemis/scripts/db.py update-job --id "uuid" --status "to_review"

# Mark not interested with reason
uv run python .agent/skills/artemis/scripts/db.py update-job --id "uuid" --status "not_interested" --reason "Too junior"
```

### Companies

```bash
# Add a target company
uv run python .agent/skills/artemis/scripts/db.py add-company \
  --name "Anthropic" \
  --domain "anthropic.com" \
  --careers-url "https://anthropic.com/careers" \
  --why "AI safety leader, strong product culture" \
  --priority high

# List target companies
uv run python .agent/skills/artemis/scripts/db.py list-companies
```

### Pipeline

```bash
# Dashboard
uv run python .agent/skills/artemis/scripts/db.py status
```

---

## Project Structure

```
project-artemis/
├── .agent/skills/artemis/
│   ├── SKILL.md              # Skill definition — commands, context refs, instructions
│   ├── context/
│   │   └── preferences.md    # Target roles, companies, deal-breakers (Artemis-owned)
│   └── scripts/
│       └── db.py             # Supabase CRUD CLI helper
├── db/migrations/            # Supabase schema (6 migrations)
├── ingestion/                # Raw source files (resume JSON, coaching state)
├── AGENT.md                  # Project-level agent instructions
├── pyproject.toml            # Python dependencies (supabase, httpx, python-dotenv)
└── .env                      # Supabase credentials (not committed)
```

### What the skill reads from other projects

```
~/Dev/interview-coach-skill/
├── coaching_state.md              # Profile, storybank, interview loops, coaching notes
├── references/storybank-guide.md  # Story framework and deployment guidance
└── CLAUDE.md                      # Full interview coaching skill instructions

~/Dev/alex-s-lens/
└── public/resume.json             # Structured resume (source of truth)
```

---

## Supabase Schema

| Table | Purpose |
|-------|---------|
| `jobs` | Pipeline — title, URL, status, match score, gap analysis, source |
| `companies` | Company directory + target watchlist (is_target, why_target, priority) |
| `contacts` | People at companies (name, title, LinkedIn, relationship type) |
| `anecdotes` | STAR-format stories (situation, task, action, result, tags) |
| `applications` | Submitted applications (resume URL, cover letter, follow-up dates) |
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
- Gemini function-calling Scout agent with iterative tool-use loop
- Serper.dev + DuckDuckGo web search integration
- FastAPI server + Discord bot stubs

To access: `git checkout archive/full-stack-v1`

---

## Future Considerations

- **Gemini Google Search Grounding** — if Claude's built-in search isn't sufficient for scouting, the `google.genai` SDK supports `tools: [{ googleSearch: {} }]` for structured Google Search results. Exploration code is on the archive branch.
- **Discord Bot** — for push notifications on new scouted jobs or pipeline reminders.
- **Scheduled scouting** — automated periodic runs to check target company career pages.
