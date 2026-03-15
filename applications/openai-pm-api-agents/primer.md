# Primer: Product Manager, API Agents — OpenAI
*Generated: 2026-03-14*

---

## Role Summary

**Title:** Product Manager, API Agents
**Company:** OpenAI
**Location:** San Francisco, CA (on-site)
**Comp:** $293K–$325K/year
**Posted:** ~2 weeks ago (LinkedIn ID 4375275973)
**URL:** https://openai.com/careers/product-manager-api-agents-san-francisco/

This role sits on the OpenAI API team — the infrastructure layer that powers millions of developers building on top of OpenAI's models. Specifically, it owns the *agentic* side: SDKs, APIs, and developer primitives for building agent-based applications. This is not a consumer PM role. It is a highly technical, deeply developer-facing role at the center of OpenAI's platform strategy.

---

## Company Overview

OpenAI is in a pivotal transition from model provider to full-stack developer platform. The API team's north star is making OpenAI's models effortlessly accessible to developers — managing the infrastructure, SDKs, and product layers that support fine-tuning, data management, and user experience delivery at scale.

**What matters to OpenAI's API team right now:**
- Reliability and ergonomics for agentic workflows (tool use, orchestration, state)
- SDK quality — Assistants API, the Responses API, and agents SDK are evolving rapidly
- Developer trust: the API is a professional tool; DX problems are existential
- Balancing velocity (move fast, ship) with the stakes of being foundational infrastructure

**Recent context:**
- OpenAI launched the Responses API and an agents SDK in early 2025; these are still evolving
- Competing developer platforms (Anthropic, Google, Mistral) are all aggressively courting the same developers
- "Agentic" is now the primary growth vector — Operator, Swarm, LangGraph, etc. all rely on OpenAI APIs

---

## Fit Score: 85 / 100

### Matched Requirements

| Requirement | Evidence | Strength |
|---|---|---|
| 5+ years PM experience | ~3 years PM (Neat Capital → Google Workspace → Smartsheet) + 7 years engineering at Google | Strong — SWE history elevates the actual depth |
| Building for developers | Nest SDK (Pairing Kit, Works with Nest Platform), Nest × Yale BLE provisioning, all engineering roles building developer-facing tools | Strong — not just empathy, actual memory |
| API intuition | Designed developer-facing APIs at Nest; built LLM eval harness (effectively an internal eval API); now building agentic tools on top of OpenAI/Claude APIs as a practitioner | Strong |
| Agentic AI depth | Built 3-tiered eval framework for agentic AI; prototyped RAG/agent workflows with LangChain + Claude; actively builds Claude agent skills (career coaching system) | Strong — practitioner, not just theorist |
| Cross-functional with research/engineering | Google Workspace (50-person product org alignment), Smartsheet (partnered with data science + engineering on eval infra) | Strong |
| Prioritization under ambiguity | Multiple stories: S003 (headcount freeze), S005 (no market data), S004 (competitive reframe) | Strong |

### Gaps

| Gap | Severity | Mitigation |
|---|---|---|
| Explicit "developer tools PM" title | Medium | 7 years as an engineer IS developer experience — frame the SWE arc as the source of developer intuition, not just background |
| PM tenure breadth (3 years PM vs. 5+ expected) | Low-Medium | Engineering years are deeply relevant; the JD says "5+ years PM or related industry experience" — engineering counts |
| No OSS community leadership | Low | Not mentioned in JD; only flagged in OpenHands context. OpenAI API is primarily commercial, not OSS-first |
| San Francisco on-site requirement | Depends | Confirm location readiness; OpenAI is explicitly SF-based |

---

## Interview Strategy

### Your Core Narrative for This Role

> "I have the SWE background to think like the developers I'm building for, and the agentic AI depth to understand what they're actually trying to build. My superpower is that I don't have to translate between product and engineering — I speak both natively. And I've been building with OpenAI APIs as a practitioner, which means I have real opinions about where the developer experience breaks down."

Lead every answer with the point, not the context. Anchor to one story. Close with the earned insight.

---

### Anticipated Questions & Story Deployments

**1. "Tell me about your experience building products for developers."**
- **Deploy:** Nest SDK work (Pairing Kit / Works with Nest Platform) + current agentic prototyping
- **Lead:** "I've been a developer building for developers — at Nest I engineered the Android SDK that third-party developers used to integrate with the Nest ecosystem. That experience gave me something different from empathy: developer memory. I still remember what it felt like to stare at an API reference and wonder why the abstraction was wrong."
- **Anchor to:** Specific API ergonomics challenges you've encountered as a practitioner with OpenAI's SDK

**2. "How do you think about evaluating AI products? How do you know when something is ready to ship?"**
- **Deploy:** S001 (LLM-as-a-judge eval harness) — this is your strongest story for this role
- **Lead:** "At Smartsheet I built the evaluation infrastructure that gave leadership the confidence to ship AI features — a 3-tiered system that became the company's standard for when agentic features were safe to launch."
- **Key earned insight:** "Non-deterministic AI requires a different definition of 'done.' Writing pass/fail unit tests for generative systems breaks — the system surfaces 5 correct answers when you expected 3. The failure isn't the AI; it's the test. And data rots: test stability requires synthetic injection, not just golden datasets."

**3. "What's broken about the current developer experience for building agents?"**
- **This is a free-form product thinking question — have opinions ready**
- Current friction points with OpenAI's API agents stack (be specific and honest):
  - State management across tool calls is still manual and error-prone
  - The contract between agent and tool is under-specified — unclear when/how to handle partial failures
  - Observability is weak; developers can't easily inspect what happened inside a multi-step agent run
  - Reliability guarantees are missing — there's no "this will retry with backoff" built in
- **Anchor:** "The hardest part of building agents isn't the LLM call — it's everything around it. I've been building agent infrastructure both professionally and as a side project, and the consistent friction I see is..."

**4. "How do you prioritize what to build when there's no market data?"**
- **Deploy:** S005 (File Sharing / incomplete data) or S007 (semantic search prototype)
- **Lead with S007:** "When the idea is hard to explain and data is thin, build the thing that makes it undeniable. At Brandfolder I threw out an incremental search roadmap and bet on semantic search — and instead of arguing for it, I built a working prototype in a weekend that made the case in five minutes."
- **Close:** "The principle I took from it: a precise use case that makes the requirement undeniable beats five data points that are directionally interesting."

**5. "Tell me about a time you had to make a hard call with incomplete information."**
- **Deploy:** S004 (People Tagging — halted first launch) or S003 (Neat Capital headcount freeze)
- **S004 is stronger here:** Halting a launch mid-flight, resetting requirements, and reframing a business case is a high-conviction decision with real stakes.

**6. "How do you collaborate with research and engineering to ship model improvements?"**
- **Deploy:** S001 (eval harness + Databricks lakehouse pivot) — shows graceful pivoting and cross-team coordination
- **Note:** At OpenAI, this question has extra weight — the PM is literally adjacent to the research team. Show that you can talk to researchers as a peer, not just translate for them.

**7. "Why OpenAI? Why this role specifically?"**
- Be specific and honest: you've been building on OpenAI's APIs, you've observed the friction in agentic systems from the developer side, and you want to be on the team making that better.
- Reference: "I've built a Claude-powered career coaching agent as a side project — not because I had to, but because I wanted to understand how developers actually experience building agents. The issues I ran into — state management, evaluation, observability — are exactly the problems this role works on."
- Avoid generic "OpenAI is changing the world" framing. They hear it all day.

---

## Questions to Ask

1. **"The Responses API and agents SDK both shipped in the last year — how do you think about API stability vs. the pace of model capability improvement? Where does the PM draw that line?"**
   *(Shows you understand the fundamental tension of developer platform PM)*

2. **"When you talk to developers building on the agents SDK, what's the most common thing they're surprised by — positively or negatively?"**
   *(Shows practitioner curiosity; also gets you real intelligence)*

3. **"How does the API team's roadmap interact with the research team's output? Is it primarily pull (research ships, API team exposes it) or does the API team shape what gets built?"**
   *(Important for understanding where the PM actually has leverage)*

4. **"What does 'agentic reliability' mean to this team — is that a research problem, an API design problem, or both?"**
   *(Probes whether this is a PM role with real scope or a coordination role)*

---

## Watch Out For

**"Your PM experience is only 3 years — we need 5+"**
- Counter: The JD says "5+ years PM or related industry experience." Seven years as a Google engineer building developer-facing platforms is directly relevant — it's not background, it's the job.
- Don't be defensive. Say: "My 7 years of engineering is the reason I have real developer intuition, not learned empathy. I've been on both sides of the API."

**"You don't have explicit developer tools PM experience"**
- This was the OpenHands rejection signal too. Have a sharp, specific counter ready.
- Counter: Lead with the Nest SDK work, then the agentic AI prototyping work (Claude career coach, RAG prototypes), then the eval harness. "I've been building with these APIs as a practitioner, not as an observer — I have opinions based on real friction."

**"Is this role a step down from your current scope?"**
- This role is highly focused; your current role has broader $70M ARR scope. If asked, frame it as going deeper, not narrower: "I want to go deeper on the technical layer where I have the most conviction."

**Location**
- OpenAI requires SF on-site. Be clear and prepared on this.

---

## Stories to Deploy (Ranked for This Role)

| Priority | Story | Why |
|---|---|---|
| 1 | **S001 — LLM-as-a-Judge Eval Harness** | Directly maps to model capability/quality work at OpenAI; hardest technical story |
| 2 | **Nest SDK / Works with Nest Platform** | Developer-facing API design; shows you've been the developer |
| 3 | **S007 — Semantic Search Prototype** | Rapid experimentation; show-don't-tell; addresses OpenHands gap |
| 4 | **S004 — People Tagging / $2M ARR** | 0-to-1 AI delivery with real conviction; good "hard decision" story |
| 5 | **S006 — HCI Research (ContextType)** | Use only if asked about product philosophy origins; rare differentiator |

---

## Loop Setup (If Advancing)

If you get past the recruiter screen, expect:
- **Round 1:** Product thinking on developer experience / API design. Likely an engineer or senior PM.
- **Round 2:** AI/agentic technical depth. Could be a researcher or senior engineer. Have S001 sharp.
- **Round 3:** Vision / culture / leadership. Likely Sam Altman or a VP. Have a point of view on where agentic infrastructure needs to go in the next 2 years.

Update `coaching_state.md` with OpenAI loop details as rounds complete.
