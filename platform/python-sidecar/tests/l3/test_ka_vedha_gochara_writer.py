"""Writer-shell tests for ka_vedha_gochara — the DB-touching orchestration
around the pure logic tested in test_ka_vedha_gochara.py. Uses a minimal
FakeConn/FakeCursor (no real Postgres) — mirrors the FakeConn pattern already
used by test_ka_kota_chakra_writer.py / test_ka_moorti_nirnaya_writer.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_vedha_gochara.writer import (
    _fetch_janma_moon,
    _fetch_latta_rules,
    _fetch_malefic_scale,
    _fetch_school_tagged_vedha_pair,
    _fetch_vedha_rules,
)


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
        # dict_row: writer accesses row["fact_id"] / row["fact_value_num"] by name
        conn = _FakeConnOne(fetchone_result={"fact_id": "fact123", "fact_value_num": None})
        assert _fetch_janma_moon(conn, "chart-x") is None

    def test_present_fact_derives_sign_and_nakshatra_idx(self):
        # Moon longitude_sidereal = 327.055230133129 -> sign_idx 10 (Aquarius,
        # 0-indexed) and nak_idx 24 (Purva Bhadrapada) — the exact
        # FORENSIC-anchored value for chart 482012f1 (CLAUDE.md §B): "Moon =
        # Purva Bhadrapada" is one of the 7 FORENSIC birth anchors.
        # dict_row: writer accesses row["fact_id"] / row["fact_value_num"] by name
        conn = _FakeConnOne(fetchone_result={"fact_id": "7cf5902c6bd63146", "fact_value_num": 327.055230133129})
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


class TestFetchSchoolTaggedVedhaPair:
    """ADJUDICATION-11 Part 2: bg_sarvatobhadra_grid lookup — the currently-
    empty table returns None (honest, only-possible-today outcome)."""

    def test_empty_table_returns_none(self):
        conn = _FakeConnOne(fetchone_result=None)
        assert _fetch_school_tagged_vedha_pair(conn, 1) is None

    def test_null_cell_value_returns_none(self):
        # dict_row: writer accesses row["cell_value"] / row["school_tag"] by name
        conn = _FakeConnOne(fetchone_result={"cell_value": None, "school_tag": "some_school"})
        assert _fetch_school_tagged_vedha_pair(conn, 1) is None

    def test_populated_row_returns_pair_and_school_tag(self):
        # dict_row: writer accesses row["cell_value"] / row["school_tag"] by name
        conn = _FakeConnOne(fetchone_result={"cell_value": "15", "school_tag": "test_school_v01"})
        assert _fetch_school_tagged_vedha_pair(conn, 1) == (15, "test_school_v01")

    def test_malformed_cell_value_returns_none(self):
        # dict_row: writer accesses row["cell_value"] / row["school_tag"] by name
        conn = _FakeConnOne(fetchone_result={"cell_value": "not_a_number", "school_tag": "test_school_v01"})
        assert _fetch_school_tagged_vedha_pair(conn, 1) is None


class TestFetchLattaRules:
    def test_empty_returns_empty_dict(self):
        conn = _FakeConnAll([])
        assert _fetch_latta_rules(conn) == {}

    def test_rows_keyed_by_graha(self):
        conn = _FakeConnAll([
            {"graha": "Sun", "count_from_graha": 12, "direction": "forward",
             "effect_description": "Ruin of every business.",
             "affliction_condition": "...", "source_citation": "PG339"},
            {"graha": "Mars", "count_from_graha": 3, "direction": "forward",
             "effect_description": None,
             "affliction_condition": "...", "source_citation": "PG339"},
        ])
        rules = _fetch_latta_rules(conn)
        assert set(rules.keys()) == {"Sun", "Mars"}
        assert rules["Sun"]["count_from_graha"] == 12
        assert rules["Mars"]["effect_description"] is None
        # Ketu absent — never a key here (see brahmagyan/l0_phaladeepika_vedha.py)
        assert "Ketu" not in rules


class TestFetchMaleficScale:
    def test_empty_returns_empty_dict(self):
        conn = _FakeConnAll([])
        assert _fetch_malefic_scale(conn) == {}

    def test_rows_keyed_by_malefic_count(self):
        conn = _FakeConnAll([
            {"malefic_count": 1, "effect_grade": "fear",
             "effect_description": "...", "source_citation": "PG353"},
            {"malefic_count": 5, "effect_grade": "ignominy",
             "effect_description": "...", "source_citation": "PG353"},
        ])
        scale = _fetch_malefic_scale(conn)
        assert set(scale.keys()) == {1, 5}
        assert scale[1]["effect_grade"] == "fear"
        assert scale[5]["effect_grade"] == "ignominy"
