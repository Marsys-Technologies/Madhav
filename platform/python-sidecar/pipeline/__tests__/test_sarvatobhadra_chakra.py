"""
test_sarvatobhadra_chakra.py — Tests for A17 Sarvatobhadra Chakra reference data.

Covers:
  1. Exactly 28 positions in SBC_POSITIONS
  2. nakshatra_ids are unique and in range 1-28
  3. grid positions (row, col) are unique — no two nakshatras share a cell
  4. All rows/cols in range 0-8
  5. side values all in {north, south, east, west}
  6. Exactly 14 vedha pairs in SBC_VEDHA_PAIRS
  7. No nakshatra appears in more than one vedha pair (vedha is exclusive)
  8. (DB) seed_sarvatobhadra() inserts 28 positions + 14 vedha pairs
  9. (DB) Second seed call inserts 0 rows (idempotency)

A17 [BUILD-ORCH-STREAM-C-A17-S1]
"""

import os
import pytest

from pipeline.sarvatobhadra_chakra import SBC_POSITIONS, SBC_VEDHA_PAIRS, seed_sarvatobhadra

# ---------------------------------------------------------------------------
# DB connection helper (mirrors test_g29_timing_rules.py pattern)
# ---------------------------------------------------------------------------

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DB_PORT", "5433")
DB_USER = os.environ.get("DB_USER", "amjis_app")
DB_PASS = os.environ.get("DB_PASS", "aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF")
DB_NAME = os.environ.get("DB_NAME", "amjis")


def _get_conn():
    """Return a psycopg2 connection, or raise if unavailable."""
    import psycopg2
    return psycopg2.connect(
        host=DB_HOST, port=int(DB_PORT), user=DB_USER,
        password=DB_PASS, dbname=DB_NAME,
        connect_timeout=3,
    )


def _db_reachable() -> bool:
    try:
        conn = _get_conn()
        conn.close()
        return True
    except Exception:
        return False


DB_AVAILABLE = _db_reachable()

# ---------------------------------------------------------------------------
# Test 1 — Exactly 28 positions
# ---------------------------------------------------------------------------

def test_sbc_positions_count():
    """SBC_POSITIONS must contain exactly 28 nakshatras (27 standard + Abhijit)."""
    assert len(SBC_POSITIONS) == 28, (
        f"Expected exactly 28 positions, got {len(SBC_POSITIONS)}"
    )


# ---------------------------------------------------------------------------
# Test 2 — nakshatra_ids unique and in range 1-28
# ---------------------------------------------------------------------------

def test_nakshatra_ids_unique_and_in_range():
    """nakshatra_id values must be unique and span exactly 1-28."""
    ids = [p["nakshatra_id"] for p in SBC_POSITIONS]
    assert len(ids) == len(set(ids)), "Duplicate nakshatra_id values found"
    assert set(ids) == set(range(1, 29)), (
        f"nakshatra_ids must be exactly 1-28, got: {sorted(ids)}"
    )


# ---------------------------------------------------------------------------
# Test 3 — grid (row, col) pairs unique
# ---------------------------------------------------------------------------

def test_grid_cells_unique():
    """No two nakshatras may occupy the same (grid_row, grid_col) cell."""
    cells = [(p["grid_row"], p["grid_col"]) for p in SBC_POSITIONS]
    assert len(cells) == len(set(cells)), (
        f"Duplicate grid cells found: "
        f"{[c for c in cells if cells.count(c) > 1]}"
    )


# ---------------------------------------------------------------------------
# Test 4 — row and col in range 0-8
# ---------------------------------------------------------------------------

def test_grid_bounds():
    """All grid_row and grid_col values must be in range 0-8."""
    for p in SBC_POSITIONS:
        assert 0 <= p["grid_row"] <= 8, (
            f"nakshatra '{p['nakshatra_name']}' has out-of-bounds row {p['grid_row']}"
        )
        assert 0 <= p["grid_col"] <= 8, (
            f"nakshatra '{p['nakshatra_name']}' has out-of-bounds col {p['grid_col']}"
        )


# ---------------------------------------------------------------------------
# Test 5 — side values from allowed set
# ---------------------------------------------------------------------------

ALLOWED_SIDES = {"north", "south", "east", "west"}


def test_side_values():
    """All side values must be in {north, south, east, west}."""
    for p in SBC_POSITIONS:
        assert p["side"] in ALLOWED_SIDES, (
            f"nakshatra '{p['nakshatra_name']}' has invalid side '{p['side']}'"
        )


# ---------------------------------------------------------------------------
# Test 6 — Exactly 14 vedha pairs
# ---------------------------------------------------------------------------

def test_vedha_pairs_count():
    """SBC_VEDHA_PAIRS must contain exactly 14 vedha pairs."""
    assert len(SBC_VEDHA_PAIRS) == 14, (
        f"Expected exactly 14 vedha pairs, got {len(SBC_VEDHA_PAIRS)}"
    )


# ---------------------------------------------------------------------------
# Test 7 — No nakshatra in more than one vedha pair
# ---------------------------------------------------------------------------

def test_vedha_exclusivity():
    """Each nakshatra must appear in at most one vedha pair."""
    from collections import Counter
    appearances: list[int] = []
    for pair in SBC_VEDHA_PAIRS:
        appearances.append(pair["nakshatra_1_id"])
        appearances.append(pair["nakshatra_2_id"])
    counts = Counter(appearances)
    duplicates = {nid: cnt for nid, cnt in counts.items() if cnt > 1}
    assert not duplicates, (
        f"Nakshatras appearing in multiple vedha pairs: {duplicates}"
    )


# ---------------------------------------------------------------------------
# Test 8 (DB) — seed inserts 28 + 14 rows
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not DB_AVAILABLE, reason="DB not reachable at 127.0.0.1:5433")
def test_seed_inserts_correct_counts():
    """seed_sarvatobhadra() must insert exactly 28 positions and 14 vedha pairs."""
    conn = _get_conn()
    try:
        # Clear any previous seed data for a clean test
        with conn.cursor() as cur:
            cur.execute("DELETE FROM l1_sarvatobhadra_vedha")
            cur.execute("DELETE FROM l1_sarvatobhadra_positions")
            conn.commit()

        pos_inserted, vedha_inserted = seed_sarvatobhadra(conn)
        assert pos_inserted == 28, (
            f"Expected 28 positions inserted, got {pos_inserted}"
        )
        assert vedha_inserted == 14, (
            f"Expected 14 vedha pairs inserted, got {vedha_inserted}"
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test 9 (DB) — second seed call inserts 0 rows (idempotency)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not DB_AVAILABLE, reason="DB not reachable at 127.0.0.1:5433")
def test_seed_idempotent():
    """Second call to seed_sarvatobhadra() must insert 0 rows."""
    conn = _get_conn()
    try:
        # First call (data already present from test_8 or earlier seed)
        seed_sarvatobhadra(conn)
        # Second call — must return (0, 0)
        pos_inserted, vedha_inserted = seed_sarvatobhadra(conn)
        assert pos_inserted == 0, (
            f"Expected 0 positions on second seed, got {pos_inserted}"
        )
        assert vedha_inserted == 0, (
            f"Expected 0 vedha pairs on second seed, got {vedha_inserted}"
        )
    finally:
        conn.close()
