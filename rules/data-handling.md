---
description: Rules for handling data, PII, CLI tools, and Supabase operations
---

# Data Handling Rules

- Never hardcode PII in scripts. Build extensible CLI tools and pipe data via stdin at runtime.
- CLI commands must be single-line. Strip newlines from text fields before passing as args.
- Supabase is the source of truth for structured data. Local markdown files are caches/views.
- Batch operations via JSON stdin are preferred over individual CLI calls for multiple items.
- All engagement actions (likes, comments, posts) go through an approval queue. Nothing gets posted without user sign-off.
- Resume bullets must come verbatim from `resume_master.md`. Never fabricate new ones.
