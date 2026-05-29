"""
test_graha_utils.py — Unit tests for graha_utils.py planetary constants module.

No DB interaction, no swisseph calls — pure data validation.
"""

import pytest

from pipeline.graha_utils import (
    GRAHAS,
    REQUIRED_KEYS,
    get_graha,
    grahas_ruling_rashi,
    is_debilitated,
    is_exalted,
)

# ---------------------------------------------------------------------------
# 1. Completeness: all 9 grahas present
# ---------------------------------------------------------------------------

EXPECTED_GRAHAS = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}


def test_all_nine_grahas_present():
    assert set(GRAHAS.keys()) == EXPECTED_GRAHAS


def test_graha_count_is_nine():
    assert len(GRAHAS) == 9


# ---------------------------------------------------------------------------
# 2. Schema: required keys on every entry
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("graha_id", list(EXPECTED_GRAHAS))
def test_required_keys_present(graha_id):
    g = GRAHAS[graha_id]
    missing = REQUIRED_KEYS - set(g.keys())
    assert not missing, f"{graha_id} missing keys: {missing}"


@pytest.mark.parametrize("graha_id", list(EXPECTED_GRAHAS))
def test_id_field_matches_dict_key(graha_id):
    assert GRAHAS[graha_id]["id"] == graha_id


@pytest.mark.parametrize("graha_id", list(EXPECTED_GRAHAS))
def test_ruler_of_is_list(graha_id):
    assert isinstance(GRAHAS[graha_id]["ruler_of"], list)


# ---------------------------------------------------------------------------
# 3. Sun
# ---------------------------------------------------------------------------

def test_sun_exalted_in_mesha():
    assert GRAHAS["sun"]["exalted_in"] == "mesha"


def test_sun_exalted_deg_10():
    assert GRAHAS["sun"]["exalted_deg"] == 10.0


def test_sun_debilitated_in_tula():
    assert GRAHAS["sun"]["debilitated_in"] == "tula"


def test_sun_rules_simha():
    assert "simha" in GRAHAS["sun"]["ruler_of"]


def test_sun_nature_malefic():
    assert GRAHAS["sun"]["nature"] == "malefic"


def test_sun_moolatrikona_simha():
    assert GRAHAS["sun"]["moolatrikona"] == "simha"


# ---------------------------------------------------------------------------
# 4. Moon
# ---------------------------------------------------------------------------

def test_moon_exalted_in_vrishabha():
    assert GRAHAS["moon"]["exalted_in"] == "vrishabha"


def test_moon_exalted_deg_3():
    assert GRAHAS["moon"]["exalted_deg"] == 3.0


def test_moon_debilitated_in_vrischika():
    assert GRAHAS["moon"]["debilitated_in"] == "vrischika"


def test_moon_nature_benefic():
    assert GRAHAS["moon"]["nature"] == "benefic"


# ---------------------------------------------------------------------------
# 5. Mars
# ---------------------------------------------------------------------------

def test_mars_rules_mesha():
    assert "mesha" in GRAHAS["mars"]["ruler_of"]


def test_mars_rules_vrischika():
    assert "vrischika" in GRAHAS["mars"]["ruler_of"]


def test_mars_rules_exactly_two_rashis():
    assert len(GRAHAS["mars"]["ruler_of"]) == 2


def test_mars_exalted_in_makara():
    assert GRAHAS["mars"]["exalted_in"] == "makara"


def test_mars_exalted_deg_28():
    assert GRAHAS["mars"]["exalted_deg"] == 28.0


# ---------------------------------------------------------------------------
# 6. Mercury
# ---------------------------------------------------------------------------

def test_mercury_nature_neutral():
    assert GRAHAS["mercury"]["nature"] == "neutral"


def test_mercury_gender_neuter():
    assert GRAHAS["mercury"]["gender"] == "neuter"


def test_mercury_exalted_in_kanya():
    assert GRAHAS["mercury"]["exalted_in"] == "kanya"


def test_mercury_debilitated_in_meena():
    assert GRAHAS["mercury"]["debilitated_in"] == "meena"


# ---------------------------------------------------------------------------
# 7. Jupiter
# ---------------------------------------------------------------------------

def test_jupiter_nature_benefic():
    assert GRAHAS["jupiter"]["nature"] == "benefic"


def test_jupiter_exalted_in_karka():
    assert GRAHAS["jupiter"]["exalted_in"] == "karka"


def test_jupiter_exalted_deg_5():
    assert GRAHAS["jupiter"]["exalted_deg"] == 5.0


def test_jupiter_debilitated_in_makara():
    assert GRAHAS["jupiter"]["debilitated_in"] == "makara"


def test_jupiter_rules_dhanus():
    assert "dhanus" in GRAHAS["jupiter"]["ruler_of"]


def test_jupiter_rules_meena():
    assert "meena" in GRAHAS["jupiter"]["ruler_of"]


# ---------------------------------------------------------------------------
# 8. Venus
# ---------------------------------------------------------------------------

def test_venus_exalted_in_meena():
    assert GRAHAS["venus"]["exalted_in"] == "meena"


def test_venus_exalted_deg_27():
    assert GRAHAS["venus"]["exalted_deg"] == 27.0


def test_venus_debilitated_in_kanya():
    assert GRAHAS["venus"]["debilitated_in"] == "kanya"


def test_venus_nature_benefic():
    assert GRAHAS["venus"]["nature"] == "benefic"


# ---------------------------------------------------------------------------
# 9. Saturn
# ---------------------------------------------------------------------------

def test_saturn_exalted_in_tula():
    assert GRAHAS["saturn"]["exalted_in"] == "tula"


def test_saturn_exalted_deg_20():
    assert GRAHAS["saturn"]["exalted_deg"] == 20.0


def test_saturn_debilitated_in_mesha():
    assert GRAHAS["saturn"]["debilitated_in"] == "mesha"


def test_saturn_rules_makara():
    assert "makara" in GRAHAS["saturn"]["ruler_of"]


def test_saturn_rules_kumbha():
    assert "kumbha" in GRAHAS["saturn"]["ruler_of"]


def test_saturn_nature_malefic():
    assert GRAHAS["saturn"]["nature"] == "malefic"


# ---------------------------------------------------------------------------
# 10. Rahu / Ketu
# ---------------------------------------------------------------------------

def test_rahu_nature_malefic():
    assert GRAHAS["rahu"]["nature"] == "malefic"


def test_ketu_nature_malefic():
    assert GRAHAS["ketu"]["nature"] == "malefic"


def test_rahu_ruler_of_empty():
    assert GRAHAS["rahu"]["ruler_of"] == []


def test_ketu_ruler_of_empty():
    assert GRAHAS["ketu"]["ruler_of"] == []


def test_rahu_moolatrikona_none():
    assert GRAHAS["rahu"]["moolatrikona"] is None


def test_ketu_moolatrikona_none():
    assert GRAHAS["ketu"]["moolatrikona"] is None


def test_rahu_exalted_in_mithuna():
    assert GRAHAS["rahu"]["exalted_in"] == "mithuna"


def test_ketu_exalted_in_dhanus():
    assert GRAHAS["ketu"]["exalted_in"] == "dhanus"


def test_rahu_debilitated_in_dhanus():
    assert GRAHAS["rahu"]["debilitated_in"] == "dhanus"


def test_ketu_debilitated_in_mithuna():
    assert GRAHAS["ketu"]["debilitated_in"] == "mithuna"


def test_rahu_ketu_share_swisseph_id_11():
    assert GRAHAS["rahu"]["swisseph_id"] == 11
    assert GRAHAS["ketu"]["swisseph_id"] == 11


def test_rahu_tattva_none():
    assert GRAHAS["rahu"]["tattva"] is None


def test_ketu_tattva_none():
    assert GRAHAS["ketu"]["tattva"] is None


# ---------------------------------------------------------------------------
# 11. get_graha() helper
# ---------------------------------------------------------------------------

def test_get_graha_returns_correct_dict():
    g = get_graha("sun")
    assert g["name"] == "Surya"
    assert g["id"] == "sun"


def test_get_graha_key_error_on_unknown():
    with pytest.raises(KeyError):
        get_graha("pluto")


def test_get_graha_key_error_on_empty_string():
    with pytest.raises(KeyError):
        get_graha("")


# ---------------------------------------------------------------------------
# 12. grahas_ruling_rashi()
# ---------------------------------------------------------------------------

def test_grahas_ruling_simha_is_sun():
    result = grahas_ruling_rashi("simha")
    assert result == ["sun"]


def test_grahas_ruling_mesha_is_mars():
    result = grahas_ruling_rashi("mesha")
    assert result == ["mars"]


def test_grahas_ruling_karka_is_moon():
    result = grahas_ruling_rashi("karka")
    assert result == ["moon"]


def test_grahas_ruling_dhanus_is_jupiter():
    result = grahas_ruling_rashi("dhanus")
    assert result == ["jupiter"]


def test_grahas_ruling_tula_is_venus():
    result = grahas_ruling_rashi("tula")
    assert result == ["venus"]


def test_grahas_ruling_kanya_is_mercury():
    result = grahas_ruling_rashi("kanya")
    assert result == ["mercury"]


def test_grahas_ruling_makara_is_saturn():
    result = grahas_ruling_rashi("makara")
    assert result == ["saturn"]


def test_grahas_ruling_unknown_rashi_is_empty():
    result = grahas_ruling_rashi("nonexistent")
    assert result == []


# ---------------------------------------------------------------------------
# 13. is_exalted() / is_debilitated() spot checks
# ---------------------------------------------------------------------------

def test_is_exalted_sun_in_mesha():
    assert is_exalted("sun", "mesha") is True


def test_is_exalted_sun_not_in_tula():
    assert is_exalted("sun", "tula") is False


def test_is_debilitated_sun_in_tula():
    assert is_debilitated("sun", "tula") is True


def test_is_debilitated_sun_not_in_mesha():
    assert is_debilitated("sun", "mesha") is False


def test_is_exalted_moon_in_vrishabha():
    assert is_exalted("moon", "vrishabha") is True


def test_is_debilitated_moon_in_vrischika():
    assert is_debilitated("moon", "vrischika") is True


def test_is_exalted_jupiter_in_karka():
    assert is_exalted("jupiter", "karka") is True


def test_is_debilitated_jupiter_in_makara():
    assert is_debilitated("jupiter", "makara") is True


def test_is_exalted_saturn_in_tula():
    assert is_exalted("saturn", "tula") is True


def test_is_debilitated_saturn_in_mesha():
    assert is_debilitated("saturn", "mesha") is True


def test_is_exalted_mars_in_makara():
    assert is_exalted("mars", "makara") is True


def test_is_debilitated_mars_in_karka():
    assert is_debilitated("mars", "karka") is True


def test_is_exalted_venus_in_meena():
    assert is_exalted("venus", "meena") is True


def test_is_exalted_mercury_in_kanya():
    assert is_exalted("mercury", "kanya") is True


# ---------------------------------------------------------------------------
# 14. Index / swisseph_id uniqueness checks
# ---------------------------------------------------------------------------

def test_all_indices_unique():
    indices = [g["index"] for g in GRAHAS.values()]
    assert len(indices) == len(set(indices))


def test_indices_range_0_to_8():
    indices = sorted(g["index"] for g in GRAHAS.values())
    assert indices == list(range(9))


def test_swisseph_ids_planets_unique():
    """The 7 classical planets (not nodes) should have distinct swisseph_ids."""
    classical = {gid: g for gid, g in GRAHAS.items() if gid not in ("rahu", "ketu")}
    ids = [g["swisseph_id"] for g in classical.values()]
    assert len(ids) == len(set(ids))
