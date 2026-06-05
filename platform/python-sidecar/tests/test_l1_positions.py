"""
test_l1_positions.py — Tests for brahmagyan.ganita.l1_positions (ganita.positions)

Tests:
  1.  VOLUME_FLOOR >= 50 (5 ayanamshas × 10 bodies)
  2.  AYANAMSHAS list has exactly 5 entries
  3.  All 5 ayanamsha keys present: lahiri, raman, kp, true_citra, yukteshwar
  4.  GRAHA_NAMES has exactly 10 entries (9 grahas + Lagna)
  5.  check_volume() returns GREEN status
  6.  check_volume() actual >= volume_floor
  7.  check_volume() all 5 ayanamshas in ayanamshas_ok
  8.  compute_positions_all_bodies: Lahiri returns 10 bodies
  9.  compute_positions_all_bodies: all sidereal longitudes in [0, 360)
  10. compute_positions_all_bodies: all sign_id in [1, 12]
  11. compute_positions_all_bodies: all nakshatra_id in [1, 27]
  12. compute_positions_all_bodies: all nakshatra_pada in [1, 4]
  13. compute_positions_all_bodies: Sun in Capricorn under Lahiri (FORENSIC anchor)
  14. compute_positions_all_bodies: Moon in Purva Bhadrapada under Lahiri (FORENSIC anchor)
  15. compute_positions_all_bodies: Rahu/Ketu 180° apart under Lahiri
  16. compute_all_ayanamshas: returns dict with 5 keys
  17. compute_all_ayanamshas: total rows = 50 (5 × 10)
  18. compute_all_ayanamshas: Raman ayanamsha produces 10 bodies
  19. compute_all_ayanamshas: KP ayanamsha produces 10 bodies
  20. compute_all_ayanamshas: True Citra ayanamsha produces 10 bodies
  21. compute_all_ayanamshas: Yukteshwar ayanamsha produces 10 bodies
  22. compute_all_ayanamshas: Sun sign differs between at least 2 ayanamshas OR is consistent
  23. compute_all_ayanamshas: each body has house field
  24. Lagna is included in each ayanamsha result
  25. compute_positions_all_bodies: Lagna longitude in [0, 360)
"""
from __future__ import annotations

import pytest


def _get_mod():
    from brahmagyan.ganita import l1_positions as mod
    return mod


def _jd():
    mod = _get_mod()
    return mod._birth_jd_utc()


# ── Constants ─────────────────────────────────────────────────────────────────

class TestConstants:
    def test_volume_floor_gte_50(self):
        mod = _get_mod()
        assert mod.VOLUME_FLOOR >= 50

    def test_five_ayanamshas(self):
        mod = _get_mod()
        assert len(mod.AYANAMSHAS) == 5

    def test_ayanamsha_keys_present(self):
        mod = _get_mod()
        keys = {a["key"] for a in mod.AYANAMSHAS}
        assert "lahiri" in keys
        assert "raman" in keys
        assert "kp" in keys
        assert "true_citra" in keys
        assert "yukteshwar" in keys

    def test_graha_names_ten(self):
        mod = _get_mod()
        assert len(mod.GRAHA_NAMES) == 10
        assert "Lagna" in mod.GRAHA_NAMES


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

    def test_all_five_ayanamshas_ok(self, vol):
        ok = set(vol.get("ayanamshas_ok", []))
        assert "lahiri" in ok
        assert "raman" in ok
        assert "kp" in ok
        assert "true_citra" in ok
        assert "yukteshwar" in ok

    def test_source_citation_present(self, vol):
        assert vol.get("source_citation")


# ── Single ayanamsha positions ────────────────────────────────────────────────

class TestSingleAyanamsha:
    @pytest.fixture(scope="class")
    def lahiri_positions(self):
        mod = _get_mod()
        jd = _jd()
        return mod.compute_positions_all_bodies(jd, "lahiri")

    def test_ten_bodies_lahiri(self, lahiri_positions):
        assert len(lahiri_positions) == 10

    def test_all_longitudes_in_range(self, lahiri_positions):
        for p in lahiri_positions:
            assert 0.0 <= p["sidereal_longitude"] < 360.0, (
                f"{p['name']} lon={p['sidereal_longitude']}"
            )

    def test_all_sign_ids_in_range(self, lahiri_positions):
        for p in lahiri_positions:
            assert 1 <= p["sign_id"] <= 12, f"{p['name']} sign_id={p['sign_id']}"

    def test_all_nakshatra_ids_in_range(self, lahiri_positions):
        for p in lahiri_positions:
            if p["name"] == "Lagna":
                continue  # Lagna nakshatra is derived from ascendant
            assert 1 <= p["nakshatra_id"] <= 27, (
                f"{p['name']} nakshatra_id={p['nakshatra_id']}"
            )

    def test_all_nakshatra_pada_in_range(self, lahiri_positions):
        for p in lahiri_positions:
            assert 1 <= p["nakshatra_pada"] <= 4, (
                f"{p['name']} pada={p['nakshatra_pada']}"
            )

    def test_sun_in_capricorn_lahiri(self, lahiri_positions):
        """FORENSIC structural anchor: Sun in Capricorn (sign_id=10) under Lahiri."""
        by_name = {p["name"]: p for p in lahiri_positions}
        sun = by_name["Sun"]
        assert sun["sign_id"] == 10, f"Sun sign_id={sun['sign_id']} sign={sun['sign']}"

    def test_moon_in_purva_bhadrapada_lahiri(self, lahiri_positions):
        """FORENSIC structural anchor: Moon in Purva Bhadrapada (nak_id=25) under Lahiri."""
        by_name = {p["name"]: p for p in lahiri_positions}
        moon = by_name["Moon"]
        assert moon["nakshatra_id"] == 25, (
            f"Moon nak_id={moon['nakshatra_id']} nak={moon['nakshatra']}"
        )

    def test_rahu_ketu_180_apart_lahiri(self, lahiri_positions):
        by_name = {p["name"]: p for p in lahiri_positions}
        rahu = by_name["Rahu"]["sidereal_longitude"]
        ketu = by_name["Ketu"]["sidereal_longitude"]
        sep = abs(rahu - ketu) % 360.0
        sep = min(sep, 360.0 - sep)
        assert abs(sep - 180.0) < 0.5, f"Rahu/Ketu sep={sep}"

    def test_lagna_in_result(self, lahiri_positions):
        names = [p["name"] for p in lahiri_positions]
        assert "Lagna" in names

    def test_lagna_longitude_in_range(self, lahiri_positions):
        by_name = {p["name"]: p for p in lahiri_positions}
        lagna = by_name.get("Lagna", {})
        assert 0.0 <= lagna.get("sidereal_longitude", 0) < 360.0


# ── All ayanamshas ────────────────────────────────────────────────────────────

class TestAllAyanamshas:
    @pytest.fixture(scope="class")
    def all_positions(self):
        mod = _get_mod()
        jd = _jd()
        return mod.compute_all_ayanamshas(jd)

    def test_five_keys_returned(self, all_positions):
        assert len(all_positions) == 5

    def test_total_fifty_rows(self, all_positions):
        total = sum(len(v) for v in all_positions.values())
        assert total == 50, f"total={total}"

    def test_raman_ten_bodies(self, all_positions):
        assert len(all_positions["raman"]) == 10

    def test_kp_ten_bodies(self, all_positions):
        assert len(all_positions["kp"]) == 10

    def test_true_citra_ten_bodies(self, all_positions):
        assert len(all_positions["true_citra"]) == 10

    def test_yukteshwar_ten_bodies(self, all_positions):
        assert len(all_positions["yukteshwar"]) == 10

    def test_all_bodies_have_house(self, all_positions):
        for aya_key, positions in all_positions.items():
            for p in positions:
                assert "house" in p, f"{aya_key}/{p['name']} missing 'house'"

    def test_ayanamsha_keys_tagged(self, all_positions):
        for aya_key, positions in all_positions.items():
            for p in positions:
                assert p["ayanamsha_key"] == aya_key

    def test_lahiri_lagna_in_aries(self, all_positions):
        """FORENSIC v6.0 MET.LAGNA.SIGN = Aries under Lahiri."""
        lahiri = {p["name"]: p for p in all_positions["lahiri"]}
        lagna = lahiri.get("Lagna", {})
        assert lagna.get("sign_id") == 1, f"Lagna sign_id={lagna.get('sign_id')}"

    def test_ayanamsha_values_differ(self, all_positions):
        """Five ayanamshas should produce different ayanamsha offset values."""
        aya_values = set()
        for aya_key, positions in all_positions.items():
            if positions:
                aya_values.add(round(positions[0]["ayanamsha_value"], 2))
        assert len(aya_values) >= 3, f"Only {len(aya_values)} distinct ayanamsha values"
