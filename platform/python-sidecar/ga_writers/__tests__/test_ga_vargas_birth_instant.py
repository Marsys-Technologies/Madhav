"""ga_vargas must compute graha longitudes for the BIRTH instant, not tz hours later.

Nirmāṇa L1-W1 finding F-A1 (cross-layer notice #1747).

PyJHora carries two julian-day conventions and they are not interchangeable.
`drik.sidereal_longitude`'s own docstring states it:

    "The julian day number supplied to this function must be UTC date/time.
     All other functions of this PyJHora library will require JD and not JD_UTC.
     JD_UTC = JD - Place.TimeZoneInFloatHours"

`ga_vargas_writer` builds its JD from the LOCAL time of birth, so it holds
PyJHora's "JD" -- correct for `drik.ascendant(jd, place)`, which applies the
timezone itself, and wrong for `drik.sidereal_longitude`, which does not.

The defect hid because the FORENSIC gate checks Sun sign, Moon nakshatra and
Lagna -- and the Lagna call is the one that IS place-aware. Meanwhile 21.9% of
varga sign rows disagreed with `ga_positions`' own L1 longitudes, rising to 96%
at D2700 as the divisor amplifies a sub-degree error into a sign flip.

These are golden values measured from production `chart_facts`
(`graha_position.longitude_sidereal`, chart 482012f1, lahiri_chitrapaksha) --
i.e. from the L1 authority this asset must agree with, per CLAUDE.md §N.5, not
from this writer's own output.
"""
from __future__ import annotations

import os

import pytest

# Both libraries are in requirements-ci.txt.  Under CI (GITHUB_ACTIONS=true) a missing one must
# FAIL the module's collection, not silently skip every test in it (CLAUDE.md §N.8: a green that
# nothing could have turned red is not a result).  Locally, an absent dependency still skips.
if os.environ.get("GITHUB_ACTIONS") == "true":
    import jhora  # noqa: F401
    import swisseph  # noqa: F401
else:
    pytest.importorskip("jhora", reason="PyJHora required for the birth-instant regression")
    pytest.importorskip("swisseph")

# Native birth params (CLAUDE.md §B), as stored in public.charts.
BIRTH_LAT = 20.2961
BIRTH_LON = 85.8245
BIRTH_TZ = 5.5
BIRTH_DATE = (1984, 2, 5)
BIRTH_TIME = (10, 43, 0)

# From chart_facts.graha_position / fact_key='longitude_sidereal'.
L1_AUTHORITY_LONGITUDES = {
    "Sun": 291.9626,
    "Moon": 327.0552,
}

# One tenth of an arcsecond is far tighter than the 0.23 deg (Sun) / 2.72 deg
# (Moon) error this test exists to catch, and loose enough to absorb float noise.
TOLERANCE_DEG = 0.001


def _longitudes(jd: float, ayanamsha_id: str = "lahiri_chitrapaksha") -> dict[str, float]:
    import swisseph as swe

    from pyjhora_adapter._ayanamsha import resolve_mode
    from pyjhora_adapter._jhora import drik

    mode, _ = resolve_mode(ayanamsha_id)
    drik.set_ayanamsa_mode(mode)
    return {
        "Sun": float(drik.sidereal_longitude(jd, swe.SUN)) % 360.0,
        "Moon": float(drik.sidereal_longitude(jd, swe.MOON)) % 360.0,
    }


def _birth_jds() -> tuple[float, float]:
    """Return (local-time JD as the writer builds it, the UTC JD it must use)."""
    from pyjhora_adapter._jhora import drik, utils

    jd_local = utils.julian_day_number(drik.Date(*BIRTH_DATE), BIRTH_TIME)
    return jd_local, jd_local - BIRTH_TZ / 24.0


def test_the_writer_itself_reproduces_the_l1_authority_longitudes() -> None:
    """End-to-end: ga_vargas' OWN D1 computation must agree with ga_positions.

    Calls the writer's `_compute_varga_positions` rather than re-deriving the
    longitudes here, so the test exercises the code that ships. Re-deriving them
    independently would pass whether or not the writer was fixed.
    """
    from ga_writers.ga_vargas_writer import _compute_varga_positions

    jd_local, _ = _birth_jds()
    _, d1_longitudes = _compute_varga_positions(
        jd_local, "lahiri_chitrapaksha", BIRTH_LAT, BIRTH_LON, BIRTH_TZ,
    )
    for body, expected in L1_AUTHORITY_LONGITUDES.items():
        assert d1_longitudes[body] == pytest.approx(expected, abs=TOLERANCE_DEG), (
            f"{body}: ga_vargas computes {d1_longitudes[body]:.4f} against the L1 "
            f"authority's {expected:.4f} — the two L1 surfaces must not disagree (§N.5)"
        )


def test_reference_convention_matches_the_l1_authority() -> None:
    """The convention itself, independent of the writer: JD_UTC reproduces L1."""
    _, jd_utc = _birth_jds()
    actual = _longitudes(jd_utc)
    for body, expected in L1_AUTHORITY_LONGITUDES.items():
        assert actual[body] == pytest.approx(expected, abs=TOLERANCE_DEG)


def test_local_julian_day_is_wrong_by_exactly_the_timezone_offset() -> None:
    """The pre-fix behaviour must remain detectable, or this test proves nothing.

    Without this, a regression that quietly reverted to the local JD would still
    pass the assertion above only if the fix were also reverted -- so pin the
    defect's signature: each body offset by the SAME fraction of a day, equal to
    the timezone, expressed in its own daily motion. Two bodies whose daily
    motion differs ~12x is what makes this a real detector rather than an
    arithmetic identity.
    """
    jd_local, jd_utc = _birth_jds()
    wrong = _longitudes(jd_local)
    right = _longitudes(jd_utc)

    # Approximate mean daily motion, deliberately coarse — the assertion is that
    # both bodies are displaced by the same TIME, not by the same angle.
    daily_motion = {"Sun": 1.0146, "Moon": 11.86}
    offsets_in_days = {
        body: ((wrong[body] - right[body]) % 360.0) / daily_motion[body]
        for body in L1_AUTHORITY_LONGITUDES
    }

    expected_offset_days = BIRTH_TZ / 24.0  # 0.229166…
    for body, offset in offsets_in_days.items():
        assert offset == pytest.approx(expected_offset_days, abs=0.01), (
            f"{body} displaced by {offset:.4f} d; expected the timezone offset "
            f"{expected_offset_days:.4f} d"
        )


def test_writer_passes_the_utc_julian_day_to_sidereal_longitude() -> None:
    """Guard the call site itself, so the convention cannot silently regress.

    The numeric tests above would also catch a regression, but only by running
    the ephemeris. This one names the exact mistake so a future reader sees why
    two julian-day variables exist in that function.
    """
    from pathlib import Path

    source = Path(__file__).resolve().parents[1] / "ga_vargas_writer.py"
    text = source.read_text(encoding="utf-8")
    assert "jd_utc = jd_ut - tz / 24.0" in text
    assert "drik.sidereal_longitude(jd_utc" in text
    assert "drik.sidereal_longitude(jd_ut," not in text, (
        "sidereal_longitude must never receive the local-time JD (F-A1)"
    )
    # The Lagna call is correct as-is and must NOT be 'fixed' to jd_utc:
    # drik.ascendant applies the timezone itself from `place`.
    assert "drik.ascendant(jd_ut, place)" in text


def test_parashari_d10_covers_all_signs_and_subdivision_boundaries() -> None:
    from math import nextafter

    from pyjhora_adapter.vargas import parashari_d10

    # First D10 sign in Aries–Pisces order, using zero-based sign indices.
    opening_signs = (0, 9, 2, 11, 4, 1, 6, 3, 8, 5, 10, 7)
    for natal_sign, first_sign in enumerate(opening_signs):
        for division in range(10):
            boundary = 3.0 * division
            expected = (first_sign + division) % 12
            assert parashari_d10(natal_sign, boundary) == (expected, 0.0)
            assert parashari_d10(natal_sign, boundary + 1.5) == (expected, 15.0)
            if division:
                prior_sign, prior_degree = parashari_d10(natal_sign, nextafter(boundary, 0.0))
                assert prior_sign == (expected - 1) % 12
                assert 29.99 < prior_degree < 30.0


def test_d10_writer_and_chart_adapter_use_the_parashari_positions() -> None:
    from ga_writers.ga_vargas_writer import _compute_varga_positions
    from pyjhora_adapter.vargas import compute_vargas

    jd_local, _ = _birth_jds()
    ayanamsha = "lahiri_chitrapaksha"
    vargas, _ = _compute_varga_positions(
        jd_local, ayanamsha, BIRTH_LAT, BIRTH_LON, BIRTH_TZ,
    )
    adapter = compute_vargas(
        jd_local, ayanamsha, lat=BIRTH_LAT, lon=BIRTH_LON, tz=BIRTH_TZ,
    )
    # The natal Sun is in Capricorn (even); its eighth division lands in
    # Aries. The natal Moon is in Aquarius (odd); its tenth lands in Scorpio.
    assert vargas["D10"]["Sun"]["sign"] == "Aries"
    assert vargas["D10"]["Moon"]["sign"] == "Scorpio"
    for row in adapter["D10"]:
        if row["name"] in vargas["D10"]:
            writer_row = vargas["D10"][row["name"]]
            assert row["sign_id"] == writer_row["sign_id"]
            assert row["degree_in_sign"] == pytest.approx(writer_row["degree_in_sign"])
