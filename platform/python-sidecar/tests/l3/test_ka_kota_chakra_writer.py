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

from services.ka_kota_chakra.writer import _fetch_janma_nakshatra_idx


class _FakeCursor:
    def __init__(self, fetchone_result=None):
        self._fetchone_result = fetchone_result

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.last_sql = sql
        self.last_params = params

    def fetchone(self):
        return self._fetchone_result


class _FakeConn:
    def __init__(self, fetchone_result=None):
        self._fetchone_result = fetchone_result

    def cursor(self, row_factory=None):
        return _FakeCursor(self._fetchone_result)


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
