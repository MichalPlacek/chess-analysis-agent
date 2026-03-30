"""Agent state definition."""

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """Shared state passed between all nodes in the LangGraph agent."""

    # Input
    fen: str
    depth: int

    # Tool results
    validation: dict
    material: dict
    stockfish: dict
    tactics: dict

    # Final output
    explanation: str
