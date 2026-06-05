"""
test_l1_panchanga_birth.py — Tests for brahmagyan.ganita.l1_panchanga_birth

Tests:
  1.  FORENSIC_PANCHANGA has tithi_name = Tritiya
  2.  FORENSIC_PANCHANGA has vara = Ravivara
  3.  FORENSIC_PANCHANGA has nakshatra = Purva Bhadrapada
  4.  FORENSIC_PANCHANGA has yoga = Shiva
  5.  FORENSIC_PANCHANGA has karana = Garaja
  6.  FORENSIC_PANCHANGA has lagna_sign = Aries
  7.  compute_birth_panchanga() returns dict with required keys
  8.  tithi paksha = Shukla (FORENSIC anchor)
  9.  tithi name = Tritiya (FORENSIC anchor)
  10. vara = Ravivara (Sunday — confirmed historical)
  11. nakshatra = Purva Bhadrapada (FORENSIC anchor)
  12. yoga = Shiva (FORENSIC anchor)
  13. karana = Garaja (FORENSIC anchor)
  14. lagna sign = Aries (FORENSIC anchor from MET.LAGNA.SIGN)
  15. forensic_gate_passed = True
  16. forensic_checks list non-empty
  17. all forensic_checks have id/desc/passed/value
  18. forensic_render() returns planet_table with 10 bodies
  19. forensic_render() acceptance_gate passed
  20. forensic_render() Sun in Capricorn
  21. forensic_render() Moon in Purva Bhadrapada
  22. forensic_render() Lagna in Aries
  23. check_facts_store_schema() returns dict with primary_store = chart_facts
  24. check_volume() returns GREEN status
  25. provenance_envelope present in panchanga
"""
from __future__ import annotations

import pytest


def _get_mod():
    from brahmagyan.ganita import l1_panchanga_birth as mod
    return mod


# ── Constants ─────────────────────────────────────────────────────────────────

class TestConstants:
    def test_forensic_tithi_name(self):
        mod = _get_mod()
        assert mod.FORENSIC_PANCHANGA["tithi_name"] == "Tritiya"

    def test_forensic_vara(self):
        mod = _get_mod()
        assert mod.FORENSIC_PANCHANGA["vara"] == "Ravivara"

    def test_forensic_nakshatra(self):
        mod = _get_mod()
        assert mod.FORENSIC_PANCHANGA["nakshatra"] == "Purva Bhadrapada"

    def test_forensic_yoga(self):
        mod = _get_mod()
        assert mod.FORENSIC_PANCHANGA["yoga"] == "Shiva"

    def test_forensic_karana(self):
        mod = _get_mod()
        assert mod.FORENSIC_PANCHANGA["karana"] == "Garaja"

    def test_forensic_lagna_sign(self):
        mod = _get_mod()
        assert mod.FORENSIC_PANCHANGA["lagna_sign"] == "Aries"


# ── Panchanga computation ─────────────────────────────────────────────────────

class TestComputeBirthPanchanga:
    @pytest.fixture(scope="class")
    def panchanga(self):
        mod = _get_mod()
        return mod.compute_birth_panchanga()

    def test_required_keys_present(self, panchanga):
        for key in ("tithi", "vara", "nakshatra", "yoga", "karana", "lagna",
                    "forensic_checks", "forensic_gate_passed", "provenance_envelope"):
            assert key in panchanga, f"missing key: {key}"

    def test_tithi_paksha_shukla(self, panchanga):
        assert panchanga["tithi"]["paksha"] == "Shukla"

    def test_tithi_name_tritiya(self, panchanga):
        assert panchanga["tithi"]["name"] == "Tritiya"

    def test_vara_ravivara(self, panchanga):
        assert panchanga["vara"]["name"] == "Ravivara", (
            f"vara={panchanga['vara']['name']}"
        )

    def test_nakshatra_purva_bhadrapada(self, panchanga):
        assert panchanga["nakshatra"]["name"] == "Purva Bhadrapada", (
            f"nakshatra={panchanga['nakshatra']['name']}"
        )

    def test_yoga_shiva(self, panchanga):
        assert panchanga["yoga"]["name"] == "Shiva", (
            f"yoga={panchanga['yoga']['name']}"
        )

    def test_karana_garaja(self, panchanga):
        assert panchanga["karana"]["name"] == "Garaja", (
            f"karana={panchanga['karana']['name']}"
        )

    def test_lagna_aries(self, panchanga):
        assert panchanga["lagna"]["sign"] == "Aries", (
            f"lagna={panchanga['lagna']['sign']}"
        )

    def test_forensic_gate_passed(self, panchanga):
        failed = [c for c in panchanga["forensic_checks"] if not c["passed"]]
        assert panchanga["forensic_gate_passed"], (
            f"Forensic gate FAILED. Failed checks: {failed}"
        )

    def test_forensic_checks_non_empty(self, panchanga):
        assert len(panchanga["forensic_checks"]) > 0

    def test_forensic_checks_structure(self, panchanga):
        for c in panchanga["forensic_checks"]:
            assert "id" in c
            assert "desc" in c
            assert "passed" in c
            assert "value" in c

    def test_provenance_envelope_present(self, panchanga):
        prov = panchanga["provenance_envelope"]
        assert prov["layer"] == "L1-ganita"
        assert prov["asset"] == "ganita.panchanga"


# ── forensic_render ───────────────────────────────────────────────────────────

class TestForensicRender:
    @pytest.fixture(scope="class")
    def render(self):
        mod = _get_mod()
        return mod.forensic_render()

    def test_planet_table_ten_bodies(self, render):
        assert len(render["planet_table"]) == 10

    def test_acceptance_gate_passed(self, render):
        failed = [c for c in render["acceptance_gate"]["checks"] if not c["passed"]]
        assert render["acceptance_gate"]["passed"], (
            f"forensic_render gate FAILED. Failed checks: {failed}"
        )

    def test_sun_in_capricorn(self, render):
        by_graha = {r["graha"]: r for r in render["planet_table"]}
        sun = by_graha["Sun"]
        assert sun["sign_id"] == 10, f"Sun sign_id={sun['sign_id']}"

    def test_moon_in_purva_bhadrapada(self, render):
        by_graha = {r["graha"]: r for r in render["planet_table"]}
        moon = by_graha["Moon"]
        assert moon["nakshatra_id"] == 25, f"Moon nak_id={moon['nakshatra_id']}"

    def test_lagna_in_aries(self, render):
        by_graha = {r["graha"]: r for r in render["planet_table"]}
        lagna = by_graha.get("Lagna", {})
        assert lagna.get("sign_id") == 1, f"Lagna sign_id={lagna.get('sign_id')}"


# ── Facts store check ────────────────────────────────────────────────────────

class TestFactsStoreCheck:
    @pytest.fixture(scope="class")
    def check(self):
        mod = _get_mod()
        return mod.check_facts_store_schema()

    def test_primary_store_chart_facts(self, check):
        assert check["primary_store"] == "chart_facts"

    def test_status_valid(self, check):
        assert check["status"] in ("GREEN", "AMBER", "RED")


# ── Volume check ──────────────────────────────────────────────────────────────

class TestCheckVolume:
    @pytest.fixture(scope="class")
    def vol(self):
        mod = _get_mod()
        return mod.check_volume()

    def test_status_green(self, vol):
        assert vol["status"] == "GREEN", f"vol={vol}"

    def test_panchanga_forensic_gate_passed(self, vol):
        assert vol["panchanga_forensic_gate"], f"panchanga_forensic_gate=False"

    def test_forensic_render_gate_passed(self, vol):
        assert vol["forensic_render_gate"], f"forensic_render_gate=False"
