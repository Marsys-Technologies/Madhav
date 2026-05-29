"""
test_saturn_ingresses.py — Unit tests for Saturn ingress computation (G21).

No DB required. Tests the computation functions imported from
bootstrap_sankranti_saturn.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import swisseph as swe
from bootstrap_sankranti_saturn import (
    get_saturn_longitude_sidereal,
    get_saturn_sign,
    is_saturn_retrograde,
    find_saturn_ingress,
    jd_to_datetime_utc,
    AYANAMSHA_MAP,
    SIGNS,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LAHIRI = AYANAMSHA_MAP["lahiri"]
START_YEAR = 1950
END_YEAR = 2100
STEP = 10.0  # days — same as seeder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def scan_saturn_ingresses(swe_id: int, start_year: int, end_year: int) -> list:
    """
    Scan for Saturn sign changes between start_year and end_year.
    Returns list of (from_sign, to_sign, ingress_jd, is_retrograde).
    """
    jd = swe.julday(start_year, 1, 1, 0.0)
    jd_end = swe.julday(end_year, 12, 31, 0.0)
    prev_sign = get_saturn_sign(jd, swe_id)
    prev_jd = jd
    ingresses = []

    while jd <= jd_end:
        jd += STEP
        curr_sign = get_saturn_sign(jd, swe_id)
        if curr_sign != prev_sign:
            ingress_jd = find_saturn_ingress(curr_sign, prev_jd, jd, swe_id)
            retro = is_saturn_retrograde(ingress_jd, swe_id)
            ingresses.append((prev_sign, curr_sign, ingress_jd, retro))
        prev_sign = curr_sign
        prev_jd = jd

    return ingresses


# ---------------------------------------------------------------------------
# Tests: basic sign/longitude retrieval
# ---------------------------------------------------------------------------

def test_saturn_longitude_is_in_range():
    """Saturn sidereal longitude should be in [0, 360)."""
    jd = swe.julday(2000, 1, 1, 0.0)
    lon = get_saturn_longitude_sidereal(jd, LAHIRI)
    assert 0.0 <= lon < 360.0, f"Expected [0,360), got {lon}"


def test_saturn_sign_is_between_1_and_12():
    """get_saturn_sign should always return 1-12."""
    for year in [1950, 1984, 2000, 2017, 2050, 2100]:
        jd = swe.julday(year, 6, 15, 0.0)
        sign = get_saturn_sign(jd, LAHIRI)
        assert 1 <= sign <= 12, f"Year {year}: sign {sign} not in [1, 12]"


def test_saturn_sign_is_1_to_12_across_all_ayanamshas():
    """Saturn sign should be 1-12 for all 5 ayanamshas at a fixed date."""
    jd = swe.julday(2000, 1, 1, 0.0)
    for name, swe_id in AYANAMSHA_MAP.items():
        sign = get_saturn_sign(jd, swe_id)
        assert 1 <= sign <= 12, f"Ayanamsha {name}: sign {sign} not in [1, 12]"


# ---------------------------------------------------------------------------
# Tests: retrograde detection
# ---------------------------------------------------------------------------

def test_retrograde_returns_boolean():
    """is_saturn_retrograde should return a bool."""
    jd = swe.julday(2000, 1, 1, 0.0)
    result = is_saturn_retrograde(jd, LAHIRI)
    assert isinstance(result, bool), f"Expected bool, got {type(result)}"


def test_saturn_not_always_retrograde():
    """Over a 12-year span, Saturn should not be retrograde every single day."""
    retrograde_count = 0
    total = 0
    jd = swe.julday(2000, 1, 1, 0.0)
    # Check every 10 days for 4 years
    for _ in range(146):
        if is_saturn_retrograde(jd, LAHIRI):
            retrograde_count += 1
        total += 1
        jd += 10.0
    # Saturn is retrograde ~37% of the time — certainly not 100% or 0%
    assert retrograde_count < total, "Saturn was retrograde every sample — unexpected"
    assert retrograde_count > 0, "Saturn was never retrograde in 4-year sample — unexpected"


# ---------------------------------------------------------------------------
# Tests: ingress scan correctness
# ---------------------------------------------------------------------------

def test_saturn_changes_sign_at_least_once_per_3_years():
    """
    Saturn moves ~1 sign per 2.5 years. Over any 3-year span we expect at least
    one sign change (direct or retrograde).
    """
    # Scan 10 different 3-year windows
    for start_year in [1950, 1960, 1975, 1990, 2000, 2010, 2020, 2030, 2050, 2080]:
        ingresses = scan_saturn_ingresses(LAHIRI, start_year, start_year + 3)
        assert len(ingresses) >= 1, (
            f"No Saturn ingress in {start_year}–{start_year+3} for Lahiri"
        )


def test_saturn_ingress_sign_numbers_valid():
    """All ingress to_sign values should be in 1-12."""
    ingresses = scan_saturn_ingresses(LAHIRI, 1980, 1990)
    for from_sign, to_sign, jd, retro in ingresses:
        assert 1 <= to_sign <= 12, f"to_sign={to_sign} out of range"
        assert 1 <= from_sign <= 12, f"from_sign={from_sign} out of range"


def test_saturn_ingress_jds_ascending():
    """Saturn ingress JDs should be strictly ascending."""
    ingresses = scan_saturn_ingresses(LAHIRI, 1970, 2020)
    jds = [e[2] for e in ingresses]
    for i in range(1, len(jds)):
        assert jds[i] > jds[i - 1], (
            f"Ingress JD not ascending at index {i}: {jds[i]:.4f} <= {jds[i-1]:.4f}"
        )


# ---------------------------------------------------------------------------
# Tests: known Saturn ingress — Capricorn ~Dec 2017 (Lahiri)
# ---------------------------------------------------------------------------

def test_saturn_entered_capricorn_jan_2020_lahiri():
    """
    Saturn entered Capricorn (sign 10) around Jan 2020 for Lahiri ayanamsha.
    Lahiri adds ~23.8° to tropical longitude, so Saturn's sidereal Capricorn
    ingress is ~2 years later than the tropical (Dec 2017) date.
    There should be a direct ingress into Capricorn between Nov 2019 and Mar 2020.
    """
    ingresses = scan_saturn_ingresses(LAHIRI, 2019, 2020)
    capricorn_entries = [
        (from_s, to_s, jd, retro)
        for (from_s, to_s, jd, retro) in ingresses
        if to_s == 10 and not retro
    ]
    assert len(capricorn_entries) >= 1, (
        "Expected at least one direct Saturn → Capricorn ingress in 2019-2020 for Lahiri. "
        f"Found ingresses: {[(SIGNS[t-1], jd_to_datetime_utc(jd)[1]) for _,t,jd,_ in ingresses]}"
    )
    # Verify the date is in early 2020 (Jan–Mar)
    _, _, ingress_jd, _ = capricorn_entries[0]
    dt, date_str, year = jd_to_datetime_utc(ingress_jd)
    assert year == 2020, f"Expected Saturn→Capricorn in 2020, got year={year} ({date_str})"
    assert dt.month in (1, 2, 3), (
        f"Expected Jan-Mar 2020 for Saturn→Capricorn ingress, got {date_str}"
    )


def test_saturn_ingress_retrograde_correctly_flagged():
    """
    Saturn's retrograde ingresses exist — verify that at least some ingresses
    in the 1970-2020 window are flagged retrograde and some direct.
    """
    ingresses = scan_saturn_ingresses(LAHIRI, 1970, 2020)
    retrograde_ingresses = [e for e in ingresses if e[3]]
    direct_ingresses = [e for e in ingresses if not e[3]]
    assert len(retrograde_ingresses) > 0, (
        "Expected some retrograde Saturn ingresses in 1970-2020, found none"
    )
    assert len(direct_ingresses) > 0, (
        "Expected some direct Saturn ingresses in 1970-2020, found none"
    )


# ---------------------------------------------------------------------------
# Tests: find_saturn_ingress precision
# ---------------------------------------------------------------------------

def test_find_saturn_ingress_precision():
    """
    After find_saturn_ingress, Saturn's longitude should be very close to
    the target sign boundary.

    Saturn (Lahiri) enters Capricorn (sign 10, boundary 270°) on 2020-01-24.
    The seeder always uses a tight bracket (prev_jd to prev_jd+10 days).
    We replicate that here: bracket Jan 20 – Feb 5, 2020.
    """
    # Tight bracket: Saturn is at ~269° on Jan 20 and ~271° on Feb 5
    jd_start = swe.julday(2020, 1, 20, 0.0)
    jd_end = swe.julday(2020, 2, 5, 0.0)

    # Find the ingress into sign 10 (Capricorn, boundary at 270°)
    ingress_jd = find_saturn_ingress(10, jd_start, jd_end, LAHIRI)
    lon = get_saturn_longitude_sidereal(ingress_jd, LAHIRI)
    expected_lon = 270.0  # sign 10 starts at 270°
    diff = abs((lon - expected_lon) % 360.0)
    if diff > 180.0:
        diff = 360.0 - diff
    assert diff < 0.01, (
        f"Saturn longitude at Capricorn ingress: expected ~270°, got {lon:.6f}° "
        f"(diff={diff:.6f}°)"
    )


# ---------------------------------------------------------------------------
# Tests: total ingress count sanity
# ---------------------------------------------------------------------------

def test_saturn_ingress_count_reasonable_1950_2100():
    """
    Saturn traverses all 12 signs in ~29.5 years. Over 150 years we expect
    roughly 150/29.5 * 12 ≈ 61 direct ingresses, plus retrograde back-and-forth
    ingresses (typically 1-2 extra per sign traversal). Observed count for Lahiri
    is ~130 (61 direct + ~69 retrograde/re-entry events).
    Total should be between 60 and 150 for Lahiri.
    """
    ingresses = scan_saturn_ingresses(LAHIRI, START_YEAR, END_YEAR)
    assert 60 <= len(ingresses) <= 150, (
        f"Expected 60-150 Saturn ingresses in 1950-2100, got {len(ingresses)}"
    )
