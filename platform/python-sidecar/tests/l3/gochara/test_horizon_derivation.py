"""FB-1 to FB-3 (FINAL_BUILD_SCOPE): the per-chart horizon is DERIVED, by one pure function, and refused by name outside the substrate domain.

No database, no ephemeris. The pinned chart's inputs are checked against the real life-event log file in the repository: the derivation must land on
[1998-01-01, 2084-02-05) with basis first_dated_event from the log's OWN rows, not from a typed-in date.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from services.gochara_kernel import horizon as hz
from services.gochara_kernel.horizon import (BASIS_BUILD_DATE, BASIS_FIRST_DATED_EVENT, HorizonDerivationRefusal, HorizonOutsideSubstrateDomain,
                                             LelEvent, derive_chart_horizon, is_fully_dated, require_inside_substrate_domain)

UTC = timezone.utc
BIRTH = date(1984, 2, 5)
LEL_FILE = Path(__file__).resolve().parents[5] / "01_FACTS_LAYER" / "LIFE_EVENT_LOG_v1_2.md"


def _ev(event_id, d, conf="exact"):
    return LelEvent(event_id, d, conf)


def _real_lel_events() -> list[LelEvent]:
    """Every `EVT.` block of the real log file with its `date:` and its `date_confidence:` (mapped to the database vocabulary: only the file's `exact` is exact)."""
    events, current = [], None
    for line in LEL_FILE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(EVT\.[0-9X]{4}\.[0-9X]{2}\.[0-9X]{2}\.[0-9]{2}):\s*$", line)
        if m:
            current = {"id": m.group(1)}
            continue
        if current is None:
            continue
        m = re.match(r"^  date:\s*(\S+)", line)
        if m and "date" not in current:
            current["date"] = m.group(1)
        m = re.match(r"^  date_confidence:\s*([a-z-]+)", line)
        if m and "conf" not in current:
            current["conf"] = m.group(1)
        if "date" in current and "conf" in current:
            raw = current["date"]
            # an undated event stores a placeholder date: take the year (and 01 for the unknown parts), exactly what a loader would
            parts = (raw.split("-") + ["01", "01"])[:3]
            parts = [p if p.isdigit() else "01" for p in parts]
            events.append(LelEvent(current["id"], date(int(parts[0]), int(parts[1]), int(parts[2])), "exact" if current["conf"] == "exact" else "year_only"))
            current = None
    return events


def test_the_pinned_chart_resolves_to_1998_01_01_through_2084_02_05_from_the_real_life_event_log():
    events = _real_lel_events()
    assert len(events) >= 40, "the log's rows were read"
    got = derive_chart_horizon(BIRTH, events, date(2026, 10, 5))
    assert got.bounds == (datetime(1998, 1, 1, tzinfo=UTC), datetime(2084, 2, 5, tzinfo=UTC))
    assert got.basis == BASIS_FIRST_DATED_EVENT and got.first_event_id == "EVT.1998.02.16.01"
    assert (hz.PINNED_CHART_HORIZON.bounds, hz.PINNED_CHART_HORIZON.basis, hz.PINNED_CHART_HORIZON.first_event_id) == (got.bounds, got.basis, got.first_event_id), "the named pinned-chart value is what the real rows derive"
    # the rule runs on the RAW rows: how many it set aside is reported (the log will be revised, so no exact count is pinned here)
    assert got.events_total == len(events) and got.excluded_birth_entry == 1 and got.excluded_not_fully_dated > 0
    assert got.events_total == got.excluded_birth_entry + got.excluded_not_fully_dated + sum(1 for e in events if e.event_date > BIRTH and is_fully_dated(e))
    # the log holds undated events BEFORE 1998 (EVT.1995.XX.XX.01 and the birth entry): neither may fix the start
    assert any(e.event_id.startswith("EVT.1995.") for e in events) and any(e.event_date == BIRTH for e in events)


def test_a_chart_with_no_dated_events_starts_on_the_build_date_and_the_basis_says_so():
    a = derive_chart_horizon(BIRTH, [], date(2026, 10, 5))
    b = derive_chart_horizon(BIRTH, [], date(2026, 10, 6))
    assert a.basis == BASIS_BUILD_DATE and a.first_event_id is None
    assert a.start == datetime(2026, 10, 5, tzinfo=UTC) and a.end == datetime(2084, 2, 5, tzinfo=UTC)
    assert a != b and a.start != b.start, "two builds on different dates of an event-less chart derive different horizons (the build date is IN the manifest)"


@pytest.mark.parametrize("event, expected", [
    (_ev("EVT.1998.02.16.01", date(1998, 2, 16)), True),
    (_ev("EVT.1995.XX.XX.01", date(1995, 1, 1)), False),                     # year-only: placeholder places
    (_ev("EVT.2001.03.XX.01", date(2001, 3, 1)), False),                     # month-only
    (_ev("EVT.1998.02.16.01", date(1998, 2, 16), "month_known"), False),     # the flag says not exact
    (_ev("EVT.1998.02.16.01", date(1998, 2, 17)), False),                    # stored date disagrees with the id
    (_ev("EVT.1998.13.40.01", date(1998, 1, 1)), False),                     # impossible date in the id
    (_ev("EVT.1998.02.16", date(1998, 2, 16)), False),                       # not the id shape
])
def test_fully_dated_is_decided_from_the_id_the_flag_and_the_stored_date_together(event, expected):
    assert is_fully_dated(event) is expected


def test_the_birth_entry_and_anything_before_it_never_fixes_the_start_and_a_year_only_event_never_does_either():
    events = [_ev("EVT.1984.02.05.01", BIRTH), _ev("EVT.1983.12.31.01", date(1983, 12, 31)), _ev("EVT.1995.XX.XX.01", date(1995, 1, 1), "year_only"),
              _ev("EVT.2003.06.XX.01", date(2003, 6, 1), "month_known"), _ev("EVT.2010.05.05.01", date(2010, 5, 5)), _ev("EVT.2004.04.04.01", date(2004, 4, 4))]
    got = derive_chart_horizon(BIRTH, events, date(2026, 1, 1))
    assert got.start == datetime(2004, 1, 1, tzinfo=UTC) and got.first_event_id == "EVT.2004.04.04.01", "the earliest FULLY dated event after birth, by date not by list order"


def test_the_start_is_the_first_of_january_of_the_year_not_the_event_day():
    got = derive_chart_horizon(BIRTH, [_ev("EVT.2000.12.31.01", date(2000, 12, 31))], date(2026, 1, 1))
    assert got.start == datetime(2000, 1, 1, tzinfo=UTC)


def test_the_end_is_birth_plus_one_hundred_years_and_a_leap_day_birth_is_refused_when_the_target_year_has_no_leap_day():
    assert derive_chart_horizon(date(1980, 7, 1), [], date(2020, 1, 1)).end == datetime(2080, 7, 1, tzinfo=UTC)
    assert derive_chart_horizon(date(1984, 2, 29), [], date(2020, 1, 1)).end == datetime(2084, 2, 29, tzinfo=UTC)      # 2084 is a leap year
    with pytest.raises(HorizonDerivationRefusal, match="29 February"):
        derive_chart_horizon(date(2000, 2, 29), [], date(2120, 1, 1))                                                  # 2100 is not: named refusal, no guess


def test_an_empty_or_inverted_horizon_and_a_non_date_are_refused():
    with pytest.raises(HorizonDerivationRefusal, match="empty or inverted"):
        derive_chart_horizon(date(1900, 1, 1), [], date(2020, 1, 1))              # build date after birth + 100 y
    with pytest.raises(HorizonDerivationRefusal, match="not a date"):
        derive_chart_horizon("1984-02-05", [], date(2026, 1, 1))                  # type: ignore[arg-type]
    with pytest.raises(HorizonDerivationRefusal, match="not a date"):
        derive_chart_horizon(BIRTH, [], datetime(2026, 1, 1))                     # a datetime is not a date: no silent truncation


def test_derivation_is_order_independent_and_deterministic():
    events = [_ev("EVT.2010.05.05.01", date(2010, 5, 5)), _ev("EVT.1998.02.16.01", date(1998, 2, 16)), _ev("EVT.2004.04.04.01", date(2004, 4, 4))]
    assert derive_chart_horizon(BIRTH, events, date(2026, 1, 1)) == derive_chart_horizon(BIRTH, list(reversed(events)), date(2026, 1, 1))


# ── FB-3: the substrate domain ────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_horizon_must_lie_inside_the_substrate_domain_the_edges_pass_and_one_day_over_is_refused_by_name():
    require_inside_substrate_domain((datetime(1998, 1, 1, tzinfo=UTC), datetime(2084, 2, 5, tzinfo=UTC)))       # the pinned chart: 331 days of margin
    require_inside_substrate_domain((datetime(1998, 1, 1, tzinfo=UTC), datetime(2085, 1, 1, tzinfo=UTC)))       # the domain itself
    for bad in ((datetime(1998, 1, 1, tzinfo=UTC), datetime(2085, 1, 2, tzinfo=UTC)),                          # FB-3 oracle: 2085-01-02
                (datetime(1997, 12, 31, tzinfo=UTC), datetime(2084, 2, 5, tzinfo=UTC))):
        with pytest.raises(HorizonOutsideSubstrateDomain, match="horizon_outside_substrate_domain"):
            require_inside_substrate_domain(bad)


def test_the_pinned_chart_horizon_leaves_331_days_of_substrate_margin():
    """FINAL_BUILD_SCOPE FB-3 says 330 days; measured from the half-open end 2084-02-05T00:00Z to the domain end 2085-01-01T00:00Z it is 331 (2084 is a leap year;
    330 counts 2084-02-05 as its own day). The rule that matters is the inequality, pinned above; the number is recorded here as measured."""
    from services.gochara_kernel.substrate import SUBSTRATE_DOMAIN_END
    assert (SUBSTRATE_DOMAIN_END - hz.PINNED_CHART_HORIZON.end).days == 331


# ── MB-ADDITIONS 1: the START edge is refused by name, with oracles ───────────────────────────────────────────────────────────────────

def test_a_start_before_the_substrate_domain_start_is_refused_by_name():
    # the first fully dated event is in 1990: 1990-01-01 is before the domain start 1998-01-01
    with pytest.raises(HorizonOutsideSubstrateDomain, match=r"horizon_outside_substrate_domain \(start edge\)"):
        derive_chart_horizon(date(1984, 2, 5), [_ev("EVT.1990.06.06.01", date(1990, 6, 6))], date(2026, 1, 1))
    with pytest.raises(HorizonOutsideSubstrateDomain, match="start edge"):
        derive_chart_horizon(date(1984, 2, 5), [], date(1997, 12, 31))         # an event-less chart whose build date is before the domain start
    # the edge itself passes
    assert derive_chart_horizon(date(1984, 2, 5), [_ev("EVT.1998.01.01.01", date(1998, 1, 1))], date(2026, 1, 1)).start == datetime(1998, 1, 1, tzinfo=UTC)


def test_a_start_before_birth_is_refused_by_name():
    # an event in the birth year after the birth date: 1 January of that year is before the birth date
    with pytest.raises(hz.HorizonStartBeforeBirth, match="horizon_start_before_birth"):
        derive_chart_horizon(date(1998, 6, 1), [_ev("EVT.1998.08.08.01", date(1998, 8, 8))], date(2026, 1, 1))


def test_a_start_in_the_future_is_refused_by_name():
    with pytest.raises(hz.HorizonStartInTheFuture, match="horizon_start_in_the_future"):
        derive_chart_horizon(date(1984, 2, 5), [_ev("EVT.2030.03.03.01", date(2030, 3, 3))], date(2026, 10, 5))
    # the build date itself is not the future
    assert derive_chart_horizon(date(1984, 2, 5), [], date(2026, 10, 5)).start == datetime(2026, 10, 5, tzinfo=UTC)


def test_the_leap_day_refusal_is_named_and_gives_no_guess_for_either_neighbouring_day():
    with pytest.raises(HorizonDerivationRefusal) as e:
        derive_chart_horizon(date(2000, 2, 29), [], date(2020, 1, 1))
    assert "refused, the end of the horizon is never guessed" in str(e.value) and "2000-02-29" in str(e.value)


# ── MB-ADDITIONS 2 and 3: raw rows, counts, shapes, and the pinned basis record ───────────────────────────────────────────────────────

def test_raw_rows_are_counted_birth_entry_and_not_fully_dated_and_the_total_adds_up():
    rows = [_ev("EVT.1984.02.05.01", BIRTH), _ev("EVT.1995.XX.XX.01", date(1995, 1, 1), "year_only"), _ev("EVT.2001.03.XX.01", date(2001, 3, 1), "month_known"),
            _ev("EVT.1998.02.16.01", date(1998, 2, 16)), _ev("EVT.2010.05.05.01", date(2010, 5, 5), "month_known")]
    got = derive_chart_horizon(BIRTH, rows, date(2026, 1, 1))
    assert (got.events_total, got.excluded_birth_entry, got.excluded_not_fully_dated) == (5, 1, 3)
    assert got.first_event_id == "EVT.1998.02.16.01"


def test_the_shape_of_an_event_does_not_change_which_date_is_read_the_literal_event_date_is_used():
    interval = LelEvent("EVT.2003.04.04.01", date(2003, 4, 4), "exact", "interval")        # interval_start / interval_end are NOT read
    chain = LelEvent("EVT.2002.02.02.01", date(2002, 2, 2), "exact", "chain")
    got = derive_chart_horizon(BIRTH, [interval, chain], date(2026, 1, 1))
    assert got.first_event_id == "EVT.2002.02.02.01" and got.first_event_shape == "chain" and got.start == datetime(2002, 1, 1, tzinfo=UTC)


def test_the_basis_record_names_the_kind_the_event_its_date_and_confidence_and_the_build_date_as_a_utc_date():
    rec = derive_chart_horizon(BIRTH, [_ev("EVT.1998.02.16.01", date(1998, 2, 16))], date(2026, 10, 5)).basis_record()
    assert rec["schema"] == hz.HORIZON_BASIS_SCHEMA and rec["kind"] == BASIS_FIRST_DATED_EVENT
    assert rec["first_event"] == {"event_id": "EVT.1998.02.16.01", "event_date": "1998-02-16", "date_confidence": "exact", "shape": "point"}
    assert rec["build_date_utc"] == "2026-10-05" and rec["horizon"] == ["1998-01-01T00:00:00+00:00", "2084-02-05T00:00:00+00:00"]
    none = derive_chart_horizon(BIRTH, [], date(2026, 10, 5)).basis_record()
    assert none["kind"] == BASIS_BUILD_DATE and none["first_event"] is None and none["build_date_utc"] == "2026-10-05"
    import json
    assert json.loads(json.dumps(rec)) == rec, "JSON-plain"
