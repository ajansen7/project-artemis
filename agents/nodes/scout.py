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

import httpx
import structlog
import google.generativeai as genai

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
    genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="web_search",
                description="Search Google for anything — job postings, company info, forums, hiring threads, career pages. Use diverse queries.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "query": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="The search query. Keep it simple and natural (3-8 words).",
                        ),
                    },
                    required=["query"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="read_page",
                description="Read the text content of a web page. Use to dig into search results, read career pages, explore company sites, or read forum threads.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "url": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="The URL to read.",
                        ),
                    },
                    required=["url"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="save_lead",
                description="Save a specific job posting you've found and verified. Only call this for real, open job postings.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "title": genai.protos.Schema(type=genai.protos.Type.STRING, description="Exact job title"),
                        "company": genai.protos.Schema(type=genai.protos.Type.STRING, description="Company name"),
                        "url": genai.protos.Schema(type=genai.protos.Type.STRING, description="URL of the job posting"),
                        "description": genai.protos.Schema(type=genai.protos.Type.STRING, description="2-3 sentence role summary"),
                        "why_good_fit": genai.protos.Schema(type=genai.protos.Type.STRING, description="Why this is a good fit for the candidate"),
                    },
                    required=["title", "company", "url", "why_good_fit"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="save_target_company",
                description="Add a company to the watchlist for ongoing monitoring. Use when you find a company that seems like a great cultural/skills fit even if they don't have a specific opening right now.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "name": genai.protos.Schema(type=genai.protos.Type.STRING, description="Company name"),
                        "domain": genai.protos.Schema(type=genai.protos.Type.STRING, description="Company website domain (e.g., 'acme.com')"),
                        "careers_url": genai.protos.Schema(type=genai.protos.Type.STRING, description="URL of their careers/jobs page"),
                        "why_target": genai.protos.Schema(type=genai.protos.Type.STRING, description="Why this company is a good fit"),
                        "priority": genai.protos.Schema(type=genai.protos.Type.STRING, description="high, medium, or low"),
                    },
                    required=["name", "why_target", "priority"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="check_existing",
                description="Check what jobs and target companies are already being tracked. Call this early to avoid saving duplicates.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={},
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="done",
                description="Call when you've finished researching. Provide a summary of what you found.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "summary": genai.protos.Schema(
                            type=genai.protos.Type.STRING,
                            description="Brief summary of discoveries, patterns noticed, and suggestions for next run.",
                        ),
                    },
                    required=["summary"],
                ),
            ),
        ]
    )
]


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
    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        system_instruction=system_prompt,
        tools=SCOUT_TOOLS,
    )

    # Start the conversation with the candidate's profile
    initial_message = f"""Here is the candidate's professional profile from their knowledge base:

{profile_context}

---

Begin your research. Start by checking what's already tracked, then explore broadly.
Think about what kinds of companies and roles would be the best fit for this candidate,
and then go find them. Remember to follow leads and dig deeper into promising threads."""

    chat = model.start_chat()
    tool_calls_made = 0
    leads_saved = 0
    companies_saved = 0
    agent_done = False

    logger.info("scout.loop.start", max_tools=MAX_TOOL_CALLS)

    # ── Agentic loop ───────────────────────────────────────────
    response = await chat.send_message_async(initial_message)

    while tool_calls_made < MAX_TOOL_CALLS and not agent_done:
        # Check if the model wants to call tools
        if not response.candidates or not response.candidates[0].content.parts:
            logger.info("scout.loop.no_response")
            break

        # Process each part of the response
        tool_responses = []
        has_function_call = False

        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call.name:
                has_function_call = True
                fn_name = part.function_call.name
                fn_args = dict(part.function_call.args) if part.function_call.args else {}

                logger.info("scout.tool_call", tool=fn_name, args_keys=list(fn_args.keys()))

                # Handle the "done" tool specially
                if fn_name == "done":
                    summary = fn_args.get("summary", "No summary provided.")
                    logger.info("scout.done", summary=summary)
                    agent_done = True
                    tool_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name="done",
                                response={"result": "Session complete."},
                            )
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
                    if fn_name == "save_lead" and "✅" in result:
                        leads_saved += 1
                    elif fn_name == "save_target_company" and "✅" in result:
                        companies_saved += 1

                    tool_calls_made += 1
                    logger.info("scout.tool_result", tool=fn_name, result_preview=result[:100], calls=tool_calls_made)

                    tool_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=fn_name,
                                response={"result": result},
                            )
                        )
                    )
                else:
                    tool_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=fn_name,
                                response={"result": f"Unknown tool: {fn_name}"},
                            )
                        )
                    )
            elif hasattr(part, "text") and part.text:
                # The model is thinking out loud — log it
                logger.info("scout.thinking", text=part.text[:200])

        if agent_done:
            break

        if not has_function_call:
            # Model stopped calling tools — prompt it to continue or finish
            logger.info("scout.no_tools_called", message="Model stopped calling tools")
            try:
                response = await chat.send_message_async(
                    "Continue researching or call the `done` tool if you're finished."
                )
            except Exception as e:
                logger.error("scout.continue_error", error=str(e))
                break
            continue

        # Send tool results back to the model
        if tool_responses:
            try:
                response = await chat.send_message_async(
                    genai.protos.Content(parts=tool_responses)
                )
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
