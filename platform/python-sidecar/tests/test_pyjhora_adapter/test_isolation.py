"""Internal-consistency tests for the per-ayanamsha isolation helper."""
from __future__ import annotations

from pyjhora_adapter import positions
from pyjhora_adapter._isolation import AYANAMSHAS, per_ayanamsha


def test_per_ayanamsha_returns_five_results(native_jd):
    res = per_ayanamsha(
        positions.compute_positions, native_jd,
        lat=20.2961, lon=85.8245, tz=5.5,
    )
    assert set(res.keys()) == set(AYANAMSHAS)
    assert len(res) == 5


def test_per_ayanamsha_sun_longitudes_differ(native_jd):
    """Each ayanamsha shifts the sidereal zero, so the Sun's sidereal longitude
    must differ across all five (no two identical to 4 dp)."""
    res = per_ayanamsha(
        positions.compute_positions, native_jd,
        lat=20.2961, lon=85.8245, tz=5.5,
    )
    suns = {
        a: next(g for g in grahas if g["name"] == "Sun")["longitude_deg"]
        for a, grahas in res.items()
    }
    distinct = {round(v, 4) for v in suns.values()}
    assert len(distinct) == 5, f"expected 5 distinct Sun longitudes, got {suns}"


def test_per_ayanamsha_each_returns_nine_grahas(native_jd):
    res = per_ayanamsha(
        positions.compute_positions, native_jd,
        lat=20.2961, lon=85.8245, tz=5.5,
    )
    for ayan, grahas in res.items():
        assert len(grahas) == 9, f"{ayan}: expected 9 grahas, got {len(grahas)}"
