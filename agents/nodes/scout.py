"""
Scout Agent — autonomous job research via Gemini function calling.

Uses an iterative tool-use loop where Gemini reasons about search results,
follows leads, discovers companies, and saves job opportunities. The agent
has a set of tools (web search, page reading, saving leads/companies) and
autonomously decides what to explore and when to dig deeper.

This is NOT a scripted pipeline — the LLM drives the strategy.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field

import httpx
import structlog
from google import genai
from google.genai import types, errors
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from agents.config import settings
from agents.llm import load_system_prompt
from agents.state import AgentState
from agents.tools.vector_tools import query_knowledge_base
from agents.tools.supabase_tools import get_supabase_client

logger = structlog.get_logger()

MAX_TOOL_CALLS = 30
SCRAPE_TIMEOUT = 15.0

# ─── Tool Definitions (Gemini function declarations) ───────────

SCOUT_TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="web_search",
                description="Search Google for anything — job postings, company info, forums, hiring threads, career pages. Use diverse queries.",
                parameters_json_schema={
                    "type": "OBJECT",
                    "properties": {
                        "query": {
                            "type": "STRING",
                            "description": "The search query. Keep it simple and natural (3-8 words).",
                        },
                    },
                    "required": ["query"],
                },
            ),
            types.FunctionDeclaration(
                name="read_page",
                description="Read the text content of a web page. Use to dig into search results, read career pages, explore company sites, or read forum threads.",
                parameters_json_schema={
                    "type": "OBJECT",
                    "properties": {
                        "url": {
                            "type": "STRING",
                            "description": "The URL to read.",
                        },
                    },
                    "required": ["url"],
                },
            ),
            types.FunctionDeclaration(
                name="save_lead",
                description="Save any relevant job posting you find. Cast a wide net — it does not need to be a perfect fit, downstream agents will filter later. Only call this for real, open job postings.",
                parameters_json_schema={
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Exact job title"},
                        "company": {"type": "STRING", "description": "Company name"},
                        "url": {"type": "STRING", "description": "URL of the job posting"},
                        "description": {"type": "STRING", "description": "2-3 sentence role summary"},
                        "why_good_fit": {"type": "STRING", "description": "Why this is a good fit for the candidate"},
                    },
                    "required": ["title", "company", "url", "why_good_fit"],
                },
            ),
            types.FunctionDeclaration(
                name="save_target_company",
                description="Add a company to the watchlist for ongoing monitoring. Use when you find a company that seems like a great cultural/skills fit even if they don't have a specific opening right now.",
                parameters_json_schema={
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING", "description": "Company name"},
                        "domain": {"type": "STRING", "description": "Company website domain (e.g., 'acme.com')"},
                        "careers_url": {"type": "STRING", "description": "URL of their careers/jobs page"},
                        "why_target": {"type": "STRING", "description": "Why this company is a good fit"},
                        "priority": {"type": "STRING", "description": "high, medium, or low"},
                    },
                    "required": ["name", "why_target", "priority"],
                },
            ),
            types.FunctionDeclaration(
                name="check_existing",
                description="Check what jobs and target companies are already being tracked. Call this early to avoid saving duplicates.",
                parameters_json_schema={
                    "type": "OBJECT",
                    "properties": {},
                },
            ),
            types.FunctionDeclaration(
                name="done",
                description="Call when you've finished researching. Provide a summary of what you found.",
                parameters_json_schema={
                    "type": "OBJECT",
                    "properties": {
                        "summary": {
                            "type": "STRING",
                            "description": "Brief summary of discoveries, patterns noticed, and suggestions for next run.",
                        },
                    },
                    "required": ["summary"],
                },
            ),
            types.FunctionDeclaration(
                name="find_jobs_via_llm",
                description=(
                    "Use an LLM with Google Search to find a list of recent, relevant job "
                    "postings based on a query. The LLM will perform exhaustive web crawling "
                    "and extract structured job data."
                ),
                parameters_json_schema={
                    "type": "OBJECT",
                    "properties": {
                        "query": {
                            "type": "STRING",
                            "description": (
                                "The search query, e.g., 'recent AI Product Manager job openings "
                                "at YC startups'. Be specific about roles and criteria."
                            ),
                        },
                    },
                    "required": ["query"],
                },
            ),
            types.FunctionDeclaration(
                name="find_companies_via_llm",
                description=(
                    "Use an LLM with Google Search to discover a list of potential target "
                    "companies based on a query. The LLM will identify companies that match "
                    "your criteria."
                ),
                parameters_json_schema={
                    "type": "OBJECT",
                    "properties": {
                        "query": {
                            "type": "STRING",
                            "description": (
                                "The search query, e.g., 'top climate-tech companies hiring "
                                "product managers' or 'fast growing series A developer tools startups'."
                            ),
                        },
                    },
                    "required": ["query"],
                },
            ),
        ]
    )
]

# ─── Pydantic Schemas for LLM Tools ──────────────────────────

class LLMJobResult(BaseModel):
    title: str = Field(description="Exact job title")
    company: str = Field(description="Company name")
    location: str = Field(description="Location (e.g., 'Remote', 'San Francisco', etc.)")
    postedDate: str = Field(description="E.g., '2 days ago'")
    sourceUrl: str = Field(description="URL to the job posting")
    description: str = Field(description="Short summary (2-3 sentences)")
    relevanceScore: int = Field(description="0-100, how well it fits based on the query")
    keyRequirements: list[str] = Field(description="List of key requirements")
    salaryRange: str | None = Field(None, description="Salary range if available, otherwise null")

class LLMCompanyResult(BaseModel):
    name: str = Field(description="Company name")
    domain: str | None = Field(None, description="Company website domain (e.g., 'acme.com')")
    careersUrl: str | None = Field(None, description="URL of their careers/jobs page if found")
    whyTarget: str = Field(description="Why this company is a good fit based on the query")
    priority: str = Field(description="'high', 'medium', or 'low'")


# ─── Tool Implementations ─────────────────────────────────────


async def _tool_web_search(query: str) -> str:
    """Execute a web search and return results as text."""
    logger.info("scout.tool.web_search", query=query)

    # Try Serper.dev first (Google Search API)
    if settings.serper_api_key:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    json={"q": query, "num": 10},
                    headers={
                        "X-API-KEY": settings.serper_api_key,
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                data = response.json()

            results = []
            for item in data.get("organic", []):
                results.append(
                    f"- [{item.get('title', '')}]({item.get('link', '')})\n"
                    f"  {item.get('snippet', '')}"
                )

            if results:
                return f"Search results for '{query}':\n\n" + "\n\n".join(results)
            return f"No results found for '{query}'."
        except Exception as e:
            logger.error("scout.tool.serper_error", error=str(e))

    # Fallback to DuckDuckGo
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            ddg_results = list(ddgs.text(query, max_results=10))

        if ddg_results:
            results = []
            for r in ddg_results:
                results.append(f"- [{r.get('title', '')}]({r.get('href', '')})\n  {r.get('body', '')}")
            return f"Search results for '{query}':\n\n" + "\n\n".join(results)
    except Exception as e:
        logger.error("scout.tool.ddg_error", error=str(e))

    return f"Search failed for '{query}'. Try a different query."


async def _tool_read_page(url: str) -> str:
    """Scrape and return the text content of a web page."""
    logger.info("scout.tool.read_page", url=url[:80])
    try:
        async with httpx.AsyncClient(
            timeout=SCRAPE_TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        html = response.text
        # Strip scripts, styles, and tags
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        if text:
            return f"Page content from {url}:\n\n{text[:6000]}"
        return f"Could not extract text from {url}."

    except Exception as e:
        return f"Failed to read {url}: {str(e)}"


async def _tool_save_lead(
    title: str, company: str, url: str, description: str = "", why_good_fit: str = ""
) -> str:
    """Save a job lead to Supabase."""
    logger.info("scout.tool.save_lead", title=title, company=company)
    try:
        sb = get_supabase_client()

        # Check for duplicate
        existing = sb.table("jobs").select("id").eq("url", url).execute()
        if existing.data:
            return f"Already tracking this job: {title} at {company}."

        # Ensure company exists
        company_row = sb.table("companies").select("id").eq("name", company).execute()
        company_id = None
        if company_row.data:
            company_id = company_row.data[0]["id"]
        else:
            insert = sb.table("companies").insert({"name": company}).execute()
            if insert.data:
                company_id = insert.data[0]["id"]

        job_data: dict[str, Any] = {
            "title": title,
            "url": url,
            "description_md": f"{description}\n\n**Scout's reasoning:** {why_good_fit}",
            "status": "scouted",
            "source": "scout_agent",
        }
        if company_id:
            job_data["company_id"] = company_id

        sb.table("jobs").insert(job_data).execute()
        return f"✅ Saved job lead: {title} at {company}"

    except Exception as e:
        logger.error("scout.tool.save_lead_error", error=str(e))
        return f"Failed to save lead: {str(e)}"


async def _tool_save_target_company(
    name: str, domain: str = "", careers_url: str = "", why_target: str = "", priority: str = "medium"
) -> str:
    """Save a target company to the watchlist."""
    logger.info("scout.tool.save_target_company", name=name, priority=priority)
    try:
        sb = get_supabase_client()

        # Check if company already exists
        existing = sb.table("companies").select("id, is_target").eq("name", name).execute()
        if existing.data:
            row = existing.data[0]
            if row.get("is_target"):
                return f"Already tracking {name} as a target company."
            # Update existing company to be a target
            sb.table("companies").update({
                "is_target": True,
                "why_target": why_target,
                "scout_priority": priority,
                "domain": domain or None,
                "careers_url": careers_url or None,
            }).eq("id", row["id"]).execute()
            return f"✅ Upgraded {name} to target company (priority: {priority})"

        # Insert new target company
        sb.table("companies").insert({
            "name": name,
            "domain": domain or None,
            "careers_url": careers_url or None,
            "is_target": True,
            "why_target": why_target,
            "scout_priority": priority,
        }).execute()
        return f"✅ Added {name} to target company watchlist (priority: {priority})"

    except Exception as e:
        logger.error("scout.tool.save_company_error", error=str(e))
        return f"Failed to save company: {str(e)}"


async def _tool_check_existing() -> str:
    """Check what's already tracked in Supabase."""
    logger.info("scout.tool.check_existing")
    try:
        sb = get_supabase_client()

        # Get existing jobs
        jobs = sb.table("jobs").select("title, url, status").execute()
        job_list = jobs.data or []

        # Get target companies
        companies = sb.table("companies").select("name, careers_url, is_target, scout_priority").eq("is_target", True).execute()
        company_list = companies.data or []

        output = f"Currently tracking {len(job_list)} jobs and {len(company_list)} target companies.\n\n"

        if job_list:
            output += "**Existing jobs:**\n"
            for j in job_list[:20]:
                output += f"- [{j.get('status', '?')}] {j.get('title', '?')} — {j.get('url', 'no url')}\n"
            if len(job_list) > 20:
                output += f"  ... and {len(job_list) - 20} more\n"

        if company_list:
            output += "\n**Target companies:**\n"
            for c in company_list:
                output += f"- {c.get('name', '?')} ({c.get('scout_priority', '?')}) — {c.get('careers_url', 'no careers url')}\n"

        return output

    except Exception as e:
        return f"Failed to check existing data: {str(e)}"


async def _tool_find_jobs_via_llm(query: str) -> str:
    """Use Gemini with Google Search to find jobs."""
    logger.info("scout.tool.find_jobs_via_llm", query=query)
    try:
        client = genai.Client(api_key=settings.google_api_key)
        system_instruction = (
            "You are an expert job scout. Your task is to find the most recent "
            "and relevant job postings based on the user's query.\n\n"
            "1. Extract structured data for each job.\n"
            "2. Ensure you provide real URLs to the job postings.\n"
            "3. Focus on recent postings (last 7-14 days if possible)."
        )
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Find recent job openings based on this query: {query}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[{"google_search": {}}],  # type: ignore
                response_mime_type="application/json",
                response_schema=list[LLMJobResult],  # type: ignore
            )
        )
        if response.text:
            return f"Found jobs mapping to the schema:\n{response.text}"
        return f"No structural results returned for jobs query '{query}'."
    except Exception as e:
        logger.error("scout.tool.find_jobs_error", error=str(e))
        return f"Failed to run LLM job search: {str(e)}"


async def _tool_find_companies_via_llm(query: str) -> str:
    """Use Gemini with Google Search to discover target companies."""
    logger.info("scout.tool.find_companies_via_llm", query=query)
    try:
        client = genai.Client(api_key=settings.google_api_key)
        system_instruction = (
            "You are an expert corporate scout. Your task is to discover interesting "
            "companies that match the user's query parameters and might be good "
            "long-term targets for a candidate's career.\n\n"
            "1. Extract structured data for each company.\n"
            "2. Try to find their domains and career page URLs if possible.\n"
            "3. Explain why they are a good target based on the criteria."
        )
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Find target companies based on this query: {query}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[{"google_search": {}}],  # type: ignore
                response_mime_type="application/json",
                response_schema=list[LLMCompanyResult],  # type: ignore
            )
        )
        if response.text:
            return f"Found companies mapping to the schema:\n{response.text}"
        return f"No structural results returned for companies query '{query}'."
    except Exception as e:
        logger.error("scout.tool.find_companies_error", error=str(e))
        return f"Failed to run LLM company search: {str(e)}"


# ─── Tool Dispatcher ──────────────────────────────────────────


TOOL_HANDLERS = {
    "web_search": lambda args: _tool_web_search(args.get("query", "")),
    "read_page": lambda args: _tool_read_page(args.get("url", "")),
    "save_lead": lambda args: _tool_save_lead(
        title=args.get("title", ""),
        company=args.get("company", "Unknown"),
        url=args.get("url", ""),
        description=args.get("description", ""),
        why_good_fit=args.get("why_good_fit", ""),
    ),
    "save_target_company": lambda args: _tool_save_target_company(
        name=args.get("name", ""),
        domain=args.get("domain", ""),
        careers_url=args.get("careers_url", ""),
        why_target=args.get("why_target", ""),
        priority=args.get("priority", "medium"),
    ),
    "check_existing": lambda args: _tool_check_existing(),
    "find_jobs_via_llm": lambda args: _tool_find_jobs_via_llm(args.get("query", "")),
    "find_companies_via_llm": lambda args: _tool_find_companies_via_llm(args.get("query", "")),
}


# ─── Main Agent Loop ──────────────────────────────────────────


async def _build_initial_context() -> str:
    """Build the candidate profile context from ChromaDB."""
    profile_chunks = await query_knowledge_base(
        query_text="professional experience skills roles career product management AI leadership projects achievements",
        n_results=15,
    )

    if not profile_chunks:
        return "No profile context available. The vector database may be empty."

    context_parts = []
    for chunk in profile_chunks:
        source = chunk.get("metadata", {}).get("source", "unknown")
        context_parts.append(f"[{source}] {chunk.get('document', '')[:500]}")

    return "\n---\n".join(context_parts[:10])


async def scout_jobs(state: AgentState) -> AgentState:
    """Run the autonomous Scout Agent.

    Uses Gemini function calling in an iterative loop:
    1. Build profile context from ChromaDB
    2. Initialize Gemini with tools and system prompt
    3. Let Gemini reason and call tools until it's done or hits budget
    """
    logger.info("scout.start")

    # ── Build context ──────────────────────────────────────────
    profile_context = await _build_initial_context()
    system_prompt = load_system_prompt("scout")

    # ── Initialize Gemini with tools ───────────────────────────
    client = genai.Client(api_key=settings.google_api_key)

    # Start the conversation with the candidate's profile
    initial_message = f"""Here is the candidate's professional profile from their knowledge base:

{profile_context}

---

Begin your research. Start by checking what's already tracked, then explore broadly.
Think about what kinds of companies and roles would be the best fit for this candidate,
and then go find them. Remember to follow leads and dig deeper into promising threads.

CRUCIAL INSTRUCTION: Your goal is to cast a VERY WIDE NET and build an exhaustive list 
of potential opportunities. If a role or company is even somewhat relevant, save it! 
Do not filter rigidly — downstream agents will carefully review and score the leads you find."""

    chat = client.aio.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=SCOUT_TOOLS,
        )
    )
    tool_calls_made = 0
    leads_saved = 0
    companies_saved = 0
    agent_done = False

    logger.info("scout.loop.start", max_tools=MAX_TOOL_CALLS)

    @retry(
        retry=retry_if_exception_type(errors.APIError),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        stop=stop_after_attempt(6)
    )
    async def _send_message_with_retry(msg: Any) -> Any:
        try:
            return await chat.send_message(msg)
        except errors.APIError as e:
            if e.code == 429:
                logger.warning("scout.rate_limit", error="Gemini API rate limit hit. Retrying with backoff...")
                raise e
            raise e

    # ── Agentic loop ───────────────────────────────────────────
    response = await _send_message_with_retry(initial_message)

    while tool_calls_made < MAX_TOOL_CALLS and not agent_done:
        # Check if the model wants to call tools
        if not response.function_calls and not response.text:
            logger.info("scout.loop.no_response")
            break

        tool_responses = []
        has_function_call = False

        if response.function_calls:
            for fc in response.function_calls:
                has_function_call = True
                fn_name = fc.name
                fn_args = fc.args

                logger.info("scout.tool_call", tool=fn_name, args_keys=list(fn_args.keys()))

                # Handle the "done" tool specially
                if fn_name == "done":
                    summary = fn_args.get("summary", "No summary provided.") if fn_args else "No summary provided."
                    logger.info("scout.done", summary=summary)
                    agent_done = True
                    tool_responses.append(
                        types.Part.from_function_response(
                            name="done",
                            response={"result": "Session complete."},
                        )
                    )
                    break

                # Execute the tool
                handler = TOOL_HANDLERS.get(fn_name)
                if handler:
                    try:
                        result = await handler(fn_args)
                    except Exception as e:
                        result = f"Tool error: {str(e)}"
                        logger.error("scout.tool_error", tool=fn_name, error=str(e))

                    # Track saves
                    if fn_name == "save_lead" and "✅" in str(result):
                        leads_saved = int(leads_saved) + 1
                    elif fn_name == "save_target_company" and "✅" in str(result):
                        companies_saved = int(companies_saved) + 1

                    tool_calls_made = int(tool_calls_made) + 1
                    logger.info("scout.tool_result", tool=fn_name, result_preview=result[:100], calls=tool_calls_made)

                    tool_responses.append(
                        types.Part.from_function_response(
                            name=fn_name,
                            response={"result": result},
                        )
                    )
                else:
                    tool_responses.append(
                        types.Part.from_function_response(
                            name=fn_name,
                            response={"result": f"Unknown tool: {fn_name}"},
                        )
                    )
        elif response.text:
            # The model is thinking out loud — log it
            logger.info("scout.thinking", text=response.text[:200])

        if agent_done:
            break

        if not has_function_call:
            # Model stopped calling tools — prompt it to continue or finish
            logger.info("scout.no_tools_called", message="Model stopped calling tools")
            try:
                response = await _send_message_with_retry(
                    "Continue researching or call the `done` tool if you're finished."
                )
            except Exception as e:
                logger.error("scout.continue_error", error=str(e))
                break
            continue

        # Send tool results back to the model
        if tool_responses:
            try:
                response = await _send_message_with_retry(tool_responses)
            except Exception as e:
                logger.error("scout.response_error", error=str(e))
                break

    logger.info(
        "scout.complete",
        tool_calls=tool_calls_made,
        leads_saved=leads_saved,
        companies_saved=companies_saved,
    )

    return {
        **state,
        "scouted_count": leads_saved,
        "target_companies_added": companies_saved,
        "tool_calls": tool_calls_made,
    }
