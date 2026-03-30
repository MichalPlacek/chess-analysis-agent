"""Stockfish engine evaluation tool."""

import chess
import chess.engine


STOCKFISH_PATH = "/usr/bin/stockfish"
DEFAULT_DEPTH = 15


def stockfish_eval(fen: str, depth: int = DEFAULT_DEPTH) -> dict:
    """Evaluate a position using the Stockfish chess engine.

    Args:
        fen: FEN string representing a chess position.
        depth: Search depth for Stockfish analysis.

    Returns:
        Dict with keys: score_cp, score_mate, best_move, depth.
        score_cp is centipawns from the perspective of the side to move
        (positive = better for side to move).
        score_mate is moves-to-mate when Stockfish finds forced mate (else None).
        best_move is the engine's top choice in UCI notation.
    """
    try:
        board = chess.Board(fen)
    except ValueError as e:
        return {"error": f"Invalid FEN: {e}"}

    if board.is_game_over():
        return {
            "score_cp": None,
            "score_mate": None,
            "best_move": None,
            "depth": 0,
            "note": "game is already over",
        }

    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            result = engine.analyse(board, chess.engine.Limit(depth=depth))
    except FileNotFoundError:
        return {"error": f"Stockfish binary not found at {STOCKFISH_PATH}"}
    except chess.engine.EngineError as e:
        return {"error": f"Engine error: {e}"}

    score = result["score"].relative
    best_move = result.get("pv", [None])[0]

    return {
        "score_cp": score.score(),          # None when mate is on the board
        "score_mate": score.mate(),         # None when no forced mate
        "best_move": best_move.uci() if best_move else None,
        "depth": depth,
    }
