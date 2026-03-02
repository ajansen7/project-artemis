"""
Orchestrator — manages workflow routing and HITL interactions.

The orchestrator is not an LLM-powered agent itself; it's the control
flow logic that decides which agent to invoke next based on the current
AgentState. HITL interrupts happen in `review_gaps`.
"""

from __future__ import annotations

from langgraph.types import interrupt

from agents.state import AgentAction, AgentState


def review_gaps(state: AgentState) -> AgentState:
    """Present gap analysis to the user and collect feedback.

    This node uses LangGraph's `interrupt()` to pause execution and
    wait for human input before continuing.
    """
    match_result = state.get("match_result")
    if not match_result or not match_result.gaps:
        # No gaps found — proceed directly
        return {
            "next_action": AgentAction.DONE,
            "user_has_anecdote": None,
        }

    # Build a summary of gaps for the user
    gap_summary = "\n".join(
        f"- [{g.severity.upper()}] {g.requirement}: {g.suggestion}"
        for g in match_result.gaps
    )

    # Pause and wait for human input
    human_response = interrupt(
        f"Match Score: {match_result.match_score}/100\n\n"
        f"Identified Gaps:\n{gap_summary}\n\n"
        "Do you have an existing anecdote for any of these gaps? "
        "Reply with the anecdote, or say 'no' to get growth suggestions."
    )

    # Process the human's response
    has_anecdote = human_response.lower().strip() != "no"

    return {
        "human_feedback": human_response,
        "user_has_anecdote": has_anecdote,
        "next_action": (
            AgentAction.CREATE_ARTIFACTS if has_anecdote else AgentAction.SUGGEST_GROWTH
        ),
    }


def route_next_action(state: AgentState) -> AgentAction:
    """Conditional edge function — returns the next node to visit."""
    return state.get("next_action", AgentAction.DONE)
