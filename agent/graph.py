"""LangGraph agent graph definition."""

import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from agent.state import AgentState
from agent.tools.material import analyze_material
from agent.tools.stockfish import stockfish_eval
from agent.tools.tactics import find_tactics
from agent.tools.validator import validate_position

load_dotenv()


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def node_validate(state: AgentState) -> dict:
    result = validate_position(state["fen"])
    return {"validation": result}


def node_material(state: AgentState) -> dict:
    result = analyze_material(state["fen"])
    return {"material": result}


def node_stockfish(state: AgentState) -> dict:
    depth = state.get("depth", 15)
    result = stockfish_eval(state["fen"], depth=depth)
    return {"stockfish": result}


def node_tactics(state: AgentState) -> dict:
    result = find_tactics(state["fen"])
    return {"tactics": result}


def node_explain(state: AgentState) -> dict:
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.environ["ANTHROPIC_API_KEY"],
    )

    prompt = _build_prompt(state)
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"explanation": response.content}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def route_after_validation(state: AgentState) -> str:
    if not state["validation"]["valid"]:
        return END
    return "material"


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(state: AgentState) -> str:
    v = state["validation"]
    m = state["material"]
    s = state["stockfish"]
    t = state["tactics"]

    score = (
        f"mate in {s['score_mate']}" if s.get("score_mate") is not None
        else f"{s['score_cp']} centipawns" if s.get("score_cp") is not None
        else "unavailable"
    )
    best_move = s.get("best_move") or "unavailable"

    forks = t.get("forks", [])
    pins = t.get("pins", [])
    skewers = t.get("skewers", [])
    discoveries = t.get("discovered_attacks", [])
    mate_in = t.get("mate_in")

    return f"""You are a chess coach. Analyze the following position and explain it clearly to a club-level player.

Position (FEN): {state['fen']}
Turn: {v['turn']}
Game status: {v['status']}

Material balance: {m['balance']} centipawns (positive = white ahead)
White pieces: {m['white']}
Black pieces: {m['black']}
Pawn structure — white: {m['pawn_structure']['white']}
Pawn structure — black: {m['pawn_structure']['black']}

Stockfish evaluation: {score} (from the perspective of the side to move)
Best move according to engine: {best_move}

Tactical motifs found:
- Forks: {forks if forks else 'none'}
- Pins: {pins if pins else 'none'}
- Skewers: {skewers if skewers else 'none'}
- Discovered attacks: {discoveries if discoveries else 'none'}
- Forced mate in: {mate_in if mate_in else 'none found'}

Write a concise analysis (3–5 sentences) covering:
1. Who stands better and why
2. Key tactical or structural features
3. The recommended move and the idea behind it
"""


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("validate", node_validate)
    graph.add_node("material", node_material)
    graph.add_node("stockfish", node_stockfish)
    graph.add_node("tactics", node_tactics)
    graph.add_node("explain", node_explain)

    graph.set_entry_point("validate")

    graph.add_conditional_edges("validate", route_after_validation)
    graph.add_edge("material", "stockfish")
    graph.add_edge("stockfish", "tactics")
    graph.add_edge("tactics", "explain")
    graph.add_edge("explain", END)

    return graph.compile()
