"""Material count and pawn structure analysis tool."""

import chess


# Standard piece values in centipawns
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


def analyze_material(fen: str) -> dict:
    """Count material and analyze pawn structure for both sides.

    Args:
        fen: FEN string representing a chess position.

    Returns:
        Dict with keys: white, black, balance, pawn_structure.
        Each side has piece counts and total centipawn value.
        balance is positive when white is ahead.
    """
    try:
        board = chess.Board(fen)
    except ValueError as e:
        return {"error": str(e)}

    white = _count_material(board, chess.WHITE)
    black = _count_material(board, chess.BLACK)
    balance = white["total"] - black["total"]
    pawn_structure = _analyze_pawn_structure(board)

    return {
        "white": white,
        "black": black,
        "balance": balance,
        "pawn_structure": pawn_structure,
    }


def _count_material(board: chess.Board, color: chess.Color) -> dict:
    """Count pieces and compute total centipawn value for one side."""
    counts = {
        "pawns": len(board.pieces(chess.PAWN, color)),
        "knights": len(board.pieces(chess.KNIGHT, color)),
        "bishops": len(board.pieces(chess.BISHOP, color)),
        "rooks": len(board.pieces(chess.ROOK, color)),
        "queens": len(board.pieces(chess.QUEEN, color)),
    }
    total = (
        counts["pawns"] * PIECE_VALUES[chess.PAWN]
        + counts["knights"] * PIECE_VALUES[chess.KNIGHT]
        + counts["bishops"] * PIECE_VALUES[chess.BISHOP]
        + counts["rooks"] * PIECE_VALUES[chess.ROOK]
        + counts["queens"] * PIECE_VALUES[chess.QUEEN]
    )
    return {**counts, "total": total}


def _analyze_pawn_structure(board: chess.Board) -> dict:
    """Detect doubled, isolated, and passed pawns for both sides."""
    return {
        "white": _pawn_structure_for_color(board, chess.WHITE),
        "black": _pawn_structure_for_color(board, chess.BLACK),
    }


def _pawn_structure_for_color(board: chess.Board, color: chess.Color) -> dict:
    """Return doubled, isolated, and passed pawn squares for one side."""
    pawn_squares = list(board.pieces(chess.PAWN, color))
    files = [chess.square_file(sq) for sq in pawn_squares]

    doubled = _find_doubled(pawn_squares, files)
    isolated = _find_isolated(pawn_squares, files)
    passed = _find_passed(board, pawn_squares, color)

    return {
        "doubled": [chess.square_name(sq) for sq in doubled],
        "isolated": [chess.square_name(sq) for sq in isolated],
        "passed": [chess.square_name(sq) for sq in passed],
    }


def _find_doubled(pawn_squares: list, files: list) -> list:
    """Return squares of pawns that share a file with another friendly pawn."""
    doubled = []
    for sq, f in zip(pawn_squares, files):
        if files.count(f) > 1:
            doubled.append(sq)
    return doubled


def _find_isolated(pawn_squares: list, files: list) -> list:
    """Return squares of pawns with no friendly pawn on an adjacent file."""
    file_set = set(files)
    isolated = []
    for sq, f in zip(pawn_squares, files):
        neighbors = {f - 1, f + 1}
        if not neighbors & file_set:
            isolated.append(sq)
    return isolated


def _find_passed(board: chess.Board, pawn_squares: list, color: chess.Color) -> list:
    """Return squares of passed pawns (no opposing pawn can block or capture them)."""
    opponent = not color
    opponent_pawn_squares = list(board.pieces(chess.PAWN, opponent))
    opponent_files = {chess.square_file(sq) for sq in opponent_pawn_squares}

    passed = []
    for sq in pawn_squares:
        f = chess.square_file(sq)
        r = chess.square_rank(sq)
        adjacent_files = {f - 1, f, f + 1} & set(range(8))

        # Check if any opponent pawn is ahead of this pawn on adjacent files
        blocked = False
        for opp_sq in opponent_pawn_squares:
            opp_f = chess.square_file(opp_sq)
            opp_r = chess.square_rank(opp_sq)
            if opp_f not in adjacent_files:
                continue
            # "Ahead" depends on color
            if color == chess.WHITE and opp_r > r:
                blocked = True
                break
            if color == chess.BLACK and opp_r < r:
                blocked = True
                break

        if not blocked:
            passed.append(sq)

    return passed
