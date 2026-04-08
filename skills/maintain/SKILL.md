---
name: maintain
description: Pipeline maintenance — deduplicate jobs, cull stale/low-value entries, merge duplicates
---

# Maintain — Pipeline Hygiene

Keep the job pipeline clean by finding duplicates, merging them, and culling stale or low-relevance entries. These operations require judgment — use AI reasoning to decide what's a duplicate and what should be culled, not rigid algorithmic matching.

## Resources

| Resource | Path | Purpose |
|----------|------|---------|
| DB Tool | `tools/db.py` | CRUD operations (list-jobs, update-job, merge-jobs, batch-update) |
| Sync Tool | `tools/sync_contacts.py` | Resync contacts after merges |
| Preferences | `state/preferences.md` | Target roles, companies, deal-breakers |

## Commands

### `/dedupe` — Find and Resolve Duplicate Jobs

Scan the pipeline for duplicate job postings and merge them. Auto-merge clear matches; only ask the user about ambiguous cases.

**Steps:**

1. **Fetch all active jobs:**
   ```
   artemis-db list-jobs --limit 500
   ```

2. **Reason over the full list to identify duplicates.** Group by company and look for:
   - Same role posted from different sources (LinkedIn vs company careers page vs email)
   - Same role with slightly different titles ("Senior PM, AI Platform" vs "Product Manager, AI/ML Platform")
   - Same posting URL with different query parameters
   - Same role reposted after expiry (older + newer version)

3. **For each duplicate group, decide which job to keep.** Prefer the job that:
   - Is further along in the pipeline (applied > to_review > scouted)
   - Has application materials attached
   - Has a higher match score
   - Has richer description or notes
   - Has more contact links

4. **Auto-merge clear matches** (obviously same role, same company, high confidence):
   ```
   artemis-db merge-jobs --keep "<keeper_id>" --merge "<dup_id>"
   ```
   The merge command combines sources, fills empty fields, re-points contacts, transfers applications, and marks the duplicate as deleted.

5. **Surface ambiguous cases** to the user with your reasoning. Ask which to keep or whether they're actually different roles.

6. **Resync contacts** after all merges:
   ```
   artemis-sync
   ```

7. **Report summary:** How many duplicates found, how many auto-merged, how many need user review.

**When triggered from "Flag Duplicate" button with a specific job context:**
- Focus on finding the best match for the flagged job specifically
- Check same-company jobs first, then broaden if no match found
- Merge automatically if a clear match exists, otherwise ask

### `/cull` — Bulk Cull Low-Value and Stale Jobs

Identify and remove jobs that are no longer worth tracking. Use judgment, not just thresholds.

**Steps:**

1. **Fetch all active jobs with full details:**
   ```
   artemis-db list-jobs --limit 500
   ```

2. **Read preferences** to understand target roles, companies, and deal-breakers:
   ```
   Read state/preferences.md
   ```

3. **Reason over the full list to identify cull candidates.** Consider:
   - **Low relevance:** Match score below ~25, especially if the role doesn't align with target preferences
   - **Stale:** Sitting in scouted/to_review for 30+ days with no progress
   - **Both:** Low score AND stale — strongest cull signal
   - **Preserve:** High-score jobs regardless of age, jobs with applications, jobs in active pipeline stages (applied+), jobs at target companies even if score is moderate

4. **Present cull candidates** to the user grouped by reason:
   - "Low relevance" — poor fit, low score
   - "Stale" — old, no progress
   - "Both" — stale and low relevance
   Show job title, company, score, age, and brief reasoning for each.

5. **On user confirmation**, batch-update to `not_interested`:
   ```
   echo '[{"id": "...", "status": "not_interested", "reason": "Culled: <reason>"}]' | artemis-db batch-update
   ```

6. **Report summary:** How many culled by category, how many preserved, current pipeline health.
