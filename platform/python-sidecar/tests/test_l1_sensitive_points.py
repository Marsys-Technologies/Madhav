"""
test_l1_sensitive_points.py — Tests for brahmagyan.ganita.l1_sensitive_points

Tests:
  1.  VOLUME_FLOOR >= 27 (6 + 5 + 4 + 12)
  2.  check_volume() status GREEN
  3.  check_volume() actual >= volume_floor
  4.  check_volume() breakdown has 6 upagrahas
  5.  check_volume() breakdown has 5 special_lagnas
  6.  check_volume() breakdown has 4 sahams
  7.  check_volume() breakdown has 12 arudhas
  8.  compute_all_sensitive_points() returns dict with required keys
  9.  upagrahas has exactly 6 entries
  10. upagraha names: Mandi, Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu
  11. all upagraha longitudes in [0, 360)
  12. all upagraha sign_id in [1, 12]
  13. special_lagnas has exactly 5 entries
  14. special_lagna names: Hora_Lagna, Ghati_Lagna, Bhava_Lagna, Varnada_Lagna, Sree_Lagna
  15. all special_lagna longitudes in [0, 360)
  16. sahams has exactly 4 entries
  17. saham names: Punya_Saham, Vidya_Saham, Rajya_Saham, Vivaha_Saham
  18. all saham longitudes in [0, 360)
  19. arudhas has exactly 12 entries (A1–A12)
  20. all arudha sign_id in [1, 12]
  21. arudha A1 (Lagna Pada) has sign attribute
  22. provenance_envelope present
  23. Dhuma = Sun + ~133°20'
  24. Parivesha = Vyatipata + 180° (mod 360)
  25. total_rows = 27 (6+5+4+12)
"""
from __future__ import annotations

import pytest


def _get_mod():
    from brahmagyan.ganita import l1_sensitive_points as mod
    return mod


# ── Constants ─────────────────────────────────────────────────────────────────

class TestConstants:
    def test_volume_floor_gte_27(self):
        mod = _get_mod()
        assert mod.VOLUME_FLOOR >= 27


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

    def test_six_upagrahas(self, vol):
        assert vol["breakdown"]["upagrahas"] == 6

    def test_five_special_lagnas(self, vol):
        assert vol["breakdown"]["special_lagnas"] == 5

    def test_four_sahams(self, vol):
        assert vol["breakdown"]["sahams"] == 4

    def test_twelve_arudhas(self, vol):
        assert vol["breakdown"]["arudhas"] == 12


# ── Full sensitive points computation ────────────────────────────────────────

class TestComputeAllSensitivePoints:
    @pytest.fixture(scope="class")
    def result(self):
        mod = _get_mod()
        return mod.compute_all_sensitive_points()

    def test_required_keys_present(self, result):
        for key in ("upagrahas", "special_lagnas", "sahams", "arudhas",
                    "total_rows", "provenance_envelope"):
            assert key in result, f"missing key: {key}"

    def test_total_rows_equals_27(self, result):
        assert result["total_rows"] == 27

    def test_provenance_envelope(self, result):
        prov = result["provenance_envelope"]
        assert prov["layer"] == "L1-ganita"
        assert prov["asset"] == "ganita.sensitive_points"


# ── Upagrahas ─────────────────────────────────────────────────────────────────

class TestUpagrahas:
    @pytest.fixture(scope="class")
    def upagrahas(self):
        mod = _get_mod()
        return mod.compute_all_sensitive_points()["upagrahas"]

    def test_six_upagrahas(self, upagrahas):
        assert len(upagrahas) == 6

    def test_expected_names(self, upagrahas):
        expected = {"Mandi", "Dhuma", "Vyatipata", "Parivesha", "Indrachapa", "Upaketu"}
        assert set(upagrahas.keys()) == expected

    def test_all_longitudes_in_range(self, upagrahas):
        for name, data in upagrahas.items():
            assert 0.0 <= data["longitude"] < 360.0, f"{name} lon={data['longitude']}"

    def test_all_sign_ids_in_range(self, upagrahas):
        for name, data in upagrahas.items():
            assert 1 <= data["sign_id"] <= 12, f"{name} sign_id={data['sign_id']}"

    def test_dhuma_parivesha_relationship(self, upagrahas):
        """Parivesha = Vyatipata + 180° (mod 360)."""
        vy = upagrahas["Vyatipata"]["longitude"]
        pa = upagrahas["Parivesha"]["longitude"]
        expected = (vy + 180.0) % 360.0
        assert abs(pa - expected) < 0.1, f"Parivesha={pa} Vyatipata+180={expected}"

    def test_dhuma_offset_from_sun(self, upagrahas):
        """Dhuma ≈ Sun + 133°20' = Sun + 133.333°."""
        from brahmagyan.ganita.l1_positions import compute_positions_all_bodies, _birth_jd_utc
        jd = _birth_jd_utc()
        positions = {p["name"]: p for p in compute_positions_all_bodies(jd, "lahiri")}
        sun_lon = positions["Sun"]["sidereal_longitude"]
        dhuma_lon = upagrahas["Dhuma"]["longitude"]
        expected_dhuma = (sun_lon + 133 + 20.0/60.0) % 360.0
        assert abs(dhuma_lon - expected_dhuma) < 0.5, (
            f"Dhuma={dhuma_lon} expected={expected_dhuma}"
        )


# ── Special Lagnas ────────────────────────────────────────────────────────────

class TestSpecialLagnas:
    @pytest.fixture(scope="class")
    def special_lagnas(self):
        mod = _get_mod()
        return mod.compute_all_sensitive_points()["special_lagnas"]

    def test_five_special_lagnas(self, special_lagnas):
        assert len(special_lagnas) == 5

    def test_expected_names(self, special_lagnas):
        expected = {"Hora_Lagna", "Ghati_Lagna", "Bhava_Lagna", "Varnada_Lagna", "Sree_Lagna"}
        assert set(special_lagnas.keys()) == expected

    def test_all_longitudes_in_range(self, special_lagnas):
        for name, data in special_lagnas.items():
            assert 0.0 <= data["longitude"] < 360.0, f"{name} lon={data['longitude']}"

    def test_computation_tag_present(self, special_lagnas):
        for name, data in special_lagnas.items():
            assert "computation" in data, f"{name} missing computation tag"


# ── Sahams ────────────────────────────────────────────────────────────────────

class TestSahams:
    @pytest.fixture(scope="class")
    def sahams(self):
        mod = _get_mod()
        return mod.compute_all_sensitive_points()["sahams"]

    def test_four_sahams(self, sahams):
        assert len(sahams) == 4

    def test_expected_names(self, sahams):
        expected = {"Punya_Saham", "Vidya_Saham", "Rajya_Saham", "Vivaha_Saham"}
        assert set(sahams.keys()) == expected

    def test_all_longitudes_in_range(self, sahams):
        for name, data in sahams.items():
            assert 0.0 <= data["longitude"] < 360.0, f"{name} lon={data['longitude']}"

    def test_formula_present(self, sahams):
        for name, data in sahams.items():
            assert "formula" in data, f"{name} missing formula"


# ── Arudhas ───────────────────────────────────────────────────────────────────

class TestArudhas:
    @pytest.fixture(scope="class")
    def arudhas(self):
        mod = _get_mod()
        return mod.compute_all_sensitive_points()["arudhas"]

    def test_twelve_arudhas(self, arudhas):
        assert len(arudhas) == 12

    def test_a1_through_a12_present(self, arudhas):
        for i in range(1, 13):
            assert f"A{i}" in arudhas, f"A{i} missing"

    def test_all_sign_ids_in_range(self, arudhas):
        for name, data in arudhas.items():
            assert 1 <= data["sign_id"] <= 12, f"{name} sign_id={data['sign_id']}"

    def test_a1_has_sign(self, arudhas):
        assert "sign" in arudhas["A1"]

    def test_all_have_house_lord(self, arudhas):
        for name, data in arudhas.items():
            assert "house_lord" in data, f"{name} missing house_lord"
