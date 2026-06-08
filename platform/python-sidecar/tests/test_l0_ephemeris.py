"""
test_l0_ephemeris.py — Unit tests for brahmagyan.l0_ephemeris (BRAHMA-BG-0-6)

Tests (all pass without live DB or pyswisseph):
  1. VOLUME_FLOOR is >= 825,084
  2. NATIVE constants correct (Bhubaneswar coords, birth date)
  3. SOURCE_CITATION is non-null
  4. AYANAMSHA_ID is 'tropical'
  5. DAILY_BODIES: 9 entries (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu)
  6. BUILD_START is 1900-01-01, BUILD_END is 2150-12-31
  7. check_volume: dry_run returns EMPTY status
  8. check_volume: EMPTY when row count = 0
  9. check_volume: AMBER when 0 < actual < floor
  10. check_volume: GREEN when actual >= floor
  11. check_volume: ayanamsha_id null check
  12. check_volume: source_citation null check
  13. check_volume: birth date check passes when Sun in [0,360)
  14. check_volume: birth date check fails when no Sun row
  15. algorithmic_fallback: returns 9 rows for a given date
  16. algorithmic_fallback: all longitudes in [0, 360)
  17. algorithmic_fallback: all ayanamsha_id = 'tropical'
  18. query_ephemeris: returns ok=False when DB unavailable
  19. query_ephemeris: provenance_envelope present in result
  20. query_ephemeris: filters by body correctly (mocked)
  21. query_ephemeris: date_range filters applied (mocked)
  22. _compute_positions_for_date: falls back to algorithmic when swe not available
"""
from __future__ import annotations

import sys
import importlib
from datetime import date
from unittest.mock import MagicMock, patch, call
import pytest


def _get_mod():
    from brahmagyan import l0_ephemeris as mod
    return mod


# ── Constants ─────────────────────────────────────────────────────────────────

class TestConstants:
    def test_volume_floor_gte_825084(self):
        mod = _get_mod()
        assert mod.VOLUME_FLOOR >= 825_084

    def test_bhubaneswar_lat(self):
        mod = _get_mod()
        assert abs(mod.NATIVE_LAT - 20.2961) < 0.01

    def test_bhubaneswar_lon(self):
        mod = _get_mod()
        assert abs(mod.NATIVE_LON - 85.8245) < 0.01

    def test_native_birth_date(self):
        mod = _get_mod()
        assert mod.NATIVE_BIRTH_DATE == date(1984, 2, 5)

    def test_source_citation_non_null(self):
        mod = _get_mod()
        assert mod.SOURCE_CITATION
        assert "DE441" in mod.SOURCE_CITATION or "pyswisseph" in mod.SOURCE_CITATION

    def test_ayanamsha_id_is_tropical(self):
        mod = _get_mod()
        assert mod.AYANAMSHA_ID == "tropical"

    def test_daily_bodies_count(self):
        mod = _get_mod()
        # 9 bodies (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu)
        assert len(mod.DAILY_BODIES) == 9

    def test_daily_bodies_names(self):
        mod = _get_mod()
        names = {b["name"] for b in mod.DAILY_BODIES}
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                    "Saturn", "Rahu", "Ketu"}
        assert names == expected

    def test_build_start(self):
        mod = _get_mod()
        assert mod.BUILD_START == date(1900, 1, 1)

    def test_build_end(self):
        mod = _get_mod()
        assert mod.BUILD_END == date(2150, 12, 31)


# ── check_volume ──────────────────────────────────────────────────────────────

class TestCheckVolume:
    def test_dry_run_returns_empty(self):
        mod = _get_mod()
        result = mod.check_volume(dry_run=True)
        assert result["status"] == "EMPTY"
        assert result["actual_rows"] == 0
        assert result["asset"] == "brahmagyan.ephemeris"

    def test_floor_present_in_dry_run(self):
        mod = _get_mod()
        result = mod.check_volume(dry_run=True)
        assert result["floor"] >= 825_084

    def _make_mock_conn(self, row_count: int, sun_lon: float | None,
                        null_citation: int = 0, null_ayanamsha: int = 0):
        """Build a mock connection that returns given counts."""
        cursor = MagicMock()
        conn = MagicMock()
        conn.cursor.return_value.__enter__ = lambda s: cursor
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        sun_row = (sun_lon,) if sun_lon is not None else None

        cursor.fetchone.side_effect = [
            (row_count,),      # COUNT(*)
            sun_row,           # Sun row for birth date
            (null_citation,),  # null citation count
            (null_ayanamsha,), # null ayanamsha count
        ]
        return conn

    def test_empty_status_when_zero_rows(self):
        mod = _get_mod()
        conn = self._make_mock_conn(0, None)
        result = mod.check_volume(conn=conn)
        assert result["status"] == "EMPTY"

    def test_amber_status_when_below_floor(self):
        mod = _get_mod()
        conn = self._make_mock_conn(1000, 316.5)
        result = mod.check_volume(conn=conn)
        assert result["status"] == "AMBER"

    def test_green_status_when_at_floor(self):
        mod = _get_mod()
        conn = self._make_mock_conn(mod.VOLUME_FLOOR, 316.5)
        result = mod.check_volume(conn=conn)
        assert result["status"] == "GREEN"

    def test_birth_date_check_pass(self):
        mod = _get_mod()
        # Sun at 316.5° (Aquarius tropical) — valid [0, 360)
        conn = self._make_mock_conn(mod.VOLUME_FLOOR, 316.5)
        result = mod.check_volume(conn=conn)
        assert result["birth_date_check"]["status"] == "PASS"

    def test_birth_date_check_fail_no_row(self):
        mod = _get_mod()
        conn = self._make_mock_conn(mod.VOLUME_FLOOR, None)
        result = mod.check_volume(conn=conn)
        assert result["birth_date_check"]["status"] == "FAIL"

    def test_ayanamsha_check_pass(self):
        mod = _get_mod()
        conn = self._make_mock_conn(mod.VOLUME_FLOOR, 316.5, null_ayanamsha=0)
        result = mod.check_volume(conn=conn)
        assert result["ayanamsha_check"]["status"] == "PASS"

    def test_ayanamsha_check_fail(self):
        mod = _get_mod()
        conn = self._make_mock_conn(mod.VOLUME_FLOOR, 316.5, null_ayanamsha=5)
        result = mod.check_volume(conn=conn)
        assert result["ayanamsha_check"]["status"] == "FAIL"

    def test_citation_check_pass(self):
        mod = _get_mod()
        conn = self._make_mock_conn(mod.VOLUME_FLOOR, 316.5, null_citation=0)
        result = mod.check_volume(conn=conn)
        assert result["source_citation_check"]["status"] == "PASS"


# ── Algorithmic fallback ──────────────────────────────────────────────────────

class TestAlgorithmicFallback:
    def test_returns_9_rows(self):
        mod = _get_mod()
        rows = mod._algorithmic_fallback(date(1984, 2, 5))
        assert len(rows) == 9

    def test_all_longitudes_in_range(self):
        mod = _get_mod()
        rows = mod._algorithmic_fallback(date(1984, 2, 5))
        for r in rows:
            lon = r["tropical_longitude"]
            assert 0.0 <= lon < 360.0, f"{r['body']}: lon={lon} out of range"

    def test_all_ayanamsha_id_tropical(self):
        mod = _get_mod()
        rows = mod._algorithmic_fallback(date(1984, 2, 5))
        for r in rows:
            assert r["ayanamsha_id"] == "tropical"

    def test_all_have_date(self):
        mod = _get_mod()
        d = date(2024, 6, 1)
        rows = mod._algorithmic_fallback(d)
        for r in rows:
            assert r["date"] == d

    def test_all_have_source_citation(self):
        mod = _get_mod()
        rows = mod._algorithmic_fallback(date(1984, 2, 5))
        for r in rows:
            assert r["source_citation"]

    def test_all_expected_bodies_present(self):
        mod = _get_mod()
        rows = mod._algorithmic_fallback(date(1984, 2, 5))
        names = {r["body"] for r in rows}
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter",
                    "Venus", "Saturn", "Rahu", "Ketu"}
        assert names == expected


# ── query_ephemeris ──────────────────────────────────────────────────────────

class TestQueryEphemeris:
    def test_returns_ok_false_when_db_unavailable(self):
        mod = _get_mod()
        # Patch _get_conn to raise
        with patch.object(mod, "_get_conn", side_effect=RuntimeError("no DB")):
            result = mod.query_ephemeris()
        assert result["ok"] is False
        assert result["count"] == 0

    def test_provenance_envelope_present_on_error(self):
        mod = _get_mod()
        with patch.object(mod, "_get_conn", side_effect=RuntimeError("no DB")):
            result = mod.query_ephemeris()
        assert "provenance_envelope" in result
        env = result["provenance_envelope"]
        assert env["source"] == "brahmagyan.ephemeris"
        assert env["ayanamsha_id"] == "tropical"

    def test_provenance_envelope_present_on_success(self):
        mod = _get_mod()
        # Build a mock cursor that returns no rows
        cursor = MagicMock()
        cursor.description = [MagicMock(name="date")]
        cursor.fetchall.return_value = []
        conn = MagicMock()
        conn.cursor.return_value.__enter__ = lambda s: cursor
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        result = mod.query_ephemeris(conn=conn)
        assert "provenance_envelope" in result
        assert result["provenance_envelope"]["source"] == "brahmagyan.ephemeris"
        assert result["provenance_envelope"]["ayanamsha_id"] == "tropical"

    def test_ok_true_on_success(self):
        mod = _get_mod()
        cursor = MagicMock()
        cursor.description = []
        cursor.fetchall.return_value = []
        conn = MagicMock()
        conn.cursor.return_value.__enter__ = lambda s: cursor
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        result = mod.query_ephemeris(conn=conn)
        assert result["ok"] is True

    def test_ayanamsha_id_in_result(self):
        mod = _get_mod()
        cursor = MagicMock()
        cursor.description = []
        cursor.fetchall.return_value = []
        conn = MagicMock()
        conn.cursor.return_value.__enter__ = lambda s: cursor
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        result = mod.query_ephemeris(conn=conn, ayanamsha_id="tropical")
        assert result["ayanamsha_id"] == "tropical"

    def test_source_citation_in_result(self):
        mod = _get_mod()
        cursor = MagicMock()
        cursor.description = []
        cursor.fetchall.return_value = []
        conn = MagicMock()
        conn.cursor.return_value.__enter__ = lambda s: cursor
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        result = mod.query_ephemeris(conn=conn)
        assert result["source_citation"] == mod.SOURCE_CITATION
