# Operational Lessons

Best practices that evolve as the agent is used. Skills and the orchestrator should follow these.

## Data Handling
- Never hardcode PII in scripts. Build extensible CLI tools, pipe data via stdin at runtime.
- Batch operations via JSON stdin are preferred over individual CLI calls for multiple items.
- CLI commands must be single-line. Strip newlines from text fields before passing as args.

## Pipeline Workflow
- Always run context freshness check before skills that depend on candidate_context.md.
- After any networking operation, resync contacts via sync_contacts.py (zero-token, <2s).
- Cast a wide net when scouting. Downstream analysis filters. If even somewhat relevant, save it.

## Application Quality
- Resume bullets must come verbatim from resume_master.md. Never fabricate new ones.
- Always read apply_lessons.md before generating application materials.
- Cover letters should lean on your unique positioning, not generic language.

## Communication
- Open with the point, not the context. Avoid preamble.
- Escalate clearly when user input is needed. Don't stall.
