---
name: profile
description: Candidate profile management and interview preparation — build context cache, generate interview prep materials
---

# Profile — Candidate Context & Interview Prep Skill

You manage the candidate profile cache and generate interview preparation materials.

## Connected Projects

Configure paths to companion projects. These are optional — skills degrade gracefully without them.

| Project | Path | What it owns |
|---------|------|-------------|
| **Portfolio** | *(set via `PORTFOLIO_PATH` env var, e.g. `~/Dev/my-portfolio/`)* | Resume, LinkedIn content, professional narrative |
| **Interview Coach** | `.claude/skills/interview-coach/` | Coaching state, storybank, interview prep, drills |

### Key source-of-truth files:

| File | Project | Purpose |
|------|---------|---------|
| `coaching_state.md` | Interview Coach | Full candidate profile, career history, stories, interview intelligence |
| `references/storybank-guide.md` | Interview Coach | Storybank framework and deployment guidance |
| `public/resume.json` | Portfolio | Structured resume data (source of truth) |

### Cross-project updates:
- **New story or refined anecdote** -> Update `coaching_state.md` in Interview Coach
- **Story surfaces a better resume bullet** -> Surface to user and offer to update `resume_master.md` in Artemis
- **Resume positioning change** -> Update resume data in Portfolio project
- **Interview outcome** -> Update the Outcome Log in `coaching_state.md`

### Storybank → resume_master feedback loop:
When the interview-coach's storybank captures a story with a strong impact statement or metric that doesn't yet appear in `resume_master.md`, flag it: "The story you told about [X] suggests a stronger framing for this bullet — want to update resume_master.md?" This keeps both systems in sync as the storybank grows.

## Resources

| Resource | Path | Purpose |
|----------|------|---------|
| DB tool | `.claude/tools/db.py` | Supabase CRUD |
| Candidate context | `.claude/skills/hunt/references/candidate_context.md` | Output: cached profile |
| Preferences | `.claude/skills/hunt/references/preferences.md` | Target roles, companies, deal-breakers |

## Commands

### `/context` — Build & Refresh Candidate Context

Builds or refreshes the cached candidate context from source-of-truth files. This is the **only command** that reads the full external files.

**When to run:**
- First time (cache doesn't exist)
- When `coaching_state.md` has been updated more recently than `candidate_context.md`
- After a coaching session, interview, or major profile change

**Steps:**
1. Read the full source-of-truth files:
   - `coaching_state.md` from Interview Coach (profile, stories, positioning, interview intelligence)
   - `resume.json` from Portfolio (career history, skills)
   - `.claude/skills/hunt/references/preferences.md` (target roles, companies, deal-breakers)
2. Distill into `.claude/skills/hunt/references/candidate_context.md` with these sections:
   - **Profile Summary** — name, current role, target roles, experience level, location
   - **Core Positioning** — voice, differentiator, headline, career arc
   - **Career History** (compact table) — company, title, dates, 1-line highlight
   - **Key Strengths & Differentiators** — top 5-7 with evidence
   - **Story Index** (compact table) — ID, title, "deploy for" tag, drilled status (no full STAR)
   - **Scoring Factors** — weighted criteria for job matching
   - **Deal Breakers** — from preferences
   - **Target Companies** — tiered list from preferences
   - **Known Gaps** — to address proactively
   - **Interview Intelligence** — effective/ineffective patterns, coaching focus
3. Set `Last Synced` timestamp in the file header
4. **Bidirectional sync checks** (new):
   - Run `uv run python .claude/tools/sync_state.py --check --json` to get current sync status
   - If storybank → resume_master is stale: scan coaching_state.md storybank for stories with strong metrics/impact statements not yet in resume_master.md. Surface suggestions: "The story about [X] suggests a stronger bullet — want to update resume_master.md?"
   - If resume → coaching is stale: note that resume positioning changes may not be reflected in coaching state
   - If preferences changed: incorporate updated target companies and deal-breakers into the context
   - Report all sync directions and their status
5. Report what was updated and changes detected since last sync

---

### `/prep <company or job>` — Interview Preparation

Generate tailored interview prep for a specific company or role.

**Steps:**
1. Read `.claude/skills/hunt/references/candidate_context.md` (profile, story index, interview intelligence, known gaps)
2. Look up the job/company: `uv run python .claude/tools/db.py get-job --id "..."`
3. Research the company (web search: recent news, culture, leadership, tech stack)
4. Generate:
   - **Company Overview**: what they do, recent news, culture signals
   - **Role Fit Summary**: why the candidate is competitive
   - **Anticipated Questions** (5-7) with suggested story deployments
   - **Questions to Ask** (3-5) showing genuine understanding
   - **Stories to Drill**: read **only those story sections** from `coaching_state.md` for full STAR details
   - **Watch Out For**: concerns to address proactively (from Known Gaps)
5. If the Interview Coach skill should capture a new interview loop, update `coaching_state.md`
