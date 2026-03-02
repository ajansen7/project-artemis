"""
Diplomat Agent — communication tracking and follow-up drafting.

Integrates with Gmail (OAuth, read + drafts-only) to monitor recruiter
responses, log status changes, and draft follow-up emails.
"""

from __future__ import annotations

import structlog

from agents.state import AgentState

logger = structlog.get_logger()


async def draft_followup(state: AgentState) -> AgentState:
    """Monitor inbox and draft follow-up emails.

    Phase 3 implementation:
        1. Authenticate via Gmail OAuth (read + compose/drafts scope).
        2. Monitor inbox for emails matching tracked company domains.
        3. Log status changes to Supabase CRM.
        4. After 7 days of silence, draft follow-up → Gmail Drafts.
        5. Ping user for review before sending.
    """
    logger.info("diplomat.start", job_id=state.get("job_id"))

    # TODO: Implement in Phase 3
    # - Gmail API authentication
    # - Inbox monitoring
    # - Follow-up drafting
    # - Draft placement in Gmail

    logger.info("diplomat.complete")
    return state
