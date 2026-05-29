"""
test_saham_formulas.py — Test suite for the Tajik Saham formula library.

Covers:
- SAHAM_FORMULAS completeness (>=55 entries)
- Schema integrity (required keys on all entries)
- Specific saham content assertions (Punya, Vivah, Putra, Karma, etc.)
- compute_saham_longitude correctness (day/night, modulo-360, known values)
- get_saham (case-insensitive lookup, KeyError on unknown)
- list_sahams_by_domain filtering
- same_day_night flag behaviour
- Error handling for missing bodies

Minimum 30 distinct assertions.
"""

from __future__ import annotations

import math
import pytest

from pipeline.saham_formulas import (
    SAHAM_FORMULAS,
    compute_saham_longitude,
    get_saham,
    list_sahams_by_domain,
)

# ---------------------------------------------------------------------------
# Required schema keys every entry must carry
# ---------------------------------------------------------------------------
REQUIRED_KEYS = {
    "name",
    "domain",
    "day_formula",
    "night_formula",
    "same_day_night",
    "classical_citation",
}

# ---------------------------------------------------------------------------
# Helper: simple mock positions covering all body identifiers
# ---------------------------------------------------------------------------
MOCK_POSITIONS: dict[str, float] = {
    "sun":     30.0,
    "moon":    90.0,
    "mars":   120.0,
    "mercury": 60.0,
    "jupiter": 200.0,
    "venus":   270.0,
    "saturn":  300.0,
    "rahu":    150.0,
    "ketu":    330.0,
    "asc":      0.0,
}


# ============================================================
# Section 1 — Completeness
# ============================================================

class TestCompleteness:
    def test_at_least_55_entries(self):
        """SAHAM_FORMULAS must contain at least 55 sahams."""
        assert len(SAHAM_FORMULAS) >= 55  # assertion 1

    def test_all_entries_have_required_keys(self):
        """Every entry must carry all required schema keys."""
        for key, entry in SAHAM_FORMULAS.items():
            missing = REQUIRED_KEYS - set(entry.keys())
            assert not missing, f"Entry '{key}' missing keys: {missing}"  # assertion 2

    def test_all_day_formulas_are_3_tuples(self):
        """day_formula must be a tuple/list of exactly 3 string body identifiers."""
        for key, entry in SAHAM_FORMULAS.items():
            assert len(entry["day_formula"]) == 3, \
                f"Entry '{key}' day_formula length != 3"  # assertion 3

    def test_all_night_formulas_are_3_tuples(self):
        """night_formula must be a tuple/list of exactly 3 string body identifiers."""
        for key, entry in SAHAM_FORMULAS.items():
            assert len(entry["night_formula"]) == 3, \
                f"Entry '{key}' night_formula length != 3"  # assertion 4

    def test_all_same_day_night_are_bool(self):
        """same_day_night must be a boolean."""
        for key, entry in SAHAM_FORMULAS.items():
            assert isinstance(entry["same_day_night"], bool), \
                f"Entry '{key}' same_day_night is not bool"  # assertion 5

    def test_all_names_are_nonempty_strings(self):
        """name field must be a non-empty string."""
        for key, entry in SAHAM_FORMULAS.items():
            assert isinstance(entry["name"], str) and len(entry["name"]) > 0, \
                f"Entry '{key}' has invalid name"  # assertion 6

    def test_all_citations_are_nonempty_strings(self):
        """classical_citation must be a non-empty string."""
        for key, entry in SAHAM_FORMULAS.items():
            assert isinstance(entry["classical_citation"], str) and \
                len(entry["classical_citation"]) > 0, \
                f"Entry '{key}' has empty citation"  # assertion 7

    def test_all_domains_are_nonempty_strings(self):
        """domain must be a non-empty string."""
        for key, entry in SAHAM_FORMULAS.items():
            assert isinstance(entry["domain"], str) and len(entry["domain"]) > 0, \
                f"Entry '{key}' has empty domain"  # assertion 8


# ============================================================
# Section 2 — Key sahams present and correct
# ============================================================

class TestKeyEntries:
    # ---- Punya ----
    def test_punya_present(self):
        assert "punya" in SAHAM_FORMULAS  # assertion 9

    def test_punya_day_formula(self):
        assert SAHAM_FORMULAS["punya"]["day_formula"] == ("moon", "sun", "asc")  # assertion 10

    def test_punya_night_formula(self):
        assert SAHAM_FORMULAS["punya"]["night_formula"] == ("sun", "moon", "asc")  # assertion 11

    def test_punya_domain(self):
        assert SAHAM_FORMULAS["punya"]["domain"] == "fortune"  # assertion 12

    def test_punya_same_day_night_false(self):
        assert SAHAM_FORMULAS["punya"]["same_day_night"] is False  # assertion 13

    # ---- Vivah ----
    def test_vivah_present(self):
        assert "vivah" in SAHAM_FORMULAS  # assertion 14

    def test_vivah_domain(self):
        assert SAHAM_FORMULAS["vivah"]["domain"] == "marriage"  # assertion 15

    def test_vivah_day_formula(self):
        assert SAHAM_FORMULAS["vivah"]["day_formula"] == ("venus", "sun", "asc")  # assertion 16

    # ---- Putra ----
    def test_putra_present(self):
        assert "putra" in SAHAM_FORMULAS  # assertion 17

    def test_putra_domain(self):
        assert SAHAM_FORMULAS["putra"]["domain"] == "children"  # assertion 18

    def test_putra_day_formula(self):
        assert SAHAM_FORMULAS["putra"]["day_formula"] == ("jupiter", "moon", "asc")  # assertion 19

    def test_putra_night_formula(self):
        assert SAHAM_FORMULAS["putra"]["night_formula"] == ("moon", "jupiter", "asc")  # assertion 20

    # ---- Karma ----
    def test_karma_present(self):
        assert "karma" in SAHAM_FORMULAS  # assertion 21

    def test_karma_domain(self):
        assert SAHAM_FORMULAS["karma"]["domain"] == "career"  # assertion 22

    def test_karma_day_formula(self):
        assert SAHAM_FORMULAS["karma"]["day_formula"] == ("saturn", "sun", "asc")  # assertion 23

    # ---- Mrityu ----
    def test_mrityu_present(self):
        assert "mrityu" in SAHAM_FORMULAS  # assertion 24

    def test_mrityu_domain(self):
        assert SAHAM_FORMULAS["mrityu"]["domain"] == "death"  # assertion 25

    # ---- Vivah night-same variant ----
    def test_vivah_night_same_flag(self):
        assert SAHAM_FORMULAS["vivah_night_same"]["same_day_night"] is True  # assertion 26


# ============================================================
# Section 3 — get_saham API
# ============================================================

class TestGetSaham:
    def test_get_saham_lowercase(self):
        entry = get_saham("punya")
        assert entry["name"] == "Punya"  # assertion 27

    def test_get_saham_uppercase(self):
        entry = get_saham("PUNYA")
        assert entry["name"] == "Punya"  # assertion 28

    def test_get_saham_mixed_case(self):
        entry = get_saham("Vivah")
        assert entry["domain"] == "marriage"  # assertion 29

    def test_get_saham_unknown_raises_key_error(self):
        with pytest.raises(KeyError):
            get_saham("nonexistent_saham_xyz")  # assertion 30

    def test_get_saham_with_whitespace(self):
        entry = get_saham("  karma  ")
        assert entry["domain"] == "career"  # assertion 31


# ============================================================
# Section 4 — compute_saham_longitude
# ============================================================

class TestComputeSahamLongitude:
    """
    Punya day formula: moon - sun + asc = 90 - 30 + 0 = 60.0
    Punya night formula: sun - moon + asc = 30 - 90 + 0 = -60 % 360 = 300.0
    """

    def test_punya_day_birth(self):
        result = compute_saham_longitude("punya", MOCK_POSITIONS, is_day_birth=True)
        assert math.isclose(result, 60.0, abs_tol=1e-9)  # assertion 32

    def test_punya_night_birth(self):
        result = compute_saham_longitude("punya", MOCK_POSITIONS, is_day_birth=False)
        assert math.isclose(result, 300.0, abs_tol=1e-9)  # assertion 33

    def test_result_in_range_0_to_360(self):
        """All results must be in [0, 360)."""
        for name in SAHAM_FORMULAS:
            for is_day in (True, False):
                r = compute_saham_longitude(name, MOCK_POSITIONS, is_day)
                assert 0.0 <= r < 360.0, \
                    f"{name} day={is_day} result {r} out of range"  # assertion 34

    def test_same_day_night_flag_ignored(self):
        """For same_day_night=True entries, day and night results are identical."""
        result_day = compute_saham_longitude(
            "vivah_night_same", MOCK_POSITIONS, is_day_birth=True
        )
        result_night = compute_saham_longitude(
            "vivah_night_same", MOCK_POSITIONS, is_day_birth=False
        )
        assert math.isclose(result_day, result_night, abs_tol=1e-9)  # assertion 35

    def test_known_value_karma_day(self):
        """Karma day: saturn - sun + asc = 300 - 30 + 0 = 270."""
        result = compute_saham_longitude("karma", MOCK_POSITIONS, is_day_birth=True)
        assert math.isclose(result, 270.0, abs_tol=1e-9)  # assertion 36

    def test_known_value_vivah_day(self):
        """Vivah day: venus - sun + asc = 270 - 30 + 0 = 240."""
        result = compute_saham_longitude("vivah", MOCK_POSITIONS, is_day_birth=True)
        assert math.isclose(result, 240.0, abs_tol=1e-9)  # assertion 37

    def test_missing_body_raises_key_error(self):
        incomplete = {"sun": 30.0, "moon": 90.0}  # missing 'asc'
        with pytest.raises(KeyError):
            compute_saham_longitude("punya", incomplete, is_day_birth=True)  # assertion 38

    def test_case_insensitive_name(self):
        r1 = compute_saham_longitude("punya", MOCK_POSITIONS, True)
        r2 = compute_saham_longitude("PUNYA", MOCK_POSITIONS, True)
        assert math.isclose(r1, r2, abs_tol=1e-9)  # assertion 39

    def test_modulo_wraps_over_360(self):
        """Force a result that would exceed 360 without modulo."""
        positions = dict(MOCK_POSITIONS)
        positions["jupiter"] = 350.0  # jupiter - moon + asc = 350 - 90 + 0 = 260
        r = compute_saham_longitude("putra", positions, is_day_birth=True)
        assert 0.0 <= r < 360.0  # assertion 40

    def test_modulo_wraps_negative(self):
        """Force a negative intermediate before modulo."""
        positions = dict(MOCK_POSITIONS)
        positions["jupiter"] = 10.0  # jupiter - moon + asc = 10 - 90 + 0 = -80 → 280
        r = compute_saham_longitude("putra", positions, is_day_birth=True)
        assert math.isclose(r, 280.0, abs_tol=1e-9)  # assertion 41


# ============================================================
# Section 5 — list_sahams_by_domain
# ============================================================

class TestListSahamsByDomain:
    def test_marriage_domain_nonempty(self):
        result = list_sahams_by_domain("marriage")
        assert len(result) > 0  # assertion 42

    def test_marriage_domain_contains_vivah(self):
        result = list_sahams_by_domain("marriage")
        assert "vivah" in result  # assertion 43

    def test_children_domain_contains_putra(self):
        result = list_sahams_by_domain("children")
        assert "putra" in result  # assertion 44

    def test_career_domain_contains_karma(self):
        result = list_sahams_by_domain("career")
        assert "karma" in result  # assertion 45

    def test_unknown_domain_returns_empty_list(self):
        result = list_sahams_by_domain("nonexistent_domain_xyz")
        assert result == []  # assertion 46

    def test_case_insensitive_domain(self):
        lower = list_sahams_by_domain("fortune")
        upper = list_sahams_by_domain("FORTUNE")
        assert lower == upper  # assertion 47

    def test_returns_sorted_list(self):
        result = list_sahams_by_domain("career")
        assert result == sorted(result)  # assertion 48

    def test_fortune_domain_contains_punya(self):
        result = list_sahams_by_domain("fortune")
        assert "punya" in result  # assertion 49

    def test_longevity_domain_nonempty(self):
        result = list_sahams_by_domain("longevity")
        assert len(result) >= 1  # assertion 50
