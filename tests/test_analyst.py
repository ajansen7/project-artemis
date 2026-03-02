"""
Tests for the Analyst agent.
"""

from __future__ import annotations

import pytest

from agents.state import MatchResult, GapItem, AgentAction


class TestMatchResult:
    """Test the MatchResult Pydantic model."""

    def test_valid_match_result(self) -> None:
        result = MatchResult(
            match_score=85,
            matched_requirements=["Python experience — Evidence: github:random"],
            gaps=[
                GapItem(
                    requirement="LLM orchestration experience",
                    severity="medium",
                    suggestion="Build a LangGraph project",
                )
            ],
            recommended_actions=["Apply with emphasis on AI projects"],
        )
        assert result.match_score == 85
        assert len(result.gaps) == 1
        assert result.gaps[0].severity == "medium"

    def test_score_validation(self) -> None:
        with pytest.raises(ValueError):
            MatchResult(match_score=101)

        with pytest.raises(ValueError):
            MatchResult(match_score=-1)

    def test_empty_result(self) -> None:
        result = MatchResult(match_score=0)
        assert result.matched_requirements == []
        assert result.gaps == []
        assert result.recommended_actions == []


class TestAgentAction:
    """Test the AgentAction enum."""

    def test_all_actions_exist(self) -> None:
        expected = {
            "analyze", "create_artifacts", "find_contacts",
            "draft_followup", "suggest_growth", "await_human", "done",
        }
        actual = {a.value for a in AgentAction}
        assert expected == actual
