"""
Tests for rashi_utils.py — 12-sign lookup with tattva/guna metadata.
No DB interaction, no swisseph calls.
"""

import pytest
from pipeline.rashi_utils import RASHIS, rashi_for_longitude, rashi_for_all_ayanamshas


# ---------------------------------------------------------------------------
# Table completeness tests
# ---------------------------------------------------------------------------

def test_rashis_has_12_entries():
    assert len(RASHIS) == 12


def test_rashis_sequential_ids():
    """IDs must run 1 through 12 in order."""
    for i, r in enumerate(RASHIS):
        assert r["id"] == i + 1, f"Expected id={i+1}, got {r['id']} at index {i}"


def test_rashis_start_end_boundaries():
    """Each rashi spans exactly 30° and boundaries are contiguous."""
    for i, r in enumerate(RASHIS):
        assert r["start_deg"] == i * 30.0
        assert r["end_deg"] == (i + 1) * 30.0


def test_all_four_tattvas_present():
    """Fire, Earth, Air, Water — each must appear exactly 3 times."""
    from collections import Counter
    counts = Counter(r["tattva"] for r in RASHIS)
    assert counts["Fire"] == 3
    assert counts["Earth"] == 3
    assert counts["Air"] == 3
    assert counts["Water"] == 3


def test_both_gunas_present():
    """Rajas × 6, Tamas × 6."""
    from collections import Counter
    counts = Counter(r["guna"] for r in RASHIS)
    assert counts["Rajas"] == 6
    assert counts["Tamas"] == 6


def test_tattva_guna_alternation():
    """Rashis alternate Rajas/Tamas starting with Mesha=Rajas."""
    expected_gunas = ["Rajas", "Tamas"] * 6
    actual_gunas = [r["guna"] for r in RASHIS]
    assert actual_gunas == expected_gunas


def test_ruler_sun_simha():
    """Sun rules Simha (id=5)."""
    simha = next(r for r in RASHIS if r["id"] == 5)
    assert simha["name"] == "Simha"
    assert simha["ruler"] == "Sun"


def test_ruler_moon_karka():
    """Moon rules Karka (id=4)."""
    karka = next(r for r in RASHIS if r["id"] == 4)
    assert karka["name"] == "Karka"
    assert karka["ruler"] == "Moon"


def test_ruler_mars_mesha_and_vrischika():
    """Mars rules both Mesha (id=1) and Vrischika (id=8)."""
    mars_signs = [r for r in RASHIS if r["ruler"] == "Mars"]
    assert len(mars_signs) == 2
    ids = {r["id"] for r in mars_signs}
    assert ids == {1, 8}


def test_ruler_jupiter_dhanus_and_meena():
    """Jupiter rules both Dhanus (id=9) and Meena (id=12)."""
    jup_signs = [r for r in RASHIS if r["ruler"] == "Jupiter"]
    assert len(jup_signs) == 2
    ids = {r["id"] for r in jup_signs}
    assert ids == {9, 12}


# ---------------------------------------------------------------------------
# rashi_for_longitude — boundary and point tests
# ---------------------------------------------------------------------------

def test_mesha_at_zero():
    """0° → Mesha (id=1)."""
    result = rashi_for_longitude(0.0)
    assert result["id"] == 1
    assert result["name"] == "Mesha"
    assert result["degrees_into"] == 0.0


def test_boundary_at_30_is_vrishabha():
    """30° exactly → Vrishabha (id=2)."""
    result = rashi_for_longitude(30.0)
    assert result["id"] == 2
    assert result["name"] == "Vrishabha"
    assert result["degrees_into"] == 0.0


def test_meena_near_360():
    """359.9° → Meena (id=12)."""
    result = rashi_for_longitude(359.9)
    assert result["id"] == 12
    assert result["name"] == "Meena"


def test_360_wraps_to_mesha():
    """360° wraps to Mesha (id=1)."""
    result = rashi_for_longitude(360.0)
    assert result["id"] == 1
    assert result["name"] == "Mesha"
    assert result["degrees_into"] == 0.0


def test_negative_longitude_wraps():
    """-30° is equivalent to 330° → Meena (id=12), since 330° = start of Meena."""
    result = rashi_for_longitude(-30.0)
    assert result["id"] == 12
    assert result["name"] == "Meena"
    assert result["degrees_into"] == 0.0


def test_negative_large_longitude_wraps():
    """-360° wraps to Mesha (id=1)."""
    result = rashi_for_longitude(-360.0)
    assert result["id"] == 1


def test_degrees_into_mid_sign():
    """135° is 15° into Simha (start=120°) → degrees_into=15.0."""
    result = rashi_for_longitude(135.0)
    assert result["id"] == 5
    assert result["name"] == "Simha"
    assert result["degrees_into"] == pytest.approx(15.0, abs=1e-6)


def test_degrees_into_precision():
    """Non-round longitude: 45.123456° → Vrishabha, degrees_into=15.123456°."""
    result = rashi_for_longitude(45.123456)
    assert result["id"] == 2
    assert result["degrees_into"] == pytest.approx(15.123456, abs=1e-5)


def test_degrees_into_never_negative():
    """degrees_into must always be >= 0 for any input."""
    for lon in [-1e-10, 0.0, 29.9999999, 30.0, 359.9999999, 360.0, 720.0]:
        result = rashi_for_longitude(lon)
        assert result["degrees_into"] >= 0.0, f"degrees_into negative for lon={lon}"


def test_all_12_signs_reachable():
    """Every rashi id 1–12 must be reachable by stepping 30° at a time."""
    for i in range(12):
        lon = i * 30.0 + 15.0  # midpoint of each sign
        result = rashi_for_longitude(lon)
        assert result["id"] == i + 1


def test_large_longitude_wraps():
    """720° + 15° (= 15° after 2 full circles) → Mesha."""
    result = rashi_for_longitude(735.0)
    assert result["id"] == 1
    assert result["degrees_into"] == pytest.approx(15.0, abs=1e-6)


# ---------------------------------------------------------------------------
# rashi_for_all_ayanamshas
# ---------------------------------------------------------------------------

def test_rashi_for_all_ayanamshas_key_count():
    """Output must have the same number of keys as input."""
    ayanamshas = {"lahiri": 23.85, "raman": 22.46, "kp": 23.86}
    tropical = 100.0
    result = rashi_for_all_ayanamshas(tropical, ayanamshas)
    assert len(result) == 3
    assert set(result.keys()) == {"lahiri", "raman", "kp"}


def test_rashi_for_all_ayanamshas_correct_rashi_per_offset():
    """Each ayanamsha produces the correct rashi based on tropical − offset."""
    # tropical=50.0, offset=20.0 → sidereal=30.0 → Vrishabha (id=2)
    # tropical=50.0, offset=5.0  → sidereal=45.0 → Vrishabha (id=2, mid-sign)
    # tropical=50.0, offset=50.0 → sidereal=0.0  → Mesha (id=1)
    ayanamshas = {"a": 20.0, "b": 5.0, "c": 50.0}
    result = rashi_for_all_ayanamshas(50.0, ayanamshas)
    assert result["a"]["id"] == 2   # sidereal=30.0
    assert result["b"]["id"] == 2   # sidereal=45.0
    assert result["c"]["id"] == 1   # sidereal=0.0


def test_rashi_for_all_ayanamshas_empty_input():
    """Empty ayanamsha dict returns empty result."""
    result = rashi_for_all_ayanamshas(100.0, {})
    assert result == {}


def test_rashi_for_all_ayanamshas_integer_keys():
    """Numeric (int) ayanamsha ids are preserved as keys."""
    ayanamshas = {1: 23.85, 2: 22.46}
    result = rashi_for_all_ayanamshas(100.0, ayanamshas)
    assert 1 in result
    assert 2 in result
