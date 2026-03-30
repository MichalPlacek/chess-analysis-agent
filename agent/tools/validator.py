"""FEN position validation tool."""

import chess


def validate_position(fen: str) -> dict:
    """Validate a FEN string and return position details.

    Args:
        fen: FEN string representing a chess position.

    Returns:
        Dict with keys: valid, error, turn, status, fen.
    """
    try:
        board = chess.Board(fen)
    except ValueError as e:
        return {
            "valid": False,
            "error": str(e),
            "turn": None,
            "status": None,
            "fen": fen,
        }

    status = _get_game_status(board)

    return {
        "valid": True,
        "error": None,
        "turn": "white" if board.turn == chess.WHITE else "black",
        "status": status,
        "fen": fen,
    }


def _get_game_status(board: chess.Board) -> str:
    """Determine the current game status."""
    if board.is_checkmate():
        winner = "black" if board.turn == chess.WHITE else "white"
        return f"checkmate — {winner} wins"
    if board.is_stalemate():
        return "stalemate"
    if board.is_insufficient_material():
        return "draw — insufficient material"
    if board.is_check():
        return "check"
    return "in progress"
