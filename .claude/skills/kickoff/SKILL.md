---
name: kickoff
description: One-time setup wizard for new Artemis users — builds hot memory, search preferences, resume master, and form defaults from user input
---

# Kickoff — Initial Setup Skill

You guide new users through building the personal artifacts that Artemis needs to function. This is a one-time setup flow (though users can re-run it to update specific files).

## What This Skill Creates

| File | Location | Purpose |
|------|----------|---------|
| `identity.md` | `.claude/memory/hot/` | Candidate name, role, targets, positioning |
| `voice.md` | `.claude/memory/hot/` | Tone rules for communications |
| `active_loops.md` | `.claude/memory/hot/` | Current interview loops (starts empty) |
| `lessons.md` | `.claude/memory/hot/` | Operational best practices (starts with defaults) |
| `preferences.md` | `.claude/skills/hunt/references/` | Target roles, companies, industries, deal-breakers |
| `resume_master.md` | `.claude/skills/apply/references/` | Verified resume bullets (source of truth) |
| `form_defaults.md` | `.claude/skills/apply/references/` | Standard application form answers |

## Commands

### `/setup` — Run Initial Setup

Walk the user through building their candidate profile and search configuration.

**Steps:**

1. **Check existing state.** For each file above, check if it already exists. Report what's already set up and what's missing.

2. **For each missing file, guide the user through creating it:**

   **identity.md** (required first):
   - Ask: name, current role/company, target roles, seniority level, location preferences, search status
   - Ask: positioning headline and career arc narrative
   - Ask: key differentiator (what makes them uniquely qualified)
   - Write to `.claude/memory/hot/identity.md` using the format from `identity.example.md`

   **voice.md** (optional — offer defaults):
   - Show the default voice rules from `voice.example.md`
   - Ask if they want to customize or use defaults
   - If customizing, ask about specific tone preferences
   - Write to `.claude/memory/hot/voice.md`

   **preferences.md** (required for /scout):
   - Ask: target roles (list), target industries, location preferences, deal-breakers
   - Ask: target companies by tier (Tier 1 = apply now, Tier 2 = worth pursuing, Tier 3 = watch)
   - Ask: compensation expectations (optional)
   - Generate search keywords from the above
   - Write to `.claude/skills/hunt/references/preferences.md`

   **form_defaults.md** (required for /generate):
   - Ask: contact info (email, phone, LinkedIn, portfolio, GitHub)
   - Ask: work authorization, location for forms, pronouns
   - Ask: years of experience, management experience
   - Ask: compensation preferences for forms
   - Ask: demographics (optional, for voluntary fields)
   - Write to `.claude/skills/apply/references/form_defaults.md`

   **resume_master.md** (required for /generate):
   - Ask the user to provide their resume (paste text, provide a file path, or provide a URL)
   - Parse and structure into the expected format with tagged bullets
   - Ask the user to review and approve the structured version
   - Write to `.claude/skills/apply/references/resume_master.md`

   **active_loops.md** and **lessons.md**:
   - Copy from `.example.md` templates (active_loops starts empty, lessons starts with defaults)
   - No user input needed

3. **Verify Supabase connection:**
   ```bash
   uv run python .claude/tools/db.py status
   ```
   If this fails, remind the user to set up `.env` with Supabase credentials per the README.

4. **Build candidate context:**
   - If the interview-coach submodule has a `coaching_state.md`, run the profile skill's `/context` flow to build `candidate_context.md`
   - Otherwise, tell the user they can run `/context` later once they've set up the interview-coach

5. **Report summary:**
   - List all files created with their paths
   - List any files still missing and what skill they block
   - Suggest next steps: "Try `/scout` to find jobs, or `/review` to see your pipeline."

**Important:**
- Be conversational, not interrogative. Group related questions naturally.
- Offer to skip optional fields. Don't block on demographics or compensation.
- If the user provides a resume file, read it and structure it rather than asking them to manually format it.
- For the resume, always ask the user to confirm the structured output before saving — bullets must be human-approved.
