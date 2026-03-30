"""End-to-end tests for the LangGraph agent."""

import os

import pytest

from agent.graph import build_graph

# Skip all tests in this module if ANTHROPIC_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
MATE_IN_1_FEN = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1"  # Re8#
INVALID_FEN = "not-a-fen"


@pytest.fixture(scope="module")
def graph():
    return build_graph()


class TestGraphEndToEnd:
    def test_starting_position_produces_explanation(self, graph):
        result = graph.invoke({"fen": STARTING_FEN, "depth": 10})
        assert result["validation"]["valid"] is True
        assert isinstance(result["explanation"], str)
        assert len(result["explanation"]) > 50

    def test_invalid_fen_stops_early(self, graph):
        result = graph.invoke({"fen": INVALID_FEN})
        assert result["validation"]["valid"] is False
        assert "explanation" not in result or result.get("explanation") is None

    def test_mate_in_1_position(self, graph):
        result = graph.invoke({"fen": MATE_IN_1_FEN, "depth": 15})
        assert result["validation"]["valid"] is True
        assert result["stockfish"].get("score_mate") is not None or result["tactics"].get("mate_in") is not None
        assert isinstance(result["explanation"], str)
        assert len(result["explanation"]) > 50

    def test_result_contains_all_fields(self, graph):
        result = graph.invoke({"fen": STARTING_FEN, "depth": 10})
        assert "validation" in result
        assert "material" in result
        assert "stockfish" in result
        assert "tactics" in result
        assert "explanation" in result
