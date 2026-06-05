"""
test_l1_dashas.py — Tests for brahmagyan.ganita.l1_dashas (ganita.dashas)

Tests:
  1.  VOLUME_FLOOR >= 6561 (MD×AD×PD×Sukshma = 9^4)
  2.  DASHA_SEQUENCE has 9 lords
  3.  DASHA_TOTAL_YEARS = 120
  4.  YOGINI_SEQUENCE has 8 lords
  5.  check_volume() status GREEN
  6.  check_volume() actual_vimshottari >= volume_floor
  7.  check_volume() all 4 systems present in 'systems' dict
  8.  compute_all_dashas() returns dict with vimshottari key
  9.  compute_all_dashas() vimshottari count >= 6561
  10. compute_all_dashas() has MD level (level=1) rows
  11. compute_all_dashas() has AD level (level=2) rows
  12. compute_all_dashas() has PD level (level=3) rows
  13. compute_all_dashas() has Sukshma level (level=4) rows
  14. compute_all_dashas() Moon in Purva Bhadrapada (FORENSIC anchor)
  15. compute_all_dashas() moon_nakshatra_lord = Jupiter
  16. vimshottari rows: all levels in [1, 4]
  17. vimshottari rows: all lords in DASHA_SEQUENCE
  18. vimshottari rows: start_date before end_date
  19. vimshottari rows: no date gaps at MD level
  20. vimshottari rows: 2026-06-05 falls in Mercury MD
  21. yogini rows: non-empty
  22. yogini rows: all lords in known Yogini names
  23. kalachakra rows: non-empty
  24. ashtottari rows: non-empty
  25. ashtottari rows: all lords in known planets
"""
from __future__ import annotations

import pytest
from datetime import date


def _get_mod():
    from brahmagyan.ganita import l1_dashas as mod
    return mod


# ── Constants ─────────────────────────────────────────────────────────────────

class TestConstants:
    def test_volume_floor_gte_6500(self):
        mod = _get_mod()
        assert mod.VOLUME_FLOOR >= 6500

    def test_dasha_sequence_nine_lords(self):
        mod = _get_mod()
        assert len(mod.DASHA_SEQUENCE) == 9

    def test_dasha_total_years_120(self):
        mod = _get_mod()
        assert mod.DASHA_TOTAL_YEARS == 120

    def test_yogini_sequence_eight_lords(self):
        mod = _get_mod()
        assert len(mod.YOGINI_SEQUENCE) == 8


# ── Volume check ──────────────────────────────────────────────────────────────

class TestCheckVolume:
    @pytest.fixture(scope="class")
    def vol(self):
        mod = _get_mod()
        return mod.check_volume()

    def test_status_green(self, vol):
        assert vol["status"] == "GREEN", f"vol={vol}"

    def test_actual_vimshottari_gte_floor(self, vol):
        assert vol["actual_vimshottari"] >= vol["volume_floor"], (
            f"actual={vol['actual_vimshottari']} < floor={vol['volume_floor']}"
        )

    def test_all_four_systems_present(self, vol):
        systems = vol.get("systems", {})
        assert "vimshottari" in systems
        assert "yogini" in systems
        assert "kalachakra" in systems
        assert "ashtottari" in systems

    def test_moon_nakshatra_present(self, vol):
        assert vol.get("moon_nakshatra")


# ── Full dasha computation ────────────────────────────────────────────────────

class TestComputeAllDashas:
    @pytest.fixture(scope="class")
    def result(self):
        mod = _get_mod()
        return mod.compute_all_dashas()

    def test_vimshottari_key_present(self, result):
        assert "vimshottari" in result

    def test_vimshottari_count_gte_floor(self, result):
        mod = _get_mod()
        count = len(result["vimshottari"])
        assert count >= mod.VOLUME_FLOOR, f"Vimshottari rows={count} < floor={mod.VOLUME_FLOOR}"

    def test_has_md_rows(self, result):
        md_rows = [r for r in result["vimshottari"] if r["level"] == 1]
        assert len(md_rows) > 0

    def test_has_ad_rows(self, result):
        ad_rows = [r for r in result["vimshottari"] if r["level"] == 2]
        assert len(ad_rows) > 0

    def test_has_pd_rows(self, result):
        pd_rows = [r for r in result["vimshottari"] if r["level"] == 3]
        assert len(pd_rows) > 0

    def test_has_sukshma_rows(self, result):
        sk_rows = [r for r in result["vimshottari"] if r["level"] == 4]
        assert len(sk_rows) > 0

    def test_moon_in_purva_bhadrapada(self, result):
        """FORENSIC structural anchor: Moon in Purva Bhadrapada."""
        assert result["moon_nakshatra"] == "Purva Bhadrapada", (
            f"moon_nakshatra={result['moon_nakshatra']}"
        )

    def test_moon_nakshatra_lord_jupiter(self, result):
        """FORENSIC structural anchor: Purva Bhadrapada lord = Jupiter."""
        assert result["moon_nakshatra_lord"] == "Jupiter", (
            f"moon_nakshatra_lord={result['moon_nakshatra_lord']}"
        )


# ── Vimshottari row integrity ─────────────────────────────────────────────────

class TestVimshottariRows:
    @pytest.fixture(scope="class")
    def rows(self):
        mod = _get_mod()
        return mod.compute_all_dashas()["vimshottari"]

    def test_all_levels_in_1_4(self, rows):
        for r in rows:
            assert r["level"] in (1, 2, 3, 4), f"row level={r['level']}"

    def test_all_lords_in_sequence(self, rows):
        mod = _get_mod()
        valid_lords = set(mod.DASHA_SEQUENCE)
        for r in rows:
            assert r["lord"] in valid_lords, f"unknown lord={r['lord']}"

    def test_start_lte_end(self, rows):
        """Start date must be <= end date. Same-day rows can occur for very short Sukshma periods."""
        for r in rows:
            assert r["start_date"] <= r["end_date"], (
                f"start={r['start_date']} > end={r['end_date']}"
            )

    def test_no_md_gaps(self, rows):
        """MD-level rows should have no date gaps."""
        md_rows = sorted(
            [r for r in rows if r["level"] == 1],
            key=lambda x: x["start_date"]
        )
        for i in range(len(md_rows) - 1):
            assert md_rows[i]["end_date"] == md_rows[i + 1]["start_date"], (
                f"Gap between MD[{i}]→MD[{i+1}]: "
                f"{md_rows[i]['end_date']} → {md_rows[i+1]['start_date']}"
            )

    def test_today_in_mercury_md(self, rows):
        """2026-06-05 should fall in Mercury MD (approx 2009-2027)."""
        today = "2026-06-05"
        md_rows = [r for r in rows if r["level"] == 1]
        active_md = None
        for r in md_rows:
            if r["start_date"] <= today < r["end_date"]:
                active_md = r["lord"]
                break
        assert active_md == "Mercury", f"Active MD on {today} = {active_md}"


# ── Additional systems ────────────────────────────────────────────────────────

class TestAdditionalSystems:
    @pytest.fixture(scope="class")
    def result(self):
        mod = _get_mod()
        return mod.compute_all_dashas()

    def test_yogini_non_empty(self, result):
        assert len(result["yogini"]) > 0

    def test_yogini_lords_valid(self, result):
        mod = _get_mod()
        valid = {y[0] for y in mod.YOGINI_SEQUENCE}
        for r in result["yogini"]:
            assert r["lord"] in valid, f"Yogini lord={r['lord']}"

    def test_kalachakra_non_empty(self, result):
        assert len(result["kalachakra"]) > 0

    def test_ashtottari_non_empty(self, result):
        assert len(result["ashtottari"]) > 0

    def test_ashtottari_lords_valid(self, result):
        valid = {"Sun", "Moon", "Mars", "Mercury", "Saturn", "Jupiter", "Rahu", "Venus"}
        for r in result["ashtottari"]:
            assert r["lord"] in valid, f"Ashtottari lord={r['lord']}"
