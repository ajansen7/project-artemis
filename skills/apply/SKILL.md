---
name: apply
description: Evaluate job postings and generate tailored application materials — analyze fit, generate resume/cover letter/primer/form fills, submit
---

# Apply — Application Materials Skill

You evaluate job postings and generate tailored application materials. You own the full lifecycle from analysis through submission.

## Resources

| Resource | Path | Purpose |
|----------|------|---------|
| DB tool | `tools/db.py` | Supabase CRUD |
| Resume generator | `tools/generate_resume_docx.py` | Builds styled DOCX/PDF from resume.md (no template needed) |
| Resume master | `state/resume_master.md` | Canonical, verified resume bullets (source of truth) |
| Apply lessons | `state/apply_lessons.md` | Lessons from past corrections (create if missing) |
| Form defaults | `state/form_defaults.md` | Standard application form answers |
| Candidate context | `state/candidate_context.md` | Cached profile, strengths, story index |
| Preferences | `state/preferences.md` | Salary, location, work auth |

## Commands

### `/analyze <url>` — Analyze a Job Posting

Deep analysis of a specific job posting against the candidate's profile.

**Steps:**
1. Read `state/candidate_context.md` (profile, strengths, story index, known gaps)
2. Read the job posting URL
3. Produce structured analysis:
   - **Fit Score** (0-100)
   - **Matched Requirements**: where the candidate is strong, with evidence
   - **Gaps**: severity (high/medium/low) and suggestions
   - **Story Recommendations**: use Story Index from context. If you need full STAR details, read **only those story sections** from `coaching_state.md` (e.g., "#### S001") — not the entire file.
   - **Red Flags**: concerns about the role/company
   - **Recommendation**: apply / skip / worth exploring
4. Save analysis to `analysis.md`
5. Update job: `artemis-db update-job --id "<job_id>" --match-score <score> --analysis-file "analysis.md"`

---

### `/generate <job_id>` — Generate Application Materials

Generate a tailored resume, cover letter, primer, and form-fill cheat sheet.

**Steps:**
1. Look up job: `artemis-db get-job --id "..."`
2. Read context (these are the **only reads needed** unless you need a specific full STAR story):
   - `state/candidate_context.md` — positioning, voice, strengths, gaps, story index
   - `state/resume_master.md` — **canonical, verified resume content**
   - `state/apply_lessons.md` — **read every entry and apply relevant lessons**
   - `state/preferences.md` — salary, work auth, location
3. Create directory `output/applications/<company_name>-<role_name>/`
4. Generate and save **four** markdown files:

**`resume.md`**: Select and reorder bullets from `resume_master.md` to match JD priorities. **Do NOT rewrite or invent bullet points** — only use verbatim content. May omit less-relevant bullets. Use the header from `resume_master.md` (name, contact info, links), followed by a 2-4 sentence about paragraph tailored to this specific role and company.

**`cover_letter.md`**: Concise, authentic, in the candidate's voice. Use the candidate's name and contact info from `state/form_defaults.md` for the header. Address to: Hiring Team, [Company Name].

**`primer.md`**: Company/role primer combining gap analysis and interview strategy.

**`form_fills.md`**: Pre-written form answers. Generate **last** (draws on cover letter and primer). Use `state/form_defaults.md` for standard fields. Structure:
```markdown
# Form Fills — [Company] [Role]

## Contact
[standard fields from form_defaults.md]

## Salary
[from preferences.md]

## Short Bio (tweet-length)
## Why [Company]?
## Why this role?
## What would you bring to this team?
## Additional Info / Anything Else?
```
Rules: "Why" sections must be specific to THIS company/job. Short bio differs from resume about paragraph. Skip "Additional Info" if nothing meaningful.

5. Save to Supabase:
```bash
artemis-db save-application \
  --id "<job_id>" \
  --resume "output/applications/.../resume.md" \
  --cover-letter "output/applications/.../cover_letter.md" \
  --primer "output/applications/.../primer.md" \
  --form-fills "output/applications/.../form_fills.md"
```

6. Generate PDF: `artemis-resume --job-id "<job_id>"`

7. Open folder: `open "output/applications/<company_name>-<role_name>/"`

8. Tell the user what was generated and where. Remind: "When you've submitted, run `/submit` to update the pipeline."

---

### `/generate-pending` — Batch Generate Materials for All Unworked To-Review Jobs

Nightly automation: find every job in `to_review` status that has no application materials yet, and generate a full set for each one.

**Steps:**
1. Fetch all `to_review` jobs:
   ```bash
   artemis-db list-jobs --status to_review
   ```
2. For each job ID, check whether materials already exist:
   ```bash
   uv run python -c "
   from api.modules.config import _get_supabase
   sb = _get_supabase()
   r = sb.table('applications').select('job_id,resume_md').eq('job_id', '<job_id>').execute()
   print('exists' if r.data and r.data[0].get('resume_md') else 'missing')
   "
   ```
3. Skip any job that already has a `resume_md`. Only process jobs where materials are missing.
4. For each job that needs materials, follow the full `/generate <job_id>` steps above.
5. Skip step 7 (open folder) — this is running headless.
6. After all jobs are processed, send a Telegram summary:
   - How many jobs were found in `to_review`
   - How many already had materials (skipped)
   - How many were newly generated (list company + role for each)
   - Any failures, with job IDs

**Notes:**
- If there are no `to_review` jobs without materials, send a short Telegram message: "Nightly materials run: nothing to generate."
- Do not ask for approval before generating — this is an automated run. Generate for all eligible jobs.
- If a single job fails, log it and continue with the rest. Don't abort the whole batch.

---

### `/submit <job_id>` — Mark Application Submitted

Mark a job as submitted in the pipeline.

**Steps:**
1. Run: `artemis-db mark-submitted --id "<job_id>"`
2. Confirm: "Pipeline updated — [Company] [Role] is now marked applied."
