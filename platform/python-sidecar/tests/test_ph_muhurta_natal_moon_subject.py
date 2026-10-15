"""
test_ph_muhurta_natal_moon_subject.py -- FAIL-ON-BASE (SS N-574, verified live defect): ph_muhurta read the natal
Moon nakshatra / sign with `fact_subject = 'Moon'`, but chart_facts holds the Moon under the graha-vocabulary
subject code 'MOON' (1,395 rows for the native, zero 'Moon' rows), so the query matched nothing and the natal star
silently fell to a default (main: natal_moon_nakshatra_idx = 0 = Ashwini in the jsonb echo; tarabala/chandrabala
= the 0.5 placeholder). The loaders now bind the subject code, pin fact_category and carry a total ORDER BY
(fact_id) with LIMIT 1 (§N.7 item 2); a missing fact is an honest None the caller records as the placeholder,
never an ordinal.
"""
from __future__ import annotations

import logging
import re
from unittest.mock import MagicMock

import pytest

from brahmagyan.graha_vocabulary import graha_subject_code
from pipeline.orchestrator.writers.ph_muhurta import PhMuhurtaWriter

CHART = "482012f1-710e-4a25-994a-93821f5871aa"


def _fact(subject, key, text, fact_id="f1", category="graha_position", ay="lahiri_chitrapaksha"):
    return {"fact_subject": subject, "fact_key": key, "fact_value_text": text, "fact_id": fact_id, "fact_category": category, "ayanamsha_id": ay, "chart_id": CHART}


class _TableConn:
    """A chart_facts-shaped fake: evaluates the loader's WHERE clause (literal or bound subject, key, optional
    category pin, ORDER BY fact_id) against `rows`, so main's `fact_subject = 'Moon'` misses a 'MOON' row."""

    def __init__(self, rows):
        self.rows, self.sql, self.params = rows, [], []
        conn = self
        class _Cur:
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def execute(s, sql, params=()):
                conn.sql.append(" ".join(sql.split())); conn.params.append(tuple(params))
            def fetchone(s):
                sql, params = conn.sql[-1], conn.params[-1]
                m_sub = re.search(r"fact_subject = (%s|'(\w+)')", sql)
                subject = params[1] if m_sub.group(1) == "%s" else m_sub.group(2)
                key = re.search(r"fact_key = '(\w+)'", sql).group(1)
                cat = re.search(r"fact_category = '(\w+)'", sql)
                ay = re.search(r"ayanamsha_id = '(\w+)'", sql).group(1)
                hits = [r for r in conn.rows if r["chart_id"] == params[0] and r["fact_subject"] == subject and r["fact_key"] == key
                        and r["ayanamsha_id"] == ay and (cat is None or r["fact_category"] == cat.group(1))]
                if "ORDER BY fact_id" in sql:
                    hits.sort(key=lambda r: r["fact_id"])
                return (hits[0]["fact_value_text"],) if hits else None
        self._cur = _Cur()

    def cursor(self, **kw):
        return self._cur


def _writer() -> PhMuhurtaWriter:
    return PhMuhurtaWriter.__new__(PhMuhurtaWriter)


NATIVE = [_fact("MOON", "nakshatra", "Purva Bhadrapada", "n1"), _fact("MOON", "sign", "Aquarius", "s1"),
          _fact("JUPITER", "nakshatra", "Mula", "n2"), _fact("MOON", "pada", None, "p1")]


def test_FAIL_ON_BASE_the_natives_moon_is_found_under_its_subject_code():
    """chart_facts stores 'MOON' (graha_vocabulary code); main's literal 'Moon' finds nothing and the idx defaults to 0 = Ashwini."""
    assert graha_subject_code("Moon") == "MOON"
    conn = _TableConn(NATIVE)
    assert _writer()._load_natal_moon_nakshatra_id(conn, CHART) == 25        # Purva Bhadrapada
    assert _writer()._load_natal_moon_nakshatra_idx(conn, CHART) == 24       # 0-based echo; main returns 0 (Ashwini) here
    assert _writer()._load_natal_moon_sign_id(conn, CHART) == 11             # Aquarius
    sel = [q for q in conn.sql if q.startswith("SELECT")]
    assert sel and all("fact_subject = %s" in q and "'Moon'" not in q for q in sel)
    assert all(p[1] == "MOON" for p in conn.params if len(p) > 1)


def test_the_reads_pin_the_category_and_carry_a_total_order_by_with_limit_1():
    conn = _TableConn(NATIVE)
    _writer()._load_natal_moon_nakshatra_id(conn, CHART); _writer()._load_natal_moon_sign_id(conn, CHART)
    for q in (q for q in conn.sql if q.startswith("SELECT")):
        assert "fact_category = 'graha_position'" in q and "ORDER BY fact_id LIMIT 1" in q, q


def test_order_by_fact_id_makes_the_single_row_deterministic():
    rows = [_fact("MOON", "nakshatra", "Revati", "z9"), _fact("MOON", "nakshatra", "Purva Bhadrapada", "a1")]
    assert _writer()._load_natal_moon_nakshatra_id(_TableConn(rows), CHART) == 25   # the smallest fact_id, whatever the insertion order


def test_a_missing_fact_is_an_honest_none_recorded_as_not_computed_never_an_ordinal(caplog):
    w = _writer()
    with caplog.at_level(logging.WARNING, logger="pipeline.orchestrator.writers.ph_muhurta"):
        conn = _TableConn([_fact("JUPITER", "nakshatra", "Mula", "n2")])          # no Moon fact at all
        assert w._load_natal_moon_nakshatra_id(conn, CHART) is None
        assert w._load_natal_moon_nakshatra_idx(conn, CHART) is None             # never 0 / Ashwini
        assert w._load_natal_moon_sign_id(conn, CHART) is None
    assert any("natal Moon nakshatra" in r.getMessage() and "NOT computed" in r.getMessage() for r in caplog.records)
    scores = w._compute_tara_chandra_scores(None, 11, {"latitude_deg": 20.3, "longitude_deg": 85.8, "tz_offset_hours": 5.5}, "2026-10-12T06:00:00Z")
    assert scores[2] == "placeholder_no_ephemeris" and scores[:2] == (0.5, 0.5)   # the recorded not-computed marker, not a real tara


def test_a_legacy_title_case_subject_row_is_not_what_l1_emits_and_is_not_read():
    """L1 writes the subject code; a stray 'Moon' row is not the L1 fact and must not be served as it."""
    assert _writer()._load_natal_moon_nakshatra_id(_TableConn([_fact("Moon", "nakshatra", "Ashwini", "x1")]), CHART) is None


def test_the_stored_spelling_still_goes_through_the_normaliser():
    rows = [_fact("MOON", "nakshatra", "Mula", "n1")]
    assert _writer()._load_natal_moon_nakshatra_id(_TableConn(rows), CHART) == 19
    with pytest.raises(ValueError):
        _writer()._load_natal_moon_nakshatra_id(_TableConn([_fact("MOON", "nakshatra", "NotANakshatra", "n1")]), CHART)
