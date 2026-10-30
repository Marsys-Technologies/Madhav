"""SUR-RB-48: offset normalisation for verified offsets with non-zero seconds (input-only; L1 needs whole minutes).

The verified offset is rounded to the nearest whole minute (ties away from zero) and the local clock time is shifted by
the residual seconds, so UT is identical to the record's UT to the second. A shift that crosses local midnight refuses
the chart. Whole-minute records are untouched. The -5/0/+5-minute builds use the same transformation.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from services.rulebook.engine import birthrecord as B


def resolve(tz_raw, d, t, lat, lon, zone):
    return B.resolve_birth(B.parse_birth_record({"local_date": d, "local_time": t, "lat": lat, "lon": lon, "tz_iana": zone,
                                                 **B.record_fields_from_adb_tz_raw(tz_raw)}))


@pytest.mark.parametrize("sec,minutes,residual", [(561, 9, 21), (-20173, -336, -13), (19270, 321, 10), (21200, 353, 20),
                                                  (90, 2, -30), (-90, -2, 30), (89, 1, 29), (-30, -1, 30), (30, 1, -30)])
def test_rounding_ties_away_from_zero(sec, minutes, residual):
    assert B.round_offset_minutes(sec) == (minutes, residual)


def test_pmt_record_is_normalised_with_identical_ut():
    r = resolve("PMT m2e2015 (is standard time)", "1905-06-01", "10:00", 48.85, 2.35, "Europe/Paris")
    n = r.normalisation
    assert n == {"original_local": "1905-06-01T10:00:00", "original_offset_seconds": 561,
                 "normalised_local": "1905-06-01T09:59:39", "normalised_offset_minutes": 9, "residual_seconds": 21}
    assert r.record.local_time == "09:59:39" and r.record.utc_offset_minutes == 9 and r.record.utc_offset_seconds == 540
    assert B.ut_of(r.record) == r.utc and r.utc.isoformat() == "1905-06-01T09:50:39+00:00"
    b = r.birth()
    assert b.birth_time_local == "09:59:39" and b.utc_offset_minutes == 9 and b.birth_utc == r.utc


def test_negative_offset_normalised_with_identical_ut():
    r = resolve("SJMT m84w0315 (is standard time)", "1916-03-01", "08:00", 9.93, -84.08, "America/Costa_Rica")
    assert r.record.local_time == "08:00:13" and r.record.utc_offset_minutes == -336
    assert B.ut_of(r.record) == r.utc and r.utc.isoformat() == "1916-03-01T13:36:13+00:00"


def test_whole_minute_records_are_untouched():
    r = resolve("PDT h7w (is daylight saving time)", "1964-07-01", "21:28", 37.77, -122.42, "America/Los_Angeles")
    assert r.normalisation is None and r.record.local_time == "21:28"


def test_shift_across_local_midnight_is_refused():
    with pytest.raises(B.ChartRefused) as e:  # 00:00:10 local minus 21 s crosses midnight
        resolve("PMT m2e2015 (is standard time)", "1905-06-01", "00:00:10", 48.85, 2.35, "Europe/Paris")
    assert e.value.code == B.OFFSET_NORMALISATION_CROSSES_MIDNIGHT


@pytest.mark.parametrize("shift", [-5, 0, 5])
def test_plus_minus_five_minute_builds_use_the_same_transformation(shift):
    from datetime import datetime

    local = datetime(1905, 6, 1, 10, 0) + timedelta(minutes=shift)
    r = resolve("PMT m2e2015 (is standard time)", local.date().isoformat(), local.strftime("%H:%M:%S"), 48.85, 2.35, "Europe/Paris")
    assert r.normalisation["residual_seconds"] == 21
    assert r.record.local_time == (local - timedelta(seconds=21)).strftime("%H:%M:%S")
    assert B.ut_of(r.record) == r.utc == (local - timedelta(seconds=561)).replace(tzinfo=r.utc.tzinfo)
