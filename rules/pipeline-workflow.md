---
description: Operational rules for the job pipeline, scouting, deduplication, and application workflow
---

# Pipeline Workflow Rules

- Always run context freshness check before skills that depend on candidate_context.md.
- After any networking operation, resync contacts via sync_contacts.py (zero-token, <2s).
- Cast a wide net when scouting. Downstream analysis filters. If even somewhat relevant, save it.
- Jobs are unique by role+company, not by source. A job posted on LinkedIn and Greenhouse is the same job. Before adding a new scouted job, check for an existing entry with the same title and company. If found, merge (use `merge-jobs`) rather than add.
- A rejected job that reappears on a new job board is still rejected.
- Resume bullets must come verbatim from resume_master.md. Never fabricate new ones.
- Always read apply_lessons.md before generating application materials.
- Cover letters should lean on unique positioning, not generic language.
