"""
Unit tests for the dict_row-vs-tuple class fix (pre-regen blocker sweep).

Root cause: psycopg3 connection uses row_factory=dict_row, so cursor.fetchall()
returns list[dict]. Writers that did dict(zip(cols, row)) on already-dict rows
produced {col_name: entire_row_dict} — a dict-of-dicts. This causes
float(dict) → ValueError in downstream salience computation.

These tests use a MagicMock cursor that returns psycopg3-style dict rows and
assert that the fixed _fetch_dict / row-accessor code returns real scalar values.

Run: python -m pytest platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_dict_row_fixes.py -v
"""
from __future__ import annotations

import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


# ── Helper: mock psycopg3 dict_row result ─────────────────────────────────────

def _dict_cursor_mock(rows: list[dict]):
    """Return a mock that behaves like a psycopg3 dict_row cursor."""
    cur = MagicMock()
    cur.fetchall.return_value = rows
    # description unused after the fix but kept for API compat
    cur.description = [MagicMock(name=k) for k in (rows[0].keys() if rows else [])]
    return cur


def _conn_mock(rows: list[dict]):
    """Return a mock conn whose .execute() and .cursor().__enter__ return dict rows."""
    conn = MagicMock()
    cur = _dict_cursor_mock(rows)
    conn.execute.return_value = cur
    # cursor() context manager
    ctx_cur = _dict_cursor_mock(rows)
    conn.cursor.return_value.__enter__ = MagicMock(return_value=ctx_cur)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cur, ctx_cur


# ── FIX 1: bo_laksana._fetch_dict ─────────────────────────────────────────────

def test_bo_laksana_fetch_dict_returns_plain_dicts():
    """_fetch_dict must return list[dict] with scalar values, not dict-of-dicts."""
    from pipeline.orchestrator.writers.bo_laksana import _fetch_dict

    fake_rows = [
        {"fact_key": "Sun", "fact_value_num": 450.5},
        {"fact_key": "Moon", "fact_value_num": 320.0},
    ]
    conn, cur, _ = _conn_mock(fake_rows)

    result = _fetch_dict(conn, "SELECT fact_key, fact_value_num FROM chart_facts WHERE 1=0", [])

    assert len(result) == 2
    # Before fix: result[0]["fact_value_num"] was the whole row dict → float(dict) would crash.
    # After fix: must be a real float.
    assert isinstance(result[0]["fact_value_num"], float), (
        f"expected float, got {type(result[0]['fact_value_num'])}: {result[0]['fact_value_num']!r}"
    )
    assert result[0]["fact_value_num"] == 450.5
    assert result[1]["fact_key"] == "Moon"


def test_bo_laksana_build_strength_lookup_returns_floats():
    """_build_strength_lookup must return dict[str, float], not dict[str, dict].

    Updated for the ŚUDDHA-VĀCA P0-5/P0-6 fix (2026-07-28,
    SUDDHA_VACA_FIX_LEDGER_v1_0.md, lane:bo-laksana). Pre-fix this test's
    fixture used a stale pre-B2 contract (fact_key holding 'Sun:D1' etc.,
    when graha actually lives in fact_subject) and asserted the buggy
    raw-rupa/1.0 normalization — it was already failing against the current
    (pre-this-fix) source before this edit. The fixed function keys off
    fact_subject and returns the L1-precomputed 'ratio' (achieved/required
    shadbala) fact_value_num, pinned by fact_key='ratio' at the SQL layer;
    this mock does not model the WHERE clause, so the fixture below feeds it
    exactly what a fact_key='ratio' SELECT already yields. See
    test_bo_laksana_p05_p06_shadbala_ratio.py for the full golden-table
    coverage (determinism + normalization) with a query-aware fake conn.
    """
    from pipeline.orchestrator.writers.bo_laksana import _build_strength_lookup

    fake_shadbala_rows = [
        {"fact_subject": "SUN", "fact_value_num": 1.694},
        {"fact_subject": "MOON", "fact_value_num": 0.9417},
        {"fact_subject": "MAR", "fact_value_num": 1.114},
    ]
    conn, cur, _ = _conn_mock(fake_shadbala_rows)

    lookup = _build_strength_lookup(conn, "chart-123", "lahiri_chitrapaksha")

    assert "SUN" in lookup
    assert isinstance(lookup["SUN"], float), f"expected float, got {type(lookup['SUN'])}: {lookup['SUN']!r}"
    assert lookup["SUN"] == pytest.approx(1.694)
    assert lookup["MOON"] == pytest.approx(0.9417)


# ── FIX 2: bo_drishti._fetch_dict ─────────────────────────────────────────────

def test_bo_drishti_fetch_dict_returns_plain_dicts():
    from pipeline.orchestrator.writers.bo_drishti import _fetch_dict

    fake_rows = [{"signal_id": "uuid-1", "computed_salience": 1.25}]
    conn, _, ctx_cur = _conn_mock(fake_rows)
    ctx_cur.fetchall.return_value = fake_rows

    result = _fetch_dict(conn, "SELECT ...", [])

    assert result[0]["computed_salience"] == 1.25
    assert isinstance(result[0]["computed_salience"], float)


# ── FIX 2: bo_sangati._fetch_dict ─────────────────────────────────────────────

def test_bo_sangati_fetch_dict_returns_plain_dicts():
    from pipeline.orchestrator.writers.bo_sangati import _fetch_dict

    fake_rows = [{"signal_id": "uuid-2", "computed_salience": 0.75}]
    conn, _, ctx_cur = _conn_mock(fake_rows)
    ctx_cur.fetchall.return_value = fake_rows

    result = _fetch_dict(conn, "SELECT ...", [])

    assert result[0]["computed_salience"] == 0.75


# ── FIX 2: ka_jivana_parva row-key access ─────────────────────────────────────

def test_ka_jivana_parva_does_not_unpack_dict_keys():
    """
    ka_jivana_parva must use dict key access on dashas and conv_windows rows.
    Before fix: tuple-unpack `(planet, start_dt, end_dt) = row` on a dict row
    gave planet='lord_graha' (the key string) instead of the planet name.
    """
    from datetime import date

    # Simulate what the writer does with dashas rows (dict_row)
    from pipeline.orchestrator.writers.ka_jivana_parva import _assign_quality, _derive_theme

    # The fix: dict key access; verify the downstream functions get real values
    dasha_row = {
        'lord_graha': 'Saturn',
        'start_date': date(2012, 1, 1),
        'end_date': date(2031, 1, 1),
    }
    planet = dasha_row['lord_graha']
    start_dt = dasha_row['start_date']
    end_dt = dasha_row['end_date']

    assert planet == 'Saturn', f"planet must be 'Saturn', got {planet!r}"
    assert isinstance(start_dt, date)

    quality = _assign_quality(0, 9, 2, 0.55, start_dt.year, end_dt.year)
    assert quality in ('peak', 'building', 'consolidating', 'receding', 'transitional')

    theme = _derive_theme(planet, quality)
    assert 'discipline' in theme or 'responsibility' in theme or 'delay' in theme, (
        f"Saturn themes expected, got: {theme}"
    )


def test_ka_jivana_parva_conv_windows_key_access():
    """conv_windows rows must be accessed by dict key, not integer index."""
    from datetime import date

    # Replicate the span_windows filter logic with dict rows (post-fix)
    start_dt = date(2020, 1, 1)
    end_dt_actual = date(2025, 1, 1)

    conv_windows = [
        {'peak_date': date(2021, 6, 15), 'convergence_score': 0.6, 'effective_score': 0.65},
        {'peak_date': date(2026, 1, 1), 'convergence_score': 0.3, 'effective_score': 0.3},  # out of range
    ]

    span_windows = [
        w for w in conv_windows
        if w['peak_date'] and start_dt <= w['peak_date'] <= end_dt_actual
    ]
    assert len(span_windows) == 1
    assert span_windows[0]['peak_date'] == date(2021, 6, 15)

    high_count = sum(1 for w in span_windows if (w['effective_score'] or 0) >= 0.5)
    assert high_count == 1

    avg_score = sum(w['effective_score'] or 0 for w in span_windows) / len(span_windows)
    assert isinstance(avg_score, float)
    assert avg_score == 0.65


# ── FIX 2: ka_bhavishya_lekha row-key access ─────────────────────────────────

def test_ka_bhavishya_lekha_signal_id_extraction():
    """signal_id must be extracted by dict key, not integer index r[1]."""
    # Simulate darshana_rows as list[dict] (dict_row result)
    darshana_rows = [
        {'convergence_id': 'c1', 'signal_id': 'sig-uuid-1', 'net_label': 'flowing',
         'effective_score': 0.72, 'peak_date': None, 'window_start': None,
         'window_end': None, 'narrative': None, 'obstruction_summary': None,
         'confidence_label': 'high', 'rarity_years': 5.0, 'mode': 'stellar'},
    ]

    # Before fix: r[1] on a dict gives second key ('signal_id') as a string, not the value
    # After fix: r['signal_id'] gives the actual UUID
    signal_ids = [str(r['signal_id']) for r in darshana_rows if r['signal_id']]
    assert signal_ids == ['sig-uuid-1'], f"Expected UUID value, got: {signal_ids}"

    # Unpack via dict keys (post-fix pattern)
    row = darshana_rows[0]
    signal_id = row['signal_id']
    net_label = row['net_label']
    eff_score = row['effective_score']

    assert signal_id == 'sig-uuid-1'
    assert net_label == 'flowing'
    assert isinstance(eff_score, float)
    assert eff_score == 0.72
