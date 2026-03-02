"""
Project Artemis — LangGraph StateGraph definition.

This is the main orchestration graph. Each node is a specialized agent
that reads from and writes to the shared AgentState.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from agents.nodes.analyst import analyze_job
from agents.nodes.orchestrator import route_next_action, review_gaps
from agents.state import AgentAction, AgentState


def build_graph() -> StateGraph:
    """Construct and compile the Artemis agent graph.

    Flow (Phase 1 — MVP):
        START → analyze_job → review_gaps (HITL interrupt) → route
            ├─ suggest_growth → END
            ├─ create_artifacts → END
            └─ done → END
    """
    graph = StateGraph(AgentState)

    # ── Nodes ───────────────────────────────────────────────────
    graph.add_node("analyze_job", analyze_job)
    graph.add_node("review_gaps", review_gaps)

    # ── Edges ───────────────────────────────────────────────────
    graph.set_entry_point("analyze_job")
    graph.add_edge("analyze_job", "review_gaps")

    # Conditional routing after HITL review
    graph.add_conditional_edges(
        "review_gaps",
        route_next_action,
        {
            AgentAction.SUGGEST_GROWTH: END,  # Phase 1: just log suggestion
            AgentAction.CREATE_ARTIFACTS: END,  # Phase 1: placeholder
            AgentAction.DONE: END,
        },
    )

    return graph.compile()


# Pre-compiled graph instance
artemis_graph = build_graph()
