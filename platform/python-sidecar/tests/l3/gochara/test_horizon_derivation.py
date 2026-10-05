"""MEASURING_BUILD_CONTRACT v1.0 MB-1 (T1.1, T1.2): the per-chart horizon DETECTOR, pure (no database, no ephemeris), on the REAL column shapes.

The owner-approved pair [1998-01-01, 2084-02-05) is the authority for the pinned chart; the detector is evidence guarded by `horizon_derivation_disagrees_with_ruling`.
Rows carry a uuid5-like `event_id` and the canonical `EVT.YYYY.MM.DD.NN` id in `provenance_lel_id` (the intake writes no date_confidence, so 457's default `exact` stands
on proxy-dated rows). The pinned chart's inputs are also checked against the real life-event log file in the repository (its own rows, not typed-in dates).
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from services.gochara_kernel import horizon as hz
from services.gochara_kernel.horizon import LelEvent, derive_chart_horizon

UTC = timezone.utc
BIRTH = date(1984, 2, 5)
BUILD = date(2026, 10, 6)
LEL_FILE = Path(__file__).resolve().parents[5] / "01_FACTS_LAYER" / "LIFE_EVENT_LOG_v1_2.md"


def _row(lel_id, d, conf="exact", shape="point", *, uid=None, **kw):
    """A row as the intake stores it: a uuid5-style event_id and the LEL id in provenance."""
    return LelEvent(event_id=uid or f"{uuid.uuid5(uuid.NAMESPACE_DNS, 'BRAHMA-MI-5-1:' + str(lel_id))}", event_date=d, date_confidence=conf, shape=shape,
                    provenance_lel_id=lel_id, **kw)


def _birth():
    return _row("EVT.1984.02.05.01", BIRTH, domain="other/birth", category="other", event_type="other")


def _fixture(*extra):
    """The contract's real-column fixture: the birth row, year_only 1993-07-01 and 1995-07-01, the exact point 1998-02-16, later exact rows."""
    return [_birth(), _row("EVT.1993.XX.XX.01", date(1993, 7, 1), "year_only"), _row("EVT.1995.XX.XX.01", date(1995, 7, 1), "year_only"),
            _row("EVT.1998.02.16.01", date(1998, 2, 16)), _row("EVT.2007.06.10.01", date(2007, 6, 10)), _row("EVT.2008.06.09.01", date(2008, 6, 9)), *extra]


def _derive(rows, build=BUILD, **kw):
    return derive_chart_horizon(BIRTH, rows, build, **kw)


def _real_lel_events() -> list[LelEvent]:
    """Every `EVT.` block of the real log file as the INTAKE would store it: uuid5 event_id, the id in provenance, domain `<event_type>/<subcategory>`, and NO
    date_confidence written (457's default `exact` on every row, proxy-dated rows included)."""
    events, current = [], None
    for line in LEL_FILE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(EVT\.[0-9X]{4}\.[0-9X]{2}\.[0-9X]{2}\.[0-9]{2}):\s*$", line)
        if m:
            current = {"id": m.group(1)}
            continue
        if current is None:
            continue
        for key, pat in (("date", r"^  date:\s*(\S+)"), ("sub", r"^  subcategory:\s*(\S+)"), ("cat", r"^  category:\s*(\S+)")):
            m = re.match(pat, line)
            if m and key not in current:
                current[key] = m.group(1)
        if {"date", "sub", "cat"} <= set(current):
            parts = (current["date"].split("-") + ["01", "01"])[:3]
            parts = [p if p.isdigit() else "07" if i == 1 else "01" for i, p in enumerate(parts)]          # a proxy date, as the intake stores (YYYY-07-01)
            events.append(_row(current["id"], date(int(parts[0]), int(parts[1]), int(parts[2])), "exact", category=current["cat"], event_type=current["cat"],
                               domain=f"{current['cat']}/{current['sub']}"))
            current = None
    return events


# ── T1.1 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_contracts_fixture_derives_the_ruled_pair_and_sets_aside_two_undated_rows():
    got = _derive(_fixture())
    assert got.bounds == hz.RULED_HORIZON == (datetime(1998, 1, 1, tzinfo=UTC), datetime(2084, 2, 5, tzinfo=UTC))
    assert got.basis == "first_dated_event" and got.first_event_id == _row("EVT.1998.02.16.01", date(1998, 2, 16)).event_id and got.excluded_not_fully_dated == 2
    assert got.birth_row.provenance_lel_id == "EVT.1984.02.05.01" and got.flag_exact_but_id_undated == ()
    assert got.shape_readings == {"event_date_start": "1998-01-01", "interval_start_start": "1998-01-01", "chain_root_start": "1998-01-01"}
    assert got.fully_dated_readings == {"rule_F_start": "1998-01-01", "rule_I_start": "1998-01-01", "conjunction_start": "1998-01-01"}


def test_a_row_flagged_exact_by_457s_default_whose_lel_id_is_undated_is_excluded_and_listed_never_a_refusal():
    """The intake writes no date_confidence, so EVT.1993.XX.XX.01 (proxy date 1993-07-01) reads `exact`: it is NOT fully dated (the id is undated), 1998 stands."""
    rows = [_birth(), _row("EVT.1993.XX.XX.01", date(1993, 7, 1), "exact"), _row("EVT.1995.XX.XX.01", date(1995, 7, 1), "exact"), _row("EVT.1998.02.16.01", date(1998, 2, 16))]
    got = _derive(rows)
    assert got.bounds == hz.RULED_HORIZON and got.excluded_not_fully_dated == 2
    assert set(got.flag_exact_but_id_undated) == {rows[1].event_id, rows[2].event_id}
    assert got.fully_dated_readings == {"rule_F_start": "1993-01-01", "rule_I_start": "1998-01-01", "conjunction_start": "1998-01-01"}, "both readings are pinned"


def test_reordering_the_rows_changes_nothing_and_removing_the_1998_row_moves_the_start_to_the_next_exact_rows_year():
    rows = _fixture()
    assert _derive(list(reversed(rows))) == _derive(rows)
    got = _derive([r for r in rows if r.provenance_lel_id != "EVT.1998.02.16.01"])
    assert got.start == datetime(2007, 1, 1, tzinfo=UTC) and got.first_event.provenance_lel_id == "EVT.2007.06.10.01"


def test_the_pinned_chart_from_the_real_log_file_as_the_intake_stores_it_derives_the_ruled_pair():
    events = _real_lel_events()
    assert len(events) >= 40 and sum(1 for e in events if e.domain == "other/birth") == 1
    got = _derive(events, ruled=hz.RULED_HORIZON)                     # guarded: the log derives EXACTLY the owner-approved pair
    assert got.bounds == hz.RULED_HORIZON and got.first_event.provenance_lel_id == "EVT.1998.02.16.01"
    assert len(got.flag_exact_but_id_undated) > 30 and got.excluded_not_fully_dated == len(got.flag_exact_but_id_undated), "457's default exact on proxy-dated rows"


def test_no_rows_means_the_build_date_and_two_dates_give_two_horizons():
    a, b = _derive([], date(2026, 10, 5)), _derive([], date(2026, 10, 6))
    assert a.basis == "build_date" and a.first_event is None and a.birth_row is None
    assert a.start == datetime(2026, 10, 5, tzinfo=UTC) and a.end == datetime(2084, 2, 5, tzinfo=UTC) and a != b


def test_a_log_that_exists_but_has_no_fully_dated_event_is_refused_and_never_falls_back_to_the_build_date():
    with pytest.raises(hz.HorizonUnderivableLogHasNoDatedEvent, match="horizon_underivable_log_has_no_dated_event"):
        _derive([_birth(), _row("EVT.1995.XX.XX.01", date(1995, 7, 1), "year_only")])
    with pytest.raises(hz.HorizonUnderivableLogHasNoDatedEvent):
        _derive([_birth(), _row("EVT.1995.XX.XX.01", date(1995, 7, 1), "exact")])                        # flagged exact, id undated: still no dated event


def test_the_start_is_the_first_of_january_of_the_year_not_the_event_day():
    assert _derive([_birth(), _row("EVT.2000.12.31.01", date(2000, 12, 31))]).start == datetime(2000, 1, 1, tzinfo=UTC)


def test_the_end_is_birth_plus_one_hundred_years():
    assert derive_chart_horizon(date(1980, 7, 1), [], date(2020, 1, 1)).end == datetime(2080, 7, 1, tzinfo=UTC)
    assert derive_chart_horizon(date(1984, 2, 29), [], date(2020, 1, 1)).end == datetime(2084, 2, 29, tzinfo=UTC)


# ── the corrected rule: the LEL id is provenance, never event_id ────────────────────────────────────────────────────────────────────

def test_the_lel_id_is_read_from_provenance_only_and_event_id_is_never_a_fallback():
    only_event_id = _row(None, date(1998, 2, 16), uid="EVT.1998.02.16.01")                         # an event_id that LOOKS like the id, and no provenance lel_id
    assert not hz.rule_id_digits(only_event_id) and not hz.is_fully_dated(only_event_id)
    with pytest.raises(hz.LelIdMissingOnCandidateFirstEvent, match="lel_id_missing_on_candidate_first_event"):
        _derive([_birth(), only_event_id, _row("EVT.2007.06.10.01", date(2007, 6, 10))])


def test_a_row_without_a_lel_id_that_is_not_the_candidate_first_event_is_only_not_fully_dated():
    later = _row(None, date(2010, 1, 1))
    got = _derive([_birth(), _row("EVT.1998.02.16.01", date(1998, 2, 16)), later])
    assert got.bounds == hz.RULED_HORIZON and got.excluded_not_fully_dated == 1


def test_a_stored_date_that_disagrees_with_its_lel_id_is_not_fully_dated():
    assert hz.rule_flag_exact(_row("EVT.1998.02.16.01", date(1998, 2, 17))) and not hz.rule_id_digits(_row("EVT.1998.02.16.01", date(1998, 2, 17)))
    assert not hz.is_fully_dated(_row("EVT.1998.13.40.01", date(1998, 1, 1))) and not hz.is_fully_dated(_row("EVT.1998.02.16", date(1998, 2, 16)))
    assert not hz.is_fully_dated(_row("EVT.1998.02.16.01", date(1998, 2, 16), "month_known"))


# ── the birth row: domain other/birth ───────────────────────────────────────────────────────────────────────────────────────────────

def test_the_birth_row_is_identified_through_domain_other_birth_or_the_provenance_subcategory():
    assert hz.BIRTH_DOMAIN == "other/birth"
    assert _derive(_fixture()).birth_row.domain == "other/birth"
    via_sub = [_row("EVT.1984.02.05.01", BIRTH, provenance_subcategory="birth")] + _fixture()[1:]
    assert _derive(via_sub).birth_row.provenance_subcategory == "birth"


@pytest.mark.parametrize("birth_rows", [
    [_row("EVT.1984.02.05.01", BIRTH, category="birth", event_type="birth")],                                         # category/event_type birth only: NOT the vocabulary
    [_row("EVT.1984.02.05.01", BIRTH, domain="other/birth"), _row("EVT.1984.02.05.02", BIRTH, domain="other/birth")],   # two
    [],                                                                                                                 # none in a non-empty log
], ids=["category_only", "two", "none"])
def test_a_non_empty_log_without_exactly_one_birth_row_is_refused(birth_rows):
    with pytest.raises(hz.LelBirthRowUnidentifiable, match="lel_birth_row_unidentifiable"):
        _derive([*birth_rows, _row("EVT.1998.02.16.01", date(1998, 2, 16))])


# ── the basis record (v1.0 MB-1.4) ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_basis_record_pins_every_consumed_row_with_its_13_fields_the_birth_row_the_readings_and_the_digest():
    rec = _derive(_fixture(), chart_id=hz.PINNED_CHART_ID).basis_record()
    assert rec["schema"] == "horizon_basis/1" and rec["rule"] == "ruling7+ruling13" and rec["basis"] == "first_dated_event" and rec["chart_id"] == hz.PINNED_CHART_ID
    assert rec["birth_date"] == "1984-02-05" and rec["build_date"] == "2026-10-06" and rec["horizon"] == [hz.RULED_HORIZON[0].isoformat(), hz.RULED_HORIZON[1].isoformat()]
    assert rec["chosen"]["lel_id"] == "EVT.1998.02.16.01" and rec["chosen"]["event_date"] == "1998-02-16" and set(rec["chosen"]) == {"event_id", "lel_id", "event_date", "date_confidence", "shape"}
    assert rec["birth_row"]["lel_id"] == "EVT.1984.02.05.01" and rec["birth_row"]["domain"] == "other/birth" and rec["birth_row"]["column_used"] == "domain"
    assert set(rec["birth_row"]) == {"event_id", "lel_id", "event_date", "domain", "provenance_subcategory", "column_used"}
    assert rec["rows_total"] == 6 == len(rec["consumed_rows"]) and rec["excluded_not_fully_dated"] == 2 and rec["flag_exact_but_id_undated"] == []
    assert set(rec["consumed_rows"][0]) == {"event_id", "event_date", "category", "event_type", "domain", "provenance_lel_id", "provenance_subcategory", "shape",
                                            "date_confidence", "interval_start", "interval_end", "chain_parent_event_id", "date_tightened_at"}
    assert [(r["event_date"], r["event_id"]) for r in rec["consumed_rows"]] == sorted((r["event_date"], r["event_id"]) for r in rec["consumed_rows"]), "sorted by (event_date, event_id)"
    assert rec["consumed_rows_digest"] == hashlib.sha256(json.dumps(rec["consumed_rows"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    assert set(rec["fully_dated_readings"]) == {"rule_F_start", "rule_I_start", "conjunction_start"} and set(rec["shape_readings"]) == {"event_date_start", "interval_start_start", "chain_root_start"}
    assert json.loads(json.dumps(rec)) == rec, "JSON-plain"
    none = _derive([]).basis_record()
    assert none["chosen"] is None and none["birth_row"] is None and none["consumed_rows"] == [] and none["basis"] == "build_date" and none["rows_total"] == 0


def test_changed_row_ids_names_added_removed_and_changed_rows_only():
    a = _derive(_fixture()).basis_record()["consumed_rows"]
    new = _row("EVT.2010.01.01.01", date(2010, 1, 1))
    b = _derive(_fixture(new)).basis_record()["consumed_rows"]
    assert hz.changed_row_ids(a, b) == [new.event_id] and hz.changed_row_ids(a, a) == []
    victim = _row("EVT.2007.06.10.01", date(2007, 6, 10)).event_id
    c = [dict(r, date_confidence="month_known") if r["event_id"] == victim else r for r in a]
    assert hz.changed_row_ids(a, c) == [victim]


# ── T1.2: each refusal by exactly one mutation of the fixture ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("rows, build, birth, code", [
    ([_row("EVT.1983.05.01.01", date(1983, 5, 1)), _birth()], BUILD, BIRTH, "horizon_start_before_birth"),
    ([_birth(), _row("EVT.1990.05.05.01", date(1990, 5, 5))], BUILD, BIRTH, "horizon_start_before_substrate_domain"),
    ([_birth(), _row("EVT.2030.03.03.01", date(2030, 3, 3))], BUILD, BIRTH, "horizon_start_in_future"),
    ([], date(2000, 3, 3), date(2000, 2, 29), "horizon_birth_anniversary_undefined"),
    ([], date(1997, 12, 31), BIRTH, "horizon_start_before_substrate_domain"),
    ([], date(2090, 1, 1), BIRTH, "horizon_empty"),
    ([_birth(), _row("EVT.1998.02.16.01", date(1998, 2, 16), "circa")], BUILD, BIRTH, "lel_date_confidence_unknown"),
    ([_birth(), _row("EVT.1998.02.16.01", date(1998, 2, 16), shape="loop")], BUILD, BIRTH, "lel_shape_unknown"),
    ([_birth(), _row("EVT.1998.02.16.01", None)], BUILD, BIRTH, "lel_date_missing"),
])
def test_each_refusal_is_produced_by_one_mutation_and_named(rows, build, birth, code):
    with pytest.raises(hz.HorizonRefusal) as e:
        derive_chart_horizon(birth, rows, build)
    assert e.value.code == code and str(e.value).startswith(code + ":"), str(e.value)


def test_the_end_after_the_substrate_domain_end_is_refused_by_name():
    with pytest.raises(hz.HorizonOutsideSubstrateDomain, match="horizon_outside_substrate_domain"):
        derive_chart_horizon(date(1990, 7, 1), [], date(2020, 1, 1))


def test_the_shape_readings_are_all_computed_and_a_reading_that_changes_the_start_is_refused():
    sens = _fixture(_row("EVT.1998.06.01.01", date(1998, 6, 1), shape="interval", interval_start=date(1996, 1, 1), interval_end=date(1998, 6, 1)))
    with pytest.raises(hz.LelShapeReadingSensitive, match="lel_shape_reading_sensitive") as e:
        _derive(sens)
    assert "1996-01-01" in str(e.value) and "1998-01-01" in str(e.value)
    ok = _fixture(_row("EVT.2003.06.01.01", date(2003, 6, 1), shape="interval", interval_start=date(2003, 1, 1)))
    assert _derive(ok).start == datetime(1998, 1, 1, tzinfo=UTC)
    root = _row("EVT.2001.03.03.01", date(2001, 3, 3))
    chain = _fixture(root, _row("EVT.2003.03.03.01", date(2003, 3, 3), shape="chain", chain_parent_event_id=root.event_id))
    assert _derive(chain).start == datetime(1998, 1, 1, tzinfo=UTC) and _derive(chain).shape_readings["chain_root_start"] == "1998-01-01"


def test_a_chain_with_a_cycle_or_a_missing_parent_is_unresolvable():
    a, b = _row("EVT.2003.03.03.01", date(2003, 3, 3), shape="chain"), _row("EVT.2004.04.04.01", date(2004, 4, 4), shape="chain")
    cyc = _fixture(a._replace(chain_parent_event_id=b.event_id), b._replace(chain_parent_event_id=a.event_id))
    missing = _fixture(a._replace(chain_parent_event_id="nonexistent"))
    for rows in (cyc, missing):
        with pytest.raises(hz.LelChainUnresolvable, match="lel_chain_unresolvable"):
            _derive(rows)


# ── the ruling guard (MB-1.2 item 7) and the substrate domain ───────────────────────────────────────────────────────────────────────

def test_the_ruling_guard_refuses_a_derivation_that_is_not_the_owner_approved_pair():
    revised = [r for r in _fixture() if r.provenance_lel_id != "EVT.1998.02.16.01"]
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
        hz.require_inside_substrate_domain(end_edge)
    hz.require_inside_substrate_domain(hz.RULED_HORIZON)
    hz.require_inside_substrate_domain((datetime(1998, 1, 1, tzinfo=UTC), datetime(2085, 1, 1, tzinfo=UTC)))
    from services.gochara_kernel.substrate import SUBSTRATE_DOMAIN_END
    assert (SUBSTRATE_DOMAIN_END - hz.RULED_HORIZON[1]).days == 331    # FINAL_BUILD_SCOPE FB-3 says 330 (counting 2084-02-05 as its own day); measured from the half-open end it is 331


def test_every_refusal_of_the_contract_exists_with_its_exact_token():
    contract = {"horizon_empty", "horizon_start_before_birth", "horizon_start_before_substrate_domain", "horizon_start_in_future", "horizon_outside_substrate_domain",
                "horizon_birth_anniversary_undefined", "lel_birth_row_unidentifiable", "lel_date_confidence_unknown", "lel_shape_unknown", "lel_date_missing",
                "lel_chain_unresolvable", "lel_shape_reading_sensitive", "horizon_derivation_disagrees_with_ruling", "lel_id_missing_on_candidate_first_event",
                "horizon_underivable_log_has_no_dated_event"}
    assert set(hz.REFUSAL_CODES) == contract and len(hz.REFUSAL_CODES) == len(set(hz.REFUSAL_CODES))
    assert "lel_dating_rules_disagree" not in hz.REFUSAL_CODES, "withdrawn by the steward (MB-CONTRACT-V1)"


def test_a_non_date_input_is_refused_not_truncated():
    with pytest.raises(hz.HorizonRefusal, match="not a date"):
        derive_chart_horizon("1984-02-05", [], BUILD)                    # type: ignore[arg-type]
    with pytest.raises(hz.HorizonRefusal, match="not a date"):
        derive_chart_horizon(BIRTH, [], datetime(2026, 1, 1))
