"""Tactical motif detection tool using python-chess."""

import chess


# Piece values used to judge whether a target is "valuable enough"
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 9999,
}

FORK_MIN_TARGETS = 2
FORK_MIN_TARGET_VALUE = 300  # ignore pawns as fork targets


def find_tactics(fen: str) -> dict:
    """Detect tactical motifs in a position.

    Args:
        fen: FEN string representing a chess position.

    Returns:
        Dict with keys: forks, pins, skewers, discovered_attacks, mate_in.
        mate_in is None when no forced mate is found within 3 moves.
    """
    try:
        board = chess.Board(fen)
    except ValueError as e:
        return {"error": f"Invalid FEN: {e}"}

    return {
        "forks": _find_forks(board),
        "pins": _find_pins(board),
        "skewers": _find_skewers(board),
        "discovered_attacks": _find_discovered_attacks(board),
        "mate_in": _find_mate_in(board, max_depth=3),
    }


# ---------------------------------------------------------------------------
# Fork detection
# ---------------------------------------------------------------------------

def _find_forks(board: chess.Board) -> list[dict]:
    """Find moves that fork two or more valuable opponent pieces."""
    side = board.turn
    opponent = not side
    results = []

    for move in board.legal_moves:
        board.push(move)
        attacker_sq = move.to_square
        piece = board.piece_at(attacker_sq)
        if piece and piece.color == side:
            attacked = [
                sq for sq in board.attacks(attacker_sq)
                if board.piece_at(sq) is not None
                and board.piece_at(sq).color == opponent
                and PIECE_VALUES[board.piece_at(sq).piece_type] >= FORK_MIN_TARGET_VALUE
            ]
            if len(attacked) >= FORK_MIN_TARGETS:
                results.append({
                    "move": move.uci(),
                    "piece": piece.symbol().upper(),
                    "targets": [chess.square_name(sq) for sq in attacked],
                })
        board.pop()

    return results


# ---------------------------------------------------------------------------
# Pin detection
# ---------------------------------------------------------------------------

def _find_pins(board: chess.Board) -> list[dict]:
    """Find opponent pieces that are pinned against their king."""
    opponent = not board.turn
    results = []

    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece and piece.color == opponent:
            if board.is_pinned(opponent, sq):
                pin_ray = board.pin(opponent, sq)
                results.append({
                    "square": chess.square_name(sq),
                    "piece": piece.symbol().upper(),
                    "pin_ray": _ray_to_squares(pin_ray),
                })

    return results


def _ray_to_squares(ray: chess.SquareSet) -> list[str]:
    return [chess.square_name(sq) for sq in ray]


# ---------------------------------------------------------------------------
# Skewer detection
# ---------------------------------------------------------------------------

def _find_skewers(board: chess.Board) -> list[dict]:
    """Find skewers: a valuable piece is attacked, and a lesser piece hides behind it."""
    side = board.turn
    opponent = not side
    results = []

    sliding_types = {chess.BISHOP, chess.ROOK, chess.QUEEN}

    for attacker_sq in board.pieces(chess.BISHOP, side) | board.pieces(chess.ROOK, side) | board.pieces(chess.QUEEN, side):
        attacker = board.piece_at(attacker_sq)
        for ray in _get_rays(attacker_sq, attacker.piece_type):
            pieces_on_ray = [sq for sq in ray if board.piece_at(sq) is not None]
            if len(pieces_on_ray) < 2:
                continue
            front_sq = pieces_on_ray[0]
            back_sq = pieces_on_ray[1]
            front_piece = board.piece_at(front_sq)
            back_piece = board.piece_at(back_sq)
            if front_piece.color != opponent or back_piece.color != opponent:
                continue
            if (PIECE_VALUES[front_piece.piece_type] > PIECE_VALUES[back_piece.piece_type]
                    and PIECE_VALUES[front_piece.piece_type] >= PIECE_VALUES[chess.ROOK]):
                results.append({
                    "attacker": chess.square_name(attacker_sq),
                    "attacker_piece": attacker.symbol().upper(),
                    "front": chess.square_name(front_sq),
                    "front_piece": front_piece.symbol().upper(),
                    "back": chess.square_name(back_sq),
                    "back_piece": back_piece.symbol().upper(),
                })

    return results


def _get_rays(square: chess.Square, piece_type: chess.PieceType) -> list[list[chess.Square]]:
    """Return directional rays from a square for sliding pieces."""
    rays = []
    if piece_type in {chess.ROOK, chess.QUEEN}:
        for delta in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            rays.append(_ray_in_direction(square, delta))
    if piece_type in {chess.BISHOP, chess.QUEEN}:
        for delta in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            rays.append(_ray_in_direction(square, delta))
    return [r for r in rays if r]


def _ray_in_direction(square: chess.Square, delta: tuple[int, int]) -> list[chess.Square]:
    """Walk from square in a direction, returning all squares until board edge."""
    squares = []
    f, r = chess.square_file(square), chess.square_rank(square)
    df, dr = delta
    f, r = f + df, r + dr
    while 0 <= f <= 7 and 0 <= r <= 7:
        squares.append(chess.square(f, r))
        f, r = f + df, r + dr
    return squares


# ---------------------------------------------------------------------------
# Discovered attack detection
# ---------------------------------------------------------------------------

def _find_discovered_attacks(board: chess.Board) -> list[dict]:
    """Find moves that uncover an attack by a piece behind the moving piece."""
    side = board.turn
    opponent = not side
    results = []

    for move in board.legal_moves:
        from_sq = move.from_square
        # Collect attacks on opponent pieces before the move
        attacks_before = _attacked_opponent_squares(board, side, opponent)

        board.push(move)
        attacks_after = _attacked_opponent_squares(board, side, opponent)
        board.pop()

        # New attacks that weren't there before, not on squares the moving piece attacks
        moving_piece_attacks = board.attacks(move.to_square) if board.piece_at(move.to_square) else chess.SquareSet()
        new_attacks = attacks_after - attacks_before

        # Filter: only count if the newly attacked square is not attacked by the moved piece itself
        board.push(move)
        moved_piece_attacks = board.attacks(move.to_square)
        discovered = new_attacks - moved_piece_attacks
        board.pop()

        for target_sq in discovered:
            target = board.piece_at(target_sq)
            if target and PIECE_VALUES[target.piece_type] >= PIECE_VALUES[chess.KNIGHT]:
                results.append({
                    "move": move.uci(),
                    "revealed_attack_on": chess.square_name(target_sq),
                    "target_piece": target.symbol().upper(),
                })

    return results


def _attacked_opponent_squares(board: chess.Board, side: chess.Color, opponent: chess.Color) -> chess.SquareSet:
    """Return all squares occupied by opponent pieces that are attacked by side."""
    attacked = chess.SquareSet()
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece and piece.color == opponent:
            if board.is_attacked_by(side, sq):
                attacked.add(sq)
    return attacked


# ---------------------------------------------------------------------------
# Mate-in-N detection (up to depth 3)
# ---------------------------------------------------------------------------

def _find_mate_in(board: chess.Board, max_depth: int = 3) -> int | None:
    """Return N if there is a forced mate in N moves, else None."""
    for depth in range(1, max_depth + 1):
        if _is_mate_in_n(board, depth):
            return depth
    return None


def _is_mate_in_n(board: chess.Board, n: int) -> bool:
    """Return True if the side to move can force mate in exactly n moves."""
    if n == 0:
        return board.is_checkmate()

    for move in board.legal_moves:
        board.push(move)
        if _opponent_gets_mated(board, n - 1):
            board.pop()
            return True
        board.pop()

    return False


def _opponent_gets_mated(board: chess.Board, remaining: int) -> bool:
    """Return True if the opponent (now to move) cannot escape mate in remaining moves."""
    if board.is_checkmate():
        return True
    if remaining == 0:
        return False
    if board.is_game_over():
        return False

    # Opponent must be mated regardless of their response
    for move in board.legal_moves:
        board.push(move)
        can_escape = not _is_mate_in_n(board, remaining)
        board.pop()
        if can_escape:
            return False

    return True
