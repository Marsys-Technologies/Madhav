"""
test_l1_engine_check.py — Tests for brahmagyan.ganita.l1_engine_check (ganita.engine)

Tests (all pass without live DB):
  1. ENGINE_VERSION is non-empty string
  2. NATIVE_BIRTH_IST is correct date
  3. NATIVE_LAT is Bhubaneswar latitude (~20.3)
  4. NATIVE_LON is Bhubaneswar longitude (~85.8)
  5. run_engine_smoke() returns a dict with required keys
  6. run_engine_smoke() status is GREEN, AMBER, or RED
  7. run_engine_smoke() positions list has exactly 9 grahas
  8. run_engine_smoke() all sidereal longitudes in [0, 360)
  9. run_engine_smoke() Rahu/Ketu 180° apart
  10. run_engine_smoke() Sun in Capricorn (FORENSIC anchor)
  11. run_engine_smoke() Moon in Purva Bhadrapada (FORENSIC anchor)
  12. run_engine_smoke() Lagna in Scorpio (FORENSIC anchor)
  13. run_engine_smoke() checks list non-empty with id/desc/passed/value
  14. run_engine_smoke() provenance_envelope present
  15. run_engine_smoke() dasha_tree has md_count > 0
  16. check_volume() returns dict with volume_floor >= 9
  17. check_volume() actual >= volume_floor when engine is live
  18. check_volume() status in {GREEN, AMBER, RED}
  19. run_engine_smoke() lagna has longitude_sidereal in [0, 360)
  20. run_engine_smoke() all grahas have nakshatra_id in [1, 27]
  21. run_engine_smoke() all grahas have nakshatra_pada in [1, 4]
  22. run_engine_smoke() all grahas have sign_id in [1, 12]
  23. check_volume() source_citation non-empty
  24. run_engine_smoke() native dict has birth_ist, lat, lon keys
"""
from __future__ import annotations

import pytest


def _get_mod():
    from brahmagyan.ganita import l1_engine_check as mod
    return mod


# ── Constants ─────────────────────────────────────────────────────────────────

class TestConstants:
    def test_engine_version_non_empty(self):
        mod = _get_mod()
        assert isinstance(mod.ENGINE_VERSION, str) and len(mod.ENGINE_VERSION) > 0

    def test_native_birth_ist(self):
        mod = _get_mod()
        assert mod.NATIVE_BIRTH_IST.startswith("1984-02-05")

    def test_native_lat_bhubaneswar(self):
        mod = _get_mod()
        assert abs(mod.NATIVE_LAT - 20.2961) < 0.1

    def test_native_lon_bhubaneswar(self):
        mod = _get_mod()
        assert abs(mod.NATIVE_LON - 85.8245) < 0.1

    def test_expected_sun_sign(self):
        mod = _get_mod()
        assert mod.EXPECTED_SUN_SIGN == "Capricorn"
        assert mod.EXPECTED_SUN_SIGN_ID == 10

    def test_expected_moon_nakshatra(self):
        mod = _get_mod()
        assert mod.EXPECTED_MOON_NAKSHATRA == "Purva Bhadrapada"
        assert mod.EXPECTED_MOON_NAKSHATRA_ID == 25

    def test_expected_lagna_sign(self):
        mod = _get_mod()
        assert mod.EXPECTED_LAGNA_SIGN == "Aries"
        assert mod.EXPECTED_LAGNA_SIGN_ID == 1


# ── Smoke test ────────────────────────────────────────────────────────────────

class TestEngineSmoke:
    @pytest.fixture(scope="class")
    def result(self):
        mod = _get_mod()
        return mod.run_engine_smoke()

    def test_returns_dict(self, result):
        assert isinstance(result, dict)

    def test_required_keys(self, result):
        for key in ("status", "engine_version", "checks", "positions", "lagna",
                    "dasha_tree", "provenance_envelope", "native"):
            assert key in result, f"missing key: {key}"

    def test_status_valid(self, result):
        assert result["status"] in ("GREEN", "AMBER", "RED")

    def test_status_green(self, result):
        """Engine should be GREEN for native birth data with pyswisseph."""
        assert result["status"] == "GREEN", (
            f"Engine status is {result['status']}. "
            f"Failed checks: {[c for c in result['checks'] if not c['passed']]}"
        )

    def test_positions_nine_grahas(self, result):
        assert len(result["positions"]) == 9

    def test_all_longitudes_in_range(self, result):
        for p in result["positions"]:
            assert 0.0 <= p["sidereal_longitude"] < 360.0, (
                f"{p['name']} lon={p['sidereal_longitude']}"
            )

    def test_rahu_ketu_180_apart(self, result):
        by_name = {p["name"]: p for p in result["positions"]}
        sep = abs(
            by_name["Rahu"]["sidereal_longitude"] - by_name["Ketu"]["sidereal_longitude"]
        ) % 360.0
        sep = min(sep, 360.0 - sep)
        assert abs(sep - 180.0) < 0.5, f"Rahu/Ketu separation = {sep}"

    def test_sun_in_capricorn(self, result):
        by_name = {p["name"]: p for p in result["positions"]}
        sun = by_name["Sun"]
        assert sun["sign_id"] == 10, f"Sun sign_id={sun['sign_id']} sign={sun['sign']}"

    def test_moon_in_purva_bhadrapada(self, result):
        by_name = {p["name"]: p for p in result["positions"]}
        moon = by_name["Moon"]
        assert moon["nakshatra_id"] == 25, (
            f"Moon nak_id={moon['nakshatra_id']} nak={moon['nakshatra']}"
        )

    def test_lagna_in_aries(self, result):
        """FORENSIC v6.0 MET.LAGNA.SIGN = Aries, MET.LAGNA.DEG = 12°23'55\" (Lahiri)."""
        lagna = result["lagna"]
        if not lagna:
            pytest.skip("Lagna computation unavailable")
        assert lagna["sign_id"] == 1, f"Lagna sign_id={lagna['sign_id']} sign={lagna['sign']}"

    def test_checks_list_non_empty(self, result):
        checks = result["checks"]
        assert len(checks) > 0
        for c in checks:
            assert "id" in c
            assert "desc" in c
            assert "passed" in c
            assert "value" in c

    def test_provenance_envelope_present(self, result):
        prov = result["provenance_envelope"]
        assert "source" in prov
        assert "ayanamsha" in prov
        assert "layer" in prov
        assert prov["layer"] == "L1-ganita"

    def test_dasha_tree_has_md_count(self, result):
        dt = result["dasha_tree"]
        assert dt.get("md_count", 0) > 0

    def test_lagna_longitude_in_range(self, result):
        lagna = result["lagna"]
        if not lagna:
            pytest.skip("Lagna computation unavailable")
        assert 0.0 <= lagna["longitude_sidereal"] < 360.0

    def test_all_grahas_nakshatra_id_in_range(self, result):
        for p in result["positions"]:
            assert 1 <= p["nakshatra_id"] <= 27, (
                f"{p['name']} nakshatra_id={p['nakshatra_id']}"
            )

    def test_all_grahas_nakshatra_pada_in_range(self, result):
        for p in result["positions"]:
            assert 1 <= p["nakshatra_pada"] <= 4, (
                f"{p['name']} nakshatra_pada={p['nakshatra_pada']}"
            )

    def test_all_grahas_sign_id_in_range(self, result):
        for p in result["positions"]:
            assert 1 <= p["sign_id"] <= 12, (
                f"{p['name']} sign_id={p['sign_id']}"
            )

    def test_native_dict_keys(self, result):
        native = result["native"]
        assert "birth_ist" in native
        assert "lat" in native
        assert "lon" in native


# ── Volume check ──────────────────────────────────────────────────────────────

class TestCheckVolume:
    @pytest.fixture(scope="class")
    def vol(self):
        mod = _get_mod()
        return mod.check_volume()

    def test_volume_floor_gte_9(self, vol):
        assert vol["volume_floor"] >= 9

    def test_actual_gte_floor(self, vol):
        assert vol["actual"] >= vol["volume_floor"], (
            f"actual={vol['actual']} < floor={vol['volume_floor']}"
        )

    def test_status_valid(self, vol):
        assert vol["status"] in ("GREEN", "AMBER", "RED")

    def test_status_green(self, vol):
        assert vol["status"] == "GREEN", f"vol status={vol['status']}"

    def test_source_citation_non_empty(self, vol):
        assert vol.get("source_citation") and len(vol["source_citation"]) > 0
