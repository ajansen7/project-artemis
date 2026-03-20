---
name: artemis-setup
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

---

## Commands

### `/kickoff` or `/setup` — Run Initial Setup

Walk the user through building their candidate profile and search configuration.

---

### Step 0: Submodule Check

Before anything else, check whether the interview-coach submodule is initialized:

```bash
git submodule status .claude/skills/interview-coach
```

- If the output starts with `-`: the submodule has **not** been cloned.
- If it starts with `+` or a commit hash: it's already initialized — skip to Step 1.

**If not cloned**, tell the user:

> "The interview-coach submodule isn't set up yet. It handles storybank building, mock interviews, and coaching — and its kickoff is actually a great way to extract the background info we need here too. Want me to clone it? It's a quick git operation."

- If yes: `git submodule update --init .claude/skills/interview-coach`
- If no: proceed without it. Note that `/coach` and `/prep` commands will be unavailable.

---

### Step 1: Orientation — Goals & Context

**Do this conversationally, not as a form.** Ask 3–4 questions in a single message to understand where the user is:

1. Where are they in the search? (Just starting, actively interviewing, passively exploring, in late-stage loops?)
2. What kind of roles are they targeting? (Title, level, function — broadly)
3. What's their timeline? (Urgent, a few months, no rush)
4. What's their biggest concern or thing they most want help with? (Finding jobs, writing materials, interview prep, networking — or something else)

Use the answers to calibrate the rest of the session. Don't ask unnecessary questions if the answers are clear from context.

**Interview history — ask only if relevant to their timeline/concerns:**

- Have they been interviewing for this type of role? How has it been going?
- This shapes coaching:
  - **First-time / just starting**: Needs orientation. Storybank and positioning are the priority.
  - **Active but not advancing**: Needs diagnosis. Ask where they're getting stuck (first rounds, finals, no callbacks). Tailor accordingly.
  - **Experienced but rusty**: Needs refreshing, not rebuilding. Recent experience into stories, sharpen differentiation.

---

### Step 2: Interview-Coach Kickoff Offer

If the interview-coach submodule is present, offer this before diving into Artemis's form-building:

> "The interview coach has its own kickoff — it does a deep extraction: resume analysis, story seeds, positioning strengths, likely interviewer concerns, and initializes your storybank. That content is also the foundation for your Artemis profile.
>
> Want to run that first? I can pull everything I learn there directly into the Artemis setup. Or if you'd rather knock out the Artemis basics now and do the coach kickoff later, that works too."

**If they choose interview-coach first:**
- Invoke the interview-coach kickoff flow (see `.claude/skills/interview-coach/references/commands/kickoff.md`)
- After it completes, use `coaching_state.md` as the source for identity, positioning, and resume information — don't re-ask what's already been captured
- Jump to Step 4 (skipping the resume re-capture in Step 3, since the coach already analyzed it)

**If they decline or prefer to do Artemis first:**
- Continue through Steps 3–5 as written
- At the end (Step 6), offer to run the interview-coach kickoff

---

### Step 3: Check Existing State

For each file in the **What This Skill Creates** table, check if it already exists (excluding `.example.md` files). Report what's already set up and what's missing.

If most files exist (re-run scenario), ask: "Looks like you're mostly set up. Do you want to update a specific file, or rebuild everything from scratch?"

---

### Step 4: Build the Candidate Files

Work through each missing file. Be conversational — group related questions naturally. Skip optional fields gracefully.

#### `identity.md` (required first)

If `coaching_state.md` exists from the interview-coach, pull from it:
- Name, current role/company, target roles, seniority, location preferences
- Positioning headline and career arc narrative
- Key differentiator

Otherwise ask:
- Name, current role/company, target roles, seniority, location preferences
- Positioning headline: the one-line thing that's true and differentiated about you
- Career arc: the narrative someone would use to explain your trajectory
- Key differentiator: the thing that's hard to find in other candidates

Write to `.claude/memory/hot/identity.md` using the format from `identity.example.md`.

#### `voice.md` (optional — offer defaults)

Show the default voice rules from `voice.example.md`. Ask if they want to customize or use defaults.

Write to `.claude/memory/hot/voice.md`.

#### `preferences.md` (required for `/scout`)

Ask:
- Target roles (list)
- Target industries
- Location preferences, remote/hybrid flexibility
- Deal-breakers (company size, industry, comp floor, travel, etc.)
- Target companies by tier: Tier 1 (apply now), Tier 2 (worth pursuing), Tier 3 (watch)
- Compensation expectations (optional)

Generate search keywords from the above.

Write to `.claude/skills/hunt/references/preferences.md`.

#### `form_defaults.md` (required for `/generate`)

Ask:
- Contact info: email, phone, LinkedIn, portfolio, GitHub
- Work authorization, location for forms, pronouns
- Years of experience, management experience
- Compensation preferences for forms
- Demographics (optional, for voluntary fields)

Write to `.claude/skills/apply/references/form_defaults.md`.

#### `resume_master.md` (required for `/generate`)

**If `coaching_state.md` already has a resume analysis from the interview-coach kickoff**, use that as the source — parse it into `resume_master.md` format. Ask the user to confirm the structured version before saving.

**Otherwise:**
- Ask the user to provide their resume (paste text, provide a file path, or provide a URL)
- Parse and structure into the expected format with tagged bullets
- Do a coaching-quality resume analysis while you're at it (this doubles as useful context):
  1. **Positioning strengths**: What hiring managers see in 30 seconds
  2. **Likely concerns**: Gaps, short tenures, domain switches, seniority mismatches
  3. **Story seeds**: Bullets that likely have rich stories behind them — flag these
  4. **Career narrative gaps**: Transitions that need a story ready
- Ask the user to review and approve the structured version before writing

Write to `.claude/skills/apply/references/resume_master.md`.

**Storybank → resume_master feedback loop**: If the interview-coach's storybank captures new anecdotes from past roles (via the coach's `stories` or `kickoff` commands), those stories can surface new or better resume bullets. When this happens, surface it: "The story you told about [X] suggests a stronger framing for this bullet — want to update resume_master.md?"

#### `active_loops.md` and `lessons.md`

Copy from `.example.md` templates — no user input needed.

---

### Step 5: Verify Connections

**Supabase:**
```bash
uv run python .claude/tools/db.py status
```

If this fails, remind the user to set up `.env` with Supabase credentials per the README. Non-blocking — continue.

**Gmail/Calendar MCP (optional):**
Check if Gmail MCP tools are available by attempting `gmail_get_profile`. If available, mention:
> "Gmail and Calendar are connected. You can use `/inbox` to monitor for recruiter emails and `/schedule` to track upcoming interviews."

If not available, mention:
> "Gmail/Calendar MCP tools aren't set up yet. When you add them, the `/inbox` and `/schedule` commands will let you monitor for recruiter outreach and track interviews automatically."

**Chrome MCP (optional):**
Check if Chrome MCP tools are available. If available, mention:
> "Chrome is connected. You can use `/linkedin-scout` to browse LinkedIn for jobs and `/linkedin-engage` to build your professional presence."

If not available, mention:
> "Chrome MCP isn't set up yet. When you add it, you'll be able to browse LinkedIn for jobs and engagement directly from Artemis."

---

### Step 6: Build Candidate Context (if interview-coach is present)

If `coaching_state.md` exists, run the profile skill's `/context` flow to build `candidate_context.md`. This synthesizes coach state + preferences into the cached profile that hunt/apply/connect use.

If not, tell the user: "You can run `/context` later once you've done the interview-coach kickoff — it'll significantly enrich your candidate context."

---

### Step 7: Interview-Coach Kickoff Bridge (if not already done)

If the interview-coach kickoff wasn't run at the start of this session, and the submodule is present, offer it now:

> "One more thing worth doing: the interview coach's kickoff. It builds your storybank, does a deeper resume analysis, and initializes coaching state — all of which feeds back into how Artemis writes your cover letters, scores jobs, and preps you for interviews. It takes about 10–15 minutes but is probably the highest-leverage setup step. Want to kick that off now?"

If yes, invoke the interview-coach kickoff. The stories and storybank it builds can later be surfaced as resume bullet improvements via the storybank → resume_master feedback loop described in Step 4.

---

### Step 8: Summary & Next Steps

Report:
- All files created with their paths
- Any files still missing and what skill they block
- Whether interview-coach is set up and what that unlocks

Suggested next steps, based on their orientation from Step 1:
- **Urgent search / active interviewing**: "Try `/prep [company]` to get ready for your next interview, or `/scout` to find more opportunities."
- **Building pipeline**: "Try `/scout` to find jobs, then `/review` to triage what comes in. Or `/inbox` to scan for recruiter emails already in your inbox."
- **Just exploring**: "Try `/scout` to see what's out there, or `/coach kickoff` to build your storybank."
- **Building brand**: "Try `/blog-ideas` to generate content ideas that align with your positioning, or `/linkedin-engage` to start engaging with relevant posts."
- **Full campaign**: "Start with `/inbox` + `/schedule` for a current-state check, then `/scout` for new opportunities, and `/blog-ideas` to build thought leadership."

---

## Important Notes

- Be conversational, not interrogative. Don't fire questions like a form. Group them naturally.
- Offer to skip optional fields. Never block on demographics or compensation.
- If the user ran the interview-coach kickoff first, don't re-ask what's already been captured.
- For the resume, always ask the user to confirm the structured output before saving — bullets must be human-approved.
- If the user already has most files set up (re-run scenario), target only what's missing or outdated.
- The interview-coach and Artemis are complementary, not redundant. The coach goes deep on stories and coaching; Artemis goes wide on pipeline, applications, and networking. Setting up both is the full system.
