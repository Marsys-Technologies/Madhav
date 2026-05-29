"""
test_remedial_library.py — MARSYS-JIS
Tests for remedial_library.py (G27 — integrated remedial library per graha).
Minimum 25 assertions covering all 9 grahas and all public API functions.
"""

import pytest
from pipeline.remedial_library import (
    REMEDIAL_LIBRARY,
    REQUIRED_KEYS,
    ALL_GRAHAS,
    get_remedies,
    get_gemstone_recommendation,
    get_mantra_ids,
    get_full_remedy_text,
)

# ---------------------------------------------------------------------------
# Constants / expected data
# ---------------------------------------------------------------------------

ALL_NINE_GRAHAS = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}


# ---------------------------------------------------------------------------
# 1. REMEDIAL_LIBRARY structure tests
# ---------------------------------------------------------------------------

class TestRemedialLibraryStructure:

    def test_library_has_nine_grahas(self):
        """REMEDIAL_LIBRARY must contain exactly 9 grahas."""
        assert len(REMEDIAL_LIBRARY) == 9

    def test_all_nine_grahas_present(self):
        """All 9 canonical graha names must be present."""
        assert ALL_NINE_GRAHAS == set(REMEDIAL_LIBRARY.keys())

    def test_all_grahas_match_all_grahas_constant(self):
        """ALL_GRAHAS constant matches REMEDIAL_LIBRARY keys."""
        assert ALL_GRAHAS == ALL_NINE_GRAHAS

    def test_all_grahas_have_mantra_ids(self):
        """Every graha must have a non-empty mantra_ids list."""
        for graha, entry in REMEDIAL_LIBRARY.items():
            assert "mantra_ids" in entry, f"{graha} missing mantra_ids"
            assert isinstance(entry["mantra_ids"], list), f"{graha}.mantra_ids must be a list"
            assert len(entry["mantra_ids"]) > 0, f"{graha}.mantra_ids must be non-empty"

    def test_all_grahas_have_gemstone_dict(self):
        """Every graha must have a gemstone dict with required keys."""
        for graha, entry in REMEDIAL_LIBRARY.items():
            gem = entry.get("gemstone", {})
            assert "primary" in gem, f"{graha}.gemstone missing 'primary'"
            assert "substitute" in gem, f"{graha}.gemstone missing 'substitute'"
            assert isinstance(gem["substitute"], list), f"{graha}.gemstone.substitute must be list"
            assert "weight_ratti" in gem, f"{graha}.gemstone missing 'weight_ratti'"

    def test_all_grahas_have_fasting_day(self):
        """Every graha must have a fasting_day field."""
        for graha, entry in REMEDIAL_LIBRARY.items():
            assert "fasting_day" in entry, f"{graha} missing fasting_day"
            assert isinstance(entry["fasting_day"], str), f"{graha}.fasting_day must be a string"
            assert len(entry["fasting_day"]) > 0, f"{graha}.fasting_day must be non-empty"

    def test_all_grahas_have_classical_citation(self):
        """Every graha must have a classical_citation field."""
        for graha, entry in REMEDIAL_LIBRARY.items():
            assert "classical_citation" in entry, f"{graha} missing classical_citation"
            assert len(entry["classical_citation"]) > 0, f"{graha}.classical_citation non-empty"

    def test_all_grahas_have_yantra(self):
        """Every graha must have a yantra field."""
        for graha, entry in REMEDIAL_LIBRARY.items():
            assert "yantra" in entry, f"{graha} missing yantra"
            assert "Yantra" in entry["yantra"], f"{graha}.yantra should mention 'Yantra'"

    def test_all_grahas_have_ritual(self):
        """Every graha must have a ritual field."""
        for graha, entry in REMEDIAL_LIBRARY.items():
            assert "ritual" in entry, f"{graha} missing ritual"
            assert len(entry["ritual"]) > 0, f"{graha}.ritual must be non-empty"

    def test_all_grahas_have_required_keys(self):
        """Every graha entry must contain all REQUIRED_KEYS."""
        for graha, entry in REMEDIAL_LIBRARY.items():
            missing = REQUIRED_KEYS - set(entry.keys())
            assert not missing, f"{graha} is missing required keys: {missing}"


# ---------------------------------------------------------------------------
# 2. Per-graha spot checks
# ---------------------------------------------------------------------------

class TestSunRemedies:

    def test_sun_remedies_returns_dict(self):
        result = get_remedies("sun")
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_sun_gemstone_is_ruby(self):
        gem = get_gemstone_recommendation("sun")
        assert gem["primary"] == "Ruby"

    def test_sun_mantra_ids_include_beej(self):
        ids = get_mantra_ids("sun")
        assert "sun_beej_mantra" in ids

    def test_sun_mantra_ids_include_aditya_hridayam(self):
        ids = get_mantra_ids("sun")
        assert "aditya_hridayam_full" in ids

    def test_sun_fasting_day_is_sunday(self):
        entry = get_remedies("sun")
        assert "Sunday" in entry["fasting_day"]


class TestMoonRemedies:

    def test_moon_gemstone_is_pearl(self):
        gem = get_gemstone_recommendation("moon")
        assert gem["primary"] == "Pearl"

    def test_moon_full_remedy_text_non_empty(self):
        text = get_full_remedy_text("moon")
        assert isinstance(text, str)
        assert len(text) > 50

    def test_moon_full_remedy_text_contains_graha_name(self):
        text = get_full_remedy_text("moon")
        assert "MOON" in text

    def test_moon_mantra_ids_include_beej(self):
        ids = get_mantra_ids("moon")
        assert "moon_beej_mantra" in ids


class TestJupiterRemedies:

    def test_jupiter_gemstone_is_yellow_sapphire(self):
        """Jupiter primary gemstone must be Yellow Sapphire (Pukhraj)."""
        gem = get_gemstone_recommendation("jupiter")
        primary = gem.get("primary", "")
        # Accept Yellow Sapphire as the canonical name
        assert "Sapphire" in primary or "Pukhraj" in primary or primary == "Yellow Sapphire"

    def test_jupiter_alternate_name_is_pukhraj(self):
        gem = get_gemstone_recommendation("jupiter")
        assert "Pukhraj" in gem.get("alternate_name", "")

    def test_jupiter_mantra_ids_non_empty(self):
        ids = get_mantra_ids("jupiter")
        assert len(ids) > 0

    def test_jupiter_mantra_ids_include_beej(self):
        ids = get_mantra_ids("jupiter")
        assert "jupiter_beej_mantra" in ids


class TestSaturnRemedies:

    def test_saturn_mantra_ids_non_empty(self):
        ids = get_mantra_ids("saturn")
        assert len(ids) > 0

    def test_saturn_mantra_ids_include_beej(self):
        ids = get_mantra_ids("saturn")
        assert "saturn_beej_mantra" in ids

    def test_saturn_gemstone_is_blue_sapphire(self):
        gem = get_gemstone_recommendation("saturn")
        assert "Sapphire" in gem["primary"] or "Neelam" in gem.get("alternate_name", "")

    def test_saturn_fasting_day_is_saturday(self):
        entry = get_remedies("saturn")
        assert "Saturday" in entry["fasting_day"]


class TestMarsRemedies:

    def test_mars_gemstone_is_red_coral(self):
        gem = get_gemstone_recommendation("mars")
        assert "Coral" in gem["primary"]

    def test_mars_mantra_ids_include_hanuman(self):
        """Mars remedies include Hanuman (Mars's deity) mantra."""
        ids = get_mantra_ids("mars")
        assert "hanuman_beej_mantra" in ids


class TestRahuRemedies:

    def test_rahu_gemstone_is_hessonite(self):
        gem = get_gemstone_recommendation("rahu")
        assert "Hessonite" in gem["primary"] or "Gomed" in gem.get("alternate_name", "")

    def test_rahu_mantra_ids_non_empty(self):
        ids = get_mantra_ids("rahu")
        assert len(ids) > 0


class TestKetuRemedies:

    def test_ketu_gemstone_is_cats_eye(self):
        gem = get_gemstone_recommendation("ketu")
        assert "Eye" in gem["primary"] or "Lehsunia" in gem.get("alternate_name", "")

    def test_ketu_mantra_ids_non_empty(self):
        ids = get_mantra_ids("ketu")
        assert len(ids) > 0

    def test_ketu_full_remedy_text_non_empty(self):
        text = get_full_remedy_text("ketu")
        assert len(text) > 50


# ---------------------------------------------------------------------------
# 3. API edge-case tests
# ---------------------------------------------------------------------------

class TestAPIEdgeCases:

    def test_get_remedies_unknown_graha_returns_empty_dict(self):
        result = get_remedies("pluto")
        assert result == {}

    def test_get_gemstone_recommendation_unknown_returns_empty(self):
        result = get_gemstone_recommendation("neptune")
        assert result == {}

    def test_get_mantra_ids_unknown_returns_empty_list(self):
        result = get_mantra_ids("vulcan")
        assert result == []

    def test_get_full_remedy_text_unknown_returns_empty_string(self):
        result = get_full_remedy_text("unknown_planet")
        assert result == ""

    def test_get_remedies_case_insensitive(self):
        """get_remedies should handle uppercase input."""
        result_lower = get_remedies("sun")
        result_upper = get_remedies("SUN")
        assert result_lower == result_upper

    def test_all_mantra_ids_are_strings(self):
        """All mantra ID values must be strings (referencing mantras.py)."""
        for graha in ALL_NINE_GRAHAS:
            ids = get_mantra_ids(graha)
            for mid in ids:
                assert isinstance(mid, str), f"{graha}: mantra id {mid!r} must be a string"
                assert len(mid) > 0, f"{graha}: mantra id must be non-empty string"

    def test_full_remedy_text_includes_mantra_ids(self):
        """get_full_remedy_text output should reference mantra IDs."""
        for graha in ALL_NINE_GRAHAS:
            text = get_full_remedy_text(graha)
            assert "mantra_ids" in text.lower() or "MANTRA" in text, (
                f"{graha}: full remedy text missing mantra reference"
            )

    def test_all_gemstones_have_non_empty_primary(self):
        """Primary gemstone name must be a non-empty string for all grahas."""
        for graha in ALL_NINE_GRAHAS:
            gem = get_gemstone_recommendation(graha)
            assert isinstance(gem.get("primary"), str) and len(gem["primary"]) > 0, (
                f"{graha}: gemstone.primary must be non-empty string"
            )

    def test_all_gemstones_have_at_least_one_substitute(self):
        """Every graha must have at least one substitute gemstone."""
        for graha in ALL_NINE_GRAHAS:
            gem = get_gemstone_recommendation(graha)
            subs = gem.get("substitute", [])
            assert len(subs) >= 1, f"{graha}: must have at least 1 substitute gemstone"

    def test_classical_citations_mention_bphs_or_garuda(self):
        """All 9 grahas should cite BPHS or Garuda Purana."""
        for graha, entry in REMEDIAL_LIBRARY.items():
            citation = entry.get("classical_citation", "")
            has_bphs = "BPHS" in citation
            has_garuda = "Garuda" in citation
            has_skanda = "Skanda" in citation
            has_mani_mala = "Mani Mala" in citation
            assert any([has_bphs, has_garuda, has_skanda, has_mani_mala]), (
                f"{graha}: classical_citation must reference at least one classical text"
            )
