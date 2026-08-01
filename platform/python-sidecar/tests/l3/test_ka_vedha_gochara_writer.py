"""Writer-shell tests for ka_vedha_gochara — the DB-touching orchestration
around the pure logic tested in test_ka_vedha_gochara.py. Uses a minimal
FakeConn/FakeCursor (no real Postgres) — mirrors the FakeConn pattern already
used by test_ka_kota_chakra_writer.py / test_ka_moorti_nirnaya_writer.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_vedha_gochara.writer import _fetch_janma_moon, _fetch_vedha_rules


class _FakeCursorOne:
    def __init__(self, fetchone_result=None):
        self._fetchone_result = fetchone_result

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        pass

    def fetchone(self):
        return self._fetchone_result


class _FakeConnOne:
    def __init__(self, fetchone_result=None):
        self._fetchone_result = fetchone_result

    def cursor(self, row_factory=None):
        return _FakeCursorOne(self._fetchone_result)


class TestFetchJanmaMoon:
    def test_missing_fact_returns_none(self):
        conn = _FakeConnOne(fetchone_result=None)
        assert _fetch_janma_moon(conn, "chart-x") is None

    def test_null_value_returns_none(self):
        conn = _FakeConnOne(fetchone_result=("fact123", None))
        assert _fetch_janma_moon(conn, "chart-x") is None

    def test_present_fact_derives_sign_and_nakshatra_idx(self):
        # Moon longitude_sidereal = 327.055230133129 -> sign_idx 10 (Aquarius,
        # 0-indexed) and nak_idx 24 (Purva Bhadrapada) — the exact
        # FORENSIC-anchored value for chart 482012f1 (CLAUDE.md §B): "Moon =
        # Purva Bhadrapada" is one of the 7 FORENSIC birth anchors.
        conn = _FakeConnOne(fetchone_result=("7cf5902c6bd63146", 327.055230133129))
        result = _fetch_janma_moon(conn, "482012f1-710e-4a25-994a-93821f5871aa")
        assert result == (10, 24, "7cf5902c6bd63146")


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


class TestFetchVedhaRules:
    def test_empty_returns_empty_dict(self):
        conn = _FakeConnAll([])
        assert _fetch_vedha_rules(conn) == {}

    def test_rows_keyed_by_lowercase_graha_and_house(self):
        conn = _FakeConnAll([
            {"graha": "Sun", "primary_house": 3, "vedha_house": 9,
             "phala": "Courage, travel, gain from siblings",
             "classical_citation": "BPHS Ch.29"},
            {"graha": "Moon", "primary_house": 1, "vedha_house": 5,
             "phala": "Good health, mental peace",
             "classical_citation": "BPHS Ch.29"},
        ])
        rules = _fetch_vedha_rules(conn)
        assert set(rules.keys()) == {("sun", 3), ("moon", 1)}
        assert rules[("sun", 3)]["vedha_house"] == 9
        assert rules[("moon", 1)]["phala"] == "Good health, mental peace"
