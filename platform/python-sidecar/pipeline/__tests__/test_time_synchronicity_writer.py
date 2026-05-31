"""
Tests for time_synchronicity_writer.py — A15 Time-Synchronicity convergence windows.
Stream C — A15 [BUILD-ORCH-STREAM-C-A15-S1]
"""

from __future__ import annotations

import os
from datetime import date

import pytest

# ---------------------------------------------------------------------------
# DB connectivity helper (mirrors pattern used elsewhere in the test suite)
# ---------------------------------------------------------------------------

def _get_conn():
    """Return a psycopg2 connection or None if DB is unavailable."""
    try:
        import psycopg2  # noqa: PLC0415

        db_name = os.environ.get("DB_NAME", "amjis")
        db_host = os.environ.get("DB_HOST", "127.0.0.1")
        db_port = int(os.environ.get("DB_PORT", "5433"))
        db_user = os.environ.get("DB_USER", "amjis_app")
        db_pass = os.environ.get(
            "DB_PASS",
            "aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF",
        )
        return psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_pass,
        )
    except Exception:  # noqa: BLE001
        return None


DB_AVAILABLE = _get_conn() is not None

CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"

# ---------------------------------------------------------------------------
# Import module under test
# ---------------------------------------------------------------------------
from pipeline.time_synchronicity_writer import (  # noqa: E402
    CLUSTER_THRESHOLD,
    TOTAL_SYSTEMS,
    enumerate_key_dates,
    enumerate_tajik_dates,
    find_synchronicity_windows,
    seed_time_synchronicity,
)


# ---------------------------------------------------------------------------
# Test 1: enumerate_key_dates returns dict with all 7 system keys
# ---------------------------------------------------------------------------

def test_enumerate_key_dates_has_all_seven_system_keys():
    """enumerate_key_dates must return exactly the 7 expected timing-system keys."""
    conn = _get_conn()
    if conn is None:
        # Use a mock connection that returns empty results
        import unittest.mock as mock
        mock_cur = mock.MagicMock()
        mock_cur.fetchall.return_value = []
        mock_conn = mock.MagicMock()
        mock_conn.cursor.return_value.__enter__ = mock.MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = mock.MagicMock(return_value=False)
        conn = mock_conn

    key_dates = enumerate_key_dates(conn, CHART_ID)

    expected_keys = {
        "vimshottari_dasha",
        "jaimini_chara",
        "tajik_varsha",
        "bhrigu_bindu",
        "graha_aspect",
        "vedha_activation",
        "sade_sati",
    }
    assert set(key_dates.keys()) == expected_keys, (
        f"Expected keys {expected_keys}, got {set(key_dates.keys())}"
    )


# ---------------------------------------------------------------------------
# Test 2: bhrigu_bindu returns >= 50 dates (DB test)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not DB_AVAILABLE, reason="DB not available")
def test_bhrigu_bindu_returns_sufficient_dates():
    """bhrigu_bindu key_dates should have >= 50 hits in 2026-2060 for the native."""
    conn = _get_conn()
    key_dates = enumerate_key_dates(conn, CHART_ID)
    conn.close()

    bb_dates = key_dates["bhrigu_bindu"]
    assert len(bb_dates) >= 50, (
        f"Expected >= 50 BB transit dates in 2026-2060, got {len(bb_dates)}"
    )


# ---------------------------------------------------------------------------
# Test 3: find_synchronicity_windows returns non-empty list
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not DB_AVAILABLE, reason="DB not available")
def test_find_synchronicity_windows_non_empty():
    """find_synchronicity_windows must return at least one convergence window."""
    conn = _get_conn()
    key_dates = enumerate_key_dates(conn, CHART_ID)
    windows = find_synchronicity_windows(key_dates, chart_id=CHART_ID)

    assert len(windows) > 0, "Expected at least one synchronicity window in 2026-2060"


# ---------------------------------------------------------------------------
# Test 4: All window dicts have required keys
# ---------------------------------------------------------------------------

def test_window_dicts_have_required_keys():
    """Every window dict must contain all required fields."""
    required_keys = {
        "chart_id",
        "window_start",
        "window_end",
        "cluster_intensity",
        "systems_active",
        "key_dates",
        "divergence_flag",
        "convergence_score",
    }

    conn = _get_conn()
    if conn is None:
        import unittest.mock as mock
        mock_cur = mock.MagicMock()
        mock_cur.fetchall.return_value = []
        mock_conn = mock.MagicMock()
        mock_conn.cursor.return_value.__enter__ = mock.MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = mock.MagicMock(return_value=False)
        conn = mock_conn

    key_dates = enumerate_key_dates(conn, CHART_ID)
    windows = find_synchronicity_windows(key_dates, chart_id=CHART_ID)

    for w in windows:
        missing = required_keys - set(w.keys())
        assert not missing, f"Window dict missing keys: {missing}"


# ---------------------------------------------------------------------------
# Test 5: cluster_intensity >= 3 for all windows
# ---------------------------------------------------------------------------

def test_cluster_intensity_meets_threshold():
    """All returned windows must have cluster_intensity >= CLUSTER_THRESHOLD (3)."""
    conn = _get_conn()
    if conn is None:
        import unittest.mock as mock
        mock_cur = mock.MagicMock()
        mock_cur.fetchall.return_value = []
        mock_conn = mock.MagicMock()
        mock_conn.cursor.return_value.__enter__ = mock.MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = mock.MagicMock(return_value=False)
        conn = mock_conn

    key_dates = enumerate_key_dates(conn, CHART_ID)
    windows = find_synchronicity_windows(key_dates, chart_id=CHART_ID)

    for w in windows:
        assert w["cluster_intensity"] >= CLUSTER_THRESHOLD, (
            f"Window {w['window_start']} has intensity {w['cluster_intensity']} "
            f"< threshold {CLUSTER_THRESHOLD}"
        )


# ---------------------------------------------------------------------------
# Test 6: convergence_score between 0.0 and 1.0
# ---------------------------------------------------------------------------

def test_convergence_score_in_range():
    """convergence_score must be in [0.0, 1.0] for all windows."""
    conn = _get_conn()
    if conn is None:
        import unittest.mock as mock
        mock_cur = mock.MagicMock()
        mock_cur.fetchall.return_value = []
        mock_conn = mock.MagicMock()
        mock_conn.cursor.return_value.__enter__ = mock.MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = mock.MagicMock(return_value=False)
        conn = mock_conn

    key_dates = enumerate_key_dates(conn, CHART_ID)
    windows = find_synchronicity_windows(key_dates, chart_id=CHART_ID)

    for w in windows:
        score = w["convergence_score"]
        assert 0.0 <= score <= 1.0, (
            f"Window {w['window_start']} has convergence_score={score} outside [0.0, 1.0]"
        )


# ---------------------------------------------------------------------------
# Test 7 (DB): seed_time_synchronicity inserts > 5 windows and is idempotent
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not DB_AVAILABLE, reason="DB not available")
def test_seed_time_synchronicity_inserts_and_is_idempotent():
    """Fresh seed → > 5 rows; second call → 0 (true idempotency check)."""
    conn = _get_conn()
    try:
        # Clear rows for this chart_id so first seed is a genuine fresh insert
        with conn.cursor() as cur:
            cur.execute("DELETE FROM l1_time_synchronicity WHERE chart_id = %s", (CHART_ID,))
            conn.commit()

        count1 = seed_time_synchronicity(conn, CHART_ID)
        assert count1 > 5, f"Expected > 5 windows inserted, got {count1}"

        # Idempotency: second run should insert 0 (ON CONFLICT DO NOTHING)
        count2 = seed_time_synchronicity(conn, CHART_ID)
        assert count2 == 0, f"Expected 0 rows on second run (idempotency), got {count2}"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test 8: Feb 5 appears in tajik_varsha system dates
# ---------------------------------------------------------------------------

def test_tajik_varsha_contains_native_birthday():
    """tajik_varsha dates must include Feb 5 entries for the native's solar returns."""
    tajik_dates = enumerate_tajik_dates(start_year=2026, end_year=2060)

    # Every year 2026-2060 should have a Feb 5 entry
    feb_5_dates = [d for d in tajik_dates if d.month == 2 and d.day == 5]
    assert len(feb_5_dates) >= 34, (
        f"Expected >= 34 Feb 5 solar returns (2026-2060), got {len(feb_5_dates)}"
    )

    # Spot-check 2026-02-05 is present
    assert date(2026, 2, 5) in tajik_dates, "2026-02-05 missing from tajik_varsha dates"
    assert date(2040, 2, 5) in tajik_dates, "2040-02-05 missing from tajik_varsha dates"
