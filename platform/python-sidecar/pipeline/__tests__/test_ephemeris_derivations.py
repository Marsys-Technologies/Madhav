"""Unit tests for ephemeris_derivations — assert BPHS-canonical values."""
import sys
import os

# Ensure the pipeline package is importable when running from the sidecar root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pipeline.ephemeris_derivations import (
    compute_dignity,
    compute_combust,
    compute_vargottama,
    compute_whole_sign_house,
    compute_sign_ingress,
    compute_graha_yuddha,
    d9_sign,
    midpoint_arc,
    compute_bhava_chalit_house,
)


def test_sun_exalted_in_aries_at_10deg():
    assert compute_dignity("sun", "Aries", 10.0) == "exalted"


def test_sun_debilitated_in_libra():
    assert compute_dignity("sun", "Libra", 10.0) == "debilitated"


def test_saturn_mooltrikona_in_aquarius_first_20():
    assert compute_dignity("saturn", "Aquarius", 10.0) == "mooltrikona"
    assert compute_dignity("saturn", "Aquarius", 25.0) == "own_sign"


def test_mars_debilitated_in_cancer():
    assert compute_dignity("mars", "Cancer", 28.0) == "debilitated"


def test_rahu_exalted_in_taurus():
    assert compute_dignity("rahu", "Taurus", 0.0) == "exalted"


def test_ketu_exalted_in_scorpio():
    assert compute_dignity("ketu", "Scorpio", 15.0) == "exalted"


def test_jupiter_exalted_in_cancer():
    assert compute_dignity("jupiter", "Cancer", 5.0) == "exalted"


def test_combust_mercury_retrograde_orb():
    # Mercury retrograde combust threshold is 12°; at 11° from Sun → combust.
    is_c, orb = compute_combust("mercury", 100.0, 89.0, is_retrograde=True)
    assert is_c is True
    assert abs(orb - 11.0) < 0.001


def test_combust_mercury_direct_over_threshold():
    # Mercury direct combust threshold is 14°; at 15° from Sun → NOT combust.
    is_c, orb = compute_combust("mercury", 100.0, 85.0, is_retrograde=False)
    assert is_c is False  # 15° > 14° threshold
    assert abs(orb - 15.0) < 0.001


def test_combust_sun_returns_false():
    assert compute_combust("sun", 100.0, 100.0, False) == (False, None)


def test_combust_rahu_returns_false():
    assert compute_combust("rahu", 100.0, 100.0, False) == (False, None)


def test_whole_sign_house_aries_lagna():
    # Native lagna = Aries (index 0). Transit in Capricorn (index 9) → house 10.
    assert compute_whole_sign_house("Capricorn") == 10
    # Transit in Aries itself → house 1.
    assert compute_whole_sign_house("Aries") == 1
    # Transit in Pisces (index 11) → house 12.
    assert compute_whole_sign_house("Pisces") == 12


def test_d9_sign_aries_first_navamsha():
    # Aries is movable; D9 starts at Aries; first 3°20' = Aries.
    assert d9_sign("Aries", 1.0) == "Aries"


def test_d9_sign_taurus_first_navamsha():
    # Taurus is fixed; D9 starts at 9th from Taurus = Capricorn.
    assert d9_sign("Taurus", 1.0) == "Capricorn"


def test_vargottama_aries_first_3deg():
    # Aries D1 + Aries D9 → vargottama
    assert compute_vargottama("Aries", 1.0) is True


def test_vargottama_taurus_first_3deg_is_not():
    # Taurus D1 + Capricorn D9 → NOT vargottama
    assert compute_vargottama("Taurus", 1.0) is False


def test_sign_ingress_today_when_changed():
    assert compute_sign_ingress("Taurus", "Aries") is True
    assert compute_sign_ingress("Aries", "Aries") is False
    assert compute_sign_ingress("Aries", None) is False  # first day in table


def test_graha_yuddha_mars_jupiter_within_1deg():
    same_day = {"mars": 100.0, "jupiter": 100.5}
    assert compute_graha_yuddha("mars", 100.0, same_day) == "jupiter"


def test_graha_yuddha_excludes_sun():
    same_day = {"mars": 100.0, "sun": 100.5}
    assert compute_graha_yuddha("mars", 100.0, same_day) is None


def test_graha_yuddha_over_1deg_returns_none():
    same_day = {"mars": 100.0, "jupiter": 101.5}
    assert compute_graha_yuddha("mars", 100.0, same_day) is None


# ── Bhava-Chalit (Sripati cusps) tests ───────────────────────────────────────
#
# Native Sripati madhyas (from _compute_native_sripati_cusps for
# 1984-02-05T05:13:00 UTC, Bhubaneswar, Lahiri sidereal):
#   bhava  1: 12.4189° (Aries lagna midpoint = ASC)
#   bhava  2: 39.2710°
#   bhava  3: 66.1230°
#   bhava  4: 92.9750° (IC)
#   bhava  5: 126.1230°
#   bhava  6: 159.2710°
#   bhava  7: 192.4189° (DSC)
#   bhava  8: 219.2710°
#   bhava  9: 246.1230°
#   bhava 10: 272.9750° (MC)
#   bhava 11: 306.1230°
#   bhava 12: 339.2710°
#
# Bhava sandhis (boundaries, computed by compute_bhava_chalit_house internally):
#   sandhi 12/1 : 355.8449°   sandhi 1/2 : 25.8449°   sandhi 2/3 : 52.6970°
#   sandhi 3/4 :  79.5490°    sandhi 4/5 : 109.5490°  sandhi 5/6 : 142.6970°
#   sandhi 6/7 : 175.8449°    sandhi 7/8 : 205.8449°  sandhi 8/9 : 232.6970°
#   sandhi 9/10: 259.5490°    sandhi 10/11: 289.5490° sandhi 11/12: 322.6970°

# Simple equal-spaced synthetic cusps (12 × 30° apart, starting at 0°) for
# unit tests that don't need real native values.
_EQUAL_CUSPS = [float(i * 30) for i in range(12)]  # [0, 30, 60, ..., 330]

# Actual native Sripati madhyas (verified via swisseph computation above).
_NATIVE_CUSPS = [
    12.4189, 39.2710, 66.1230, 92.9750, 126.1230, 159.2710,
    192.4189, 219.2710, 246.1230, 272.9750, 306.1230, 339.2710,
]


def test_midpoint_arc_handles_wraparound():
    # midpoint between 350° and 10° should be 0° (shortest arc = 20°, mid = 10° back from 10 = 0°)
    result = midpoint_arc(350.0, 10.0)
    assert abs(result - 0.0) < 0.001


def test_midpoint_arc_normal_case():
    result = midpoint_arc(10.0, 30.0)
    assert abs(result - 20.0) < 0.001


def test_bhava_chalit_planet_at_ascendant_degree_is_house_1():
    # ASC = 12.4189° — should land in bhava 1
    # (bhava 1 spans sandhi 355.8449° → 25.8449°)
    assert compute_bhava_chalit_house(12.4189, _NATIVE_CUSPS) == 1


def test_bhava_chalit_planet_one_degree_after_ascendant_is_house_1():
    # 13.5° is clearly within bhava 1 (ends at 25.8449°)
    assert compute_bhava_chalit_house(13.5, _NATIVE_CUSPS) == 1


def test_bhava_chalit_planet_at_descendant_is_house_7():
    # DSC = 192.4189° — should land in bhava 7
    # (bhava 7 spans sandhi 175.8449° → 205.8449°)
    assert compute_bhava_chalit_house(192.4189, _NATIVE_CUSPS) == 7


def test_bhava_chalit_planet_at_midpoint_to_2nd_is_house_2():
    # The bhava 2 madhya is 39.271°; it is well inside bhava 2
    # (spans sandhi 25.8449° → 52.6970°)
    assert compute_bhava_chalit_house(39.271, _NATIVE_CUSPS) == 2


def test_bhava_chalit_wraps_around_360_at_12_to_1():
    # A planet at 356° is just past sandhi 12/1 (355.8449°) → bhava 1
    assert compute_bhava_chalit_house(356.0, _NATIVE_CUSPS) == 1


def test_bhava_chalit_handles_lon_in_bhava_12():
    # bhava 12 spans sandhi 322.6970° → 355.8449°; 340° is inside bhava 12
    assert compute_bhava_chalit_house(340.0, _NATIVE_CUSPS) == 12


def test_bhava_chalit_native_birthday_saturn_spot_check():
    # Saturn on 1984-02-05 at sidereal Libra 22.43° = 202.43°
    # Expected: bhava 7 (Saturn opposite Aries lagna, near DSC at 192.42°)
    # bhava 7 spans 175.8449° → 205.8449°
    assert compute_bhava_chalit_house(202.43, _NATIVE_CUSPS) == 7


def test_bhava_chalit_equal_cusps_planet_at_0_is_house_1():
    # With equal cusps starting at 0°: bhava 1 = 0°–30°; planet at 5° → bhava 1
    # Boundaries for equal cusps: midpoints between 30°-apart points → at 15°, 45°...
    # sandhi 12/1 = midpoint(330, 0) = 345°; sandhi 1/2 = midpoint(0, 30) = 15°
    # bhava 1 spans 345° → 15°
    assert compute_bhava_chalit_house(5.0, _EQUAL_CUSPS) == 1


def test_compute_bhava_chalit_raises_on_wrong_cusp_count():
    import pytest
    with pytest.raises(ValueError, match="expected 12 cusps"):
        compute_bhava_chalit_house(100.0, [0.0, 30.0, 60.0])  # only 3 cusps
