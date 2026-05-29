"""
Tests for A4-S5: emit_solar_context() and emit_calendrical()
Native birth date: 1984-02-05
"""
import pytest
from pipeline.writers.panchanga_writer_a4 import (
    emit_solar_context,
    emit_calendrical,
    RITU_TABLE,
    JOVIAN_CYCLE,
    MASA_NAMES,
    _find_sankranti,
)

CHART_ID = "aaaaaaaa-0000-0000-0000-000000000001"
BUILD_ID = "test-build-a4-s5"
NATIVE_DATE = "1984-02-05"


# ── emit_solar_context ────────────────────────────────────────────────────────

class TestEmitSolarContext:
    def test_returns_seven_rows(self):
        rows = emit_solar_context(CHART_ID, BUILD_ID, NATIVE_DATE)
        assert len(rows) == 7

    def test_all_invariant_ayanamsha(self):
        rows = emit_solar_context(CHART_ID, BUILD_ID, NATIVE_DATE)
        for r in rows:
            assert r['ayanamsha_id'] == 'INVARIANT'

    def test_ayana_is_uttarayana_for_february(self):
        rows = emit_solar_context(CHART_ID, BUILD_ID, NATIVE_DATE)
        ayana_row = next(r for r in rows if r['fact_key'] == 'ayana')
        assert ayana_row['fact_value_text'] == 'Uttarayana'

    def test_ritu_is_shishir_for_february(self):
        rows = emit_solar_context(CHART_ID, BUILD_ID, NATIVE_DATE)
        ritu_row = next(r for r in rows if r['fact_key'] == 'ritu')
        assert ritu_row['fact_value_text'] == 'Shishir'

    def test_last_sankranti_is_makara(self):
        rows = emit_solar_context(CHART_ID, BUILD_ID, NATIVE_DATE)
        row = next(r for r in rows if r['fact_key'] == 'last_sankranti_name')
        assert row['fact_value_text'] == 'Makara'

    def test_next_sankranti_is_kumbha(self):
        rows = emit_solar_context(CHART_ID, BUILD_ID, NATIVE_DATE)
        row = next(r for r in rows if r['fact_key'] == 'next_sankranti_name')
        assert row['fact_value_text'] == 'Kumbha'

    def test_solar_arc_is_positive(self):
        rows = emit_solar_context(CHART_ID, BUILD_ID, NATIVE_DATE)
        row = next(r for r in rows if r['fact_key'] == 'solar_arc_into_current_sign_deg')
        assert row['fact_value_num'] is not None
        assert row['fact_value_num'] > 0

    def test_solar_arc_reasonable_for_native(self):
        # Birth Feb 5, last sankranti ~Jan 14 → ~22 days → ~21-23 degrees
        rows = emit_solar_context(CHART_ID, BUILD_ID, NATIVE_DATE)
        row = next(r for r in rows if r['fact_key'] == 'solar_arc_into_current_sign_deg')
        assert 18.0 <= row['fact_value_num'] <= 25.0

    def test_fact_category(self):
        rows = emit_solar_context(CHART_ID, BUILD_ID, NATIVE_DATE)
        for r in rows:
            assert r['fact_category'] == 'panchanga_solar_context'
            assert r['fact_subject'] == 'SOLAR_CONTEXT_BIRTH'

    def test_dakshinayana_for_july(self):
        rows = emit_solar_context(CHART_ID, BUILD_ID, "1984-07-15")
        ayana_row = next(r for r in rows if r['fact_key'] == 'ayana')
        assert ayana_row['fact_value_text'] == 'Dakshinayana'

    def test_ritu_table_completeness(self):
        for m in range(1, 13):
            assert m in RITU_TABLE


# ── emit_calendrical ──────────────────────────────────────────────────────────

class TestEmitCalendrical:
    def test_returns_seven_rows(self):
        rows = emit_calendrical(CHART_ID, BUILD_ID, NATIVE_DATE)
        assert len(rows) == 7

    def test_all_invariant_ayanamsha(self):
        rows = emit_calendrical(CHART_ID, BUILD_ID, NATIVE_DATE)
        for r in rows:
            assert r['ayanamsha_id'] == 'INVARIANT'

    def test_vikram_samvat_native(self):
        # 1984 + 57 = 2041; acceptance criteria allows ±1 (2040)
        rows = emit_calendrical(CHART_ID, BUILD_ID, NATIVE_DATE)
        row = next(r for r in rows if r['fact_key'] == 'vikram_samvat')
        assert abs(row['fact_value_num'] - 2040) <= 1

    def test_shaka_samvat_native(self):
        # 1984 - 78 = 1906; acceptance criteria allows ±1 (1905)
        rows = emit_calendrical(CHART_ID, BUILD_ID, NATIVE_DATE)
        row = next(r for r in rows if r['fact_key'] == 'shaka_samvat')
        assert abs(row['fact_value_num'] - 1905) <= 1

    def test_kali_samvat_native(self):
        # 1984 + 3101 = 5085; acceptance criteria allows ±1 (5084)
        rows = emit_calendrical(CHART_ID, BUILD_ID, NATIVE_DATE)
        row = next(r for r in rows if r['fact_key'] == 'kali_samvat')
        assert abs(row['fact_value_num'] - 5084) <= 1

    def test_jovian_cycle_name_is_string(self):
        rows = emit_calendrical(CHART_ID, BUILD_ID, NATIVE_DATE)
        row = next(r for r in rows if r['fact_key'] == 'jovian_60yr_cycle_name')
        assert row['fact_value_text'] in JOVIAN_CYCLE

    def test_jovian_position_range(self):
        rows = emit_calendrical(CHART_ID, BUILD_ID, NATIVE_DATE)
        row = next(r for r in rows if r['fact_key'] == 'jovian_60yr_position')
        assert 1 <= row['fact_value_num'] <= 60

    def test_masa_purnimanta_and_amanta_equal(self):
        rows = emit_calendrical(CHART_ID, BUILD_ID, NATIVE_DATE)
        p = next(r for r in rows if r['fact_key'] == 'masa_purnimanta')
        a = next(r for r in rows if r['fact_key'] == 'masa_amanta')
        assert p['fact_value_text'] == a['fact_value_text']

    def test_masa_is_valid_name(self):
        rows = emit_calendrical(CHART_ID, BUILD_ID, NATIVE_DATE)
        row = next(r for r in rows if r['fact_key'] == 'masa_purnimanta')
        assert row['fact_value_text'] in MASA_NAMES

    def test_fact_category(self):
        rows = emit_calendrical(CHART_ID, BUILD_ID, NATIVE_DATE)
        for r in rows:
            assert r['fact_category'] == 'panchanga_calendrical'
            assert r['fact_subject'] == 'CALENDRICAL_BIRTH'

    def test_jovian_cycle_has_60_entries(self):
        assert len(JOVIAN_CYCLE) == 60


# ── _find_sankranti helper ────────────────────────────────────────────────────

class TestFindSankranti:
    def test_native_birth_date(self):
        last_name, last_iso, next_name, next_iso = _find_sankranti(1984, 2, 5)
        assert last_name == 'Makara'
        assert next_name == 'Kumbha'

    def test_last_before_birth(self):
        last_name, last_iso, next_name, next_iso = _find_sankranti(1984, 2, 5)
        assert last_iso <= '1984-02-05'

    def test_next_after_birth(self):
        last_name, last_iso, next_name, next_iso = _find_sankranti(1984, 2, 5)
        assert next_iso > '1984-02-05'
