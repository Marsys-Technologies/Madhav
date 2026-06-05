"""
test_l1_divisionals.py — Tests for brahmagyan.ganita.l1_divisionals (ganita.divisionals)

Tests:
  1.  VOLUME_FLOOR >= 160 (16 divisionals × 10 bodies)
  2.  KEY_DIVISIONALS has exactly 16 entries
  3.  D1 present in KEY_DIVISIONALS
  4.  D9 (Navamsha) present in KEY_DIVISIONALS
  5.  D60 (Shashtiamsha) present in KEY_DIVISIONALS
  6.  check_volume() returns GREEN status
  7.  check_volume() actual >= volume_floor
  8.  check_volume() 16 divisionals in result
  9.  compute_all_divisionals() returns dict with divisionals key
  10. compute_all_divisionals() total_rows >= 160
  11. compute_all_divisionals() D1 contains all 10 bodies
  12. compute_all_divisionals() D9 contains all 10 bodies
  13. compute_all_divisionals() D60 contains all 10 bodies
  14. compute_all_divisionals() all sign_id in [1, 12] for D1
  15. compute_all_divisionals() all house in [1, 12] for D1
  16. compute_divisional_sign D1: Sun in Capricorn (sign_id=10)
  17. compute_divisional_sign D9: navamsha computation gives valid sign
  18. compute_divisional_sign D3: drekkana in valid range
  19. compute_divisional_sign D2: hora = Leo(5) or Cancer(4) only
  20. compute_house_in_divisional: body=lagna gives house=1
  21. compute_house_in_divisional: wrap-around correct
  22. compute_all_divisionals() D9 Sun sign in [1,12]
  23. compute_all_divisionals() each divisional has lagna_sign_id in [1,12]
  24. compute_all_divisionals() D1 Sun is in Capricorn (FORENSIC anchor)
  25. compute_all_divisionals() ayanamsha is lahiri
"""
from __future__ import annotations

import pytest


def _get_mod():
    from brahmagyan.ganita import l1_divisionals as mod
    return mod


# ── Constants ─────────────────────────────────────────────────────────────────

class TestConstants:
    def test_volume_floor_gte_160(self):
        mod = _get_mod()
        assert mod.VOLUME_FLOOR >= 160

    def test_sixteen_key_divisionals(self):
        mod = _get_mod()
        assert len(mod.KEY_DIVISIONALS) == 16

    def test_d1_present(self):
        mod = _get_mod()
        assert 1 in mod.KEY_DIVISIONALS

    def test_d9_present(self):
        mod = _get_mod()
        assert 9 in mod.KEY_DIVISIONALS

    def test_d60_present(self):
        mod = _get_mod()
        assert 60 in mod.KEY_DIVISIONALS


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

    def test_sixteen_divisionals_computed(self, vol):
        assert len(vol.get("divisionals_computed", [])) == 16


# ── Divisional sign formulas ──────────────────────────────────────────────────

class TestDivisionalSign:
    def test_d1_capricorn_for_sun(self):
        """Sun at ~285° sidereal = Capricorn (sign_id=10). Capricorn covers 270-300°."""
        mod = _get_mod()
        # Capricorn (sign 10) covers 270-300 degrees sidereal
        sun_lon = 285.0  # mid-Capricorn
        sign = mod.compute_divisional_sign(sun_lon, 1)
        assert sign == 10, f"D1 Sun sign={sign} (expected Capricorn=10)"

    def test_d9_navamsha_valid_range(self):
        mod = _get_mod()
        # Test for Moon at ~322° (Aquarius/Purva Bhadrapada)
        moon_lon = 322.0
        sign = mod.compute_divisional_sign(moon_lon, 9)
        assert 1 <= sign <= 12, f"D9 Moon sign={sign}"

    def test_d3_drekkana_valid_range(self):
        mod = _get_mod()
        for lon in [15.0, 45.0, 90.0, 180.0, 270.0, 305.0]:
            sign = mod.compute_divisional_sign(lon, 3)
            assert 1 <= sign <= 12, f"D3 lon={lon} sign={sign}"

    def test_d2_hora_cancer_or_leo_only(self):
        mod = _get_mod()
        for lon in [5.0, 20.0, 35.0, 50.0, 65.0, 80.0, 95.0]:
            sign = mod.compute_divisional_sign(lon, 2)
            assert sign in (4, 5), f"D2 lon={lon} sign={sign} (expected Cancer=4 or Leo=5)"

    def test_d9_standard_cases(self):
        """D9 for Aries 0° = Aries start → Aries navamsha 1 = Aries (1)."""
        mod = _get_mod()
        sign = mod.compute_divisional_sign(0.1, 9)  # 0° Aries
        assert sign == 1, f"D9 Aries-start navamsha = Aries expected, got {sign}"

    def test_d30_trimshamsha_valid_range(self):
        mod = _get_mod()
        for lon in [2.0, 7.0, 14.0, 22.0, 28.0, 35.0, 42.0]:
            sign = mod.compute_divisional_sign(lon, 30)
            assert 1 <= sign <= 12, f"D30 lon={lon} sign={sign}"

    def test_d60_valid_range(self):
        mod = _get_mod()
        for lon in [0.5, 15.0, 90.0, 180.0, 270.0, 359.0]:
            sign = mod.compute_divisional_sign(lon, 60)
            assert 1 <= sign <= 12, f"D60 lon={lon} sign={sign}"

    def test_house_body_at_lagna_gives_house_1(self):
        mod = _get_mod()
        assert mod.compute_house_in_divisional(5, 5) == 1

    def test_house_wrap_around(self):
        mod = _get_mod()
        # Body in Aries (1), Lagna in Taurus (2): house = (1-2)%12+1 = 12
        assert mod.compute_house_in_divisional(1, 2) == 12


# ── Full divisional computation ───────────────────────────────────────────────

class TestComputeAllDivisionals:
    @pytest.fixture(scope="class")
    def result(self):
        mod = _get_mod()
        return mod.compute_all_divisionals()

    def test_divisionals_key_present(self, result):
        assert "divisionals" in result

    def test_total_rows_gte_160(self, result):
        assert result["total_rows"] >= 160, f"total_rows={result['total_rows']}"

    def test_d1_has_ten_bodies(self, result):
        assert len(result["divisionals"]["D1"]["bodies"]) == 10

    def test_d9_has_ten_bodies(self, result):
        assert len(result["divisionals"]["D9"]["bodies"]) == 10

    def test_d60_has_ten_bodies(self, result):
        assert len(result["divisionals"]["D60"]["bodies"]) == 10

    def test_d1_all_sign_ids_in_range(self, result):
        for name, body in result["divisionals"]["D1"]["bodies"].items():
            assert 1 <= body["sign_id"] <= 12, f"D1/{name} sign_id={body['sign_id']}"

    def test_d1_all_houses_in_range(self, result):
        for name, body in result["divisionals"]["D1"]["bodies"].items():
            assert 1 <= body["house"] <= 12, f"D1/{name} house={body['house']}"

    def test_d1_sun_in_capricorn(self, result):
        """FORENSIC structural anchor: D1 Sun in Capricorn (sign_id=10)."""
        sun = result["divisionals"]["D1"]["bodies"]["Sun"]
        assert sun["sign_id"] == 10, f"D1 Sun sign_id={sun['sign_id']} sign={sun['sign']}"

    def test_d9_sun_sign_valid(self, result):
        sun = result["divisionals"]["D9"]["bodies"]["Sun"]
        assert 1 <= sun["sign_id"] <= 12

    def test_all_divisionals_have_lagna_sign(self, result):
        for d_key, d_data in result["divisionals"].items():
            assert 1 <= d_data["lagna_sign_id"] <= 12, (
                f"{d_key} lagna_sign_id={d_data['lagna_sign_id']}"
            )

    def test_ayanamsha_is_lahiri(self, result):
        assert result["ayanamsha"] == "lahiri"

    def test_sixteen_divisionals_present(self, result):
        assert len(result["divisionals"]) == 16
