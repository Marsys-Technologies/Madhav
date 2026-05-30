"""
Tests for sade_sati_writer.py — A9 (G3-06)
Sade Sati cycle phase computation + chart_facts upsert.

All tests use unittest.mock.MagicMock — no real DB required.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Ensure the pipeline package is importable from this test location
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."),
)

from pipeline.writers.sade_sati_writer import (
    write,
    _compute_sade_sati_rows,
    _build_approximate_sign_changes,
    _year_frac_to_date,
    _SIGN_NAMES,
    _PHASE_LABEL,
    ENGINE_VERSION,
)

# ── Helper factories ───────────────────────────────────────────────────────────

def _moon(sign_name: str, sign_num: int) -> dict:
    return {"id": "moon", "sign": sign_name, "sign_num": sign_num}


def _saturn_period(sign_name: str, sign_num: int, start: str, end: str) -> dict:
    return {"sign": sign_name, "sign_num": sign_num, "start_date": start, "end_date": end}


def _chart_output(moon_sign: str, moon_sign_num: int, saturn_changes=None) -> dict:
    out = {"planets": [_moon(moon_sign, moon_sign_num)]}
    if saturn_changes is not None:
        out["saturn_sign_changes"] = saturn_changes
    return out


def _run_write(chart_output, build_id="bld-test", chart_id="chart-00000001",
               ayanamsha_id="lahiri"):
    conn = MagicMock()
    with patch(
        "pipeline.writers.sade_sati_writer._upsert_chart_facts"
    ) as mock_upsert:
        result = write(build_id, chart_id, ayanamsha_id, chart_output, conn)
        rows = mock_upsert.call_args[0][1] if mock_upsert.called else []
    return result, rows


def _get_rows_by_key(rows, fact_key):
    return [r for r in rows if r[10] == fact_key]


def _get_rows_by_subject(rows, fact_subject):
    return [r for r in rows if r[9] == fact_subject]


def _get_rows_by_category(rows, fact_category):
    return [r for r in rows if r[8] == fact_category]


# ── 1. Return type ────────────────────────────────────────────────────────────

def test_write_returns_int():
    result, _ = _run_write(_chart_output("Aquarius", 10))
    assert isinstance(result, int)


# ── 2. Empty planets — no crash, only summary row ─────────────────────────────

def test_empty_planets_no_crash():
    conn = MagicMock()
    with patch("pipeline.writers.sade_sati_writer._upsert_chart_facts"):
        result = write("bld1", "chart-000", "lahiri", {"planets": []}, conn)
    assert isinstance(result, int)
    assert result >= 1   # at least the fallback summary row


def test_empty_planets_returns_small_number():
    conn = MagicMock()
    with patch("pipeline.writers.sade_sati_writer._upsert_chart_facts"):
        result = write("bld1", "chart-000", "lahiri", {"planets": []}, conn)
    assert result <= 5   # not a full cycle load — just 1 summary row


# ── 3. Moon in Aquarius (sign_num=10) → Sade Sati signs ──────────────────────

def test_aquarius_moon_12th_sign_is_capricorn():
    # 12th phase = (10 - 1) % 12 = 9 = Capricorn
    approx = _build_approximate_sign_changes(10)
    sign_nums = [p["sign_num"] for p in approx]
    assert 9 in sign_nums, "Capricorn (sign_num=9) must be in Sade Sati for Aquarius Moon"


def test_aquarius_moon_natal_sign_is_aquarius():
    approx = _build_approximate_sign_changes(10)
    sign_nums = [p["sign_num"] for p in approx]
    assert 10 in sign_nums, "Aquarius (sign_num=10) must be in Sade Sati for Aquarius Moon"


def test_aquarius_moon_2nd_sign_is_pisces():
    # 2nd phase = (10 + 1) % 12 = 11 = Pisces
    approx = _build_approximate_sign_changes(10)
    sign_nums = [p["sign_num"] for p in approx]
    assert 11 in sign_nums, "Pisces (sign_num=11) must be in Sade Sati for Aquarius Moon"


# ── 4. Moon in Aries (sign_num=0) ────────────────────────────────────────────

def test_aries_moon_12th_sign_is_pisces():
    # (0 - 1) % 12 = 11 = Pisces
    approx = _build_approximate_sign_changes(0)
    sign_nums = {p["sign_num"] for p in approx}
    assert 11 in sign_nums, "Pisces wraps around correctly for Aries Moon"


def test_aries_moon_2nd_sign_is_taurus():
    approx = _build_approximate_sign_changes(0)
    sign_nums = {p["sign_num"] for p in approx}
    assert 1 in sign_nums, "Taurus (2nd from Aries) must be in Sade Sati"


# ── 5. Moon in Pisces (sign_num=11) wrap-around ───────────────────────────────

def test_pisces_moon_12th_sign_wraps_to_aquarius():
    # (11 - 1) % 12 = 10 = Aquarius
    approx = _build_approximate_sign_changes(11)
    sign_nums = {p["sign_num"] for p in approx}
    assert 10 in sign_nums, "Aquarius must wrap correctly for Pisces Moon"


def test_pisces_moon_2nd_sign_wraps_to_aries():
    # (11 + 1) % 12 = 0 = Aries
    approx = _build_approximate_sign_changes(11)
    sign_nums = {p["sign_num"] for p in approx}
    assert 0 in sign_nums, "Aries must wrap correctly for Pisces Moon (2nd from Pisces)"


# ── 6. Summary row stored with correct sign name ──────────────────────────────

def test_summary_row_has_correct_sign_name():
    result, rows = _run_write(_chart_output("Aquarius", 10))
    summary = _get_rows_by_subject(rows, "natal_moon")
    assert len(summary) == 1
    assert summary[0][11] == "Aquarius"   # value_text


def test_summary_row_sign_number_correct():
    result, rows = _run_write(_chart_output("Aquarius", 10))
    summary = _get_rows_by_subject(rows, "natal_moon")
    assert summary[0][12] == 10.0   # value_number


# ── 7. All rows have fact_category = 'sade_sati' ─────────────────────────────

def test_all_rows_fact_category_sade_sati():
    result, rows = _run_write(_chart_output("Aquarius", 10))
    for r in rows:
        assert r[8] == "sade_sati", f"Expected fact_category='sade_sati', got {r[8]!r}"


# ── 8. Phase keys 12th_phase, natal_phase, 2nd_phase all appear ───────────────

def test_all_phase_keys_present_with_saturn_sign_changes():
    saturn = [
        _saturn_period("Capricorn",  9, "2017-01-26", "2020-01-24"),
        _saturn_period("Aquarius",  10, "2020-01-24", "2023-03-07"),
        _saturn_period("Pisces",    11, "2023-03-07", "2025-10-20"),
    ]
    result, rows = _run_write(_chart_output("Aquarius", 10, saturn))
    keys = {r[10] for r in rows}
    assert "12th_phase" in keys
    assert "natal_phase" in keys
    assert "2nd_phase" in keys


# ── 9. duration_years > 0 for each phase row ─────────────────────────────────

def test_phase_duration_years_positive():
    saturn = [
        _saturn_period("Capricorn",  9, "2017-01-26", "2020-01-24"),
        _saturn_period("Aquarius",  10, "2020-01-24", "2023-03-07"),
        _saturn_period("Pisces",    11, "2023-03-07", "2025-10-20"),
    ]
    result, rows = _run_write(_chart_output("Aquarius", 10, saturn))
    phase_rows = [r for r in rows if r[9] != "natal_moon"]
    assert len(phase_rows) >= 3
    for r in phase_rows:
        assert r[12] is not None and r[12] > 0, f"duration_years must be positive, got {r[12]}"


# ── 10. With full saturn_sign_changes: correct phases detected ────────────────

def test_correct_phases_detected_from_saturn_sign_changes():
    saturn = [
        _saturn_period("Sagittarius", 8, "2014-11-02", "2017-01-26"),  # not Sade Sati for Aquarius Moon
        _saturn_period("Capricorn",   9, "2017-01-26", "2020-01-24"),   # 12th phase
        _saturn_period("Aquarius",   10, "2020-01-24", "2023-03-07"),   # natal phase
        _saturn_period("Pisces",     11, "2023-03-07", "2025-10-20"),   # 2nd phase
        _saturn_period("Aries",       0, "2025-10-20", "2028-03-04"),   # not Sade Sati
    ]
    result, rows = _run_write(_chart_output("Aquarius", 10, saturn))
    phase_rows = [r for r in rows if r[9] != "natal_moon"]
    phase_keys = {r[10] for r in phase_rows}
    assert "12th_phase" in phase_keys
    assert "natal_phase" in phase_keys
    assert "2nd_phase" in phase_keys

    # Verify Sagittarius and Aries periods are NOT included
    value_texts = [r[11] for r in phase_rows]
    assert all("2014" not in (vt or "") for vt in value_texts), "Sagittarius should be excluded"
    assert all("2025-10-20 to 2028" not in (vt or "") for vt in value_texts), "Aries should be excluded"


def test_12th_phase_value_text_contains_correct_dates():
    saturn = [
        _saturn_period("Capricorn", 9, "2017-01-26", "2020-01-24"),
        _saturn_period("Aquarius", 10, "2020-01-24", "2023-03-07"),
        _saturn_period("Pisces",   11, "2023-03-07", "2025-10-20"),
    ]
    result, rows = _run_write(_chart_output("Aquarius", 10, saturn))
    twelfth_rows = _get_rows_by_key(rows, "12th_phase")
    assert len(twelfth_rows) >= 1
    assert "2017-01-26" in twelfth_rows[0][11]
    assert "2020-01-24" in twelfth_rows[0][11]


# ── 11. citation_human contains 'BPHS' ───────────────────────────────────────

def test_citation_human_contains_bphs():
    result, rows = _run_write(_chart_output("Aquarius", 10))
    for r in rows:
        assert "BPHS" in (r[14] or ""), f"citation_human must contain 'BPHS', got {r[14]!r}"


# ── 12. Approximate fallback generates rows ────────────────────────────────────

def test_approximate_fallback_generates_cycle_rows():
    # No saturn_sign_changes key → fallback
    result, rows = _run_write(_chart_output("Aquarius", 10))
    assert result > 1, "Approximate fallback must produce more than just the summary row"


def test_approximate_fallback_covers_three_ss_signs():
    approx = _build_approximate_sign_changes(10)
    ss_signs_found = {p["sign_num"] for p in approx}
    assert 9 in ss_signs_found   # Capricorn
    assert 10 in ss_signs_found  # Aquarius
    assert 11 in ss_signs_found  # Pisces


# ── 13. _year_frac_to_date basic sanity ───────────────────────────────────────

def test_year_frac_to_date_format():
    d = _year_frac_to_date(2020.0)
    assert d.startswith("2020-")
    parts = d.split("-")
    assert len(parts) == 3


def test_year_frac_to_date_mid_year():
    d = _year_frac_to_date(2020.5)
    assert d.startswith("2020-")
    # Mid-year should be around July
    month = int(d.split("-")[1])
    assert 6 <= month <= 8


# ── 14. _compute_sade_sati_rows cycle grouping ────────────────────────────────

def test_two_cycles_produce_separate_cycle_subjects():
    # Two complete cycles: one historical, one current
    saturn = [
        # Cycle 0 (historical ~1990s)
        _saturn_period("Capricorn",  9, "1990-01-01", "1993-01-01"),
        _saturn_period("Aquarius",  10, "1993-01-01", "1995-07-01"),
        _saturn_period("Pisces",    11, "1995-07-01", "1998-01-01"),
        # Cycle 1 (current ~2017+)
        _saturn_period("Capricorn",  9, "2017-01-26", "2020-01-24"),
        _saturn_period("Aquarius",  10, "2020-01-24", "2023-03-07"),
        _saturn_period("Pisces",    11, "2023-03-07", "2025-10-20"),
    ]
    rows = _compute_sade_sati_rows(
        "chart-001", "lahiri", "bld1", 10, "Aquarius", saturn
    )
    subjects = {r[9] for r in rows}
    assert "cycle_0" in subjects
    assert "cycle_1" in subjects


# ── 15. Row tuple structure (spot-check positions) ────────────────────────────

def test_row_tuple_engine_version():
    result, rows = _run_write(_chart_output("Aquarius", 10))
    # ENGINE_VERSION is at position 17 in the tuple
    for r in rows:
        assert r[17] == ENGINE_VERSION


def test_row_tuple_divisional_chart_d1():
    result, rows = _run_write(_chart_output("Aquarius", 10))
    # divisional_chart is at position 5
    for r in rows:
        assert r[5] == "D1"


def test_row_tuple_source_section():
    result, rows = _run_write(_chart_output("Aquarius", 10))
    # source_section is at position 6
    for r in rows:
        assert r[6] == "sade_sati_writer"
