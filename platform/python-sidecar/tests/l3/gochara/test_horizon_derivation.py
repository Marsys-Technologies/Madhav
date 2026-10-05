"""MEASURING_BUILD_CONTRACT MB-1 (T1.1, T1.2): the per-chart horizon DETECTOR, pure (no database, no ephemeris).

The owner-approved pair [1998-01-01, 2084-02-05) is the authority for the pinned chart; the detector is evidence guarded by `horizon_derivation_disagrees_with_ruling`.
The pinned chart's inputs are checked against the real life-event log file in the repository (its own rows, not typed-in dates).
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from services.gochara_kernel import horizon as hz
from services.gochara_kernel.horizon import LelEvent, derive_chart_horizon

UTC = timezone.utc
BIRTH = date(1984, 2, 5)
BUILD = date(2026, 10, 6)
COL = "category"                                        # a pinned column for the pure tests; the real one is pinned by steward OS-1 after a production read
LEL_FILE = Path(__file__).resolve().parents[5] / "01_FACTS_LAYER" / "LIFE_EVENT_LOG_v1_2.md"


def _ev(event_id, d, conf="exact", shape="point", **kw):
    return LelEvent(event_id, d, conf, shape, **kw)


def _birth():
    return _ev("EVT.1984.02.05.01", BIRTH, birth_word="birth")


def _fixture(*extra):
    """The contract's real-column fixture: the birth row, year_only 1993-07-01 and 1995-07-01, the exact point 1998-02-16, later exact rows."""
    return [_birth(), _ev("EVT.1993.XX.XX.01", date(1993, 7, 1), "year_only"), _ev("EVT.1995.XX.XX.01", date(1995, 7, 1), "year_only"),
            _ev("EVT.1998.02.16.01", date(1998, 2, 16)), _ev("EVT.2007.06.10.01", date(2007, 6, 10)), _ev("EVT.2008.06.09.01", date(2008, 6, 9)), *extra]


def _derive(rows, build=BUILD, **kw):
    return derive_chart_horizon(BIRTH, rows, build, birth_word_column=COL, **kw)


def _real_lel_events() -> list[LelEvent]:
    """Every `EVT.` block of the real log file with its `date:` and `date_confidence:`; the birth block carries the birth word (subcategory birth in the file)."""
    events, current = [], None
    for line in LEL_FILE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(EVT\.[0-9X]{4}\.[0-9X]{2}\.[0-9X]{2}\.[0-9]{2}):\s*$", line)
        if m:
            current = {"id": m.group(1)}
            continue
        if current is None:
            continue
        for key, pat in (("date", r"^  date:\s*(\S+)"), ("conf", r"^  date_confidence:\s*([a-z-]+)"), ("sub", r"^  subcategory:\s*(\S+)")):
            m = re.match(pat, line)
            if m and key not in current:
                current[key] = m.group(1)
        if "date" in current and "conf" in current and "sub" in current:
            parts = (current["date"].split("-") + ["01", "01"])[:3]
            parts = [p if p.isdigit() else "01" for p in parts]
            events.append(LelEvent(current["id"], date(int(parts[0]), int(parts[1]), int(parts[2])), "exact" if current["conf"] == "exact" else "year_only",
                                   birth_word="birth" if current["sub"] == "birth" else current["sub"]))
            current = None
    return events


# ── T1.1 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_contracts_fixture_derives_the_ruled_pair_and_sets_aside_two_undated_rows():
    got = _derive(_fixture())
    assert got.bounds == hz.RULED_HORIZON == (datetime(1998, 1, 1, tzinfo=UTC), datetime(2084, 2, 5, tzinfo=UTC))
    assert got.basis == "first_dated_event" and got.first_event_id == "EVT.1998.02.16.01" and got.excluded_not_fully_dated == 2
    assert got.birth_row.event_id == "EVT.1984.02.05.01" and got.birth_word_column == COL
    assert got.readings == {"event_date": "1998-01-01", "interval_start": "1998-01-01", "chain_root": "1998-01-01"}


def test_reordering_the_rows_changes_nothing_and_removing_the_1998_row_moves_the_start_to_the_next_exact_rows_year():
    rows = _fixture()
    assert _derive(list(reversed(rows))) == _derive(rows)
    got = _derive([r for r in rows if r.event_id != "EVT.1998.02.16.01"])
    assert got.start == datetime(2007, 1, 1, tzinfo=UTC) and got.first_event_id == "EVT.2007.06.10.01"


def test_the_pinned_chart_from_the_real_log_file_derives_the_ruled_pair_with_the_real_row_counts():
    events = _real_lel_events()
    assert len(events) >= 40 and sum(1 for e in events if e.birth_word == "birth") == 1
    got = _derive(events, ruled=hz.RULED_HORIZON)                     # guarded: the log derives EXACTLY the owner-approved pair
    assert got.bounds == hz.RULED_HORIZON and got.first_event_id == "EVT.1998.02.16.01"
    assert got.excluded_not_fully_dated > 0 and any(e.event_id.startswith("EVT.1995.") for e in events)


def test_no_rows_means_the_build_date_and_the_basis_says_so_and_two_dates_give_two_horizons():
    a, b = _derive([], date(2026, 10, 5)), _derive([], date(2026, 10, 6))
    assert a.basis == "build_date" and a.first_event is None and a.birth_row is None and a.birth_word_column is None
    assert a.start == datetime(2026, 10, 5, tzinfo=UTC) and a.end == datetime(2084, 2, 5, tzinfo=UTC) and a != b


def test_rows_with_none_fully_dated_also_start_on_the_build_date():
    got = _derive([_birth(), _ev("EVT.1995.XX.XX.01", date(1995, 7, 1), "year_only")])
    assert got.basis == "build_date" and got.start == datetime(2026, 10, 6, tzinfo=UTC) and got.excluded_not_fully_dated == 1


def test_the_start_is_the_first_of_january_of_the_year_not_the_event_day():
    assert _derive([_birth(), _ev("EVT.2000.12.31.01", date(2000, 12, 31))]).start == datetime(2000, 1, 1, tzinfo=UTC)


def test_the_end_is_birth_plus_one_hundred_years():
    assert derive_chart_horizon(date(1980, 7, 1), [], date(2020, 1, 1)).end == datetime(2080, 7, 1, tzinfo=UTC)
    assert derive_chart_horizon(date(1984, 2, 29), [], date(2020, 1, 1)).end == datetime(2084, 2, 29, tzinfo=UTC)


# ── the basis record (MB-1.4) ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_basis_record_pins_every_consumed_row_with_its_digest_the_birth_row_the_readings_and_both_dating_rules():
    rec = _derive(_fixture()).basis_record()
    assert rec["schema"] == "horizon_basis/1" and rec["rule"] == "ruling7+ruling13" and rec["basis"] == "first_dated_event"
    assert rec["birth_date"] == "1984-02-05" and rec["build_date"] == "2026-10-06"
    assert rec["chosen"] == {"event_id": "EVT.1998.02.16.01", "event_date": "1998-02-16", "date_confidence": "exact", "shape": "point"}
    assert rec["birth_row"] == {"event_id": "EVT.1984.02.05.01", "column_used": COL}
    assert [r["event_id"] for r in rec["consumed_rows"]] == sorted(r["event_id"] for r in rec["consumed_rows"]) and len(rec["consumed_rows"]) == 6
    assert set(rec["consumed_rows"][0]) == {"event_id", "event_date", "date_confidence", "shape", "interval_start", "interval_end", "chain_parent_event_id"}
    import hashlib
    assert rec["consumed_rows_digest"] == hashlib.sha256(json.dumps(rec["consumed_rows"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    assert rec["excluded_not_fully_dated"] == 2 and rec["readings"] == {"event_date": "1998-01-01", "interval_start": "1998-01-01", "chain_root": "1998-01-01"}
    assert rec["dating_rules"] == {"flag_exact": "EVT.1998.02.16.01", "id_digits": "EVT.1998.02.16.01"} and rec["horizon"] == [hz.RULED_HORIZON[0].isoformat(), hz.RULED_HORIZON[1].isoformat()]
    assert json.loads(json.dumps(rec)) == rec, "JSON-plain"
    none = _derive([]).basis_record()
    assert none["chosen"] is None and none["birth_row"] is None and none["consumed_rows"] == [] and none["basis"] == "build_date"


def test_changed_row_ids_names_added_removed_and_changed_rows_only():
    a = _derive(_fixture()).basis_record()["consumed_rows"]
    b = _derive(_fixture(_ev("EVT.2010.01.01.01", date(2010, 1, 1)))).basis_record()["consumed_rows"]
    assert hz.changed_row_ids(a, b) == ["EVT.2010.01.01.01"] and hz.changed_row_ids(a, a) == []
    c = [dict(r, date_confidence="month_known") if r["event_id"] == "EVT.2007.06.10.01" else r for r in a]
    assert hz.changed_row_ids(a, c) == ["EVT.2007.06.10.01"]


# ── T1.2: each refusal by exactly one mutation of the fixture ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("rows, build, birth, code", [
    ([_ev("EVT.1983.05.01.01", date(1983, 5, 1)), _birth()], BUILD, BIRTH, "horizon_start_before_birth"),                               # exact row dated before birth
    ([_birth(), _ev("EVT.1990.05.05.01", date(1990, 5, 5))], BUILD, BIRTH, "horizon_start_before_substrate_domain"),
    ([_birth(), _ev("EVT.2030.03.03.01", date(2030, 3, 3))], BUILD, BIRTH, "horizon_start_in_future"),
    ([], date(2000, 3, 3), date(2000, 2, 29), "horizon_birth_anniversary_undefined"),
    ([], date(1997, 12, 31), BIRTH, "horizon_start_before_substrate_domain"),                                                          # an event-less chart built too early
    ([], date(2090, 1, 1), BIRTH, "horizon_empty"),                                                                                     # build date after birth + 100 y
    ([_birth(), _ev("EVT.1998.02.16.01", date(1998, 2, 16), "circa")], BUILD, BIRTH, "lel_date_confidence_unknown"),
    ([_birth(), _ev("EVT.1998.02.16.01", date(1998, 2, 16), shape="loop")], BUILD, BIRTH, "lel_shape_unknown"),
    ([_birth(), _ev("EVT.1998.02.16.01", None)], BUILD, BIRTH, "lel_date_missing"),
])
def test_each_refusal_is_produced_by_one_mutation_and_named(rows, build, birth, code):
    with pytest.raises(hz.HorizonRefusal) as e:
        derive_chart_horizon(birth, rows, build, birth_word_column=COL)
    assert e.value.code == code and str(e.value).startswith(code + ":"), str(e.value)


def test_the_end_after_the_substrate_domain_end_is_refused_by_name():
    with pytest.raises(hz.HorizonOutsideSubstrateDomain, match="horizon_outside_substrate_domain"):
        derive_chart_horizon(date(1990, 7, 1), [], date(2020, 1, 1))                                                                    # end 2090-07-01 > 2085-01-01


def test_the_birth_row_must_be_unique_and_identified_or_the_derivation_refuses():
    two = [_birth(), _ev("EVT.1984.02.05.02", BIRTH, birth_word="birth"), _ev("EVT.1998.02.16.01", date(1998, 2, 16))]
    none = [_ev("EVT.1984.02.05.01", BIRTH, birth_word="other"), _ev("EVT.1998.02.16.01", date(1998, 2, 16))]
    for rows in (two, none):
        with pytest.raises(hz.LelBirthRowUnidentifiable, match="lel_birth_row_unidentifiable"):
            _derive(rows)
    with pytest.raises(hz.LelBirthRowUnidentifiable, match="not pinned yet"):
        derive_chart_horizon(BIRTH, _fixture(), BUILD)                                                                                  # steward OS-1: until the column is pinned


def test_the_shape_readings_are_all_computed_and_a_reading_that_changes_the_start_is_refused():
    # an exact interval event whose event_date is 1998-06-01 but whose interval_start is 1996-01-01: the readings give 1998 and 1996
    sens = _fixture(_ev("EVT.1998.06.01.01", date(1998, 6, 1), shape="interval", interval_start=date(1996, 1, 1), interval_end=date(1998, 6, 1)))
    with pytest.raises(hz.LelShapeReadingSensitive, match="lel_shape_reading_sensitive") as e:
        _derive(sens)
    assert "1996-01-01" in str(e.value) and "1998-01-01" in str(e.value)
    # an interval that does not change the start is fine, and the literal event_date is the primary reading
    ok = _fixture(_ev("EVT.2003.06.01.01", date(2003, 6, 1), shape="interval", interval_start=date(2003, 1, 1)))
    assert _derive(ok).start == datetime(1998, 1, 1, tzinfo=UTC)
    # a chain whose root is an earlier fully dated row that does not move the start: every reading agrees
    chain = _fixture(_ev("EVT.2001.03.03.01", date(2001, 3, 3)), _ev("EVT.2003.03.03.01", date(2003, 3, 3), shape="chain", chain_parent_event_id="EVT.2001.03.03.01"))
    assert _derive(chain).start == datetime(1998, 1, 1, tzinfo=UTC) and _derive(chain).readings["chain_root"] == "1998-01-01"
    # a chain whose ROOT is the earliest fully dated row and whose own date is later: the chain reading would start in 1999, the literal one in 1999 too (no change)
    only = [_birth(), _ev("EVT.1999.03.03.01", date(1999, 3, 3)), _ev("EVT.2003.03.03.01", date(2003, 3, 3), shape="chain", chain_parent_event_id="EVT.1999.03.03.01")]
    assert _derive(only).start == datetime(1999, 1, 1, tzinfo=UTC)


def test_a_chain_with_a_cycle_or_a_missing_parent_is_unresolvable():
    cyc = _fixture(_ev("EVT.2003.03.03.01", date(2003, 3, 3), shape="chain", chain_parent_event_id="EVT.2004.04.04.01"),
                   _ev("EVT.2004.04.04.01", date(2004, 4, 4), shape="chain", chain_parent_event_id="EVT.2003.03.03.01"))
    missing = _fixture(_ev("EVT.2003.03.03.01", date(2003, 3, 3), shape="chain", chain_parent_event_id="EVT.9999.01.01.01"))
    for rows in (cyc, missing):
        with pytest.raises(hz.LelChainUnresolvable, match="lel_chain_unresolvable"):
            _derive(rows)


# ── steward ruling 2(c): BOTH dating rules, refusing when they disagree on the first event ──────────────────────────────────────────────

def test_a_year_only_row_left_at_the_default_exact_would_fix_the_start_under_the_flag_alone_so_the_rules_disagreeing_is_refused():
    rows = [_birth(), _ev("EVT.1995.XX.XX.01", date(1995, 7, 1), "exact"), _ev("EVT.1998.02.16.01", date(1998, 2, 16))]               # 457's default left 1995 'exact'
    with pytest.raises(hz.LelDatingRulesDisagree, match="lel_dating_rules_disagree") as e:
        _derive(rows)
    assert "EVT.1995.XX.XX.01" in str(e.value) and "EVT.1998.02.16.01" in str(e.value)


def test_a_row_the_id_says_is_dated_but_the_flag_says_is_not_also_disagrees():
    rows = [_birth(), _ev("EVT.1998.02.16.01", date(1998, 2, 16), "month_known"), _ev("EVT.2007.06.10.01", date(2007, 6, 10))]
    with pytest.raises(hz.LelDatingRulesDisagree):
        _derive(rows)


def test_a_stored_date_that_disagrees_with_its_id_is_not_fully_dated_under_the_id_rule():
    assert hz.rule_flag_exact(_ev("EVT.1998.02.16.01", date(1998, 2, 17))) and not hz.rule_id_digits(_ev("EVT.1998.02.16.01", date(1998, 2, 17)))
    assert not hz.is_fully_dated(_ev("EVT.1998.13.40.01", date(1998, 1, 1))) and not hz.is_fully_dated(_ev("EVT.1998.02.16", date(1998, 2, 16)))


# ── the ruling guard (MB-1.2 item 7) and the substrate domain ───────────────────────────────────────────────────────────────────────────

def test_the_ruling_guard_refuses_a_derivation_that_is_not_the_owner_approved_pair():
    revised = [r for r in _fixture() if r.event_id != "EVT.1998.02.16.01"]
    with pytest.raises(hz.HorizonDerivationDisagreesWithRuling, match="horizon_derivation_disagrees_with_ruling") as e:
        _derive(revised, ruled=hz.RULED_HORIZON)
    assert "2007-01-01" in str(e.value) and "1998-01-01" in str(e.value)
    assert _derive(_fixture(), ruled=hz.RULED_HORIZON).bounds == hz.RULED_HORIZON
    assert hz.RULED_HORIZONS == {hz.PINNED_CHART_ID: hz.RULED_HORIZON}


def test_the_domain_edges_are_two_different_refusals_and_the_pinned_horizon_leaves_331_days_of_margin():
    start_edge, end_edge = (datetime(1997, 12, 31, tzinfo=UTC), datetime(2084, 2, 5, tzinfo=UTC)), (datetime(1998, 1, 1, tzinfo=UTC), datetime(2085, 1, 2, tzinfo=UTC))
    with pytest.raises(hz.HorizonStartBeforeSubstrateDomain):
        hz.require_inside_substrate_domain(start_edge)
    with pytest.raises(hz.HorizonOutsideSubstrateDomain, match="horizon_outside_substrate_domain"):
        hz.require_inside_substrate_domain(end_edge)                                                                                    # FB-3 oracle: 2085-01-02
    hz.require_inside_substrate_domain(hz.RULED_HORIZON)
    hz.require_inside_substrate_domain((datetime(1998, 1, 1, tzinfo=UTC), datetime(2085, 1, 1, tzinfo=UTC)))
    from services.gochara_kernel.substrate import SUBSTRATE_DOMAIN_END
    assert (SUBSTRATE_DOMAIN_END - hz.RULED_HORIZON[1]).days == 331    # FINAL_BUILD_SCOPE FB-3 says 330 (counting 2084-02-05 as its own day); measured from the half-open end it is 331


def test_every_refusal_of_the_contract_exists_with_its_exact_token():
    contract = {"horizon_empty", "horizon_start_before_birth", "horizon_start_before_substrate_domain", "horizon_start_in_future", "horizon_outside_substrate_domain",
                "horizon_birth_anniversary_undefined", "lel_birth_row_unidentifiable", "lel_date_confidence_unknown", "lel_shape_unknown", "lel_date_missing",
                "lel_chain_unresolvable", "lel_shape_reading_sensitive", "horizon_derivation_disagrees_with_ruling", "lel_dating_rules_disagree"}
    assert set(hz.REFUSAL_CODES) == contract and len(hz.REFUSAL_CODES) == len(set(hz.REFUSAL_CODES))


def test_a_non_date_input_is_refused_not_truncated():
    with pytest.raises(hz.HorizonRefusal, match="not a date"):
        derive_chart_horizon("1984-02-05", [], BUILD)                    # type: ignore[arg-type]
    with pytest.raises(hz.HorizonRefusal, match="not a date"):
        derive_chart_horizon(BIRTH, [], datetime(2026, 1, 1))
