"""
test_vedha_writer.py — Tests for vedha_writer.py

Covers:
  Test 1: total row count >= 60
  Test 2: all tuples have exactly 8 elements
  Test 3: vedha_system values are all in the allowed set
  Test 4: severity values are all in {strong, moderate, weak, cancellation}
  Test 5: cancellation_rule is non-None for severity=cancellation rows
  Test 6 (DB): seed_vedha_extended() inserts >= 60 rows and is idempotent on second call
  Test 7 (DB): unique index prevents duplicate (system, source, obstructing, type)

Stream C — A18 [BUILD-ORCH-STREAM-C-A18-S1]
"""
from __future__ import annotations

import os

import pytest

from pipeline.vedha_writer import (
    VEDHA_ALL_ROWS,
    _ALLOWED_SEVERITIES,
    _ALLOWED_SYSTEMS,
    seed_vedha_extended,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DB_AVAILABLE = bool(os.environ.get("DB_NAME"))


def _get_conn():
    """Return a psycopg2 connection using env vars."""
    import psycopg2
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "5433")),
        dbname=os.environ.get("DB_NAME", "amjis"),
        user=os.environ.get("DB_USER", "amjis_app"),
        password=os.environ.get(
            "DB_PASS", "aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF"
        ),
    )


# ---------------------------------------------------------------------------
# Unit tests (no DB required)
# ---------------------------------------------------------------------------


def test_total_row_count_at_least_60():
    """Test 1: VEDHA_ALL_ROWS has at least 60 rows across all 6 systems."""
    assert len(VEDHA_ALL_ROWS) >= 60, (
        f"Expected >= 60 vedha rows, got {len(VEDHA_ALL_ROWS)}"
    )


def test_all_tuples_have_8_elements():
    """Test 2: every tuple has exactly 8 elements."""
    bad = [
        (i, len(row))
        for i, row in enumerate(VEDHA_ALL_ROWS)
        if len(row) != 8
    ]
    assert not bad, f"Rows with wrong element count (index, length): {bad}"


def test_vedha_system_values_in_allowed_set():
    """Test 3: vedha_system (index 0) is always in the allowed set."""
    bad = {row[0] for row in VEDHA_ALL_ROWS if row[0] not in _ALLOWED_SYSTEMS}
    assert not bad, f"Unknown vedha_system values: {bad}"


def test_severity_values_in_allowed_set():
    """Test 4: severity (index 4) is always in {strong, moderate, weak, cancellation}."""
    bad = {row[4] for row in VEDHA_ALL_ROWS if row[4] not in _ALLOWED_SEVERITIES}
    assert not bad, f"Unknown severity values: {bad}"


def test_cancellation_rule_present_when_severity_cancellation():
    """Test 5: cancellation_rule (index 5) is non-None for cancellation rows."""
    violations = [
        row for row in VEDHA_ALL_ROWS
        if row[4] == 'cancellation' and row[5] is None
    ]
    assert not violations, (
        f"cancellation rows missing cancellation_rule: {violations}"
    )


# ---------------------------------------------------------------------------
# DB tests (skipped when DB_NAME not set)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not DB_AVAILABLE, reason="DB_NAME env var not set")
def test_seed_vedha_extended_inserts_rows_and_is_idempotent():
    """Test 6 (DB): fresh seed → >= 60 rows; second call → 0 (true idempotency)."""
    conn = _get_conn()
    try:
        # Clear table first so the first seed is a genuine fresh insert
        with conn.cursor() as cur:
            cur.execute("DELETE FROM l1_vedha_extended")
            conn.commit()

        # First call — should insert all rows
        count1 = seed_vedha_extended(conn)
        assert count1 >= 60, f"Expected >= 60 inserted on first call, got {count1}"

        # Second call — ON CONFLICT DO NOTHING → 0 new rows
        count2 = seed_vedha_extended(conn)
        assert count2 == 0, f"Expected 0 on idempotent second call, got {count2}"
    finally:
        conn.close()


@pytest.mark.skipif(not DB_AVAILABLE, reason="DB_NAME env var not set")
def test_unique_index_prevents_duplicates():
    """Test 7 (DB): unique index rejects a duplicate (system, source, obstructing, type)."""
    import psycopg2
    conn = _get_conn()
    try:
        # Ensure at least one row is present
        seed_vedha_extended(conn)

        first_row = VEDHA_ALL_ROWS[0]
        dup_sql = """
            INSERT INTO l1_vedha_extended
                (vedha_system, source_nakshatra, obstructing_element,
                 obstruction_type, severity)
            VALUES (%s, %s, %s, %s, 'weak')
        """
        with conn.cursor() as cur:
            with pytest.raises(psycopg2.errors.UniqueViolation):
                cur.execute(dup_sql, (first_row[0], first_row[1], first_row[2], first_row[3]))
                conn.commit()
    finally:
        conn.rollback()
        conn.close()
