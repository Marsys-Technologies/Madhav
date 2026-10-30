"""YARDSTICK v1.6 Q1 (SUR-RB-44): mean-time birth records in the 'm<deg>(e|w)<arcmin>[<arcsec>]' meridian form.

The form states the offset as a meridian: offset = (deg + arcmin/60 + arcsec/3600) / 15 hours, east positive (for example
'PMT m2e2015' = 2°20'15" E = +0:09:21, Paris Mean Time; 'SJMT m84w0315' = -5:36:13). Checks:
  LMT/LST (true local mean time): tzdb must show a local-mean-time period for the zone at the birth instant, AND the
  offset must equal the birthplace longitude / 15 within 1 minute of time;
  any other label (a named regional mean time): tzdb's offset within 1 second AND tzdb's abbreviation == the label.
"""
from __future__ import annotations

import pytest

from services.rulebook.engine import birthrecord as B


def rec(tz_raw, d, t, lat, lon, zone):
    return B.parse_birth_record({"local_date": d, "local_time": t, "lat": lat, "lon": lon, "tz_iana": zone,
                                 **B.record_fields_from_adb_tz_raw(tz_raw)})


@pytest.mark.parametrize("raw,seconds,code", [
    ("PMT m2e2015 (is standard time)", 561, "PMT"),
    ("SJMT m84w0315 (is standard time)", -20173, "SJMT"),
    ("LMT m72e50 (is local mean time)", 17480, "LMT"),
    ("MMT m80e1730 (is standard time)", 19270, "MMT"),
    ("LST m4e53 (is standard time)", 1172, "LST"),
])
def test_meridian_form_parses_to_exact_seconds(raw, seconds, code):
    f = B.record_fields_from_adb_tz_raw(raw)
    assert f["utc_offset_seconds"] == seconds and f["source_zone_code"] == code and f["mean_time_form"] is True
    assert f["utc_offset_minutes"] == round(seconds / 60)


def test_regional_mean_time_outside_its_capital_passes_on_tzdb_offset_and_abbreviation():
    # a PMT record at Bordeaux (-0.58 E), 1905: tzdb Europe/Paris is on PMT +0:09:21; the longitude rule is NOT applied
    r = B.resolve_birth(rec("PMT m2e2015 (is standard time)", "1905-06-01", "10:00", 44.84, -0.58, "Europe/Paris"))
    assert r.utc.isoformat() == "1905-06-01T09:50:39+00:00"


def test_regional_label_that_tzdb_does_not_show_is_excluded():
    with pytest.raises(B.ChartExcluded) as e:  # Paris switched to WET in 1911: PMT no longer in force
        B.resolve_birth(rec("PMT m2e2015 (is standard time)", "1912-06-01", "10:00", 48.85, 2.35, "Europe/Paris"))
    assert e.value.code == B.MEAN_TIME_REGIONAL_MISMATCH


def test_san_jose_mean_time_passes():
    r = B.resolve_birth(rec("SJMT m84w0315 (is standard time)", "1916-03-01", "08:00", 9.93, -84.08, "America/Costa_Rica"))
    assert r.utc.isoformat() == "1916-03-01T13:36:13+00:00"


def test_lmt_where_tzdb_shows_standard_time_is_excluded():
    with pytest.raises(B.ChartExcluded) as e:  # Rome 1911: CET already in force
        B.resolve_birth(rec("LMT m15e17 (is local mean time)", "1911-05-01", "12:00", 40.9, 15.28, "Europe/Rome"))
    assert e.value.code == B.MEAN_TIME_NOT_LMT_PERIOD


def test_lmt_in_an_lmt_period_with_matching_longitude_passes():
    # Asia/Kolkata is LMT before 1854; birthplace longitude 88.36 E -> +5:53:26.4; record m88e21 = +5:53:24 (within 1 min)
    r = B.resolve_birth(rec("LMT m88e21 (is local mean time)", "1850-01-01", "06:00", 22.57, 88.36, "Asia/Kolkata"))
    assert r.utc.isoformat() == "1850-01-01T00:06:36+00:00"


def test_lmt_offset_more_than_one_minute_from_longitude_is_excluded():
    with pytest.raises(B.ChartExcluded) as e:  # record says 88°40' (+5:54:40) but the place is at 88.36 E (+5:53:26)
        B.resolve_birth(rec("LMT m88e40 (is local mean time)", "1850-01-01", "06:00", 22.57, 88.36, "Asia/Kolkata"))
    assert e.value.code == B.MEAN_TIME_LONGITUDE_MISMATCH


@pytest.mark.parametrize("raw", ["PMT m2x2015", "PMT m2e", "PMT 2e2015", "PMT m2e2075", "PMT m2e20155", "PMT m200e20", "m2e2015", "PMT m2e2060"])
def test_malformed_meridian_strings_are_refused(raw):
    with pytest.raises(B.ChartRefused):
        B.record_fields_from_adb_tz_raw(raw)


def test_h_form_records_keep_the_old_path():
    f = B.record_fields_from_adb_tz_raw("PDT h7w (is daylight saving time)")
    assert f["utc_offset_minutes"] == -420 and "mean_time_form" not in f


def test_true_lmt_far_from_the_zone_city_lmt_is_unrepresentable():
    # SUR-RB-47: passes v1.6 Q1 (tzdb LMT period; offset = birthplace longitude / 15), but tzdb's LMT for the zone is the
    # zone city's (Lagos, +0:13:35), 47 minutes away from +1:01:08: L1 takes its offset from tzdb only, so excluded
    with pytest.raises(B.ChartExcluded) as e:
        B.resolve_birth(rec("LMT m15e17 (is local mean time)", "1911-05-01", "12:00", -4.27, 15.28, "Africa/Brazzaville"))
    assert e.value.code == B.L1_OFFSET_UNREPRESENTABLE


def test_true_lmt_within_one_minute_of_the_zone_lmt_is_kept():
    # Kolkata 1850: record +5:53:24, tzdb LMT +5:53:28 (4 s apart): representable
    r = B.resolve_birth(rec("LMT m88e21 (is local mean time)", "1850-01-01", "06:00", 22.57, 88.36, "Asia/Kolkata"))
    assert r.utc.isoformat() == "1850-01-01T00:06:36+00:00"
