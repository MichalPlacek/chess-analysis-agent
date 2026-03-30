"""Streamlit UI for Chess Analysis Agent."""

import chess
import chess.svg
import streamlit as st
import streamlit.components.v1 as components  # noqa: F401

from agent.graph import build_graph

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

st.set_page_config(page_title="Chess Analysis Agent", layout="wide")
st.title("♟ Chess Analysis Agent")

# ---------------------------------------------------------------------------
# Sidebar — inputs
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Position")
    fen = st.text_input("FEN", value=STARTING_FEN)
    depth = st.slider("Stockfish depth", min_value=1, max_value=25, value=15)
    analyze = st.button("Analyze", type="primary")

# ---------------------------------------------------------------------------
# Board rendering
# ---------------------------------------------------------------------------

col_board, col_analysis = st.columns([1, 1])

with col_board:
    try:
        board = chess.Board(fen)
        svg = chess.svg.board(board, size=400)
        st.components.v1.html(svg, height=420)
    except ValueError:
        st.error("Invalid FEN — cannot render board.")

# ---------------------------------------------------------------------------
# Analysis panel
# ---------------------------------------------------------------------------

with col_analysis:
    if not analyze:
        st.info("Enter a FEN and click **Analyze**.")
        st.stop()

    with st.spinner("Analyzing..."):
        try:
            graph = build_graph()
            result = graph.invoke({"fen": fen, "depth": depth})
        except Exception as e:
            st.error(f"Agent error: {e}")
            st.stop()

    validation = result.get("validation", {})

    if not validation.get("valid"):
        st.error(f"Invalid position: {validation.get('error', 'unknown error')}")
        st.stop()

    # Material
    material = result.get("material", {})
    balance = material.get("balance", 0)
    balance_str = f"+{balance}" if balance > 0 else str(balance)
    st.subheader("📊 Material")
    st.write(f"Balance: **{balance_str} cp** ({'White' if balance >= 0 else 'Black'} ahead)")

    pw = material.get("white", {})
    pb = material.get("black", {})
    st.write(f"White: ♙×{pw.get('pawns',0)} ♘×{pw.get('knights',0)} ♗×{pw.get('bishops',0)} ♖×{pw.get('rooks',0)} ♕×{pw.get('queens',0)}")
    st.write(f"Black: ♟×{pb.get('pawns',0)} ♞×{pb.get('knights',0)} ♝×{pb.get('bishops',0)} ♜×{pb.get('rooks',0)} ♛×{pb.get('queens',0)}")

    pawn_w = material.get("pawn_structure", {}).get("white", {})
    pawn_b = material.get("pawn_structure", {}).get("black", {})
    if any(pawn_w.values()) or any(pawn_b.values()):
        st.write("**Pawn structure:**")
        for label, data in [("White", pawn_w), ("Black", pawn_b)]:
            issues = []
            if data.get("doubled"):
                issues.append(f"doubled: {', '.join(data['doubled'])}")
            if data.get("isolated"):
                issues.append(f"isolated: {', '.join(data['isolated'])}")
            if data.get("passed"):
                issues.append(f"passed: {', '.join(data['passed'])}")
            if issues:
                st.write(f"  {label}: {'; '.join(issues)}")

    # Stockfish
    stockfish = result.get("stockfish", {})
    st.subheader("🔢 Engine evaluation")
    if stockfish.get("error"):
        st.warning(f"Stockfish: {stockfish['error']}")
    else:
        if stockfish.get("score_mate") is not None:
            st.write(f"Score: **mate in {stockfish['score_mate']}**")
        elif stockfish.get("score_cp") is not None:
            cp = stockfish["score_cp"]
            st.write(f"Score: **{'+' if cp > 0 else ''}{cp} cp** (side to move)")
        if stockfish.get("best_move"):
            st.write(f"Best move: **{stockfish['best_move']}**")

    # Tactics
    tactics = result.get("tactics", {})
    st.subheader("💡 Tactics")
    found_any = False
    if tactics.get("mate_in"):
        st.write(f"🚨 **Mate in {tactics['mate_in']}!**")
        found_any = True
    if tactics.get("forks"):
        for f in tactics["forks"]:
            st.write(f"⚔️ Fork: **{f['move']}** — {f['piece']} attacks {', '.join(f['targets'])}")
            found_any = True
    if tactics.get("pins"):
        for p in tactics["pins"]:
            st.write(f"📌 Pin: {p['piece']} on **{p['square']}**")
            found_any = True
    if tactics.get("skewers"):
        for s in tactics["skewers"]:
            st.write(f"🗡️ Skewer: {s['attacker_piece']} on {s['attacker']} → {s['front_piece']} on {s['front']}")
            found_any = True
    if tactics.get("discovered_attacks"):
        for d in tactics["discovered_attacks"]:
            st.write(f"🔓 Discovered attack: **{d['move']}** reveals attack on {d['target_piece']} ({d['revealed_attack_on']})")
            found_any = True
    if not found_any:
        st.write("No tactical motifs found.")

    # Explanation
    st.subheader("🎯 Analysis")
    explanation = result.get("explanation", "")
    if explanation:
        st.write(explanation)
