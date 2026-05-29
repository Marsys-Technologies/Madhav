"""
test_ritual_nadi.py — Tests for G39 Vedic Ritual Library + G44 Nadi Astrology Tables
MARSYS-JIS Build Orchestrator session A-16.

Minimum 25 assertions covering:
- VEDIC_RITUAL_LIBRARY structure and content
- get_ritual(), list_occasions(), get_ritual_by_type()
- NADI_NAKSHATRA_RISHI mapping and rishi cycling
- KP_NADI_SUBLORDS structure and known values
- get_nadi_rishi(), get_kp_sublord()
- BHRIGU_NADI_YOGAS completeness
- list_bhrigu_yogas()
- Error handling
"""

import pytest
from pipeline.ritual_nadi import (
    VEDIC_RITUAL_LIBRARY,
    NADI_NAKSHATRA_RISHI,
    KP_NADI_SUBLORDS,
    BHRIGU_NADI_YOGAS,
    NADI_AMSA_TABLE,
    RISHI_NAMES,
    get_ritual,
    list_occasions,
    get_ritual_by_type,
    get_nadi_rishi,
    get_kp_sublord,
    list_bhrigu_yogas,
)

# ---------------------------------------------------------------------------
# G39 — VEDIC_RITUAL_LIBRARY tests
# ---------------------------------------------------------------------------

class TestVedicRitualLibrary:

    def test_library_has_at_least_10_occasions(self):
        """Assertion 1: VEDIC_RITUAL_LIBRARY has at minimum 10 occasions."""
        assert len(VEDIC_RITUAL_LIBRARY) >= 10

    def test_all_occasions_have_ritual_name(self):
        """Assertion 2: Every occasion has a non-empty ritual_name."""
        for key, data in VEDIC_RITUAL_LIBRARY.items():
            assert "ritual_name" in data, f"{key} missing ritual_name"
            assert data["ritual_name"], f"{key} has empty ritual_name"

    def test_all_occasions_have_occasion_type(self):
        """Assertion 3: Every occasion has a valid occasion_type."""
        valid_types = {"samskara", "deity", "ancestor", "seasonal"}
        for key, data in VEDIC_RITUAL_LIBRARY.items():
            assert "occasion_type" in data, f"{key} missing occasion_type"
            assert data["occasion_type"] in valid_types, (
                f"{key} has invalid occasion_type: {data['occasion_type']}"
            )

    def test_all_occasions_have_ritual_sequence(self):
        """Assertion 4: Every occasion has a non-empty ritual_sequence list."""
        for key, data in VEDIC_RITUAL_LIBRARY.items():
            assert "ritual_sequence" in data, f"{key} missing ritual_sequence"
            assert isinstance(data["ritual_sequence"], list), f"{key} ritual_sequence not a list"
            assert len(data["ritual_sequence"]) >= 1, f"{key} has empty ritual_sequence"

    def test_all_occasions_have_classical_citation(self):
        """Assertion 5: Every occasion has a classical_citation."""
        for key, data in VEDIC_RITUAL_LIBRARY.items():
            assert "classical_citation" in data, f"{key} missing classical_citation"
            assert data["classical_citation"], f"{key} has empty classical_citation"

    def test_get_ritual_marriage_returns_correct_data(self):
        """Assertion 6: get_ritual('marriage') returns non-empty dict with required keys."""
        result = get_ritual("marriage")
        assert result, "get_ritual('marriage') returned empty dict"
        assert "ritual_name" in result
        assert "ritual_sequence" in result
        assert "mantras" in result
        assert "classical_citation" in result

    def test_get_ritual_birth_has_sankalpa(self):
        """Assertion 7: get_ritual('birth') includes sankalpa text."""
        result = get_ritual("birth")
        assert "sankalpa" in result
        assert len(result["sankalpa"]) > 10

    def test_get_ritual_case_insensitive(self):
        """Assertion 8: get_ritual() is case-insensitive."""
        assert get_ritual("BIRTH") == get_ritual("birth")
        assert get_ritual("Marriage") == get_ritual("marriage")

    def test_get_ritual_unknown_returns_empty_dict(self):
        """Assertion 9: get_ritual() returns empty dict for unknown occasions."""
        result = get_ritual("unknown_occasion_xyz")
        assert result == {}

    def test_list_occasions_returns_list_of_strings(self):
        """Assertion 10: list_occasions() returns a non-empty list of strings."""
        occasions = list_occasions()
        assert isinstance(occasions, list)
        assert len(occasions) >= 10
        for occ in occasions:
            assert isinstance(occ, str)

    def test_list_occasions_contains_core_samskaras(self):
        """Assertion 11: list_occasions() contains the core life-cycle samskaras."""
        occasions = list_occasions()
        for expected in ["birth", "naming", "marriage", "death_rites"]:
            assert expected in occasions, f"'{expected}' missing from list_occasions()"

    def test_get_ritual_by_type_samskara(self):
        """Assertion 12: get_ritual_by_type('samskara') returns correct entries."""
        samskaras = get_ritual_by_type("samskara")
        assert isinstance(samskaras, list)
        assert len(samskaras) >= 3  # birth, naming, annaprashan, thread_ceremony at minimum
        for item in samskaras:
            assert item["occasion_type"] == "samskara"
            assert "occasion" in item  # key is injected

    def test_get_ritual_by_type_ancestor(self):
        """Assertion 13: get_ritual_by_type('ancestor') returns ancestor rituals."""
        ancestors = get_ritual_by_type("ancestor")
        assert len(ancestors) >= 2  # shradh and death_rites
        occasion_keys = [a["occasion"] for a in ancestors]
        assert "death_rites" in occasion_keys
        assert "shradh" in occasion_keys

    def test_get_ritual_by_type_deity(self):
        """Assertion 14: get_ritual_by_type('deity') returns deity puja entries."""
        deity_rituals = get_ritual_by_type("deity")
        assert len(deity_rituals) >= 2  # navratri, satyanarayan_puja
        for item in deity_rituals:
            assert item["occasion_type"] == "deity"

    def test_get_ritual_by_type_unknown_returns_empty(self):
        """Assertion 15: get_ritual_by_type() with unknown type returns empty list."""
        result = get_ritual_by_type("nonexistent_type")
        assert result == []

    def test_marriage_ritual_sequence_has_saptapadi(self):
        """Assertion 16: Marriage ritual_sequence mentions Saptapadi."""
        marriage = get_ritual("marriage")
        seq_text = " ".join(marriage["ritual_sequence"]).lower()
        assert "saptapadi" in seq_text

    def test_navratri_has_10_day_sequence(self):
        """Assertion 17: Navratri ritual_sequence covers 10 steps (9 nights + Vijaya Dashami)."""
        navratri = get_ritual("navratri")
        assert len(navratri["ritual_sequence"]) >= 10


# ---------------------------------------------------------------------------
# G44 — NADI_LOOKUP_TABLES tests
# ---------------------------------------------------------------------------

class TestNadiNakshatraRishi:

    def test_nadi_nakshatra_rishi_has_27_entries(self):
        """Assertion 18: NADI_NAKSHATRA_RISHI has exactly 27 entries."""
        assert len(NADI_NAKSHATRA_RISHI) == 27

    def test_get_nadi_rishi_ashwini_is_vasishtha(self):
        """Assertion 19: get_nadi_rishi(1) == 'Vasishtha' (Ashwini)."""
        assert get_nadi_rishi(1) == "Vasishtha"

    def test_get_nadi_rishi_cycle_repeats_at_10(self):
        """Assertion 20: get_nadi_rishi(10) == 'Vasishtha' — cycle repeats every 9."""
        assert get_nadi_rishi(10) == "Vasishtha"

    def test_get_nadi_rishi_cycle_repeats_at_19(self):
        """Assertion 21: get_nadi_rishi(19) == 'Vasishtha' — third cycle."""
        assert get_nadi_rishi(19) == "Vasishtha"

    def test_get_nadi_rishi_bharani_is_atri(self):
        """Assertion 22: Nakshatra 2 (Bharani) maps to Atri."""
        assert get_nadi_rishi(2) == "Atri"
        assert get_nadi_rishi(11) == "Atri"  # second cycle
        assert get_nadi_rishi(20) == "Atri"  # third cycle

    def test_get_nadi_rishi_all_27_return_strings(self):
        """Assertion 23: get_nadi_rishi() returns a non-empty string for all 27 nakshatras."""
        for n in range(1, 28):
            rishi = get_nadi_rishi(n)
            assert isinstance(rishi, str)
            assert len(rishi) > 0

    def test_get_nadi_rishi_out_of_range_raises(self):
        """Assertion 24: get_nadi_rishi() raises ValueError for out-of-range inputs."""
        with pytest.raises(ValueError):
            get_nadi_rishi(0)
        with pytest.raises(ValueError):
            get_nadi_rishi(28)

    def test_nadi_nakshatra_rishi_values_are_valid_rishis(self):
        """Assertion 25: All NADI_NAKSHATRA_RISHI values are from the 9 primary rishis."""
        nine_primary = {
            "Vasishtha", "Atri", "Bharadwaja", "Vishwamitra", "Gautama",
            "Jamadagni", "Kashyapa", "Agastya", "Kaundinya",
        }
        for nak, rishi in NADI_NAKSHATRA_RISHI.items():
            assert rishi in nine_primary, f"Nakshatra {nak} has unexpected rishi: {rishi}"


class TestKPNadiSublords:

    def test_kp_sublords_has_27_entries(self):
        """Assertion 26: KP_NADI_SUBLORDS has exactly 27 nakshatra entries."""
        assert len(KP_NADI_SUBLORDS) == 27

    def test_each_nakshatra_has_9_sublords(self):
        """Assertion 27: Each nakshatra entry has exactly 9 sub-positions."""
        for nakshatra in range(1, 28):
            assert nakshatra in KP_NADI_SUBLORDS
            assert len(KP_NADI_SUBLORDS[nakshatra]) == 9

    def test_ashwini_starts_with_ketu(self):
        """Assertion 28: get_kp_sublord(1, 1) == 'ketu' (Ashwini starts with Ketu)."""
        assert get_kp_sublord(1, 1) == "ketu"

    def test_bharani_starts_with_venus(self):
        """Assertion 29: get_kp_sublord(2, 1) == 'venus' (Bharani starts with Venus)."""
        assert get_kp_sublord(2, 1) == "venus"

    def test_krittika_starts_with_sun(self):
        """Assertion 30: get_kp_sublord(3, 1) == 'sun' (Krittika starts with Sun)."""
        assert get_kp_sublord(3, 1) == "sun"

    def test_rohini_starts_with_moon(self):
        """Assertion 31: get_kp_sublord(4, 1) == 'moon' (Rohini starts with Moon)."""
        assert get_kp_sublord(4, 1) == "moon"

    def test_mrigashira_starts_with_mars(self):
        """Assertion 32: get_kp_sublord(5, 1) == 'mars' (Mrigashira starts with Mars)."""
        assert get_kp_sublord(5, 1) == "mars"

    def test_ardra_starts_with_rahu(self):
        """Assertion 33: get_kp_sublord(6, 1) == 'rahu' (Ardra starts with Rahu)."""
        assert get_kp_sublord(6, 1) == "rahu"

    def test_punarvasu_starts_with_jupiter(self):
        """Assertion 34: get_kp_sublord(7, 1) == 'jupiter' (Punarvasu starts with Jupiter)."""
        assert get_kp_sublord(7, 1) == "jupiter"

    def test_pushya_starts_with_saturn(self):
        """Assertion 35: get_kp_sublord(8, 1) == 'saturn' (Pushya starts with Saturn)."""
        assert get_kp_sublord(8, 1) == "saturn"

    def test_ashlesha_starts_with_mercury(self):
        """Assertion 36: get_kp_sublord(9, 1) == 'mercury' (Ashlesha starts with Mercury)."""
        assert get_kp_sublord(9, 1) == "mercury"

    def test_sublord_sequence_is_vimshottari(self):
        """Assertion 37: Second position of Ashwini sub = 'venus' (next in Vimshottari after Ketu)."""
        # Ashwini sub1=ketu, sub2=venus (next in sequence)
        assert get_kp_sublord(1, 2) == "venus"

    def test_sublord_wraps_around_at_position_9(self):
        """Assertion 38: Position 9 of Ashwini = 'mercury' (last in Vimshottari before wrapping)."""
        # Full Vimshottari: ketu,venus,sun,moon,mars,rahu,jupiter,saturn,mercury
        assert get_kp_sublord(1, 9) == "mercury"

    def test_get_kp_sublord_all_values_are_valid_planets(self):
        """Assertion 39: All KP sublord values are valid planet names."""
        valid_planets = {"ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury"}
        for nak in range(1, 28):
            for pos in range(1, 10):
                planet = get_kp_sublord(nak, pos)
                assert planet in valid_planets, f"Nak {nak} pos {pos} has invalid planet: {planet}"

    def test_get_kp_sublord_out_of_range_raises(self):
        """Assertion 40: get_kp_sublord() raises ValueError for out-of-range inputs."""
        with pytest.raises(ValueError):
            get_kp_sublord(0, 1)
        with pytest.raises(ValueError):
            get_kp_sublord(1, 0)
        with pytest.raises(ValueError):
            get_kp_sublord(28, 1)
        with pytest.raises(ValueError):
            get_kp_sublord(1, 10)


class TestBhriguNadiYogas:

    def test_bhrigu_yogas_has_at_least_10_rules(self):
        """Assertion 41: BHRIGU_NADI_YOGAS has at minimum 10 yoga rules."""
        assert len(BHRIGU_NADI_YOGAS) >= 10

    def test_each_yoga_has_required_keys(self):
        """Assertion 42: Each Bhrigu yoga dict has yoga_name, prediction, and source."""
        for i, yoga in enumerate(BHRIGU_NADI_YOGAS):
            assert "yoga_name" in yoga, f"Yoga {i} missing yoga_name"
            assert "prediction" in yoga, f"Yoga {i} missing prediction"
            assert "source" in yoga, f"Yoga {i} missing source"

    def test_each_yoga_source_is_bhrigu_nadi(self):
        """Assertion 43: Each Bhrigu yoga has source = 'Bhrigu Nadi'."""
        for yoga in BHRIGU_NADI_YOGAS:
            assert yoga["source"] == "Bhrigu Nadi"

    def test_list_bhrigu_yogas_returns_same_as_constant(self):
        """Assertion 44: list_bhrigu_yogas() returns the BHRIGU_NADI_YOGAS list."""
        assert list_bhrigu_yogas() is BHRIGU_NADI_YOGAS

    def test_bhrigu_yogas_prediction_fields_non_empty(self):
        """Assertion 45: Every yoga has a non-empty prediction string."""
        for yoga in BHRIGU_NADI_YOGAS:
            assert yoga["prediction"], f"Yoga '{yoga.get('yoga_name')}' has empty prediction"

    def test_sun_saturn_yoga_present(self):
        """Assertion 46: Sun-Saturn yoga (father-son conflict) is in the Bhrigu yoga list."""
        yoga_names = [y["yoga_name"].lower() for y in BHRIGU_NADI_YOGAS]
        assert any("sun" in n and "saturn" in n for n in yoga_names), (
            "Sun-Saturn yoga missing from Bhrigu yoga list"
        )

    def test_moon_venus_yoga_present(self):
        """Assertion 47: Moon-Venus yoga (artistic talents) is in the Bhrigu yoga list."""
        yoga_names = [y["yoga_name"].lower() for y in BHRIGU_NADI_YOGAS]
        assert any("moon" in n and "venus" in n for n in yoga_names)


class TestNadiAmsaTable:

    def test_amsa_table_has_27_entries(self):
        """Assertion 48: NADI_AMSA_TABLE has 27 nakshatra entries."""
        assert len(NADI_AMSA_TABLE) == 27

    def test_amsa_table_ashwini_rishi_is_vasishtha(self):
        """Assertion 49: NADI_AMSA_TABLE Ashwini primary_rishi = Vasishtha."""
        assert NADI_AMSA_TABLE["Ashwini"]["primary_rishi"] == "Vasishtha"

    def test_amsa_table_all_have_nadi_classification(self):
        """Assertion 50: All amsa entries have nadi_classification (adi/madhya/antya)."""
        valid_classes = {"adi", "madhya", "antya"}
        for name, data in NADI_AMSA_TABLE.items():
            assert data["nadi_classification"] in valid_classes, (
                f"{name} has invalid nadi_classification: {data['nadi_classification']}"
            )
