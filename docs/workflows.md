# Workflows & Command Reference

This guide covers recommended workflows for getting the most out of Artemis, followed by a detailed reference for each command.

---

## Recommended Workflows

Start with Workflow 1 and layer on the others as you get comfortable.

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

The orchestrator is a single long-running Claude session that handles both Telegram messages and scheduled task execution -- tasks arrive instantly via a push channel rather than polling.

See **[automation.md](automation.md)** for scheduler details and **[getting-started.md](getting-started.md)** for Telegram setup.

---

## Command Reference

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
