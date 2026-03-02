"""
Shared agent state definition for the LangGraph orchestrator.

All agents read from and write to this central TypedDict.
The Orchestrator manages routing based on state transitions.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# ─── Enums ──────────────────────────────────────────────────────


class JobStatus(str, Enum):
    """Pipeline status for a tracked job."""

    SCOUTED = "scouted"
    TO_REVIEW = "to_review"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    REJECTED = "rejected"
    OFFER = "offer"


class AgentAction(str, Enum):
    """Next action the orchestrator should route to."""

    ANALYZE = "analyze"
    CREATE_ARTIFACTS = "create_artifacts"
    FIND_CONTACTS = "find_contacts"
    DRAFT_FOLLOWUP = "draft_followup"
    SUGGEST_GROWTH = "suggest_growth"
    AWAIT_HUMAN = "await_human"
    DONE = "done"


# ─── Structured sub-models ──────────────────────────────────────


class GapItem(BaseModel):
    """A single identified gap between the user's profile and a JD."""

    requirement: str = Field(description="The JD requirement that is not fully met")
    severity: str = Field(description="high | medium | low")
    suggestion: str = Field(description="Recommended action to fill the gap")


class MatchResult(BaseModel):
    """Output of the Analyst agent's scoring."""

    match_score: int = Field(ge=0, le=100, description="Overall fit score 0-100")
    matched_requirements: list[str] = Field(
        default_factory=list,
        description="JD requirements matched with evidence from the knowledge base",
    )
    gaps: list[GapItem] = Field(
        default_factory=list, description="Identified gaps with severity"
    )
    recommended_actions: list[str] = Field(
        default_factory=list, description="Suggested next steps"
    )


# ─── Central Agent State ────────────────────────────────────────


class AgentState(TypedDict, total=False):
    """Central state shared across all agents in the LangGraph graph.

    Fields are optional (total=False) so agents only write what they own.
    The `messages` field uses LangGraph's add_messages reducer for
    append-only chat history.
    """

    # ── Conversation history (append-only via reducer) ──────────
    messages: Annotated[list, add_messages]

    # ── Current job context ─────────────────────────────────────
    job_url: str
    job_description_md: str
    job_id: str  # Supabase UUID after insertion

    # ── Analyst output ──────────────────────────────────────────
    match_result: MatchResult

    # ── Artisan output ──────────────────────────────────────────
    resume_path: str
    cover_letter_path: str

    # ── Networker output ────────────────────────────────────────
    contacts: list[dict]

    # ── Diplomat output ─────────────────────────────────────────
    followup_draft: str

    # ── HITL ────────────────────────────────────────────────────
    human_feedback: str  # free-text response from user
    user_has_anecdote: bool | None

    # ── Routing ─────────────────────────────────────────────────
    next_action: AgentAction
