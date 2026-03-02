"""
Analyst Agent — job matching and gap analysis.

Takes a job URL or raw JD text, extracts requirements, queries the
vector store for matching context, and produces a scored MatchResult.
All LLM calls go through Gemini 2.5 Pro.
"""

from __future__ import annotations

import json
import structlog

from agents.config import settings
from agents.llm import generate_json, load_system_prompt
from agents.state import AgentState, MatchResult, GapItem, AgentAction
from agents.tools.scraping_tools import scrape_url_to_markdown
from agents.tools.vector_tools import query_knowledge_base
from agents.tools.supabase_tools import upsert_job

logger = structlog.get_logger()

# Load system prompt once at module level
ANALYST_SYSTEM_PROMPT = load_system_prompt("analyst")


async def analyze_job(state: AgentState) -> AgentState:
    """Score a job against the user's knowledge base.

    Steps:
        1. Convert job URL to clean markdown (via Firecrawl or basic scrape).
        2. Extract structured requirements from the JD using Gemini.
        3. Query ChromaDB for top-k relevant chunks.
        4. Prompt Gemini to produce a MatchResult with scores, matches, and gaps.
        5. Upsert results to Supabase.

    Returns:
        Updated state with match_result, job_description_md, job_id, and next_action.
    """
    job_url = state.get("job_url", "")
    job_description_md = state.get("job_description_md", "")

    logger.info("analyst.start", job_url=job_url)

    # ── Step 1: Get job description as markdown ─────────────────
    if job_url and not job_description_md:
        logger.info("analyst.scrape", url=job_url)
        try:
            job_description_md = await scrape_url_to_markdown(job_url)
            if not job_description_md or len(job_description_md.strip()) < 50:
                logger.warning("analyst.scrape.short_result", length=len(job_description_md))
                job_description_md = f"[Could not scrape sufficient content from {job_url}]"
        except Exception as e:
            logger.error("analyst.scrape.error", error=str(e))
            job_description_md = f"[Failed to scrape {job_url}: {e}]"

    if not job_description_md:
        logger.error("analyst.no_jd")
        return {
            "job_description_md": "",
            "match_result": MatchResult(
                match_score=0,
                recommended_actions=["No job description provided — enter a URL or paste JD text"],
            ),
            "next_action": AgentAction.DONE,
        }

    # ── Step 2: Extract key requirements from the JD ────────────
    logger.info("analyst.extract_requirements")
    requirements_prompt = f"""Analyze this job description and extract a structured list of requirements.

For each requirement, categorize it as one of: technical_skill, soft_skill, experience, education, certification, domain_knowledge.

Also extract the job title, company name (if present), and seniority level.

Job Description:
---
{job_description_md[:8000]}
---

Respond with JSON:
{{
    "job_title": "...",
    "company_name": "...",
    "seniority": "...",
    "requirements": [
        {{
            "text": "requirement description",
            "category": "technical_skill|soft_skill|experience|education|certification|domain_knowledge",
            "importance": "must_have|nice_to_have"
        }}
    ]
}}"""

    try:
        jd_parsed = await generate_json(requirements_prompt)
    except Exception as e:
        logger.error("analyst.extract.error", error=str(e))
        jd_parsed = {"job_title": "Unknown", "company_name": "Unknown", "requirements": []}

    job_title = jd_parsed.get("job_title", "Unknown Role")
    company_name = jd_parsed.get("company_name", "Unknown Company")
    requirements = jd_parsed.get("requirements", [])

    logger.info(
        "analyst.requirements_extracted",
        title=job_title,
        company=company_name,
        count=len(requirements),
    )

    # ── Step 3: Query vector store for relevant context ─────────
    logger.info("analyst.query_vectors")

    # Build a rich query from the JD requirements
    query_parts = [f"Job: {job_title} at {company_name}"]
    for req in requirements[:15]:  # Top 15 requirements
        query_parts.append(req.get("text", ""))
    query_text = "\n".join(query_parts)

    try:
        context_chunks = await query_knowledge_base(
            query_text=query_text,
            n_results=20,
        )
    except Exception as e:
        logger.error("analyst.vectors.error", error=str(e))
        context_chunks = []

    # Format context for the LLM
    context_text = ""
    if context_chunks:
        context_parts = []
        for chunk in context_chunks:
            source = chunk.get("metadata", {}).get("source", "unknown")
            content_type = chunk.get("metadata", {}).get("content_type", "")
            distance = chunk.get("distance", "?")
            context_parts.append(
                f"[Source: {source} | Type: {content_type} | Relevance: {distance}]\n"
                f"{chunk.get('document', '')}"
            )
        context_text = "\n\n---\n\n".join(context_parts)
    else:
        context_text = "[No knowledge base context available. The vector store may be empty — run the ingestion pipeline first.]"

    logger.info("analyst.context", chunks=len(context_chunks))

    # ── Step 4: Score with Gemini ───────────────────────────────
    logger.info("analyst.score")

    scoring_prompt = f"""You are evaluating this candidate for the following role.

## Job Description
Title: {job_title}
Company: {company_name}

Requirements:
{json.dumps(requirements, indent=2)}

## Full Job Posting
{job_description_md[:6000]}

## Candidate's Knowledge Base Context
The following are the most relevant excerpts from the candidate's knowledge base (portfolio, GitHub repos, Substack articles, career anecdotes, etc.):

{context_text[:12000]}

## Your Task

Score this candidate against the job requirements following your scoring rubric. For each matched requirement, cite the specific source from the knowledge base. For each gap, provide an actionable suggestion.

Respond with JSON matching this exact schema:
{{
    "match_score": <0-100>,
    "matched_requirements": [
        "Requirement — Evidence: [source:specific excerpt]"
    ],
    "gaps": [
        {{
            "requirement": "the missing requirement",
            "severity": "high|medium|low",
            "suggestion": "specific action to fill this gap"
        }}
    ],
    "recommended_actions": [
        "action 1",
        "action 2"
    ]
}}"""

    try:
        result_json = await generate_json(scoring_prompt, system_prompt=ANALYST_SYSTEM_PROMPT)
    except Exception as e:
        logger.error("analyst.score.error", error=str(e))
        return {
            "job_description_md": job_description_md,
            "match_result": MatchResult(
                match_score=0,
                recommended_actions=[f"Scoring failed: {e}"],
            ),
            "next_action": AgentAction.DONE,
        }

    # Parse into MatchResult
    gaps = []
    for gap_data in result_json.get("gaps", []):
        try:
            gaps.append(GapItem(
                requirement=gap_data.get("requirement", "Unknown"),
                severity=gap_data.get("severity", "medium"),
                suggestion=gap_data.get("suggestion", ""),
            ))
        except Exception:
            continue

    match_result = MatchResult(
        match_score=min(100, max(0, result_json.get("match_score", 0))),
        matched_requirements=result_json.get("matched_requirements", []),
        gaps=gaps,
        recommended_actions=result_json.get("recommended_actions", []),
    )

    logger.info(
        "analyst.scored",
        score=match_result.match_score,
        matches=len(match_result.matched_requirements),
        gaps=len(match_result.gaps),
    )

    # ── Step 5: Save to Supabase ────────────────────────────────
    job_id = ""
    try:
        job_record = await upsert_job(
            company_name=company_name,
            title=job_title,
            url=job_url or "",
            description_md=job_description_md[:10000],
            status="to_review",
            match_score=match_result.match_score,
            gap_analysis={
                "matched_requirements": match_result.matched_requirements,
                "gaps": [g.model_dump() for g in match_result.gaps],
                "recommended_actions": match_result.recommended_actions,
            },
        )
        job_id = job_record.get("id", "")
        logger.info("analyst.saved", job_id=job_id)
    except Exception as e:
        logger.error("analyst.save.error", error=str(e))

    return {
        "job_description_md": job_description_md,
        "match_result": match_result,
        "job_id": job_id,
        "next_action": AgentAction.AWAIT_HUMAN,
    }
