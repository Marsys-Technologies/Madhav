"""Internal-consistency tests for graha positions."""
from __future__ import annotations

from pyjhora_adapter import positions

_EXPECTED_NAMES = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
]


def _ang_sep(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def test_nine_grahas_in_canonical_order(native_jd):
    grahas = positions.compute_positions(
        native_jd, "lahiri", lat=20.2961, lon=85.8245, tz=5.5
    )
    assert [g["name"] for g in grahas] == _EXPECTED_NAMES


def test_rahu_ketu_180_apart(native_jd):
    grahas = positions.compute_positions(
        native_jd, "lahiri", lat=20.2961, lon=85.8245, tz=5.5
    )
    rahu = next(g for g in grahas if g["name"] == "Rahu")
    ketu = next(g for g in grahas if g["name"] == "Ketu")
    sep = _ang_sep(rahu["longitude_deg"], ketu["longitude_deg"])
    assert abs(sep - 180.0) < 0.5, f"Rahu/Ketu separation {sep} not ~180"


def test_all_longitudes_in_range(native_jd):
    grahas = positions.compute_positions(
        native_jd, "lahiri", lat=20.2961, lon=85.8245, tz=5.5
    )
    for g in grahas:
        assert 0.0 <= g["longitude_deg"] < 360.0
        assert 1 <= g["sign_id"] <= 12
        assert 1 <= g["nakshatra_pada"] <= 4
        assert 1 <= g["nakshatra_id"] <= 27


def test_native_sun_in_capricorn(native_jd):
    """FORENSIC-grounded internal-consistency anchor: native Sun is in
    Capricorn (Shravana) under Lahiri. This is the chart's own structural
    fingerprint, not an external oracle."""
    grahas = positions.compute_positions(
        native_jd, "lahiri", lat=20.2961, lon=85.8245, tz=5.5
    )
    sun = next(g for g in grahas if g["name"] == "Sun")
    assert sun["sign"] == "Capricorn"
    moon = next(g for g in grahas if g["name"] == "Moon")
    assert moon["nakshatra"] == "Purva Bhadrapada"
