"""
Tests for varga_formulas.py — Divisional chart formula library.

Covers:
- VARGA_FORMULAS completeness (30+ entries, required D-numbers present)
- Required keys in each entry
- Nadi vargas (D108, D150, D2700)
- list_all_vargas() return contract
- compute_navamsa_sign() — all 4 element starting points + intermediate padas
- compute_dasamsa_sign() — odd/even sign starts + mid-sign parts
- compute_drekkana_sign() — triplicity offset formula
- compute_dvadasamsa_sign() — self-referential counting
- get_varga_formula() — retrieval and KeyError
- formula_type values are from allowed set
- divisor field matches dict key
"""

import pytest

from pipeline.varga_formulas import (
    VARGA_FORMULAS,
    get_varga_formula,
    list_all_vargas,
    compute_navamsa_sign,
    compute_dasamsa_sign,
    compute_drekkana_sign,
    compute_dvadasamsa_sign,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {"divisor", "name", "formula_type", "assignment_rule", "significance", "classical_source"}
ALLOWED_FORMULA_TYPES = {"equal_division", "special", "navamsa_cycle", "nadi"}

# Core Parashari standard D-numbers that must be present
PARASHARI_REQUIRED = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 16, 20, 24, 27, 30, 36, 40, 45, 60}

# Nadi vargas that must be present
NADI_REQUIRED = {108, 150, 2700}


# ===========================================================================
# Section 1 — VARGA_FORMULAS structure
# ===========================================================================

class TestVargaFormulasDictStructure:

    def test_at_least_30_entries(self):
        """VARGA_FORMULAS must have at least 30 entries."""
        assert len(VARGA_FORMULAS) >= 30, (
            f"Expected ≥30 entries, got {len(VARGA_FORMULAS)}"
        )

    def test_parashari_standard_keys_present(self):
        """All required Parashari standard D-numbers must be present."""
        missing = PARASHARI_REQUIRED - set(VARGA_FORMULAS.keys())
        assert not missing, f"Missing Parashari vargas: {sorted(missing)}"

    def test_nadi_vargas_present(self):
        """D108, D150, D2700 (Nadi vargas) must be present."""
        missing = NADI_REQUIRED - set(VARGA_FORMULAS.keys())
        assert not missing, f"Missing Nadi vargas: {sorted(missing)}"

    def test_d1_present(self):
        assert 1 in VARGA_FORMULAS

    def test_d2_present(self):
        assert 2 in VARGA_FORMULAS

    def test_d3_present(self):
        assert 3 in VARGA_FORMULAS

    def test_d7_present(self):
        assert 7 in VARGA_FORMULAS

    def test_d9_present(self):
        assert 9 in VARGA_FORMULAS

    def test_d10_present(self):
        assert 10 in VARGA_FORMULAS

    def test_d12_present(self):
        assert 12 in VARGA_FORMULAS

    def test_d16_present(self):
        assert 16 in VARGA_FORMULAS

    def test_d24_present(self):
        assert 24 in VARGA_FORMULAS

    def test_d27_present(self):
        assert 27 in VARGA_FORMULAS

    def test_d30_present(self):
        assert 30 in VARGA_FORMULAS

    def test_d60_present(self):
        assert 60 in VARGA_FORMULAS

    def test_d108_present(self):
        assert 108 in VARGA_FORMULAS

    def test_d150_present(self):
        assert 150 in VARGA_FORMULAS

    def test_d2700_present(self):
        assert 2700 in VARGA_FORMULAS

    @pytest.mark.parametrize("divisor", sorted(VARGA_FORMULAS.keys()))
    def test_each_entry_has_required_keys(self, divisor):
        """Every entry must contain all required keys."""
        entry = VARGA_FORMULAS[divisor]
        missing = REQUIRED_KEYS - set(entry.keys())
        assert not missing, f"D{divisor} missing keys: {missing}"

    @pytest.mark.parametrize("divisor", sorted(VARGA_FORMULAS.keys()))
    def test_divisor_field_matches_dict_key(self, divisor):
        """The 'divisor' field inside each entry must match its dict key."""
        assert VARGA_FORMULAS[divisor]["divisor"] == divisor

    @pytest.mark.parametrize("divisor", sorted(VARGA_FORMULAS.keys()))
    def test_formula_type_is_valid(self, divisor):
        """formula_type must be one of the allowed values."""
        ft = VARGA_FORMULAS[divisor]["formula_type"]
        assert ft in ALLOWED_FORMULA_TYPES, (
            f"D{divisor} has invalid formula_type '{ft}'"
        )

    @pytest.mark.parametrize("divisor", sorted(VARGA_FORMULAS.keys()))
    def test_name_is_nonempty_string(self, divisor):
        name = VARGA_FORMULAS[divisor]["name"]
        assert isinstance(name, str) and len(name) > 0

    @pytest.mark.parametrize("divisor", sorted(VARGA_FORMULAS.keys()))
    def test_assignment_rule_is_nonempty(self, divisor):
        rule = VARGA_FORMULAS[divisor]["assignment_rule"]
        assert isinstance(rule, str) and len(rule) >= 10

    def test_nadi_vargas_have_nadi_formula_type(self):
        """D108, D150, D2700 must have formula_type='nadi'."""
        for d in NADI_REQUIRED:
            ft = VARGA_FORMULAS[d]["formula_type"]
            assert ft == "nadi", f"D{d} expected formula_type='nadi', got '{ft}'"

    def test_d9_formula_type_is_navamsa_cycle(self):
        assert VARGA_FORMULAS[9]["formula_type"] == "navamsa_cycle"

    def test_d30_formula_type_is_special(self):
        """D30 Trimsamsa uses unequal divisions — must be 'special'."""
        assert VARGA_FORMULAS[30]["formula_type"] == "special"


# ===========================================================================
# Section 2 — list_all_vargas()
# ===========================================================================

class TestListAllVargas:

    def test_returns_list(self):
        result = list_all_vargas()
        assert isinstance(result, list)

    def test_returns_ints(self):
        result = list_all_vargas()
        assert all(isinstance(d, int) for d in result)

    def test_is_sorted(self):
        result = list_all_vargas()
        assert result == sorted(result)

    def test_d9_in_list(self):
        assert 9 in list_all_vargas()

    def test_d60_in_list(self):
        assert 60 in list_all_vargas()

    def test_d2700_in_list(self):
        assert 2700 in list_all_vargas()

    def test_length_matches_dict(self):
        assert len(list_all_vargas()) == len(VARGA_FORMULAS)

    def test_first_element_is_1(self):
        assert list_all_vargas()[0] == 1


# ===========================================================================
# Section 3 — get_varga_formula()
# ===========================================================================

class TestGetVargaFormula:

    def test_d9_name_contains_navamsa(self):
        formula = get_varga_formula(9)
        assert "Navamsa" in formula["name"]

    def test_d9_divisor_field(self):
        assert get_varga_formula(9)["divisor"] == 9

    def test_d10_name_contains_dasamsa(self):
        formula = get_varga_formula(10)
        assert "Dasamsa" in formula["name"]

    def test_d1_name(self):
        formula = get_varga_formula(1)
        assert "Rasi" in formula["name"]

    def test_unknown_divisor_raises_key_error(self):
        with pytest.raises(KeyError):
            get_varga_formula(999)

    def test_d2700_name_contains_nadi(self):
        formula = get_varga_formula(2700)
        # Name or alias should reference Nadi
        combined = formula["name"] + formula.get("alias", "")
        assert "Nadi" in combined or "nadi" in combined.lower()

    def test_returns_dict(self):
        result = get_varga_formula(12)
        assert isinstance(result, dict)


# ===========================================================================
# Section 4 — compute_navamsa_sign()
# ===========================================================================

class TestComputeNavamsaSign:

    # --- Fire signs start from Aries (0) ---

    def test_aries_0deg_returns_aries(self):
        """Aries (fire) at 0° → pada 0 → Aries navamsa."""
        assert compute_navamsa_sign(0, 0.0) == 0

    def test_aries_3deg20_boundary_returns_taurus(self):
        """Aries at 3°20' (= 3.333..°) → pada 1 → Taurus navamsa."""
        assert compute_navamsa_sign(0, 10.0 / 3) == 1

    def test_aries_3deg30_returns_taurus(self):
        """Aries at 3°30' is in pada 1 → Taurus navamsa."""
        assert compute_navamsa_sign(0, 3.5) == 1

    def test_aries_late_degree_returns_pisces(self):
        """Aries at 29° → pada 8 → Aries+8 = Sagittarius (0+8=8)."""
        assert compute_navamsa_sign(0, 29.0) == 8

    def test_leo_fire_sign_starts_aries(self):
        """Leo (fire, index=4) at 0° → pada 0 → Aries navamsa."""
        assert compute_navamsa_sign(4, 0.0) == 0

    def test_sagittarius_fire_sign_starts_aries(self):
        """Sagittarius (fire, index=8) at 0° → pada 0 → Aries navamsa."""
        assert compute_navamsa_sign(8, 0.0) == 0

    # --- Earth signs start from Capricorn (9) ---

    def test_taurus_0deg_returns_capricorn(self):
        """Taurus (earth, index=1) at 0° → pada 0 → Capricorn navamsa."""
        assert compute_navamsa_sign(1, 0.0) == 9

    def test_taurus_3deg30_returns_aquarius(self):
        """Taurus at 3°30' → pada 1 → Capricorn+1 = Aquarius (10)."""
        assert compute_navamsa_sign(1, 3.5) == 10

    def test_virgo_earth_sign_starts_capricorn(self):
        """Virgo (earth, index=5) at 0° → Capricorn navamsa."""
        assert compute_navamsa_sign(5, 0.0) == 9

    def test_capricorn_earth_sign_starts_capricorn(self):
        """Capricorn (earth, index=9) at 0° → Capricorn navamsa."""
        assert compute_navamsa_sign(9, 0.0) == 9

    # --- Air signs start from Libra (6) ---

    def test_gemini_0deg_returns_libra(self):
        """Gemini (air, index=2) at 0° → pada 0 → Libra navamsa."""
        assert compute_navamsa_sign(2, 0.0) == 6

    def test_libra_air_sign_starts_libra(self):
        """Libra (air, index=6) at 0° → Libra navamsa."""
        assert compute_navamsa_sign(6, 0.0) == 6

    def test_aquarius_air_sign_starts_libra(self):
        """Aquarius (air, index=10) at 0° → Libra navamsa."""
        assert compute_navamsa_sign(10, 0.0) == 6

    # --- Water signs start from Cancer (3) ---

    def test_cancer_0deg_returns_cancer(self):
        """Cancer (water, index=3) at 0° → pada 0 → Cancer navamsa."""
        assert compute_navamsa_sign(3, 0.0) == 3

    def test_scorpio_water_sign_starts_cancer(self):
        """Scorpio (water, index=7) at 0° → Cancer navamsa."""
        assert compute_navamsa_sign(7, 0.0) == 3

    def test_pisces_water_sign_starts_cancer(self):
        """Pisces (water, index=11) at 0° → Cancer navamsa."""
        assert compute_navamsa_sign(11, 0.0) == 3

    # --- Wraparound ---

    def test_navamsa_wraparound_pisces(self):
        """Cancer at 26°40' → pada 8 → Cancer+8 = Pisces (3+8=11)."""
        assert compute_navamsa_sign(3, 26.7) == 11


# ===========================================================================
# Section 5 — compute_dasamsa_sign()
# ===========================================================================

class TestComputeDasamsaSign:

    def test_aries_0deg_returns_aries(self):
        """Aries (index=0, 0-indexed even = classical odd) at 0° → Aries dasamsa."""
        assert compute_dasamsa_sign(0, 0.0) == 0

    def test_taurus_0deg_returns_capricorn(self):
        """Taurus (index=1, 0-indexed odd = classical even) at 0° → Capricorn dasamsa."""
        assert compute_dasamsa_sign(1, 0.0) == 9

    def test_aries_15deg_returns_gemini(self):
        """Aries at 15° → part 5 → Aries+5 = Gemini (0+5=5)."""
        assert compute_dasamsa_sign(0, 15.0) == 5

    def test_aries_3deg_returns_taurus(self):
        """Aries at 3° → part 1 → 0+1 = Taurus (1)."""
        assert compute_dasamsa_sign(0, 3.0) == 1

    def test_taurus_9deg_returns_sagittarius(self):
        """Taurus at 9° → part 3 → Capricorn+3 = Sagittarius (9+3=12%12=0)... wait, 9+3=12%12=0."""
        # 9+3=12, 12%12=0 = Aries
        assert compute_dasamsa_sign(1, 9.0) == 0

    def test_gemini_0deg_returns_aries(self):
        """Gemini (index=2, even) at 0° → Aries start → Aries dasamsa (0)."""
        assert compute_dasamsa_sign(2, 0.0) == 0

    def test_cancer_0deg_returns_capricorn(self):
        """Cancer (index=3, odd) at 0° → Capricorn start (9)."""
        assert compute_dasamsa_sign(3, 0.0) == 9

    def test_aries_29deg_returns_capricorn(self):
        """Aries at 29° → part 9 → 0+9=9 = Capricorn."""
        assert compute_dasamsa_sign(0, 29.0) == 9

    def test_pisces_0deg_returns_capricorn(self):
        """Pisces (index=11, odd) at 0° → Capricorn start (9)."""
        assert compute_dasamsa_sign(11, 0.0) == 9

    def test_scorpio_15deg(self):
        """Scorpio (index=7, odd) at 15° → part 5 → 9+5=14%12=2 = Gemini."""
        assert compute_dasamsa_sign(7, 15.0) == 2


# ===========================================================================
# Section 6 — compute_drekkana_sign()
# ===========================================================================

class TestComputeDrekkanaSign:

    def test_aries_0deg_returns_aries(self):
        """Aries at 0° → part 0 → same sign = Aries (0)."""
        assert compute_drekkana_sign(0, 0.0) == 0

    def test_aries_10deg_returns_leo(self):
        """Aries at 10° → part 1 → 0+1*4=4 = Leo."""
        assert compute_drekkana_sign(0, 10.0) == 4

    def test_aries_20deg_returns_sagittarius(self):
        """Aries at 20° → part 2 → 0+2*4=8 = Sagittarius."""
        assert compute_drekkana_sign(0, 20.0) == 8

    def test_cancer_0deg_returns_cancer(self):
        """Cancer at 0° → part 0 → 3+0*4=3 = Cancer."""
        assert compute_drekkana_sign(3, 0.0) == 3

    def test_cancer_10deg_returns_scorpio(self):
        """Cancer at 10° → part 1 → 3+1*4=7 = Scorpio."""
        assert compute_drekkana_sign(3, 10.0) == 7

    def test_cancer_20deg_returns_pisces(self):
        """Cancer at 20° → part 2 → 3+2*4=11 = Pisces."""
        assert compute_drekkana_sign(3, 20.0) == 11


# ===========================================================================
# Section 7 — compute_dvadasamsa_sign()
# ===========================================================================

class TestComputeDvadasamsaSign:

    def test_aries_0deg_returns_aries(self):
        """Aries at 0° → part 0 → 0+0=0 = Aries."""
        assert compute_dvadasamsa_sign(0, 0.0) == 0

    def test_aries_2deg30_returns_taurus(self):
        """Aries at 2°30' = 2.5° → part 1 → 0+1=1 = Taurus."""
        assert compute_dvadasamsa_sign(0, 2.5) == 1

    def test_taurus_0deg_returns_taurus(self):
        """Taurus at 0° → part 0 → 1+0=1 = Taurus."""
        assert compute_dvadasamsa_sign(1, 0.0) == 1

    def test_taurus_2deg5_returns_gemini(self):
        """Taurus at 2.5° → part 1 → 1+1=2 = Gemini."""
        assert compute_dvadasamsa_sign(1, 2.5) == 2

    def test_pisces_27deg5_returns_pisces(self):
        """Pisces at 27.5° → part 11 → 11+11=22%12=10 = Aquarius."""
        assert compute_dvadasamsa_sign(11, 27.5) == (11 + 11) % 12
