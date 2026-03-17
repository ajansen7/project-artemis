---
name: apply
description: Evaluate job postings and generate tailored application materials — analyze fit, generate resume/cover letter/primer/form fills, submit
---

# Apply — Application Materials Skill

You evaluate job postings and generate tailored application materials. You own the full lifecycle from analysis through submission.

## Resources

| Resource | Path | Purpose |
|----------|------|---------|
| DB tool | `.claude/tools/db.py` | Supabase CRUD |
| Resume generator | `.claude/tools/generate_resume_docx.py` | Markdown -> DOCX/PDF |
| Resume master | `references/resume_master.md` | Canonical, verified resume bullets (source of truth) |
| Apply lessons | `references/apply_lessons.md` | Lessons from past corrections |
| Resume template | `references/resume_template.docx` | Noto Sans DOCX template |
| Form defaults | `references/form_defaults.md` | Standard application form answers |
| Candidate context | `.claude/skills/hunt/references/candidate_context.md` | Cached profile, strengths, story index |
| Preferences | `.claude/skills/hunt/references/preferences.md` | Salary, location, work auth |

## Commands

### `/analyze <url>` — Analyze a Job Posting

Deep analysis of a specific job posting against the candidate's profile.

**Steps:**
1. Read `.claude/skills/hunt/references/candidate_context.md` (profile, strengths, story index, known gaps)
2. Read the job posting URL
3. Produce structured analysis:
   - **Fit Score** (0-100)
   - **Matched Requirements**: where the candidate is strong, with evidence
   - **Gaps**: severity (high/medium/low) and suggestions
   - **Story Recommendations**: use Story Index from context. If you need full STAR details, read **only those story sections** from `coaching_state.md` (e.g., "#### S001") — not the entire file.
   - **Red Flags**: concerns about the role/company
   - **Recommendation**: apply / skip / worth exploring
4. Save analysis to `analysis.md`
5. Update job: `uv run python .claude/tools/db.py update-job --id "<job_id>" --match-score <score> --analysis-file "analysis.md"`

---

### `/generate <job_id>` — Generate Application Materials

Generate a tailored resume, cover letter, primer, and form-fill cheat sheet.

**Steps:**
1. Look up job: `uv run python .claude/tools/db.py get-job --id "..."`
2. Read context (these are the **only reads needed** unless you need a specific full STAR story):
   - `.claude/skills/hunt/references/candidate_context.md` — positioning, voice, strengths, gaps, story index
   - `references/resume_master.md` — **canonical, verified resume content**
   - `references/apply_lessons.md` — **read every entry and apply relevant lessons**
   - `.claude/skills/hunt/references/preferences.md` — salary, work auth, location
3. Create directory `output/applications/<company_name>-<role_name>/`
4. Generate and save **four** markdown files:

**`resume.md`**: Select and reorder bullets from `resume_master.md` to match JD priorities. **Do NOT rewrite or invent bullet points** — only use verbatim content. May omit less-relevant bullets. MUST use this header:
```markdown
# Alex Jansen
ajansen1090@gmail.com | 509-531-9857 | [LinkedIn](https://www.linkedin.com/in/alex-jansen-product/) | [Portfolio](https://alex-jansen-portfolio.lovable.app/) | [GitHub](https://github.com/ajansen7)

<2-4 sentence about paragraph tailored to this specific role and company.>
```

**`cover_letter.md`**: Concise, authentic, in the candidate's voice. MUST use this header:
```markdown
Alex Jansen
ajansen1090@gmail.com
509-531-9857

Hiring Team
[Company Name]
```

**`primer.md`**: Company/role primer combining gap analysis and interview strategy.

**`form_fills.md`**: Pre-written form answers. Generate **last** (draws on cover letter and primer). Use `references/form_defaults.md` for standard fields. Structure:
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
uv run python .claude/tools/db.py save-application \
  --id "<job_id>" \
  --resume "output/applications/.../resume.md" \
  --cover-letter "output/applications/.../cover_letter.md" \
  --primer "output/applications/.../primer.md" \
  --form-fills "output/applications/.../form_fills.md"
```

6. Generate PDF: `uv run python .claude/tools/generate_resume_docx.py --job-id "<job_id>"`

7. Open folder: `open "output/applications/<company_name>-<role_name>/"`

8. Tell the user what was generated and where. Remind: "When you've submitted, run `/submit` to update the pipeline."

---

### `/submit <job_id>` — Mark Application Submitted

Mark a job as submitted in the pipeline.

**Steps:**
1. Run: `uv run python .claude/tools/db.py mark-submitted --id "<job_id>"`
2. Confirm: "Pipeline updated — [Company] [Role] is now marked applied."
