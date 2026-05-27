"""
test_pyswisseph_crosscheck.py — Independent pyswisseph cross-check + edge cases.

Goals (per brief 1.2 §AC.2, §AC.3):

  AC.2 — Cross-check that the engine's astronomical core agrees with a
         direct pyswisseph call (i.e. no adapter / config drift). We import
         swisseph here OUTSIDE the engine module to keep the check honest.

  AC.3 — Edge-case validation set: extreme latitudes, leap-second-boundary
         dates, retrograde-station-adjacent dates — assert no NaN /
         exceptions / out-of-bounds longitudes. Not parity vs an oracle;
         just non-crash + structural sanity.

This test set does NOT load the JH oracle — it is an independent contract
on the engine + pyswisseph pair, kept separate from the JH parity battery.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest
import swisseph as swe

from natal_engine import compute_chart
from natal_engine.ayanamsha_registry import apply_ayanamsha


# ---------------------------------------------------------------------------
# AC.2 — pyswisseph cross-check (no engine in the truth column)
# ---------------------------------------------------------------------------

NATIVE_INPUTS = {
    "datetime_iso": "1984-02-05T10:43:00+05:30",
    "tz_offset_hours": 5.5,
    "latitude_deg": 20.233333,
    "longitude_deg": 85.833333,
    "place_name": "Bhubaneswar",
    "subject_label": "Abhisek Mohanty",
}


def _native_jd_ut() -> float:
    # 1984-02-05 10:43 IST = 05:13:00 UT
    return swe.julday(1984, 2, 5, 5 + 13 / 60.0, swe.GREG_CAL)


def test_pyswisseph_sun_moon_agree_with_engine_under_jh_true_chitra() -> None:
    """Sun + Moon sidereal longitude: independent swisseph call vs engine."""
    jd_ut = _native_jd_ut()
    # Independent reference: apply ayanamsha via the registry then read directly
    apply_ayanamsha(jd_ut, "jh_true_chitra")
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
    ref_sun = swe.calc_ut(jd_ut, swe.SUN, flags)[0][0] % 360.0
    ref_moon = swe.calc_ut(jd_ut, swe.MOON, flags)[0][0] % 360.0

    chart = compute_chart(
        NATIVE_INPUTS,
        ayanamsha_id="jh_true_chitra",
        computed_at_iso="1984-02-05T05:13:00+00:00",
    )
    eng_sun = next(g for g in chart["grahas"] if g["name"] == "Sun")["longitude_deg"]
    eng_moon = next(g for g in chart["grahas"] if g["name"] == "Moon")["longitude_deg"]

    # The engine wraps the same swisseph call; arc-second agreement is the
    # honest contract (1" tolerance allows for one ULP-ish numerical wiggle).
    assert abs(eng_sun - ref_sun) * 3600.0 < 1.0, (
        f"Sun engine={eng_sun:.9f}° vs swisseph={ref_sun:.9f}°"
    )
    assert abs(eng_moon - ref_moon) * 3600.0 < 1.0, (
        f"Moon engine={eng_moon:.9f}° vs swisseph={ref_moon:.9f}°"
    )


def test_pyswisseph_rahu_uses_mean_node() -> None:
    """Engine pins Rahu to MEAN_NODE (Phase 4B standard). Cross-check that
    the engine's Rahu longitude matches a direct MEAN_NODE swisseph call.

    We do NOT cross-check against TRUE_NODE here because TRUE_NODE requires
    the swiss ephemeris data files (FLG_SWIEPH) which are not installed in
    the dev venv (Moshier fallback can't evaluate TRUE_NODE in this build).
    The MEAN_NODE vs TRUE_NODE distinction is documented in
    positions.py / NINE_GRAHAS_SWE.
    """
    jd_ut = _native_jd_ut()
    apply_ayanamsha(jd_ut, "jh_true_chitra")
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
    ref_mean = swe.calc_ut(jd_ut, swe.MEAN_NODE, flags)[0][0] % 360.0

    chart = compute_chart(
        NATIVE_INPUTS,
        ayanamsha_id="jh_true_chitra",
        computed_at_iso="1984-02-05T05:13:00+00:00",
    )
    eng_rahu = next(g for g in chart["grahas"] if g["name"] == "Rahu")["longitude_deg"]

    assert abs(eng_rahu - ref_mean) * 3600.0 < 1.0, (
        f"Rahu must match MEAN_NODE: engine={eng_rahu:.6f} mean={ref_mean:.6f}"
    )
    # MEAN_NODE behaves deterministically (no ephemeris-data dependency).
    # The JH parity oracle further validates Rahu under the same convention:
    # the parity test asserts engine Rahu within 60" of JH's 49.048586°.


def test_ketu_is_rahu_plus_180() -> None:
    """Engine derives Ketu = (Rahu + 180) mod 360 — assert that holds."""
    chart = compute_chart(
        NATIVE_INPUTS,
        ayanamsha_id="jh_true_chitra",
        computed_at_iso="1984-02-05T05:13:00+00:00",
    )
    rahu = next(g for g in chart["grahas"] if g["name"] == "Rahu")["longitude_deg"]
    ketu = next(g for g in chart["grahas"] if g["name"] == "Ketu")["longitude_deg"]
    expected = (rahu + 180.0) % 360.0
    delta_arcsec = abs(ketu - expected) * 3600.0
    assert delta_arcsec < 0.001, (
        f"Ketu must equal Rahu+180mod360: rahu={rahu:.9f} ketu={ketu:.9f} "
        f"expected={expected:.9f} delta_arcsec={delta_arcsec:.6f}"
    )


# ---------------------------------------------------------------------------
# AC.3 — Edge-case validation set
# ---------------------------------------------------------------------------

def _all_longitudes_in_range(chart: dict) -> bool:
    """All emitted longitudes must be finite + in [0, 360)."""
    for g in chart["grahas"]:
        lon = g["longitude_deg"]
        if not math.isfinite(lon) or not (0.0 <= lon < 360.0):
            return False
        if not math.isfinite(g["speed_deg_per_day"]):
            return False
    asc = chart["ascendant"]["longitude_deg"]
    if not math.isfinite(asc) or not (0.0 <= asc < 360.0):
        return False
    return True


def test_edge_case_high_latitude_78n_does_not_crash() -> None:
    """Lat=78N (Svalbard) — the houses_ex Placidus call CAN throw near the
    poles; the engine should still produce finite longitudes for the 9
    grahas (which don't depend on house system)."""
    inputs = {
        "datetime_iso": "2000-06-21T12:00:00+00:00",
        "tz_offset_hours": 0.0,
        "latitude_deg": 78.0,
        "longitude_deg": 15.0,
        "place_name": "Svalbard",
    }
    try:
        chart = compute_chart(
            inputs, ayanamsha_id="jh_true_chitra",
            computed_at_iso="2000-06-21T12:00:00+00:00",
        )
    except Exception as exc:
        # Document the failure but don't pass it off as silent.
        pytest.fail(f"compute_chart raised at lat=78N: {exc!r}")
    assert _all_longitudes_in_range(chart), "non-finite longitude at extreme latitude"


def test_edge_case_leap_second_boundary_does_not_crash() -> None:
    """A nominal leap-second-boundary moment (1999-12-31 23:59:60 UTC). We
    can't actually express :60 in Python's datetime, so use the closest
    legal instant (23:59:59) — but the test exists to flag if pyswisseph
    starts emitting non-finite values near calendar discontinuities."""
    inputs = {
        "datetime_iso": "1999-12-31T23:59:59+00:00",
        "tz_offset_hours": 0.0,
        "latitude_deg": 0.0,
        "longitude_deg": 0.0,
        "place_name": "Equator/Greenwich",
    }
    chart = compute_chart(
        inputs, ayanamsha_id="jh_true_chitra",
        computed_at_iso="1999-12-31T23:59:59+00:00",
    )
    assert _all_longitudes_in_range(chart), (
        "non-finite longitude at leap-second-boundary moment"
    )


def test_edge_case_retrograde_station_adjacent_dates() -> None:
    """Mercury retrograde stations occur ~3-4×/year. We sample around a
    known station (2024-04-01, near apparent retrograde for Mercury) and
    assert all chart fields are finite + valid. Doesn't assert direction
    flip — only structural soundness."""
    # Pick a date a few days after a Mercury station; the engine should still
    # emit a finite chart.
    for iso in [
        "2024-04-01T12:00:00+00:00",
        "2024-04-02T12:00:00+00:00",
        "2024-04-15T12:00:00+00:00",  # mid-retrograde
        "2024-05-01T12:00:00+00:00",  # back direct
    ]:
        inputs = {
            "datetime_iso": iso,
            "tz_offset_hours": 0.0,
            "latitude_deg": 0.0,
            "longitude_deg": 0.0,
            "place_name": "Equator/Greenwich",
        }
        chart = compute_chart(
            inputs, ayanamsha_id="jh_true_chitra",
            computed_at_iso=iso,
        )
        assert _all_longitudes_in_range(chart), (
            f"non-finite longitude at {iso}"
        )


def test_edge_case_southern_high_latitude_minus_78s() -> None:
    """Mirror of the 78N case, southern hemisphere."""
    inputs = {
        "datetime_iso": "2000-12-21T12:00:00+00:00",
        "tz_offset_hours": 0.0,
        "latitude_deg": -78.0,
        "longitude_deg": -120.0,
        "place_name": "Antarctica",
    }
    chart = compute_chart(
        inputs, ayanamsha_id="jh_true_chitra",
        computed_at_iso="2000-12-21T12:00:00+00:00",
    )
    assert _all_longitudes_in_range(chart), (
        "non-finite longitude at lat=-78S"
    )


def test_three_ayanamsha_ids_all_produce_valid_charts() -> None:
    """Smoke-test the registry: each id produces a schema-valid chart with
    finite longitudes (catches a registry entry whose swe_sid_mode constant
    has been renamed in a future swisseph version)."""
    for ay_id in ("jh_true_chitra", "kp", "lahiri_standard"):
        chart = compute_chart(
            NATIVE_INPUTS, ayanamsha_id=ay_id,
            computed_at_iso="1984-02-05T05:13:00+00:00",
        )
        assert _all_longitudes_in_range(chart), (
            f"non-finite longitude for ayanamsha_id={ay_id!r}"
        )
        assert chart["ayanamsha"]["id"] == ay_id
        assert 0.0 < chart["ayanamsha"]["value_deg"] < 30.0, (
            f"ayanamsha value out of plausible range for {ay_id!r}: "
            f"{chart['ayanamsha']['value_deg']}°"
        )
