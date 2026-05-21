"""
test_muhurat_cache.py — Unit tests for Muhurat Finder cache path (WRAPUP-S4 Packet C).

Tests:
  1. is_bhubaneswar(20.27, 85.84) → True (native coordinates)
  2. is_bhubaneswar(19.07, 72.87) → False (Mumbai — ~1400 km away)
  3. fetch_panchanga_range with mocked DB → returns correctly shaped list
  4. fetch_panchanga_range with DB exception → returns None (cache miss)
  5. Router fallback: when find_muhurat_from_cache returns None, engine-direct runs

No live DB connection required. All DB calls are mocked.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# 1 + 2: is_bhubaneswar fence
# ---------------------------------------------------------------------------

class TestIsBhubaneswar:
    def test_native_coords_inside_fence(self):
        from panchang_engine.panchang_daily_reader import is_bhubaneswar
        assert is_bhubaneswar(20.2700, 85.8400) is True

    def test_coords_just_inside_fence(self):
        """~2 km north of Bhubaneswar centre — still inside 10 km fence."""
        from panchang_engine.panchang_daily_reader import is_bhubaneswar
        assert is_bhubaneswar(20.2880, 85.8400) is True

    def test_mumbai_outside_fence(self):
        """Mumbai (19.07°N 72.87°E) is ~1400 km away — well outside fence."""
        from panchang_engine.panchang_daily_reader import is_bhubaneswar
        assert is_bhubaneswar(19.07, 72.87) is False

    def test_delhi_outside_fence(self):
        """Delhi (28.61°N 77.21°E) — outside fence."""
        from panchang_engine.panchang_daily_reader import is_bhubaneswar
        assert is_bhubaneswar(28.61, 77.21) is False

    def test_coords_just_outside_fence(self):
        """~15 km northeast of Bhubaneswar — outside 10 km fence."""
        from panchang_engine.panchang_daily_reader import is_bhubaneswar
        # 15 km north ≈ 0.135° latitude shift
        assert is_bhubaneswar(20.4050, 85.8400) is False


# ---------------------------------------------------------------------------
# Helpers: sample DB row
# ---------------------------------------------------------------------------

def _sample_row(d: date = date(2026, 6, 1)) -> dict:
    """Return a minimal panchanga_daily row shaped as fetch_panchanga_range returns."""
    return {
        "date": d,
        "tithi_id": 10,
        "nakshatra_id": 7,
        "vara_id": 1,         # Sunday
        "yoga_id": 3,
        "karana_id": 2,
        "sunrise_utc": datetime(2026, 6, 1, 0, 48, 0),
        "sunset_utc":  datetime(2026, 6, 1, 13, 10, 0),
        "moon_phase": 0.35,
        "special_yogas": [{"yoga": "Amrita", "strength": "auspicious", "stars": 4, "name": "Amrita"}],
        "choghadiya": {"day": [], "night": []},
        "hora": [{"label": "hora_sun", "start_utc": "2026-06-01T00:48:00Z", "end_utc": "2026-06-01T01:48:00Z"}],
        "inauspicious": [{"label": "rahu_kalam", "start_utc": "2026-06-01T07:30:00Z", "end_utc": "2026-06-01T09:00:00Z"}],
        "auspicious": [{"label": "abhijit", "start_utc": "2026-06-01T06:00:00Z", "end_utc": "2026-06-01T06:48:00Z"}],
    }


# ---------------------------------------------------------------------------
# 3: fetch_panchanga_range with mocked DB
# ---------------------------------------------------------------------------

class TestFetchPanchangaRange:
    def _make_cursor_mock(self, rows: list[dict]):
        """
        Return (conn_mock, cur_mock) where cur.fetchall() yields the given rows
        as tuples, and cur.description matches the column ordering in the SQL.
        """
        columns = [
            "date", "tithi_id", "nakshatra_id", "vara_id", "yoga_id",
            "karana_id", "sunrise_utc", "sunset_utc", "moon_phase",
            "special_yogas", "choghadiya", "hora", "inauspicious", "auspicious",
        ]
        # description entries only need index-0 to be the column name
        description = [(col,) for col in columns]

        # Convert rows to tuples matching column order; JSONB cols as dicts (psycopg3 style)
        raw_rows = []
        for r in rows:
            raw_rows.append(tuple(r.get(col) for col in columns))

        cur_mock = MagicMock()
        cur_mock.__enter__ = lambda s: s
        cur_mock.__exit__ = MagicMock(return_value=False)
        cur_mock.description = description
        cur_mock.fetchall.return_value = raw_rows

        conn_mock = MagicMock()
        conn_mock.__enter__ = lambda s: s
        conn_mock.__exit__ = MagicMock(return_value=False)
        conn_mock.cursor.return_value = cur_mock

        return conn_mock, cur_mock

    def test_returns_list_of_dicts_on_success(self):
        from panchang_engine.panchang_daily_reader import fetch_panchanga_range

        sample = _sample_row()
        conn_mock, _ = self._make_cursor_mock([sample])

        with patch("panchang_engine.panchang_daily_reader.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = conn_mock
            result = fetch_panchanga_range(date(2026, 6, 1), date(2026, 6, 1), "postgresql://fake/db")

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        row = result[0]
        assert row["tithi_id"] == 10
        assert row["nakshatra_id"] == 7
        assert row["vara_id"] == 1
        assert isinstance(row["special_yogas"], list)
        assert isinstance(row["inauspicious"], list)
        assert isinstance(row["auspicious"], list)
        assert isinstance(row["choghadiya"], dict)
        assert isinstance(row["hora"], list)

    def test_returns_none_on_empty_result(self):
        """Empty result set → None (cache miss, not error)."""
        from panchang_engine.panchang_daily_reader import fetch_panchanga_range

        conn_mock, _ = self._make_cursor_mock([])

        with patch("panchang_engine.panchang_daily_reader.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = conn_mock
            result = fetch_panchanga_range(date(2026, 6, 1), date(2026, 6, 1), "postgresql://fake/db")

        assert result is None

    def test_jsonb_string_deserialization(self):
        """When psycopg2 returns JSONB as strings, they are deserialized to dicts/lists."""
        from panchang_engine.panchang_daily_reader import fetch_panchanga_range

        sample = _sample_row()
        # Simulate psycopg2 returning JSONB as JSON strings
        sample_as_strings = dict(sample)
        sample_as_strings["special_yogas"] = json.dumps(sample["special_yogas"])
        sample_as_strings["choghadiya"]    = json.dumps(sample["choghadiya"])
        sample_as_strings["hora"]          = json.dumps(sample["hora"])
        sample_as_strings["inauspicious"]  = json.dumps(sample["inauspicious"])
        sample_as_strings["auspicious"]    = json.dumps(sample["auspicious"])

        conn_mock, _ = self._make_cursor_mock([sample_as_strings])

        with patch("panchang_engine.panchang_daily_reader.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = conn_mock
            result = fetch_panchanga_range(date(2026, 6, 1), date(2026, 6, 1), "postgresql://fake/db")

        assert result is not None
        assert isinstance(result[0]["special_yogas"], list)
        assert isinstance(result[0]["choghadiya"], dict)


# ---------------------------------------------------------------------------
# 4: fetch_panchanga_range with DB exception → None
# ---------------------------------------------------------------------------

class TestFetchPanchangaRangeDbFailure:
    def test_returns_none_on_connection_error(self):
        from panchang_engine.panchang_daily_reader import fetch_panchanga_range

        with patch("panchang_engine.panchang_daily_reader.psycopg") as mock_psycopg:
            mock_psycopg.connect.side_effect = Exception("connection refused")
            result = fetch_panchanga_range(date(2026, 6, 1), date(2026, 6, 30), "postgresql://fake/db")

        assert result is None

    def test_returns_none_on_missing_table(self):
        from panchang_engine.panchang_daily_reader import fetch_panchanga_range

        with patch("panchang_engine.panchang_daily_reader.psycopg") as mock_psycopg:
            mock_psycopg.connect.side_effect = Exception("relation panchanga_daily does not exist")
            result = fetch_panchanga_range(date(2026, 6, 1), date(2026, 6, 30), "postgresql://fake/db")

        assert result is None

    def test_returns_none_when_db_url_empty(self):
        from panchang_engine.panchang_daily_reader import fetch_panchanga_range

        result = fetch_panchanga_range(date(2026, 6, 1), date(2026, 6, 30), "")
        assert result is None


# ---------------------------------------------------------------------------
# 5: Cache path returns None → router falls back to engine-direct
# ---------------------------------------------------------------------------

class TestRouterFallback:
    """
    When find_muhurat_from_cache returns None, the router must call find_muhurat()
    (engine-direct) and return its result.
    """

    def test_fallback_called_when_cache_returns_none(self):
        """Cache miss → engine-direct is invoked."""
        from panchang_engine.types import MuhuratWindow

        fake_window = MuhuratWindow(
            event="vivah",
            start_utc=datetime(2026, 6, 1, 0, 48, 0),
            end_utc=datetime(2026, 6, 1, 13, 10, 0),
            star_rating=4,
            score=72.5,
            breakdown={"tithi_id": 10},
        )

        with (
            patch("routers.muhurat.is_bhubaneswar", return_value=True),
            patch("routers.muhurat.find_muhurat_from_cache", return_value=None) as mock_cache,
            patch("routers.muhurat.find_muhurat", return_value=[fake_window]) as mock_engine,
            patch.dict("os.environ", {"DATABASE_URL": "postgresql://fake/db"}),
        ):
            # Import the endpoint function after patching env
            from routers.muhurat import compute_muhurat_endpoint
            from routers.muhurat import MuhuratRequest

            req = MuhuratRequest(
                event="vivah",
                date_from=date(2026, 6, 1),
                date_to=date(2026, 6, 30),
                lat=20.27,
                lon=85.84,
            )

            import asyncio
            result = asyncio.get_event_loop().run_until_complete(
                compute_muhurat_endpoint(req)
            )

        mock_cache.assert_called_once()
        mock_engine.assert_called_once()
        assert result["ok"] is True
        assert len(result["windows"]) == 1

    def test_cache_result_returned_directly_without_engine(self):
        """Cache hit → engine-direct is NOT invoked."""
        from panchang_engine.types import MuhuratWindow

        fake_window = MuhuratWindow(
            event="vivah",
            start_utc=datetime(2026, 6, 1, 0, 48, 0),
            end_utc=datetime(2026, 6, 1, 13, 10, 0),
            star_rating=5,
            score=85.0,
            breakdown={"tithi_id": 10},
        )

        with (
            patch("routers.muhurat.is_bhubaneswar", return_value=True),
            patch("routers.muhurat.find_muhurat_from_cache", return_value=[fake_window]) as mock_cache,
            patch("routers.muhurat.find_muhurat") as mock_engine,
            patch.dict("os.environ", {"DATABASE_URL": "postgresql://fake/db"}),
        ):
            from routers.muhurat import compute_muhurat_endpoint
            from routers.muhurat import MuhuratRequest

            req = MuhuratRequest(
                event="vivah",
                date_from=date(2026, 6, 1),
                date_to=date(2026, 6, 30),
                lat=20.27,
                lon=85.84,
            )

            import asyncio
            result = asyncio.get_event_loop().run_until_complete(
                compute_muhurat_endpoint(req)
            )

        mock_cache.assert_called_once()
        mock_engine.assert_not_called()
        assert result["ok"] is True
        assert result["windows"][0]["star_rating"] == 5

    def test_non_bhubaneswar_skips_cache(self):
        """Non-Bhubaneswar request goes straight to engine-direct, never touches cache."""
        from panchang_engine.types import MuhuratWindow

        fake_window = MuhuratWindow(
            event="yatra",
            start_utc=datetime(2026, 6, 5, 1, 0, 0),
            end_utc=datetime(2026, 6, 5, 13, 0, 0),
            star_rating=3,
            score=55.0,
            breakdown={},
        )

        with (
            patch("routers.muhurat.is_bhubaneswar", return_value=False),
            patch("routers.muhurat.find_muhurat_from_cache") as mock_cache,
            patch("routers.muhurat.find_muhurat", return_value=[fake_window]) as mock_engine,
            patch.dict("os.environ", {"DATABASE_URL": "postgresql://fake/db"}),
        ):
            from routers.muhurat import compute_muhurat_endpoint
            from routers.muhurat import MuhuratRequest

            req = MuhuratRequest(
                event="yatra",
                date_from=date(2026, 6, 1),
                date_to=date(2026, 6, 30),
                lat=19.07,
                lon=72.87,  # Mumbai
            )

            import asyncio
            result = asyncio.get_event_loop().run_until_complete(
                compute_muhurat_endpoint(req)
            )

        mock_cache.assert_not_called()
        mock_engine.assert_called_once()
        assert result["ok"] is True


# ---------------------------------------------------------------------------
# Proxy dataclass smoke tests
# ---------------------------------------------------------------------------

class TestCachedPanchang:
    """Smoke tests for _CachedPanchang proxy."""

    def test_proxy_builds_from_row(self):
        from panchang_engine.muhurat import _CachedPanchang

        row = _sample_row()
        proxy = _CachedPanchang(row)

        assert proxy.tithi.id == 10
        assert proxy.nakshatra.id == 7
        assert proxy.vara.id == 1
        assert isinstance(proxy.inauspicious, list)
        assert len(proxy.inauspicious) == 1
        assert proxy.inauspicious[0].label == "rahu_kalam"
        assert isinstance(proxy.special_yogas, list)
        assert proxy.special_yogas[0]["strength"] == "auspicious"
        assert proxy.planets == []  # no planet data in cache

    def test_proxy_inauspicious_has_label_attr(self):
        """score_muhurat uses getattr(t, 'label', '') on inauspicious items."""
        from panchang_engine.muhurat import _CachedPanchang

        row = _sample_row()
        proxy = _CachedPanchang(row)

        for t in proxy.inauspicious:
            label = getattr(t, "label", "MISSING")
            assert label != "MISSING"

    def test_proxy_sunrise_sunset_parsed(self):
        """sunrise_utc and sunset_utc are datetime objects."""
        from panchang_engine.muhurat import _CachedPanchang

        row = _sample_row()
        proxy = _CachedPanchang(row)

        assert isinstance(proxy.sunrise_utc, datetime)
        assert isinstance(proxy.sunset_utc, datetime)

    def test_proxy_sunrise_from_iso_string(self):
        """Handles ISO string sunrise_utc (psycopg2 path)."""
        from panchang_engine.muhurat import _CachedPanchang

        row = _sample_row()
        row["sunrise_utc"] = "2026-06-01T00:48:00Z"
        row["sunset_utc"]  = "2026-06-01T13:10:00Z"
        proxy = _CachedPanchang(row)

        assert isinstance(proxy.sunrise_utc, datetime)
        assert proxy.sunrise_utc.hour == 0
        assert proxy.sunrise_utc.minute == 48
