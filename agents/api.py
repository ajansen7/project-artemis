"""
FastAPI application — HTTP API for the Command Center frontend and Discord bot.
"""

from __future__ import annotations

import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.nodes.analyst import analyze_job as run_analyst

app = FastAPI(
    title="Project Artemis API",
    description="Multi-agent orchestration API for job hunting automation",
    version="0.1.0",
)

# ─── CORS (allow Next.js dev server) ────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response Models ──────────────────────────────────


class AnalyzeJobRequest(BaseModel):
    """Request to analyze a job posting."""

    job_url: str | None = None
    job_description_md: str | None = None


class AnalyzeJobResponse(BaseModel):
    """Response from the Analyst agent."""

    job_id: str | None = None
    match_score: int
    matched_requirements: list[str] = []
    gaps: list[dict] = []
    recommended_actions: list[str] = []


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


# ─── Routes ─────────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Service health check."""
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/api/analyze", response_model=AnalyzeJobResponse)
async def analyze_job(request: AnalyzeJobRequest) -> AnalyzeJobResponse:
    """Submit a job for analysis.

    Accepts either a job URL (which will be scraped) or raw JD markdown.
    Returns match score, gaps, and recommendations.
    """
    if not request.job_url and not request.job_description_md:
        raise HTTPException(
            status_code=400,
            detail="Provide either job_url or job_description_md",
        )

    # Build initial state dict for the analyst node
    initial_state: dict = {}
    if request.job_url:
        initial_state["job_url"] = request.job_url
    if request.job_description_md:
        initial_state["job_description_md"] = request.job_description_md

    try:
        result = await run_analyst(initial_state)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    match_result = result.get("match_result")
    if not match_result:
        raise HTTPException(status_code=500, detail="Analysis failed to produce results")

    # match_result is a MatchResult pydantic model
    return AnalyzeJobResponse(
        job_id=result.get("job_id"),
        match_score=match_result.match_score,
        matched_requirements=match_result.matched_requirements or [],
        gaps=[g.model_dump() if hasattr(g, "model_dump") else g for g in (match_result.gaps or [])],
        recommended_actions=match_result.recommended_actions or [],
    )


# ─── Embed endpoint (for HITL anecdote capture) ────────────────


class EmbedRequest(BaseModel):
    """Request to embed text into the vector knowledge base."""
    text: str
    source: str
    content_type: str = "anecdote"
    tags: list[str] = []


class EmbedResponse(BaseModel):
    chunks: int


@app.post("/api/embed", response_model=EmbedResponse)
async def embed_text(request: EmbedRequest) -> EmbedResponse:
    """Embed new text into the ChromaDB vector store."""
    try:
        from ingestion.embedder import embed_and_store
        chunks = await embed_and_store(
            text=request.text,
            source=request.source,
            content_type=request.content_type,
            tags=request.tags,
        )
        return EmbedResponse(chunks=chunks)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")


# ─── Scout endpoint ────────────────────────────────────────────


class ScoutResponse(BaseModel):
    scouted_count: int
    message: str


@app.post("/api/scout", response_model=ScoutResponse)
async def run_scout() -> ScoutResponse:
    """Trigger the Scout Agent to discover new jobs."""
    try:
        from agents.nodes.scout import scout_jobs
        result = await scout_jobs({})
        count = result.get("scouted_count", 0)
        return ScoutResponse(
            scouted_count=count,
            message=f"Scouted {count} new job(s)",
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Scout failed: {e}")
