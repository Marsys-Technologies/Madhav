"""Writer-shell tests for ka_kota_chakra — the DB-touching orchestration
around the pure logic tested in test_ka_kota_chakra.py. Uses a minimal
FakeConn/FakeCursor (no real Postgres — mirrors the FakeConn pattern already
used elsewhere in this campaign, e.g. services/ka_kshetra's own tests) so the
B.10 honest-empty paths are verified without requiring a live DB in CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_kota_chakra.writer import _fetch_janma_nakshatra_idx, _fetch_ring_assignments


class _FakeCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self._fetchone_result = fetchone_result
        self._fetchall_result = fetchall_result if fetchall_result is not None else []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.last_sql = sql
        self.last_params = params

    def fetchone(self):
        return self._fetchone_result

    def fetchall(self):
        return self._fetchall_result


class _FakeConn:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self._fetchone_result = fetchone_result
        self._fetchall_result = fetchall_result

    def cursor(self, row_factory=None):
        return _FakeCursor(self._fetchone_result, self._fetchall_result)


class TestFetchJanmaNakshatraIdx:
    def test_missing_fact_returns_none(self):
        conn = _FakeConn(fetchone_result=None)
        assert _fetch_janma_nakshatra_idx(conn, "chart-x") is None

    def test_null_value_returns_none(self):
        # row present but fact_value_num is NULL — same honest-absence outcome
        conn = _FakeConn(fetchone_result=("fact123", None))
        assert _fetch_janma_nakshatra_idx(conn, "chart-x") is None

    def test_present_fact_derives_nakshatra_idx(self):
        # Moon longitude_sidereal = 327.055230133129 -> nak_idx 24 (PurvaBhadrapada),
        # the exact FORENSIC-anchored value for chart 482012f1 (CLAUDE.md §B).
        conn = _FakeConn(fetchone_result=("7cf5902c6bd63146", 327.055230133129))
        result = _fetch_janma_nakshatra_idx(conn, "482012f1-710e-4a25-994a-93821f5871aa")
        assert result == (24, "7cf5902c6bd63146")


class TestFetchRingAssignments:
    """ADJUDICATION-9: the ring partition is now an L0 dependency read at run
    time, not a module constant — same honest-absence discipline as
    _fetch_janma_nakshatra_idx (B.10)."""

    def test_empty_table_returns_none(self):
        # bg_kota_chakra_rings not yet built (L0 dependency missing) — honest
        # absence, mirrors _fetch_janma_nakshatra_idx's None-on-missing-fact.
        conn = _FakeConn(fetchall_result=[])
        assert _fetch_ring_assignments(conn) is None

    def test_present_rows_build_ring_sets_and_citation(self):
        citation_text = "Kota-Chakra ring table — tier-(iii) transcription (ADJUDICATION-9)"
        rows = [
            (4, "stambha", "kota_chakra_rings_v01", citation_text),
            (11, "stambha", "kota_chakra_rings_v01", citation_text),
            (3, "durgantara", "kota_chakra_rings_v01", citation_text),
            (2, "prakara", "kota_chakra_rings_v01", citation_text),
            (1, "bahya", "kota_chakra_rings_v01", citation_text),
        ]
        conn = _FakeConn(fetchall_result=rows)
        result = _fetch_ring_assignments(conn)
        assert result is not None
        ring_sets, citation = result
        assert citation == citation_text
        assert ring_sets["stambha"] == frozenset({4, 11})
        assert ring_sets["durgantara"] == frozenset({3})
        assert ring_sets["prakara"] == frozenset({2})
        assert ring_sets["bahya"] == frozenset({1})
