"""The decorator's date-window parser must accept EXACTLY what production hands it.

After the fail-closed window fix, a decorated per-chart writer raises ``WindowUncheckedError``
unless ``ctx.config['birth_params']['datetime_iso']`` is present and parseable. Production builds
that dict in ONE place: ``pipeline.orchestrator.asset_runner`` calls
``pipeline.orchestrator.birth_params.fetch_birth_params(conn, chart_id)`` and passes the result as
``ctx.config['birth_params']`` (asset_runner.py: ``config={'chart_id': chart_id, 'birth_params':
birth_params}``). These tests drive the REAL ``fetch_birth_params`` code path (a stub connection
returns charts-table-shaped rows: python ``date``/``time`` objects as psycopg returns them) and feed
its output, unmodified, to the decorator's parser. No hand-made ``datetime_iso`` fixture.
"""
from __future__ import annotations

import datetime as dt
import re
from types import SimpleNamespace

import pytest

from panchang_engine.swiss_backend import WindowUncheckedError, _chart_lifetime_jds
from pipeline.orchestrator.birth_params import fetch_birth_params

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


class _Cursor:
    def __init__(self, row):
        self._row = row

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):  # the real query text is irrelevant to the shape test
        assert "FROM public.charts" in sql

    def fetchone(self):
        return self._row


class _Conn:
    def __init__(self, row):
        self._row = row

    def cursor(self, row_factory=None):
        return _Cursor(self._row)


def _row(birth_date, birth_time, tzid="Asia/Kolkata", lat=20.2961, lng=85.8245):
    return {
        "birth_date": birth_date, "birth_time": birth_time, "birth_lat": lat, "birth_lng": lng,
        "birth_place": "Place", "timezone_id": tzid, "label": "Subject",
    }


def _decorator_window(row):
    """fetch_birth_params (real code) -> the exact ctx the orchestrator builds -> the parser."""
    bp = fetch_birth_params(_Conn(row), "00000000-0000-0000-0000-000000000000")
    ctx = SimpleNamespace(config={"chart_id": "00000000-0000-0000-0000-000000000000", "birth_params": bp})
    return bp, _chart_lifetime_jds(ctx)


CASES = {
    "native_shape_ist": _row(dt.date(1984, 2, 5), dt.time(10, 43)),
    "with_seconds": _row(dt.date(1984, 2, 5), dt.time(10, 43, 27)),
    "microseconds_dropped": _row(dt.date(1990, 6, 15), dt.time(23, 59, 59, 999999), "America/New_York"),
    "midnight": _row(dt.date(2000, 1, 1), dt.time(0, 0), "UTC"),
    "tz_aware_time_column": _row(dt.date(1984, 2, 5), dt.time(10, 43, tzinfo=IST)),
    "dst_zone": _row(dt.date(2001, 7, 1), dt.time(12, 30), "Europe/London"),
    "early_year_inside_corpus": _row(dt.date(1850, 3, 1), dt.time(6, 0), "Asia/Kolkata"),
    "negative_offset_zone": _row(dt.date(1975, 12, 31), dt.time(22, 15), "Pacific/Honolulu"),
}


@pytest.mark.parametrize("name", sorted(CASES))
def test_decorator_accepts_exactly_what_fetch_birth_params_returns(name):
    bp, (lo, hi) = _decorator_window(CASES[name])
    # The exact key and format production produces: naive local ISO with seconds (no microseconds);
    # a tz-aware TIME column would add a numeric offset, which fromisoformat also parses.
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}([+-]\d{2}:\d{2})?", bp["datetime_iso"]), bp["datetime_iso"]
    assert lo < hi
    # the window brackets the chart's own date and spans the lifetime horizon
    jd_birth = _jd(CASES[name]["birth_date"])
    assert lo < jd_birth < hi


def _jd(d):
    import swisseph as swe
    return swe.julday(d.year, d.month, d.day, 12.0)


def test_fetch_birth_params_keys_are_the_ones_the_runner_forwards():
    bp, _ = _decorator_window(CASES["native_shape_ist"])
    assert set(bp) == {"datetime_iso", "latitude_deg", "longitude_deg", "tz_offset_hours", "place_name", "subject_label"}
    assert bp["datetime_iso"] == "1984-02-05T10:43:00"
    assert bp["tz_offset_hours"] == 5.5


@pytest.mark.parametrize("bad_row_field", ["birth_date", "birth_time", "birth_lat", "birth_lng", "timezone_id"])
def test_a_chart_row_missing_required_birth_data_fails_in_fetch_birth_params_not_silently(bad_row_field):
    row = dict(CASES["native_shape_ist"])
    row[bad_row_field] = None
    with pytest.raises(ValueError):
        fetch_birth_params(_Conn(row), "00000000-0000-0000-0000-000000000000")


def test_the_global_scope_shape_is_refused_by_the_decorator_parser():
    """asset_runner passes birth_params={} for GLOBAL assets (chart_id None). A decorated writer is
    per-chart (the 15 decorated assets are all scope per_chart in asset_registry), so this shape
    must never reach it; if it ever does, the parser refuses loudly rather than recording swieph."""
    ctx = SimpleNamespace(config={"chart_id": None, "birth_params": {}})
    with pytest.raises(WindowUncheckedError):
        _chart_lifetime_jds(ctx)
