"""Verifier side of the measuring build (FINAL_BUILD_SCOPE FB-2/FB-3/FB-50, §13) — pure tests, no database.

Every expected number is worked by hand from the rule in the module's docstring, never read back from the code.
The horizon of the pinned chart is 1998-01-01 .. 2084-02-05 (31,446 days). The database readers are tested in
test_measuring_report_db.py on the stub chart's world.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from services.gochara_kernel import measuring_report as mr
from services.gochara_kernel.measuring_report import (
    MeasuringBuildView, MeasuringReportError, SupportRecord, admitted_days, as_utc_date, class_share_report,
    clip_windows_for_scoring, derive_chart_horizon, derive_chart_horizon_detail, fully_dated_events, length_distribution,
    measuring_refusals, near_miss_counts)

H = (date(1998, 1, 1), date(2084, 2, 5))
H_DAYS = 31446                       # 1998-01-01 .. 2084-02-05: 86*365 + 21 leap days (2000..2080) + 35 days (Jan 1 -> Feb 5)
BIRTH = date(1984, 2, 5)
BUILD = date(2026, 10, 5)


def T(y, m, d, hh=0, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)


_SEQ = {"n": 0}


_NOID = object()


def LEL(d, conf="exact", shape="point", category="work", interval_start=None, event_id=None, lel_id=_NOID, **extra):
    """a STORED life_events row as the intake writes it: a uuid5-style `event_id` and the human id in `provenance.lel_id`
    (`EVT.YYYY.MM.DD.NN`, `EVT.YYYY.XX.XX.NN` for a year-only row). `lel_id=None` = no lel id at all."""
    _SEQ["n"] += 1
    if lel_id is _NOID:
        lel_id = (f"EVT.{d.year:04d}.XX.XX.{_SEQ['n']:02d}" if conf == "year_only" else f"EVT.{d.year:04d}.{d.month:02d}.{d.day:02d}.{_SEQ['n']:02d}")
    if event_id is None:
        event_id = f"1234abcd-0000-5000-8000-{_SEQ['n']:012d}"
    row = {"event_id": event_id, "event_date": d, "category": category, "date_confidence": conf, "shape": shape, "interval_start": interval_start,
           "interval_end": None, "chain_parent_event_id": None, "provenance": ({"lel_id": lel_id} if lel_id is not None else {})}
    row.update(extra)
    return row


def born(d=BIRTH):
    """the birth row as the REAL log has it (R-LEL): category other, event_type other, domain other/birth"""
    return LEL(d, category="other", event_type="other", domain="other/birth", lel_id=f"EVT.{d.year:04d}.{d.month:02d}.{d.day:02d}.00")


BIRTH_ROW = born()


def _refuses(fn, code):
    """the call must raise MeasuringReportError carrying `code`; any other outcome is an assertion failure (not a raw exception)"""
    try:
        fn()
    except MeasuringReportError as exc:
        assert code in str(exc), str(exc)
    except Exception as exc:                                                    # noqa: BLE001
        raise AssertionError(f"not a named refusal: {type(exc).__name__}: {exc}") from None
    else:
        raise AssertionError(f"no refusal ({code} expected)")


# ── the horizon ──────────────────────────────────────────────────────────────────────────────────────────────────
def test_the_pinned_chart_horizon_is_1998_01_01_to_2084_02_05_and_has_the_measured_day_count():
    start, end, basis = derive_chart_horizon(BIRTH, [BIRTH_ROW, LEL(date(1998, 8, 20)), LEL(date(2003, 5, 1))], BUILD)
    assert (start, end, basis) == (date(1998, 1, 1), date(2084, 2, 5), "first_dated_event")
    assert mr.horizon_days((start, end)) == H_DAYS


def test_the_real_fixture_gives_the_ruled_pair_and_reordering_changes_nothing():
    rows = [BIRTH_ROW, LEL(date(1993, 7, 1), conf="year_only"), LEL(date(1995, 7, 1), conf="year_only"), LEL(date(1998, 2, 16)), LEL(date(2003, 5, 1))]
    d = derive_chart_horizon_detail(BIRTH, rows, BUILD)
    assert (d["start"], d["end"], d["basis"], d["excluded_undated"]) == (date(1998, 1, 1), date(2084, 2, 5), "first_dated_event", 2)
    assert derive_chart_horizon_detail(BIRTH, list(reversed(rows)), BUILD) == d
    without_1998 = [r for r in rows if r["event_date"] != date(1998, 2, 16)]
    assert derive_chart_horizon(BIRTH, without_1998, BUILD)[0] == date(2003, 1, 1)


def test_an_empty_log_reaches_the_rebuild_date_fallback_and_a_nonempty_one_without_a_dated_event_does_too():
    a = derive_chart_horizon(BIRTH, [], BUILD)
    assert a == (BUILD, date(2084, 2, 5), "build_date")
    b = derive_chart_horizon(BIRTH, [], BUILD + timedelta(days=1))
    assert b[0] == BUILD + timedelta(days=1) and b[2] == "build_date" and a != b       # the build date is IN the result


def test_a_log_that_exists_but_opens_no_dated_event_is_refused_not_read_as_an_absent_log():
    _refuses(lambda: derive_chart_horizon(BIRTH, [BIRTH_ROW], BUILD), "horizon_underivable_log_has_no_dated_event")
    _refuses(lambda: derive_chart_horizon(BIRTH, [BIRTH_ROW, LEL(date(2001, 1, 1), conf="year_only")], BUILD), "horizon_underivable_log_has_no_dated_event")
    _refuses(lambda: derive_chart_horizon(BIRTH, [BIRTH_ROW, LEL(date(1999, 5, 5), conf="month_known")], BUILD), "horizon_underivable_log_has_no_dated_event")


def test_the_birth_date_is_the_civil_date_of_datetime_iso_in_its_own_offset():
    params = {"datetime_iso": "1984-02-05T10:43:00+05:30", "lat": 20.27}                  # the real runner passes datetime_iso and no birth_date key
    assert mr.birth_date_of(params) == date(1984, 2, 5)                                    # 05:13Z the same day; an offset near midnight would differ
    assert mr.birth_date_of({"datetime_iso": "1984-02-05T00:10:00+05:30"}) == date(1984, 2, 5)    # 1984-02-04T18:40Z, still the 5th in its own offset
    assert derive_chart_horizon(params, [BIRTH_ROW, LEL(date(1998, 2, 16))], BUILD) == (date(1998, 1, 1), date(2084, 2, 5), "first_dated_event")
    for bad in ({}, {"datetime_iso": None}, {"datetime_iso": "never"}):
        _refuses(lambda b=bad: derive_chart_horizon(b, [], BUILD), "birth_params_unreadable")


def test_the_build_date_is_a_utc_date_a_tz_aware_instant_is_taken_to_its_utc_date_and_nothing_else_is_accepted():
    late_ist = datetime(2026, 10, 5, 23, 30, tzinfo=timezone(timedelta(hours=5, minutes=30)))     # 18:00 UTC the same day
    early_ist = datetime(2026, 10, 6, 1, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))      # 19:30 UTC on the 5th
    assert derive_chart_horizon(BIRTH, [], late_ist)[0] == date(2026, 10, 5)
    assert derive_chart_horizon(BIRTH, [], early_ist)[0] == date(2026, 10, 5)
    _refuses(lambda: derive_chart_horizon(BIRTH, [], datetime(2026, 10, 5, 12)), "naive_datetime")
    for bad in (None, "2026-10-05", 20261005):
        _refuses(lambda b=bad: derive_chart_horizon(BIRTH, [], b), "build_date_unreadable")


def test_the_first_event_is_the_earliest_not_the_first_listed():
    rows = [BIRTH_ROW, LEL(date(2010, 3, 3)), LEL(date(1999, 12, 31))]
    assert derive_chart_horizon(BIRTH, rows, BUILD)[0] == date(1999, 1, 1)


def test_the_birth_row_is_identified_by_the_domain_column_only_and_refused_when_a_nonempty_log_has_none_or_two():
    assert mr.is_birth_row(LEL(BIRTH, domain="other/birth"))
    for not_birth in ({"category": "other", "subcategory": "birth"}, {"event_type": "birth"}, {"provenance": {"subcategory": "birth"}}, {"category": "birth"},
                      {"category": "other"}, {"domain": "other"}, {"domain": "birth"}, {"domain": "psychological/speech_pattern_arc"}):
        assert not mr.is_birth_row(LEL(BIRTH, **not_birth)), not_birth                      # R-LEL: the domain column is the ONLY identifier
    _refuses(lambda: fully_dated_events([LEL(date(2001, 6, 9))], birth_date=BIRTH), "lel_birth_row_unidentifiable")                 # none
    _refuses(lambda: fully_dated_events([born(date(1984, 2, 6)), LEL(date(2001, 6, 9))], birth_date=BIRTH), "lel_birth_row_unidentifiable")   # wrong date
    _refuses(lambda: fully_dated_events([BIRTH_ROW, born(), LEL(date(2001, 6, 9))], birth_date=BIRTH), "lel_birth_row_unidentifiable")        # two
    assert fully_dated_events([], birth_date=BIRTH)["dates"] == []                                                                   # an empty log is not an error


def test_fully_dated_is_a_conjunction_of_exact_and_a_dated_lel_id_and_a_failing_row_is_excluded_and_reported_never_a_refusal():
    rows = [BIRTH_ROW, LEL(date(1997, 7, 1), conf="year_only"), LEL(date(1997, 5, 1), conf="month_known"), LEL(date(2001, 6, 9))]
    info = fully_dated_events(rows, birth_date=BIRTH)
    assert info["dates"] == [date(2001, 6, 9)] and info["excluded"] == 2 and info["flag_exact_but_id_undated"] == []
    # the reviewer's input: the intake's uuid `event_id` with the EVT id in provenance.lel_id is a VALID fully dated event (no refusal)
    ok = LEL(date(1998, 2, 16), event_id="12345678-1234-1234-1234-123456789abc", lel_id="EVT.1998.02.16.01")
    d = derive_chart_horizon_detail(BIRTH, [BIRTH_ROW, ok], BUILD)
    assert (d["start"], d["basis"], d["chosen"]) == (date(1998, 1, 1), "first_dated_event", "12345678-1234-1234-1234-123456789abc")
    # an exact-flagged row whose lel id is undated (457 defaulted legacy rows to exact) before a valid 1998 event: EXCLUDED and REPORTED, start 1998
    legacy = LEL(date(1995, 7, 1), lel_id="EVT.1995.XX.XX.01")
    d = derive_chart_horizon_detail(BIRTH, [BIRTH_ROW, legacy, ok], BUILD)
    assert d["start"] == date(1998, 1, 1) and d["excluded_undated"] == 1
    assert [r["lel_id"] for r in d["flag_exact_but_id_undated"]] == ["EVT.1995.XX.XX.01"]
    # a stored date that differs from its lel id's date is the same exclusion
    skewed = LEL(date(1996, 3, 3), lel_id="EVT.1996.03.04.01")
    assert derive_chart_horizon_detail(BIRTH, [BIRTH_ROW, skewed, ok], BUILD)["start"] == date(1998, 1, 1)
    # the reverse: a dated top-level event_id (EVT form) with an UNDATED provenance.lel_id is disqualified, not accepted
    reverse = LEL(date(1996, 3, 3), event_id="EVT.1996.03.03.01", lel_id="EVT.1996.XX.XX.01")
    assert derive_chart_horizon_detail(BIRTH, [BIRTH_ROW, reverse, ok], BUILD)["start"] == date(1998, 1, 1)


def test_a_row_with_no_provenance_lel_id_is_excluded_and_reported_never_a_refusal_never_a_fallback_to_event_id():
    no_id = LEL(date(1996, 3, 3), lel_id=None)                                    # exact-flagged, no provenance.lel_id, uuid event_id, the EARLIEST exact row
    info = fully_dated_events([BIRTH_ROW, no_id, LEL(date(2001, 6, 9))], birth_date=BIRTH)
    assert info["dates"] == [date(2001, 6, 9)] and info["excluded"] == 1
    assert info["rows_without_lel_id"] == [{"event_id": no_id["event_id"], "event_date": "1996-03-03"}] and info["flag_exact_but_id_undated"] == []
    # a dated top-level event_id with no provenance.lel_id is NOT a substitute: excluded and reported, first or later
    dated_event_id = LEL(date(2001, 6, 9), event_id="EVT.2001.06.09.07", lel_id=None)
    d = derive_chart_horizon_detail(BIRTH, [BIRTH_ROW, dated_event_id, LEL(date(2003, 4, 4))], BUILD)
    assert d["start"] == date(2003, 1, 1) and [r["event_id"] for r in d["rows_without_lel_id"]] == ["EVT.2001.06.09.07"]
    later = LEL(date(2009, 3, 3), event_id="EVT.2009.03.03.07", lel_id=None)
    info = fully_dated_events([BIRTH_ROW, LEL(date(2001, 6, 9)), later], birth_date=BIRTH)
    assert info["dates"] == [date(2001, 6, 9)] and [r["event_id"] for r in info["rows_without_lel_id"]] == ["EVT.2009.03.03.07"] and info["flag_exact_but_id_undated"] == []
    # a log that exists but whose only exact row has no lel id still refuses (no fully dated row), by the horizon's own name
    _refuses(lambda: derive_chart_horizon(BIRTH, [BIRTH_ROW, no_id], BUILD), "horizon_underivable_log_has_no_dated_event")
    # EVERY row without a provenance lel id is reported, whatever its confidence (R-LEL-ASTRA); a non-exact one is excluded by its confidence as before
    year_only = LEL(date(2001, 1, 1), conf="year_only", lel_id=None)
    month_known = LEL(date(1999, 5, 5), conf="month_known", lel_id=None)
    info = fully_dated_events([BIRTH_ROW, year_only, month_known, LEL(date(2001, 6, 9))], birth_date=BIRTH)
    assert info["dates"] == [date(2001, 6, 9)] and info["excluded"] == 2
    assert info["rows_without_lel_id"] == [{"event_id": month_known["event_id"], "event_date": "1999-05-05"}, {"event_id": year_only["event_id"], "event_date": "2001-01-01"}]
    # two id-less rows (one exact, one not): both entries, in date order whatever the read order, and the exact one is excluded exactly once
    exact_no_id = LEL(date(1996, 3, 3), lel_id=None)
    both = [BIRTH_ROW, year_only, exact_no_id, LEL(date(2001, 6, 9))]
    for rows in (both, list(reversed(both))):
        info = fully_dated_events(rows, birth_date=BIRTH)
        assert info["rows_without_lel_id"] == [{"event_id": exact_no_id["event_id"], "event_date": "1996-03-03"}, {"event_id": year_only["event_id"], "event_date": "2001-01-01"}]
        assert info["excluded"] == 2 and info["dates"] == [date(2001, 6, 9)] and info["flag_exact_but_id_undated"] == []
    # a row WITH an id is never listed there, undated id or not
    assert fully_dated_events([BIRTH_ROW, LEL(date(2001, 1, 1), conf="year_only"), LEL(date(2001, 6, 9))], birth_date=BIRTH)["rows_without_lel_id"] == []


def _readback_rows():
    """The eight earliest rows of the real log, written out from /Users/Dev/pravaha/run/R_LEL_READBACK_20261005.txt (production read, 5 Oct 2026, chart 482012f1): date |
    category/event_type | domain | lel_id | shape | date_confidence | interval. The readback holds no event_id; a synthetic uuid per row stands in."""
    def row(n, event_date, category, event_type, domain, lel_id, shape, conf, interval=None):
        return {"event_id": f"00000000-0000-5000-8000-{n:012d}", "event_date": event_date, "category": category, "event_type": event_type, "domain": domain,
                "date_confidence": conf, "shape": shape, "interval_start": interval[0] if interval else None, "interval_end": interval[1] if interval else None,
                "chain_parent_event_id": None, "provenance": ({"lel_id": lel_id} if lel_id else {})}
    return [
        row(1, date(1984, 2, 5), "psychological", "psychological", "psychological/speech_pattern_arc", None, "interval", "exact", (date(1984, 2, 5), date(2026, 7, 19))),
        row(2, date(1984, 2, 5), "other", "other", "other/birth", "EVT.1984.02.05.01", "point", "exact"),
        row(3, date(1993, 7, 1), "creative", "creative", "creative/award", "EVT.1993.XX.XX.01", "point", "exact"),
        row(4, date(1995, 7, 1), "psychological", "psychological", "psychological/speech_pattern_arc", "EVT.1995.XX.XX.02", "point", "exact"),
        row(5, date(1995, 7, 1), "health", "health", "health/chronic_onset", "EVT.1995.XX.XX.01", "interval", "year_only", (date(1995, 1, 1), date(2010, 12, 31))),
        row(6, date(1998, 2, 16), "relationship", "relationship", "relationship/romantic_long_term_started", "EVT.1998.02.16.01", "point", "exact"),
        row(7, date(1998, 7, 1), "spiritual", "spiritual", "spiritual/transmission", "EVT.1998.XX.XX.02", "point", "exact"),
        row(8, date(2000, 6, 1), "education", "education", "education/advanced_course_partial", "EVT.2000.XX.XX.01", "point", "exact"),
    ]


def test_the_eight_earliest_rows_of_the_real_log_start_the_horizon_at_1998_01_01_with_every_exclusion_reported():
    rows = _readback_rows()
    d = derive_chart_horizon_detail(date(1984, 2, 5), rows, BUILD)
    assert (d["start"], d["end"], d["basis"]) == (date(1998, 1, 1), date(2084, 2, 5), "first_dated_event")
    assert d["chosen"] == "00000000-0000-5000-8000-000000000006"                                    # EVT.1998.02.16.01, the first row passing the conjunction
    # row 1: exact interval on the birth date with NO lel id -> reported, not a refusal, not the birth row, not an event
    assert d["rows_without_lel_id"] == [{"event_id": "00000000-0000-5000-8000-000000000001", "event_date": "1984-02-05"}]
    # rows 3, 4, 7, 8: exact-flagged with an undated id -> reported
    assert [r["lel_id"] for r in d["flag_exact_but_id_undated"]] == ["EVT.1993.XX.XX.01", "EVT.1995.XX.XX.02", "EVT.1998.XX.XX.02", "EVT.2000.XX.XX.01"]
    # row 5 is excluded by its year_only confidence; the birth row (row 2, domain other/birth) is set aside: 1 + 4 + 1 excluded
    assert d["excluded_undated"] == 6
    info = fully_dated_events(rows, birth_date=date(1984, 2, 5))
    assert info["birth_row"]["event_id"] == "00000000-0000-5000-8000-000000000002" and info["dates"] == [date(1998, 2, 16)]
    # the order of the rows changes nothing
    assert derive_chart_horizon_detail(date(1984, 2, 5), list(reversed(rows)), BUILD) == d
    # the real runner passes birth_params, not a date
    assert derive_chart_horizon_detail({"datetime_iso": "1984-02-05T10:43:00+05:30"}, rows, BUILD) == d


def test_a_shape_reading_that_would_change_start_is_refused_and_one_that_does_not_is_not():
    # the row's own event_date is 1998-06-01; its interval_start 1996-01-01 would open an earlier year: the owner's open point matters here
    sens = LEL(date(1998, 6, 1), shape="interval", interval_start=date(1996, 1, 1))
    _refuses(lambda: fully_dated_events([BIRTH_ROW, sens], birth_date=BIRTH), "lel_shape_reading_sensitive")
    benign = LEL(date(1998, 6, 1), shape="interval", interval_start=date(1998, 3, 1))              # same year: START is the same under both readings
    d = derive_chart_horizon_detail(BIRTH, [BIRTH_ROW, benign], BUILD)
    assert d["start"] == date(1998, 1, 1) and d["readings"]["interval_start"] == d["readings"]["event_date"]
    root = LEL(date(2005, 1, 1), event_id="EVT.2005.01.01.07")
    child = LEL(date(2006, 1, 1), shape="chain", chain_parent_event_id="EVT.2005.01.01.07", event_id="EVT.2006.01.01.08")
    assert derive_chart_horizon_detail(BIRTH, [BIRTH_ROW, root, child], BUILD)["start"] == date(2005, 1, 1)
    early_child = LEL(date(1999, 1, 1), shape="chain", chain_parent_event_id="EVT.2005.01.01.07", event_id="EVT.1999.01.01.08")
    _refuses(lambda: fully_dated_events([BIRTH_ROW, root, early_child], birth_date=BIRTH), "lel_shape_reading_sensitive")      # the root's date would open 2005
    dangling = LEL(date(2006, 1, 1), shape="chain", chain_parent_event_id="EVT.9999.01.01.99", event_id="EVT.2006.01.01.08")
    _refuses(lambda: fully_dated_events([BIRTH_ROW, dangling], birth_date=BIRTH), "lel_chain_unresolvable")


def test_an_unknown_confidence_or_shape_word_or_a_missing_date_is_refused_by_name():
    _refuses(lambda: fully_dated_events([BIRTH_ROW, LEL(date(2001, 6, 9), conf="circa")], birth_date=BIRTH), "lel_date_confidence_unknown")
    _refuses(lambda: fully_dated_events([BIRTH_ROW, LEL(date(2001, 6, 9), shape="blob")], birth_date=BIRTH), "lel_shape_unknown")
    _refuses(lambda: fully_dated_events([BIRTH_ROW, LEL(None, lel_id="EVT.2001.06.09.01")], birth_date=BIRTH), "lel_date_missing")


def test_the_horizon_cannot_start_before_the_substrate_domain_or_before_birth_or_in_the_future():
    _refuses(lambda: derive_chart_horizon(BIRTH, [BIRTH_ROW, LEL(date(1990, 5, 5))], BUILD), "horizon_start_before_substrate_domain")       # 1990-01-01 < 1998-01-01
    _refuses(lambda: derive_chart_horizon(BIRTH, [BIRTH_ROW, LEL(date(1983, 5, 1))], BUILD), "horizon_start_before_birth")                   # the reviewer's case
    _refuses(lambda: derive_chart_horizon(BIRTH, [BIRTH_ROW, LEL(date(2030, 3, 3))], BUILD), "horizon_start_in_future")
    assert derive_chart_horizon(BIRTH, [BIRTH_ROW, LEL(date(1998, 1, 1))], BUILD)[0] == date(1998, 1, 1)                                     # the domain start itself is fine


def test_a_leap_day_birth_without_an_anniversary_is_refused_by_name():
    _refuses(lambda: derive_chart_horizon(date(2000, 2, 29), [born(date(2000, 2, 29))], BUILD), "horizon_birth_anniversary_undefined")      # 2100 is not a leap year
    assert derive_chart_horizon(date(1904, 2, 29), [born(date(1904, 2, 29)), LEL(date(1999, 1, 2))], BUILD)[1] == date(2004, 2, 29)


def test_the_substrate_rule_FB3_at_both_edges_and_birth():
    p = mr.horizon_problem
    assert p(H) is None and p((date(1998, 1, 1), date(2085, 1, 1))) is None        # both domain edges themselves
    assert (p((date(1997, 12, 31), date(2084, 2, 5))) or "").startswith("horizon_start_before_substrate_domain")
    assert (p((H[0], date(2085, 1, 2))) or "").startswith("horizon_outside_substrate_domain")
    assert (p((date(2030, 1, 1), date(2030, 1, 1))) or "").startswith("horizon_empty")
    assert p(H, birth_date=BIRTH) is None and (p(H, birth_date=date(1999, 1, 1)) or "").startswith("horizon_start_before_birth")


# ── stored bounds (the builder stores tz-aware instants / tstzrange bounds) ──────────────────────────────────────
def test_stored_bounds_normalise_to_utc_midnight_dates_and_anything_else_is_a_named_refusal():
    ist = timezone(timedelta(hours=5, minutes=30))
    assert as_utc_date(date(1998, 1, 1)) == date(1998, 1, 1)
    assert as_utc_date(T(1998, 1, 1)) == date(1998, 1, 1)
    assert as_utc_date(datetime(1998, 1, 1, 5, 30, tzinfo=ist)) == date(1998, 1, 1)          # 05:30 IST is 00:00 UTC
    assert as_utc_date("1998-01-01") == date(1998, 1, 1) and as_utc_date("1998-01-01T00:00:00+00:00") == date(1998, 1, 1)
    with pytest.raises(MeasuringReportError, match="horizon_bound_not_midnight"):
        as_utc_date(T(1998, 1, 1, 0, 1))
    with pytest.raises(MeasuringReportError, match="horizon_bound_not_midnight"):
        as_utc_date(datetime(1998, 1, 1, 0, 0, tzinfo=ist))                                  # IST midnight is 18:30 UTC the day before
    with pytest.raises(MeasuringReportError, match="naive_datetime"):
        as_utc_date(datetime(1998, 1, 1))
    with pytest.raises(MeasuringReportError, match="horizon_bound_unreadable"):
        as_utc_date("soon")
    with pytest.raises(MeasuringReportError, match="horizon_bound_unreadable"):
        as_utc_date(19980101)


# ── day arithmetic ───────────────────────────────────────────────────────────────────────────────────────────────
def test_a_day_is_admitted_by_a_positive_overlap_and_midnight_ends_do_not_spill():
    assert admitted_days([(T(2000, 1, 1), T(2000, 1, 2))], H) == 1                # exactly one day
    assert admitted_days([(T(2000, 1, 1, 23, 59), T(2000, 1, 2, 0, 1))], H) == 2  # two minutes across midnight
    assert admitted_days([(T(2000, 1, 1, 6), T(2000, 1, 1, 7))], H) == 1          # an hour inside one day
    assert admitted_days([(T(2000, 1, 1, 6), T(2000, 1, 1, 6))], H) == 0          # zero length


def test_intervals_sharing_a_day_count_it_once_and_overlaps_are_not_double_counted():
    ivs = [(T(2000, 1, 1, 0), T(2000, 1, 1, 10)), (T(2000, 1, 1, 14), T(2000, 1, 2, 3)),
           (T(2000, 1, 5), T(2000, 1, 8)), (T(2000, 1, 6), T(2000, 1, 7))]
    assert admitted_days(ivs, H) == 2 + 3                                         # Jan 1,2 and Jan 5,6,7


def test_intervals_are_clipped_to_the_horizon_both_sides():
    ivs = [(T(1997, 12, 30), T(1998, 1, 3)), (T(2084, 2, 3), T(2084, 3, 1))]
    assert admitted_days(ivs, H) == 2 + 2                                         # Jan 1,2 1998; Feb 3,4 2084


def test_a_naive_instant_and_an_inverted_interval_are_refused():
    with pytest.raises(MeasuringReportError, match="naive_datetime"):
        admitted_days([(datetime(2000, 1, 1), datetime(2000, 1, 2))], H)
    with pytest.raises(MeasuringReportError, match="interval_inverted"):
        admitted_days([(T(2000, 1, 3), T(2000, 1, 1))], H)


def test_length_distribution_definitions_and_the_honest_null():
    assert length_distribution([]) == {"count": 0, "median": None, "p90": None, "max": None}
    assert length_distribution([5.0]) == {"count": 1, "median": 5.0, "p90": 5.0, "max": 5.0}
    d = length_distribution(list(range(1, 11)))                       # 1..10: median 5.5, p90 = 9th smallest = 9
    assert d == {"count": 10, "median": 5.5, "p90": 9, "max": 10}
    assert length_distribution([4, 1, 3])["median"] == 3              # unsorted input, odd count


# ── the share report (FB-50) ─────────────────────────────────────────────────────────────────────────────────────
def _rec(cls, path, agent, *spans, via="base"):
    return SupportRecord(cls, path, agent, tuple(spans), via)


def _p4(agent, lo, hi, via="base", cls="marriage"):
    return _rec(cls, "P4", agent, (lo, hi), via=via)


def test_shares_by_path_fast_slow_union_and_per_agent_contribution_with_p4_as_an_intersection():
    d = lambda n, h=0: T(2000, 1, n, h)                                            # noqa: E731
    recs = [
        _rec("marriage", "P3", "venus", (d(1), d(4))),                             # fast: Jan 1,2,3
        _rec("marriage", "P3", "jupiter", (d(3), d(6))),                           # slow: Jan 3,4,5
        _rec("marriage", "P3", "saturn", (d(10), d(11))),                          # slow: Jan 10
        _p4("jupiter", d(3), d(6)),                                                # Jupiter influence Jan 3,4,5
        _p4("saturn", d(4, 12), d(8)),                                             # Saturn influence from Jan 4 12:00 to Jan 8
        _rec("marriage", "P2", "moon", (d(20), d(22))),                            # P2: Jan 20,21
    ]
    r = class_share_report(recs, [], H)["classes"]["marriage"]
    days = r["admitted_days"]
    assert days["P3_fast"] == 3 and days["P3_slow"] == 4 and days["P3_union"] == 6      # {1,2,3} ∪ {3,4,5,10}
    # P4 = Jupiter ∩ Saturn at the instant level: [Jan 4 12:00, Jan 6) -> Jan 4 and Jan 5 = 2 days (a UNION would be 5)
    assert days["P4_without_dvi"] == 2 and days["P4_with_dvi"] == 2 and days["P2"] == 2
    assert days["class_union"] == 8                                                # P3's 6 + P2's 2; P4's two days lie inside P3's
    assert days["P1_base"] == 0 and days["kb_only"] == 0
    assert r["admitted_share"]["P3_union"] == 6 / H_DAYS
    # per agent over P1-P3 records: venus {1,2,3} exclusive {1,2}; jupiter {3,4,5} exclusive {4,5}; saturn {10}; moon {20,21}; P4 is joint
    # `exclusive_days` is against the other agents' P1-P3 records; `exclusive_days_vs_class` also removes the P4 intersection {Jan 4, 5}:
    assert r["per_agent"]["venus"] == {"days": 3, "exclusive_days": 2, "exclusive_days_vs_class": 2}
    # removing Jupiter removes its P3 days {3,4,5}... of which only {4,5} are left uncovered by Venus, AND it breaks the P4 intersection: 2 days lost
    assert r["per_agent"]["jupiter"] == {"days": 3, "exclusive_days": 2, "exclusive_days_vs_class": 2}
    # removing Saturn removes P3 {10} and breaks P4 (Jupiter alone), whose days {4,5} stay covered by Jupiter's P3: 1 day lost
    assert r["per_agent"]["saturn"] == {"days": 1, "exclusive_days": 1, "exclusive_days_vs_class": 1}
    assert r["per_agent"]["moon"] == {"days": 2, "exclusive_days": 2, "exclusive_days_vs_class": 2}
    assert r["P4_joint"] == {"without_dvi_days": 2, "with_dvi_days": 2}


def test_p4_is_the_intersection_of_the_two_agents_instants_not_their_union_and_not_a_day_set_intersection():
    cls = lambda recs: class_share_report(recs, [], H)["classes"]["marriage"]["admitted_days"]            # noqa: E731
    d = lambda n, h=0: T(2000, 1, n, h)                                            # noqa: E731
    # the reviewer's input: Jupiter [Jan 1, Jan 6), Saturn [Jan 4, Jan 9) -> Jan 4,5 = 2 days (a union is 8)
    assert cls([_p4("jupiter", d(1), d(6)), _p4("saturn", d(4), d(9))])["P4_without_dvi"] == 2
    # disjoint supports -> 0 (a union is positive)
    assert cls([_p4("jupiter", d(1), d(3)), _p4("saturn", d(5), d(8))])["P4_without_dvi"] == 0
    # one agent alone -> 0
    assert cls([_p4("jupiter", d(1), d(6))])["P4_without_dvi"] == 0
    # same calendar day, disjoint instants (morning vs afternoon): a day-set intersection would say 1, the instant intersection says 0
    assert cls([_p4("jupiter", d(4), d(4, 12)), _p4("saturn", d(4, 12), d(5))])["P4_without_dvi"] == 0
    # several records per agent are unioned first, then intersected
    assert cls([_p4("jupiter", d(1), d(3)), _p4("jupiter", d(5), d(7)), _p4("saturn", d(2), d(6))])["P4_without_dvi"] == 2   # Jan 2 and Jan 5
    # the class union takes the P4 INTERSECTION, not the union of the two agents
    assert cls([_p4("jupiter", d(1), d(6)), _p4("saturn", d(4), d(9))])["class_union"] == 2


def test_k_b_and_dvi_enter_the_p4_variants_through_the_agents_influence():
    d = lambda m, n: T(2000, m, n)                                                  # noqa: E731
    recs = [
        _rec("marriage", "P1", "venus", (d(2, 1), d(2, 3))),                       # base P1: Feb 1,2
        _rec("marriage", "P1", "jupiter", (d(2, 10), d(2, 12)), via="karakatva"),  # extension: Feb 10,11
        _p4("saturn", d(2, 20), d(2, 23)), _p4("jupiter", d(2, 20), d(2, 23)),     # base P4: Feb 20,21,22
        _p4("jupiter", d(2, 25), d(2, 27), via="dvi"), _p4("saturn", d(2, 25), d(2, 27), via="dvi"),   # DVI both: Feb 25,26
        _rec("marriage", "P3", "saturn", (d(2, 20), d(2, 23))),                    # base P3 covers 20-22
        _rec("marriage", "P3", "saturn", (d(2, 28), d(2, 29)), via="kb"),          # K-B in P3 only: Feb 28
        _p4("jupiter", d(3, 3), d(3, 5), via="kb"), _p4("saturn", d(3, 4), d(3, 6), via="kb"),        # K-B in P4: the two agents overlap on Mar 4
    ]
    days = class_share_report(recs, [], H)["classes"]["marriage"]["admitted_days"]
    assert days["P1_base"] == 2 and days["P1_with_karakatva"] == 4
    assert days["P4_without_dvi"] == 3 + 1                                         # base Feb 20-22 plus the K-B overlap Mar 4
    assert days["P4_with_dvi"] == 3 + 1 + 2                                        # plus the DVI days Feb 25,26
    assert days["kb_only"] == 2                                                    # Feb 28 (P3 K-B) and Mar 4 (P4 K-B) are admitted only through K-B
    assert days["P3_union"] == 4                                                   # base 20-22 plus the K-B day 28
    plain = class_share_report([r for r in recs if r.via == "base"], [], H)["classes"]["marriage"]["admitted_days"]
    assert plain["P1_with_karakatva"] == plain["P1_base"] == 2 and plain["P4_with_dvi"] == plain["P4_without_dvi"] == 3 and plain["kb_only"] == 0


def test_an_admitted_testimony_record_is_refused_in_a_scored_share_and_a_p4_agent_must_be_jupiter_or_saturn():
    ok = (T(2001, 1, 1), T(2001, 1, 11))
    _refuses(lambda: class_share_report([SupportRecord("marriage", "P1", "venus", (ok,), "base", "testimony")], [], H), "testimony_record_in_scored_share")
    _refuses(lambda: class_share_report([_p4("mars", *ok)], [], H), "p4_agent_not_jupiter_or_saturn")


def test_the_two_grids_are_labelled_and_never_mixed_the_scorers_convention_is_ist_inclusive_10334():
    from services.gochara_eval import registry as scorer
    assert mr._SCORER_H0 == scorer.H0 and mr._SCORER_H1 == scorer.H1 and mr.SCORED_DAYS == scorer.H_DAYS == 10334
    g = mr.scored_grid()
    assert (g.label, g.days) == ("ist_inclusive", 10334) and g.hi - g.lo == timedelta(days=10334)
    b = mr.build_grid(H)
    assert (b.label, b.days) == ("utc_half_open", H_DAYS)
    recs = [_rec("marriage", "P3", "sun", (T(2000, 1, 1), T(2000, 1, 11)))]                     # 10 days
    assert class_share_report(recs, [], H)["convention"] == "utc_half_open"
    sc = mr.scored_share_report(recs, [])
    assert sc["convention"] == "ist_inclusive" and sc["horizon_days"] == 10334 and sc["horizon"] == ["1998-01-01", "2026-04-17"]
    # 2000-01-01T00:00Z is 05:30 IST on Jan 1; 2000-01-11T00:00Z is 05:30 IST on Jan 11: ten days become ELEVEN IST calendar days
    assert sc["classes"]["marriage"]["admitted_days"]["P3_union"] == 11


def test_the_ist_day_boundary_is_18_30_utc_and_the_scored_horizon_includes_the_17th_of_april_2026():
    one_ist_day = [_rec("marriage", "P3", "sun", (datetime(2000, 1, 1, 18, 30, tzinfo=timezone.utc), datetime(2000, 1, 2, 18, 30, tzinfo=timezone.utc)))]
    # the scorer's rule: the IST dates from the start's date THROUGH the end's date, inclusive: this window starts at IST 2000-01-02 00:00 and ends at
    # IST 2000-01-03 00:00 exactly, so it counts BOTH dates (2) — a positive-overlap rule would say 1
    assert mr.scored_share_report(one_ist_day, [])["classes"]["marriage"]["admitted_days"]["P3_union"] == 2
    last = [_rec("marriage", "P3", "sun", (datetime(2026, 4, 16, 18, 30, tzinfo=timezone.utc), datetime(2026, 4, 17, 18, 30, tzinfo=timezone.utc)))]
    after = [_rec("marriage", "P3", "sun", (datetime(2026, 4, 17, 18, 30, tzinfo=timezone.utc), datetime(2026, 4, 18, 18, 30, tzinfo=timezone.utc)))]
    assert mr.scored_share_report(last, [])["classes"]["marriage"]["admitted_days"]["P3_union"] == 1           # 17 April IST: inside
    assert mr.scored_share_report(after, [])["classes"]["marriage"]["admitted_days"]["P3_union"] == 0          # 18 April IST: outside


def test_the_forty_percent_guard_input_flips_on_the_scorers_convention_and_not_on_the_build_one():
    # the reviewer's guard-flipping input: matching Jupiter and Saturn P4 supports over 4,133 UTC days plus the observation-end day
    first = (T(1998, 1, 1), T(2009, 4, 26))                                                     # 4,133 UTC days
    last = (T(2026, 4, 17), T(2026, 4, 18))
    recs = [SupportRecord("marriage", "P4", a, (first, last), "base") for a in ("jupiter", "saturn")]
    sc = mr.scored_share_report(recs, [])["classes"]["marriage"]
    # IST: 2009-04-26T00:00Z is 05:30 IST on the 26th (that day is touched) -> 4,134 days; the observation-end day adds 1 -> 4,135 of 10,334
    assert sc["admitted_days"]["P4_with_dvi"] == 4135 and sc["admitted_share"]["P4_with_dvi"] == 4135 / 10334
    assert sc["admitted_share"]["P4_with_dvi"] > 0.40                                          # the guard fires on the scorer's grid
    # the half-open UTC half-open 10,333-day grid would give 4,133 + 0 = 4,133 / 10,333 = 39.998 percent: NOT the number the guard uses
    assert 4133 / 10333 < 0.40 < 4135 / 10334


def test_extension_variants_equal_base_when_absent():
    d = lambda n: T(2000, 2, n)                                                    # noqa: E731
    recs = [_rec("marriage", "P1", "venus", (d(1), d(3)))]
    days = class_share_report(recs, [], H)["classes"]["marriage"]["admitted_days"]
    assert days["P1_with_karakatva"] == days["P1_base"] == 2 and days["P4_with_dvi"] == days["P4_without_dvi"] == 0 and days["kb_only"] == 0


def test_classes_are_reported_independently():
    recs = [_rec("marriage", "P3", "sun", (T(2001, 1, 1), T(2001, 1, 2))),
            _rec("surgery", "P3", "sun", (T(2001, 1, 1), T(2001, 1, 3)))]
    out = class_share_report(recs, [], H)["classes"]
    assert sorted(out) == ["marriage", "surgery"]
    assert out["marriage"]["admitted_days"]["P3_union"] == 1 and out["surgery"]["admitted_days"]["P3_union"] == 2


def test_window_length_distribution_per_path_and_scoring_clip_leave_the_stored_windows_alone():
    wins = [("marriage", "P3", T(2000, 1, 1), T(2000, 1, 3)), ("marriage", "P3", T(2000, 2, 1), T(2000, 2, 11)),
            ("marriage", "P4", T(2000, 3, 1), T(2000, 3, 2))]
    out = class_share_report([], wins, H)["classes"]["marriage"]["window_lengths_days"]
    assert out["P3"] == {"count": 2, "median": 6.0, "p90": 10.0, "max": 10.0}      # lengths 2 and 10
    assert out["P4"]["count"] == 1 and out["P1"]["count"] == 0 and out["P1"]["median"] is None
    # FB-5: served, not scored, after 2026-04-17: a straddling window is cut, one after is dropped, input untouched
    end = T(2026, 4, 17)
    stored = [("marriage", "P3", T(2026, 4, 10), T(2026, 4, 25)), ("marriage", "P3", T(2026, 5, 1), T(2026, 5, 2)),
              ("marriage", "P3", T(2020, 1, 1), T(2020, 1, 2))]
    clipped = clip_windows_for_scoring(stored, end)
    assert clipped == [("marriage", "P3", T(2026, 4, 10), end), ("marriage", "P3", T(2020, 1, 1), T(2020, 1, 2))]
    assert stored[0][3] == T(2026, 4, 25)


@pytest.mark.parametrize("agent", ["Jupiter", "JUPITER", " jupiter", "pluto", "", None])
def test_an_unknown_or_differently_cased_agent_is_refused_never_a_silent_zero(agent):
    with pytest.raises(MeasuringReportError, match="unknown_agent"):
        class_share_report([_rec("marriage", "P3", agent, (T(2001, 1, 1), T(2001, 1, 2)))], [], H)


def test_the_nine_agents_all_pass_and_partition_into_fast_and_slow_so_no_agent_can_fall_in_neither():
    recs = [_rec("marriage", "P3", a, (T(2001, 1, 1), T(2001, 1, 2))) for a in sorted(mr.ALL_AGENTS)]
    days = class_share_report(recs, [], H)["classes"]["marriage"]["admitted_days"]
    assert len(mr.ALL_AGENTS) == 9 and days["P3_fast"] == 1 and days["P3_slow"] == 1 and days["P3_union"] == 1
    assert not mr.FAST_AGENTS & mr.SLOW_AGENTS and mr.P4_AGENTS <= mr.SLOW_AGENTS
    one_each = {a: class_share_report([_rec("marriage", "P3", a, (T(2001, 1, 1), T(2001, 1, 2)))], [], H)["classes"]["marriage"]["admitted_days"]
                for a in mr.ALL_AGENTS}
    assert all(d["P3_fast"] + d["P3_slow"] == 1 for d in one_each.values())            # each agent lands in exactly one


def test_an_unknown_path_via_window_path_and_an_inverted_interval_are_refused_and_so_is_an_empty_horizon():
    ok = (T(2001, 1, 1), T(2001, 1, 2))
    with pytest.raises(MeasuringReportError, match="unknown_path"):
        class_share_report([_rec("marriage", "P5", "sun", ok)], [], H)
    with pytest.raises(MeasuringReportError, match="unknown_path"):
        class_share_report([], [("marriage", "P9", ok[0], ok[1])], H)                  # a window with an unknown path is not dropped
    with pytest.raises(MeasuringReportError, match="unknown_via"):
        class_share_report([_rec("marriage", "P3", "sun", ok, via="Base")], [], H)
    with pytest.raises(MeasuringReportError, match="interval_inverted"):
        class_share_report([_rec("marriage", "P3", "sun", (T(2001, 1, 3), T(2001, 1, 1)))], [], H)
    with pytest.raises(MeasuringReportError, match="interval_inverted"):
        class_share_report([], [("marriage", "P3", T(2001, 1, 3), T(2001, 1, 1))], H)
    with pytest.raises(MeasuringReportError, match="horizon_empty"):
        class_share_report([], [], (date(2030, 1, 1), date(2030, 1, 1)))


# ── near-misses: reported, never added (FB-29) ────────────────────────────────────────────────────────────────────
def test_near_miss_counts_is_a_pure_tally_of_what_it_is_given():
    counts = near_miss_counts([("marriage", "aspect", "jupiter"), ("marriage", "aspect", "jupiter"), ("surgery", "conjunction", "mars")])
    assert counts == {"total": 3, "by_class_relation_body": {"marriage|aspect|jupiter": 2, "surgery|conjunction|mars": 1}}
    assert near_miss_counts([]) == {"total": 0, "by_class_relation_body": {}}
    # NOT claimed: layer-on/off noninterference. The share report takes no near-miss input, so there is nothing to switch; that proof belongs to the
    # builder-side on/off comparison of the real scored outputs (near_miss_verifier.noninterference_problems compares two such output sets).


# ── acceptance of the measuring build (§13) ──────────────────────────────────────────────────────────────────────
ALL26 = frozenset(mr.SCORED_CLASSES)
HOLDING_PATHS = frozenset({("marriage", "P3"), ("surgery", "P2"), ("bereavement", "P4"), ("spiritual_turn", "P2")})     # the eight hold P2 rows today


def _view(**kw):
    base = dict(stored_scope="test_slice", run="all_classes_full", sealed=False, published=False, horizon=H,
                rule_versions=frozenset({"1.0.0"}), near_miss_rows_stored=0, class_paths_with_rows=HOLDING_PATHS,
                marker_classes=ALL26, marker_horizon=H, marker_schema="gochara_v5_test_slice/1", marker_digest="d" * 64)
    base.update(kw)
    return MeasuringBuildView(**base)


def test_a_faithful_measuring_build_is_accepted_in_date_form_and_in_the_stored_instant_form():
    assert measuring_refusals(_view(), expected_horizon=H, birth_date=BIRTH) == []
    stored = (T(1998, 1, 1), T(2084, 2, 5))                                 # what a tstzrange read returns
    assert measuring_refusals(_view(horizon=stored, marker_horizon=stored), expected_horizon=H, birth_date=BIRTH) == []
    assert measuring_refusals(_view(horizon=stored, marker_horizon=("1998-01-01", "2084-02-05")), expected_horizon=stored) == []


@pytest.mark.parametrize("kw,code", [
    (dict(stored_scope="full"), "measuring_scope_not_test_slice"),
    (dict(stored_scope=None), "measuring_scope_not_test_slice"),
    (dict(run="one_class_full"), "measuring_run_not_all_classes_full"),
    (dict(sealed=True), "measuring_build_sealed"),
    (dict(published=True), "measuring_build_published"),
    (dict(horizon=(date(1998, 2, 16), date(2084, 2, 5))), "horizon_mismatch"),
    (dict(horizon=(date(1998, 1, 1), date(2085, 1, 2))), "horizon_outside_substrate_domain"),
    (dict(horizon=(date(1997, 1, 1), date(2084, 2, 5))), "horizon_start_before_substrate_domain"),
    (dict(horizon=(T(1998, 1, 1, 0, 1), T(2084, 2, 5))), "horizon_bound_not_midnight"),
    (dict(horizon=(datetime(1998, 1, 1), T(2084, 2, 5))), "naive_datetime"),
    (dict(marker_horizon=(date(1998, 2, 16), date(2084, 2, 5))), "marker_horizon_mismatch"),
    (dict(rule_versions=frozenset({"1.0.0", "1.2.0"})), "rule_version_not_in_scope"),
    (dict(rule_versions=frozenset({"9.9.9"})), "rule_version_not_in_scope"),
    (dict(rule_versions=frozenset({"1.0.0", "1.1.0"})), "rule_version_not_in_scope"),
    (dict(near_miss_rows_stored=3), "near_miss_rows_stored"),
    (dict(class_paths_with_rows=HOLDING_PATHS | {("spiritual_turn", "P3")}), "excluded_path_has_rows"),
    (dict(class_paths_with_rows=HOLDING_PATHS | {("parental_event", "P1")}), "excluded_path_has_rows"),
    (dict(class_paths_with_rows=HOLDING_PATHS | {("achievement_recognition", "P4")}), "excluded_path_has_rows"),
    (dict(class_paths_with_rows=frozenset({("marriage", "P3"), ("pluto_transit", "P3")})), "unknown_class_has_rows"),
    (dict(marker_horizon=None), "marker_incomplete"),
    (dict(marker_schema=None), "marker_incomplete"),
    (dict(marker_schema="other/1"), "marker_incomplete"),
    (dict(marker_digest=None), "marker_incomplete"),
    (dict(marker_digest=""), "marker_incomplete"),
    (dict(marker_classes=frozenset()), "class_census_mismatch"),
    (dict(marker_classes=frozenset({"marriage"})), "class_census_mismatch"),
    (dict(marker_classes=ALL26 | {"birth_anchor"}), "class_census_mismatch"),
])
def test_each_departure_from_the_measuring_shape_is_refused_by_name(kw, code):
    out = measuring_refusals(_view(**kw), expected_horizon=H)
    assert any(x.startswith(code) for x in out), out


def test_an_instant_horizon_never_raises_a_type_error_and_a_non_midnight_one_never_emits_a_false_mismatch():
    out = measuring_refusals(_view(horizon=(T(1998, 1, 1, 6), T(2084, 2, 5))), expected_horizon=H)
    assert any(x.startswith("horizon_bound_not_midnight") for x in out) and not any(x.startswith("horizon_mismatch") for x in out)


def test_the_horizon_before_birth_is_refused_when_the_birth_is_known():
    out = measuring_refusals(_view(), expected_horizon=H, birth_date=date(1999, 1, 1))
    assert any(x.startswith("horizon_start_before_birth") for x in out)


def test_the_scored_class_table_is_the_26_of_the_27_registered_minus_the_annotation():
    assert len(mr.SCORED_CLASSES) == 26 and "birth_anchor" not in mr.SCORED_CLASSES
    assert mr.EXCLUDED_EIGHT < mr.SCORED_CLASSES and "bereavement" in mr.SCORED_CLASSES


def test_the_eight_excluded_classes_are_exactly_these_eight_names_and_the_bound_versions_are_exactly_1_0_0():
    assert mr.EXCLUDED_EIGHT == frozenset({
        "achievement_recognition", "business_launch", "financial_deception", "foreign_settlement",
        "parental_event", "property_acquisition", "psychological_arc", "spiritual_turn"})
    assert mr.ALLOWED_RULE_VERSIONS == frozenset({"1.0.0"})


def test_several_departures_are_all_named_not_just_the_first():
    out = measuring_refusals(_view(sealed=True, near_miss_rows_stored=1, run="all_classes_1y"), expected_horizon=H)
    assert len(out) == 3


# ── the readers' refusals, on a scripted connection (the real schema forbids most of these shapes, so they cannot be seeded) ──────────
class _Result:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _Conn:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, sql, params=()):
        return _Result(self._rows)


def _row(cls="marriage", path="P3", version="1.0.0", agent="saturn", lo=T(2000, 1, 1), hi=T(2000, 1, 5), lo_inf=False, hi_inf=False):
    return (cls, path, version, agent, lo, hi, lo_inf, hi_inf)


def test_read_records_accepts_a_bounded_bound_row_and_a_record_with_no_support_interval():
    recs = mr.read_records(_Conn([_row(), _row(agent="venus", lo=None, hi=None)]), "c", "g")
    assert recs == [mr.SupportRecord("marriage", "P3", "saturn", ((T(2000, 1, 1), T(2000, 1, 5)),), "base"),
                    mr.SupportRecord("marriage", "P3", "venus", (), "base")]


@pytest.mark.parametrize("row,code", [
    (_row(hi=None, hi_inf=True), "support_interval_unbounded"),
    (_row(lo=None, lo_inf=True), "support_interval_unbounded"),
    (_row(hi=None), "support_interval_unbounded"),
    (_row(path="P5"), "unknown_path_id"),
    (_row(version="1.2.0"), "rule_version_not_in_scope"),
    (_row(version="1.1.0"), "rule_version_not_in_scope"),
    (_row(agent="Saturn"), "unknown_agent"),
])
def test_read_records_refuses_each_unreadable_stored_shape_by_name(row, code):
    with pytest.raises(MeasuringReportError, match=code):
        mr.read_records(_Conn([row]), "c", "g")


def test_read_measuring_view_refuses_several_manifests_rather_than_picking_one():
    two = [("candidate", {}, T(1998, 1, 1), T(2084, 2, 5)), ("published", {}, T(1998, 1, 1), T(2084, 2, 5))]
    with pytest.raises(MeasuringReportError, match="measuring_manifest_ambiguous"):
        mr.read_measuring_view(_Conn(two), "c", "g")


# ── amendments of review VERIFIER-FABLE-2 (3185) ────────────────────────────────────────────────────────────────
def test_an_empty_generation_is_not_a_measuring_build():
    out = measuring_refusals(_view(class_paths_with_rows=frozenset()), expected_horizon=H)
    assert any(x.startswith("measuring_build_holds_no_rows") for x in out), out
    assert not any(x.startswith("measuring_build_holds_no_rows") for x in measuring_refusals(_view(), expected_horizon=H))


@pytest.mark.parametrize("status", ["superseded", "rolled_back", "weird"])
def test_a_publication_status_other_than_candidate_or_published_is_named(status):
    assert any(x.startswith("measuring_status_not_candidate") for x in measuring_refusals(_view(status=status), expected_horizon=H))
    assert not any(x.startswith("measuring_status_not_candidate") for x in measuring_refusals(_view(status="candidate"), expected_horizon=H))


def test_an_absent_near_miss_store_is_unknown_not_zero():
    assert measuring_refusals(_view(near_miss_rows_stored=None), expected_horizon=H) == []                # unknown: no claim either way
    assert any(x.startswith("near_miss_rows_stored") for x in measuring_refusals(_view(near_miss_rows_stored=1), expected_horizon=H))


@pytest.mark.parametrize("via,path,ok", [("dvi", "P4", True), ("dvi", "P3", False), ("kb", "P3", True), ("kb", "P4", True), ("kb", "P1", False),
                                          ("karakatva", "P1", True), ("karakatva", "P3", False), ("base", "P2", True)])
def test_an_extension_tag_is_valid_only_on_its_own_paths(via, path, ok):
    rec = [_rec("marriage", path, "saturn", (T(2001, 1, 1), T(2001, 1, 2)), via=via)]
    if ok:
        class_share_report(rec, [], H)
    else:
        with pytest.raises(MeasuringReportError, match="via_not_valid_for_path"):
            class_share_report(rec, [], H)


def test_the_eight_classes_may_hold_p2_rows_today_and_a_faithful_build_with_them_is_accepted():
    view = _view(class_paths_with_rows=frozenset({(c, "P2") for c in mr.EXCLUDED_EIGHT} | {("marriage", "P3"), ("bereavement", "P1")}))
    assert measuring_refusals(view, expected_horizon=H) == []


def test_the_scorers_numerator_counts_the_end_date_so_a_support_ending_at_ist_midnight_flips_the_guard():
    # [1998-01-01T00:00Z, 2009-04-25T18:30Z): the end is exactly IST midnight of 2009-04-26. A positive-overlap rule counts 4,133 days (39.994%);
    # the scorer's inclusive date pair counts 1998-01-01 .. 2009-04-26 = 4,134 (40.004%)
    sup = (T(1998, 1, 1), datetime(2009, 4, 25, 18, 30, tzinfo=timezone.utc))
    recs = [SupportRecord("marriage", "P4", a, (sup,), "base") for a in ("jupiter", "saturn")]
    sc = mr.scored_share_report(recs, [])["classes"]["marriage"]
    assert sc["admitted_days"]["P4_with_dvi"] == 4134 and sc["admitted_share"]["P4_with_dvi"] == 4134 / 10334 > 0.40
    assert 4133 / 10334 < 0.40                                                      # the old count would not have fired the guard
    # the scorer's own day counting agrees on the same date pair
    from services.gochara_eval.extract import MergedWindow
    w = MergedWindow(cls="marriage", ws=date(1998, 1, 1), we=date(2009, 4, 26), pk=date(1998, 1, 1), si=0.0)
    assert w.days_in_horizon(date(1998, 1, 1), date(2026, 4, 17)) == 4134


def test_a_p3_day_that_p4_already_admits_is_not_exclusive_to_the_agent_against_the_class():
    d = lambda n: T(2000, 1, n)                                                    # noqa: E731
    recs = [_rec("marriage", "P3", "venus", (d(1), d(3))), _p4("jupiter", d(1), d(3)), _p4("saturn", d(1), d(3))]
    pa = class_share_report(recs, [], H)["classes"]["marriage"]["per_agent"]["venus"]
    assert pa["exclusive_days"] == 2 and pa["exclusive_days_vs_class"] == 0         # fully covered by the P4 intersection: nothing is exclusive


def test_the_marker_digest_is_never_presented_as_verified_and_a_malformed_one_is_refused():
    v = _view()
    assert v.marker_digest_verified is None and v.marker_digest_reason == "not_checked_by_verifier_steward_stamp_proof"
    assert measuring_refusals(v, expected_horizon=H) == []                         # well-formed: accepted, but not 'verified'
    for bad in ("garbage", "d" * 63, "d" * 65, "D" * 64, "g" * 64, "zz" + "d" * 62):
        assert any(x.startswith("marker_digest_malformed") for x in measuring_refusals(_view(marker_digest=bad), expected_horizon=H)), bad


def test_an_agents_contribution_against_complete_class_admission_includes_the_p4_it_breaks():
    d = lambda n: T(2000, 1, n)                                                    # noqa: E731
    ten = (d(1), d(11))
    recs = [_rec("marriage", "P3", "jupiter", ten), _p4("jupiter", *ten), _p4("saturn", *ten)]
    r = class_share_report(recs, [], H)["classes"]["marriage"]
    assert r["admitted_days"]["class_union"] == 10
    pa = r["per_agent"]
    assert pa["jupiter"]["exclusive_days_vs_class"] == 10                          # without Jupiter: no P3 and no P4 -> 0 days (the reviewer's input)
    assert pa["saturn"]["exclusive_days_vs_class"] == 0                            # without Saturn Jupiter's P3 still admits all ten days
    only_p4 = class_share_report([_p4("jupiter", *ten), _p4("saturn", *ten)], [], H)["classes"]["marriage"]["per_agent"]
    assert set(only_p4) == {"jupiter", "saturn"} and only_p4["jupiter"]["exclusive_days_vs_class"] == only_p4["saturn"]["exclusive_days_vs_class"] == 10


def test_a_digest_with_a_trailing_newline_or_any_extra_character_is_refused():
    for bad in ("d" * 64 + "\n", "d" * 64 + " ", "\n" + "d" * 64, "d" * 64 + "\x00"):
        assert any(x.startswith("marker_digest_malformed") for x in measuring_refusals(_view(marker_digest=bad), expected_horizon=H)), repr(bad)
    assert measuring_refusals(_view(marker_digest="a1" * 32), expected_horizon=H) == []
