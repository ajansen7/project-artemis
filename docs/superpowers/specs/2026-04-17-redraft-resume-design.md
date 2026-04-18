# Re-draft Resume — UI-Triggered Resume Revision + PDF Storage Upsert Fix

## Context

Project Artemis already supports two related actions from the dashboard's Application Modal:

- **"Generate Application"** (`POST /api/generate-application`) — queues a full `/generate` orchestrator task that re-drafts resume + cover letter + primer + form fills from scratch. Expensive and sweeping.
- **"Regen PDF"** (`POST /api/generate-pdf`) — synchronously re-renders the *existing* resume.md to DOCX + PDF. Does not change the markdown.

There is no affordance in between: a way to ask Claude to take another pass at the resume markdown itself (reusing the primer and context already captured for this job) without re-canvassing or touching the cover letter / primer / form fills. The user often wants exactly this — a polish pass on the resume, optionally steered by a short note ("lean more into AI eval work"), followed by an automatic PDF regen.

A second problem compounds the missing feature: after any PDF regen today, the download button frequently returns the **previous** PDF. Root cause is a silent failure in `_upload_artifact_to_storage` — `supabase.storage.upload(...)` without `upsert` returns 409 on a second call for the same path, the exception is swallowed, and `resume_pdf_path_storage` stays pointed at the stale object in the bucket. So even a successful local regen won't surface to the user until this is fixed.

This spec covers both: the new re-draft feature, and the bundled storage-upsert fix that makes any regen workflow actually reach the user.

## Goals

1. Add a UI-triggered resume-only re-draft flow: button in Application Modal → optional steering note → orchestrator runs Claude with a new `/redraft-resume` skill command → new resume.md → auto-regenerated PDF + DOCX → dashboard reflects fresh artifacts on next fetch.
2. Fix the silent Supabase Storage upsert failure so every successful regen actually replaces the downloadable object and updates the DB path.
3. Surface upload failures in the API response instead of masking them as `{ status: "success" }`.

## Non-Goals

- Do not touch cover letter, primer, or form fills during a re-draft.
- Do not re-fetch the job posting URL or re-run `/analyze`. The primer already captures JD intelligence.
- Do not migrate existing stale storage objects. The next successful upsert overwrites them in-place; no backfill job.
- Do not switch the download handler's storage-first ordering. Storage-first is correct once upsert works.
- Do not add cache-busting query params to download URLs. The download endpoint streams bytes directly; there is no URL-level caching in play.
- Do not add a UI for scope selection (resume-only vs. full bundle). The existing "Generate Application" button covers the bundle case; this feature is explicitly resume-only.

## Architecture

Four layers, each small:

1. **Skill** — new `/redraft-resume <job_id> [optional note]` command in `skills/apply/SKILL.md`. Reads existing artifacts + state; writes new `resume.md`; invokes `artemis-resume --job-id <id>` for DOCX/PDF.
2. **API** — new `POST /api/redraft-resume` endpoint in `api/modules/routes/applications.py`. Inserts a `task_queue` row (`skill: "redraft-resume"`, `skill_args` packs job_id + optional note). Returns `{ task_id, status: "queued" }`. The existing orchestrator picks it up and runs the skill against Claude — no new infrastructure.
3. **Frontend** — new "✨ Re-draft Resume" button in `frontend/src/components/ApplicationModal.tsx`, resume-tab preview mode only, next to "Regen PDF". Click reveals an inline optional textarea (collapsed by default). Submit calls `/api/redraft-resume`. Async feedback mirrors the existing "Generate Application" button: spinner during queue + first-leg orchestration, poll task status, then `onGenerationComplete()` → parent refetch.
4. **Bug fix** — `tools/generate_resume_docx.py::_upload_artifact_to_storage` uses `file_options={"upsert": "true"}`, stops swallowing exceptions, and the calling flow (`update_pdf_path_in_db` → `/api/generate-pdf` handler) bubbles failures to the API response.

Data flow for a re-draft:

```
[user clicks Re-draft Resume, optionally types note]
     │
     ▼
POST /api/redraft-resume { job_id, note? }
     │
     ├─── inserts task_queue row
     │       (skill=redraft-resume, skill_args="Job ID: <uuid>. Note: <note>")
     │
     └─── returns { task_id, status: "queued" }
     │
     ▼
[orchestrator picks up task, runs `claude /redraft-resume <job_id> <note>`]
     │
     ▼
skill reads: applications (primer_md, analysis_md, resume_md, cover_letter_md,
             form_fills_md), state/candidate_context.md, state/resume_master.md,
             state/apply_lessons.md, state/form_defaults.md, selective sections
             of state/coaching_state.md
     │
     ▼
skill writes: output/applications/<slug>/resume.md
     │
     ▼
skill runs: artemis-db save-application --id <job_id> --resume <path>
     │
     ▼
skill runs: artemis-resume --job-id <job_id>
             ├─ markdown → DOCX → PDF (LibreOffice)
             ├─ _upload_artifact_to_storage(...) with upsert=true
             └─ update applications.resume_pdf_path / _storage / resume_docx_path
     │
     ▼
[frontend polls task status; on completion, onUpdate() → fresh job row + artifacts]
```

## Components

### Skill: `/redraft-resume` (in `skills/apply/SKILL.md`)

Command contract:

- **Invocation**: `/redraft-resume <job_id> [optional note]`
- **Reads**:
  - DB: `applications.primer_md`, `applications.analysis_md`, `applications.resume_md` (current draft), `applications.cover_letter_md`, `applications.form_fills_md` — all via a single `artemis-db get-application --job-id <id>` call.
  - State files: `state/candidate_context.md`, `state/resume_master.md`, `state/apply_lessons.md`, `state/form_defaults.md`.
  - `state/coaching_state.md` — **only** the specific story sections flagged by the story index in `candidate_context.md`, not the whole file. Follows the same pattern `/generate` uses today.
  - Optional user note from `skill_args`.
- **Does not read**: the job URL, nor anything that would trigger a network fetch.
- **Writes**:
  1. `output/applications/<slug>/resume.md` — overwrite.
  2. `artemis-db save-application --id <job_id> --resume <path>` — DB sync.
  3. `artemis-resume --job-id <job_id>` — triggers DOCX + PDF regen, storage upload, and DB path update.
- **Core instruction to Claude** (to be embedded in the skill):
  > You are revising the resume for an existing application. The primer, analysis, cover letter, and current resume draft describe this role completely — do not re-read the JD. Using that context plus the candidate's story index and resume_master bullet bank, produce a better tailored resume. Select and reorder bullets to match the role's priorities. Apply all formatting rules from the `/generate` section (strip `[tag]` markers, preserve sub-role bolding, no `## About` header, no markdown invention). If the user provided a note, treat it as a steering signal that overrides your default instincts. Only use bullet content verbatim from `resume_master.md`.

### API: `POST /api/redraft-resume` (in `api/modules/routes/applications.py`)

- **Request body**: `RedraftResumeRequest { job_id: str, note: str | None = None }`
- **Behavior**: fetch the job's company/title for name framing (single Supabase query), then insert a `task_queue` row:
  ```
  {
    name: "redraft-resume — <company> <title>",
    skill: "redraft-resume",
    skill_args: "Job ID: <job_id>." + (note ? " Note: <note>" : ""),
    source: "api",
    user_id: <authenticated user_id>,
    status: "queued"
  }
  ```
- **Returns**: `{ task_id, status: "queued", name }`. Same shape as `/api/generate-application` so the frontend pattern reuses cleanly.

### Frontend: re-draft button + optional note (in `ApplicationModal.tsx`)

- New button **"✨ Re-draft Resume"** rendered alongside existing "Regen PDF" when `activeTab === 'resume'` and `mode === 'preview'` and `hasResume`.
- Click: toggles a collapsed textarea directly below the button row (placeholder: `"Optional: any steering notes? (e.g., 'lean more into AI eval work')"`). Blank is fine.
- A secondary **"Send"** button inside the expanded state calls `POST /api/redraft-resume` with `{ job_id, note: note || undefined }`.
- Button state management follows the existing `handleGenerate` / `handleRegeneratePdf` patterns: loading spinner, disabled state, toast on queueing success/failure.
- On queue-success, the modal calls `onGenerationComplete()` so the parent `JobDetail` triggers `onUpdate()` after the orchestrator completes (same pattern as today's Generate Application button). No new polling infrastructure.

### Bug fix: `_upload_artifact_to_storage` + error propagation (in `tools/generate_resume_docx.py` + `api/modules/routes/applications.py`)

- `_upload_artifact_to_storage`: pass `file_options={"upsert": "true"}` to `supabase.storage.from_("artifacts").upload(...)`. On Supabase's Python SDK this is the documented way to replace an existing object.
- Narrow the exception handler: catch the specific Supabase `StorageApiError` (or equivalent) for logging, but **re-raise** so `update_pdf_path_in_db` sees real failures instead of silent None returns. Broad `except Exception` disappears.
- `update_pdf_path_in_db`: let upload exceptions propagate. The calling API endpoint decides the user-facing response.
- `/api/generate-pdf` handler: if `subprocess.run(...)` returns non-zero, OR if `update_pdf_path_in_db` raises, return HTTP 500 with `{ status: "error", message: <details> }` instead of masking with `"success"`.

## Error Handling

- **Upload fails** (permissions, quota, transient network): API returns 500; frontend toast shows the error; user can retry. No DB inconsistency because we only write the storage path after a successful upload.
- **Skill fails mid-flight** (e.g., DB fetch error, resume_master.md missing): orchestrator marks the `task_queue` row `failed` with error text. Frontend polls and surfaces this via the same path as existing `generate` failures.
- **User submits with blank note**: treated as a blind pass. Skill command applies its default instincts against the existing artifacts.
- **User submits re-draft while a previous task is still queued/running for the same job**: frontend disables the button while `regenerating` state is true. Server does not enforce a single-in-flight check (out of scope — same race is possible today with Generate Application).
- **Stale storage objects from pre-fix generations**: first successful re-draft overwrites them via upsert. No migration.

## Testing / Verification

1. **Bug fix, reproduction**: generate PDF for a job; note the storage path; generate a second time; confirm the storage object has a newer `updated_at` and downloads return the second PDF. Pre-fix this fails silently; post-fix it must succeed.
2. **Bug fix, failure surfacing**: intentionally break the upload (e.g., revoke service-role key for the bucket) and confirm `/api/generate-pdf` returns 500 with a readable message instead of `{ status: "success" }`.
3. **Skill command manual run**: from CLI, `claude` invoke `/redraft-resume <job_id>` with no note — confirm new `resume.md` is written, DB is updated, new PDF and DOCX exist at the expected path, storage object is replaced.
4. **Skill command with note**: same run with a specific steering note ("lean more into AI eval work"); inspect the resulting resume.md and verify the bullet selection reflects the nudge while still adhering to formatting rules.
5. **End-to-end UI**: from Application Modal, click "Re-draft Resume" with and without a note. Confirm:
   - Button shows loading state.
   - Task queues (check `task_queue` row with `skill: "redraft-resume"`).
   - Orchestrator picks up the task and runs the skill.
   - On completion, the modal's next fetch shows fresh `resume_md` and a new `resume_pdf_path_storage`.
   - Downloading the PDF returns the newly generated content (not the pre-redraft version).
6. **Non-regression**: confirm Generate Application still works unchanged and still rewrites all four materials.
7. **Formatting rules still apply**: generated resume has no `[tag]` markers, all sub-roles bold, no `## About` header — the existing formatting invariants hold after a re-draft pass.

## Risk Assessment

- **Low-risk**: the skill command, API endpoint, and button all follow existing patterns. The storage upsert flag is a well-documented Supabase SDK feature.
- **Medium-risk**: narrowing the exception handler in `_upload_artifact_to_storage` could surface errors that the old code silently swallowed in unrelated code paths. Mitigated by running the full generate-pending batch once manually post-change to verify no new failures.
- **Out-of-scope regressions**: none expected; cover letter / primer / form fills are untouched; download endpoint is untouched.
