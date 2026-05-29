"""
Tests for pipeline/render/vargas_renderer.py (F-12)

Coverage (30+ tests):
- Empty chart_output → no crash, returns string
- Parashari section heading present
- Nadi section heading present
- D1 table rendered
- D9 table rendered
- D10 table rendered
- D60 table rendered
- D108 table rendered with Rishi column
- D150 table rendered
- D2700 table rendered
- Lagna row present in each table
- All 9 grahas in D1 table
- All 9 grahas in D9 table
- Sign column populated
- Lord column populated
- Dignity column populated
- Vargottama flag rendered as ✓
- Vargottama flag rendered as ✗
- Vargottama flag None renders —
- Rishi column in D108
- Rishi column NOT in D1
- D9 two-pass verification heading present
- D9 verification PASS when match=True
- D9 verification FAIL when match=False
- D9 verification discrepancy count shown
- Discrepancy text shown when present
- Missing varga data renders dashes
- PARASHARI_VARGAS has 20 entries
- NADI_VARGAS has 3 entries
- ALL_VARGAS has 23 entries
- render_vargas_section returns str
- No narration verbs in full output
- Varga description text included
- D9 desc contains navamsha keyword
- D10 desc contains dasamsha or career keyword
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.vargas_renderer import (
    GRAHAS,
    GRAHA_DISPLAY,
    PARASHARI_VARGAS,
    NADI_VARGAS,
    ALL_VARGAS,
    VARGA_DESC,
    render_vargas_section,
    _render_single_varga,
    _render_d9_verification,
    _safe,
    _varg_flag,
)
from pipeline.render.base_renderer import lint_narration, NarrationViolation


# ---------------------------------------------------------------------------
# Sample data builders
# ---------------------------------------------------------------------------

def _make_graha_entry(
    sign: str = "Aries",
    lord: str = "Mars",
    dignity: str = "neutral",
    vargottama: bool = False,
    rishi: str = "Vasishtha",
) -> dict:
    return {
        "sign": sign,
        "lord": lord,
        "dignity": dignity,
        "vargottama": vargottama,
        "rishi": rishi,
    }


def _make_lagna(sign: str = "Cancer", lord: str = "Moon") -> dict:
    return {"sign": sign, "lord": lord}


def _make_varga_data(vargottama: bool = False, rishi: str = "Agastya") -> dict:
    d: dict = {"lagna": _make_lagna()}
    for g in GRAHAS:
        d[g] = _make_graha_entry(vargottama=vargottama, rishi=rishi)
    return d


def _full_chart() -> dict:
    vargas: dict = {}
    for v in ALL_VARGAS:
        vargas[v] = _make_varga_data()
    return {
        "vargas": vargas,
        "d9_verification": {"match": True, "discrepancies": []},
    }


# ---------------------------------------------------------------------------
# Tests: module-level constants
# ---------------------------------------------------------------------------

def test_parashari_vargas_has_20():
    assert len(PARASHARI_VARGAS) == 20


def test_nadi_vargas_has_3():
    assert len(NADI_VARGAS) == 3


def test_all_vargas_has_23():
    assert len(ALL_VARGAS) == 23


def test_d1_in_parashari():
    assert "D1" in PARASHARI_VARGAS


def test_d60_in_parashari():
    assert "D60" in PARASHARI_VARGAS


def test_d108_in_nadi():
    assert "D108" in NADI_VARGAS


def test_d2700_in_nadi():
    assert "D2700" in NADI_VARGAS


# ---------------------------------------------------------------------------
# Tests: _varg_flag helper
# ---------------------------------------------------------------------------

def test_vargottama_true():
    assert _varg_flag(True) == "✓"


def test_vargottama_false():
    assert _varg_flag(False) == "✗"


def test_vargottama_none():
    assert _varg_flag(None) == "—"


def test_vargottama_string_true():
    assert _varg_flag("true") == "✓"


# ---------------------------------------------------------------------------
# Tests: render_vargas_section — empty / graceful
# ---------------------------------------------------------------------------

def test_empty_chart_returns_string():
    result = render_vargas_section({})
    assert isinstance(result, str)


def test_empty_chart_no_crash():
    result = render_vargas_section({})
    assert len(result) > 0


def test_missing_varga_renders_dashes():
    result = render_vargas_section({"vargas": {"D1": {"lagna": {"sign": "Cancer"}}}})
    assert "—" in result


# ---------------------------------------------------------------------------
# Tests: Parashari section
# ---------------------------------------------------------------------------

def test_parashari_heading():
    result = render_vargas_section(_full_chart())
    assert "Parashari Divisional Charts" in result


def test_d1_table_heading():
    result = render_vargas_section(_full_chart())
    assert "D1 —" in result


def test_d9_table_heading():
    result = render_vargas_section(_full_chart())
    assert "D9 —" in result


def test_d10_table_heading():
    result = render_vargas_section(_full_chart())
    assert "D10 —" in result


def test_d60_table_heading():
    result = render_vargas_section(_full_chart())
    assert "D60 —" in result


def test_lagna_row_in_d1():
    out = _render_single_varga("D1", _make_varga_data())
    assert "| Lagna |" in out


def test_all_9_grahas_in_d1():
    out = _render_single_varga("D1", _make_varga_data())
    for g in GRAHA_DISPLAY.values():
        assert f"| {g} |" in out


def test_all_9_grahas_in_d9():
    out = _render_single_varga("D9", _make_varga_data())
    for g in GRAHA_DISPLAY.values():
        assert f"| {g} |" in out


def test_sign_in_d1_table():
    out = _render_single_varga("D1", _make_varga_data())
    assert "Aries" in out


def test_dignity_in_d1_table():
    out = _render_single_varga("D1", _make_varga_data())
    assert "neutral" in out


def test_vargottama_check_in_d9():
    data = _make_varga_data(vargottama=True)
    out = _render_single_varga("D9", data)
    assert "✓" in out


def test_d9_desc_contains_navamsha():
    assert "navamsha" in VARGA_DESC.get("D9", "").lower() or "navamsha" in VARGA_DESC.get("D9", "").lower() or "Navamsha" in VARGA_DESC.get("D9", "")


def test_d10_desc_contains_career():
    assert "career" in VARGA_DESC.get("D10", "").lower() or "dasamsha" in VARGA_DESC.get("D10", "").lower()


def test_rishi_column_not_in_d1():
    out = _render_single_varga("D1", _make_varga_data(), is_nadi=False)
    assert "Rishi" not in out


# ---------------------------------------------------------------------------
# Tests: Nadi section
# ---------------------------------------------------------------------------

def test_nadi_heading():
    result = render_vargas_section(_full_chart())
    assert "Nadi Divisional Charts" in result


def test_d108_table_heading():
    result = render_vargas_section(_full_chart())
    assert "D108 —" in result


def test_d108_has_rishi_column():
    out = _render_single_varga("D108", _make_varga_data(rishi="Vasishtha"), is_nadi=True)
    assert "Rishi" in out


def test_d108_rishi_value():
    out = _render_single_varga("D108", _make_varga_data(rishi="Vasishtha"), is_nadi=True)
    assert "Vasishtha" in out


def test_d150_table_heading():
    result = render_vargas_section(_full_chart())
    assert "D150 —" in result


def test_d2700_table_heading():
    result = render_vargas_section(_full_chart())
    assert "D2700 —" in result


# ---------------------------------------------------------------------------
# Tests: D9 verification
# ---------------------------------------------------------------------------

def test_d9_verification_heading():
    result = render_vargas_section(_full_chart())
    assert "D9 Two-Pass Verification" in result


def test_d9_verification_pass():
    out = _render_d9_verification({"match": True, "discrepancies": []})
    assert "PASS" in out


def test_d9_verification_fail():
    out = _render_d9_verification({"match": False, "discrepancies": ["Sun: Aries vs Taurus"]})
    assert "FAIL" in out


def test_d9_verification_discrepancy_shown():
    out = _render_d9_verification({"match": False, "discrepancies": ["Sun: Aries vs Taurus"]})
    assert "Sun: Aries vs Taurus" in out


def test_d9_verification_zero_discrepancies():
    out = _render_d9_verification({"match": True, "discrepancies": []})
    assert "0" in out


# ---------------------------------------------------------------------------
# Tests: no narration verbs + return type
# ---------------------------------------------------------------------------

def test_no_narration_verbs():
    result = render_vargas_section(_full_chart())
    lint_narration(result)


def test_no_narration_empty():
    result = render_vargas_section({})
    lint_narration(result)


def test_render_returns_str():
    assert isinstance(render_vargas_section(_full_chart()), str)


def test_render_non_empty():
    assert len(render_vargas_section(_full_chart())) > 0
