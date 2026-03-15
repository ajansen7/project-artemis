# Application Primer — Cohere
**Role:** Product Manager, Platform Experience & Developer Product
**URL:** https://jobs.ashbyhq.com/cohere/fe2e2971-e2c0-43fd-9ab1-187571776a5d
**Date:** 2026-03-14

---

## Company Overview

**What Cohere Does**
Enterprise AI platform built for regulated industries — the core pitch is security-first, data-private LLMs you can deploy in your own VPC or on-prem without sending customer data to a hyperscaler. That's the real differentiation vs. OpenAI/Anthropic for the RBC, Oracle, Salesforce enterprise buyer.

**Products**
- Frontier LLM APIs (Generate, Embed, Classify, Neural Search)
- North Platform — enterprise-grade GenAI with compliance controls; North for Banking launched with RBC Jan 2025
- Model customization / fine-tuning on proprietary data
- Cloud + on-prem deployments with data residency controls

**Company Signals**
- Founded by Aidan Gomez (co-author of "Attention is All You Need") — research credibility is real, not decorative
- $6.8B valuation (Aug 2025), $500M raised, $240M+ ARR, IPO signaled for 2026
- Chief AI Officer: Joelle Pineau (former Meta FAIR head) — strong research org
- Remote-first; Toronto HQ + SF/NY/London

**Culture Reads**
- Technical founders who came from research — expect depth, not buzz
- Security and compliance seriousness distinguishes them from hyperscaler-adjacent players
- "Trust without a hyperscaler" is their product narrative — resonate with this

---

## Role Scope

The PM owns three connected surfaces:
1. **Managed Services / Models as a Service** — deployment models, data residency, compliance controls
2. **API & SDK** — design, stability, documentation, ergonomic primitives
3. **Developer Tooling** — console, credentials management, usage analytics, testing environments

This is essentially the platform "trust layer" — the surface that determines whether a developer or enterprise team can depend on Cohere in production.

---

## Fit Analysis

### Where You're Strong

| Requirement | Your Evidence |
|---|---|
| Technical fluency / API design thinking | 7 years SWE at Google; built with LangChain, Anthropic Claude API; can engage at the API layer as a practitioner, not just a PM |
| Internal developer tooling | Built eval harness as cross-team shared infrastructure (S001) — exactly the "tooling that an org depends on" pattern |
| Platform PM with AI depth | Smartsheet AI platform owner; 3-tiered eval framework with statistical metrics for probabilistic systems |
| Execution bias / shipping quickly | People Tagging stop-and-relaunch (S004) — knew when to hold; Semantic Search prototype (S007) — knew when to skip the doc and build |
| Cross-functional collaboration | Google Workspace: aligned 50+ person product org without direct authority (S002) |
| Enterprise context | Neat Capital compliance automation; Smartsheet enterprise deployments |

### Gaps to Address

| Gap | Severity | Mitigation |
|---|---|---|
| Direct API/SDK product ownership | Medium | You've been a deep technical user and have built on top of these systems — frame as "I've been the developer your PM needs to understand" and bridge to internal tooling work |
| Model serving / inference infrastructure | Low | Nice-to-have per JD; acknowledge honestly if asked, point to depth in adjacent layer (eval infrastructure, platform tooling) |
| Data residency / compliance PM ownership | Low | Neat Capital compliance automation is adjacent; honest about where the gap is |
| Developer-first company culture (vs. enterprise B2B) | Low-Medium | OpenHands rejection cited this — address proactively; lean into the builder/tinkerer positioning and practitioner AI usage |

---

## Anticipated Interview Questions

### 1. "What's your experience owning an API or developer-facing product?"
**Story to deploy:** S001 (eval harness as developer infrastructure) + S007 (Lovable prototype — show don't tell PM instinct)
**Frame:** "I haven't owned a public-facing API product, but I've built and driven adoption of internal developer tooling — and I've been a technical user of AI APIs for years. The thing I've internalized about API product management is that the contract you make with developers is binding in a way that user-facing UX isn't..."

### 2. "How do you think about measuring success for a platform product where downstream use cases vary widely?"
**Story to deploy:** S001 (pass@k / pass^k metrics for probabilistic systems; 50-metric lesson)
**Key insight:** "I learned this the hard way — I built an eval harness with 50 metrics. 50 metrics is noise. The discipline is 5-10 core metrics that are load-bearing for the decisions you need to make, not comprehensive coverage."

### 3. "Tell me about a time you had to drive adoption of something you built across teams who hadn't asked for it."
**Story to deploy:** S001 (eval harness cross-team adoption at Smartsheet)
**Opening line:** "At Smartsheet I built the evaluation infrastructure that gave leadership the confidence to ship AI features — a 3-tiered system covering 100+ scenarios that became the company's standard for when agentic features were safe to launch."

### 4. "How do you prioritize when there are competing demands — API stability vs. new capabilities vs. developer experience?"
**Story to deploy:** S004 (People Tagging — halting a launch vs. competitive urgency; knowing what the right definition of done is)
**Key insight:** "Stability is not a feature — it's the tax that makes everything else trustworthy. I've made the call to halt a launch because it would have shipped a broken contract with users. That cost was worth it."

### 5. "What does good developer experience look like to you?"
**Frame:** Lead with practitioner perspective — you've been the developer struggling with API docs, SDK ergonomics, and missing console instrumentation. HCI research roots give you a principled answer: friction that doesn't feel like friction is the hardest problem. Reference the SurTouch/ContextType research as origin story for "interfaces should fit the person."
**Close with:** S007 — prototyping as the fastest way to surface DX problems that are invisible in a spec

### 6. "Why Cohere specifically?"
**Frame:** Be specific — not about "enterprise AI" generically. The answer is: the trust problem for regulated industries is real and unsolved by hyperscalers; Cohere's architectural bet (data residency as a foundation, not a feature flag) is the right answer; and Aidan Gomez building from the research up means the models are real. Don't flatter — engage with the product problem.

---

## Questions to Ask

1. **"The platform PM role spans API stability, managed services, and developer tooling — three surfaces with different shipping cadences and different customer personas. How does the team think about sequencing? Where's the constraint right now?"**

2. **"Data residency and compliance seem to be key differentiators for enterprise buyers — how much of the PM's work touches those requirements directly vs. working through engineering?"**

3. **"Cohere is in a category where the research org and the product org have to work in tight partnership. How does that relationship work in practice — is the PM driving the research roadmap, or reading research outputs and figuring out what to surface?"**

4. **"With an IPO on the horizon, how is the company thinking about the tension between developer/startup acquisition and enterprise reliability requirements? Do those compete for platform team attention?"**

---

## Stories to Drill Before Applying/Interviewing

| Priority | Story | Why |
|---|---|---|
| **1 — Must drill** | S001 (eval harness) | The single most relevant proof point — covers internal tooling, probabilistic systems, cross-team adoption. Opening line discipline critical. |
| **2 — Must drill** | S007 (semantic search prototype) | Rapid experimentation / show-don't-tell — directly addresses the OpenHands rejection gap and the developer-facing product instinct question |
| **3 — Useful** | S002 (Google Workspace) | Cross-functional influence at scale — use if asked about alignment without authority or org complexity |
| **4 — Optional** | S006 (HCI research) | "What shaped your product philosophy" — great closer if asked about values/origins; don't lead with it |

---

## Watch Out For

- **"Sole IC" reads as limited influence** — preempt by quantifying cross-team impact explicitly in S001 (shared infrastructure across multiple agentic AI teams)
- **Short Google Workspace tenure** — Cohere is not a big-company-prestige shop; less likely to probe this than a FAANG would, but have the narrative ready: "I came in for a specific transformation project; when it shipped, I moved to a role with more AI depth"
- **Enterprise-heavy positioning** — Cohere is developer-first even for enterprise buyers; lean into builder/tinkerer framing more than DAM/enterprise context
- **OpenHands rejection echo** — "rapid experimentation" gap is a real pattern across this job search. S007 is the counter, but needs a tight opening line. Don't let it come up as a surprise.

---

## Application Notes

- **Resume variant used:** Platform Experience PM tailored (leads with eval harness and internal tooling)
- **Cover letter tone:** Builder/tinkerer, practitioner depth, no AI-speak
- **Optimal story sequence for screening call:** S001 → S007 → bridge to S002 if org complexity comes up
- **Target:** 85/100 fit — platform PM + technical depth are strong matches; API ownership gap is real but bridgeable
