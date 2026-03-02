# Coaching State — Alex Jansen
Last updated: 2026-02-26

## Profile
- Target role(s): Senior Product Manager / Group Product Manager / Director of Product (AI-native companies)
- Seniority band: Senior/Lead (8-15 years)
- Track: Full System
- Feedback directness: 3
- Interview timeline: Graham Neubig (Chief Scientist) screen tomorrow (2026-02-27); ongoing search after
- Time-aware coaching mode: Triage for Graham screen → Full system ongoing
- Interview history: Experienced but rusty
- Biggest concern: Storytelling (long-winded, rambling); getting callbacks on blind applications
- Known interview formats: OpenHands Round 1 = product thinking / developer experience / prioritization tradeoffs (principal engineer); Round 2 = Graham Neubig (expect AI/agent technical depth + product POV)

## Resume Analysis
- Positioning strengths:
  1. Rare SWE-to-PM arc (6 years Google engineering before PM) — can speak to engineers as a peer, not a translator
  2. Hands-on AI evals depth — built LLM-as-a-judge harness (100+ scenarios, 50 metrics), not just buzzword AI fluency
  3. Scale + 0-to-1 duality — 1B+ user Google Workspace transformation + 0-to-1 AI roadmap for $70M ARR unit
- Likely interviewer concerns:
  1. Short Google Workspace tenure (10 months) — needs clean, rehearsed narrative
  2. "Sole IC" framing — could read as limited cross-functional influence; needs stories showing influence without authority
  3. B2B/enterprise-heavy recent history — less obvious fit for developer-first / OSS company cultures
- Career narrative gaps:
  - Google → Neat Capital (mortgage lending) transition needs a throughline story for broader search
  - Neat Capital → Google Workspace → Smartsheet arc should feel intentional, not reactive
- Story seeds:
  - LLM-as-a-judge eval harness (strongest AI-native story)
  - $2M+ ARR retention through custom solutioning
  - Google Workspace UI transformation (organizational influence at scale)
  - Neat Capital: $500M → $1B volume without headcount increase
  - People Tagging AI feature (0-to-1 AI product delivery — partially captured)
  - Brandfolder AI roadmap ($1.5M-$5M ARR business cases — not yet captured)
  - File sharing launch decision (incomplete data / product instinct — emerged in debrief)
  - Surface personalized touch input model (HCI research — not yet captured)
  - ContextType context-aware keyboard (HCI research — not yet captured)

## Storybank
| ID | Title | Primary Skill | Earned Secret | Strength | Last Used |
|----|-------|---------------|---------------|----------|-----------|
| S001 | LLM-as-a-Judge Eval Harness | AI Evals / Platform PM | Non-deterministic AI needs a different definition of "done" — deterministic QA thinking breaks generative systems | Substance, Differentiation | 2026-02-26 (drill ×3) |
| S002 | Google Workspace UI Transformation | Org Influence / Vision | The investment thesis IS the product — ship the doc first, then build the coalition | Structure, Credibility | 2026-02-25 (prep) |
| S003 | Neat Capital Volume Doubling | Operational Rigor | Constraint is a design input — the headcount freeze forced the redesign that was right anyway | Substance, Relevance | 2026-02-25 (prep) |
| S004 | $2M ARR Retention / People Tagging | Customer + Competitive Urgency | Feature went from paid differentiator to table stakes while leadership's attention drifted — reframing as churn risk, not growth opportunity, was what got it resourced | Credibility, Relevance | 2026-02-26 (stories session) |
| S005 | File Sharing Launch Decision | Product Instinct / Incomplete Data | When data is thin, a precise use case beats a general argument — the construction management story made the requirement undeniable | Differentiation | 2026-02-26 (debrief drill) |
| S006 | Surface Touch Input / ContextType | Human-Centered AI Origins | Everyone has a different internal model of where keys are — personalization isn't a feature, it's a prerequisite for interfaces that actually fit people | Differentiation | — |

### Story Details
#### S001 — LLM-as-a-Judge Eval Harness
- Situation: Smartsheet building agentic AI features across platform; no standard for measuring whether generative features were actually working
- Task: Build evaluation infrastructure that could give engineering and executive leadership quantifiable confidence in AI feature quality
- Action: Built 3-tiered eval system (manual audits, LLM-as-a-judge, human-in-the-loop); created harness covering 100+ scenarios and 50 metrics; exposed right tools to harness (auth, API connections, data access scopes); used synthetic data injection to control test scenarios; established company standard for launch readiness
- Result: Became shared infrastructure across Smartsheet AI platform; gave teams clear signal for when to ship and when to hold; integrated into CI pipelines
- Earned Secret: Non-deterministic AI requires a fundamentally different definition of "done." Writing unit tests for generative systems breaks — you define pass/fail logic but the system surfaces 5 correct answers when you expected 3. The failure isn't the AI; it's the test. Also: data rots on live platforms, so test stability requires synthetic injection, not just golden datasets.
- Deploy for: AI technical depth, platform PM, eval framework, "tell me about a complex AI system" questions
- Opening line: "At Smartsheet I built the evaluation infrastructure that gave leadership the confidence to ship AI features — a 3-tiered system covering 100+ scenarios that became the company's standard for when agentic features were safe to launch."
- Drilled: Yes — 3 iterations, final version scored Strong Hire

#### S002 — Google Workspace UI Transformation
- Situation: Google Workspace had fragmented UI patterns across the suite; unifying required navigating massive org complexity
- Task: Drive decade-first UI transformation (Material Design 3) across entire suite
- Action: Authored investment thesis; built executive coalition; aligned 50+ person product org on unified vision
- Result: Shipped to 1B+ users; 80%+ positive CSAT far exceeding baseline
- Earned Secret: At Google's scale, the PM's job isn't to have the best idea, it's to build the coalition. The investment thesis — the written doc that makes the business case — IS the real product. Ship that first.
- Deploy for: Cross-functional influence, alignment without authority, big-picture vision, organizational complexity questions
- Opening line: "I drove a decade-first UI transformation across Google Workspace — meaning I had to get executive alignment across a 50+ person product org on a unified vision, not just ship a feature."

#### S003 — Neat Capital Volume Doubling
- Situation: B2B2C loan origination platform needed to scale volume without scaling headcount
- Task: Double funded loan volume while maintaining operational efficiency
- Action: Redesigned core digital mortgage experience; automated strategic compliance workflows; reduced processing time by 50%
- Result: Volume grew $500M → $1B+ annually; 100% YoY increase in funded loan volume; no operational headcount added
- Earned Secret: Constraint is a design input, not just a limitation — the headcount freeze forced the redesign that turned out to be the right product anyway.
- Deploy for: Early-stage execution, doing more with less, prioritization under constraint, operational rigor questions
- Opening line: "I doubled loan volume at a fintech startup — from $500M to $1B annually — without adding a single person to operations, by redesigning the core workflow and automating compliance."

#### S004 — People Tagging / $2M ARR Retention
- Situation: People Tagging (facial recognition for Brandfolder) was first attempted poorly — Alex joined mid-flight, feature had no defined success criteria, 24-hour tagging delay made it unusable. Alex paused the launch. Over an 18-month gap while company priorities shifted, facial recognition went from early differentiator to table stakes competitive requirement. Feature is now a top churn risk and deal-blocker.
- Task: Reset the feature properly, define success criteria upfront, and reframe the business case to get it resourced again
- Action: Halted first launch; documented comprehensive list of gaps with rationale; re-engaged from scratch as sole IC with clear requirements (real-time tagging as core requirement); reframed business case from growth opportunity to churn/deal-loss risk; quantified $2M ARR at stake
- Result: Feature shipped (status: in progress/shipped — confirm at next session); $2M ARR at risk identified and defended
- Earned Secret: A feature's strategic framing has to match the moment. "Paid differentiator" framing won't get resources when the market has moved. Reframing as "we're losing deals without this" unlocked what growth framing couldn't.
- Deploy for: Pausing/killing projects, competitive awareness, reframing business cases, prioritization decisions, shipping under organizational complexity
- Note: $2M figure — confirm whether Alex's own analysis or someone else's (outstanding question from stories session)
- Version history: 2026-02-26 — initial capture; STAR partially complete, needs result confirmation

#### S005 — File Sharing Launch Decision
- Situation: Building file sharing for Smartsheet with no market benchmark — files aren't a standalone product elsewhere, so no external data to anchor decisions
- Task: Decide when the feature was ready to launch and build the case for why it mattered
- Action: Anchored on a single precise use case — construction management, where documents (SOWs, permits, invoices, procurement) drive the entire workflow and each has different stakeholders with different permission needs. Used that story to make permissibility a non-negotiable requirement. Enrolled leadership progressively so launch decision wasn't a surprise.
- Result: Got buy-in; feature launched (metrics TBD — not captured yet)
- Earned Secret: When data is thin, a precise use case beats a general argument. One vivid story that makes the requirement undeniable is worth more than five data points that are directionally interesting.
- Deploy for: Decisions with incomplete information, product instinct, getting buy-in, making the case without data
- Note: Emerged organically in debrief drill — not previously in storybank. Needs full STAR development.
- Version history: 2026-02-26 — initial capture from debrief session

#### S006 — Surface Touch Input / ContextType (HCI Research)
- Situation: Early days of touchscreen mobile — accessibility and personalization were unsolved problems. Two research projects: (1) personalized touch input model on Microsoft Surface for people with motor impairments; (2) ContextType — context-aware keyboard that detected phone grip posture and adjusted layout accordingly
- Task: Prove that touchscreens could be made to fit the person, not the other way around
- Action: Built personalized input model that adapted to individual motor patterns; built posture-detection keyboard that auto-adjusted key sizing based on how the phone was held; published both at ACM
- Result: Proof of concept validated; published; pointed toward a broader insight about personalization in interfaces
- Earned Secret: Everyone has a different internal model of where keys are and how they type. Personalization isn't a premium feature — it's a prerequisite for interfaces that actually work. That insight from 2011 still isn't solved well today.
- Deploy for: Human-centered AI philosophy, long arc of thinking about AI + people, differentiation as a thinker, "what shaped your product philosophy" questions
- Note: Powerful origin story for Alex's AI-human philosophy. Use when interviewers ask about what drives you or where your point of view comes from. Don't lead with it — deploy when asked about background or values.

## Score History
### Historical Summary
None yet.

### Recent Scores
| Date | Type | Context | Sub | Str | Rel | Cred | Diff | Hire Signal | Self-Δ |
|------|------|---------|-----|-----|-----|------|------|-------------|--------|
| 2026-02-26 | practice | Eval harness story v1 (drill) | 4 | 2 | 3 | 4 | 3 | Mixed | over |
| 2026-02-26 | practice | Eval harness story v2 (drill) | 4 | 4 | 4 | 4 | 4 | Strong Hire | accurate |
| 2026-02-26 | practice | Why OpenHands v1 (drill) | 2 | 3 | 2 | 2 | 1 | Mixed | over |
| 2026-02-26 | practice | Why OpenHands v2 (drill) | 3 | 4 | 4 | 4 | 3 | Hire | accurate |
| 2026-02-26 | practice | Production eval off-script v1 | 3 | 3 | 3 | 3 | 2 | Mixed | over |
| 2026-02-26 | practice | Production eval off-script v2 | 5 | 4 | 5 | 5 | 5 | Strong Hire | accurate |
| 2026-02-26 | practice | File sharing / incomplete data (debrief) | 2 | 2 | 3 | 3 | 2 | Mixed | over |

## Outcome Log
| Date | Company | Role | Round | Result | Notes |
|------|---------|------|-------|--------|-------|
| 2026-02-26 | OpenHands | PM (Developer Experience) | Round 1 — Principal Engineer screen | pending | Product thinking / developer experience / prioritization tradeoffs. Alex felt cautiously optimistic. Rambling noted. |
| 2026-02-27 | OpenHands | PM (Developer Experience) | Round 2 — Graham Neubig (Chief Scientist) | pending — cautiously optimistic | Conversational. Strong on KPIs, agentic AI usage, math/AI limits. Tools question shakier. Data fidelity insight buried again. Coach: Hire/Strong Hire. |

## Drill Progression
- Current stage: 1
- Gates passed: []
- Revisit queue:
  - Conciseness / opening-line discipline (persistent — every session)
  - Framework-listing without story anchor (emerged in debrief — deploy one story per question)
  - "The principle I took from it..." closing habit (introduced 2026-02-26 — not yet drilled)

## Interview Loops (active)
### OpenHands
- Status: Interviewing
- Rounds completed: [Round 1 — Principal Engineer, 2026-02-26]
- Round formats:
  - Round 1: Principal engineer screen — product thinking, developer experience, prioritization tradeoffs
  - Round 2: Graham Neubig (Chief Scientist) — expect AI/agent technical depth + product POV
- Stories used: S001 (eval harness — drilled), S004 (People Tagging / pausing project), S005 (file sharing — incomplete data)
- Concerns surfaced: Rambling in live interview confirmed; framework-listing without story anchor observed
- Interviewer intel: Graham Neubig — CMU professor, NLP/agent researcher, built OpenHands Index / SWE-Bench infrastructure. Most technically rigorous of the three cofounders. Will go deep on AI eval, agent architecture, production vs. benchmark gap.
- Prepared questions:
  1. "The OpenHands Index shows model benchmark performance — how do you think about the gap between that and what enterprise customers actually experience in production? PM problem or research problem?"
  2. "You're model-agnostic by design. As you move upmarket, are you seeing pressure toward a more opinionated default stack, or is flexibility a competitive advantage with your buyer?"
  3. "What does the open source community tell you that your enterprise customers don't?"
- Next round: 2026-02-27 — Graham Neubig
- Fit assessment: Strong

## Active Coaching Strategy
Persistent pattern: Alex has strong substance and real earned insights but buries them under long preambles and framework lists. The coaching intervention is structural, not content-based:
1. Open with the point (insight or result), not the context
2. One story per question — anchor hard, don't enumerate frameworks
3. Close every answer with "The principle I took from it..." to surface the earned insight explicitly
4. Stop and let the interviewer pull — they will, especially technical founders

## Meta-Check Log
| Date | Trigger | Check | Outcome |
|------|---------|-------|---------|

## Session Log
| Date | Focus | Key Output | Next Step |
|------|-------|-----------|-----------|
| 2026-02-25 | Kickoff + OpenHands prep | Full company research, 3 story mappings, interview prep doc (.docx) | Practice eval harness story; confirm which cofounder |
| 2026-02-26 | Drills (eval harness ×2, Why OpenHands ×2, off-script ×2) + debrief Round 1 + stories session (partial) | Strong Hire on 3 drilled answers; S004/S005/S006 captured; file sharing debrief drill | Graham screen tomorrow — review scripts tonight; one story per question discipline |
| 2026-02-26 | Broader search: resume repositioning | Full resume rewrite (v2.docx + .md); new headline, summary arc, outcome bullets, consistent formatting | Targeting strategy + LinkedIn next |

## Coaching Notes
- Persistent weakness: long-winded storytelling — framework-listing is the tell that he's searching for the story. Fix: find the story first, then tell it.
- In live interview (Round 1) confirmed rambling even with prep — the habit is deep, needs reps not just awareness
- "The principle I took from it..." closing habit introduced 2026-02-26 — not yet drilled, worth reinforcing
- Strong technical depth; earns credibility fast with technical interviewers when he gets specific
- Genuine motivation for AI-native/frontier companies — comes through naturally, don't over-coach it
- HCI research background (Surface touch, ContextType) is a powerful origin story for his human-centered AI philosophy — use when asked about values or what shaped his thinking
- Stories session was interrupted mid-capture (People Tagging $2M figure sourcing and Brandfolder AI roadmap not yet fully developed)
- Outstanding: confirm People Tagging ship status and whether $2M ARR figure is Alex's own analysis

---
## Resume Work (2026-02-26)
- Full resume repositioned — v2 complete
- New headline: "Technical AI Product Leader · Former Google Engineer"
- Summary rewritten as single coherent arc: HCI researcher → engineer → PM
- Key changes:
  - Eval work and Brandfolder split into separate subheads under Smartsheet
  - Self-initiated framing on eval work added
  - "Sole IC" replaced with actual cross-functional team picture (13 engineers, designer, researcher, PMM)
  - Short tenure context notes added to Google Workspace and Neat Capital
  - All bullets outcome-driven with consistent bold label pattern
  - People Tagging updated to "early access" status
- Outputs: Alex_Jansen_Resume_v2.docx, Alex_Jansen_Resume.md
- Outstanding: targeting strategy and LinkedIn still to do

---
## Accuracy Correction (2026-02-26)
Critical correction made to eval harness story after candidate flagged overstatement:
- What's accurate: designed 3-tiered framework, built and ran 100+ scenarios / 50 metrics, drove cross-team adoption, shipped phase 1 (human SME oversight), made pragmatic call not to wait for LLM-as-a-judge given evolving toolchain
- What was removed: "company standard," "CI pipeline integration" (not shipped), clean success narrative
- What was added: honest metric design lesson (50 metrics = too much noise; lesson is 5-10 core metrics first), toolchain pivot context (Databricks lakehouse), political infighting context
- Updated: resume v2 docx, resume markdown, LinkedIn About, coaching state
- Storybank note: S001 earned secret updated — the honest version (what broke + lessons) is actually MORE differentiated for technical audiences than the clean version
- Key insight for future interviews: lead with what you learned, not just what you built. The metric narrowing lesson is a stronger signal than "we built 50 metrics."

---
## Engineering Background Correction (2026-02-26)
- Google tenure corrected to 7 years (2014-2021), split evenly between Nest and Street View (Maps)
- Street View IS part of Maps — synonymous
- Nest work was equally substantial — three distinct engineering stories now captured:

### New Story Seeds from Nest Engineering
**Works with Nest Platform (codegen):**
- Built protobuf + Jinja2 codegen system that auto-generated fully functional cross-platform interfaces (Android, iOS, web, backend, firmware + all networking layers) from a device capability definition
- Third-party device integrations went from weeks to hours
- Deploy for: 0-to-1 developer platform stories, "tell me about a system you built from scratch," technical depth questions

**Pairing Kit (Android SDK):**
- Built internal Android SDK normalizing device pairing flows across Nest product suite
- Reduced integration effort for device teams, improved UX consistency for users
- Deploy for: platform thinking, developer tooling empathy, internal SDK/API stories

**Nest × Yale Lock (interaction design + engineering):**
- Months of interactive prototyping to refine micro-interactions (open/close animations, failure states)
- Shows design depth + engineering craft combination — rare for a PM
- Deploy for: human-centered design philosophy, prototyping/craft questions

### Street View Accurate Summary
- Rearchitected Street View mobile + web app (flat imagery support across Android, iOS, web)
- Modernized coverage map rendering
- Built hardware lab + GPS antenna rig on Boulder office roof (bespoke hardware, electrical engineering coordination)
- Built Android routing app for SV drivers with automatic route correction
- Coordinated with ML teams as new imagery sources fed into their pipelines

All resume and LinkedIn files updated to reflect accurate Nest/Street View split.

---
## Voice & Positioning Update (2026-02-26)
Candidate articulated authentic voice in their own words:
"I'm a builder and a tinkerer. I care about building things that enrich people's lives. I'm not the PM who writes the most detailed spec — I'm the one peering beyond the horizon."

All documents updated to reflect this voice:
- Resume summary rewritten — same energy as LinkedIn About, sounds like a person not a positioning doc
- LinkedIn About rewritten in candidate's own words
- Coaching note: this framing is also the answer to "tell me about yourself" and "what kind of PM are you" — it's authentic, specific, and differentiating. Reinforce in future sessions.

Answer to Q5 from kickoff ("what do you want to be remembered for"):
Not "revolutionizing AI" — that's generic. The real answer: a PM who genuinely cared about the people using the thing, who chased what's next rather than optimizing what exists, and who built things that made people's lives better. That's the through-line from HCI research to Nest to Brandfolder AI.

---
## Content & LinkedIn Session (2026-02-26)

### Substack Post — Published
- Title: "We tried to evaluate our AI. Here's what broke."
- Published on: The Technical PM Lab (thetechnicalpmlab.substack.com)
- Key themes: unit test problem, 50-metrics trap, data harder than metrics, test rot, walk first
- Smartsheet removed — generalized to "our team" and "enterprise tools"
- File: Substack_Post_Draft.md

### LinkedIn Post — Ready to publish
- Copy: "I spent the last quarter building AI evaluation infrastructure from scratch. Here's the honest version of what we got wrong — and what actually worked. Most eval framework posts describe the destination. This one is about the journey: the unit test problem, the 50-metrics trap, and the thing nobody talks about — the data was harder than the metrics. Full post here: [Substack link]"
- Decision: post with link in body (option 2) — small network, reach penalty acceptable
- Note: "link in first comment" trick is dead as of 2026 — LinkedIn penalizes it too

### Targeting Strategy — Documented
Tier 1 (apply now):
- Anthropic — open PM role posted 2026-02-25; strong fit on eval + HCI mission alignment
- OpenHands — already in play (Round 2 with Graham tomorrow)
- Cursor (Anysphere) — $29B valuation, moving into enterprise, devex PM fit
- Cognition (Devin) — natural adjacent if OpenHands doesn't close

Tier 2 (worth pursuing):
- Replit, Linear, Notion, Cohere

Tier 3 (watch):
- Sierra, Braintrust/Arize/W&B

### All Outputs This Session
- Alex_Jansen_Resume_v2.docx ✓
- Alex_Jansen_Resume.md ✓
- LinkedIn_Profile.md ✓ (headline, About in authentic voice, featured section guidance)
- Substack_Post_Draft.md ✓ (published)
- coaching_state.md ✓
- OpenHands_Interview_Prep.docx ✓ (from earlier session)

---
## LinkedIn Experience Blurbs (2026-02-26)

All blurbs written in conversational voice matching the About section. Dates TBD where noted — Alex to fill in.

### Senior Product Manager · Smartsheet (Brandfolder) · May 2023 – Present
I was running two jobs at once here, and I'll be honest about that. On one side: PM lead for Brandfolder, a $70M ARR digital asset management platform — owning the roadmap, the team, and the business. On the other: I saw that Smartsheet had no real way to evaluate whether its agentic AI features were actually working, so I built the infrastructure to answer that question. Nobody asked me to. The problem needed solving.

For Brandfolder, I drove the AI roadmap — People Tagging, Semantic Search, automated taxonomy tools — and spent a lot of time on the unglamorous stuff too: security hardening, WCAG compliance, transitioning the engineering team offshore while keeping delivery on track. I also had to fight to get features resourced when the competitive window was closing faster than leadership realized.

For the eval work: I designed a 3-tiered framework (human expert review → LLM-as-a-judge → human-in-the-loop), got cross-team adoption across all of Smartsheet's agentic AI teams, and made the call to ship phase one before the perfect system existed. We learned more from that decision than we would have from six more months of design.

### Product Manager · Google Workspace · May 2022 – March 2023
I came back to Google as a PM after six years as an engineer — went through a full interview loop to do it, which felt like the right way to make the transition real. I joined the Workspace team and immediately got handed something genuinely hard: a decade-first UI transformation across the entire suite, for over a billion users.

The product challenge was interesting. The organizational challenge was harder. Getting a 50+ person product org aligned on a unified vision — and keeping it aligned through the actual build — required as much coalition-building as product thinking. The investment thesis I wrote to make the case for it was, in a lot of ways, the most important artifact I produced. The transformation shipped, CSAT came in well above our baseline targets, and some of the AI collaboration strategies I pushed for early on are now table stakes across the suite.

The role ended in Google's first large-scale layoff. I was the sole remote employee on the team, based in Colorado. I've made my peace with it.

### Product Manager · Neat Capital · February 2021 – May 2022
First non-founding PM hire at a venture-backed mortgage fintech. I joined to build — and that's what we did. The goal was to scale loan volume without scaling the operational headcount to match it, which meant the product had to do the heavy lifting.

We redesigned the core digital mortgage experience from the ground up and automated the compliance workflows that were eating the most time. Loan volume went from $500M to over $1B annually. Processing time dropped by 50%. The team stayed the same size. When the funding runway ended and the company wound down, I was proud of what we'd shipped.

### Software Engineer / UX Engineer · Google — Nest & Street View · October 2014 – January 2021
Seven years of building things. Split roughly evenly between Nest and Street View, which is part of the Maps team.

At Nest, I built the Works with Nest platform — a codegen system that let third parties describe their device's capabilities in a protobuf and automatically generate fully functional interfaces across Android, iOS, web, backend, and firmware, including all the networking layers. What used to take weeks took hours. I also built Pairing Kit, an internal Android SDK that normalized device pairing flows across the whole Nest product suite. And I spent months prototyping micro-interactions for the Nest × Yale Lock — obsessing over things like open/close animations and failure states — before we shipped the mobile experience on Android and iOS.

At Street View, I rearchitected the mobile and web app, adding flat imagery support across platforms and modernizing how we rendered coverage maps. I built a hardware lab in our Boulder office — including a benchtop version of the Street View car and a bespoke GPS antenna installation on the building roof, which involved more electrical engineering coordination than I expected. I also built the Android routing app for our Street View drivers, with automatic route correction when someone deviated from their plan.

This is where I learned what it actually means to build. I'm a better PM because I spent this time as an engineer.

### Research Intern · Samsung Research America · [Dates TBD]
In 2013, before anyone was talking about model hubs or dataset marketplaces, I was prototyping one. The project was an ML toolkit marketplace for mobile — a place where developers could browse and curate datasets built from different sensor configurations, and access custom models trained on those datasets. Think of it as an early, pre-LLM sketch of what Hugging Face would eventually become.

It was a research prototype, not a shipped product. But the core idea — that the ecosystem around models matters as much as the models themselves, and that making it easy to find and use the right data is half the battle — has aged pretty well.

### Research Assistant · University of Washington iSchool · [Dates TBD]
Spent my graduate years running HCI research in the lab — designing studies, building prototypes, and publishing findings. The work focused on input modeling, accessibility, and how people physically interact with technology: pointing errors, motor impairments, touch interfaces, context-aware keyboards. Six ACM publications came out of this period, including full papers at CHI and UIST.

The throughline across all of it: I was obsessed with the gap between how interfaces assume people will interact with them and how people actually do. That obsession is still what drives me.

### Pre-Doctoral Lecturer · University of Washington iSchool · [Dates TBD]
Designed and taught a graduate-level course called "Design Methods for Inputs and Interactions" — a foundational HCI primer for incoming master's students. Covered the core methods: user research, prototyping, interaction modeling, evaluation frameworks.

One of my students told me that class set them on the path to becoming a PM. They're now my peer at my current company. I still think about that more than most things I've shipped.

### Creative Manager · The Daily (UW Student Newspaper) · [Dates TBD]
Managed a team of 5-6 designers responsible for all advertising graphics in a daily print publication with over $1M in annual ad revenue. The job was part creative direction, part production management, part on-call firefighter — I was reachable after midnight on print nights to resolve last-minute color issues or incompatible files before the paper went to press.

The thing I'm most proud of: I built an automated workflow that pulled ad orders directly from Salesforce into InDesign templates, eliminating a manual process that was taking 3-4 hours every day. Nobody asked me to build it. It just seemed like an obviously broken thing that could be fixed. That instinct hasn't changed much.

## Outstanding (LinkedIn)
- Fill in dates for Samsung Research, UW Research Assistant, Pre-Doctoral Lecturer, The Daily
- Add Substack link to featured section
- Pin portfolio to featured section
- Remove 3-year-old Google Workspace reshare

---
## Round 2 Debrief — Graham Neubig (Chief Scientist, OpenHands) · 2026-02-27

### Outcome
- Gut feel: Cautiously optimistic
- Coach assessment: Hire / Strong Hire
- Status: Pending decision

### Format
- 30 minutes, conversational — less technically rigorous than expected
- Topics: User feedback / KPIs, AI eval depth, agentic AI in day-to-day, where AI fails

### Question-by-Question Breakdown

**Q1: How do you track user feedback / measure KPIs?**
- Alex's answer: Hero metrics over broad measurement; DAU + hero feature engagement as core signals; lightweight in-product feedback (thumbs up/down); correction rates as a signal (People Tagging — how often users had to override the system); qualitative customer conversations as the richest signal
- What landed: Hero metrics framing echoed eval insight — narrow focus, consistent worldview coming through
- Coach note: Strong answer, consistent philosophical thread across the interview

**Q2: How did you approach AI evals?**
- Alex's answer: 3-tiered approach; started with LLM-as-a-judge, walked it back to human SME oversight out of necessity; touched on data fidelity challenge; framed Smartsheet as a learning organization, not an expert one — enterprise customers are all on this journey; lesson is start small, be humble
- What landed: "Walk before you run" framing, honest about organizational maturity
- What didn't land: Data fidelity insight (test rot, representativeness question) was mentioned but not driven home — got buried. This was the most original insight and deserved more airtime.
- Coach note: The answer that would have fully landed — connect tools to the deeper data problem: "The hard part wasn't the tooling — it was the data. What do you evaluate against? Real customer data is messy but representative. Synthetic fixtures rot over time — dates are the obvious culprit in a workflow tool. SME review was partly our answer to that tension."

**Q3: Tools deep-dive (Graham pushed)**
- Alex's answer: Promptfoo as harness; second model as LLM-as-a-judge evaluating against rubric criteria; CI/CD integration
- What happened: Felt uncertain about what Graham was looking for; probed back; dug into technical details
- Coach note: Answer was more solid than Alex gave himself credit for — real mechanics, real tooling. Uncertainty came from not knowing what Graham was fishing for, not from lack of substance. Gap: didn't connect tooling choices to the WHY (the data tension, the tradeoffs). That's the jump from "we used Promptfoo" to "here's what we were actually navigating."

**Q4: How are you using agentic AI in your day-to-day?**
- Alex's answer: Led with Claude as career coaching skill (this conversation) — described how a skill provides guardrails and process structure around an unbounded tool; Lovable prototype for Brandfolder semantic search (got engineering + leadership buy-in); AI for rapid prototyping
- What landed: Bold move that paid off — specific, current, real example. Talking to the Chief Scientist of an AI agent company about using AI agents daily, with a concrete story. Most candidates give generic answers.
- Coach note: Strong Hire moment. The Lovable prototype story shows AI as a product thinking tool, not just a writing assistant.

**Q5: Where does AI do a bad job? Where don't you use it?**
- Alex's answer: Math / functional reasoning — "like a middle schooler, they might know the function but the output isn't reliable." Followed up: still uses AI to build queries and write scripts to get the numbers efficiently — AI is still in the process, just not trusted for the final calculation.
- What landed: Memorable analogy, practitioner nuance on the follow-up
- Coach note: Sharp answer. The pivot — "I still use it, just not for the final math" — showed sophistication.

### Patterns Observed
- Rambling still present but less severe than Round 1 — focus on outcomes helped
- Tools question: uncertainty about what interviewer wanted caused hesitation — not lack of substance
- Data fidelity insight (strongest original observation) continues to get buried — needs to be a lead, not a footnote
- Consistent philosophical thread emerging across answers (narrow focus, walk before run, be humble) — this is good, reinforce it

### Stories Used
- S001 (eval harness) — deployed, partially effective
- S004 (People Tagging correction rate) — deployed as signal example, good
- New: Claude career coaching skill — strong, unscripted moment
- New: Lovable semantic search prototype — strong, shows AI-native PM instincts

### Next Steps
- Await Round 3 decision
- If advancing: research remaining interviewers, prep new stories
- If rejected: debrief and apply lessons to Anthropic / Cursor outreach
