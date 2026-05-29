"""
test_vargas_all_bodies.py — E-06 tests for D1/D9/D10 varga_position on all 23 bodies.

Verifies:
  - compute_varga_for_lon() returns well-formed D1/D9/D10 dicts for any longitude.
  - All 9 graha dicts in compute_chart() output have varga_position.
  - node_variants (rahu_true/ketu_true/rahu_mean/ketu_mean) all have varga_position.
  - lilith_variants (lilith_mean/lilith_true) have varga_position.
  - outer_bodies (8 main bodies) have varga_position.
  - Specific known values for spot-check longitudes.
  - Sentinel zero-longitude produces valid (not None) varga_position.
  - D9 navamsa sign index is in range 1..12.
  - D10 dasamsa sign index is in range 1..12.
"""

from __future__ import annotations

import pytest

NATIVE_INPUTS = {
    "datetime_iso": "1984-02-05T10:43:00",
    "tz_offset_hours": 5.5,
    "latitude_deg": 20.27,
    "longitude_deg": 85.84,
    "place_name": "Bhubaneswar",
    "subject_label": "Abhisek Mohanty",
}

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


# ---------------------------------------------------------------------------
# Unit tests for compute_varga_for_lon() standalone
# ---------------------------------------------------------------------------

def test_varga_for_lon_imports():
    from natal_engine.positions import compute_varga_for_lon
    assert callable(compute_varga_for_lon)


def test_varga_for_lon_structure_keys():
    from natal_engine.positions import compute_varga_for_lon
    result = compute_varga_for_lon(45.0)  # Taurus 15°
    assert set(result.keys()) == {"D1", "D9", "D10"}
    for division in ("D1", "D9", "D10"):
        assert "sign" in result[division]
        assert "sign_index" in result[division]


def test_varga_for_lon_d1_sign():
    """D1 sign must match the simple 30°-arc rule."""
    from natal_engine.positions import compute_varga_for_lon
    # 0–30 = Aries
    r = compute_varga_for_lon(0.0)
    assert r["D1"]["sign"] == "Aries"
    assert r["D1"]["sign_index"] == 1
    # 30–60 = Taurus
    r = compute_varga_for_lon(30.0)
    assert r["D1"]["sign"] == "Taurus"
    assert r["D1"]["sign_index"] == 2
    # 300–330 = Aquarius (sign 11)
    r = compute_varga_for_lon(310.0)
    assert r["D1"]["sign"] == "Aquarius"
    assert r["D1"]["sign_index"] == 11


def test_varga_for_lon_d1_degree():
    """D1 degree within sign should be longitude % 30."""
    from natal_engine.positions import compute_varga_for_lon
    r = compute_varga_for_lon(45.5)
    assert abs(r["D1"]["degree"] - 15.5) < 1e-5


def test_varga_for_lon_sign_index_range():
    """sign_index must be in 1..12 for D1, D9, D10 across representative longitudes."""
    from natal_engine.positions import compute_varga_for_lon
    test_lons = [0.0, 15.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 240.0, 270.0, 300.0, 330.0, 359.9]
    for lon in test_lons:
        r = compute_varga_for_lon(lon)
        for div in ("D1", "D9", "D10"):
            idx = r[div]["sign_index"]
            assert 1 <= idx <= 12, f"lon={lon} {div} sign_index={idx} out of range"
            # sign name must be consistent with index
            assert r[div]["sign"] == SIGN_NAMES[idx - 1], f"lon={lon} {div} sign mismatch"


def test_varga_for_lon_zero_sentinel():
    """Longitude 0.0 must produce a valid (non-None) varga_position."""
    from natal_engine.positions import compute_varga_for_lon
    r = compute_varga_for_lon(0.0)
    assert r is not None
    for div in ("D1", "D9", "D10"):
        assert r[div]["sign"] in SIGN_NAMES


def test_varga_for_lon_360_wraps():
    """Longitude 360.0 should behave identically to 0.0 (wraps to Aries)."""
    from natal_engine.positions import compute_varga_for_lon
    r0 = compute_varga_for_lon(0.0)
    r360 = compute_varga_for_lon(360.0)
    assert r0["D1"]["sign"] == r360["D1"]["sign"]
    assert r0["D9"]["sign"] == r360["D9"]["sign"]


def test_varga_for_lon_d9_movable_aries():
    """Aries (movable, sign 1) navamsa at 0° → Aries (nav_idx=0, start=Aries)."""
    from natal_engine.positions import compute_varga_for_lon
    r = compute_varga_for_lon(0.0)          # 0° Aries
    assert r["D9"]["sign"] == "Aries"


def test_varga_for_lon_d9_fixed_taurus_start():
    """Taurus (fixed, sign 2): navamsa cycle starts from 9th sign = Capricorn."""
    from natal_engine.positions import compute_varga_for_lon
    # First navamsa of Taurus (30°–33°20') → should be Capricorn
    r = compute_varga_for_lon(30.5)         # 0.5° into Taurus
    assert r["D9"]["sign"] == "Capricorn"


def test_varga_for_lon_d10_odd_sign_aries():
    """Aries (odd): dasamsa cycle starts from Aries. First 3° → D10 Aries."""
    from natal_engine.positions import compute_varga_for_lon
    r = compute_varga_for_lon(1.0)          # 1° Aries → D10 Aries
    assert r["D10"]["sign"] == "Aries"


def test_varga_for_lon_d10_even_sign_taurus():
    """Taurus (even): dasamsa starts from 9th sign = Capricorn. First 3° → D10 Capricorn."""
    from natal_engine.positions import compute_varga_for_lon
    r = compute_varga_for_lon(31.0)         # 1° into Taurus → D10 Capricorn
    assert r["D10"]["sign"] == "Capricorn"


# ---------------------------------------------------------------------------
# Integration tests: varga_position in full compute_chart() output
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def chart():
    from natal_engine import compute_chart
    return compute_chart(NATIVE_INPUTS, validate=False)


def test_chart_grahas_have_varga_position(chart):
    """All 9 graha dicts in chart['grahas'] must have varga_position."""
    grahas = chart["grahas"]
    assert len(grahas) == 9
    for g in grahas:
        assert "varga_position" in g, f"varga_position missing from graha {g.get('name')}"
        vp = g["varga_position"]
        for div in ("D1", "D9", "D10"):
            assert div in vp, f"Division {div} missing from {g.get('name')} varga_position"


def test_chart_node_variants_have_varga_position(chart):
    """node_variants keys (rahu_true/ketu_true/rahu_mean/ketu_mean) must all have varga_position."""
    node_variants = chart.get("node_variants", {})
    for key in ("rahu_true", "ketu_true", "rahu_mean", "ketu_mean"):
        entry = node_variants.get(key)
        assert entry is not None, f"node_variants['{key}'] missing"
        assert "varga_position" in entry, f"varga_position missing from {key}"
        vp = entry["varga_position"]
        for div in ("D1", "D9", "D10"):
            assert div in vp


def test_chart_lilith_variants_have_varga_position(chart):
    """lilith_mean and lilith_true must have varga_position."""
    lilith = chart.get("lilith_variants", {})
    for key in ("lilith_mean", "lilith_true"):
        entry = lilith.get(key)
        assert entry is not None, f"lilith_variants['{key}'] missing"
        assert "varga_position" in entry, f"varga_position missing from {key}"
        vp = entry["varga_position"]
        for div in ("D1", "D9", "D10"):
            assert div in vp


def test_chart_outer_bodies_have_varga_position(chart):
    """The 8 guaranteed outer bodies must have varga_position."""
    outer = chart.get("outer_bodies", {})
    required = ["chiron", "ceres", "pallas", "juno", "vesta", "uranus", "neptune", "pluto"]
    for name in required:
        entry = outer.get(name)
        assert entry is not None, f"outer_bodies['{name}'] missing"
        assert "varga_position" in entry, f"varga_position missing from outer_body {name}"
        vp = entry["varga_position"]
        for div in ("D1", "D9", "D10"):
            assert div in vp


def test_varga_position_sign_index_valid_in_chart(chart):
    """All varga_position sign_index values in the chart must be 1..12."""
    def check_vp(vp: dict, label: str):
        for div in ("D1", "D9", "D10"):
            idx = vp[div]["sign_index"]
            assert 1 <= idx <= 12, f"{label} {div} sign_index={idx} out of range"

    for g in chart["grahas"]:
        check_vp(g["varga_position"], f"graha:{g.get('name')}")
    for key, entry in chart.get("node_variants", {}).items():
        if entry:
            check_vp(entry["varga_position"], f"node:{key}")
    for key, entry in chart.get("lilith_variants", {}).items():
        if entry:
            check_vp(entry["varga_position"], f"lilith:{key}")
    for key, entry in chart.get("outer_bodies", {}).items():
        if entry:
            check_vp(entry["varga_position"], f"outer:{key}")
