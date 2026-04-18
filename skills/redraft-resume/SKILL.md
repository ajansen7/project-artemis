---
name: redraft-resume
description: Re-draft the resume markdown for an existing application using the cached primer, cover letter, and candidate context — no JD re-fetch, no touching of the other materials.
---

# Redraft-Resume — Resume-Only Re-draft Skill

Polish pass on the resume markdown for a job you've already run `/generate` on. Reuses the cached primer, cover letter, and candidate context — **does not** re-fetch the job posting URL, **does not** modify `cover_letter.md`, `primer.md`, or `form_fills.md`. Optionally takes a short steering note.

## When to Use

The user wants a better resume for an application they've already generated — new bullet selection, sharper tailoring, or a response to a specific nudge ("lean more into eval work", "cut the 5th Smartsheet bullet", etc.) — without re-running the full `/generate` flow.

## Invocation

The skill is typically queued from the dashboard's **✨ Re-draft Resume** button, which inserts a `task_queue` row with `skill: "redraft-resume"` and `skill_args: "Job ID: <uuid>. Note: <optional note>"`.

It can also be run manually by the orchestrator with `/artemis:redraft-resume Job ID: <uuid>[. Note: <note>]`.

## Steps

1. **Parse `skill_args`** — it arrives as a single string like `"Job ID: <uuid>. Note: <optional note>"`. Extract `job_id` and `note` (note may be absent).
2. **Fetch the existing application bundle:**
   ```bash
   artemis-db get-application --id "<job_id>"
   ```
   Returns JSON with `resume_md` (the current draft), `cover_letter_md`, `primer_md`, `form_fills_md`, `gap_analysis_json`, `title`, and `company`. **Do not fetch the job URL** — the primer already captures all the JD intelligence needed.
3. **Read candidate context** (only these — no full `coaching_state.md` read):
   - `state/candidate_context.md` — positioning, voice, strengths, gaps, story index
   - `state/resume_master.md` — canonical verified bullets (source of truth)
   - `state/apply_lessons.md` — read every entry and apply relevant lessons
   - `state/form_defaults.md` — contact info / header fields
   - `state/coaching_state.md` — **only** the specific story sections flagged in the Story Index (e.g., `#### S001`), not the whole file. Same pattern `/generate` uses.
4. **Produce a better-tailored `resume.md`** at `output/applications/<company_slug>-<role_slug>/resume.md` (overwrite). **All formatting rules from `/generate`'s `resume.md` section apply verbatim:**
   - Strip `[tag]` markers (e.g., `[AI]`, `[scale]`, `[0to1]`, `[ops]`, `[eng]`, `[research]`) — they must never appear in the output.
   - Preserve sub-role headers with their `**…**` bold formatting.
   - No `## About` header — the about paragraph sits between the contact line and the first `## Experience` section.
   - No markdown invention — only block types present in `resume_master.md`.
   - **Only use bullet content verbatim from `state/resume_master.md`.** Select and reorder; never rewrite.
5. **Apply the steering note, if any.** If `note` is present, treat it as a signal that overrides default bullet-selection instincts. If blank, run a blind polish pass.
6. **Persist to the DB:**
   ```bash
   artemis-db save-application --id "<job_id>" --resume "output/applications/<slug>/resume.md"
   ```
7. **Regenerate PDF + DOCX + Storage paths:**
   ```bash
   artemis-resume --job-id "<job_id>"
   ```
8. **Log activity** (non-critical — skip silently if it fails):
   ```bash
   artemis-db add-engagement --action-type "redraft-resume" --platform "artemis" --status "posted" --content "Re-drafted resume for <Company> <Role>"
   ```
9. **Report what changed** — a 2-3 bullet summary (bullets swapped in/out, whether the about paragraph was re-framed, any response to the steering note). Do not paste the whole new resume.

## Non-Goals

- Do not modify `cover_letter.md`, `primer.md`, or `form_fills.md`.
- Do not re-read the job posting URL.
- Do not invent new bullet content — select and reorder from `state/resume_master.md` only.
