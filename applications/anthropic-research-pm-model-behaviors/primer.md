# Application Primer: Anthropic — Research PM, Model Behaviors

**Role:** Research Product Manager, Model Behaviors
**URL:** https://job-boards.greenhouse.io/anthropic/jobs/5097067008
**Comp:** $305,000–$385,000 USD | SF or NYC | 25% min in-office
**Match Score:** 85/100
**Status:** Active as of 2026-03-14

---

## Company Overview

Anthropic is an AI safety company. Its stated mission is responsible development and maintenance of advanced AI for the long-term benefit of humanity. Key context:

- **Product:** Claude (consumer + API + enterprise). Claude.ai is the consumer surface; API + Claude for Work are B2B.
- **Research emphasis:** Constitutional AI, RLHF, alignment research, interpretability. The company is serious about safety — it's not a marketing layer.
- **Culture signals:** Mission-first, high-bar intellectual culture. Hiring skews toward people with research credentials or hands-on AI systems experience. Generic "AI PM" candidates don't pass here — depth required.
- **This team's position:** The Model Behaviors team sits at the intersection of research and product — responsible for how the model behaves by default and under steering. This is the alignment-product bridge.

---

## Role Fit Summary

| JD Requirement | Alex's Signal | Strength |
|---|---|---|
| 5+ years leading conversational AI products | Smartsheet agentic AI (3 yrs), Brandfolder AI roadmap, Anthropic Claude in stack | Strong |
| Alignment evaluation frameworks | Built LLM-as-a-judge harness, 3-tiered eval framework, 100+ behavioral scenarios | Directly On-Point |
| Behavioral defaults / steerability | Closest analog: metric design + pass/fail framework design for non-deterministic AI | Moderate (analytical fit, not exact experience) |
| Taxonomies of model behaviors | Closest analog: 50-metric taxonomy design, synthetic test injection, golden dataset architecture | Adjacent |
| ML fundamentals | 7 years SWE at Google + Nest; HCI research with Bayesian models, feature extraction, WEKA; published ML work | Strong |
| User interaction pattern analysis | HCI publications, granular telemetry analysis at Google Workspace scale | Strong |
| Comfort with ambiguity | Ship/hold decisions on generative features, mid-flight pivots (Databricks toolchain) | Strong |
| Consumer or B2B end-user feature delivery | Google Workspace (1B+ users), Brandfolder ($70M ARR), Neat Capital | Strong |

**Fit verdict:** Strong candidate. Eval harness experience is rare and directly applicable. The alignment angle (behavioral defaults, steerability) is adjacent rather than exact — reframe your eval work as behavioral safety work, not just quality assurance.

---

## Gap Analysis

| Gap | Severity | Counter |
|---|---|---|
| No direct alignment/safety background | Medium | Eval harness + HCI behavioral modeling is structurally the same problem — defining behavioral norms for systems that interact with humans. Lead with this reframe. |
| No published alignment research | Low | Not required. Role is PM, not researcher. But your ACM pubs show you can engage with research rigorously. |
| Conversational AI vs. generative content tools | Low | Brandfolder AI, Smartsheet agentic features — these are generative systems. Not conversational per se, but overlapping evaluation challenges. |
| 25% in-office (SF or NYC) | Flag | Confirm location flexibility before applying. |
| Short Google Workspace tenure (10 months) | Low | Have the clean narrative ready: came back through full interview loop, owned a hard org problem, layoff was first large-scale Google RIF. Don't over-explain. |

---

## Anticipated Questions

**1. "Walk me through how you've approached AI evaluations."**
→ Deploy S001 (LLM-as-a-Judge Eval Harness). Open with the earned insight: "Non-deterministic AI requires a fundamentally different definition of 'done' — the unit test mindset breaks." Then STAR. Close with the lessons: 50 metrics = noise, data rot is the silent killer, ship phase one before perfect.

**2. "How do you define 'safe' or 'good' model behavior? What's your framework?"**
→ No direct experience with constitutional AI, but you have an answer: behavioral norms come from use cases + user expectation modeling, not abstract principles. Anchor to your HCI research origins — you've spent a career studying the gap between what systems assume about human behavior and what people actually do. That's the same question Anthropic is solving.

**3. "Tell me about a time you had to navigate a hard tradeoff between moving fast and getting it right."**
→ Deploy S001 (ship phase one before LLM-as-a-judge layer was ready) OR S007 (semantic search — throw out the incremental roadmap and prototype instead). S001 is stronger here because it's explicitly about when to hold vs. ship on a safety-adjacent question.

**4. "What does good look like for a generative AI feature? How do you know when to launch?"**
→ Synthesize S001 + S005 (file sharing incomplete data). The answer: "Walk before run." Hero metrics, not coverage. Define behavioral pass criteria before writing the first line of the eval. The launch decision is really a question of whether the failure modes are understood, not whether they're eliminated.

**5. "Why Anthropic? Why this specific team?"**
→ Be genuine: you've been building with Claude (Anthropic Claude is literally in your Brandfolder stack), you've thought hard about the evaluation side of AI safety, and the Model Behaviors team is the place where your eval work has the most leverage. Mention that you've been writing about this publicly (Substack post: "We tried to evaluate our AI. Here's what broke.") — shows you're thinking about it beyond your day job.

**6. "How do you work with researchers?"**
→ Google background: you worked alongside ML teams as an engineer before you were a PM. You know how to read a research paper, how to pressure-test a methodology, and how to translate a finding into a product requirement without destroying the nuance. Give a specific example — the Databricks toolchain pivot required working closely with the data/ML team to understand what the eval infrastructure could actually support.

**7. "Where does AI fail? Where don't you use it?"**
→ This scored 4.5/5 at OpenHands. Lead with "Middle schooler" analogy for math/reasoning; add genuine specific current examples. Don't hedge — show you've thought about this critically as a practitioner, not just a product observer.

---

## Questions to Ask

1. "The Research PM title signals this team is close to the research org — how does the PM role actually interface with alignment researchers? Are you translating findings into product, or are you setting the research agenda jointly?"

2. "When you talk about 'behavioral defaults' — how much of that is driven by user research vs. theoretical alignment work vs. what you learn from real traffic? I'm curious where the ground truth comes from."

3. "Anthropic ships models to developers via API as well as consumers via Claude.ai — how does the Model Behaviors team think about the fact that 'good default behavior' might mean something different to a developer building with the API vs. an end user?"

4. "What would it look like for this role to be genuinely successful in the first 6 months — what does 'early progress' look like from the team's perspective?"

---

## Stories to Drill

| Story | Why | Drill Focus |
|---|---|---|
| S001 — LLM-as-a-Judge Eval Harness | Primary story for this loop. Most directly relevant to alignment eval work. | Open with earned insight, not context. Time to <90 seconds. |
| S007 — Semantic Search Prototype | Rapid experimentation signal; addresses OpenHands rejection gap. | Tighter opening line: "I built the prototype instead of arguing for it." |
| S006 — Surface Touch / ContextType | Origin story for human-centered AI philosophy. Deploy when asked about values or what shaped your thinking. | Don't lead with it — save for "what drives you" or values questions. |
| S002 — Google Workspace Transformation | Org influence, alignment at scale, B2B technical product at 1B+ users. | Use when cross-functional influence or scale is asked about. |

---

## Watch Out For

- **Over-explaining the eval harness** — you know this material cold and will be tempted to go long. Open with the insight, not the setup. Let them pull.
- **Not connecting eval work to alignment** — say the word "behavioral safety" explicitly. The framing matters at Anthropic; eval-as-QA is a different job than eval-as-alignment-infrastructure.
- **Google Workspace tenure question** — have the 30-second clean version ready. Do not volunteer it, but have it if asked.
- **The "sole IC" trap** — you worked with a 13-person cross-functional team. Lead with the team picture, not the solo angle.
- **Rambling preamble** (persistent pattern) — for every answer, write the point first. The context is not the story; the insight is the story.

---

## Other Anthropic Roles to Monitor

The following Anthropic postings appear to have been taken down as of 2026-03-14. Were among the highest-fit roles in the pipeline:

| Role | Score | Notes |
|---|---|---|
| Lead PM, Developer Services (ID: 5021316008) | 88 | "Highest-fit role" — DevX, Evals, Observability stack. Monitor for repost. |
| PM, Platform Developer Experiences (ID: 4987670008) | 90 | Console, SDK, docs layer. Taken down. |
| PM, API (ID: 4936029008) | 88 | Enterprise API experience. Taken down. |

If these reappear, prioritize Lead PM Developer Services — directly maps your eval harness work to a platform PM charter.
