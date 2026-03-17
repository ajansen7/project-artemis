---
name: hunt
description: Job pipeline discovery and management — scout for jobs, sync pipeline, review and triage, dashboard
---

# Hunt — Job Pipeline Skill

You manage the job pipeline: discovering opportunities, maintaining data quality, and providing visibility into the pipeline state.

## Shared Resources

| Resource | Path | Purpose |
|----------|------|---------|
| DB tool | `.claude/tools/db.py` | Supabase CRUD operations |
| Contacts sync | `.claude/tools/sync_contacts.py` | DB -> contacts markdown |
| Candidate context | `.claude/skills/hunt/references/candidate_context.md` | Cached candidate profile (primary context source) |
| Preferences | `.claude/skills/hunt/references/preferences.md` | Target roles, companies, search keywords |

> **CLI commands must be single-line.** Strip newlines from text args. Replace with spaces or ` | ` separators.

## Commands

### `/scout` — Find Jobs

Search the web for job opportunities that match the candidate's profile.

**Steps:**
1. Read `references/candidate_context.md` and `references/preferences.md`
2. Generate diverse search queries (target roles, companies, industries, communities)
3. Use web search to find postings, career pages, hiring threads
4. For each promising find:
   - Extract title, company, location, URL, description
   - **Score relevance (0-100)** using Scoring Factors from context:
     - 80-100: Strong match (role, company, seniority align)
     - 50-79: Moderate (some alignment, adjacent role or less-targeted company)
     - 20-49: Weak (tangentially relevant)
     - 0-19: Barely relevant (save only if company is interesting)
   - Save: `uv run python .claude/tools/db.py add-job --title "..." --company "..." --url "..." --description "..." --source "scout" --match-score <0-100>`
5. Save interesting companies: `uv run python .claude/tools/db.py add-company --name "..." --domain "..." --careers-url "..." --why "..." --priority "high|medium|low"`
6. Report: jobs saved, companies discovered, score distribution, patterns noticed

**Search strategy (be creative):**
- Direct: "AI Product Manager remote jobs 2026"
- Company-specific: "[Company] careers product manager"
- Community: "Hacker News who is hiring March 2026"
- Industry: "AI evaluation companies hiring"
- Adjacent roles: titles the candidate might not think of
- Career pages: target company careers pages

**Important:** Cast a wide net. Downstream analysis filters.

**Batch add (preferred for multiple jobs):**
```bash
echo '[{"title":"Senior PM","company":"Anthropic","url":"https://...","description":"...","match_score":85,"source":"scout"}]' | uv run python .claude/tools/db.py batch-add
```

---

### `/sync` — Refresh & Re-score Pipeline

Bulk maintenance: re-score, prune dead links, update based on latest preferences.

**Steps:**
1. Read `references/candidate_context.md` (scoring factors, target companies, deal breakers)
2. Get all active jobs: `uv run python .claude/tools/db.py list-jobs`
3. For each job (batch by status, `scouted`/`to_review` first):
   - **Check if still live**: read the job URL
   - If dead: search web for relocated posting before deleting. If genuinely gone, mark deleted. If unclear, flag for manual check.
   - **Re-score** against current preferences
   - Update description if changed materially
4. Batch update: `echo '<json>' | uv run python .claude/tools/db.py batch-update`
5. Report sync summary: removed, moved, flagged, re-scored, observations
6. Resync contacts: `uv run python .claude/tools/sync_contacts.py`

---

### `/review` — Review Pipeline

Show pipeline state and let the user triage.

**Steps:**
1. Query: `uv run python .claude/tools/db.py list-jobs`
2. Present summary table grouped by status
3. For each job: title, company, URL, status, match score
4. User actions:
   - Advance: `uv run python .claude/tools/db.py update-job --id "..." --status "to_review"`
   - Not interested: `uv run python .claude/tools/db.py update-job --id "..." --status "not_interested" --reason "..."`
   - Delete: `uv run python .claude/tools/db.py update-job --id "..." --status "deleted"`

---

### `/status` — Dashboard

Quick pipeline overview.

**Steps:**
1. Run: `uv run python .claude/tools/db.py status`
2. Display counts by status, recent activity, and target companies monitored
