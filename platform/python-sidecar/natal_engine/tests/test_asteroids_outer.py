"""
test_asteroids_outer.py — 10 outer planets / asteroids in compute_chart output.

Session E-05 [BUILD-ORCH-E-05].

Native birth: 1984-02-05 10:43 IST = 1984-02-05 05:13 UTC
JD_UT ≈ 2445733.717

Validates:
- compute_chart() output contains 'outer_bodies' key
- All 8 main outer bodies present: chiron, ceres, pallas, juno, vesta,
  uranus, neptune, pluto
- Each body dict has 'longitude' in [0, 360)
- Each body dict has 'sign' field (non-empty string)
- Each body dict has 'nakshatra' field (non-empty string)
- Each body dict has 'retro' field that is a bool
- Each body dict has 'speed' field that is a float
- chiron longitude is finite (not NaN / Inf)
- uranus retro is a bool (not the specific value — direction varies by date)
- neptune retro is a bool
- pluto longitude in [0, 360)
- Sedna dict slot: present and either None or a valid dict
- Eris dict slot: present and either None or a valid dict
- When Sedna/Eris are dicts (not None): their longitude is in [0, 360)
- compute_chart() grahas still has exactly 9 entries (no regression)
- compute_chart() output still has 'node_variants' key (no E-03 regression)
- compute_chart() output still has 'lilith_variants' key (no E-04 regression)
"""

from __future__ import annotations

import math

import pytest
import swisseph as swe

from natal_engine import compute_chart
from natal_engine.positions import compute_outer_bodies, set_ayanamsha

# ---------------------------------------------------------------------------
# Native birth Julian Day (UT)
# 1984-02-05 05:13 UTC → decimal hours = 5 + 13/60
# ---------------------------------------------------------------------------
NATIVE_JD_UT = swe.julday(1984, 2, 5, 5 + 13 / 60)

NATIVE_INPUTS: dict = {
    "datetime_iso": "1984-02-05T10:43:00",
    "tz_offset_hours": 5.5,
    "latitude_deg": 20.27,
    "longitude_deg": 85.84,
    "place_name": "Bhubaneswar, Odisha, India",
    "subject_label": "Abhisek Mohanty",
}

# Approximate Lahiri ayanamsha at native birth
_LAHIRI_AYAN_DEG = 23.5

# All 8 required outer body keys
_REQUIRED_OUTER = [
    "chiron", "ceres", "pallas", "juno",
    "vesta", "uranus", "neptune", "pluto",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def native_chart():
    """compute_chart() output for native birth (Lahiri ayanamsha)."""
    return compute_chart(NATIVE_INPUTS, ayanamsha_id="lahiri")


@pytest.fixture(scope="module")
def outer_direct():
    """compute_outer_bodies() called directly for unit-level assertions."""
    set_ayanamsha("lahiri", jd_ut=NATIVE_JD_UT)
    return compute_outer_bodies(
        NATIVE_JD_UT,
        ayanamsha_deg=_LAHIRI_AYAN_DEG,
    )


# ---------------------------------------------------------------------------
# 1. compute_chart() integration — outer_bodies key
# ---------------------------------------------------------------------------

class TestComputeChartOuterBodies:
    """Asserts 1–9: outer_bodies key + required body presence."""

    def test_outer_bodies_key_present(self, native_chart):
        """Assertion 1: compute_chart() must expose 'outer_bodies' key."""
        assert "outer_bodies" in native_chart, (
            "compute_chart() missing 'outer_bodies' key — E-05 regression"
        )

    @pytest.mark.parametrize("body_name", _REQUIRED_OUTER)
    def test_required_body_present(self, native_chart, body_name):
        """Assertion 2–9: each of the 8 required outer bodies is in outer_bodies."""
        outer = native_chart["outer_bodies"]
        assert body_name in outer, (
            f"outer_bodies missing required body: '{body_name}'"
        )

    @pytest.mark.parametrize("body_name", _REQUIRED_OUTER)
    def test_body_dict_not_none(self, native_chart, body_name):
        """All 8 main bodies must have a non-None dict (not graceful-None)."""
        body = native_chart["outer_bodies"][body_name]
        assert body is not None, (
            f"outer_bodies['{body_name}'] is None — expected a valid dict"
        )


# ---------------------------------------------------------------------------
# 2. Longitude range and finiteness
# ---------------------------------------------------------------------------

class TestLongitudeRange:
    """Assertions 10–17: longitude is a finite float in [0, 360)."""

    @pytest.mark.parametrize("body_name", _REQUIRED_OUTER)
    def test_longitude_in_range(self, native_chart, body_name):
        """Assertion: longitude in [0, 360) for each required body."""
        lon = native_chart["outer_bodies"][body_name]["longitude"]
        assert math.isfinite(lon), f"{body_name} longitude is not finite: {lon}"
        assert 0.0 <= lon < 360.0, (
            f"{body_name} longitude {lon} out of range [0, 360)"
        )


# ---------------------------------------------------------------------------
# 3. Field type / presence checks
# ---------------------------------------------------------------------------

class TestBodyFieldTypes:
    """Assertions 18–25: sign, nakshatra, retro, speed field types."""

    @pytest.mark.parametrize("body_name", _REQUIRED_OUTER)
    def test_sign_is_nonempty_string(self, native_chart, body_name):
        sign = native_chart["outer_bodies"][body_name]["sign"]
        assert isinstance(sign, str) and len(sign) > 0, (
            f"{body_name} sign is not a non-empty string: {sign!r}"
        )

    @pytest.mark.parametrize("body_name", _REQUIRED_OUTER)
    def test_nakshatra_is_nonempty_string(self, native_chart, body_name):
        nak = native_chart["outer_bodies"][body_name]["nakshatra"]
        assert isinstance(nak, str) and len(nak) > 0, (
            f"{body_name} nakshatra is not a non-empty string: {nak!r}"
        )

    @pytest.mark.parametrize("body_name", _REQUIRED_OUTER)
    def test_retro_is_bool(self, native_chart, body_name):
        retro = native_chart["outer_bodies"][body_name]["retro"]
        assert isinstance(retro, bool), (
            f"{body_name} retro field is not bool: {retro!r}"
        )

    @pytest.mark.parametrize("body_name", _REQUIRED_OUTER)
    def test_speed_is_float(self, native_chart, body_name):
        speed = native_chart["outer_bodies"][body_name]["speed"]
        assert isinstance(speed, (int, float)), (
            f"{body_name} speed is not numeric: {speed!r}"
        )

    @pytest.mark.parametrize("body_name", _REQUIRED_OUTER)
    def test_significance_is_nonempty_string(self, native_chart, body_name):
        sig = native_chart["outer_bodies"][body_name]["significance"]
        assert isinstance(sig, str) and len(sig) > 0, (
            f"{body_name} significance is not a non-empty string: {sig!r}"
        )


# ---------------------------------------------------------------------------
# 4. Retro bool check for slow outer planets (value not asserted — varies)
# ---------------------------------------------------------------------------

class TestSlowPlanetRetroType:
    """uranus/neptune retro is bool — value varies by date, type does not."""

    def test_uranus_retro_is_bool(self, native_chart):
        assert isinstance(native_chart["outer_bodies"]["uranus"]["retro"], bool)

    def test_neptune_retro_is_bool(self, native_chart):
        assert isinstance(native_chart["outer_bodies"]["neptune"]["retro"], bool)

    def test_pluto_longitude_finite(self, native_chart):
        lon = native_chart["outer_bodies"]["pluto"]["longitude"]
        assert math.isfinite(lon)
        assert 0.0 <= lon < 360.0


# ---------------------------------------------------------------------------
# 5. Sedna / Eris — graceful degradation (None or valid dict)
# ---------------------------------------------------------------------------

class TestNumberedAsteroidGracefulDegradation:
    """Sedna and Eris slots exist; may be None if ephemeris files absent."""

    def test_sedna_key_present(self, native_chart):
        """Assertion: outer_bodies dict contains 'sedna' key."""
        assert "sedna" in native_chart["outer_bodies"], (
            "outer_bodies missing 'sedna' key"
        )

    def test_eris_key_present(self, native_chart):
        """Assertion: outer_bodies dict contains 'eris' key."""
        assert "eris" in native_chart["outer_bodies"], (
            "outer_bodies missing 'eris' key"
        )

    def test_sedna_is_none_or_valid_dict(self, native_chart):
        sedna = native_chart["outer_bodies"]["sedna"]
        if sedna is not None:
            lon = sedna["longitude"]
            assert math.isfinite(lon) and 0.0 <= lon < 360.0, (
                f"Sedna longitude {lon} out of range when ephemeris available"
            )

    def test_eris_is_none_or_valid_dict(self, native_chart):
        eris = native_chart["outer_bodies"]["eris"]
        if eris is not None:
            lon = eris["longitude"]
            assert math.isfinite(lon) and 0.0 <= lon < 360.0, (
                f"Eris longitude {lon} out of range when ephemeris available"
            )


# ---------------------------------------------------------------------------
# 6. Regression guards — prior sessions E-01 through E-04
# ---------------------------------------------------------------------------

class TestNoRegressions:
    """Asserts the prior session deliverables are still present."""

    def test_grahas_still_9_entries(self, native_chart):
        """E-01 regression guard: grahas must still have exactly 9 entries."""
        assert len(native_chart["grahas"]) == 9, (
            f"grahas count regressed: {len(native_chart['grahas'])} != 9"
        )

    def test_node_variants_present(self, native_chart):
        """E-03 regression guard: node_variants key must still be present."""
        assert "node_variants" in native_chart, (
            "compute_chart() missing 'node_variants' key — E-03 regression"
        )

    def test_lilith_variants_present(self, native_chart):
        """E-04 regression guard: lilith_variants key must still be present."""
        assert "lilith_variants" in native_chart, (
            "compute_chart() missing 'lilith_variants' key — E-04 regression"
        )

    def test_node_variants_has_rahu_true(self, native_chart):
        """E-03 regression: rahu_true must be in node_variants."""
        assert "rahu_true" in native_chart["node_variants"]

    def test_lilith_variants_has_mean(self, native_chart):
        """E-04 regression: lilith_mean must be in lilith_variants."""
        assert "lilith_mean" in native_chart["lilith_variants"]


# ---------------------------------------------------------------------------
# 7. Direct unit — compute_outer_bodies()
# ---------------------------------------------------------------------------

class TestComputeOuterBodiesDirect:
    """Direct unit tests on compute_outer_bodies() (separate from compute_chart)."""

    def test_returns_dict(self, outer_direct):
        assert isinstance(outer_direct, dict)

    def test_has_all_required_bodies(self, outer_direct):
        for name in _REQUIRED_OUTER:
            assert name in outer_direct, f"Missing body: {name}"

    def test_has_sedna_key(self, outer_direct):
        assert "sedna" in outer_direct

    def test_has_eris_key(self, outer_direct):
        assert "eris" in outer_direct

    def test_chiron_longitude_range(self, outer_direct):
        chiron = outer_direct["chiron"]
        assert chiron is not None
        lon = chiron["longitude"]
        assert math.isfinite(lon)
        assert 0.0 <= lon < 360.0

    def test_pada_in_range(self, outer_direct):
        """pada must be 1–4 for all non-None bodies."""
        for name in _REQUIRED_OUTER:
            body = outer_direct[name]
            assert body is not None
            assert 1 <= body["pada"] <= 4, (
                f"{name} pada {body['pada']} outside [1, 4]"
            )

    def test_sign_index_in_range(self, outer_direct):
        """sign_index must be 1–12."""
        for name in _REQUIRED_OUTER:
            body = outer_direct[name]
            assert body is not None
            assert 1 <= body["sign_index"] <= 12, (
                f"{name} sign_index {body['sign_index']} outside [1, 12]"
            )
