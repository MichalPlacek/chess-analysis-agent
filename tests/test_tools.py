"""Unit tests for chess analysis tools."""

import os
import pytest

from agent.tools.validator import validate_position
from agent.tools.material import analyze_material
from agent.tools.stockfish import stockfish_eval, STOCKFISH_PATH
from agent.tools.tactics import find_tactics

# ---------------------------------------------------------------------------
# Shared FEN constants
# ---------------------------------------------------------------------------

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
INVALID_FEN = "not_a_fen"
# Fool's mate — black just played, white is checkmated
FOOLS_MATE_FEN = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
# White queen removed — material imbalance
WHITE_QUEEN_GONE_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1"
# Knight fork: white knight on d5 can jump to c7, forking black rook (a8) and king (e8)
KNIGHT_FORK_FEN = "r3k3/8/8/3N4/8/8/8/4K3 w - - 0 1"
# Back-rank mate: white rook on a1 can play Ra8#
MATE_IN_1_FEN = "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1"
# Pin: white to move, black knight on c6 pinned against black king (e8) by white bishop (b5)
PIN_FEN = "4k3/8/2n5/1B6/8/8/8/4K3 w - - 0 1"

STOCKFISH_AVAILABLE = os.path.isfile(STOCKFISH_PATH)


# ===========================================================================
# validate_position
# ===========================================================================

class TestValidatePosition:
    def test_starting_position_is_valid(self):
        result = validate_position(STARTING_FEN)
        assert result["valid"] is True
        assert result["error"] is None
        assert result["turn"] == "white"
        assert result["status"] == "in progress"

    def test_invalid_fen_returns_error(self):
        result = validate_position(INVALID_FEN)
        assert result["valid"] is False
        assert result["error"] is not None
        assert result["turn"] is None
        assert result["status"] is None

    def test_checkmate_position_detected(self):
        result = validate_position(FOOLS_MATE_FEN)
        assert result["valid"] is True
        assert "checkmate" in result["status"]

    def test_fen_preserved_in_output(self):
        result = validate_position(STARTING_FEN)
        assert result["fen"] == STARTING_FEN

    def test_black_to_move(self):
        # After 1. e4 it is black's turn
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        result = validate_position(fen)
        assert result["valid"] is True
        assert result["turn"] == "black"

    def test_check_status_detected(self):
        # White king in check from black rook
        fen = "4k3/8/8/8/8/8/8/r3K3 w - - 0 1"
        result = validate_position(fen)
        assert result["valid"] is True
        assert result["status"] == "check"


# ===========================================================================
# analyze_material
# ===========================================================================

class TestAnalyzeMaterial:
    def test_starting_position_balanced(self):
        result = analyze_material(STARTING_FEN)
        assert result["balance"] == 0
        assert result["white"]["total"] == result["black"]["total"]

    def test_starting_position_piece_counts(self):
        result = analyze_material(STARTING_FEN)
        white = result["white"]
        assert white["pawns"] == 8
        assert white["knights"] == 2
        assert white["bishops"] == 2
        assert white["rooks"] == 2
        assert white["queens"] == 1

    def test_missing_white_queen_shows_deficit(self):
        result = analyze_material(WHITE_QUEEN_GONE_FEN)
        assert result["balance"] < 0
        assert result["white"]["queens"] == 0
        assert result["black"]["queens"] == 1

    def test_invalid_fen_returns_error(self):
        result = analyze_material(INVALID_FEN)
        assert "error" in result

    def test_pawn_structure_keys_present(self):
        result = analyze_material(STARTING_FEN)
        assert "pawn_structure" in result
        for side in ("white", "black"):
            ps = result["pawn_structure"][side]
            assert "doubled" in ps
            assert "isolated" in ps
            assert "passed" in ps

    def test_passed_pawns_detected(self):
        # White pawn on e5, no black pawns on d or f files
        fen = "4k3/8/8/4P3/8/8/8/4K3 w - - 0 1"
        result = analyze_material(fen)
        assert len(result["pawn_structure"]["white"]["passed"]) > 0


# ===========================================================================
# stockfish_eval
# ===========================================================================

@pytest.mark.skipif(not STOCKFISH_AVAILABLE, reason="Stockfish not installed")
class TestStockfishEval:
    def test_returns_expected_keys(self):
        result = stockfish_eval(STARTING_FEN, depth=5)
        assert "score_cp" in result
        assert "best_move" in result
        assert "depth" in result

    def test_best_move_is_uci_string(self):
        result = stockfish_eval(STARTING_FEN, depth=5)
        assert isinstance(result["best_move"], str)
        assert len(result["best_move"]) in (4, 5)  # e.g. "e2e4" or "e7e8q"

    def test_game_over_position_returns_note(self):
        result = stockfish_eval(FOOLS_MATE_FEN, depth=5)
        assert result.get("note") == "game is already over"
        assert result["best_move"] is None

    def test_invalid_fen_returns_error(self):
        result = stockfish_eval(INVALID_FEN)
        assert "error" in result

    def test_depth_preserved_in_output(self):
        result = stockfish_eval(STARTING_FEN, depth=3)
        assert result["depth"] == 3


class TestStockfishEvalNoEngine:
    """Tests that run regardless of Stockfish availability."""

    def test_invalid_fen_returns_error(self):
        result = stockfish_eval(INVALID_FEN)
        assert "error" in result

    def test_game_over_returns_note_without_engine(self):
        # Game-over check happens before engine is called
        result = stockfish_eval(FOOLS_MATE_FEN)
        assert result.get("note") == "game is already over"


# ===========================================================================
# find_tactics
# ===========================================================================

class TestFindTactics:
    def test_returns_expected_keys(self):
        result = find_tactics(STARTING_FEN)
        for key in ("forks", "pins", "skewers", "discovered_attacks", "mate_in"):
            assert key in result

    def test_no_tactics_in_starting_position(self):
        result = find_tactics(STARTING_FEN)
        assert result["forks"] == []
        assert result["mate_in"] is None

    def test_invalid_fen_returns_error(self):
        result = find_tactics(INVALID_FEN)
        assert "error" in result

    def test_knight_fork_detected(self):
        result = find_tactics(KNIGHT_FORK_FEN)
        assert len(result["forks"]) > 0
        fork = result["forks"][0]
        assert "move" in fork
        assert "targets" in fork
        assert len(fork["targets"]) >= 2

    def test_mate_in_1_detected(self):
        result = find_tactics(MATE_IN_1_FEN)
        assert result["mate_in"] == 1

    def test_pin_detected(self):
        result = find_tactics(PIN_FEN)
        assert len(result["pins"]) > 0
        pin = result["pins"][0]
        assert "square" in pin
        assert "piece" in pin
