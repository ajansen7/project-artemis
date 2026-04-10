---
name: linkedin
description: "LinkedIn browsing and engagement — scout jobs, find contacts at target companies, and engage with relevant posts via Chrome MCP. Use when the user wants to actively browse LinkedIn for opportunities or build their professional presence."
---

# LinkedIn — Active Prospecting & Engagement Skill

You browse LinkedIn via Chrome MCP to scout jobs, find networking contacts, and build professional engagement. All actions require an active user Chrome session with LinkedIn logged in.

## Shared Resources

| Resource | Path | Purpose |
|----------|------|---------|
| DB tool | `tools/db.py` | Supabase CRUD operations |
| Candidate context | `state/candidate_context.md` | Scoring factors, target companies |
| Preferences | `state/preferences.md` | Target roles, companies, keywords |
| Identity | `state/identity.md` | Candidate positioning |
| Voice | `state/voice.md` | Tone for comments and outreach |

## MCP Tools Used

- `navigate` — go to LinkedIn pages
- `get_page_text` / `read_page` — extract page content
- `computer` — interact with page elements (click, scroll)
- `form_input` — fill in search fields, comment boxes
- `find` — locate elements on page

## Anti-Automation Safeguards

**These are hard rules, not suggestions. They protect the user's LinkedIn account.**

1. **User must be logged in.** Never store or request LinkedIn credentials. The user must have an active Chrome session with LinkedIn already logged in.
2. **Rate limiting.** Wait 3-8 seconds (vary randomly) between page loads and actions. Never rush.
3. **Session caps per invocation:**
   - Max 5 job search pages browsed
   - Max 10 profile views
   - Max 3 comments posted
   - Max 5 connection request drafts
4. **Human-in-the-loop.** ALL outreach messages, comments, and connection requests require explicit user approval before sending. Present drafts, wait for confirmation.
5. **No automated connection requests.** Draft the request text and present it. The user clicks send.
6. **Natural behavior.** Scroll through pages naturally. Don't jump directly to data extraction. Browse like a human would.

## Commands

### `/linkedin-scout [keywords]` — Browse LinkedIn for Jobs

Search LinkedIn Jobs for opportunities matching the candidate's profile.

**Steps:**
1. Read `preferences.md` for target roles, companies, and keywords
2. If keywords provided, use those. Otherwise, generate search queries from preferences
3. Navigate to LinkedIn Jobs search: `https://www.linkedin.com/jobs/search/?keywords=<encoded>`
4. For each results page (max 5 pages):
   - Use `get_page_text` to extract job listings
   - For each listing: extract title, company, location, LinkedIn job URL
   - **Wait 3-8 seconds** between page loads
5. Read `candidate_context.md` for scoring factors
6. Score each job (0-100) against preferences and context
7. Batch-add to pipeline:
   ```bash
   echo '<json>' | artemis-db batch-add
   ```
   Set `source` to `"linkedin"`
8. **Log activity:**
   ```bash
   artemis-db add-engagement --action-type "linkedin-scout" --platform "artemis" --status "posted" --content "LinkedIn scout: N found, N added to pipeline. Top: [companies]"
   ```
9. Report: jobs found, scores, companies discovered, patterns noticed
10. If high-scoring jobs found at companies with no contacts, suggest `/linkedin-people <company>`

---

### `/linkedin-people <company>` — Find Contacts at a Company

Browse a company's LinkedIn page to find relevant contacts for networking.

**Steps:**
1. Navigate to the company's LinkedIn page
2. Click through to the "People" tab
3. Filter by relevant functions if possible (Product, Engineering, Recruiting, HR)
4. For each relevant person found (max 10 profiles):
   - Extract: name, title, LinkedIn URL
   - Note any mutual connections visible
   - **Wait 3-8 seconds** between profile views
5. Present candidates in a table:
   ```
   | Name | Title | LinkedIn | Mutual Connections | Relevance |
   ```
6. Ask user which contacts to add to the pipeline
7. For selected contacts:
   ```bash
   echo '<json>' | artemis-db batch-add-contacts
   ```
   Include `"source": "linkedin"` in each contact object
8. After adding, sync: `artemis-sync`
9. **Log activity:**
   ```bash
   artemis-db add-engagement --action-type "linkedin-people" --platform "artemis" --status "posted" --content "Found N contacts at [Company]. N added to pipeline"
   ```
10. Suggest drafting outreach via the connect skill (`/network`)

---

### `/linkedin-engage` — Engage with Relevant Posts

Find and engage with posts relevant to the candidate's positioning and target companies.

**Steps:**
1. Read `identity.md` for positioning and `voice.md` for tone rules
2. Read `preferences.md` for target companies and industries
3. Navigate to LinkedIn feed or specific company pages
4. Use `get_page_text` to find relevant posts:
   - Posts by employees at target companies
   - Posts about topics aligned with candidate's expertise (AI, product management, etc.)
   - Posts by hiring managers or recruiters at target companies
5. For each relevant post (max 3 per session):
   - Read the full post content
   - Draft a thoughtful comment that:
     - Adds genuine value or insight (not "Great post!")
     - Reflects the candidate's expertise and positioning
     - Follows `voice.md` tone rules strictly (no em-dashes, conversational, genuine)
     - Is 2-4 sentences, specific, and authentic
   - Present the draft to the user: "I'd like to comment on [person]'s post about [topic]. Here's my draft: ..."
   - **Wait for explicit user approval** before posting
6. If approved:
   - Use `form_input` to enter the comment
   - Log to DB: `artemis-db add-engagement --action-type "comment" --platform "linkedin" --target-url "..." --target-person "..." --content "..." --status "posted"`
7. If the user wants to skip: log as skipped for learning
8. **Log activity:**
   ```bash
   artemis-db add-engagement --action-type "linkedin-engage" --platform "artemis" --status "posted" --content "LinkedIn engagement: N posts reviewed, N comments drafted, N posted, N skipped"
   ```
9. Report: posts engaged with, comments posted, engagement logged

**Comment quality bar:**
- Must add a specific insight, experience, or perspective
- Must reference something concrete from the post
- Must sound like a real person wrote it in 30 seconds
- No generic praise, no buzzwords, no self-promotion

---

## Important Notes

- **LinkedIn detection risk is real.** Always respect rate limits and session caps. If anything feels off (CAPTCHA, unusual page behavior), stop immediately and tell the user.
- **Privacy.** Never store LinkedIn credentials. Never scrape data beyond what's visible on the page. Respect LinkedIn's terms of service.
- **Source tracking.** Always set `source` to `"linkedin"` when adding jobs or contacts from LinkedIn browsing.
- **Cross-skill coordination.** After finding jobs, check if they're already in the pipeline (dedup on URL). After finding contacts, suggest `/network` for outreach drafts.
- **Generalizability.** This skill works for any user — it reads target companies, roles, and positioning from the user's configured preferences and identity files.
