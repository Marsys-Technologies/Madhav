"""
Tests for t1_structural_writer.py — A8-S1
Aspect matrix (Parashari + Jaimini) + Dispositor chains.

All tests use unittest.mock.MagicMock() — no real DB connection required.
"""
import pytest
from unittest.mock import MagicMock, patch

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pipeline.writers.t1_structural_writer import (
    write,
    _compute_parashari_aspects,
    _compute_jaimini_rasi_drishti,
    _compute_dispositor_chains,
    _dispositor_chain,
    _are_adjacent,
    _JAIMINI_PAIRS,
    PARASHARI_SPECIAL_ASPECTS,
    SIGN_LORDS,
    _ALL_GRAHAS,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_chart_output(planets):
    """Build a minimal chart_output dict from a list of planet dicts."""
    return {"planets": planets}


def _planet(pid, house, sign):
    return {"id": pid, "house": house, "sign": sign}


def _run_write(planets, build_id="bld1", chart_id="chart-uuid-abcdef12", ayanamsha_id="lahiri"):
    conn = MagicMock()
    chart_output = _make_chart_output(planets)
    with patch("pipeline.writers.t1_structural_writer._upsert_chart_facts") as mock_upsert:
        result = write(build_id, chart_id, ayanamsha_id, chart_output, conn)
        rows = mock_upsert.call_args[0][1] if mock_upsert.called else []
    return result, rows


def _parashari_rows(planets, chart_id="chart-uuid-abcdef12", ayanamsha_id="lahiri", build_id="bld1"):
    planet_dict = {p["id"]: p for p in planets}
    return _compute_parashari_aspects(chart_id, ayanamsha_id, build_id, planet_dict)


def _jaimini_rows(chart_id="chart-uuid-abcdef12", ayanamsha_id="lahiri", build_id="bld1"):
    return _compute_jaimini_rasi_drishti(chart_id, ayanamsha_id, build_id, {})


def _dispositor_rows(planets, chart_id="chart-uuid-abcdef12", ayanamsha_id="lahiri", build_id="bld1"):
    planet_dict = {p["id"]: p for p in planets}
    return _compute_dispositor_chains(chart_id, ayanamsha_id, build_id, planet_dict)


# Row column indices (match _row() tuple order):
# 0: fact_id, 1: chart_id, 2: ayanamsha_id, 3: build_id,
# 4: category (legacy), 5: divisional_chart, 6: source_section, 7: provenance,
# 8: fact_category, 9: fact_subject, 10: fact_key,
# 11: value_text, 12: value_number,
# 13: citation_ref, 14: citation_human,
# 15: source_calculation, 16: verification_pass_status,
# 17: engine_version, 18: computed_at_iso

IDX_FACT_CATEGORY = 8
IDX_FACT_SUBJECT  = 9
IDX_FACT_KEY      = 10
IDX_VALUE_TEXT    = 11
IDX_VALUE_NUMBER  = 12
IDX_CITATION_HUM  = 14


# ══════════════════════════════════════════════════════════════════════════════
# 1. write() return type and basic contract
# ══════════════════════════════════════════════════════════════════════════════

def test_write_returns_int():
    result, _ = _run_write([_planet("sun", 1, "aries")])
    assert isinstance(result, int)


def test_write_returns_positive_int_with_planets():
    result, _ = _run_write([_planet("sun", 1, "aries"), _planet("moon", 2, "taurus")])
    assert result > 0


def test_empty_planets_returns_zero():
    conn = MagicMock()
    with patch("pipeline.writers.t1_structural_writer._upsert_chart_facts") as mock_upsert:
        result = write("bld1", "chart-uuid-abcdef12", "lahiri", {"planets": []}, MagicMock())
        assert result == 0
        mock_upsert.assert_not_called()


def test_empty_planets_no_crash():
    """write() with empty planets must not raise any exception."""
    conn = MagicMock()
    try:
        write("bld1", "chart-uuid-abcdef12", "lahiri", {"planets": []}, conn)
    except Exception as exc:
        pytest.fail(f"write() raised unexpectedly with empty planets: {exc}")


def test_missing_planets_key_returns_zero():
    """chart_output with no 'planets' key is treated as empty."""
    result, _ = _run_write.__wrapped__ if hasattr(_run_write, "__wrapped__") else (None, None)
    conn = MagicMock()
    with patch("pipeline.writers.t1_structural_writer._upsert_chart_facts"):
        result = write("bld1", "chart-uuid-abcdef12", "lahiri", {}, conn)
    assert result == 0


# ══════════════════════════════════════════════════════════════════════════════
# 2. Parashari aspect — universal 7th-house aspect
# ══════════════════════════════════════════════════════════════════════════════

def test_sun_h2_aspects_h8():
    """Sun in house 2 → 7th from 2 = house 8 (full_aspect)."""
    rows = _parashari_rows([_planet("sun", 2, "taurus")])
    keys = {r[IDX_FACT_KEY] for r in rows}
    assert "aspected_house_8" in keys


def test_sun_h2_aspect_value_text():
    rows = _parashari_rows([_planet("sun", 2, "taurus")])
    matched = [r for r in rows if r[IDX_FACT_KEY] == "aspected_house_8"]
    assert matched, "expected row for aspected_house_8"
    assert matched[0][IDX_VALUE_TEXT] == "full_aspect"


def test_sun_h2_aspects_only_h8():
    """Sun has no special aspects — should only aspect house 8 from house 2."""
    rows = _parashari_rows([_planet("sun", 2, "taurus")])
    assert len(rows) == 1


# ══════════════════════════════════════════════════════════════════════════════
# 3. Mars special aspects (4th + 8th)
# ══════════════════════════════════════════════════════════════════════════════

def test_mars_h1_aspects_h7():
    """Mars in house 1 → universal 7th = house 7."""
    rows = _parashari_rows([_planet("mars", 1, "aries")])
    keys = {r[IDX_FACT_KEY] for r in rows}
    assert "aspected_house_7" in keys


def test_mars_h1_aspects_h4():
    """Mars in house 1 → special 4th = house 4."""
    rows = _parashari_rows([_planet("mars", 1, "aries")])
    keys = {r[IDX_FACT_KEY] for r in rows}
    assert "aspected_house_4" in keys


def test_mars_h1_aspects_h8():
    """Mars in house 1 → special 8th = house 8."""
    rows = _parashari_rows([_planet("mars", 1, "aries")])
    keys = {r[IDX_FACT_KEY] for r in rows}
    assert "aspected_house_8" in keys


def test_mars_h1_aspects_three_houses():
    """Mars in house 1 should produce exactly 3 rows (7th + 4th + 8th)."""
    rows = _parashari_rows([_planet("mars", 1, "aries")])
    assert len(rows) == 3


def test_mars_special_labels():
    """Mars special aspects get correct value_text labels."""
    rows = _parashari_rows([_planet("mars", 1, "aries")])
    texts = {r[IDX_FACT_KEY]: r[IDX_VALUE_TEXT] for r in rows}
    assert texts["aspected_house_4"] == "special_4th"
    assert texts["aspected_house_8"] == "special_8th"


# ══════════════════════════════════════════════════════════════════════════════
# 4. Jupiter special aspects (5th + 9th)
# ══════════════════════════════════════════════════════════════════════════════

def test_jupiter_h3_aspects():
    """Jupiter in house 3: 7th from 3=9, 5th from 3=7, 9th from 3=11."""
    rows = _parashari_rows([_planet("jupiter", 3, "gemini")])
    keys = {r[IDX_FACT_KEY] for r in rows}
    assert "aspected_house_9" in keys   # universal 7th
    assert "aspected_house_7" in keys   # 5th special (offset=5: (3-1+5-1)%12+1 = 7)
    assert "aspected_house_11" in keys  # 9th special (offset=9: (3-1+9-1)%12+1 = 11)


def test_jupiter_h3_three_rows():
    rows = _parashari_rows([_planet("jupiter", 3, "gemini")])
    assert len(rows) == 3


# ══════════════════════════════════════════════════════════════════════════════
# 5. Saturn special aspects (3rd + 10th)
# ══════════════════════════════════════════════════════════════════════════════

def test_saturn_h5_aspects():
    """Saturn in house 5: 7th from 5=11, 3rd from 5=7, 10th from 5=2."""
    rows = _parashari_rows([_planet("saturn", 5, "leo")])
    keys = {r[IDX_FACT_KEY] for r in rows}
    assert "aspected_house_11" in keys   # universal 7th
    assert "aspected_house_7" in keys    # 3rd special
    assert "aspected_house_2" in keys    # 10th special


def test_saturn_h5_three_rows():
    rows = _parashari_rows([_planet("saturn", 5, "leo")])
    assert len(rows) == 3


# ══════════════════════════════════════════════════════════════════════════════
# 6. Rahu / Ketu aspects (5th + 9th like Jupiter)
# ══════════════════════════════════════════════════════════════════════════════

def test_rahu_aspects_5th_and_9th():
    """Rahu in house 2: 7th=8, 5th=6, 9th=10."""
    rows = _parashari_rows([_planet("rahu", 2, "taurus")])
    keys = {r[IDX_FACT_KEY] for r in rows}
    assert "aspected_house_8" in keys   # 7th universal
    assert "aspected_house_6" in keys   # 5th special: (2-1+5-1)%12+1 = 6
    assert "aspected_house_10" in keys  # 9th special: (2-1+9-1)%12+1 = 10


def test_ketu_aspects_5th_and_9th():
    """Ketu in house 8: 7th=2, 5th=12, 9th=4."""
    rows = _parashari_rows([_planet("ketu", 8, "scorpio")])
    keys = {r[IDX_FACT_KEY] for r in rows}
    assert "aspected_house_2" in keys   # 7th universal
    assert "aspected_house_12" in keys  # 5th special
    assert "aspected_house_4" in keys   # 9th special


# ══════════════════════════════════════════════════════════════════════════════
# 7. Parashari row quality
# ══════════════════════════════════════════════════════════════════════════════

def test_parashari_citation_human():
    rows = _parashari_rows([_planet("sun", 1, "aries")])
    for r in rows:
        assert r[IDX_CITATION_HUM] == "BPHS Ch 26"


def test_parashari_value_number_is_one():
    rows = _parashari_rows([_planet("mars", 1, "aries")])
    for r in rows:
        assert r[IDX_VALUE_NUMBER] == 1.0


def test_parashari_fact_category():
    rows = _parashari_rows([_planet("sun", 1, "aries")])
    for r in rows:
        assert r[IDX_FACT_CATEGORY] == "aspect_matrix_parashari"


# ══════════════════════════════════════════════════════════════════════════════
# 8. Jaimini Rasi-drishti
# ══════════════════════════════════════════════════════════════════════════════

def test_jaimini_aries_aspects_leo():
    """Aries (moveable) should aspect Leo (fixed, non-adjacent)."""
    rows = _jaimini_rows()
    pair = [r for r in rows if r[IDX_FACT_SUBJECT] == "aries" and "leo" in r[IDX_FACT_KEY]]
    assert pair, "Aries→Leo rasi-drishti row missing"


def test_jaimini_aries_does_not_aspect_taurus():
    """Aries (moveable) must NOT aspect Taurus (adjacent fixed sign)."""
    rows = _jaimini_rows()
    pair = [r for r in rows if r[IDX_FACT_SUBJECT] == "aries" and "taurus" in r[IDX_FACT_KEY]]
    assert not pair, "Aries→Taurus should be excluded (adjacent)"


def test_jaimini_aries_does_not_aspect_pisces():
    """Aries (moveable) must NOT aspect Pisces (adjacent dual sign — different type anyway)."""
    rows = _jaimini_rows()
    pair = [r for r in rows if r[IDX_FACT_SUBJECT] == "aries" and "pisces" in r[IDX_FACT_KEY]]
    assert not pair, "Aries→Pisces should not appear (Pisces is dual, not fixed)"


def test_jaimini_gemini_aspects_virgo():
    """Gemini (dual) aspects Virgo (dual, non-adjacent)."""
    rows = _jaimini_rows()
    pair = [r for r in rows if r[IDX_FACT_SUBJECT] == "gemini" and "virgo" in r[IDX_FACT_KEY]]
    assert pair, "Gemini→Virgo rasi-drishti row missing"


def test_jaimini_total_row_count():
    """36 static pairs expected (4 moveable×3 targets + 4 fixed×3 targets + 4 dual×3 targets = 36)."""
    rows = _jaimini_rows()
    assert len(rows) == 36


def test_jaimini_value_text():
    rows = _jaimini_rows()
    for r in rows:
        assert r[IDX_VALUE_TEXT] == "rasi_drishti"


def test_jaimini_citation_human():
    rows = _jaimini_rows()
    for r in rows:
        assert r[IDX_CITATION_HUM] == "Jaimini Sutras 1.1.28"


def test_jaimini_fact_category():
    rows = _jaimini_rows()
    for r in rows:
        assert r[IDX_FACT_CATEGORY] == "aspect_matrix_jaimini"


def test_jaimini_value_number_is_one():
    rows = _jaimini_rows()
    for r in rows:
        assert r[IDX_VALUE_NUMBER] == 1.0


# ══════════════════════════════════════════════════════════════════════════════
# 9. Dispositor chains
# ══════════════════════════════════════════════════════════════════════════════

def test_dispositor_planet_in_aries_starts_with_mars():
    """Sun in Aries → dispositor is Mars; chain text starts with sun→mars."""
    rows = _dispositor_rows([_planet("sun", 1, "aries")])
    chain_rows = [r for r in rows if r[IDX_FACT_KEY] == "dispositor_chain"]
    assert chain_rows, "dispositor_chain row missing"
    chain_text = chain_rows[0][IDX_VALUE_TEXT]
    assert chain_text.startswith("sun→mars")


def test_dispositor_chain_contains_arrow():
    rows = _dispositor_rows([_planet("sun", 1, "aries")])
    chain_rows = [r for r in rows if r[IDX_FACT_KEY] == "dispositor_chain"]
    assert chain_rows
    assert "→" in chain_rows[0][IDX_VALUE_TEXT]


def test_dispositor_sun_in_leo_self_disposited():
    """Sun in Leo — Sun is its own lord; final_dispositor = sun."""
    rows = _dispositor_rows([_planet("sun", 5, "leo")])
    final_rows = [r for r in rows if r[IDX_FACT_KEY] == "final_dispositor"]
    assert final_rows, "final_dispositor row missing"
    assert final_rows[0][IDX_VALUE_TEXT] == "sun"


def test_dispositor_fact_category():
    rows = _dispositor_rows([_planet("sun", 1, "aries")])
    for r in rows:
        assert r[IDX_FACT_CATEGORY] == "dispositor_chain"


def test_dispositor_two_rows_per_graha():
    """Each graha with a chart position produces exactly 2 rows: chain + final_dispositor."""
    rows = _dispositor_rows([_planet("mars", 3, "gemini")])
    assert len(rows) == 2
    keys = {r[IDX_FACT_KEY] for r in rows}
    assert keys == {"dispositor_chain", "final_dispositor"}


# ══════════════════════════════════════════════════════════════════════════════
# 10. No forbidden narration verbs in value_text
# ══════════════════════════════════════════════════════════════════════════════

_FORBIDDEN_VERBS = {"indicates", "signifies", "shows", "suggests", "reveals",
                    "means", "represents", "denotes"}


def test_no_narration_verbs_in_value_text():
    """value_text must be data codes, not narrative sentences."""
    planets = [
        _planet("sun", 1, "aries"),
        _planet("mars", 4, "cancer"),
        _planet("jupiter", 7, "libra"),
    ]
    result, rows = _run_write(planets)
    for r in rows:
        vt = (r[IDX_VALUE_TEXT] or "").lower()
        for verb in _FORBIDDEN_VERBS:
            assert verb not in vt, f"Forbidden verb '{verb}' found in value_text: {r[IDX_VALUE_TEXT]}"


# ══════════════════════════════════════════════════════════════════════════════
# 11. Adjacency helper
# ══════════════════════════════════════════════════════════════════════════════

def test_are_adjacent_aries_taurus():
    assert _are_adjacent("aries", "taurus") is True


def test_are_adjacent_pisces_aries_circular():
    """Pisces (index 11) and Aries (index 0) are circularly adjacent."""
    assert _are_adjacent("pisces", "aries") is True


def test_not_adjacent_aries_leo():
    assert _are_adjacent("aries", "leo") is False


# ══════════════════════════════════════════════════════════════════════════════
# 12. Full write() integration — row count sanity with a single planet
# ══════════════════════════════════════════════════════════════════════════════

def test_write_single_sun_produces_correct_total():
    """
    With Sun in H1:
      - Parashari: 1 row (7th only)
      - Jaimini: 36 rows (static, chart-scoped)
      - Dispositor: 2 rows (chain + final)
    Total = 39
    """
    result, rows = _run_write([_planet("sun", 1, "leo")])
    assert result == 39
    assert len(rows) == 39


def test_write_fact_ids_unique():
    """Every row must have a unique fact_id."""
    planets = [
        _planet("sun", 1, "aries"),
        _planet("moon", 2, "taurus"),
        _planet("mars", 3, "gemini"),
    ]
    result, rows = _run_write(planets)
    fact_ids = [r[0] for r in rows]
    assert len(fact_ids) == len(set(fact_ids)), "Duplicate fact_ids found"
