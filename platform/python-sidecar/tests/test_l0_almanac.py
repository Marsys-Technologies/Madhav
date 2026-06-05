"""
test_l0_almanac.py — Unit tests for brahmagyan.l0_almanac (BRAHMA-BG-0-8)

Tests:
    1. VOLUME_FLOOR is >= 29,200
    2. NATIVE constants correct (Bhubaneswar coords)
    3. BIRTH_DATE_EXPECTED matches FORENSIC ground truth
    4. check_volume: green path (actual >= floor)
    5. check_volume: amber path (actual > 0 but < floor)
    6. check_volume: empty path (actual == 0)
    7. check_volume: birth date spot-check pass
    8. check_volume: birth date spot-check fail (wrong tithi)
    9. verify_or_bootstrap: reuses existing data when >= floor
    10. verify_or_bootstrap: returns green when spot-check passes
    11. verify_or_bootstrap: stub_bootstrap inserts birth date row

No live DB required. All DB calls are mocked.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch
import pytest


def _get_module():
    from brahmagyan import l0_almanac as mod
    return mod


class TestConstants:
    def test_volume_floor_gte_29200(self):
        mod = _get_module()
        assert mod.VOLUME_FLOOR >= 29_200

    def test_bhubaneswar_coords(self):
        mod = _get_module()
        # Bhubaneswar: ~20.3°N, ~85.8°E
        assert abs(mod.NATIVE_LAT - 20.2961) < 0.01
        assert abs(mod.NATIVE_LON - 85.8245) < 0.01

    def test_birth_date_expected_tithi(self):
        mod = _get_module()
        assert mod.BIRTH_DATE_EXPECTED["tithi"] == "Shukla Tritiya"

    def test_birth_date_expected_vara(self):
        mod = _get_module()
        assert mod.BIRTH_DATE_EXPECTED["vara"] == "Ravivara"  # Sunday

    def test_birth_date_expected_nakshatra(self):
        mod = _get_module()
        assert mod.BIRTH_DATE_EXPECTED["nakshatra"] == "Purva Bhadrapada"

    def test_native_birth_date(self):
        mod = _get_module()
        assert mod.NATIVE_BIRTH_DATE == date(1984, 2, 5)


class TestCheckVolume:
    def _make_conn(self, count: int, birth_row=None):
        """Build mock conn that returns count and optionally a birth date row."""
        mock_cur = MagicMock()
        mock_cur.__enter__ = lambda s: s
        mock_cur.__exit__ = MagicMock(return_value=False)

        call_count = [0]

        def fetchone_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return (count,)
            return birth_row

        mock_cur.fetchone.side_effect = fetchone_side_effect

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        return mock_conn

    def test_green_when_above_floor(self):
        mod = _get_module()
        conn = self._make_conn(30_000)
        result = mod.check_volume(conn)
        assert result["panchanga_daily"]["status"] == "green"
        assert result["panchanga_daily"]["actual"] == 30_000

    def test_amber_when_below_floor(self):
        mod = _get_module()
        conn = self._make_conn(1000)
        result = mod.check_volume(conn)
        assert result["panchanga_daily"]["status"] == "amber"

    def test_empty_when_zero(self):
        mod = _get_module()
        conn = self._make_conn(0)
        result = mod.check_volume(conn)
        assert result["panchanga_daily"]["status"] == "empty"

    def test_birth_date_spot_check_pass(self):
        mod = _get_module()
        # above floor + correct birth row
        conn = self._make_conn(
            30_000,
            birth_row=("Shukla Tritiya", "Ravivara", "Purva Bhadrapada", "Shiva", "Garaja"),
        )
        result = mod.check_volume(conn)
        assert "birth_date_spot_check" in result
        assert result["birth_date_spot_check"]["pass"] is True

    def test_birth_date_spot_check_fail_wrong_tithi(self):
        mod = _get_module()
        conn = self._make_conn(
            30_000,
            birth_row=("Shukla Chaturdashi", "Ravivara", "Purva Bhadrapada", "Shiva", "Garaja"),
        )
        result = mod.check_volume(conn)
        assert result["birth_date_spot_check"]["pass"] is False

    def test_no_birth_check_when_empty(self):
        mod = _get_module()
        conn = self._make_conn(0)
        result = mod.check_volume(conn)
        # When empty, no spot check attempted
        assert "birth_date_spot_check" not in result


class TestVerifyOrBootstrap:
    def _make_green_conn(self, count=30_000):
        """Conn that returns green volume and passing birth date."""
        mock_cur = MagicMock()
        mock_cur.__enter__ = lambda s: s
        mock_cur.__exit__ = MagicMock(return_value=False)

        call_count = [0]

        def fetchone_side():
            call_count[0] += 1
            if call_count[0] == 1:
                return (count,)
            return ("Shukla Tritiya", "Ravivara", "Purva Bhadrapada", "Shiva", "Garaja")

        mock_cur.fetchone.side_effect = fetchone_side

        conn = MagicMock()
        conn.cursor.return_value = mock_cur
        return conn

    def test_reuses_existing_when_above_floor(self):
        mod = _get_module()
        conn = self._make_green_conn(30_000)
        result = mod.verify_or_bootstrap(conn)
        assert result["action"] == "reused_existing"
        assert result["rows"] == 30_000

    def test_returns_green_when_spot_check_passes(self):
        mod = _get_module()
        conn = self._make_green_conn(30_000)
        result = mod.verify_or_bootstrap(conn)
        assert result["status"] == "green"

    def test_stub_bootstrap_inserts_birth_row(self):
        mod = _get_module()
        mock_cur = MagicMock()
        mock_cur.__enter__ = lambda s: s
        mock_cur.__exit__ = MagicMock(return_value=False)

        call_count = [0]

        def fetchone_side():
            call_count[0] += 1
            if call_count[0] in (1, 3):  # first count + second count after stub
                return (1 if call_count[0] == 3 else 0,)
            return ("Shukla Tritiya", "Ravivara", "Purva Bhadrapada", "Shiva", "Garaja")

        mock_cur.fetchone.side_effect = fetchone_side

        conn = MagicMock()
        conn.cursor.return_value = mock_cur

        result = mod._stub_bootstrap(conn, "test-build")
        assert result["action"] == "stub_bootstrap"
        # Should have called execute to insert the birth date row
        mock_cur.execute.assert_called()
        conn.commit.assert_called()
