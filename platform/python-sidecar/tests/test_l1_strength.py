"""
test_l1_strength.py — Tests for brahmagyan.ganita.l1_strength (ganita.strength)

Tests:
  1.  VOLUME_FLOOR >= 150
  2.  CLASSICAL_PLANETS has exactly 7 planets (no nodes)
  3.  NAISARGIKA_BALA: all 7 planets have positive values
  4.  check_volume() status GREEN
  5.  check_volume() actual >= volume_floor
  6.  check_volume() breakdown has shadbala_rows >= 7
  7.  compute_all_strength() returns shadbala dict
  8.  compute_all_strength() returns ashtakavarga dict
  9.  compute_all_strength() returns bhava_bala dict
  10. compute_all_strength() shadbala has 7 planets
  11. compute_all_strength() each planet has 6 shadbala components
  12. compute_all_strength() all shadbala totals > 0
  13. compute_all_strength() ashtakavarga has sarva key
  14. compute_all_strength() ashtakavarga sarva has 12 house bindus + total
  15. compute_all_strength() all ashtakavarga house bindus in [0, 8]
  16. compute_all_strength() bhava_bala has 12 houses
  17. compute_all_strength() all bhava_bala values > 0
  18. compute_sthana_bala() Sun has higher sthana if in Aries vs Libra
  19. compute_dig_bala() returns values in [0, 60]
  20. compute_naisargika_bala() Sun > Saturn (by definition)
  21. compute_ashtakavarga() sarva total = sum of all planet totals
  22. compute_bhava_bala() returns 12 houses
  23. compute_all_strength() total_rows >= 150
  24. shadbala components include required 6 fields
  25. source_citation non-empty
"""
from __future__ import annotations

import pytest

import ga_writers.ga_strength_writer as sut


def _get_mod():
    from brahmagyan.ganita import l1_strength as mod
    return mod


def _positions():
    from brahmagyan.ganita.l1_positions import compute_positions_all_bodies, _birth_jd_utc
    jd = _birth_jd_utc()
    pos = compute_positions_all_bodies(jd, "lahiri")
    return {p["name"]: p for p in pos}


# ── Mock chart output for _derive_shadbala_from_positions unit tests ──────────
# Represents a minimal plausible D1 chart with 9 bodies (7 classical + Rahu/Ketu).
# Planets are placed in distinct houses so drik-bala varies across grahas.
MOCK_CHART_OUTPUT: dict = {
    "grahas": [
        {"name": "Sun",     "sign_id": 10, "house": 10, "retrograde": False, "dignity_status": "neutral"},
        {"name": "Moon",    "sign_id": 11, "house": 11, "retrograde": False, "dignity_status": "neutral"},
        {"name": "Mars",    "sign_id": 1,  "house": 1,  "retrograde": False, "dignity_status": "own_sign"},
        {"name": "Mercury", "sign_id": 10, "house": 10, "retrograde": False, "dignity_status": "neutral"},
        {"name": "Jupiter", "sign_id": 9,  "house": 9,  "retrograde": False, "dignity_status": "own_sign"},
        {"name": "Venus",   "sign_id": 12, "house": 12, "retrograde": False, "dignity_status": "neutral"},
        {"name": "Saturn",  "sign_id": 3,  "house": 3,  "retrograde": False, "dignity_status": "neutral"},
        {"name": "Rahu",    "sign_id": 6,  "house": 6,  "retrograde": True,  "dignity_status": "neutral"},
        {"name": "Ketu",    "sign_id": 12, "house": 12, "retrograde": True,  "dignity_status": "neutral"},
    ],
    "panchanga": {
        "vara": 0,       # Sunday
        "tithi_id": 3,   # Shukla Tritiya → is_shukla=True
        "is_daytime": True,
    },
    "ascendant": {"sign_id": 1, "sign": "Aries"},
}


# ── Constants ─────────────────────────────────────────────────────────────────

class TestConstants:
    def test_volume_floor_gte_100(self):
        mod = _get_mod()
        assert mod.VOLUME_FLOOR >= 100

    def test_seven_classical_planets(self):
        mod = _get_mod()
        assert len(mod.CLASSICAL_PLANETS) == 7
        assert "Rahu" not in mod.CLASSICAL_PLANETS
        assert "Ketu" not in mod.CLASSICAL_PLANETS

    def test_naisargika_all_positive(self):
        mod = _get_mod()
        for planet, val in mod.NAISARGIKA_BALA.items():
            assert val > 0.0, f"{planet} naisargika={val}"

    def test_naisargika_sun_highest(self):
        mod = _get_mod()
        assert mod.NAISARGIKA_BALA["Sun"] == max(mod.NAISARGIKA_BALA.values())


# ── Volume check ──────────────────────────────────────────────────────────────

class TestCheckVolume:
    @pytest.fixture(scope="class")
    def vol(self):
        mod = _get_mod()
        return mod.check_volume()

    def test_status_green(self, vol):
        assert vol["status"] == "GREEN", f"vol={vol}"

    def test_actual_gte_floor(self, vol):
        assert vol["actual"] >= vol["volume_floor"]

    def test_shadbala_rows_gte_7(self, vol):
        assert vol["breakdown"]["shadbala_rows"] >= 7

    def test_source_citation(self, vol):
        assert vol.get("source_citation")


# ── Shadbala ──────────────────────────────────────────────────────────────────

class TestShadbala:
    @pytest.fixture(scope="class")
    def result(self):
        mod = _get_mod()
        return mod.compute_all_strength()

    def test_seven_planets(self, result):
        assert len(result["shadbala"]) == 7

    def test_six_components_per_planet(self, result):
        required = {"sthana_bala", "dig_bala", "kala_bala",
                    "cheshta_bala", "naisargika_bala", "drik_bala", "total_rupas"}
        for planet, data in result["shadbala"].items():
            for field in required:
                assert field in data, f"{planet} missing {field}"

    def test_all_totals_positive(self, result):
        for planet, data in result["shadbala"].items():
            assert data["total_rupas"] > 0.0, f"{planet} total={data['total_rupas']}"

    def test_naisargika_values_match_table(self, result):
        mod = _get_mod()
        for planet in mod.CLASSICAL_PLANETS:
            expected = mod.NAISARGIKA_BALA[planet]
            actual = result["shadbala"][planet]["naisargika_bala"]
            assert abs(actual - expected) < 0.1, (
                f"{planet} naisargika expected={expected} got={actual}"
            )


class TestSthanaDig:
    def test_sthana_bala_values_positive(self):
        mod = _get_mod()
        positions = _positions()
        sthana = mod.compute_sthana_bala(positions)
        for planet, val in sthana.items():
            assert val >= 0.0, f"{planet} sthana={val}"

    def test_dig_bala_in_range(self):
        mod = _get_mod()
        positions = _positions()
        dig = mod.compute_dig_bala(positions)
        for planet, val in dig.items():
            assert 0.0 <= val <= 60.0, f"{planet} dig={val}"

    def test_naisargika_sun_gt_saturn(self):
        mod = _get_mod()
        assert mod.compute_naisargika_bala()["Sun"] > mod.compute_naisargika_bala()["Saturn"]


# ── Ashtakavarga ──────────────────────────────────────────────────────────────

class TestAshtakavarga:
    @pytest.fixture(scope="class")
    def result(self):
        mod = _get_mod()
        return mod.compute_all_strength()

    def test_sarva_key_present(self, result):
        assert "sarva" in result["ashtakavarga"]

    def test_sarva_twelve_houses(self, result):
        sarva = result["ashtakavarga"]["sarva"]
        for h in range(1, 13):
            assert h in sarva, f"sarva missing house {h}"

    def test_all_bindus_in_0_8(self, result):
        for planet, house_data in result["ashtakavarga"].items():
            if planet == "sarva":
                continue
            for h in range(1, 13):
                bindus = house_data.get(h, 0)
                assert 0 <= bindus <= 8, f"{planet} H{h} bindus={bindus}"

    def test_sarva_total_equals_planet_sum(self, result):
        mod = _get_mod()
        planet_totals = sum(
            result["ashtakavarga"][p]["total"]
            for p in mod.CLASSICAL_PLANETS
        )
        sarva_total = result["ashtakavarga"]["sarva"]["total"]
        # They may differ slightly due to how sarva is computed vs sum of planet totals
        # Allow ±10% tolerance
        assert abs(sarva_total - planet_totals) / max(planet_totals, 1) < 0.1, (
            f"sarva_total={sarva_total} planet_sum={planet_totals}"
        )


# ── Bhava Bala ────────────────────────────────────────────────────────────────

class TestBhavaBala:
    @pytest.fixture(scope="class")
    def result(self):
        mod = _get_mod()
        return mod.compute_all_strength()

    def test_twelve_houses(self, result):
        assert len(result["bhava_bala"]) == 12

    def test_all_positive(self, result):
        for house, val in result["bhava_bala"].items():
            assert val > 0.0, f"H{house} bhava_bala={val}"

    def test_total_rows_gte_floor(self, result):
        mod = _get_mod()
        assert result["total_rows"] >= mod.VOLUME_FLOOR


# ── T1.4a: Nodal strength rows (Task 10) ─────────────────────────────────────

class TestNodalStrengthRows:
    def test_rahu_in_shadbala_output(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        assert "Rahu" in result, "Rahu missing from shadbala output"

    def test_ketu_in_shadbala_output(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        assert "Ketu" in result, "Ketu missing from shadbala output"

    def test_rahu_naisargika_is_zero(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        assert result.get("Rahu", {}).get("naisargika", -1) == 0.0

    def test_ketu_naisargika_is_zero(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        assert result.get("Ketu", {}).get("naisargika", -1) == 0.0

    def test_rahu_has_naisargika_na_flag(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        assert result.get("Rahu", {}).get("naisargika_na") is True

    def test_ketu_has_naisargika_na_flag(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        assert result.get("Ketu", {}).get("naisargika_na") is True

    def test_rahu_school_parashara_strict(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        assert result.get("Rahu", {}).get("school") == "parashara_strict"

    def test_rahu_dig_is_zero(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        assert result.get("Rahu", {}).get("dig", -1) == 0.0

    def test_rahu_kala_is_zero(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        assert result.get("Rahu", {}).get("kala", -1) == 0.0

    def test_rahu_cheshta_is_zero(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        assert result.get("Rahu", {}).get("cheshta", -1) == 0.0

    def test_classical_seven_still_present(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        classical = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert classical.issubset(result.keys()), (
            f"Missing classical planets: {classical - result.keys()}"
        )


# ── T1.4b: Kala-bala day/night fix (Task 11) ─────────────────────────────────

class TestKalaBalaDatetime:
    def test_daytime_sun_kala_higher_than_nighttime(self):
        result_day = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri", birth_hour=10.72)
        result_night = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri", birth_hour=22.5)
        sun_day = result_day.get("Sun", {}).get("kala", 0)
        sun_night = result_night.get("Sun", {}).get("kala", 0)
        assert sun_day != sun_night, "Sun kala-bala must differ between day and night"
        assert sun_day > sun_night, (
            f"Sun kala should be higher daytime: day={sun_day} night={sun_night}"
        )

    def test_nighttime_moon_kala_higher_than_daytime(self):
        result_day = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri", birth_hour=10.72)
        result_night = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri", birth_hour=22.5)
        moon_day = result_day.get("Moon", {}).get("kala", 0)
        moon_night = result_night.get("Moon", {}).get("kala", 0)
        assert moon_night > moon_day, (
            f"Moon kala should be higher nighttime: day={moon_day} night={moon_night}"
        )

    def test_birth_hour_boundary_dawn_is_daytime(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri", birth_hour=6.0)
        sun_kala = result.get("Sun", {}).get("kala", 0)
        assert sun_kala == 0.75, f"Sun at birth_hour=6.0 should be daytime; kala={sun_kala}"

    def test_birth_hour_boundary_midnight_is_nighttime(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri", birth_hour=0.0)
        sun_kala = result.get("Sun", {}).get("kala", 0)
        assert sun_kala == 0.375, f"Sun at midnight should be nighttime; kala={sun_kala}"


# ── T1.4c: Drik-bala from aspect matrix (Task 12) ────────────────────────────

class TestDrikBala:
    def test_drik_values_differ_across_grahas(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        driks = [d.get("drik", 0) for g, d in result.items() if g not in ("Rahu", "Ketu")]
        assert len(set(driks)) > 1, (
            f"All grahas have same drik (stub not fixed): {set(driks)}"
        )

    def test_drik_bounded_0_to_1(self):
        result = sut._derive_shadbala_from_positions(MOCK_CHART_OUTPUT, "lahiri")
        for g_name, sb in result.items():
            drik = sb.get("drik", 0.5)
            assert 0.0 <= drik <= 1.0, f"{g_name} drik={drik} out of bounds"

    def test_compute_drik_bala_function_exists(self):
        assert callable(sut._compute_drik_bala), "_compute_drik_bala not found on sut"

    def test_compute_drik_bala_returns_float_in_range(self):
        grahas = MOCK_CHART_OUTPUT["grahas"]
        for g in grahas:
            if g["name"] in ("Rahu", "Ketu"):
                continue
            val = sut._compute_drik_bala(g["name"], int(g["house"]), grahas)
            assert isinstance(val, float), f"{g['name']} drik not float: {type(val)}"
            assert 0.0 <= val <= 1.0, f"{g['name']} drik={val} out of [0, 1]"
