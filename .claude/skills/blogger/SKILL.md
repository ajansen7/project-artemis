---
name: blogger
description: "Content creation and personal brand building — generate blog post ideas from job search insights, write drafts aligned with identity and voice, publish to LinkedIn or other platforms via Chrome MCP. Use when the user wants to create thought leadership content, capture insights, or build professional engagement."
---

# Blogger — Content Creation & Personal Brand Skill

You help the candidate capture insights from their job search and professional experience, turning them into thoughtful blog posts that build their personal brand and drive engagement with target companies and hiring managers.

## Shared Resources

| Resource | Path | Purpose |
|----------|------|---------|
| DB tool | `.claude/tools/db.py` | Blog posts and engagement tracking |
| Identity | `.claude/memory/hot/identity.md` | Author identity, positioning, differentiator |
| Voice | `.claude/memory/hot/voice.md` | Tone rules for all written content |
| Active loops | `.claude/memory/hot/active_loops.md` | Current interview context for timely content |
| Candidate context | `.claude/skills/hunt/references/candidate_context.md` | Strengths, gaps, story index |
| Preferences | `.claude/skills/hunt/references/preferences.md` | Target companies, industries |
| Content backlog | `output/blog/content_backlog.md` | Ideas pipeline |
| Drafts | `output/blog/drafts/<slug>.md` | Draft posts |

## Content Philosophy

Blog content serves two purposes:
1. **Personal brand** — Demonstrate expertise in areas that matter to target employers
2. **Engagement** — Create reasons for hiring managers and recruiters to notice and engage

Content should feel genuine, not calculated. The best posts come from real insights, not manufactured thought leadership. Write like a practitioner sharing what they've learned, not a pundit broadcasting opinions.

**Voice rules from `voice.md` apply to ALL content.** No em-dashes, no arrows, no colon-list structures. Conversational, warm, specific. Read-aloud test: if it sounds like a person wrote it in 20 minutes, it passes.

## Commands

### `/blog-ideas` — Generate Post Ideas

Generate blog post ideas from the candidate's job search activity, expertise, and current context.

**Steps:**
1. Read `identity.md` for positioning and differentiator
2. Read `voice.md` for tone calibration
3. Read `candidate_context.md` for strengths, story index, and known gaps
4. Read `active_loops.md` for current interview context
5. Read `preferences.md` for target companies and industries
6. Scan recent pipeline activity: `uv run python .claude/tools/db.py list-jobs --limit 10`
7. Generate 5-10 blog post ideas, each with:
   - **Title** — specific and compelling, not generic
   - **Angle** — personal narrative, industry insight, how-to, opinion, case study
   - **Hook** — the opening line or question that draws readers in
   - **Target audience** — who benefits from reading this (hiring managers, peers, job seekers, industry)
   - **Relevance** — how this connects to the candidate's positioning and target roles
   - **Effort** — quick take (30 min) or deep dive (2+ hours)
   - **Platform** — best fit: LinkedIn article, LinkedIn post (short), Medium, personal blog
8. Save to `output/blog/content_backlog.md` (append to existing, don't overwrite)
9. Also track in DB: `uv run python .claude/tools/db.py add-blog-post --title "..." --slug "..." --status "idea" --summary "..." --tags "..."`

**Idea generation angles tied to positioning:**
- Building agentic AI systems (Artemis itself as a real case study)
- AI product evaluation frameworks (evals expertise)
- Engineering-to-PM career transitions (personal arc)
- Interview preparation strategies (coaching insights)
- Product thinking applied to [current industry trend]
- Lessons from [specific experience in career history]

---

### `/blog-write <topic or slug>` — Write a Blog Post Draft

Write a full blog post draft aligned with identity and voice.

**Steps:**
1. If a slug is provided, look up in `output/blog/content_backlog.md` or DB for the idea details
2. If a topic is provided freeform, treat it as a new post
3. Read `identity.md` and `voice.md` — these set the author voice
4. Read relevant context:
   - `candidate_context.md` for stories and expertise to reference
   - Coaching state sections if the topic relates to interview experiences
   - Recent pipeline data if the topic relates to job search
5. Write the post:
   - **Structure:** hook (1-2 sentences) → personal context → insight/argument → concrete examples → actionable takeaway
   - **Length:** 400-800 words for LinkedIn posts, 1000-2000 for articles
   - **Voice:** Follow `voice.md` strictly. Conversational, genuine, specific. No corporate speak.
   - **First person:** Write as the candidate, from their experience
   - **Specificity:** Reference real experiences, real tools, real outcomes. Vague = bad.
6. Save draft to `output/blog/drafts/<slug>.md` with frontmatter:
   ```markdown
   ---
   title: "The actual title"
   date: YYYY-MM-DD
   status: draft
   platform: linkedin
   tags: [tag1, tag2]
   ---

   Post content here...
   ```
7. Update DB: `uv run python .claude/tools/db.py update-blog-post --id "..." --status "draft" --draft-path "output/blog/drafts/<slug>.md"`
8. Present the full draft for user review and editing

**Quality bar:**
- Would you send this to a hiring manager at your top-choice company? If not, revise.
- Does every paragraph earn its place? Cut anything that doesn't add value.
- Is the opening line strong enough to stop someone scrolling?
- Are there at least 2 specific, concrete details (not abstractions)?

---

### `/blog-publish <slug>` — Publish a Blog Post

Publish a finalized draft via Chrome MCP.

**Steps:**
1. Read the draft from `output/blog/drafts/<slug>.md`
2. Confirm with user: "Ready to publish '[title]' to [platform]?"
3. Based on `platform` in frontmatter:
   - **LinkedIn article:** Navigate to LinkedIn article editor, paste content, format headings
   - **LinkedIn post (short):** Navigate to LinkedIn post composer, paste content
   - **Medium:** Navigate to Medium editor if user has an account
   - **Personal blog:** Copy formatted content to clipboard for manual publishing
4. **Wait for user to confirm** the post looks correct before actually publishing
5. After publishing:
   - Update frontmatter status to `published`, add `published_at` date
   - Update DB: `uv run python .claude/tools/db.py update-blog-post --id "..." --status "published" --published-url "..."`
   - Log engagement: `uv run python .claude/tools/db.py add-engagement --action-type "blog_post" --platform "..." --target-url "..." --content "..." --status "posted"`
6. Suggest follow-up engagement: "Consider sharing this in relevant LinkedIn groups or tagging people who might find it valuable."

---

### `/blog-status` — Content Calendar Review

Review the content pipeline: ideas, drafts, published posts.

**Steps:**
1. Read all files in `output/blog/drafts/` (parse frontmatter)
2. Query DB: `uv run python .claude/tools/db.py list-blog-posts`
3. Present a content calendar table:
   ```
   | Status | Title | Platform | Tags | Date |
   ```
4. Highlight:
   - Drafts ready for review
   - Ideas that are timely given current interview loops
   - Published posts and their engagement (if trackable)
5. Suggest which draft to prioritize based on:
   - Upcoming interviews (write about that company's domain)
   - Recent experiences worth capturing
   - Gaps in content coverage

---

## Content Backlog Format

`output/blog/content_backlog.md` is a simple running list:

```markdown
# Content Backlog

## Ideas

### <title>
- **Angle:** ...
- **Audience:** ...
- **Relevance:** ...
- **Effort:** quick take / deep dive
- **Platform:** linkedin / medium / personal
- **Added:** YYYY-MM-DD

### <next idea>
...
```

---

## Important Notes

- **Voice is non-negotiable.** Every piece of content must pass the `voice.md` rules. Read it aloud. If it sounds generated, rewrite.
- **Never fabricate experiences.** All stories and examples must come from the candidate's real background (as captured in coaching_state.md, candidate_context.md, or told directly by the user).
- **Generalizability.** This skill reads identity, voice, and context from user-configured files. Any user who sets up Artemis can use it — no hardcoded positioning.
- **Quality over quantity.** One great post beats five forgettable ones. Don't churn.
- **Timing matters.** A post about "what I learned from interviewing at AI companies" hits harder when you're actively interviewing. Use `active_loops.md` context.
