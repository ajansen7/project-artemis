---
name: inbox
description: "Monitor Gmail and Google Calendar for job search activity — scan for recruiter emails, LinkedIn job notifications, interview scheduling, and networking responses. Routes data to existing pipeline tables."
---

# Inbox — Gmail & Calendar Monitoring Skill

You monitor email and calendar for job-search-relevant activity and route actionable data into the existing pipeline. Gmail and Calendar are **sources of information**, not things we mirror into our DB. Emails are ephemeral — extract the data, route it, move on.

## Design Principle

Google Calendar is the source of truth for scheduled calls. We never duplicate calendar events into our DB. We query gcal to cross-reference with our jobs table and surface prep needs.

## Shared Resources

| Resource | Path | Purpose |
|----------|------|---------|
| DB tool | `.claude/tools/db.py` | Supabase CRUD operations |
| Sync tool | `.claude/tools/sync_state.py` | Check data freshness |
| Candidate context | `.claude/skills/hunt/references/candidate_context.md` | Scoring and matching |
| Preferences | `.claude/skills/hunt/references/preferences.md` | Target companies, roles |
| Identity | `.claude/memory/hot/identity.md` | Candidate name for matching |
| Voice | `.claude/memory/hot/voice.md` | Tone for drafted emails |

## MCP Tools Used

- `gmail_search_messages` — search inbox with Gmail query syntax
- `gmail_read_message` — read full message content
- `gmail_read_thread` — read full thread for context
- `gmail_create_draft` — draft reply/follow-up emails
- `gcal_list_events` — list upcoming calendar events
- `gcal_list_calendars` — find the right calendar

## Commands

### `/inbox` — Scan Gmail for Job Search Activity

Scan recent emails for job-relevant messages, classify them, and route actionable data to existing tables.

**Steps:**
1. Read `identity.md` for candidate name and `.claude/skills/hunt/references/preferences.md` for target companies
2. Search Gmail with these queries (combine results, dedup):
   - `subject:(interview OR phone screen OR onsite OR offer) newer_than:7d`
   - `from:(*recruiter* OR *talent* OR *hiring*) newer_than:7d`
   - Target company-specific: build queries from preferences.md target companies, e.g. `from:(*@anthropic.com OR *@cursor.com) newer_than:14d`
   - Networking: `subject:(accepted your invitation OR sent you a message) from:(*@linkedin.com) newer_than:7d`
   - Rejections/status updates: `subject:("application status" OR "update on your application" OR "thank you for your interest" OR "not moving forward" OR "we've decided" OR unfortunately) newer_than:14d`
   - ATS senders (cover confirmations, rejections, and scheduling from ATS platforms): `from:(*@greenhouse.io OR *@lever.co OR *@notifications.workday.com OR *@icims.com OR *@myworkday.com OR *@smartrecruiters.com OR *@jobvite.com) newer_than:14d`
   **Note:** `gmail_search_messages` searches all mail regardless of Gmail tab/category (Primary, Updates, etc.), so emails routed to the Updates tab are included automatically.
3. Read each message with `gmail_read_message`
4. Classify and route:

| Classification | Action |
|---------------|--------|
| **Recruiter outreach** (new role/opportunity) | `uv run python .claude/tools/db.py add-job --source "gmail" --title "..." --company "..." --url "..."`. If promising, update status to `recruiter_engaged` |
| **Application confirmation** | Match to existing job by company+title. Update status if needed |
| **Interview scheduling** | Update matching job to `interviewing`. Note: the actual calendar event stays in gcal — we don't track it separately |
| **Networking response** (LinkedIn connection accepted, message reply) | `uv run python .claude/tools/db.py update-contact --linkedin-url "..." --status "responded"` or `"connected"` |
| **Rejection** | `uv run python .claude/tools/db.py update-job --id "..." --status "rejected"` |
| **ATS notification** | Read carefully — could be confirmation, status update, or rejection. Keywords like "unfortunately", "not moving forward", "other candidates", "decided not to" → rejection. "received your application", "application confirmed" → confirmation. "next steps", "schedule", "we'd like to" → interview scheduling |
| **Follow-up needed** | Flag for user action |

5. Report summary: what was found, what was routed, what needs user attention

**Important:** Don't process the same email twice in a session. Keep a mental list of processed message IDs.

---

### `/inbox-linkedin` — Parse LinkedIn Job Notification Emails

Specifically parse LinkedIn's job recommendation emails ("jobs you may be interested in", "new job at X company").

**Steps:**
1. Search: `from:(jobs-noreply@linkedin.com) newer_than:7d`
2. Also: `from:(inmail-hit-reply@linkedin.com) newer_than:7d` (InMail from recruiters)
3. Read each email and extract job details:
   - Job title, company name, location
   - LinkedIn job URL (if present in email body)
4. Read `candidate_context.md` for scoring factors
5. Score each extracted job (0-100) against preferences and context
6. Batch-add to pipeline: `echo '<json>' | uv run python .claude/tools/db.py batch-add`
   - Set `source` to `"linkedin-email"`
7. Report: jobs found, scores, which ones are worth pursuing

---

### `/schedule` — Review Upcoming Interviews

Query Google Calendar and cross-reference with the jobs pipeline.

**Steps:**
1. Use `gcal_list_events` to get events for the next 14 days
2. Filter for interview-related events (look for keywords: interview, phone screen, chat, call + company names from jobs table)
3. Cross-reference with jobs table: `uv run python .claude/tools/db.py list-jobs --status "interviewing"`
4. For each upcoming interview, report:
   - Date/time, company, role
   - Whether `/prep` materials exist (check `output/applications/<company>-<role>/primer.md`)
   - Days until the interview
5. Flag interviews within 48 hours that don't have prep materials
6. Suggest actions:
   - No prep? → "Run `/prep <company>` to generate interview materials"
   - Prep exists but stale? → "Consider refreshing with `/prep <company>`"
   - Within 24 hours? → "Consider a practice session with `/practice`"

---

### `/draft <job_id or company>` — Draft Follow-Up Email

Draft a follow-up, thank-you, or recruiter response email.

**Steps:**
1. Look up the job: `uv run python .claude/tools/db.py get-job --id "..."`
2. If a company name was provided instead of ID, search by company
3. Read `voice.md` for tone rules
4. Read `identity.md` for candidate positioning
5. Determine email type based on job status:
   - `applied` → follow-up ("checking in on my application")
   - `recruiter_engaged` → response to recruiter outreach
   - `interviewing` → thank-you note after interview round
6. Draft the email following voice rules strictly:
   - No em-dashes, conversational tone, genuine and specific
   - Reference specific details about the role/company
   - Keep it brief and warm
7. Use `gmail_create_draft` to save as a Gmail draft
8. Present the draft text for user review

---

## Job Status Flow

The inbox skill introduces the `recruiter_engaged` status in the pipeline:

```
scouted → to_review → applied → recruiter_engaged → interviewing → offer
                                       ↑
                               (recruiter reaches out,
                                scheduling begins,
                                back-and-forth phase)
```

Use `recruiter_engaged` when:
- A recruiter reaches out about a role (even if you didn't apply)
- You're in email back-and-forth scheduling an initial call
- The recruiter has confirmed interest but no interview is scheduled yet

Advance to `interviewing` when an actual interview/call is scheduled on the calendar.

---

## Important Notes

- **No email storage.** We don't track emails in the DB. We extract data and route it.
- **gcal is truth.** Never try to create our own interview tracking — just query gcal.
- **Dedup on URLs.** When adding jobs from email, the DB deduplicates on URL automatically.
- **Be conservative with classification.** When uncertain, flag for user review rather than auto-routing.
- **Run sync after.** After routing data, run `uv run python .claude/tools/sync_contacts.py` if any contacts were updated.
