"""
test_cross_ayanamsha_report.py — E-07 tests for generate_cross_ayanamsha_report().

Verifies:
  - Empty/single-entry input returns a safe null report.
  - Two identical chart outputs produce divergence_score = 0 and overall = 'low'.
  - Two chart outputs with deliberately shifted longitudes produce non-zero deltas.
  - Report structure keys are all present.
  - pair_count matches C(N, 2) for N ayanamshas.
  - most_stable_graha and most_variable_graha are valid graha names.
  - Sign change detection works correctly.
  - Navamsa change detection works correctly.
  - Integration: real Lahiri vs jh_true_chitra charts produce a well-formed report.
"""

from __future__ import annotations

import copy
import pytest

NATIVE_INPUTS = {
    "datetime_iso": "1984-02-05T10:43:00",
    "tz_offset_hours": 5.5,
    "latitude_deg": 20.27,
    "longitude_deg": 85.84,
    "place_name": "Bhubaneswar",
    "subject_label": "Abhisek Mohanty",
}

GRAHA_NAMES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

REPORT_TOP_KEYS = {
    "ayanamsha_pairs", "overall_divergence", "most_divergent_pair",
    "pair_count", "graha_variance", "most_stable_graha", "most_variable_graha",
}


# ---------------------------------------------------------------------------
# Helper: build a minimal synthetic chart_output dict
# ---------------------------------------------------------------------------

def _make_chart(longitudes: dict[str, float]) -> dict:
    """Build a minimal chart_output with grahas as a list, using supplied longitudes."""
    from natal_engine.positions import SIGN_NAMES, compute_varga_for_lon
    grahas = []
    for name in GRAHA_NAMES:
        lon = longitudes.get(name, 0.0)
        sign_idx = int(lon // 30) % 12
        vp = compute_varga_for_lon(lon)
        grahas.append({
            "name": name,
            "longitude_deg": lon,
            "sign": SIGN_NAMES[sign_idx],
            "sign_index": sign_idx + 1,
            "varga_position": vp,
        })
    return {"grahas": grahas}


# Default base longitudes (arbitrary but spread across the zodiac)
_BASE_LONS = {
    "Sun":     295.0,   # Capricorn
    "Moon":     75.0,   # Gemini
    "Mars":    200.0,   # Libra
    "Mercury": 280.0,   # Capricorn
    "Jupiter": 150.0,   # Leo
    "Venus":   310.0,   # Aquarius
    "Saturn":  250.0,   # Sagittarius
    "Rahu":    180.0,   # Libra
    "Ketu":      0.0,   # Aries
}


# ---------------------------------------------------------------------------
# Structure / schema tests
# ---------------------------------------------------------------------------

def test_generate_cross_ayanamsha_report_importable():
    from natal_engine.positions import generate_cross_ayanamsha_report
    assert callable(generate_cross_ayanamsha_report)


def test_empty_input_returns_null_report():
    from natal_engine.positions import generate_cross_ayanamsha_report
    result = generate_cross_ayanamsha_report({})
    assert result["pair_count"] == 0
    assert result["ayanamsha_pairs"] == []
    assert result["overall_divergence"] == "low"
    assert result["most_divergent_pair"] is None


def test_single_entry_returns_null_report():
    from natal_engine.positions import generate_cross_ayanamsha_report
    chart = _make_chart(_BASE_LONS)
    result = generate_cross_ayanamsha_report({"lahiri": chart})
    assert result["pair_count"] == 0
    assert result["most_divergent_pair"] is None


def test_report_top_keys_present():
    from natal_engine.positions import generate_cross_ayanamsha_report
    c1 = _make_chart(_BASE_LONS)
    c2 = _make_chart(_BASE_LONS)
    result = generate_cross_ayanamsha_report({"lahiri": c1, "raman": c2})
    assert REPORT_TOP_KEYS.issubset(set(result.keys())), (
        f"Missing keys: {REPORT_TOP_KEYS - set(result.keys())}"
    )


def test_pair_count_two_ayanamshas():
    from natal_engine.positions import generate_cross_ayanamsha_report
    c1 = _make_chart(_BASE_LONS)
    c2 = _make_chart(_BASE_LONS)
    result = generate_cross_ayanamsha_report({"lahiri": c1, "raman": c2})
    assert result["pair_count"] == 1


def test_pair_count_three_ayanamshas():
    """C(3,2) = 3 pairs."""
    from natal_engine.positions import generate_cross_ayanamsha_report
    chart = _make_chart(_BASE_LONS)
    result = generate_cross_ayanamsha_report({"a": chart, "b": chart, "c": chart})
    assert result["pair_count"] == 3


def test_pair_entry_keys():
    from natal_engine.positions import generate_cross_ayanamsha_report
    c = _make_chart(_BASE_LONS)
    result = generate_cross_ayanamsha_report({"x": c, "y": c})
    pair = result["ayanamsha_pairs"][0]
    required = {
        "ayanamsha_1", "ayanamsha_2", "max_position_delta_deg",
        "divergent_grahas", "convergent_grahas",
        "sign_change_count", "navamsa_change_count", "divergence_score",
    }
    assert required.issubset(set(pair.keys()))


# ---------------------------------------------------------------------------
# Zero-divergence tests (identical charts)
# ---------------------------------------------------------------------------

def test_identical_charts_zero_delta():
    from natal_engine.positions import generate_cross_ayanamsha_report
    c = _make_chart(_BASE_LONS)
    result = generate_cross_ayanamsha_report({"a": c, "b": c})
    pair = result["ayanamsha_pairs"][0]
    assert pair["max_position_delta_deg"] == 0.0
    assert pair["divergence_score"] == 0.0
    assert pair["sign_change_count"] == 0
    assert pair["navamsa_change_count"] == 0
    assert result["overall_divergence"] == "low"


def test_identical_charts_no_divergent_grahas():
    from natal_engine.positions import generate_cross_ayanamsha_report
    c = _make_chart(_BASE_LONS)
    result = generate_cross_ayanamsha_report({"a": c, "b": c})
    assert result["ayanamsha_pairs"][0]["divergent_grahas"] == []
    assert len(result["ayanamsha_pairs"][0]["convergent_grahas"]) == 9


# ---------------------------------------------------------------------------
# Non-zero divergence tests (shifted longitudes)
# ---------------------------------------------------------------------------

def test_shifted_charts_produce_nonzero_delta():
    from natal_engine.positions import generate_cross_ayanamsha_report
    c1 = _make_chart(_BASE_LONS)
    # Shift all longitudes by ~0.9° (typical Lahiri–TrueChitra delta)
    shifted = {name: (lon + 0.9) % 360 for name, lon in _BASE_LONS.items()}
    c2 = _make_chart(shifted)
    result = generate_cross_ayanamsha_report({"lahiri": c1, "true_chitra": c2})
    pair = result["ayanamsha_pairs"][0]
    assert pair["max_position_delta_deg"] > 0.0
    assert pair["divergence_score"] > 0.0


def test_large_shift_detects_sign_change():
    """Shift Sun from end of Capricorn (295°) to early Aquarius by 5° → sign change."""
    from natal_engine.positions import generate_cross_ayanamsha_report
    lons_1 = dict(_BASE_LONS)
    lons_1["Sun"] = 299.0   # Capricorn (just before 300°=Aquarius boundary)
    lons_2 = dict(_BASE_LONS)
    lons_2["Sun"] = 301.0   # Aquarius
    # all others identical
    for name in GRAHA_NAMES:
        if name != "Sun":
            lons_2[name] = _BASE_LONS[name]
    c1 = _make_chart(lons_1)
    c2 = _make_chart(lons_2)
    result = generate_cross_ayanamsha_report({"a": c1, "b": c2})
    pair = result["ayanamsha_pairs"][0]
    assert pair["sign_change_count"] >= 1


def test_divergent_graha_threshold():
    """Graha with delta > 1° is in divergent list; ≤1° is in convergent list."""
    from natal_engine.positions import generate_cross_ayanamsha_report
    lons_2 = dict(_BASE_LONS)
    lons_2["Moon"] = (_BASE_LONS["Moon"] + 2.5) % 360   # delta > 1° → divergent
    # Sun delta = 0 → convergent
    c1 = _make_chart(_BASE_LONS)
    c2 = _make_chart(lons_2)
    result = generate_cross_ayanamsha_report({"a": c1, "b": c2})
    pair = result["ayanamsha_pairs"][0]
    assert "Moon" in pair["divergent_grahas"]
    assert "Sun" in pair["convergent_grahas"]


def test_graha_variance_populated():
    from natal_engine.positions import generate_cross_ayanamsha_report
    c1 = _make_chart(_BASE_LONS)
    shifted = {name: (lon + 0.7) % 360 for name, lon in _BASE_LONS.items()}
    c2 = _make_chart(shifted)
    result = generate_cross_ayanamsha_report({"a": c1, "b": c2})
    gv = result["graha_variance"]
    assert len(gv) == len(GRAHA_NAMES)
    for name in GRAHA_NAMES:
        assert name in gv


def test_most_stable_and_variable_are_valid_graha_names():
    from natal_engine.positions import generate_cross_ayanamsha_report
    c1 = _make_chart(_BASE_LONS)
    shifted = {name: (lon + 0.7) % 360 for name, lon in _BASE_LONS.items()}
    c2 = _make_chart(shifted)
    result = generate_cross_ayanamsha_report({"a": c1, "b": c2})
    assert result["most_stable_graha"] in GRAHA_NAMES
    assert result["most_variable_graha"] in GRAHA_NAMES


# ---------------------------------------------------------------------------
# Integration test: real Lahiri vs jh_true_chitra
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real_report():
    from natal_engine import compute_chart, generate_cross_ayanamsha_report
    chart_lahiri = compute_chart(NATIVE_INPUTS, ayanamsha_id="lahiri", validate=False)
    chart_jh = compute_chart(NATIVE_INPUTS, ayanamsha_id="jh_true_chitra", validate=False)
    return generate_cross_ayanamsha_report({"lahiri": chart_lahiri, "jh_true_chitra": chart_jh})


def test_real_report_structure(real_report):
    assert REPORT_TOP_KEYS.issubset(set(real_report.keys()))
    assert real_report["pair_count"] == 1


def test_real_report_overall_divergence_string(real_report):
    assert real_report["overall_divergence"] in ("low", "medium", "high")


def test_real_report_most_divergent_pair_is_tuple(real_report):
    mdp = real_report["most_divergent_pair"]
    assert mdp is not None
    assert len(mdp) == 2
    assert mdp[0] in ("lahiri", "jh_true_chitra")
    assert mdp[1] in ("lahiri", "jh_true_chitra")


def test_real_report_grahas_covered(real_report):
    gv = real_report["graha_variance"]
    for name in GRAHA_NAMES:
        assert name in gv, f"graha_variance missing {name}"
