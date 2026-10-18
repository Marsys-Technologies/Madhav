"""J5Q preparation: synthetic evidence only; these are not held-out scores."""
from __future__ import annotations

import copy

import pytest

from services.gochara_eval import qualification as q
from services.gochara_eval.registry import CLASSES_27


def rows():
    return [dict(event_class="marriage", ws=f"2010-{m:02}-01", we=f"2010-{m:02}-03",
                 pk=f"2010-{m:02}-02", si=si, outcome_valence_for_native=v)
            for m, si, v in [(1, 1, "favourable"), (3, 2, "adverse"), (5, 3, "mixed")]]


def cells():
    return [{"event_class": c, "year": y, "computed": True}
            for c in CLASSES_27 if c != "birth_anchor" for y in range(1998, 2027)]


def test_gate_measurements_and_no_fabricated_instant_claim():
    gates = q.engineering_diagnostics(rows(), cells())
    assert set(gates) == {"valence", "peaks", "coverage", "pre_2020", "no_fabricated_instants"}
    assert gates["valence"]["status"] == "pass"
    assert gates["valence"]["measured"] == {"favourable": 1, "adverse": 1, "mixed": 1}
    assert gates["peaks"]["status"] == "pass"
    assert gates["peaks"]["measured"]["marriage/2010"]["largest_tie_share"] == pytest.approx(1 / 3)
    assert gates["coverage"]["status"] == "pass"
    assert gates["coverage"]["measured"]["marriage"] == {"computed": 29, "expected": 29, "fraction": 1.0}
    assert gates["pre_2020"]["status"] == "pass"
    assert gates["pre_2020"]["measured"] == {"computed": 572, "expected": 572}
    assert gates["no_fabricated_instants"]["status"] == "not_evaluable"
    assert gates["no_fabricated_instants"]["measured"] is None


def test_all_favourable_is_failed_and_unknown_is_not_success():
    data = rows()
    for r in data:
        r["outcome_valence_for_native"] = "favourable"
    assert q.engineering_diagnostics(data, None)["valence"]["status"] == "fail"
    data[0]["outcome_valence_for_native"] = "unqualified"
    assert q.engineering_diagnostics(data, None)["valence"]["status"] == "insufficient_evidence"
    for r in data:
        r.pop("outcome_valence_for_native")
    assert q.engineering_diagnostics(data, None)["valence"]["status"] == "insufficient_evidence"


def test_adjacent_gap_plateau_and_unknown_representative():
    data = rows()
    for r, v in zip(data, [0, .75e-9, 1.5e-9]):
        r["si"] = v
    peak = q.engineering_diagnostics(data, None)["peaks"]
    assert peak["status"] == "fail"
    assert peak["measured"]["marriage/2010"]["largest_tie_share"] == 1
    data[0]["si"] = None
    assert q.engineering_diagnostics(data, None)["peaks"]["status"] == "insufficient_evidence"


def test_empty_rows_and_missing_coverage_never_green():
    gates = q.engineering_diagnostics([], None)
    assert all(g["status"] in ("insufficient_evidence", "not_evaluable") for g in gates.values())
    gates = q.engineering_diagnostics(rows(), [])
    assert gates["coverage"]["status"] == "insufficient_evidence"
    assert gates["pre_2020"]["status"] == "insufficient_evidence"


def test_coverage_is_cell_based_and_pre_2020_is_not_inferred_from_windows():
    data = cells()
    data = [c for c in data if not (c["event_class"] == "marriage" and c["year"] == 1998)]
    gates = q.engineering_diagnostics(rows(), data)
    assert gates["coverage"]["status"] == "insufficient_evidence"
    assert gates["coverage"]["measured"]["marriage"]["fraction"] == 28 / 29
    assert gates["pre_2020"]["status"] == "insufficient_evidence"
    data = cells()
    for c in data:
        if c["event_class"] == "marriage":
            c["computed"] = c["year"] >= 2020
    assert q.engineering_diagnostics(rows(), data)["coverage"]["status"] == "fail"
    assert q.engineering_diagnostics(rows(), data)["pre_2020"]["status"] == "fail"


@pytest.mark.parametrize("bad", ["duplicate", "outside_year", "unknown_class", "untyped"])
def test_malformed_coverage_refused(bad):
    data = cells()
    if bad == "duplicate":
        data.append(data[0])
    elif bad == "outside_year":
        data[0]["year"] = 2027
    elif bad == "unknown_class":
        data[0]["event_class"] = "invented"
    else:
        data[0]["computed"] = "true"
    with pytest.raises(ValueError):
        q.engineering_diagnostics(rows(), data)


@pytest.mark.parametrize("key,value", [("si", float("nan")), ("si", -1), ("si", True),
                                       ("we", "2000-01-01"), ("event_class", "invented")])
def test_bad_window_input_refused(key, value):
    data = rows()
    data[0][key] = value
    with pytest.raises(ValueError):
        q.engineering_diagnostics(data, None)


def test_endpoint_values_and_original_status_survive_without_zero_filling():
    raw = {"t_cover": {"hits": 31, "total": 47, "pass": False, "misses": ["x"]},
           "t_time": {"pass": None, "status": "UNQUALIFIED", "capped_median_range": [0, 182]},
           "t_rank": {"status": "VOID", "eligible": 0, "floor": 17},
           "t_fp_overall": {"pass": False}, "t_fp": {"surgery": {"burden_pct": 99, "pass": False}},
           "t_honesty": {"status": "UNVERIFIABLE", "pass": False}}
    original = copy.deepcopy(raw)
    result = q.endpoint_records(raw)
    assert set(result) == {"t_cover", "t_time", "t_rank", "t_fp", "t_honesty"}
    assert {k: v["status"] for k, v in result.items()} == {
        "t_cover": "fail", "t_time": "insufficient_evidence", "t_rank": "not_evaluable",
        "t_fp": "fail", "t_honesty": "insufficient_evidence"}
    assert result["t_cover"]["measured"] == raw["t_cover"]
    assert result["t_rank"]["measured"] == raw["t_rank"]
    assert result["t_fp"]["measured"]["adverse"] == raw["t_fp"]
    assert raw == original
    assert all(v["status"] == "insufficient_evidence" and v["measured"] is None
               for v in q.endpoint_records(None).values())


def test_only_typed_boolean_can_report_pass():
    assert q.endpoint_records({"t_cover": {"pass": "true"}})["t_cover"]["status"] == "insufficient_evidence"
    assert q.endpoint_records({"t_cover": {"pass": True, "hits": 32, "total": 47}})["t_cover"]["status"] == "pass"


def test_tolerance_boundary_is_a_cut_not_a_tie():
    data = rows()
    for r, value in zip(data, [0, 1e-9, 2e-9]):
        r["si"] = value
    peak = q.engineering_diagnostics(data, None)["peaks"]
    assert peak["status"] == "pass"
    assert peak["measured"]["marriage/2010"]["largest_tie_share"] == 1 / 3


def test_peak_diagnostics_merge_abutting_candidates_and_exclude_post_mask():
    data = rows()
    data[1].update(ws="2010-01-04", we="2010-01-06", pk="2010-01-05")
    data.append(dict(data[2], ws="2030-01-01", we="2030-01-03", pk="2030-01-02"))
    peak = q.engineering_diagnostics(data, None)["peaks"]
    assert peak["measured"]["marriage/2010"]["candidates"] == 2
    assert "marriage/2030" not in peak["measured"]


def test_explicit_null_valence_is_an_honest_serializable_gap():
    import json
    data = rows()
    data[0]["outcome_valence_for_native"] = None
    gate = q.engineering_diagnostics(data, None)["valence"]
    assert gate["status"] == "insufficient_evidence"
    assert gate["measured"] == {"missing": 1, "adverse": 1, "mixed": 1}
    json.dumps(gate, sort_keys=True, allow_nan=False)


def test_diagnostics_exclude_anchor_and_wholly_unscored_dates():
    data = rows()
    data.extend([dict(data[0], event_class="birth_anchor"),
                 dict(data[0], ws="1997-01-01", we="1997-01-03", pk="1997-01-02"),
                 dict(data[0], ws="2026-04-18", we="2026-04-20", pk="2026-04-19")])
    gate = q.engineering_diagnostics(data, None)["valence"]
    assert gate["measured"] == {"favourable": 1, "adverse": 1, "mixed": 1}


def test_peak_census_uses_highest_member_at_exact_tolerance_boundary():
    data = rows()
    data[0]["si"] = 0
    data[1]["si"] = 0
    data[2]["si"] = 1
    data.append(dict(data[0], ws="2010-01-04", we="2010-01-06", pk="2010-01-05", si=1e-9))
    peak = q.engineering_diagnostics(data, None)["peaks"]
    # The first candidate's maximum is 1e-9, distinct from the March candidate's
    # zero at strict tau. Retaining its earlier zero invents a 2/3 plateau.
    assert peak["status"] == "pass"
    assert peak["measured"]["marriage/2010"]["largest_tie_share"] == 1 / 3


def test_canonical_mergers_do_not_tie_values_exactly_tau_apart():
    from services.gochara_eval.candidate import merge_candidates
    from services.gochara_eval.extract import merge_windows
    data = [dict(rows()[0], si=1e-9, ws="2010-01-01", we="2010-01-10", pk="2010-01-08"),
            dict(rows()[0], si=0, ws="2010-01-02", we="2010-01-03", pk="2010-01-02")]
    for merge in (merge_candidates, merge_windows):
        window = merge(data)["marriage"][0]
        assert window.si == 1e-9
        assert window.pk.isoformat() == "2010-01-08"

        rising = [dict(data[0], si=0, ws="2010-01-01", we="2010-01-03", pk="2010-01-02"),
                  dict(data[0], si=1e-9, ws="2010-01-04", we="2010-01-06", pk="2010-01-05")]
        high = merge(rising)["marriage"][0]
        assert high.si == 1e-9
        assert high.pk.isoformat() == "2010-01-05"
