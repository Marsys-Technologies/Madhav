"""
test_tajik_varsha_year_lords_writer.py — Tests for A20 Tajik Hadda fold writer.

Unit tests (no DB):
  Test 01: HADDA_TABLE covers all 12 signs
  Test 02: Each sign in HADDA_TABLE has exactly 5 sectors
  Test 03: Each sign's Hadda sectors are contiguous and span 0-30
  Test 04: YEAR_LORD_SEQUENCE has exactly 7 entries (one per classical planet)
  Test 05: SIGNS list has exactly 12 entries
  Test 06: year_lord cycles correctly over 7-year period
  Test 07: compute_muntha_sign returns Lagna sign for year 1
  Test 08: compute_muntha_sign advances correctly across 12-sign cycle
  Test 09: compute_muntha_sign wraps correctly after 12 years
  Test 10: get_hadda_lord returns correct lord for Aries degree 0
  Test 11: get_hadda_lord returns correct lord for Leo degree 6 (Mercury sector)
  Test 12: get_hadda_lord edge-case — degree exactly at boundary (Aries degree 6 → Venus)
  Test 13: get_hadda_lord edge-case — degree 29.99 falls in last sector
  Test 14: SIGN_LORDS covers all 12 signs and all values are valid planet names
  Test 15: lagna_sign_from_longitude correctly maps 0-360 longitude to sign
  Test 16: degree_in_sign_from_longitude returns value in [0,30)

DB integration tests (skipped if DB not available):
  Test 17 (DB): write_tajik_varsha_year_lords inserts 150 rows
  Test 18 (DB): verify_tajik_varsha_year_lords returns True after 150 rows
  Test 19 (DB): ON CONFLICT idempotency — second write inserts 0 rows

Stream D — A20 [BUILD-ORCH-STREAM-D-A20]
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest

from pipeline.writers.tajik_varsha_year_lords_writer import (
    HADDA_TABLE,
    SIGN_LORDS,
    SIGNS,
    YEAR_LORD_SEQUENCE,
    compute_muntha_sign,
    degree_in_sign_from_longitude,
    get_hadda_lord,
    lagna_sign_from_longitude,
    verify_tajik_varsha_year_lords,
    write_tajik_varsha_year_lords,
)

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

DB_AVAILABLE = bool(os.environ.get("DB_NAME") or os.environ.get("DB_HOST"))

VALID_PLANET_NAMES = {
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
}


def _get_conn():
    """Return a psycopg2 connection using env vars (mirrors CLI defaults)."""
    import psycopg2
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "5433")),
        dbname=os.environ.get("DB_NAME", "amjis"),
        user=os.environ.get("DB_USER", "amjis_app"),
        password=os.environ.get("DB_PASS", ""),
    )


# ---------------------------------------------------------------------------
# Test 01: HADDA_TABLE covers all 12 signs
# ---------------------------------------------------------------------------
def test_hadda_table_has_all_signs():
    assert set(HADDA_TABLE.keys()) == set(SIGNS), (
        "HADDA_TABLE must cover exactly the 12 canonical sign names"
    )


# ---------------------------------------------------------------------------
# Test 02: Each sign has exactly 5 Hadda sectors
# ---------------------------------------------------------------------------
def test_hadda_table_five_sectors_per_sign():
    for sign, sectors in HADDA_TABLE.items():
        assert len(sectors) == 5, (
            f"Sign '{sign}' has {len(sectors)} Hadda sectors, expected 5"
        )


# ---------------------------------------------------------------------------
# Test 03: Hadda sectors are contiguous and span exactly 0-30 for every sign
# ---------------------------------------------------------------------------
def test_hadda_table_sectors_contiguous_and_full():
    for sign, sectors in HADDA_TABLE.items():
        assert sectors[0][0] == 0, f"Sign '{sign}' first sector must start at 0"
        assert sectors[-1][1] == 30, f"Sign '{sign}' last sector must end at 30"
        for i in range(len(sectors) - 1):
            assert sectors[i][1] == sectors[i + 1][0], (
                f"Sign '{sign}': gap or overlap between sectors {i} and {i+1}: "
                f"{sectors[i][1]} vs {sectors[i+1][0]}"
            )


# ---------------------------------------------------------------------------
# Test 04: YEAR_LORD_SEQUENCE has exactly 7 entries
# ---------------------------------------------------------------------------
def test_year_lord_sequence_length():
    assert len(YEAR_LORD_SEQUENCE) == 7, (
        "YEAR_LORD_SEQUENCE must have exactly 7 planets"
    )


# ---------------------------------------------------------------------------
# Test 05: SIGNS list has exactly 12 entries
# ---------------------------------------------------------------------------
def test_signs_list_length():
    assert len(SIGNS) == 12, "SIGNS must contain exactly 12 zodiac signs"


# ---------------------------------------------------------------------------
# Test 06: year_lord cycles correctly over 7-year period
# ---------------------------------------------------------------------------
def test_year_lord_cycle():
    # Year 1 → index 0 → Sun
    assert YEAR_LORD_SEQUENCE[(1 - 1) % 7] == "Sun"
    # Year 7 → index 6 → Saturn
    assert YEAR_LORD_SEQUENCE[(7 - 1) % 7] == "Saturn"
    # Year 8 → index 0 → Sun (cycle restarts)
    assert YEAR_LORD_SEQUENCE[(8 - 1) % 7] == "Sun"
    # Year 15 → index 0 → Sun again
    assert YEAR_LORD_SEQUENCE[(15 - 1) % 7] == "Sun"
    # All 7 planet values must be present in VALID_PLANET_NAMES
    assert set(YEAR_LORD_SEQUENCE) <= VALID_PLANET_NAMES


# ---------------------------------------------------------------------------
# Test 07: compute_muntha_sign — year 1 returns Lagna sign unchanged
# ---------------------------------------------------------------------------
def test_compute_muntha_year_1_equals_lagna():
    for sign in SIGNS:
        result = compute_muntha_sign(sign, 1)
        assert result == sign, (
            f"Year 1 Muntha should equal Lagna sign '{sign}', got '{result}'"
        )


# ---------------------------------------------------------------------------
# Test 08: compute_muntha_sign advances correctly
# ---------------------------------------------------------------------------
def test_compute_muntha_advances_one_sign_per_year():
    # Lagna = Aries (index 0)
    # Year 1 → Aries (0), Year 2 → Taurus (1), Year 3 → Gemini (2)
    assert compute_muntha_sign("Aries", 1) == "Aries"
    assert compute_muntha_sign("Aries", 2) == "Taurus"
    assert compute_muntha_sign("Aries", 3) == "Gemini"
    # Lagna = Pisces (index 11)
    # Year 1 → Pisces, Year 2 → Aries (wraps)
    assert compute_muntha_sign("Pisces", 1) == "Pisces"
    assert compute_muntha_sign("Pisces", 2) == "Aries"


# ---------------------------------------------------------------------------
# Test 09: compute_muntha_sign wraps correctly after 12 years
# ---------------------------------------------------------------------------
def test_compute_muntha_wrap_after_12_years():
    # Lagna = Cancer (index 3); Year 13 → same sign as Year 1 (full cycle)
    assert compute_muntha_sign("Cancer", 13) == compute_muntha_sign("Cancer", 1)
    assert compute_muntha_sign("Cancer", 13) == "Cancer"


# ---------------------------------------------------------------------------
# Test 10: get_hadda_lord — Aries degree 0 → Jupiter
# ---------------------------------------------------------------------------
def test_get_hadda_lord_aries_start():
    lord, start, end = get_hadda_lord("Aries", 0.0)
    assert lord == "Jupiter", f"Expected Jupiter for Aries 0°, got {lord}"
    assert start == 0 and end == 6


# ---------------------------------------------------------------------------
# Test 11: get_hadda_lord — Leo degree 6 → Mercury
# ---------------------------------------------------------------------------
def test_get_hadda_lord_leo_degree_6():
    lord, start, end = get_hadda_lord("Leo", 6.0)
    assert lord == "Mercury", f"Expected Mercury for Leo 6°, got {lord}"
    assert start == 6 and end == 11


# ---------------------------------------------------------------------------
# Test 12: get_hadda_lord — Aries degree 6 → Venus (sector boundary)
# ---------------------------------------------------------------------------
def test_get_hadda_lord_aries_boundary_degree_6():
    lord, start, end = get_hadda_lord("Aries", 6.0)
    assert lord == "Venus", (
        f"Aries 6° should be Venus sector (6-14), got {lord}"
    )


# ---------------------------------------------------------------------------
# Test 13: get_hadda_lord — degree 29.99 falls in last sector of sign
# ---------------------------------------------------------------------------
def test_get_hadda_lord_last_sector():
    # Aries last sector: (26, 30, 'Saturn')
    lord, start, end = get_hadda_lord("Aries", 29.99)
    assert lord == "Saturn", (
        f"Aries 29.99° should be Saturn (last sector), got {lord}"
    )
    assert start == 26 and end == 30


# ---------------------------------------------------------------------------
# Test 14: SIGN_LORDS covers all 12 signs with valid planet names
# ---------------------------------------------------------------------------
def test_sign_lords_complete_and_valid():
    assert set(SIGN_LORDS.keys()) == set(SIGNS), (
        "SIGN_LORDS must cover exactly the 12 canonical sign names"
    )
    for sign, lord in SIGN_LORDS.items():
        assert lord in VALID_PLANET_NAMES, (
            f"SIGN_LORDS['{sign}'] = '{lord}' is not a valid planet name"
        )


# ---------------------------------------------------------------------------
# Test 15: lagna_sign_from_longitude — spot-checks
# ---------------------------------------------------------------------------
def test_lagna_sign_from_longitude():
    assert lagna_sign_from_longitude(0.0)   == "Aries"       # 0° = Aries start
    assert lagna_sign_from_longitude(30.0)  == "Taurus"      # 30° = Taurus start
    assert lagna_sign_from_longitude(59.9)  == "Taurus"
    assert lagna_sign_from_longitude(300.0) == "Aquarius"    # 300° = 10×30
    assert lagna_sign_from_longitude(359.9) == "Pisces"


# ---------------------------------------------------------------------------
# Test 16: degree_in_sign_from_longitude returns value in [0, 30)
# ---------------------------------------------------------------------------
def test_degree_in_sign_from_longitude_range():
    for lon in [0.0, 15.5, 29.99, 30.0, 75.3, 180.0, 359.9]:
        deg = degree_in_sign_from_longitude(lon)
        assert 0.0 <= deg < 30.0, (
            f"degree_in_sign({lon}) = {deg} is outside [0,30)"
        )


# ---------------------------------------------------------------------------
# DB integration tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not DB_AVAILABLE, reason="DB not available (set DB_NAME/DB_HOST)")
def test_db_write_inserts_150_rows():
    """Test 17: write_tajik_varsha_year_lords inserts exactly 150 rows."""
    conn = _get_conn()
    try:
        chart_id = str(uuid.uuid4())
        ayanamsha_id = "lahiri"
        build_id = str(uuid.uuid4())
        birth_dt = datetime(1984, 2, 5, 5, 13, 0, tzinfo=timezone.utc)  # native birth UTC
        lagna_sign = "Aquarius"
        lagna_longitude = 313.7  # Aquarius ≈ 300+13.7 degrees

        inserted = write_tajik_varsha_year_lords(
            conn, chart_id, ayanamsha_id, build_id,
            birth_dt, lagna_sign, lagna_longitude,
        )
        assert inserted == 150, f"Expected 150 rows inserted, got {inserted}"
    finally:
        conn.close()


@pytest.mark.skipif(not DB_AVAILABLE, reason="DB not available (set DB_NAME/DB_HOST)")
def test_db_verify_returns_true_after_insert():
    """Test 18: verify_tajik_varsha_year_lords returns True after 150 rows."""
    conn = _get_conn()
    try:
        chart_id = str(uuid.uuid4())
        ayanamsha_id = "lahiri"
        build_id = str(uuid.uuid4())
        birth_dt = datetime(1984, 2, 5, 5, 13, 0, tzinfo=timezone.utc)
        lagna_sign = "Aquarius"
        lagna_longitude = 313.7

        write_tajik_varsha_year_lords(
            conn, chart_id, ayanamsha_id, build_id,
            birth_dt, lagna_sign, lagna_longitude,
        )
        ok = verify_tajik_varsha_year_lords(conn, chart_id, ayanamsha_id, build_id, 150)
        assert ok is True, "verify_tajik_varsha_year_lords should return True"
    finally:
        conn.close()


@pytest.mark.skipif(not DB_AVAILABLE, reason="DB not available (set DB_NAME/DB_HOST)")
def test_db_on_conflict_idempotency():
    """Test 19: Second write inserts 0 rows (ON CONFLICT DO NOTHING)."""
    conn = _get_conn()
    try:
        chart_id = str(uuid.uuid4())
        ayanamsha_id = "raman"
        build_id = str(uuid.uuid4())
        birth_dt = datetime(1984, 2, 5, 5, 13, 0, tzinfo=timezone.utc)
        lagna_sign = "Aquarius"
        lagna_longitude = 313.7

        first_insert = write_tajik_varsha_year_lords(
            conn, chart_id, ayanamsha_id, build_id,
            birth_dt, lagna_sign, lagna_longitude,
        )
        assert first_insert == 150

        second_insert = write_tajik_varsha_year_lords(
            conn, chart_id, ayanamsha_id, build_id,
            birth_dt, lagna_sign, lagna_longitude,
        )
        assert second_insert == 0, (
            f"Idempotency failed: second write inserted {second_insert} rows, expected 0"
        )
    finally:
        conn.close()
