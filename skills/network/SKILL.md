---
name: network
description: Networking pipeline management — surface contacts, draft outreach, advance statuses, add contacts, sync
---

# Network — Networking Pipeline Skill

You manage the networking pipeline: surfacing contacts ready for outreach, advancing statuses, drafting messages, and keeping the DB and local views in sync.

## Resources

| Resource | Path | Purpose |
|----------|------|---------|
| DB tool | `tools/db.py` | Supabase CRUD |
| Contacts sync | `tools/sync_contacts.py` | DB -> contacts markdown |
| Candidate context | `state/candidate_context.md` | Target companies, active roles |
| Contacts pipeline | `output/contacts_pipeline.md` | Generated view of all contacts |

## Commands

### `/network` — Networking Pipeline

Surface contacts ready for outreach, advance pipeline status, and log interactions.

**Steps:**
1. Query contacts from Supabase:
   ```bash
   artemis-sync --check
   ```
2. Read `state/candidate_context.md` for current target companies and active roles.
3. Build a prioritized action list:
   - **Personal connections** (marked with a star) first — highest leverage
   - Then `draft_ready` contacts ordered by priority (high, medium, low)
   - Flag contacts where `last_contacted_at` is >7 days ago with no status change (follow-up candidates)
   - **Send the list via Telegram** so the user can respond from their phone. Keep it short: name, company, suggested action. Wait for their reply before drafting messages or making status changes.
4. For status changes, use `update-contact`:
   ```bash
   artemis-db update-contact \
     --linkedin-url "linkedin.com/in/handle" --status "sent"
   ```
5. To add new contacts, use `batch-add-contacts` via JSON stdin (**never write bespoke seed scripts**):
   ```bash
   echo '[{"name":"Jane Smith","company":"Anthropic","title":"PM","linkedin_url":"linkedin.com/in/janesmith","relationship_type":"hiring_manager","outreach_status":"draft_ready","priority":"high","is_personal_connection":false,"outreach_message_md":"Subject: ...\n\nHi Jane...","notes":"...","jobs":["4cfb2cb8"]}]' | artemis-db batch-add-contacts
   ```
   Full contact schema (all fields optional except `name` and `company`):
   `name`, `company`, `title`, `linkedin_url` (dedup key), `relationship_type`
   (`recruiter|hiring_manager|referral|alumni|unknown`), `outreach_status`
   (`identified|draft_ready|sent|connected|responded|meeting_scheduled|warm`),
   `priority` (`high|medium|low`), `is_personal_connection`, `outreach_message_md`
   (include `Subject:` line at top), `mutual_connection_notes`, `notes`,
   `jobs` (array of 8-char job ID prefixes to link).

6. **Always end with a resync**:
   ```bash
   artemis-sync
   ```

**Resync rule:** Any time contacts are added, updated, or statuses change, run `sync_contacts.py` before ending. Zero token cost, <2 seconds.

> **CLI commands must be single-line.** Strip newlines from text args.
