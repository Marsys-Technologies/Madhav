"""Unit tests for 5-ayanamsha read-time derivation in l0_ephemeris.

FORENSIC anchor: Sun tropical on 1984-02-05 = 315.874297° (pyswisseph DE441, verified).
Lahiri offset on that date ≈ 23.6349° → sidereal ≈ 292.239° = Capricorn (sign 10).
"""
import pytest
from datetime import date

from brahmagyan.l0_ephemeris import derive_sidereal, _tropical_to_jd, AYANAMSHA_MAP


NATIVE_BIRTH_DATE = date(1984, 2, 5)

# Actual Sun tropical longitude on 1984-02-05 (pyswisseph DE441, noon UT)
# Verified: 315.874297°
SUN_TROPICAL_1984_02_05 = 315.874297


# ── FORENSIC anchor ───────────────────────────────────────────────────────────

def test_forensic_anchor_lahiri():
    """Sun on native birth date: Lahiri sidereal must land in Capricorn (sign 10)."""
    jd = _tropical_to_jd(NATIVE_BIRTH_DATE)
    result = derive_sidereal(SUN_TROPICAL_1984_02_05, jd, "lahiri")
    assert result["sign_number"] == 10, (
        f"Expected Capricorn (10), got sign {result['sign_number']}; "
        f"sidereal_longitude={result['sidereal_longitude']}"
    )
    # Lahiri offset ≈ 23.63° → sidereal ≈ 292.24°; allow ±1° tolerance
    assert 291.0 <= result["sidereal_longitude"] <= 294.0, (
        f"Expected ~292°, got {result['sidereal_longitude']}"
    )
    assert result["ayanamsha_offset"] == pytest.approx(23.634937, abs=0.01)


# ── 5-ayanamsha distinct offsets ──────────────────────────────────────────────

def test_all_5_ayanamshas_return_distinct_offsets():
    """All 5 canonical ayanamshas return distinct offsets, each within 20-26°."""
    jd = _tropical_to_jd(NATIVE_BIRTH_DATE)
    offsets = {}
    for name in ["lahiri", "raman", "kp", "yukteshwar", "surya_siddhanta"]:
        r = derive_sidereal(SUN_TROPICAL_1984_02_05, jd, name)
        offsets[name] = r["ayanamsha_offset"]

    # All offsets should be in range ~20-26° (verified: 20.67–23.63°)
    for name, off in offsets.items():
        assert 20.0 <= off <= 26.0, f"{name} offset {off:.6f} outside expected 20-26° range"

    # All 5 should be distinct (rounded to 2 dp)
    rounded = [round(o, 2) for o in offsets.values()]
    assert len(set(rounded)) == 5, (
        f"Expected 5 distinct offsets, got duplicates: {offsets}"
    )


# ── Sign arithmetic ───────────────────────────────────────────────────────────

def test_sign_arithmetic_aries():
    """Tropical ~53-54° → sidereal ~30° after Lahiri → Taurus boundary area (sign 2)."""
    jd = _tropical_to_jd(NATIVE_BIRTH_DATE)
    # Lahiri offset ≈ 23.63°; tropical 53.63° → sidereal ≈ 30.00° = Taurus (sign 2)
    r = derive_sidereal(53.634937, jd, "lahiri")
    assert r["sign_number"] == 2, f"Expected Taurus (2), got {r['sign_number']}"


def test_nakshatra_ashwini():
    """Sidereal ~0-13.33° should be Ashwini (nakshatra 1)."""
    jd = _tropical_to_jd(NATIVE_BIRTH_DATE)
    # tropical ≈ 23.63° → sidereal ≈ 0° = start of Ashwini
    r = derive_sidereal(24.0, jd, "lahiri")
    # sidereal ≈ 0.37° → nakshatra 1, sign 1, pada 1
    assert r["sign_number"] == 1, f"Expected Aries (1), got {r['sign_number']}"
    assert r["nakshatra_number"] == 1, f"Expected Ashwini (1), got {r['nakshatra_number']}"


# ── Pada range ────────────────────────────────────────────────────────────────

def test_pada_range():
    """Pada must always be in [1, 4] for any input longitude."""
    jd = _tropical_to_jd(NATIVE_BIRTH_DATE)
    for tropical_lon in [0.0, 45.5, 90.0, 135.7, 180.0, 225.3, 270.0, 315.9, 359.99]:
        r = derive_sidereal(tropical_lon, jd, "lahiri")
        assert 1 <= r["pada"] <= 4, (
            f"pada={r['pada']} out of range [1,4] for tropical_lon={tropical_lon}"
        )


# ── Return keys ───────────────────────────────────────────────────────────────

def test_return_keys():
    """derive_sidereal must return all 6 required keys."""
    jd = _tropical_to_jd(NATIVE_BIRTH_DATE)
    r = derive_sidereal(SUN_TROPICAL_1984_02_05, jd, "lahiri")
    required = {
        "sidereal_longitude", "sign_number", "degree_in_sign",
        "nakshatra_number", "pada", "ayanamsha_offset",
    }
    assert required <= r.keys(), f"Missing keys: {required - r.keys()}"


# ── Error handling ────────────────────────────────────────────────────────────

def test_unknown_ayanamsha_raises():
    """Unknown ayanamsha key must raise ValueError."""
    jd = _tropical_to_jd(NATIVE_BIRTH_DATE)
    with pytest.raises(ValueError, match="Unknown ayanamsha"):
        derive_sidereal(SUN_TROPICAL_1984_02_05, jd, "bogus_ayanamsha")


# ── KP / Krishnamurti alias ───────────────────────────────────────────────────

def test_krishnamurti_alias():
    """'kp' and 'krishnamurti' must produce identical results (same SIDM constant)."""
    jd = _tropical_to_jd(NATIVE_BIRTH_DATE)
    r_kp = derive_sidereal(SUN_TROPICAL_1984_02_05, jd, "kp")
    r_kr = derive_sidereal(SUN_TROPICAL_1984_02_05, jd, "krishnamurti")
    assert r_kp == r_kr, f"kp and krishnamurti diverged: kp={r_kp}, kr={r_kr}"


# ── AYANAMSHA_MAP completeness ────────────────────────────────────────────────

def test_ayanamsha_map_keys():
    """AYANAMSHA_MAP must contain all 6 expected keys."""
    expected = {"lahiri", "raman", "kp", "krishnamurti", "yukteshwar", "surya_siddhanta"}
    assert expected <= AYANAMSHA_MAP.keys(), (
        f"Missing from AYANAMSHA_MAP: {expected - AYANAMSHA_MAP.keys()}"
    )
