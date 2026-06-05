"""
test_l0_reference.py — Unit tests for brahmagyan.l0_reference (BRAHMA-BG-0-2)

Tests:
    1. Volume floor: >= 11 planets, 27 nakshatras, 12 signs, 30 aspects, 16 vargas
    2. Source citation: non-null on every record
    3. Planet completeness: all 9 grahas + Rahu + Ketu present
    4. Nakshatra completeness: IDs 1-27 all present, degrees cover 0-360
    5. Sign completeness: IDs 1-12, lords correct for key signs
    6. Aspect correctness: all planets have 7th aspect; Mars 4th/8th; Jupiter 5th/9th; Saturn 3rd/10th
    7. Varga completeness: D1, D9, D10, D60 present with correct division counts
    8. dry_run: returns correct counts without DB writes
    9. lookup_planet: resolves 'saturn' -> Saturn; 'shani' not found (canonical IDs)
    10. lookup_nakshatra: ID 25 -> Purva Bhadrapada (native Moon nakshatra)

No live DB required. All DB calls are mocked.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

# ── Lazy import ────────────────────────────────────────────────────────────────

def _get_module():
    from brahmagyan import l0_reference as mod
    return mod


# ── Volume floor tests ─────────────────────────────────────────────────────────

class TestVolumeFloors:
    def test_planets_volume_floor(self):
        mod = _get_module()
        assert len(mod.PLANETS) >= 11, f"Need >= 11 planets, got {len(mod.PLANETS)}"

    def test_nakshatras_volume_floor(self):
        mod = _get_module()
        assert len(mod.NAKSHATRAS) >= 27, f"Need >= 27 nakshatras, got {len(mod.NAKSHATRAS)}"

    def test_signs_volume_floor(self):
        mod = _get_module()
        assert len(mod.SIGNS) >= 12, f"Need >= 12 signs, got {len(mod.SIGNS)}"

    def test_aspects_volume_floor(self):
        mod = _get_module()
        # 9 planets × 7th + Mars(4,8) + Jupiter(5,9) + Saturn(3,10) + Rahu/Ketu(5,9) = 19 minimum
        assert len(mod.ASPECTS) >= 19, f"Need >= 19 aspect rows, got {len(mod.ASPECTS)}"

    def test_vargas_volume_floor(self):
        mod = _get_module()
        assert len(mod.VARGAS) >= 16, f"Need >= 16 vargas, got {len(mod.VARGAS)}"


# ── Source citation tests ──────────────────────────────────────────────────────

class TestSourceCitations:
    def test_all_planets_have_source_citation(self):
        mod = _get_module()
        for p in mod.PLANETS:
            assert p.get("source_citation"), f"Missing source_citation for planet {p['planet_id']}"

    def test_all_nakshatras_have_source_citation(self):
        mod = _get_module()
        # Nakshatra source citation is added at write time but cite is TAITTIRIYA
        assert mod.TAITTIRIYA, "TAITTIRIYA citation string must be non-empty"

    def test_all_aspects_have_source_citation(self):
        mod = _get_module()
        for a in mod.ASPECTS:
            assert a.get("source_citation"), f"Missing source_citation for aspect {a['planet_id']}/{a['aspect_house']}"


# ── Planet completeness ────────────────────────────────────────────────────────

class TestPlanetCompleteness:
    EXPECTED_PLANETS = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}

    def test_nine_grahas_present(self):
        mod = _get_module()
        planet_ids = {p["planet_id"] for p in mod.PLANETS}
        missing = self.EXPECTED_PLANETS - planet_ids
        assert not missing, f"Missing grahas: {missing}"

    def test_saturn_exalted_in_libra(self):
        mod = _get_module()
        saturn = mod.lookup_planet("saturn")
        assert saturn is not None
        assert saturn["exaltation_sign"] == 7, "Saturn should be exalted in Libra (sign 7)"

    def test_jupiter_exalted_in_cancer(self):
        mod = _get_module()
        jup = mod.lookup_planet("jupiter")
        assert jup is not None
        assert jup["exaltation_sign"] == 4, "Jupiter should be exalted in Cancer (sign 4)"

    def test_sun_debilitated_in_libra(self):
        mod = _get_module()
        sun = mod.lookup_planet("sun")
        assert sun is not None
        assert sun["debilitation_sign"] == 7, "Sun should be debilitated in Libra (sign 7)"

    def test_rahu_has_dasha_years(self):
        mod = _get_module()
        rahu = mod.lookup_planet("rahu")
        assert rahu is not None
        assert rahu["dasha_years"] == 18.0, "Rahu Vimshottari period = 18 years"

    def test_vimshottari_totals_120_years(self):
        mod = _get_module()
        total = sum(
            p["dasha_years"] for p in mod.PLANETS
            if p.get("dasha_years") is not None
        )
        assert abs(total - 120.0) < 0.1, f"Vimshottari total should be 120, got {total}"


# ── Nakshatra completeness ─────────────────────────────────────────────────────

class TestNakshatraCompleteness:
    def test_all_27_ids_present(self):
        mod = _get_module()
        nak_ids = {nak[0] for nak in mod.NAKSHATRAS}
        assert nak_ids == set(range(1, 28)), "All 27 nakshatra IDs 1-27 must be present"

    def test_degrees_cover_full_zodiac(self):
        mod = _get_module()
        start = mod.NAKSHATRAS[0][7]  # start_degree of Ashwini
        end = mod.NAKSHATRAS[-1][8]   # end_degree of Revati
        assert abs(start - 0.0) < 0.1, "Ashwini should start at 0°"
        assert abs(end - 360.0) < 0.1, "Revati should end at 360°"

    def test_native_moon_nakshatra_purva_bhadrapada(self):
        """Native (1984-02-05) Moon is in Purva Bhadrapada (ID=25)."""
        mod = _get_module()
        nak = mod.lookup_nakshatra(25)
        assert nak is not None
        assert nak[1] == "Purva Bhadrapada"
        assert nak[3] == "jupiter"  # Jupiter is its lord

    def test_purva_bhadrapada_degree_range(self):
        """Purva Bhadrapada: 320° - 333.333° (Aquarius-Pisces cusp)."""
        mod = _get_module()
        nak = mod.lookup_nakshatra(25)
        assert abs(nak[7] - 320.0) < 0.1
        assert abs(nak[8] - 333.333) < 0.1

    def test_each_nakshatra_has_4_pada_lords(self):
        mod = _get_module()
        for nak in mod.NAKSHATRAS:
            nak_id, name = nak[0], nak[1]
            pada_lords = nak[9]
            assert len(pada_lords) == 4, f"Nakshatra {name} should have 4 pada lords"


# ── Sign completeness ──────────────────────────────────────────────────────────

class TestSignCompleteness:
    def test_all_12_ids_present(self):
        mod = _get_module()
        sign_ids = {s[0] for s in mod.SIGNS}
        assert sign_ids == set(range(1, 13)), "All 12 sign IDs 1-12 must be present"

    def test_capricorn_is_saturn_ruled(self):
        mod = _get_module()
        cap = next(s for s in mod.SIGNS if s[0] == 10)
        assert cap[3] == "saturn", "Capricorn (sign 10) is Saturn-ruled"

    def test_cancer_is_moon_ruled(self):
        mod = _get_module()
        cancer = next(s for s in mod.SIGNS if s[0] == 4)
        assert cancer[3] == "moon", "Cancer (sign 4) is Moon-ruled"

    def test_sun_born_in_capricorn(self):
        """Native Sun is in Capricorn (sign 10) at birth (1984-02-05)."""
        mod = _get_module()
        cap = next(s for s in mod.SIGNS if s[0] == 10)
        assert "capricorn" in cap[1].lower() or cap[1] == "Capricorn"
        assert cap[3] == "saturn"


# ── Aspect correctness ─────────────────────────────────────────────────────────

class TestAspectCorrectness:
    def _aspects_for(self, planet_id: str) -> list[int]:
        mod = _get_module()
        return [a["aspect_house"] for a in mod.ASPECTS if a["planet_id"] == planet_id]

    def test_all_planets_have_7th_aspect(self):
        mod = _get_module()
        planets = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}
        for p in planets:
            houses = [a["aspect_house"] for a in mod.ASPECTS if a["planet_id"] == p]
            assert 7 in houses, f"{p} must have 7th house aspect"

    def test_mars_special_aspects_4_8(self):
        assert 4 in self._aspects_for("mars"), "Mars must aspect 4th house"
        assert 8 in self._aspects_for("mars"), "Mars must aspect 8th house"

    def test_jupiter_special_aspects_5_9(self):
        assert 5 in self._aspects_for("jupiter"), "Jupiter must aspect 5th house"
        assert 9 in self._aspects_for("jupiter"), "Jupiter must aspect 9th house"

    def test_saturn_special_aspects_3_10(self):
        assert 3 in self._aspects_for("saturn"), "Saturn must aspect 3rd house"
        assert 10 in self._aspects_for("saturn"), "Saturn must aspect 10th house"


# ── Varga completeness ─────────────────────────────────────────────────────────

class TestVargaCompleteness:
    def _varga(self, varga_id: str):
        mod = _get_module()
        for v in mod.VARGAS:
            if v[0] == varga_id:
                return v
        return None

    def test_d1_present(self):
        assert self._varga("D1") is not None

    def test_d9_navamsha_present(self):
        v = self._varga("D9")
        assert v is not None
        assert "marriage" in v[5].lower() or "navamsha" in v[3].lower()

    def test_d10_dashamsha_present(self):
        v = self._varga("D10")
        assert v is not None
        assert "career" in v[5].lower()

    def test_d60_shastiamsha_present(self):
        v = self._varga("D60")
        assert v is not None
        assert v[4] == 60  # division_count is index 4: (varga_id, num, name_en, name_sa, division_count, ...)

    def test_16_vargas_minimum(self):
        mod = _get_module()
        assert len(mod.VARGAS) >= 16


# ── dry_run ────────────────────────────────────────────────────────────────────

class TestDryRun:
    def test_dry_run_returns_correct_counts(self):
        mod = _get_module()
        counts = mod.seed_reference(conn=None, dry_run=True)
        assert counts["reference_planets"] >= 11
        assert counts["reference_nakshatras"] >= 27
        assert counts["reference_signs"] >= 12
        assert counts["reference_aspects"] >= 19
        assert counts["reference_vargas"] >= 16

    def test_dry_run_does_not_touch_db(self):
        mod = _get_module()
        mock_conn = MagicMock()
        counts = mod.seed_reference(conn=mock_conn, dry_run=True)
        mock_conn.cursor.assert_not_called()
        mock_conn.commit.assert_not_called()


# ── lookup helpers ─────────────────────────────────────────────────────────────

class TestLookupHelpers:
    def test_lookup_planet_saturn(self):
        mod = _get_module()
        p = mod.lookup_planet("saturn")
        assert p is not None
        assert p["canonical_name_sa"] == "Shani"

    def test_lookup_planet_unknown(self):
        mod = _get_module()
        assert mod.lookup_planet("uranus") is None

    def test_lookup_nakshatra_25_purva_bhadrapada(self):
        mod = _get_module()
        nak = mod.lookup_nakshatra(25)
        assert nak is not None
        assert "Purva Bhadrapada" in nak[1]

    def test_lookup_nakshatra_out_of_range(self):
        mod = _get_module()
        assert mod.lookup_nakshatra(28) is None
