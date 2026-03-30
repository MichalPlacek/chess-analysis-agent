# Chess Analysis Agent

An LLM-powered agent that analyzes chess positions from FEN notation and explains them in natural language — with engine evaluation, tactical motif detection, and move suggestions.

Built as a portfolio project to demonstrate **LangGraph multi-step agent design**, external tool integration, and structured LLM output.

---

## What it does

1. You paste a FEN string (or use the starting position)
2. The agent runs it through a pipeline of specialized analysis tools
3. An LLM synthesizes all results into a clear, human-readable explanation

**Example output:**
> *"White is up a pawn (+1.2) with a strong passed pawn on d5. The knight on e5 is forking the black rook and queen — Nxd7 wins the exchange. Stockfish confirms: best move is Nxd7 (+3.1)."*

---

## Architecture

The agent is a **LangGraph state machine** — not a simple chain. Each node is an independent tool; conditional edges stop execution early if the position is invalid.

```
FEN input
    │
    ▼
validate_position   ← python-chess: legality check, turn, game status
    │
    ▼ (invalid → stop)
analyze_material    ← piece counts, material balance, pawn structure
    │
    ▼
stockfish_eval      ← Stockfish engine: centipawn score + best move
    │
    ▼
find_tactics        ← fork, pin, skewer, discovered attack, mate-in-N
    │
    ▼
generate_explanation ← LLM synthesizes all results → natural language
    │
    ▼
output
```

### Tools

| Tool | What it does |
|------|-------------|
| `validator.py` | Checks FEN legality via python-chess; returns turn, castling rights, game status |
| `material.py` | Counts piece values for both sides; detects doubled, isolated, and passed pawns |
| `stockfish.py` | Calls local Stockfish engine; returns centipawn evaluation and best move at configurable depth |
| `tactics.py` | Detects forks, pins, skewers, discovered attacks; finds mate-in-N up to N=3 |

The `generate_explanation` node passes all tool results to Claude and gets back a coherent, player-friendly analysis.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM integration | [LangChain](https://github.com/langchain-ai/langchain) + [langchain-anthropic](https://github.com/langchain-ai/langchain) |
| Language model | Claude (Anthropic API) |
| Chess engine | [Stockfish](https://stockfishchess.org/) |
| Chess logic | [python-chess](https://python-chess.readthedocs.io/) |
| Web UI | [Streamlit](https://streamlit.io/) |
| Environment | [Pixi](https://pixi.sh) |

---

## Project Structure

```
├── app.py                  # Streamlit entry point
├── agent/
│   ├── graph.py            # LangGraph graph: nodes, edges, routing logic
│   ├── state.py            # AgentState TypedDict — shared across all nodes
│   └── tools/
│       ├── validator.py    # FEN validation
│       ├── material.py     # Material balance & pawn structure
│       ├── stockfish.py    # Stockfish engine wrapper
│       └── tactics.py      # Tactical motif detection
├── tests/
│   ├── test_tools.py       # Unit tests for each tool
│   └── test_graph.py       # End-to-end graph tests
├── pyproject.toml          # Pixi config & dependencies
└── .env.example
```

---

## Setup

### Prerequisites

- [Pixi](https://pixi.sh) — dependency manager
- **Stockfish** — install via your system package manager:

  ```bash
  # Fedora/RHEL
  sudo dnf install stockfish

  # Ubuntu/Debian
  sudo apt install stockfish

  # macOS
  brew install stockfish
  ```

  Verify: `stockfish --help`

- An [Anthropic API key](https://console.anthropic.com/)

### Installation

```bash
# 1. Install Python dependencies
pixi install

# 2. Set up environment variables
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=your_key_here

# 3. Run the app
pixi run streamlit run app.py
```

### Running tests

```bash
pixi run pytest tests/
```

---

## Example FEN positions

```
# Starting position
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1

# Knight fork opportunity
r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4

# Fool's mate (mate in 1)
r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 0 1
```

---

## What this project demonstrates

- **Multi-step agent design** with LangGraph — conditional edges, early termination, shared state
- **Tool use** — integrating an external program (Stockfish) as an agent tool alongside pure Python logic
- **Structured LLM output** — using the LLM as a synthesis layer on top of deterministic tool results, not as the sole source of truth
- **Testable architecture** — every tool is a pure function (FEN in, dict out), independently unit-testable
- **Real, verifiable output** — engine evaluations are objective; the LLM explanation can be cross-checked against Stockfish

---

## Possible extensions

- Load positions from PGN game notation
- Move-by-move analysis of a full game
- "Coach mode" — interactive Q&A about the position
- Lichess API integration — analyze any game by URL

---

## License

MIT. Stockfish is distributed under the [GPL v3 license](https://www.gnu.org/licenses/gpl-3.0.html).
