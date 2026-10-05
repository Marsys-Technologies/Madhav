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


def LEL(d, precision="day", is_birth=False):
    return {"date": d, "precision": precision, "is_birth": is_birth}


# ── the horizon ──────────────────────────────────────────────────────────────────────────────────────────────────
def test_the_pinned_chart_horizon_is_1998_01_01_to_2084_02_05_and_has_the_measured_day_count():
    start, end, basis = derive_chart_horizon(BIRTH, [LEL(date(1998, 8, 20)), LEL(date(2003, 5, 1))], BUILD)
    assert (start, end, basis) == (date(1998, 1, 1), date(2084, 2, 5), "first_dated_event")
    assert mr.horizon_days((start, end)) == H_DAYS


def test_a_chart_with_no_dated_event_starts_at_the_build_date_and_two_dates_differ():
    a = derive_chart_horizon(BIRTH, [], BUILD)
    b = derive_chart_horizon(BIRTH, [LEL(None, "unknown")], BUILD + timedelta(days=1))
    assert a == (BUILD, date(2084, 2, 5), "build_date")
    assert a != b and b[0] == BUILD + timedelta(days=1)                       # the build date is IN the result


def test_the_build_date_is_a_utc_date_a_tz_aware_instant_is_taken_to_its_utc_date_and_a_naive_one_is_refused():
    late_ist = datetime(2026, 10, 5, 23, 30, tzinfo=timezone(timedelta(hours=5, minutes=30)))     # 18:00 UTC the same day
    early_ist = datetime(2026, 10, 6, 1, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))      # 19:30 UTC on the 5th
    assert derive_chart_horizon(BIRTH, [], late_ist)[0] == date(2026, 10, 5)
    assert derive_chart_horizon(BIRTH, [], early_ist)[0] == date(2026, 10, 5)
    with pytest.raises(MeasuringReportError, match="naive_datetime"):
        derive_chart_horizon(BIRTH, [], datetime(2026, 10, 5, 12))


def test_the_first_event_is_the_earliest_not_the_first_listed():
    rows = [LEL(date(2010, 3, 3)), LEL(date(1999, 12, 31))]
    assert derive_chart_horizon(BIRTH, rows, BUILD)[0] == date(1999, 1, 1)


def test_only_a_fully_dated_non_birth_event_counts_and_the_excluded_are_counted():
    rows = [LEL(date(1984, 2, 5), is_birth=True), LEL(date(1997, 7, 1), "year"), LEL(date(1997, 5, 1), "month"),
            LEL(None, "unknown"), LEL(date(1999, 4, 4), "approx"), LEL(date(2001, 6, 9), "day")]
    dates, excluded = fully_dated_events(rows)
    assert dates == [date(2001, 6, 9)] and excluded == 4                          # the birth entry is aside, not "excluded"
    d = derive_chart_horizon_detail(BIRTH, rows, BUILD)
    assert d["start"] == date(2001, 1, 1) and d["excluded_undated"] == 4 and d["basis"] == "first_dated_event"
    assert derive_chart_horizon_detail(BIRTH, [LEL(date(1997, 7, 1), "year")], BUILD)["basis"] == "build_date"   # a proxy date opens nothing


def test_an_unknown_precision_word_is_refused_by_name():
    with pytest.raises(MeasuringReportError, match="lel_precision_unknown"):
        fully_dated_events([LEL(date(2001, 6, 9), "circa")])


def test_the_horizon_cannot_start_before_the_substrate_domain_or_before_birth_or_in_the_future():
    with pytest.raises(MeasuringReportError, match="horizon_start_before_substrate_domain"):
        derive_chart_horizon(BIRTH, [LEL(date(1990, 5, 5))], BUILD)                # 1990-01-01 < 1998-01-01
    with pytest.raises(MeasuringReportError, match="horizon_start_before_birth"):
        derive_chart_horizon(BIRTH, [LEL(date(1983, 5, 1))], BUILD)               # the reviewer's case: 1983-01-01 is before birth
    with pytest.raises(MeasuringReportError, match="horizon_start_in_future"):
        derive_chart_horizon(BIRTH, [LEL(date(2030, 3, 3))], BUILD)
    assert derive_chart_horizon(BIRTH, [LEL(date(1998, 1, 1))], BUILD)[0] == date(1998, 1, 1)   # the domain start itself is fine


def test_a_leap_day_birth_without_an_anniversary_is_refused_by_name():
    with pytest.raises(MeasuringReportError, match="horizon_birth_anniversary_undefined"):
        derive_chart_horizon(date(2000, 2, 29), [], BUILD)                           # 2100 is not a leap year
    assert derive_chart_horizon(date(1904, 2, 29), [LEL(date(1999, 1, 2))], BUILD)[1] == date(2004, 2, 29)


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


def test_shares_by_path_fast_slow_union_and_per_agent_contribution():
    d = lambda n: T(2000, 1, n)                                                    # noqa: E731
    recs = [
        _rec("marriage", "P3", "venus", (d(1), d(4))),                             # fast: Jan 1,2,3
        _rec("marriage", "P3", "jupiter", (d(3), d(6))),                           # slow: Jan 3,4,5
        _rec("marriage", "P3", "saturn", (d(10), d(11))),                          # slow: Jan 10
        _rec("marriage", "P4", "jupiter", (d(3), d(6))),                           # P4 alone: Jan 3,4,5
        _rec("marriage", "P2", "moon", (d(20), d(22))),                            # P2: Jan 20,21
    ]
    r = class_share_report(recs, [], H)["classes"]["marriage"]
    days = r["admitted_days"]
    assert days["P3_fast"] == 3 and days["P3_slow"] == 4 and days["P3_union"] == 6      # {1,2,3} ∪ {3,4,5,10}
    # P4-alone is the P4 path's OWN union: Jan 3,4,5 even though P3 already admits those days
    assert days["P4_without_dvi"] == 3 and days["P4_with_dvi"] == 3 and days["P2"] == 2
    assert days["class_union"] == 8                                                # 6 + P2's 2 (P4 inside P3's days)
    assert days["P1_base"] == 0 and days["kb_only"] == 0
    assert r["admitted_share"]["P3_union"] == 6 / H_DAYS
    # per agent: venus {1,2,3} exclusive {1,2}; jupiter {3,4,5} (P3 and P4) exclusive {4,5}; saturn {10}; moon {20,21}
    assert r["per_agent"]["venus"] == {"days": 3, "exclusive_days": 2}
    assert r["per_agent"]["jupiter"] == {"days": 3, "exclusive_days": 2}
    assert r["per_agent"]["saturn"] == {"days": 1, "exclusive_days": 1}
    assert r["per_agent"]["moon"] == {"days": 2, "exclusive_days": 2}


def test_the_forty_percent_comparison_is_over_the_scored_horizon_not_the_build_horizon():
    assert mr.SCORED_HORIZON == (date(1998, 1, 1), date(2026, 4, 17))
    recs = [_rec("marriage", "P4", "saturn", (T(2000, 1, 1), T(2000, 1, 11)))]                # 10 days
    build = class_share_report(recs, [], H)["classes"]["marriage"]["admitted_share"]["P4_with_dvi"]
    scored = class_share_report(recs, [], mr.SCORED_HORIZON)["classes"]["marriage"]["admitted_share"]["P4_with_dvi"]
    assert build == 10 / H_DAYS and scored == 10 / 10333 and scored > build           # 1998-01-01 .. 2026-04-17 = 10,333 days


def test_extension_variants_split_when_they_land_and_equal_base_when_absent():
    d = lambda n: T(2000, 2, n)                                                    # noqa: E731
    recs = [
        _rec("marriage", "P1", "venus", (d(1), d(3))),                             # base P1: Feb 1,2
        _rec("marriage", "P1", "jupiter", (d(10), d(12)), via="karakatva"),        # extension: Feb 10,11
        _rec("marriage", "P4", "saturn", (d(20), d(23))),                          # base P4: Feb 20,21,22
        _rec("marriage", "P4", "jupiter", (d(25), d(27)), via="dvi"),              # DVI member: Feb 25,26
        _rec("marriage", "P3", "saturn", (d(20), d(23))),                          # base P3 covers 20-22
        _rec("marriage", "P3", "saturn", (d(28), d(29)), via="kb"),                # K-B only: Feb 28
    ]
    days = class_share_report(recs, [], H)["classes"]["marriage"]["admitted_days"]
    assert days["P1_base"] == 2 and days["P1_with_karakatva"] == 4
    assert days["P4_without_dvi"] == 3 and days["P4_with_dvi"] == 5
    assert days["kb_only"] == 1                                                    # Feb 28 is admitted only through K-B
    assert days["P3_union"] == 4                                                   # base 20-22 plus the K-B day 28
    plain = class_share_report([r for r in recs if r.via == "base"], [], H)["classes"]["marriage"]["admitted_days"]
    assert plain["P1_with_karakatva"] == plain["P1_base"] == 2 and plain["P4_with_dvi"] == plain["P4_without_dvi"] == 3
    assert plain["kb_only"] == 0


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
def test_near_misses_are_counted_separately_and_cannot_change_any_share():
    recs = [_rec("marriage", "P3", "venus", (T(2000, 1, 1), T(2000, 1, 4)))]
    before = class_share_report(recs, [], H)
    counts = near_miss_counts([("marriage", "aspect", "jupiter"), ("marriage", "aspect", "jupiter"),
                               ("surgery", "conjunction", "mars")])
    assert counts == {"total": 3, "by_class_relation_body": {"marriage|aspect|jupiter": 2, "surgery|conjunction|mars": 1}}
    assert class_share_report(recs, [], H) == before                       # the report API has no near-miss input
    assert near_miss_counts([]) == {"total": 0, "by_class_relation_body": {}}


# ── acceptance of the measuring build (§13) ──────────────────────────────────────────────────────────────────────
ALL26 = frozenset(mr.SCORED_CLASSES)
HOLDING = frozenset({"marriage", "surgery", "bereavement"})


def _view(**kw):
    base = dict(stored_scope="test_slice", run="all_classes_full", sealed=False, published=False, horizon=H,
                rule_versions=frozenset({"1.0.0"}), near_miss_rows_stored=0, classes_with_records=HOLDING,
                marker_classes=ALL26, marker_horizon=H)
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
    (dict(classes_with_records=frozenset({"marriage", "spiritual_turn", "parental_event"})), "excluded_class_has_rows"),
    (dict(classes_with_records=frozenset({"marriage", "pluto_transit"})), "unknown_class_has_rows"),
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
