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
| Candidate context | `.claude/skills/hunt/references/candidate_context.md` | Scoring and matching |
| Preferences | `.claude/skills/hunt/references/preferences.md` | Target companies, roles |
| Identity | `.claude/memory/hot/identity.md` | Candidate name for matching |
| Voice | `.claude/memory/hot/voice.md` | Tone for drafted emails |
| Inbox state | `.claude/skills/inbox/references/inbox_state.json` | Last check timestamp |

## MCP Tools Used

Gmail tools come from the **smithery-gmail** MCP server (tool prefix: `mcp__smithery-gmail__`):

- `fetch_emails` — search inbox with Gmail query syntax (use `query` param, e.g. `"from:recruiter after:2026/03/01"`)
- `fetch_message_by_message_id` — read full message content by ID
- `fetch_message_by_thread_id` — read full thread for context
- `create_email_draft` — draft reply/follow-up emails
- `list_labels` — list all labels (including IDs needed for `add_label_to_email`)
- `create_label` — create a new label if it doesn't exist
- `add_label_to_email` — apply a label to a message by message ID

Calendar tools come from the **claude.ai Google Calendar** MCP server:

- `gcal_list_events` — list upcoming calendar events
- `gcal_list_calendars` — find the right calendar

### Job Applications Label

Before Step 2, ensure the **"Job Applications"** label exists and cache its ID for the session:

```
1. Call list_labels
2. Search results for a label named "Job Applications" (case-insensitive)
3. If found: store its id as JOB_LABEL_ID
4. If not found: call create_label with label_name="Job Applications" → store the returned id as JOB_LABEL_ID
```

This only needs to happen once per `/inbox` run. Reuse `JOB_LABEL_ID` for all labeling calls in Steps 3–4.

## Commands

### `/inbox` — Scan Gmail for Job Search Activity

Scan emails since the last check, classify them, and route actionable data into the pipeline.

**Step 0: Load last-check timestamp**

Read the state file to know where to start:
```bash
cat .claude/skills/inbox/references/inbox_state.json 2>/dev/null || echo '{"last_check": null}'
```

- If `last_check` is non-null (e.g. `"2026-03-20T10:00:00Z"`), extract the date as `YYYY/MM/DD` for the Gmail `after:` filter (e.g. `after:2026/03/20`).
- If `last_check` is null (first run), use `after:` for 14 days ago as fallback.
- Record the current timestamp in a variable — you'll write it to the state file at the end.

**Step 1: Read context**

Read `identity.md` and `.claude/skills/hunt/references/preferences.md` for candidate name and target companies.

**Step 2: Search Gmail**

Use `fetch_emails` with the `after:DATE` filter from Step 0 in all queries. Run these searches and combine results (deduplicate by message ID):

- `after:DATE` — broad recent inbox scan (catches everything including rejections not matched by keywords)
- `from:(*recruiter* OR *talent* OR *hiring*) after:DATE`
- Target companies: build from preferences.md, e.g. `from:(*@anthropic.com OR *@cursor.com) after:DATE`
- Networking: `subject:(accepted your invitation OR sent you a message) from:(*@linkedin.com) after:DATE`
- ATS platforms: `from:(*@greenhouse.io OR *@lever.co OR *@notifications.workday.com OR *@icims.com OR *@myworkday.com OR *@smartrecruiters.com OR *@jobvite.com) after:DATE`

**Note:** `fetch_emails` searches all mail regardless of Gmail tab/category (Primary, Updates, etc.), so emails routed to the Updates tab are included automatically.

**Exclude already-labeled emails** by adding `-label:"Job Applications"` to each query. This prevents re-processing emails from prior runs.

**Step 3: Read and classify each message**

Read each message with `fetch_message_by_message_id`. Skip messages you've already processed in this session (track message IDs).

There are two fundamentally different purposes for the inbox scan:

**Purpose A — Active loop tracking:** updating the status of jobs already in your pipeline (rejections, interview scheduling, confirmations, recruiter replies). This is the most important path. Every email that mentions a company and role should be checked against the pipeline first.

**Purpose B — New lead discovery:** recruiter outreach emails and LinkedIn job notification emails that introduce roles not yet in the pipeline.

For **every email** that mentions a company and role, look up the pipeline first:
```bash
uv run python .claude/tools/db.py find-job --company "Company Name" --title "Role Title"
```
The result of this lookup determines which path to take (see below).

---

**Path A: Email matches an existing pipeline job**

| Classification | Indicators | Action |
|---------------|------------|--------|
| **Rejection** | "unfortunately", "not moving forward", "other candidates", "decided not to", "not selected", "not a fit", "we've decided to move forward with other candidates" | `update-job --id "uuid" --status "rejected" --reason "rejection email received"` |
| **Application confirmation** | "received your application", "application confirmed", "we received your application" | Verify status is `applied` or higher; if still `scouted`/`to_review`, advance to `applied` |
| **Interview scheduling / next steps** | "we'd like to schedule", "next steps", "phone screen", calendar invite, "we're impressed" | Advance to `recruiter_engaged` if just scheduling; advance to `interviewing` if a call is confirmed on calendar |
| **Status hold / delay** | "taking longer than expected", "still reviewing", "we'll be in touch" | No status change needed; note it |
| **Offer** | "pleased to offer", "offer letter", compensation details | Advance to `offer` |

If `find-job` returns multiple matches (e.g. two Anthropic roles), use the email subject/body to identify the specific one. If genuinely ambiguous, flag for user attention rather than guessing.

If `find-job` returns a result with status `rejected`, `not_interested`, or `deleted` and the email is a **new recruiter outreach** for the same role — skip, do not re-add. Log: "Skipped — already in terminal status."

---

**Path B: No pipeline match — potential new lead**

Only reach this path if `find-job` returned empty results AND the email is clearly a new inbound opportunity (recruiter outreach, LinkedIn job notification, ATS invitation to apply).

```bash
uv run python .claude/tools/db.py add-job --title "..." --company "..." --url "..." --source "gmail" --status "recruiter_engaged"
```

For LinkedIn job notification emails (`jobs-noreply@linkedin.com`), extract each job listed, run `find-job` on each, and only add the ones with no pipeline match.

---

**After classifying any job-related email (Path A or Path B):**

Immediately apply the "Job Applications" label using the `JOB_LABEL_ID` cached in Step 2:
```
add_label_to_email(message_id=<id>, add_label_ids=[JOB_LABEL_ID])
```

This marks the email as processed and prevents it from being re-scanned on future runs (because Step 2 excludes `-label:"Job Applications"`). Apply the label even for emails that result in no action (e.g. status holds, terminal-status skips) — the point is that we read and considered it.

Do **not** apply the label to networking-only emails (LinkedIn connection accepts, InMail replies) — those are handled by the networking path below.

---

**Networking responses** (handled separately — no pipeline lookup needed):

| Classification | Indicators | Action |
|---------------|------------|--------|
| LinkedIn connection accepted | "accepted your invitation" from linkedin.com | `update-contact --linkedin-url "..." --status "connected"` |
| InMail / message reply | Reply from a contact you messaged | `update-contact --linkedin-url "..." --status "responded"` |

---

**Fallback for rejections without a clear title match:**

If the rejection email doesn't clearly identify the role (some ATS emails just say "your application to [Company]"):
```bash
uv run python .claude/tools/db.py find-job --company "Company Name"
```
Read the full email body for any clues: team name, hiring manager, role level (senior/lead/staff), product area, job code, or any language that maps to a known role. Cross-reference with the pipeline results and pick the most logical match. For example:
- "our engineering team" + only one engineering role at that company → match it
- "Claude Code" mentioned anywhere → match "Product Manager, Claude Code"
- Only one active application at that company → match it
- Application submitted date aligns with one role → match it
- Email tone/content matches a specific team's description → match it

Only escalate to the user if there are genuinely multiple plausible matches with no distinguishing signal — for example, two identical-level PM roles at the same company applied on the same day with no team context in the email. Even then, present your best guess with reasoning: "I think this is likely the [Role A] rejection based on [reason], but could also be [Role B] — confirm?"

**Step 4: Report summary**

Report what was found, what was routed, what needs user attention. Structure:
- Rejections processed: N
- Interview scheduling / recruiter engagement: N
- New jobs added: N
- Existing jobs updated with context: N
- Duplicates blocked (terminal status): N
- Items needing your attention: list them

**Step 5: Write state file**

After processing all emails, write the new timestamp:
```bash
mkdir -p .claude/skills/inbox/references
echo '{"last_check": "CURRENT_TIMESTAMP_ISO"}' > .claude/skills/inbox/references/inbox_state.json
```

Replace `CURRENT_TIMESTAMP_ISO` with the actual current UTC timestamp in ISO 8601 format (e.g. `2026-03-24T15:30:00Z`). This ensures the next run starts exactly where this one left off.

---

### `/inbox-linkedin` — Parse LinkedIn Job Notification Emails

Specifically parse LinkedIn's job recommendation emails ("jobs you may be interested in", "new job at X company").

**Steps:**
1. Check last-check timestamp (same as `/inbox` Step 0)
2. Search: `from:(jobs-noreply@linkedin.com) after:DATE`
3. Also: `from:(inmail-hit-reply@linkedin.com) after:DATE` (InMail from recruiters)
4. Read each email and extract job details: title, company, location, LinkedIn job URL
5. Read `candidate_context.md` for scoring factors
6. For each extracted job, run dedup check:
   ```bash
   uv run python .claude/tools/db.py find-job --company "X" --title "Y"
   ```
   - Terminal status → skip
   - Active status → skip (already in pipeline)
   - Not found → include in batch
7. Score each new job (0-100) against preferences and context
8. Batch-add new jobs:
   ```bash
   echo '<json>' | uv run python .claude/tools/db.py batch-add
   ```
   Set `source` to `"linkedin-email"`. `batch-add` also performs company+title dedup as a safety net.
9. Report: jobs found, skipped (terminal), skipped (already in pipeline), added

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
7. Use `create_email_draft` to save as a Gmail draft
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
- **Always dedup before adding.** Call `find-job` before every `add-job`. Never create a new entry for a company+title already in the pipeline.
- **Rejected = terminal.** A job in `rejected`, `not_interested`, or `deleted` status must never be re-added as a new lead, even if the same role appears on a different job board or in a new email.
- **Be conservative with classification.** When uncertain, flag for user review rather than auto-routing.
- **Run sync after.** After routing data, run `uv run python .claude/tools/sync_contacts.py` if any contacts were updated.
- **State file persists.** The `inbox_state.json` file ensures each run only looks at new emails. Never delete it — if something seems off, check the `last_check` timestamp.
