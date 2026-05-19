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
