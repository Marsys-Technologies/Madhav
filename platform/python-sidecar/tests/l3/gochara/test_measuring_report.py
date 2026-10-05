"""Verifier side of the measuring build (FINAL_BUILD_SCOPE FB-2/FB-3/FB-50, §13) — pure tests, no database.

Every expected number is worked by hand from the rule in the module's docstring, never read back from the code.
The horizon of the pinned chart is 1998-01-01 .. 2084-02-05; the stub chart's natal values (test_graze_interim) are not
needed here because the report reads STORED intervals, not geometry.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from services.gochara_kernel import measuring_report as mr
from services.gochara_kernel.measuring_report import (
    MeasuringBuildView, MeasuringReportError, SupportRecord, admitted_days, class_share_report,
    clip_windows_for_scoring, derive_chart_horizon, length_distribution, measuring_refusals, near_miss_counts)

H = (date(1998, 1, 1), date(2084, 2, 5))
H_DAYS = 31446                       # 1998-01-01 .. 2084-02-05: 86*365 + 21 leap days (2000..2080) + 35 days (Jan 1 -> Feb 5)


def T(y, m, d, hh=0, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)


# ── the horizon ──────────────────────────────────────────────────────────────────────────────────────────────────
def test_the_pinned_chart_horizon_is_1998_01_01_to_2084_02_05_and_has_the_measured_day_count():
    start, end, basis = derive_chart_horizon(date(1984, 2, 5), [date(1998, 8, 20), date(2003, 5, 1)], date(2026, 10, 5))
    assert (start, end, basis) == (date(1998, 1, 1), date(2084, 2, 5), "first_dated_event")
    assert mr.horizon_days((start, end)) == H_DAYS


def test_a_chart_with_no_dated_event_starts_at_the_build_date_and_two_dates_differ():
    a = derive_chart_horizon(date(1984, 2, 5), [], date(2026, 10, 5))
    b = derive_chart_horizon(date(1984, 2, 5), [None], date(2026, 10, 6))
    assert a == (date(2026, 10, 5), date(2084, 2, 5), "build_date")
    assert a != b and b[0] == date(2026, 10, 6)                     # the build date is IN the result


def test_the_first_event_is_the_earliest_not_the_first_listed():
    assert derive_chart_horizon(date(1984, 2, 5), [date(2010, 3, 3), date(1999, 12, 31)], date(2026, 1, 1))[0] \
        == date(1999, 1, 1)


def test_a_leap_day_birth_without_an_anniversary_is_refused_by_name():
    with pytest.raises(MeasuringReportError, match="horizon_birth_anniversary_undefined"):
        derive_chart_horizon(date(2000, 2, 29), [], date(2026, 1, 1))     # 2100 is not a leap year
    assert derive_chart_horizon(date(1904, 2, 29), [], date(2026, 1, 1))[1] == date(2004, 2, 29)


def test_the_substrate_margin_rule_FB3():
    assert mr.horizon_problem(H) is None                                # 2084-02-05 passes
    assert mr.horizon_problem((H[0], date(2085, 1, 1))) is None         # the domain end itself
    assert mr.horizon_problem((H[0], date(2085, 1, 2))).startswith("horizon_outside_substrate_domain")
    assert mr.horizon_problem((date(2030, 1, 1), date(2030, 1, 1))).startswith("horizon_empty")
    assert (date(2085, 1, 1) - H[1]).days == 331                        # end-to-end 331 days; FB-3's '330' counts to 2084-12-31


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


def test_a_naive_instant_is_refused():
    with pytest.raises(MeasuringReportError, match="naive_datetime"):
        admitted_days([(datetime(2000, 1, 1), datetime(2000, 1, 2))], H)


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
    assert days["P4_without_dvi"] == 3 and days["P4_with_dvi"] == 3 and days["P2"] == 2
    assert days["class_union"] == 8                                                # 6 + P2's 2 (P4 inside P3's days)
    assert days["P1_base"] == 0 and days["kb_only"] == 0
    assert r["admitted_share"]["P3_union"] == 6 / H_DAYS
    # per agent: venus {1,2,3} exclusive {1,2}; jupiter {3,4,5} (P3 and P4) exclusive {4,5}; saturn {10}; moon {20,21}
    assert r["per_agent"]["venus"] == {"days": 3, "exclusive_days": 2}
    assert r["per_agent"]["jupiter"] == {"days": 3, "exclusive_days": 2}
    assert r["per_agent"]["saturn"] == {"days": 1, "exclusive_days": 1}
    assert r["per_agent"]["moon"] == {"days": 2, "exclusive_days": 2}


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


def test_the_unadmitted_eight_are_simply_absent_and_classes_are_reported_independently():
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


def test_an_unknown_path_and_an_empty_horizon_are_refused():
    with pytest.raises(MeasuringReportError, match="unknown_path"):
        class_share_report([_rec("marriage", "P5", "sun", (T(2001, 1, 1), T(2001, 1, 2)))], [], H)
    with pytest.raises(MeasuringReportError, match="horizon_empty"):
        class_share_report([], [], (date(2030, 1, 1), date(2030, 1, 1)))


def test_the_fast_and_slow_sets_partition_the_nine_agents():
    assert mr.FAST_AGENTS | mr.SLOW_AGENTS == {"sun", "moon", "mars", "mercury", "venus", "jupiter", "saturn", "rahu", "ketu"}
    assert not mr.FAST_AGENTS & mr.SLOW_AGENTS and mr.P4_AGENTS <= mr.SLOW_AGENTS


# ── near-misses: reported, never added (FB-29) ────────────────────────────────────────────────────────────────────
def test_near_misses_are_counted_separately_and_cannot_change_any_share():
    recs = [_rec("marriage", "P3", "venus", (T(2000, 1, 1), T(2000, 1, 4)))]
    before = class_share_report(recs, [], H)
    counts = near_miss_counts([("marriage", "aspect", "jupiter"), ("marriage", "aspect", "jupiter"),
                               ("surgery", "conjunction", "mars")])
    assert counts == {"total": 3, "by_class_relation_body": {"marriage|aspect|jupiter": 2, "surgery|conjunction|mars": 1}}
    assert class_share_report(recs, [], H) == before                       # the report API has no near-miss input
    import inspect
    assert "near" not in " ".join(inspect.signature(class_share_report).parameters)
    assert near_miss_counts([]) == {"total": 0, "by_class_relation_body": {}}


# ── acceptance of the measuring build (§13) ──────────────────────────────────────────────────────────────────────
def _view(**kw):
    base = dict(stored_scope="test_slice", run="all_classes_full", sealed=False, published=False, horizon=H,
                rule_versions=frozenset({"1.0.0"}), near_miss_rows_stored=0,
                classes_with_records=frozenset({"marriage", "surgery", "bereavement"}))
    base.update(kw)
    return MeasuringBuildView(**base)


def test_a_faithful_measuring_build_is_accepted():
    assert measuring_refusals(_view(), expected_horizon=H) == []


@pytest.mark.parametrize("kw,code", [
    (dict(stored_scope="full"), "measuring_scope_not_test_slice"),
    (dict(stored_scope=None), "measuring_scope_not_test_slice"),
    (dict(run="one_class_full"), "measuring_run_not_all_classes_full"),
    (dict(sealed=True), "measuring_build_sealed"),
    (dict(published=True), "measuring_build_published"),
    (dict(horizon=(date(1998, 2, 16), date(2084, 2, 5))), "horizon_mismatch"),
    (dict(horizon=(date(1998, 1, 1), date(2085, 1, 2))), "horizon_outside_substrate_domain"),
    (dict(rule_versions=frozenset({"1.0.0", "1.2.0"})), "rule_version_not_in_scope"),
    (dict(near_miss_rows_stored=3), "near_miss_rows_stored"),
    (dict(classes_with_records=frozenset({"marriage", "spiritual_turn", "parental_event"})), "excluded_class_has_rows"),
])
def test_each_departure_from_the_measuring_shape_is_refused_by_name(kw, code):
    out = measuring_refusals(_view(**kw), expected_horizon=H)
    assert any(x.startswith(code) for x in out), out


def test_the_eight_excluded_classes_are_exactly_the_nd_h_classes_and_the_other_nineteen_may_have_rows():
    assert len(mr.EXCLUDED_EIGHT) == 8 and "bereavement" not in mr.EXCLUDED_EIGHT
    assert "marriage" not in mr.EXCLUDED_EIGHT
    assert mr.FORBIDDEN_RULE_VERSIONS == {"1.2.0"}


def test_several_departures_are_all_named_not_just_the_first():
    out = measuring_refusals(_view(sealed=True, near_miss_rows_stored=1, run="all_classes_1y"), expected_horizon=H)
    assert len(out) == 3
