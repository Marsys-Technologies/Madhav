"""
test_ga_condition_enrichment.py — Tests for Amendment 2 per-varga avastha enrichment.

Tests use no real DB — conn is mocked to return canned rows.

Amendment 2 adds:
  - _DIVISIONAL_DIGNITY_NORMALIZE: Title-case → canonical dignity map
  - INTRINSICALLY_D1_AVASTHAS: 3 floor categories
  - _build_per_varga_avastha_rows: builds chart_facts rows for baladi, deeptadi, floors
  - _insert_per_varga_avastha_rows: idempotent delete-then-insert into chart_facts
"""
from __future__ import annotations

import sys
import os
from unittest.mock import MagicMock, call

# ---------------------------------------------------------------------------
# Path bootstrap: ensure python-sidecar is on sys.path for direct test runs.
# ---------------------------------------------------------------------------
_sidecar_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
)
if _sidecar_root not in sys.path:
    sys.path.insert(0, _sidecar_root)

import pytest

from ga_writers.ga_condition_writer import (
    _DIVISIONAL_DIGNITY_NORMALIZE,
    INTRINSICALLY_D1_AVASTHAS,
    avastha_baladi_from_degree,
    _build_per_varga_avastha_rows,
    _insert_per_varga_avastha_rows,
    ALL_GRAHAS,
)
from ga_writers.ga_positions_writer import PLANET_TO_SUBJECT


# ---------------------------------------------------------------------------
# Constants for tests
# ---------------------------------------------------------------------------

CHART_ID     = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD_ID     = "test-build-001"
AYANAMSHA_ID = "lahiri_chitrapaksha"
COMPUTED_AT  = "2026-06-17T00:00:00+00:00"
ENG_VER      = "test-0.0.1"


# ---------------------------------------------------------------------------
# 1. _DIVISIONAL_DIGNITY_NORMALIZE — maps all 7 dignity strings correctly
# ---------------------------------------------------------------------------

class TestDivisionalDignityNormalize:
    """Verify all 7 Title-case dignity strings map to canonical lowercase keys."""

    def test_exalted(self):
        assert _DIVISIONAL_DIGNITY_NORMALIZE["Exalted"] == "exalted"

    def test_own(self):
        assert _DIVISIONAL_DIGNITY_NORMALIZE["Own"] == "own"

    def test_moolatrikona(self):
        assert _DIVISIONAL_DIGNITY_NORMALIZE["Moolatrikona"] == "moolatrikona"

    def test_friend(self):
        assert _DIVISIONAL_DIGNITY_NORMALIZE["Friend"] == "friend_sign"

    def test_neutral(self):
        assert _DIVISIONAL_DIGNITY_NORMALIZE["Neutral"] == "neutral_sign"

    def test_enemy(self):
        assert _DIVISIONAL_DIGNITY_NORMALIZE["Enemy"] == "enemy_sign"

    def test_debilitated(self):
        assert _DIVISIONAL_DIGNITY_NORMALIZE["Debilitated"] == "debilitated"

    def test_all_seven_keys_present(self):
        expected = {"Exalted", "Own", "Moolatrikona", "Friend", "Neutral", "Enemy", "Debilitated"}
        assert set(_DIVISIONAL_DIGNITY_NORMALIZE.keys()) == expected


# ---------------------------------------------------------------------------
# 2. avastha_baladi_from_degree — smoke tests
# ---------------------------------------------------------------------------

class TestAvastaBaladFromDegree:
    """
    Ranges (from avastha_baladi_from_degree docstring):
      0–6   = bala
      6–12  = kumara
      12–18 = yuva
      18–24 = vriddha
      24–30 = mrita
    """

    def test_degree_5_is_bala(self):
        assert avastha_baladi_from_degree(5.0) == "bala"

    def test_degree_0_is_bala(self):
        assert avastha_baladi_from_degree(0.0) == "bala"

    def test_degree_6_is_kumara(self):
        # Boundary at exactly 6 belongs to kumara
        assert avastha_baladi_from_degree(6.0) == "kumara"

    def test_degree_10_is_kumara(self):
        assert avastha_baladi_from_degree(10.0) == "kumara"

    def test_degree_12_is_yuva(self):
        assert avastha_baladi_from_degree(12.0) == "yuva"

    def test_degree_15_is_yuva(self):
        assert avastha_baladi_from_degree(15.0) == "yuva"

    def test_degree_18_is_vriddha(self):
        assert avastha_baladi_from_degree(18.0) == "vriddha"

    def test_degree_20_is_vriddha(self):
        assert avastha_baladi_from_degree(20.0) == "vriddha"

    def test_degree_24_is_mrita(self):
        assert avastha_baladi_from_degree(24.0) == "mrita"

    def test_degree_29_is_mrita(self):
        assert avastha_baladi_from_degree(29.9) == "mrita"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_divisionals_conn(raw_rows: list) -> MagicMock:
    """
    Return a mock conn whose execute().fetchall() returns raw_rows.
    Each row in raw_rows should be a dict with keys:
      graha, varga, fact_key, fact_value_text, fact_value_num
    """
    cursor_mock = MagicMock()
    cursor_mock.fetchall.return_value = raw_rows
    conn_mock = MagicMock()
    conn_mock.execute.return_value = cursor_mock
    return conn_mock


def _fake_divisional_rows() -> list[dict]:
    """Canned chart_divisionals rows for 3 (graha, varga) pairs."""
    return [
        # Sun D1: degree_in_sign=12.5 (yuva), dignity=Exalted
        {"graha": "Sun",  "varga": "D1", "fact_key": "degree_in_sign", "fact_value_text": None,       "fact_value_num": 12.5},
        {"graha": "Sun",  "varga": "D1", "fact_key": "dignity",        "fact_value_text": "Exalted",  "fact_value_num": None},
        # Moon D9: degree_in_sign=25.0 (mrita), dignity=Friend
        {"graha": "Moon", "varga": "D9", "fact_key": "degree_in_sign", "fact_value_text": None,       "fact_value_num": 25.0},
        {"graha": "Moon", "varga": "D9", "fact_key": "dignity",        "fact_value_text": "Friend",   "fact_value_num": None},
        # Rahu D9: degree_in_sign=5.0 (bala), dignity=Neutral
        {"graha": "Rahu", "varga": "D9", "fact_key": "degree_in_sign", "fact_value_text": None,       "fact_value_num": 5.0},
        {"graha": "Rahu", "varga": "D9", "fact_key": "dignity",        "fact_value_text": "Neutral",  "fact_value_num": None},
    ]


# ---------------------------------------------------------------------------
# 3. _build_per_varga_avastha_rows — main tests
# ---------------------------------------------------------------------------

class TestBuildPerVargaAvastaRows:
    """Tests for _build_per_varga_avastha_rows with mocked DB."""

    def _call(self, raw_rows=None):
        if raw_rows is None:
            raw_rows = _fake_divisional_rows()
        conn = _make_divisionals_conn(raw_rows)
        return _build_per_varga_avastha_rows(
            conn=conn,
            chart_id=CHART_ID,
            build_id=BUILD_ID,
            ayanamsha_id=AYANAMSHA_ID,
            computed_at=COMPUTED_AT,
            eng_ver=ENG_VER,
        )

    # ── Part A: Baladi rows ────────────────────────────────────────────────

    def test_baladi_rows_present(self):
        rows = self._call()
        baladi = [r for r in rows if r["fact_category"] == "graha_avastha_baladi_per_varga"]
        # 3 (graha, varga) pairs each have a degree_in_sign → 3 baladi rows
        assert len(baladi) == 3

    def test_baladi_sun_d1_is_yuva(self):
        rows = self._call()
        baladi = [r for r in rows
                  if r["fact_category"] == "graha_avastha_baladi_per_varga"
                  and r["fact_subject"] == "SUN"
                  and r["fact_key"] == "D1"]
        assert len(baladi) == 1
        assert baladi[0]["fact_value_text"] == "yuva"  # degree=12.5

    def test_baladi_moon_d9_is_mrita(self):
        rows = self._call()
        baladi = [r for r in rows
                  if r["fact_category"] == "graha_avastha_baladi_per_varga"
                  and r["fact_subject"] == "MOON"
                  and r["fact_key"] == "D9"]
        assert len(baladi) == 1
        assert baladi[0]["fact_value_text"] == "mrita"  # degree=25.0

    def test_baladi_rahu_d9_is_bala(self):
        rows = self._call()
        baladi = [r for r in rows
                  if r["fact_category"] == "graha_avastha_baladi_per_varga"
                  # A1 fix (2026-08-08): fact_subject is now the system-A
                  # short code (PLANET_TO_SUBJECT), not graha.upper() —
                  # "RAH_MEAN", never "RAHU".
                  and r["fact_subject"] == "RAH_MEAN"
                  and r["fact_key"] == "D9"]
        assert len(baladi) == 1
        assert baladi[0]["fact_value_text"] == "bala"  # degree=5.0

    # ── Part B: Deeptadi rows ──────────────────────────────────────────────

    def test_deeptaadi_rows_present(self):
        rows = self._call()
        deeptaadi = [r for r in rows if r["fact_category"] == "graha_avastha_deeptaadi_per_varga"]
        # 3 pairs each have a dignity_status → 3 deeptaadi rows
        assert len(deeptaadi) == 3

    def test_deeptaadi_sun_exalted_is_deepta(self):
        rows = self._call()
        deeptaadi = [r for r in rows
                     if r["fact_category"] == "graha_avastha_deeptaadi_per_varga"
                     and r["fact_subject"] == "SUN"
                     and r["fact_key"] == "D1"]
        assert len(deeptaadi) == 1
        # Exalted → deepta
        assert deeptaadi[0]["fact_value_text"] == "deepta"

    def test_deeptaadi_moon_friend_is_swastha(self):
        rows = self._call()
        deeptaadi = [r for r in rows
                     if r["fact_category"] == "graha_avastha_deeptaadi_per_varga"
                     and r["fact_subject"] == "MOON"
                     and r["fact_key"] == "D9"]
        assert len(deeptaadi) == 1
        # Friend → friend_sign → swastha
        assert deeptaadi[0]["fact_value_text"] == "swastha"

    def test_deeptaadi_rahu_neutral_is_shanta(self):
        rows = self._call()
        deeptaadi = [r for r in rows
                     if r["fact_category"] == "graha_avastha_deeptaadi_per_varga"
                     # A1 fix: system-A short code "RAH_MEAN", not "RAHU".
                     and r["fact_subject"] == "RAH_MEAN"
                     and r["fact_key"] == "D9"]
        assert len(deeptaadi) == 1
        # Neutral → neutral_sign → shanta
        assert deeptaadi[0]["fact_value_text"] == "shanta"

    def test_deeptaadi_verification_status(self):
        rows = self._call()
        for r in rows:
            if r["fact_category"] == "graha_avastha_deeptaadi_per_varga":
                assert r["verification_pass_status"] == "computed_extension"

    # ── Part C: Floor rows ─────────────────────────────────────────────────

    def test_floor_rows_count(self):
        """9 grahas × 3 floor categories = 27 floor rows."""
        rows = self._call()
        floor_cats = {cat for cat, _ in INTRINSICALLY_D1_AVASTHAS}
        floor_rows = [r for r in rows if r["fact_category"] in floor_cats]
        assert len(floor_rows) == 27  # 9 × 3

    def test_floor_rows_fact_key_is_D_ALL(self):
        rows = self._call()
        floor_cats = {cat for cat, _ in INTRINSICALLY_D1_AVASTHAS}
        for r in rows:
            if r["fact_category"] in floor_cats:
                assert r["fact_key"] == "D_ALL", (
                    f"Floor row has fact_key={r['fact_key']!r}, expected 'D_ALL'"
                )

    def test_floor_rows_verification_status(self):
        rows = self._call()
        floor_cats = {cat for cat, _ in INTRINSICALLY_D1_AVASTHAS}
        for r in rows:
            if r["fact_category"] in floor_cats:
                assert r["verification_pass_status"] == "floored"

    def test_floor_rows_all_nine_grahas(self):
        rows = self._call()
        floor_cats = {cat for cat, _ in INTRINSICALLY_D1_AVASTHAS}
        floor_subjects = {r["fact_subject"] for r in rows if r["fact_category"] in floor_cats}
        # A1 fix (2026-08-08): fact_subject is the system-A short code
        # (PLANET_TO_SUBJECT), not a bare graha.upper() — {g.upper() for g in
        # ALL_GRAHAS} produced "MARS"/"MERCURY"/.../"RAHU"/"KETU" before the
        # fix; PLANET_TO_SUBJECT.values() is the correct expected set.
        expected = set(PLANET_TO_SUBJECT[g] for g in ALL_GRAHAS)
        assert floor_subjects == expected

    def test_floor_rows_all_three_categories(self):
        rows = self._call()
        floor_cats = {cat for cat, _ in INTRINSICALLY_D1_AVASTHAS}
        present_cats = {r["fact_category"] for r in rows if r["fact_category"] in floor_cats}
        assert present_cats == floor_cats

    # ── No Lagna in output ─────────────────────────────────────────────────

    def test_no_lagna_rows(self):
        # Even if DB returned Lagna rows (it shouldn't), none should appear in output
        rows = self._call()
        for r in rows:
            assert r["fact_subject"] != "LAGNA", f"Lagna row found: {r}"

    # ── Rahu/Ketu included in Parts A and B ───────────────────────────────

    def test_rahu_in_baladi_output(self):
        rows = self._call()
        baladi_subjects = {r["fact_subject"] for r in rows
                           if r["fact_category"] == "graha_avastha_baladi_per_varga"}
        # A1 fix: system-A short code "RAH_MEAN", not "RAHU".
        assert "RAH_MEAN" in baladi_subjects
        assert "RAHU" not in baladi_subjects

    def test_rahu_in_deeptaadi_output(self):
        rows = self._call()
        deeptaadi_subjects = {r["fact_subject"] for r in rows
                              if r["fact_category"] == "graha_avastha_deeptaadi_per_varga"}
        # A1 fix: system-A short code "RAH_MEAN", not "RAHU".
        assert "RAH_MEAN" in deeptaadi_subjects
        assert "RAHU" not in deeptaadi_subjects

    # ── Metadata fields ────────────────────────────────────────────────────

    def test_all_rows_have_chart_id(self):
        rows = self._call()
        for r in rows:
            assert r["chart_id"] == CHART_ID

    def test_all_rows_have_ayanamsha_id(self):
        rows = self._call()
        for r in rows:
            assert r["ayanamsha_id"] == AYANAMSHA_ID

    def test_all_rows_have_unique_fact_ids(self):
        rows = self._call()
        fact_ids = [r["fact_id"] for r in rows]
        assert len(fact_ids) == len(set(fact_ids)), "fact_ids are not unique"

    def test_empty_db_result_returns_only_floors(self):
        """When chart_divisionals returns no rows, only the 27 floor rows are produced."""
        rows = self._call(raw_rows=[])
        assert len(rows) == 27
        floor_cats = {cat for cat, _ in INTRINSICALLY_D1_AVASTHAS}
        for r in rows:
            assert r["fact_category"] in floor_cats


# ---------------------------------------------------------------------------
# 4. _insert_per_varga_avastha_rows — delete-then-insert
# ---------------------------------------------------------------------------

class TestInsertPerVargaAvastaRows:
    """Verify the idempotent delete-then-insert pattern."""

    def _make_rows(self):
        return [
            {
                "fact_id":                 "aaa",
                "chart_id":                CHART_ID,
                "ayanamsha_id":            AYANAMSHA_ID,
                "build_id":                BUILD_ID,
                "fact_category":           "graha_avastha_baladi_per_varga",
                "fact_subject":            "SUN",
                "fact_key":                "D1",
                "fact_value_text":         "yuva",
                "fact_value_num":          None,
                "fact_value_jsonb":        None,
                "unit":                    None,
                "citation_ref":            None,
                "citation_human":          None,
                "source_calculation":      "test",
                "verification_pass_status":"computed_extension",
                "engine_version":          ENG_VER,
                "computed_at":             COMPUTED_AT,
            }
        ]

    def test_calls_delete_before_insert(self):
        conn = MagicMock()
        rows = self._make_rows()
        _insert_per_varga_avastha_rows(conn, rows)

        # conn.execute should have been called at least twice (once DELETE, once INSERT)
        assert conn.execute.call_count >= 2

    def test_delete_sql_contains_chart_facts(self):
        conn = MagicMock()
        rows = self._make_rows()
        _insert_per_varga_avastha_rows(conn, rows)

        calls = conn.execute.call_args_list
        delete_calls = [c for c in calls if "DELETE" in str(c)]
        assert len(delete_calls) >= 1
        # The DELETE should reference chart_facts
        assert any("chart_facts" in str(c) for c in delete_calls)

    def test_insert_sql_contains_chart_facts(self):
        conn = MagicMock()
        rows = self._make_rows()
        _insert_per_varga_avastha_rows(conn, rows)

        calls = conn.execute.call_args_list
        insert_calls = [c for c in calls if "INSERT" in str(c)]
        assert len(insert_calls) >= 1

    def test_no_op_on_empty_rows(self):
        conn = MagicMock()
        _insert_per_varga_avastha_rows(conn, [])
        conn.execute.assert_not_called()
