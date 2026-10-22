"""HARNESS-3.2b (item harness-32b): two companion changes the od1 lanes need in the trial harness, one oracle per distinct claim, each failing on its single planted
reversion (`mutants_h32.py`, ids H-d / H-e*).

H-d   (SR-D6-OBJECTIVE-UNKNOWN (b)) the named blank `no_aspect_rule_defined_at_offset` is inside the CLOSED G-2 allowed set, where the set lives (the decision table and both gate
      profiles); the generic `objective_unknown_over_component` stays OUTSIDE it.  [BPHS 1:16496-16502 defines the dṛṣṭi table at 3-10/5-9/4-8/7 only; lane review
      X-20261022T171801Z-review-lane-n1 B-1]
H-e1  (SR-NEAR-STATION-TIE option A) the trial STOPS — the named refusal `near_station_tie_cap_exceeded` — when the near-station tie rule blanks more than 0.5 % of ANY class's
      windows; at or under 0.5 % it passes with the count reported.  [ruling "report the count per class in the TR"; lane review X-20261022T175406Z-review-lane-pt N-1]
H-e2  the count is taken per class, not pooled: one class over the cap is a stop although the pooled share is far below it.
H-e3  the function `window_sweep.near_station_tie_report` exists only on the od1 integration line: absent, the report field reads null and the gate NOT_EVALUATED — never PASS (§N.8).
H-e4  the count that reaches the report is the function's, fed the STORED windows (each class's own stored `unqualified_reason`)."""
import json
import sys

import pytest

import fixtures as fx
import gates
import trial_slice as ts
from gates import FAIL, NOT_EVALUATED, PASS

NEW_REASON = "no_aspect_rule_defined_at_offset"
GENERIC = "objective_unknown_over_component"
TIE = "tie_isolation_unresolved"
PROFILES = ("gate_profile.plan_defaults.json", "gate_profile.owner_proposal.json")


# ── H-d ──────────────────────────────────────────────────────────────────────────────────────────────────────

def _with_blank(reason, n=1):
    """The A10.1 trial whose blank windows are all `state_boundaries_incomplete` (allowed whatever the owner's answers) except `n` that carry `reason`; the census still
    accounts for every blank, so only the reason moves."""
    r = fx.a10_report()
    blank = r["totals"]["blank"]
    census = {"state_boundaries_incomplete": blank - n, reason: n}
    r["totals"]["blank_reasons"], r["reason_windows_any"] = dict(census), dict(census)
    r["totals"]["unresolved_factors_in_blank_windows"] = {k: {"windows": v, "members": v} for k, v in census.items()}
    return r


def _g2(report, profile_file=None, table=True):
    profile = fx.profile() if profile_file is None else json.loads((fx.HARNESS / profile_file).read_text())
    if table:
        return gates.evaluate(report, fx.a10_baseline(), profile, second_report=fx.second(), dispatch_modules=fx.dispatch_modules(),
                              dispatch_digests=fx.dispatch_digests(), decision_table=fx.decision_table())["gates"]["G-2"]
    return gates.g2_wiring(report, profile)


@pytest.mark.parametrize("profile_file", [None, *PROFILES])
@pytest.mark.parametrize("table", [True, False])
def test_d_a_blank_under_the_named_d6_reason_passes_g2(profile_file, table):
    """The closed set the rulings allow carries the named blank, in the decision table and in both gate profiles."""
    g = _g2(_with_blank(NEW_REASON), profile_file, table)
    assert g["status"] == PASS, [c for c in g["checks"] if c["status"] != PASS]
    assert NEW_REASON in g["allowed_reasons"]


@pytest.mark.parametrize("profile_file", [None, *PROFILES])
@pytest.mark.parametrize("table", [True, False])
def test_d_the_generic_objective_unknown_code_still_fails_g2(profile_file, table):
    """SR-D6-OBJECTIVE-UNKNOWN (c): a nameable operand under the generic code is a wiring defect; the set must not take it in."""
    g = _g2(_with_blank(GENERIC), profile_file, table)
    assert g["status"] == FAIL and GENERIC not in g["allowed_reasons"]
    assert any(c["status"] == FAIL and GENERIC in str(c["observed"]) for c in g["checks"])


def test_d_the_reason_is_in_each_data_file_with_its_ruling_cited():
    t = json.loads((fx.HARNESS / "g3_decision_table.json").read_text())
    assert NEW_REASON in t["allowed_reasons"] and GENERIC not in t["allowed_reasons"] and "SR-D6-OBJECTIVE-UNKNOWN" in t["source"]
    for f in PROFILES:
        rules = {r["reason"]: r for r in json.loads((fx.HARNESS / f).read_text())["allowed_reasons"]}
        assert NEW_REASON in rules and GENERIC not in rules and rules[NEW_REASON]["source"].startswith("SR-D6-OBJECTIVE-UNKNOWN") and rules[NEW_REASON]["when"] == {}


# ── H-e1, H-e2: the cap ──────────────────────────────────────────────────────────────────────────────────────

def _report(**blanked):
    r = fx.a10_report()
    r["near_station_tie"] = fx.near_station_tie(blanked, windows=1000)
    return r


def _tie_check(report):
    v = gates.evaluate(report, fx.a10_baseline(), fx.profile(), second_report=fx.second(), dispatch_modules=fx.dispatch_modules(), dispatch_digests=fx.dispatch_digests(),
                       decision_table=fx.decision_table())
    hits = [c for c in v["gates"]["G-3"]["checks"] if "near-station tie" in c["claim"]]
    assert len(hits) == 1
    return v, hits[0]


def test_e1_one_per_cent_of_a_classs_windows_is_the_named_refusal():
    v, c = _tie_check(_report(major_loss=10))                               # 10 of 1000 = 1 %
    assert c["status"] == FAIL and c["observed"]["refusal"] == "near_station_tie_cap_exceeded" == gates.NEAR_STATION_TIE_REFUSAL
    assert c["observed"]["classes_over_cap"] == {"major_loss": {"windows": 1000, "blanked": 10}} and "near_station_tie_cap_exceeded" in c["note"]
    assert v["gates"]["G-3"]["status"] == FAIL and "G-3" in v["failed"] and not v["dispatchable"]


def test_e1_two_tenths_of_a_per_cent_passes_with_the_count_reported():
    v, c = _tie_check(_report(major_loss=2, bereavement=1))                 # 2 of 1000 = 0.2 %
    assert c["status"] == PASS and c["observed"]["near_station_tie_blanked"] == 3
    assert c["observed"]["per_class"]["major_loss"] == {"windows": 1000, "blanked": 2} and c["observed"]["per_class"]["bereavement"]["blanked"] == 1
    assert v["gates"]["G-3"]["status"] == PASS


def test_e1_exactly_half_a_per_cent_is_not_over_the_cap():
    assert _tie_check(_report(major_loss=5))[1]["status"] == PASS          # "exceeds 0.5 %" — 5 of 1000 is at, not over
    assert _tie_check(_report(major_loss=6))[1]["status"] == FAIL


def test_e2_one_class_over_the_cap_stops_although_the_pooled_share_is_far_below_it():
    r = _report(major_loss=8)                                              # 0.8 % of one class; 8 of 12000 = 0.067 % pooled
    assert r["near_station_tie"]["cap_exceeded"] is False                   # the function's own pooled reading is under the cap ...
    v, c = _tie_check(r)
    assert c["status"] == FAIL and list(c["observed"]["classes_over_cap"]) == ["major_loss"]      # ... the harness judges per class


# ── H-e3: the function absent ────────────────────────────────────────────────────────────────────────────────

def _per(**kinds):
    return {"major_loss": {"windows_total": 1000, "blank_reasons": {TIE: 3, "state_boundaries_incomplete": 2}},
            "bereavement": {"windows_total": 500, "blank_reasons": {}}} | kinds


def test_e3_function_absent_the_field_is_null_and_the_gate_not_evaluated(monkeypatch):
    ws = pytest.importorskip("services.gochara_kernel.window_sweep")
    monkeypatch.delattr(ws, "near_station_tie_report", raising=False)       # main's checkout: the function is on the od1 integration line only
    sec, why = ts.near_station_tie_section(_per())
    assert sec is None and "near_station_tie_report" in why
    r = fx.a10_report()
    r["near_station_tie"], r["near_station_tie_unavailable"] = sec, why
    v, c = _tie_check(r)
    assert c["status"] == NOT_EVALUATED and v["gates"]["G-3"]["status"] == NOT_EVALUATED and "G-3" in v["not_evaluated"] and v["overall"] == "NO_DISPATCH_NOT_EVALUATED"


def test_e3_import_failure_is_the_same_null(monkeypatch):
    monkeypatch.setitem(sys.modules, "services.gochara_kernel.window_sweep", None)      # an import that fails outright
    monkeypatch.setitem(sys.modules, "services.gochara_kernel", None)
    sec, why = ts.near_station_tie_section(_per())
    assert sec is None and ("ImportError" in why or "ModuleNotFoundError" in why)


@pytest.mark.parametrize("section", [None, {}, {"near_station_tie_blanked": None, "per_class": {}}, {"near_station_tie_blanked": 0, "per_class": {"a": {"windows": "x", "blanked": 0}}}])
def test_e3_a_missing_or_malformed_count_is_never_a_pass(section):
    r = fx.a10_report()
    r["near_station_tie"] = section
    assert _tie_check(r)[1]["status"] == NOT_EVALUATED


# ── H-e4: the count reaches the report from the stored windows, through the function ─────────────────────────

def _function_semantics(drafts_by_class):
    """What `window_sweep.near_station_tie_report` does (lane od1-plateau-tie 367087ad9): counts the drafts whose `unqualified_reason` is tie_isolation_unresolved, per class."""
    per = {c: {"windows": len(d), "blanked": sum(1 for x in d if x.unqualified_reason == TIE)} for c, d in sorted(drafts_by_class.items())}
    w, b = sum(v["windows"] for v in per.values()), sum(v["blanked"] for v in per.values())
    return {"schema": "near_station_tie_blanked/1", "near_station_tie_blanked": b, "windows": w, "per_class": per, "cap_exceeded": b * 1000 > w * 5}


def test_e4_the_stored_blank_reasons_of_each_class_are_what_the_function_counts():
    sec, why = ts.near_station_tie_section(_per(), report_fn=_function_semantics)
    assert why is None
    assert sec["per_class"] == {"bereavement": {"windows": 500, "blanked": 0}, "major_loss": {"windows": 1000, "blanked": 3}} and sec["near_station_tie_blanked"] == 3


def test_e4_the_real_function_agrees_when_the_checkout_has_it():
    ws = pytest.importorskip("services.gochara_kernel.window_sweep")
    fn = getattr(ws, "near_station_tie_report", None)
    if fn is None:
        pytest.skip("this checkout has no near_station_tie_report (od1 integration line only)")
    assert ts.near_station_tie_section(_per())[0] == ts.near_station_tie_section(_per(), report_fn=fn)[0]
    assert ts.near_station_tie_section(_per())[0]["near_station_tie_blanked"] == 3


def test_e4_analyse_writes_the_section_into_the_report(monkeypatch):
    """End to end through `analyse` on canned stored rows: the tie blank in the stored census arrives as the per-class count in the report."""
    import test_analyse as ta
    ws = pytest.importorskip("services.gochara_kernel.window_sweep")
    monkeypatch.setattr(ws, "near_station_tie_report", _function_semantics, raising=False)
    t = ta.canned()
    t[ts.BLANK_SQL] = [("bereavement", TIE, 2), ("bereavement", "state_boundaries_incomplete", 1), ("major_loss", "solver_budget_exhausted", 1)]
    rep = ts.analyse(ta.Conn(t), {"classes": ta.CL, "requested_policy": "window_qualification/1"}, {"result_policy": ta.FakeResultPolicy})
    assert rep["near_station_tie"]["per_class"]["bereavement"] == {"windows": 30, "blanked": 2} and rep["near_station_tie"]["near_station_tie_blanked"] == 2
    assert rep["near_station_tie_unavailable"] is None
    monkeypatch.delattr(ws, "near_station_tie_report")
    rep = ts.analyse(ta.Conn(t), {"classes": ta.CL, "requested_policy": "window_qualification/1"}, {"result_policy": ta.FakeResultPolicy})
    assert rep["near_station_tie"] is None and rep["near_station_tie_unavailable"]
