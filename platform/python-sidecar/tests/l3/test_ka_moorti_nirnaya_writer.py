"""Writer-shell tests for ka_moorti_nirnaya — the DB-touching orchestration
around the pure logic tested in test_ka_moorti_nirnaya.py. Uses a minimal
FakeConn/FakeCursor (no real Postgres) — mirrors the FakeConn pattern already
used by test_ka_kota_chakra_writer.py / test_ka_sudarshana_varsha_writer.py so
the B.10 honest-empty paths are verified without requiring a live DB in CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_moorti_nirnaya.writer import (
    _fetch_janma_nakshatra_idx,
    _fetch_moorti_table,
)


class _FakeCursorOne:
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


class _FakeConnOne:
    def __init__(self, fetchone_result=None):
        self._fetchone_result = fetchone_result

    def cursor(self, row_factory=None):
        return _FakeCursorOne(self._fetchone_result)


class TestFetchJanmaNakshatraIdx:
    def test_missing_fact_returns_none(self):
        conn = _FakeConnOne(fetchone_result=None)
        assert _fetch_janma_nakshatra_idx(conn, "chart-x") is None

    def test_null_value_returns_none(self):
        conn = _FakeConnOne(fetchone_result=("fact123", None))
        assert _fetch_janma_nakshatra_idx(conn, "chart-x") is None

    def test_present_fact_derives_nakshatra_idx(self):
        # Moon longitude_sidereal = 327.055230133129 -> nak_idx 24 (Purva
        # Bhadrapada), the exact FORENSIC-anchored value for chart 482012f1
        # (CLAUDE.md §B) — same fixture value test_ka_kota_chakra_writer.py uses.
        conn = _FakeConnOne(fetchone_result=("7cf5902c6bd63146", 327.055230133129))
        result = _fetch_janma_nakshatra_idx(conn, "482012f1-710e-4a25-994a-93821f5871aa")
        assert result == (24, "7cf5902c6bd63146")


class _FakeCursorAll:
    def __init__(self, fetchall_result):
        self._fetchall_result = fetchall_result

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        pass

    def fetchall(self):
        return self._fetchall_result


class _FakeConnAll:
    def __init__(self, fetchall_result):
        self._fetchall_result = fetchall_result

    def cursor(self, row_factory=None):
        return _FakeCursorAll(self._fetchall_result)


class TestFetchMoortiTable:
    def test_empty_table_returns_empty_dict(self):
        conn = _FakeConnAll([])
        assert _fetch_moorti_table(conn) == {}

    def test_rows_keyed_by_nakshatra_offset(self):
        conn = _FakeConnAll([
            {"nakshatra_offset": 1, "moorti_name": "swarna", "quality_tier": 1,
             "phala_brief": "brief-1", "classical_citation": "Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28"},
            {"nakshatra_offset": 4, "moorti_name": "loha", "quality_tier": 4,
             "phala_brief": "brief-4", "classical_citation": "Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28"},
        ])
        table = _fetch_moorti_table(conn)
        assert set(table.keys()) == {1, 4}
        assert table[1]["moorti_name"] == "swarna"
        assert table[4]["quality_tier"] == 4
        assert table[4]["classical_citation"] == "Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28"
