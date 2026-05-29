"""
test_nakshatra_utils.py — Tests for nakshatra_utils.py pure lookup table.

Covers: 27-entry completeness, ruler cycle, boundary conditions, pada boundaries,
nakshatra_for_longitude correctness, and nakshatra_for_all_ayanamshas multi-ayanamsha dispatch.
"""

import pytest
from pipeline.nakshatra_utils import (
    NAKSHATRAS,
    NAKSHATRA_SPAN,
    PADA_SIZE,
    nakshatra_for_longitude,
    nakshatra_for_all_ayanamshas,
)

# ---------------------------------------------------------------------------
# 1. Structural completeness
# ---------------------------------------------------------------------------

def test_27_nakshatras_exist():
    """NAKSHATRAS list must contain exactly 27 entries."""
    assert len(NAKSHATRAS) == 27


def test_all_27_names_present():
    """All canonical nakshatra names must be present."""
    expected_names = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "PurvaPhalguni",
        "UttaraPhalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
        "Jyeshtha", "Mula", "PurvaAshadha", "UttaraAshadha", "Shravana",
        "Dhanishtha", "Shatabhisha", "PurvaBhadrapada", "UttaraBhadrapada", "Revati",
    ]
    actual_names = [n["name"] for n in NAKSHATRAS]
    assert actual_names == expected_names


def test_ids_sequential():
    """IDs must run from 1 to 27 in order."""
    for i, nak in enumerate(NAKSHATRAS):
        assert nak["id"] == i + 1


# ---------------------------------------------------------------------------
# 2. Ruler cycle verification
# ---------------------------------------------------------------------------

RULER_CYCLE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

def test_ruler_cycle_full():
    """Ruler at index i must equal RULER_CYCLE[i % 9]."""
    for i, nak in enumerate(NAKSHATRAS):
        assert nak["ruler"] == RULER_CYCLE[i % 9], (
            f"{nak['name']} (index {i}): expected {RULER_CYCLE[i % 9]}, got {nak['ruler']}"
        )


def test_ruler_at_index_0_is_ketu():
    """Index 0 (Ashwini) ruler = Ketu."""
    assert NAKSHATRAS[0]["ruler"] == "Ketu"


def test_ruler_at_index_8_is_mercury():
    """Index 8 (Ashlesha) ruler = Mercury."""
    assert NAKSHATRAS[8]["ruler"] == "Mercury"


def test_ruler_at_index_9_is_ketu_again():
    """Index 9 (Magha) ruler = Ketu (cycle restarts)."""
    assert NAKSHATRAS[9]["ruler"] == "Ketu"


def test_ruler_at_index_18_is_ketu_third_cycle():
    """Index 18 (Mula) ruler = Ketu (third cycle)."""
    assert NAKSHATRAS[18]["ruler"] == "Ketu"


# ---------------------------------------------------------------------------
# 3. nakshatra_for_longitude — basic positions
# ---------------------------------------------------------------------------

def test_ashwini_at_zero():
    """0° sidereal → Ashwini, id=1, pada=1."""
    result = nakshatra_for_longitude(0.0)
    assert result["id"] == 1
    assert result["name"] == "Ashwini"
    assert result["pada"] == 1
    assert result["degrees_into"] == pytest.approx(0.0, abs=1e-5)


def test_boundary_at_nakshatra_span_is_bharani():
    """
    Exactly NAKSHATRA_SPAN (13.3333...°) → first degree of Bharani (id=2), pada=1.
    Uses the computed constant to avoid truncation error in the literal 13.333333.
    """
    result = nakshatra_for_longitude(NAKSHATRA_SPAN)
    assert result["id"] == 2
    assert result["name"] == "Bharani"
    assert result["pada"] == 1


def test_moon_at_45_degrees_is_rohini():
    """
    45° sidereal falls in Rohini (id=4, start=40°, end=53.33°).
    Rohini spans NAKSHATRA_SPAN*3 → NAKSHATRA_SPAN*4 ≈ 40° → 53.33°.
    """
    result = nakshatra_for_longitude(45.0)
    assert result["id"] == 4
    assert result["name"] == "Rohini"


def test_revati_just_before_360():
    """359.999° → Revati (id=27)."""
    result = nakshatra_for_longitude(359.999)
    assert result["id"] == 27
    assert result["name"] == "Revati"


def test_360_wraps_to_ashwini():
    """360° wraps to 0° → Ashwini pada 1."""
    result = nakshatra_for_longitude(360.0)
    assert result["id"] == 1
    assert result["name"] == "Ashwini"
    assert result["pada"] == 1


def test_negative_longitude_wraps():
    """
    Negative longitude wraps correctly via % 360.
    -NAKSHATRA_SPAN → 360 - NAKSHATRA_SPAN = start of Revati (id=27).
    """
    result = nakshatra_for_longitude(-NAKSHATRA_SPAN)
    # 360 - 13.3333...° = 346.6666...° → Revati starts at NAKSHATRA_SPAN*26 ≈ 346.667°
    # Actually 346.666...° is right at the Revati boundary — id=27
    assert result["id"] == 27
    assert result["name"] == "Revati"


def test_beyond_360_wraps():
    """720° wraps to 0° → Ashwini."""
    result = nakshatra_for_longitude(720.0)
    assert result["id"] == 1
    assert result["name"] == "Ashwini"


# ---------------------------------------------------------------------------
# 4. Pada boundary tests within a nakshatra
# ---------------------------------------------------------------------------

def test_ashwini_pada_1_at_start():
    """0° into Ashwini → pada 1."""
    result = nakshatra_for_longitude(0.0)
    assert result["pada"] == 1


def test_ashwini_pada_2_at_3_333():
    """3.333334° into Ashwini → pada 2."""
    result = nakshatra_for_longitude(PADA_SIZE + 0.000001)
    assert result["pada"] == 2


def test_ashwini_pada_3_at_6_667():
    """~6.667° into Ashwini → pada 3."""
    result = nakshatra_for_longitude(PADA_SIZE * 2 + 0.000001)
    assert result["pada"] == 3


def test_ashwini_pada_4_at_10():
    """~10° into Ashwini → pada 4."""
    result = nakshatra_for_longitude(PADA_SIZE * 3 + 0.000001)
    assert result["pada"] == 4


def test_pada_clamps_at_4():
    """Pada must never exceed 4 even at the very end of a nakshatra."""
    # End of Ashwini is NAKSHATRA_SPAN - epsilon
    result = nakshatra_for_longitude(NAKSHATRA_SPAN - 0.000001)
    assert result["pada"] == 4
    assert result["id"] == 1


# ---------------------------------------------------------------------------
# 5. nakshatra_for_all_ayanamshas
# ---------------------------------------------------------------------------

def test_all_ayanamshas_returns_all_keys():
    """Result must contain one entry per ayanamsha_id."""
    offsets = {"lahiri": 23.15, "raman": 22.37, "krishnamurti": 23.86}
    tropical_lon = 50.0
    result = nakshatra_for_all_ayanamshas(tropical_lon, offsets)
    assert set(result.keys()) == {"lahiri", "raman", "krishnamurti"}


def test_all_ayanamshas_each_value_is_nakshatra_dict():
    """Each value in the result is a valid nakshatra dict with 'pada' and 'degrees_into'."""
    offsets = {"lahiri": 23.15}
    result = nakshatra_for_all_ayanamshas(100.0, offsets)
    val = result["lahiri"]
    assert "id" in val
    assert "name" in val
    assert "ruler" in val
    assert "pada" in val
    assert "degrees_into" in val
    assert 1 <= val["id"] <= 27
    assert 1 <= val["pada"] <= 4


def test_all_ayanamshas_zero_offset_matches_direct():
    """Ayanamsha offset=0 → same result as nakshatra_for_longitude(tropical_lon)."""
    tropical_lon = 75.5
    result_direct = nakshatra_for_longitude(tropical_lon)
    result_multi = nakshatra_for_all_ayanamshas(tropical_lon, {"zero": 0.0})
    assert result_multi["zero"]["id"] == result_direct["id"]
    assert result_multi["zero"]["pada"] == result_direct["pada"]


def test_all_ayanamshas_different_offsets_may_differ():
    """Large offset difference can push result into a different nakshatra."""
    # tropical_lon=13.0; offset=0 → index 0 (Ashwini); offset=14.0 → lon=-1→359 → Revati
    result = nakshatra_for_all_ayanamshas(13.0, {"no_offset": 0.0, "big_offset": 14.0})
    assert result["no_offset"]["id"] == 1   # Ashwini
    assert result["big_offset"]["id"] == 27  # Revati


def test_all_ayanamshas_empty_dict():
    """Empty ayanamsha_values → empty result dict."""
    result = nakshatra_for_all_ayanamshas(100.0, {})
    assert result == {}


# ---------------------------------------------------------------------------
# 6. degrees_into precision and bounds
# ---------------------------------------------------------------------------

def test_degrees_into_is_non_negative():
    """degrees_into must always be >= 0."""
    for lon in [0.0, 13.333333, 26.666666, 100.0, 200.0, 359.999]:
        result = nakshatra_for_longitude(lon)
        assert result["degrees_into"] >= 0.0, f"Negative degrees_into at lon={lon}"


def test_degrees_into_less_than_span():
    """degrees_into must always be < NAKSHATRA_SPAN."""
    for lon in [0.0, 13.333334, 100.0, 180.0, 270.0, 359.0]:
        result = nakshatra_for_longitude(lon)
        assert result["degrees_into"] < NAKSHATRA_SPAN, (
            f"degrees_into={result['degrees_into']} >= NAKSHATRA_SPAN at lon={lon}"
        )
