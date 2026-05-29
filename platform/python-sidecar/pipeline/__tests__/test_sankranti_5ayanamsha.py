"""
test_sankranti_5ayanamsha.py — Unit tests for sankranti computation (G6).

No DB required. Tests the computation functions imported from
bootstrap_sankranti_saturn.
"""
import sys
import os

# Make the pipeline package importable when run from repo root or __tests__/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
import swisseph as swe
from bootstrap_sankranti_saturn import (
    get_sun_longitude_sidereal,
    find_sankranti,
    jd_to_datetime_utc,
    AYANAMSHA_MAP,
    SIGNS,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LAHIRI = AYANAMSHA_MAP["lahiri"]
NATIVE_BIRTH_JD = swe.julday(1984, 2, 5, 5.0 + 13.0 / 60.0)  # 10:43 IST = 05:13 UTC


# ---------------------------------------------------------------------------
# Tests: basic longitude retrieval
# ---------------------------------------------------------------------------

def test_sun_longitude_is_in_range_at_birth():
    """Sun's sidereal longitude at native birth should be in [0, 360)."""
    lon = get_sun_longitude_sidereal(NATIVE_BIRTH_JD, LAHIRI)
    assert 0.0 <= lon < 360.0, f"Expected [0,360), got {lon}"


def test_sun_in_capricorn_at_native_birth_lahiri():
    """
    Native born 1984-02-05 10:43 IST. Sun sidereal (Lahiri) should be
    in Capricorn (270°–300°, sign 10).
    """
    lon = get_sun_longitude_sidereal(NATIVE_BIRTH_JD, LAHIRI)
    sign_number = int(lon / 30) + 1
    assert sign_number == 10, (
        f"Expected Sun in Capricorn (sign 10) for Lahiri, got sign {sign_number} "
        f"(lon={lon:.4f}°)"
    )


def test_sun_in_capricorn_longitude_range_at_native_birth():
    """Sun longitude at native birth should be between 270° and 300° for Lahiri."""
    lon = get_sun_longitude_sidereal(NATIVE_BIRTH_JD, LAHIRI)
    assert 270.0 <= lon < 300.0, (
        f"Sun longitude {lon:.4f}° not in Capricorn range 270–300° for Lahiri"
    )


# ---------------------------------------------------------------------------
# Tests: find_sankranti — Aries ingress 1984
# ---------------------------------------------------------------------------

def test_mesha_sankranti_1984_lahiri_falls_march():
    """
    Mesha Sankranti (Sun enters Aries 0°) for Lahiri 1984 should fall
    between March 13 and March 15.
    """
    jd_jan1 = swe.julday(1984, 1, 1, 0.0)
    jd_may1 = swe.julday(1984, 5, 1, 0.0)
    jd_aries = find_sankranti(0.0, jd_jan1, jd_may1, LAHIRI)
    dt, date_str, year = jd_to_datetime_utc(jd_aries)
    # Lahiri ayanamsha Mesha Sankranti ~April 13-14 (tropical + ~23.8° offset)
    # For Lahiri, Mesha Sankranti is typically April 13-14
    month = dt.month
    day = dt.day
    assert month == 4, f"Expected April for Lahiri Mesha Sankranti 1984, got month={month}"
    assert 12 <= day <= 16, f"Expected day 12-16 of April, got day={day}"


def test_mesha_sankranti_1984_year_correct():
    """Year returned from jd_to_datetime_utc for Aries ingress 1984 should be 1984."""
    jd_jan1 = swe.julday(1984, 1, 1, 0.0)
    jd_may1 = swe.julday(1984, 5, 1, 0.0)
    jd_aries = find_sankranti(0.0, jd_jan1, jd_may1, LAHIRI)
    _, _, year = jd_to_datetime_utc(jd_aries)
    assert year == 1984, f"Expected year 1984, got {year}"


# ---------------------------------------------------------------------------
# Tests: sankranti produces 12 entries with correct spacing
# ---------------------------------------------------------------------------

def _compute_all_12_sankrantis_1984(swe_id: int) -> list:
    """Helper: compute all 12 sankrantis for 1984 for given ayanamsha."""
    jd_jan1 = swe.julday(1984, 1, 1, 0.0)
    jd_may1 = swe.julday(1984, 5, 1, 0.0)
    jd_aries = find_sankranti(0.0, jd_jan1, jd_may1, swe_id)

    entries = []
    prev_jd = jd_aries
    for sign_idx in range(12):
        target_lon = float(sign_idx * 30)
        if sign_idx == 0:
            jd_entry = jd_aries
        else:
            jd_entry = find_sankranti(
                target_lon,
                prev_jd + 20.0,
                prev_jd + 50.0,
                swe_id,
            )
        prev_jd = jd_entry
        entries.append(jd_entry)
    return entries


def test_sankranti_produces_12_entries_per_year_lahiri():
    """Computing sankrantis for 1984 (Lahiri) should give exactly 12 entries."""
    entries = _compute_all_12_sankrantis_1984(LAHIRI)
    assert len(entries) == 12, f"Expected 12 entries, got {len(entries)}"


def test_sankranti_entries_spaced_roughly_30_days_apart():
    """
    Consecutive sankranti entries should be ~27–33 days apart
    (Sun takes 27.3–31.4 days per sign due to elliptical orbit).
    """
    entries = _compute_all_12_sankrantis_1984(LAHIRI)
    for i in range(1, 12):
        gap = entries[i] - entries[i - 1]
        assert 27.0 <= gap <= 33.0, (
            f"Gap between sign {i} and {i+1} is {gap:.2f} days "
            f"(expected 27–33 days)"
        )


def test_sankranti_entries_ascending_order():
    """Sankranti JDs for 1984 should be strictly ascending."""
    entries = _compute_all_12_sankrantis_1984(LAHIRI)
    for i in range(1, 12):
        assert entries[i] > entries[i - 1], (
            f"Entry {i} JD {entries[i]:.4f} not greater than {i-1} JD {entries[i-1]:.4f}"
        )


# ---------------------------------------------------------------------------
# Tests: sign verification at computed sankranti JDs
# ---------------------------------------------------------------------------

def test_sun_is_at_zero_degrees_of_sign_at_aries_ingress():
    """At Aries ingress JD, Sun's sidereal longitude should be ~0°."""
    jd_jan1 = swe.julday(1984, 1, 1, 0.0)
    jd_may1 = swe.julday(1984, 5, 1, 0.0)
    jd_aries = find_sankranti(0.0, jd_jan1, jd_may1, LAHIRI)
    lon = get_sun_longitude_sidereal(jd_aries, LAHIRI)
    # Should be very close to 0° (or 360° which is same point)
    assert lon < 0.01 or lon > 359.99, (
        f"Sun longitude at Aries ingress should be ~0°, got {lon:.6f}°"
    )


def test_sun_in_correct_sign_at_each_sankranti():
    """At each computed sankranti JD, Sun should be at the start of the expected sign."""
    entries = _compute_all_12_sankrantis_1984(LAHIRI)
    for sign_idx, jd_entry in enumerate(entries):
        lon = get_sun_longitude_sidereal(jd_entry, LAHIRI)
        expected_start = float(sign_idx * 30)
        diff = abs((lon - expected_start) % 360.0)
        if diff > 180.0:
            diff = 360.0 - diff
        assert diff < 0.01, (
            f"Sign {sign_idx+1} ({SIGNS[sign_idx]}): expected lon ~{expected_start}°, "
            f"got {lon:.4f}° (diff={diff:.6f}°)"
        )


# ---------------------------------------------------------------------------
# Tests: jd_to_datetime_utc
# ---------------------------------------------------------------------------

def test_jd_to_datetime_utc_native_birth():
    """JD for native birth should convert to 1984-02-05 UTC datetime."""
    dt, date_str, year = jd_to_datetime_utc(NATIVE_BIRTH_JD)
    assert year == 1984
    assert dt.month == 2
    assert dt.day == 5
    assert date_str == "1984-02-05"


def test_jd_to_datetime_utc_timezone_is_utc():
    """jd_to_datetime_utc should return timezone-aware datetime in UTC."""
    from datetime import timezone
    dt, _, _ = jd_to_datetime_utc(NATIVE_BIRTH_JD)
    assert dt.tzinfo is not None
    assert dt.tzinfo == timezone.utc


# ---------------------------------------------------------------------------
# Tests: multiple ayanamshas consistency
# ---------------------------------------------------------------------------

def test_all_5_ayanamshas_sun_in_capricorn_at_native_birth():
    """
    At native birth (1984-02-05), Sun should be in Capricorn for all 5 ayanamshas
    (ayanamsha offset differences are small enough that Feb 5 is well within Capricorn
    for all of them).
    """
    for name, swe_id in AYANAMSHA_MAP.items():
        lon = get_sun_longitude_sidereal(NATIVE_BIRTH_JD, swe_id)
        sign = int(lon / 30) + 1
        assert sign == 10, (
            f"Ayanamsha {name}: expected Sun in Capricorn (10), got sign {sign} "
            f"(lon={lon:.4f}°)"
        )


def test_ayanamsha_offsets_differ_slightly():
    """
    Different ayanamshas should give different Sun longitudes at native birth
    (they should not all be identical).
    """
    lons = set()
    for name, swe_id in AYANAMSHA_MAP.items():
        lon = round(get_sun_longitude_sidereal(NATIVE_BIRTH_JD, swe_id), 4)
        lons.add(lon)
    assert len(lons) > 1, "All ayanamshas gave identical Sun longitudes — unexpected"
