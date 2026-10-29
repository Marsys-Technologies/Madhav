"""Explicit-UT-offset birth input (SUR-RB-6): fail closed on a missing offset, exclude on a tz-database disagreement, convert with the stated offset only."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from services.rulebook.engine import birthrecord as B


def rec(**kw):
    base = {"local_date": "1990-07-04", "local_time": "14:30:00", "lat": 34.05, "lon": -118.24, "utc_offset_minutes": -420, "tz_iana": "America/Los_Angeles"}
    base.update(kw)
    return base


# ── (1) the offset comes only from the record; missing or malformed refuses ──────────────
@pytest.mark.parametrize("value", [None, "", "   "])
def test_missing_offset_fails_closed(value):
    r = rec(utc_offset_minutes=value)
    with pytest.raises(B.ChartRefused) as e:
        B.parse_birth_record(r)
    assert e.value.code == B.OFFSET_MISSING


def test_absent_offset_key_fails_closed_even_when_a_zone_name_could_supply_one():
    r = rec()
    del r["utc_offset_minutes"]
    for extra in ({}, {"tz_iana": "Asia/Kolkata"}, {"source_zone_code": "IST"}, {"dst_applied": False}):
        with pytest.raises(B.ChartRefused) as e:
            B.parse_birth_record(dict(r, **extra))
        assert e.value.code == B.OFFSET_MISSING  # never IST, never the zone's offset


@pytest.mark.parametrize("value", ["+05:30", "330", True, False, 330.5, float("nan"), float("inf"), 5000, -5000, [330], {"m": 330}])
def test_malformed_offset_fails_closed(value):
    with pytest.raises(B.ChartRefused) as e:
        B.parse_birth_record(rec(utc_offset_minutes=value))
    assert e.value.code == B.OFFSET_MALFORMED


@pytest.mark.parametrize(
    "patch",
    [{"local_date": "1990-13-01"}, {"local_time": "25:00"}, {"local_time": "9am"}, {"lat": 91}, {"lon": -181}, {"lat": "x"}, {"dst_applied": "yes"}],
)
def test_other_malformed_fields_refuse(patch):
    with pytest.raises(B.ChartRefused) as e:
        B.parse_birth_record(rec(**patch))
    assert e.value.code == B.RECORD_MALFORMED


def test_whole_number_float_offset_is_accepted_as_minutes():
    assert B.parse_birth_record(rec(utc_offset_minutes=-420.0)).utc_offset_minutes == -420


# ── source-record formats ────────────────────────────────────────────────────────────────
def test_adb_style_tz_raw_gives_offset_code_and_dst_note_as_stated():
    f = B.record_fields_from_adb_tz_raw("PDT h7w (is daylight saving time)")
    assert f == {"utc_offset_minutes": -420, "source_zone_code": "PDT", "dst_note": "is daylight saving time", "dst_applied": True}
    assert B.record_fields_from_adb_tz_raw("EDT h4w (is daylight saving time)")["utc_offset_minutes"] == -240
    assert B.record_fields_from_adb_tz_raw("IST h5e30")["utc_offset_minutes"] == 330
    assert B.record_fields_from_adb_tz_raw("NPT h5e45")["utc_offset_minutes"] == 345
    assert B.record_fields_from_adb_tz_raw("GMT h0e")["utc_offset_minutes"] == 0


@pytest.mark.parametrize("raw", ["", "PDT", "PDT 7w", "h7w", "PDT h7x", "LMT m5e45", "PDT h7w30extra", "PDT h7e75", None])
def test_unrecognised_tz_raw_is_refused_not_guessed(raw):
    with pytest.raises(B.ChartRefused):
        B.record_fields_from_adb_tz_raw(raw)


# ── (2) cross-check against the pinned tz database ───────────────────────────────────────
@pytest.mark.parametrize(
    "d,t,off,zone",
    [
        ("1990-07-04", "14:30:00", -420, "America/Los_Angeles"),  # PDT
        ("1990-01-04", "14:30:00", -480, "America/Los_Angeles"),  # PST
        ("1992-08-12", "22:45:00", 60, "Europe/London"),  # BST
        ("1987-03-03", "18:20:00", 345, "Asia/Kathmandu"),  # +05:45
        ("2001-02-01", "21:15:00", 660, "Australia/Sydney"),  # AEDT
        ("1999-09-09", "08:30:00", -660, "Pacific/Pago_Pago"),
        ("1998-01-20", "09:05:00", 780, "Pacific/Auckland"),  # NZDT
        ("2005-01-10", "10:00:00", 660, "Australia/Lord_Howe"),  # +11:00 summer (half-hour DST zone)
        ("2005-07-10", "10:00:00", 630, "Australia/Lord_Howe"),  # +10:30 winter
    ],
)
def test_agreeing_offsets_resolve_and_ut_is_local_minus_offset(d, t, off, zone):
    tally = B.ExclusionTally()
    r = B.resolve_birth(B.parse_birth_record(rec(local_date=d, local_time=t, utc_offset_minutes=off, tz_iana=zone)), tally=tally)
    local = datetime.fromisoformat(f"{d}T{t}")
    assert r.utc == (local - timedelta(minutes=off)).replace(tzinfo=timezone.utc)
    assert r.jd_ut == pytest.approx(2440587.5 + r.utc.timestamp() / 86400.0, abs=1e-9)
    assert tally.to_json()["accepted"] == 1 and tally.excluded == 0 and tally.refused == 0
    b = r.birth()
    assert b.birth_utc == r.utc and b.utc_offset_minutes == off


@pytest.mark.parametrize(
    "d,t,off,zone",
    [
        ("1990-07-04", "14:30:00", -480, "America/Los_Angeles"),  # PST stated for a summer date
        ("1990-01-04", "14:30:00", -420, "America/Los_Angeles"),  # PDT stated in winter
        ("1987-03-03", "18:20:00", 330, "Asia/Kathmandu"),  # India's offset stated for Nepal
        ("1990-07-04", "14:30:00", 330, "America/Los_Angeles"),  # IST stated for a US place: no IST fallback blessing
        ("1980-12-21", "12:00:00", -540, "America/Anchorage"),  # Alaska was -10:00 in 1980
    ],
)
def test_tz_database_disagreement_excludes_and_is_counted(d, t, off, zone):
    tally = B.ExclusionTally()
    with pytest.raises(B.ChartExcluded) as e:
        B.resolve_birth(B.parse_birth_record(rec(local_date=d, local_time=t, utc_offset_minutes=off, tz_iana=zone)), tally=tally)
    assert e.value.code == B.TZ_DISAGREEMENT
    j = tally.to_json()
    assert j["excluded"] == 1 and j["excluded_by_reason"] == {B.TZ_DISAGREEMENT: 1} and j["accepted"] == 0


def test_dst_fold_accepts_either_valid_offset_and_a_gap_time_is_excluded():
    fold = dict(local_date="2021-11-07", local_time="01:30:00", tz_iana="America/New_York", lat=40.7, lon=-74.0)
    for off, want in ((-240, "2021-11-07T05:30:00"), (-300, "2021-11-07T06:30:00")):  # both readings of the repeated hour exist
        assert B.resolve_birth(B.parse_birth_record(rec(utc_offset_minutes=off, **fold))).utc == datetime.fromisoformat(want).replace(tzinfo=timezone.utc)
    with pytest.raises(B.ChartExcluded) as e:
        B.resolve_birth(B.parse_birth_record(rec(utc_offset_minutes=-360, **fold)))
    assert e.value.code == B.TZ_DISAGREEMENT
    gap = dict(local_date="2021-03-14", local_time="02:30:00", tz_iana="America/New_York", lat=40.7, lon=-74.0)
    for off in (-240, -300):
        with pytest.raises(B.ChartExcluded) as e:
            B.resolve_birth(B.parse_birth_record(rec(utc_offset_minutes=off, **gap)))
        assert e.value.code == B.TZ_LOCAL_TIME_NONEXISTENT


def test_uncheckable_place_is_excluded_not_trusted():
    with pytest.raises(B.ChartExcluded) as e:
        B.resolve_birth(B.parse_birth_record(rec(tz_iana="Mars/Olympus_Mons")))
    assert e.value.code == B.TZ_UNCHECKABLE


def test_zone_is_found_from_coordinates_when_the_record_names_none():
    pytest.importorskip("timezonefinder")
    r = rec()
    del r["tz_iana"]
    got = B.resolve_birth(B.parse_birth_record(r))
    assert got.zone_checked == "America/Los_Angeles"
    with pytest.raises(B.ChartExcluded):  # same place, wrong stated offset: still caught without a named zone
        B.resolve_birth(B.parse_birth_record(dict(r, utc_offset_minutes=330)))


def test_tzdb_pin_mismatch_excludes():
    with pytest.raises(B.ChartExcluded) as e:
        B.resolve_birth(B.parse_birth_record(rec()), expected_tzdb="1999a")
    assert e.value.code == B.TZDB_PIN_MISMATCH


def test_batch_reports_refused_and_excluded_counts_by_reason():
    records = [
        rec(),
        rec(utc_offset_minutes=None),
        rec(utc_offset_minutes="-07:00"),
        rec(utc_offset_minutes=-480),
        rec(local_date="2021-03-14", local_time="02:30:00", utc_offset_minutes=-300, tz_iana="America/New_York"),
        rec(local_time="99:99"),
        rec(local_date="1992-08-12", local_time="22:45:00", utc_offset_minutes=60, tz_iana="Europe/London"),
    ]
    resolved, tally, codes = B.resolve_many(records)
    j = tally.to_json()
    assert [r is not None for r in resolved] == [True, False, False, False, False, False, True]
    assert j["accepted"] == 2 and j["refused"] == 3 and j["excluded"] == 2
    assert j["refused_by_reason"] == {B.OFFSET_MALFORMED: 1, B.OFFSET_MISSING: 1, B.RECORD_MALFORMED: 1}
    assert j["excluded_by_reason"] == {B.TZ_DISAGREEMENT: 1, B.TZ_LOCAL_TIME_NONEXISTENT: 1}
    assert codes[1] == B.OFFSET_MISSING and codes[3] == B.TZ_DISAGREEMENT


# ── (3) true UT ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "local,off,ut",
    [
        ("2000-01-01T01:00:00", 780, "1999-12-31T12:00:00"),  # east of the date line: UT is the previous day
        ("2000-01-01T23:30:00", -660, "2000-01-02T10:30:00"),  # west: UT is the next day
        ("2000-06-15T12:00:00", 0, "2000-06-15T12:00:00"),
        ("1987-03-03T18:20:00", 345, "1987-03-03T12:35:00"),
    ],
)
def test_ut_conversion_uses_the_stated_offset_only(local, off, ut):
    r = B.parse_birth_record(rec(local_date=local[:10], local_time=local[11:], utc_offset_minutes=off))
    assert B.ut_of(r) == datetime.fromisoformat(ut).replace(tzinfo=timezone.utc)
