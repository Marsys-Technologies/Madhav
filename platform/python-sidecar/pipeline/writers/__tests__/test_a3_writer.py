"""
Tests for chart_facts_writer_a3 — A3 Mula-Lakshana chart facts writer.

Covers:
  - _build_rows / _build_lagna_rows: lagna fact_category/fact_subject/fact_key
  - _build_graha_rows: per-planet rows
  - _build_house_rows: per-house rows
  - _build_meta_rows: chart meta rows
  - Row tuple structure (19-element tuples matching INSERT SQL)
"""

import pytest
from pipeline.writers.chart_facts_writer_a3 import (
    _build_rows,
    _build_lagna_rows,
    _build_graha_rows,
    _build_house_rows,
    _build_meta_rows,
    _make_fact_id,
    _make_citation_ref,
)

# ── Sample chart output (minimal, covers all sections) ──────────────────────

SAMPLE_CHART = {
    "lagna": {
        "sign_num": "1",
        "longitude": 15.5,
        "nakshatra": "Ashwini",
        "nakshatra_lord": "KE",
        "nakshatra_pada": 1,
    },
    "navamsa": {
        "lagna_sign": 5,
        "lagna_lord": "SU",
    },
    "planets": {
        "SU": {
            "sign_num": "10",
            "house": 10,
            "nakshatra": "Shravana",
            "nakshatra_lord": "MO",
            "longitude": 280.5,
            "retrograde": False,
            "exalted": True,
            "debilitated": False,
            "dignity": "exalted",
            "shadbala": 1.45,
        },
        "MO": {
            "sign_num": "1",
            "house": 1,
            "nakshatra": "Ashwini",
            "nakshatra_lord": "KE",
            "longitude": 10.2,
            "retrograde": False,
            "vargottama": True,
        },
        "MA": {
            "sign_num": "8",
            "house": 8,
            "nakshatra": "Anuradha",
            "nakshatra_lord": "SA",
            "longitude": 218.3,
            "retrograde": False,
        },
    },
    "houses": {
        str(h): {
            "sign_num": str(h),
            "occupants": ["SU"] if h == 10 else (["MO"] if h == 1 else []),
            "lord_house": h,
            "lord_sign": h,
        }
        for h in range(1, 13)
    },
    "signs": {
        str(s): {
            "occupants": ["SU"] if s == 10 else (["MO"] if s == 1 else []),
            "aspects_received": [],
        }
        for s in range(1, 13)
    },
    "meta": {
        "sunrise": "06:12",
        "sunset": "18:30",
        "day_of_birth": "Sunday",
        "day_lord": "SU",
        "weekday_num": 0,
    },
    "ayanamsha_value": 23.15,
}


# ── Helper ─────────────────────────────────────────────────────────────────────

def _cats(rows):
    """Extract set of (fact_category, fact_subject, fact_key) from row tuples."""
    # Row tuple: (fact_id, chart_id, ayanamsha_id, build_id,
    #             category, divisional_chart, source_section, provenance,
    #             fact_category, fact_subject, fact_key,
    #             value_text, value_number, ...)
    return {(r[8], r[9], r[10]) for r in rows}


def _val(rows, cat, subj, key):
    """Return value_text for a specific (fact_category, fact_subject, fact_key)."""
    for r in rows:
        if r[8] == cat and r[9] == subj and r[10] == key:
            return r[11]  # value_text
    return None


def _num(rows, cat, subj, key):
    """Return value_number for a specific (fact_category, fact_subject, fact_key)."""
    for r in rows:
        if r[8] == cat and r[9] == subj and r[10] == key:
            return r[12]  # value_number
    return None


# ── Lagna tests ───────────────────────────────────────────────────────────────

def test_build_rows_lagna_present():
    rows = _build_rows("bid1", "cid1", "lahiri", SAMPLE_CHART)
    cats = _cats(rows)
    assert ('lagna_position', 'LAGNA', 'sign_num') in cats
    assert ('lagna_position', 'LAGNA', 'sign_name') in cats
    assert ('lagna_position', 'LAGNA', 'sign_lord') in cats
    assert ('lagna_position', 'LAGNA', 'longitude') in cats
    assert ('lagna_position', 'LAGNA', 'nakshatra') in cats
    assert ('lagna_position', 'LAGNA', 'nakshatra_lord') in cats
    assert ('lagna_position', 'LAGNA', 'nakshatra_pada') in cats


def test_build_rows_lagna_values():
    rows = _build_rows("bid1", "cid1", "lahiri", SAMPLE_CHART)
    assert _val(rows, 'lagna_position', 'LAGNA', 'sign_name') == 'Aries'
    assert _val(rows, 'lagna_position', 'LAGNA', 'sign_lord') == 'MA'
    assert _val(rows, 'lagna_position', 'LAGNA', 'nakshatra') == 'Ashwini'


def test_build_rows_navamsa_lagna():
    rows = _build_rows("bid1", "cid1", "lahiri", SAMPLE_CHART)
    cats = _cats(rows)
    assert ('lagna_position', 'NAVAMSA_LAGNA', 'sign_num') in cats
    assert ('lagna_position', 'NAVAMSA_LAGNA', 'sign_name') in cats
    assert _val(rows, 'lagna_position', 'NAVAMSA_LAGNA', 'sign_name') == 'Leo'


# ── Graha tests ───────────────────────────────────────────────────────────────

def test_build_rows_planets_present():
    rows = _build_rows("bid1", "cid1", "lahiri", SAMPLE_CHART)
    cats = _cats(rows)
    # Sun should have all position fields
    assert ('graha_position', 'SU', 'sign_num') in cats
    assert ('graha_position', 'SU', 'house') in cats
    assert ('graha_position', 'SU', 'nakshatra') in cats
    assert ('graha_position', 'SU', 'exalted') in cats
    assert ('graha_position', 'SU', 'dignity') in cats
    assert ('graha_position', 'SU', 'shadbala') in cats
    # Moon
    assert ('graha_position', 'MO', 'sign_num') in cats
    assert ('graha_position', 'MO', 'vargottama') in cats


def test_build_rows_planet_values():
    rows = _build_rows("bid1", "cid1", "lahiri", SAMPLE_CHART)
    assert _val(rows, 'graha_position', 'SU', 'sign_name') == 'Capricorn'
    assert _val(rows, 'graha_position', 'SU', 'exalted') == 'True'
    assert _val(rows, 'graha_position', 'SU', 'dignity') == 'exalted'
    assert _num(rows, 'graha_position', 'SU', 'shadbala') == pytest.approx(1.45)
    assert _val(rows, 'graha_position', 'MO', 'sign_name') == 'Aries'


def test_build_rows_missing_planet_skipped():
    """Planets not in chart_output are silently skipped (no KeyError)."""
    chart = {**SAMPLE_CHART, 'planets': {'SU': SAMPLE_CHART['planets']['SU']}}
    rows = _build_rows("bid1", "cid1", "lahiri", chart)
    cats = _cats(rows)
    assert ('graha_position', 'SU', 'sign_num') in cats
    # MO and MA should not appear
    assert ('graha_position', 'MO', 'sign_num') not in cats
    assert ('graha_position', 'MA', 'sign_num') not in cats


# ── House tests ───────────────────────────────────────────────────────────────

def test_build_rows_houses_present():
    rows = _build_rows("bid1", "cid1", "lahiri", SAMPLE_CHART)
    cats = _cats(rows)
    for h in range(1, 13):
        assert ('house_structure', f'H{h}', 'sign_num') in cats
        assert ('house_structure', f'H{h}', 'occupants') in cats
        assert ('house_structure', f'H{h}', 'sign_lord') in cats


def test_build_rows_house_10_has_sun():
    import json
    rows = _build_rows("bid1", "cid1", "lahiri", SAMPLE_CHART)
    occ_val = _val(rows, 'house_structure', 'H10', 'occupants')
    assert occ_val is not None
    occ = json.loads(occ_val)
    assert 'SU' in occ


# ── Meta tests ────────────────────────────────────────────────────────────────

def test_build_rows_meta():
    rows = _build_rows("bid1", "cid1", "lahiri", SAMPLE_CHART)
    cats = _cats(rows)
    assert ('chart_meta', 'CHART', 'sunrise') in cats
    assert ('chart_meta', 'CHART', 'sunset') in cats
    assert ('chart_meta', 'CHART', 'day_of_birth') in cats
    assert ('chart_meta', 'CHART', 'ayanamsha_id') in cats
    assert ('chart_meta', 'CHART', 'ayanamsha_value') in cats


def test_build_rows_meta_values():
    rows = _build_rows("bid1", "cid1", "lahiri", SAMPLE_CHART)
    assert _val(rows, 'chart_meta', 'CHART', 'ayanamsha_id') == 'lahiri'
    assert _num(rows, 'chart_meta', 'CHART', 'ayanamsha_value') == pytest.approx(23.15)


# ── Row structure tests ────────────────────────────────────────────────────────

def test_row_tuple_length():
    """Each row must be a 19-element tuple matching the INSERT SQL."""
    rows = _build_rows("bid1", "cid1", "lahiri", SAMPLE_CHART)
    assert len(rows) > 0
    for r in rows:
        assert len(r) == 19, f"Expected 19-element tuple, got {len(r)}: {r}"


def test_row_fact_id_unique():
    """fact_id (index 0) must be unique per row."""
    rows = _build_rows("bid1", "cid1", "lahiri", SAMPLE_CHART)
    fact_ids = [r[0] for r in rows]
    assert len(fact_ids) == len(set(fact_ids)), "Duplicate fact_ids detected"


def test_row_required_fields_non_null():
    """fact_id, chart_id, ayanamsha_id, build_id must be non-null."""
    rows = _build_rows("bid1", "cid1", "lahiri", SAMPLE_CHART)
    for r in rows:
        assert r[0], f"fact_id is empty: {r}"
        assert r[1] == "cid1"
        assert r[2] == "lahiri"
        assert r[3] == "bid1"


def test_row_source_section():
    """source_section (index 6) must be 'chart_facts_writer_a3'."""
    rows = _build_rows("bid1", "cid1", "lahiri", SAMPLE_CHART)
    for r in rows:
        assert r[6] == "chart_facts_writer_a3", f"Unexpected source_section: {r[6]}"


def test_row_verification_status():
    """verification_pass_status (index 16) must be a valid value."""
    valid = {'single', 'two_pass_verified', 'classical_match', 'divergent_flagged'}
    rows = _build_rows("bid1", "cid1", "lahiri", SAMPLE_CHART)
    for r in rows:
        assert r[16] in valid, f"Invalid verification_pass_status: {r[16]}"


# ── Empty / edge-case tests ───────────────────────────────────────────────────

def test_empty_chart_output_does_not_crash():
    """_build_rows with empty dict should return rows (at least meta rows)."""
    rows = _build_rows("bid1", "cid1", "lahiri", {})
    # Should return at least meta rows without crashing
    assert isinstance(rows, list)


def test_fact_id_deterministic():
    """Same inputs always produce the same fact_id."""
    fid1 = _make_fact_id('cat', 'subj', 'key', 'chart1', 'lahiri', 'build1')
    fid2 = _make_fact_id('cat', 'subj', 'key', 'chart1', 'lahiri', 'build1')
    assert fid1 == fid2


def test_fact_id_different_for_different_inputs():
    fid1 = _make_fact_id('cat', 'subj', 'key', 'chart1', 'lahiri', 'build1')
    fid2 = _make_fact_id('cat', 'subj', 'key2', 'chart1', 'lahiri', 'build1')
    assert fid1 != fid2
