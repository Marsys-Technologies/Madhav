"""test_flip_detector.py -- offline tests for platform/scripts/governance/flip_detector.py (the S-L1 flip report and hook validator).

flip_detector is a VERDICT-DECIDING tool: it produces the W7 flip report and validates the lane attribution hooks, so every verdict
class and every exit code is pinned here, and test_flip_detector_mutations.py proves these tests go red when each check is disabled.

No database, no network, no credentials: every state is an in-memory fixture (or a gzip snapshot written to a tmp dir), and `q()`, the
only function that can reach a database, is replaced by a tripwire for every test except the read-only-guard test.

Covered (SS requirements):
  (1a) UNDECLARED change -> FAIL            (1b) DECLARED-BUT-ABSENT -> FAIL / OPTIONAL_ABSENT warning when "optional": true
  (1c) KIND the hook did not declare -> FAIL (1d) the verdict is never PASS while any failure exists
  (2)  chart_dashas tier + l1_tajik_varsha_year_lords are printed as NOT CHECKED (never passing, never silent, exit 4 unless allowed)
  (3)  --validate-hooks / --require-lanes
  golden: realistic fixture built from real lane hook files (hooks_real/), pinned in golden_flip_detector_expected.json
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import random
import shutil
import sys
from datetime import timedelta

import pytest

HERE = pathlib.Path(__file__).resolve().parent
GOV_DIR = HERE.parent
FIX = HERE / "fixtures" / "flip_detector"
REAL_HOOKS = FIX / "hooks_real"
OLD_SCHEMA_HOOKS = FIX / "hooks_old_schema"
GOLDEN = FIX / "golden_flip_detector_expected.json"

# test_flip_detector_mutations.py re-runs this file against a mutated copy of the tool by pointing this variable at it.
_TOOL = pathlib.Path(os.environ.get("FLIP_DETECTOR_TOOL_UNDER_TEST") or (GOV_DIR / "flip_detector.py"))
_spec = importlib.util.spec_from_file_location("flip_detector_under_test", _TOOL)
F = importlib.util.module_from_spec(_spec)
sys.modules["flip_detector_under_test"] = F
_spec.loader.exec_module(F)

ORIG_Q = F.q
NATIVE = F.NATIVE
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"


@pytest.fixture(autouse=True)
def _no_database(monkeypatch):
    def tripwire(sql, retries=4):
        raise AssertionError("flip_detector test reached the database layer: " + sql[:80])
    monkeypatch.setattr(F, "q", tripwire)


# ----------------------------------------------------------------------------------------------- fixtures
def base_state():
    facts = []
    for ay in F.AYANS:
        facts += [[ay, "graha_position", "SUN", "sign", "Capricorn", "", "single"], [ay, "graha_position", "MOON", "nakshatra", "Purva Bhadrapada", "", "single"],
                  [ay, "graha_position", "LAGNA", "sign", "Aries", "", "single"], [ay, "graha_position", "MAR", "pada", "", "2", "single"],
                  [ay, "graha_position", "MOON", "longitude_sidereal", "", "327.055230133129", "single"],
                  [ay, "graha_gandanta", "MOON", "is_gandanta", "false", "", "single"], [ay, "argala_natal_matrix", "A1", "net", "", "1", "single"],
                  [ay, "graha_shadbala_total", "SUN", "total", "", "412.5", "two_pass_verified"]]
    for cat, subj, key, val in (("panchanga_tithi", "TITHI_BIRTH", "name", "Shukla Tritiya"), ("panchanga_vara", "VARA_BIRTH", "name", "Ravivara"),
                                ("panchanga_yoga", "YOGA_BIRTH", "name", "Shiva"), ("panchanga_karana", "KARANA_BIRTH", "name", "Garaja")):
        facts.append(["INVARIANT", cat, subj, key, val, "", "single"])
    dash = [["lahiri_chitrapaksha", "vimshottari", 1, "/Jupiter", "1975-08-18T21:50:23+00:00", "1991-08-18T21:50:23+00:00"],
            ["lahiri_chitrapaksha", "vimshottari", 1, "/Saturn", "1991-08-18T21:50:23+00:00", "2010-08-18T15:50:23+00:00"],
            ["lahiri_chitrapaksha", "yogini", 1, "/Pingala", "1950-01-01T00:00:00+00:00", "1951-02-04T23:13:00+00:00"]]
    return {"chart_facts": facts, "divisionals": [["lahiri_chitrapaksha", "D9", "Sun", "varga_position", "sign", "Leo", "", "Leo"]],
            "dashas": dash, "daily": [["2026-07-09", "5", "shukla", "5", "9", "Ashlesha", "3", "6", "7", "Panchami", "Guruvara", "Priti", "Taitila"]]}


def mutate(state, fn):
    s = copy.deepcopy(state)
    fn(s)
    return s


def hook(lane, entries, **kw):
    h = {"lane": lane, "ruling": lane, "pr": "#1", "description": "test hook", "may_change": entries}
    h.update(kw)
    return h


def entry(categories, change_types=None, table="chart_facts", **kw):
    e = {"table": table, "categories": list(categories)}
    if change_types is not None:
        e["change_types"] = list(change_types)
    e.update(kw)
    return e


ARGALA = hook("argala", [entry(["argala_natal_matrix"])])
TIERS = hook("tiers", [entry(["graha_shadbala_total"], ["tier"])])
ARGALA_OPT = hook("argala", [entry(["argala_natal_matrix"], optional=True)])  # a hook that is not the subject of the test
POS_TIER_OPT = hook("posn", [entry(["graha_position"], ["tier"], optional=True)])  # declares graha_position, but only its tier


def write_hooks(tmp_path, *hooks_, name="hooks"):
    d = tmp_path / name
    d.mkdir(exist_ok=True)
    for h in hooks_:
        (d / f"{h['lane']}.json").write_text(json.dumps(h))
    return d


def loaded(tmp_path, *hooks_):
    hs, errs = F.load_hooks(str(write_hooks(tmp_path, *hooks_)))
    assert not errs, errs
    return hs


def run(snap, cur, hooks_, chart=NATIVE, **kw):
    return F.compare_states(snap, cur, hooks_, chart, **kw)


def change_argala(s, val="2"):
    for r in s["chart_facts"]:
        if r[1] == "argala_natal_matrix":
            r[5] = val


def change_tier(s, to="classical_match"):
    for r in s["chart_facts"]:
        if r[1] == "graha_shadbala_total":
            r[6] = to


def change_pada_all(s):
    """MAR pada 2 -> 3 on all five ayanamshas: a class_num VALUE change (a continuous value such as a shadbala total is never a class change)."""
    for r in s["chart_facts"]:
        if r[1] == "graha_position" and r[2] == "MAR":
            r[5] = "3"


def change_mar_pada(s):
    for r in s["chart_facts"]:
        if r[1] == "graha_position" and r[2] == "MAR" and r[0] == "lahiri_chitrapaksha":
            r[5] = "3"


def shift_vimshottari(s, sec=6993):
    for r in s["dashas"]:
        if r[1] == "vimshottari":
            for i in (4, 5):
                r[i] = (F.ts_parse(r[i]) + timedelta(seconds=sec)).isoformat()


def counts(rep):
    return {k: v for k, v in rep["failure_counts"].items() if v}


NO_STANDING = ()  # production always uses F.STANDING_NOT_CHECKED; tests inject () only to reach the PASS class


# ----------------------------------------------------------------------------------------------- baseline behaviour
def test_identical_with_no_hooks_is_not_checked_not_pass():
    rep = run(base_state(), base_state(), [])
    assert rep["changes_total"] == 0 and not counts(rep) and not rep["ALERT_anchor_changed"]
    assert rep["verdict"] == "NOT_CHECKED" and F.exit_code(rep) == 4  # never a silent clean pass
    assert F.exit_code(rep, allow_not_checked=True) == 0


def test_pass_class_is_reachable_only_when_nothing_is_not_checked():
    rep = run(base_state(), base_state(), [], standing_not_checked=NO_STANDING)
    assert rep["verdict"] == "PASS" and F.exit_code(rep) == 0 and rep["not_checked"] == []


def test_attributed_change_names_the_lane(tmp_path):
    hooks = loaded(tmp_path, ARGALA)
    rep = run(base_state(), mutate(base_state(), change_argala), hooks, standing_not_checked=NO_STANDING)
    assert rep["verdict"] == "PASS" and rep["changes_total"] == 5 and rep["unattributed"] == 0
    assert all(c["lanes"] == ["argala"] for c in rep["changes"])


def test_continuous_and_timestamp_changes_are_not_class_changes():
    def f(s):
        for r in s["chart_facts"]:
            if r[3] == "longitude_sidereal":
                r[5] = "327.055415"
    rep = run(base_state(), mutate(base_state(), f), [], standing_not_checked=NO_STANDING)
    assert rep["verdict"] == "PASS" and rep["changes_total"] == 0 and rep["continuous"]["chart_facts"]["changed"] == 5


def test_chart_scope_of_a_hook(tmp_path):
    h = copy.deepcopy(ARGALA)
    h["charts"] = [OTHER[:8]]
    hooks = loaded(tmp_path, h)
    cur = mutate(base_state(), change_argala)
    on_native = run(base_state(), cur, hooks, chart=NATIVE)
    assert on_native["verdict"] == "FAIL" and counts(on_native) == {"UNDECLARED_CHANGE": 5}
    on_other = run(base_state(), cur, hooks, chart=OTHER)
    assert counts(on_other) == {} and on_other["unattributed"] == 0


def test_anchor_change_is_alert_and_wins_over_failures():
    def f(s):
        for r in s["chart_facts"]:
            if r[0] == "lahiri_chitrapaksha" and r[1] == "graha_position" and r[2] == "LAGNA":
                r[4] = "Taurus"
    rep = run(base_state(), mutate(base_state(), f), [])
    assert rep["verdict"] == "ALERT" and F.exit_code(rep) == 3 and F.exit_code(rep, allow_not_checked=True) == 3
    assert rep["failure_counts"]["UNDECLARED_CHANGE"] == 1
    other = run(base_state(), mutate(base_state(), f), [], chart=OTHER)  # anchors are native-only
    assert other["verdict"] == "FAIL" and not other["ALERT_anchor_changed"]


# ----------------------------------------------------------------------------------------------- (1a) undeclared
def test_1a_undeclared_fact_change_fails(tmp_path):
    hooks = loaded(tmp_path, ARGALA_OPT)
    rep = run(base_state(), mutate(base_state(), change_mar_pada), hooks)
    assert rep["verdict"] == "FAIL" and F.exit_code(rep) == 2
    assert counts(rep) == {"UNDECLARED_CHANGE": 1}
    assert rep["failures"]["UNDECLARED_CHANGE"][0]["category"] == "graha_position"


def test_1a_undeclared_change_with_no_hooks_at_all_fails():
    rep = run(base_state(), mutate(base_state(), change_argala), [])
    assert rep["verdict"] == "FAIL" and counts(rep) == {"UNDECLARED_CHANGE": 5}


def test_1a_undeclared_daily_column_and_row_fail(tmp_path):
    def col(s):
        s["daily"][0][9] = "Shashthi"
    rep = run(base_state(), mutate(base_state(), col), [])
    assert counts(rep) == {"UNDECLARED_CHANGE": 1} and rep["failures"]["UNDECLARED_CHANGE"][0]["category"] == "tithi_name"
    col_only = hook("panchanga", [entry(["tithi_name"], ["value"], table="panchanga_daily", optional=True)])
    ok = run(base_state(), mutate(base_state(), col), loaded(tmp_path, col_only))
    assert counts(ok) == {} and ok["unattributed"] == 0

    def row(s):
        s["daily"].append(["2026-07-10"] + s["daily"][0][1:])
    rep = run(base_state(), mutate(base_state(), row), loaded(tmp_path, col_only))  # a whole new date is category 'row', not declared
    assert counts(rep) == {"UNDECLARED_CHANGE": 1} and rep["failures"]["UNDECLARED_CHANGE"][0]["category"] == "row"
    with_row = hook("panchanga", [entry(["row"], ["appeared", "disappeared"], table="panchanga_daily")])
    assert counts(run(base_state(), mutate(base_state(), row), loaded(tmp_path, with_row))) == {}


def test_1a_undeclared_dasha_rowset_and_shift_fail(tmp_path):
    def drop(s):
        s["dashas"] = [r for r in s["dashas"] if r[3] != "/Saturn"]
    rep = run(base_state(), mutate(base_state(), drop), [])
    assert counts(rep) == {"UNDECLARED_CHANGE": 1} and [c["change"] for c in rep["changes"]] == ["disappeared"]
    rep = run(mutate(base_state(), drop), base_state(), [])
    assert counts(rep) == {"UNDECLARED_CHANGE": 1} and [c["change"] for c in rep["changes"]] == ["appeared"]
    rep = run(base_state(), mutate(base_state(), shift_vimshottari), [])
    assert counts(rep) == {"DASHA_SHIFT_UNDECLARED": 1} and rep["verdict"] == "FAIL"


def test_1a_declaring_one_category_does_not_cover_another(tmp_path):
    def both(s):
        change_argala(s)
        change_mar_pada(s)
    rep = run(base_state(), mutate(base_state(), both), loaded(tmp_path, ARGALA))
    assert counts(rep) == {"UNDECLARED_CHANGE": 1}  # argala (5 rows) attributed, the MAR pada change is not


# ----------------------------------------------------------------------------------------------- (1b) declared but absent
def test_1b_declared_but_absent_fails(tmp_path):
    rep = run(base_state(), base_state(), loaded(tmp_path, ARGALA))
    assert rep["verdict"] == "FAIL" and F.exit_code(rep, allow_not_checked=True) == 2
    assert counts(rep) == {"DECLARED_BUT_ABSENT": 1}
    assert "argala[0]" in rep["failures"]["DECLARED_BUT_ABSENT"][0]


def test_1b_optional_entry_absent_is_a_named_warning_not_a_failure(tmp_path):
    h = hook("argala", [entry(["argala_natal_matrix"], optional=True)])
    rep = run(base_state(), base_state(), loaded(tmp_path, h), standing_not_checked=NO_STANDING)
    assert rep["verdict"] == "PASS" and counts(rep) == {}
    assert len(rep["warnings"]) == 1 and rep["warnings"][0].startswith("OPTIONAL_ABSENT argala[0]")
    assert any(ln.startswith("WARNING OPTIONAL_ABSENT") for ln in F.render_summary(rep))


def test_1b_one_absent_entry_among_satisfied_ones_still_fails(tmp_path):
    h = hook("argala", [entry(["argala_natal_matrix"]), entry(["net_argala_per_varga"])])
    rep = run(base_state(), mutate(base_state(), change_argala), loaded(tmp_path, h))
    assert counts(rep) == {"DECLARED_BUT_ABSENT": 1} and "argala[1]" in rep["failures"]["DECLARED_BUT_ABSENT"][0]


def test_1b_expected_count_governs_the_entry(tmp_path):
    zero = hook("argala", [entry(["argala_natal_matrix"], expected_count={"exact": 0})])
    rep = run(base_state(), base_state(), loaded(tmp_path, zero), standing_not_checked=NO_STANDING)
    assert rep["verdict"] == "PASS" and counts(rep) == {}  # an explicit zero expectation is met, not 'absent'
    exact = hook("argala", [entry(["argala_natal_matrix"], expected_count={"exact": 3})])
    rep = run(base_state(), mutate(base_state(), change_argala), loaded(tmp_path, exact))
    assert counts(rep) == {"EXPECTATION_MISMATCH": 1} and rep["verdict"] == "FAIL"
    rng = hook("argala", [entry(["argala_natal_matrix"], expected_count={"min": 4, "max": 6})])
    assert counts(run(base_state(), mutate(base_state(), change_argala), loaded(tmp_path, rng), standing_not_checked=NO_STANDING)) == {}
    want_some = hook("argala", [entry(["argala_natal_matrix"], expected_count={"min": 1})])
    assert counts(run(base_state(), base_state(), loaded(tmp_path, want_some))) == {"EXPECTATION_MISMATCH": 1}


def test_1b_dasha_shift_entry_absent_fails_and_present_passes(tmp_path):
    eph = hook("ephemeris", [{"table": "chart_dashas", "kind": "dasha_shift", "systems": ["vimshottari"], "shift_range_sec": [6990, 6996]}])
    absent = run(base_state(), base_state(), loaded(tmp_path, eph))
    assert counts(absent) == {"DECLARED_BUT_ABSENT": 1}
    seen = run(base_state(), mutate(base_state(), shift_vimshottari), loaded(tmp_path, eph), standing_not_checked=NO_STANDING)
    assert seen["verdict"] == "PASS" and seen["dashas"]["lahiri_chitrapaksha|vimshottari"]["lanes"] == ["ephemeris"]
    narrow = copy.deepcopy(eph)
    narrow["may_change"][0]["shift_range_sec"] = [100, 200]
    wrong = run(base_state(), mutate(base_state(), shift_vimshottari), loaded(tmp_path, narrow))
    assert counts(wrong) == {"DECLARED_BUT_ABSENT": 1, "DASHA_SHIFT_UNDECLARED": 1}


def test_1b_hook_for_another_chart_is_not_declared_but_absent(tmp_path):
    h = copy.deepcopy(ARGALA)
    h["charts"] = [OTHER[:8]]
    rep = run(base_state(), base_state(), loaded(tmp_path, h), chart=NATIVE, standing_not_checked=NO_STANDING)
    assert counts(rep) == {} and rep["verdict"] == "PASS"


# ----------------------------------------------------------------------------------------------- (1c) kind not declared
def test_1c_value_change_under_a_tier_only_hook_is_a_kind_mismatch(tmp_path):
    rep = run(base_state(), mutate(base_state(), change_pada_all), loaded(tmp_path, POS_TIER_OPT))
    assert rep["verdict"] == "FAIL" and F.exit_code(rep) == 2
    # one value change per ayanamsha: five kind mismatches, none merely 'undeclared'
    assert counts(rep) == {"KIND_MISMATCH": 5}


def test_1c_kind_mismatch_reports_declared_kinds(tmp_path):
    rep = run(base_state(), mutate(base_state(), change_pada_all), loaded(tmp_path, POS_TIER_OPT))
    ex = rep["failures"]["KIND_MISMATCH"][0]
    assert ex["declared_kinds_by_lane"] == {"posn": ["tier"]} and ex["change"] == "value"
    # the tier change itself IS declared: only the value change is the problem
    ok = run(base_state(), mutate(base_state(), change_tier), loaded(tmp_path, TIERS), standing_not_checked=NO_STANDING)
    assert ok["verdict"] == "PASS" and all(c["lanes"] == ["tiers"] for c in ok["changes"])


def test_1c_tier_change_under_a_value_only_hook_is_a_kind_mismatch(tmp_path):
    h = hook("values", [entry(["graha_shadbala_total"], ["value"])])
    rep = run(base_state(), mutate(base_state(), change_tier), loaded(tmp_path, h))
    assert rep["verdict"] == "FAIL"
    assert counts(rep) == {"KIND_MISMATCH": 5, "DECLARED_BUT_ABSENT": 1}  # the hook's own declared value change never happened
    assert rep["failures"]["KIND_MISMATCH"][0]["declared_kinds_by_lane"] == {"values": ["value"]}


def test_1c_kind_mismatch_is_distinct_from_undeclared_and_both_count(tmp_path):
    def both(s):
        change_pada_all(s)
        change_argala(s)
    rep = run(base_state(), mutate(base_state(), both), loaded(tmp_path, POS_TIER_OPT))
    assert counts(rep) == {"UNDECLARED_CHANGE": 5, "KIND_MISMATCH": 5}


def test_1c_a_second_lane_declaring_the_kind_attributes_it(tmp_path):
    values = hook("values", [entry(["graha_position"], ["value"])])
    tier_lane = hook("posn", [entry(["graha_position"], ["tier"])])  # not optional: its own tier change never happens
    rep = run(base_state(), mutate(base_state(), change_pada_all), loaded(tmp_path, tier_lane, values), standing_not_checked=NO_STANDING)
    assert counts(rep) == {"DECLARED_BUT_ABSENT": 1}
    assert all(c["lanes"] == ["values"] for c in rep["changes"])


# ----------------------------------------------------------------------------------------------- (1d) never a false pass
FAILURE_SCENARIOS = {
    "undeclared": (lambda tmp: ([], mutate(base_state(), change_mar_pada))),
    "absent": (lambda tmp: (loaded(tmp, ARGALA), base_state())),
    "kind": (lambda tmp: (loaded(tmp, POS_TIER_OPT), mutate(base_state(), change_pada_all))),
    "expectation": (lambda tmp: (loaded(tmp, hook("argala", [entry(["argala_natal_matrix"], expected_count={"exact": 99})])), mutate(base_state(), change_argala))),
    "dasha_shift": (lambda tmp: ([], mutate(base_state(), shift_vimshottari))),
}


@pytest.mark.parametrize("name", sorted(FAILURE_SCENARIOS))
def test_1d_no_failure_scenario_is_ever_a_pass(tmp_path, name):
    hooks, cur = FAILURE_SCENARIOS[name](tmp_path)
    for standing in (F.STANDING_NOT_CHECKED, NO_STANDING):
        rep = run(base_state(), cur, hooks, standing_not_checked=standing)
        assert rep["verdict"] == "FAIL", (name, rep["failure_counts"])
        assert F.exit_code(rep) == 2 and F.exit_code(rep, allow_not_checked=True) == 2
        assert any(rep["failures"][k] for k in rep["failures"])
        assert any(ln.startswith("VERDICT: FAIL") for ln in F.render_summary(rep))


def test_1d_hook_error_is_a_failure(tmp_path):
    rep = run(base_state(), base_state(), [], hook_errors=["bad.json: not valid JSON"], standing_not_checked=NO_STANDING)
    assert rep["verdict"] == "FAIL" and counts(rep) == {"HOOK_ERROR": 1} and F.exit_code(rep, allow_not_checked=True) == 2


def test_1d_verdict_cannot_be_hidden_by_a_stale_verdict_field(tmp_path):
    rep = run(base_state(), mutate(base_state(), change_mar_pada), [])
    rep["verdict"] = "PASS"  # tamper: decide_verdict / exit_code recompute from the failure lists
    assert F.decide_verdict(rep) == "FAIL" and F.exit_code(rep, allow_not_checked=True) == 2


# ----------------------------------------------------------------------------------------------- (2) NOT CHECKED
def test_2_both_uncheckable_tier_changes_are_listed_on_every_compare(tmp_path):
    rep = run(base_state(), base_state(), [])
    ids = [n["id"] for n in rep["not_checked"]]
    assert ids == ["chart_dashas.tier", "l1_tajik_varsha_year_lords.tier", "chart_vichara", "ga_yoga_firings.strength", "bodha_msr_signals", "bodha_rm_resonances",
                   "ga_condition_composite", "ga_medical", "ga_vastu_*", "ga_prashna_*", "prashna_charts"]
    assert all(n["status"] == "NOT CHECKED" and n["readback"] for n in rep["not_checked"])


def test_2_not_checked_is_a_distinct_verdict_never_a_pass(tmp_path):
    h = hook("argala", [entry(["argala_natal_matrix"], optional=True)])
    rep = run(base_state(), base_state(), loaded(tmp_path, h))
    assert rep["verdict"] == "NOT_CHECKED" and rep["verdict"] not in ("PASS", "FAIL", "ALERT")
    assert F.exit_code(rep) == 4
    assert F.exit_code(rep, allow_not_checked=True) == 0


def test_2_summary_prints_both_not_checked_lines_even_when_allowed(tmp_path):
    rep = run(base_state(), base_state(), [])
    for allow in (False, True):
        lines = F.render_summary(rep, allow)
        assert any(ln.startswith("NOT CHECKED chart_dashas.tier") for ln in lines)
        assert any(ln.startswith("NOT CHECKED l1_tajik_varsha_year_lords.tier") for ln in lines)
        assert lines[0].startswith("VERDICT: NOT_CHECKED")
    assert F.render_summary(rep, True)[0].endswith("chart %s" % NATIVE) and "exit 0" in F.render_summary(rep, True)[0]
    assert any("only because --allow-not-checked" in ln for ln in F.render_summary(rep, True))


def test_2_declared_by_names_the_lane_that_declares_the_unverifiable_tier(tmp_path):
    tiers = hook("tiers", [entry(["graha_shadbala_total"], ["tier"]), entry(["mudda", "narayana"], ["tier"], table="chart_dashas"),
                           entry(["l1_tajik_varsha_year_lords"], ["tier"], table="l1_tajik_varsha_year_lords")])
    hooks = loaded(tmp_path, tiers)
    rep = run(base_state(), mutate(base_state(), change_tier), hooks)
    by = {n["id"]: n["declared_by_lanes"] for n in rep["not_checked"]}
    assert by["chart_dashas.tier"] == ["tiers"] and by["l1_tajik_varsha_year_lords.tier"] == ["tiers"]
    # the unobservable entries are NOT CHECKED, not declared-but-absent failures; the checkable entry was satisfied
    assert counts(rep) == {} and rep["verdict"] == "NOT_CHECKED"
    entry_level = [n for n in rep["not_checked"] if n["id"].startswith("tiers[")]
    assert sorted(n["id"] for n in entry_level) == ["tiers[1]", "tiers[2]"]


def test_2_not_checked_never_hides_a_failure(tmp_path):
    rep = run(base_state(), mutate(base_state(), change_mar_pada), [])
    assert rep["not_checked"] and rep["verdict"] == "FAIL" and F.exit_code(rep, allow_not_checked=True) == 2


def test_2_dasha_entries_are_not_checked_when_dashas_are_not_compared(tmp_path):
    h = hook("eph", [{"table": "chart_dashas", "kind": "dasha_shift", "systems": ["vimshottari"], "shift_range_sec": [6990, 6996]},
                     entry(["vimshottari"], ["appeared", "disappeared"], table="chart_dashas")])
    rep = run(base_state(), base_state(), loaded(tmp_path, h), have_dash=False)
    assert counts(rep) == {} and rep["verdict"] == "NOT_CHECKED"
    assert sorted(n["id"] for n in rep["not_checked"] if n["id"].startswith("eph[")) == ["eph[0]", "eph[1]"]


def test_2_cli_exit_codes_and_printed_output(tmp_path, capsys):
    d = write_hooks(tmp_path, hook("argala", [entry(["argala_natal_matrix"])]))
    before, after = snapshot_file(tmp_path, "b.json.gz", base_state()), snapshot_file(tmp_path, "a.json.gz", mutate(base_state(), change_argala))
    out = tmp_path / "r.json"
    code = F.main(["--compare", str(before), "--against", str(after), "--hooks-dir", str(d), "--out", str(out)])
    text = capsys.readouterr().out
    assert code == 4 and "NOT CHECKED chart_dashas.tier" in text and "NOT CHECKED l1_tajik_varsha_year_lords.tier" in text and "NOT CHECKED chart_vichara" in text
    rep = json.loads(out.read_text())
    assert rep["verdict"] == "NOT_CHECKED" and rep["exit_code"] == 4 and {"chart_dashas.tier", "l1_tajik_varsha_year_lords.tier"} <= {n["id"] for n in rep["not_checked"]}
    code = F.main(["--compare", str(before), "--against", str(after), "--hooks-dir", str(d), "--out", str(out), "--allow-not-checked"])
    text = capsys.readouterr().out
    assert code == 0 and "NOT CHECKED chart_dashas.tier" in text and json.loads(out.read_text())["verdict"] == "NOT_CHECKED"
    # a failure beats the allow flag
    bad = snapshot_file(tmp_path, "bad.json.gz", mutate(base_state(), change_mar_pada))
    code = F.main(["--compare", str(before), "--against", str(bad), "--hooks-dir", str(d), "--out", str(out), "--allow-not-checked"])
    capsys.readouterr()
    assert code == 2 and json.loads(out.read_text())["verdict"] == "FAIL"


def test_2_cli_report_is_deterministic_and_input_order_independent(tmp_path, capsys):
    d = write_hooks(tmp_path, ARGALA, TIERS)

    def one(tag, snap_rows, cur_rows):
        b = snapshot_file(tmp_path, f"b{tag}.json.gz", snap_rows)
        a = snapshot_file(tmp_path, f"a{tag}.json.gz", cur_rows)
        out = tmp_path / f"r{tag}.json"
        F.main(["--compare", str(b), "--against", str(a), "--hooks-dir", str(d), "--out", str(out)])
        capsys.readouterr()
        rep = json.loads(out.read_text())
        rep.pop("meta")
        return json.dumps(rep, sort_keys=True)

    def scramble(state):
        s = copy.deepcopy(state)
        rnd = random.Random(7)
        for k in ("chart_facts", "divisionals", "dashas"):
            rnd.shuffle(s[k])
        return s

    def both(s):
        change_argala(s)
        change_mar_pada(s)
        change_pada_all(s)
    cur = mutate(base_state(), both)
    r1, r2 = one("1", base_state(), cur), one("2", scramble(base_state()), scramble(cur))
    assert r1 == r2
    assert r1 == one("3", base_state(), cur)


# ----------------------------------------------------------------------------------------------- (3) hook validation
def snapshot_file(tmp_path, name, state, chart=NATIVE, sha=True):
    st = copy.deepcopy(state)
    st["meta"] = {"tool": "flip_detector.py", "chart_id": chart, "taken_at_utc": "2026-10-02T00:00:00+00:00"}
    p = tmp_path / name
    with gzip.open(p, "wt") as f:
        json.dump(st, f)
    if sha:
        (tmp_path / (name + ".sha256")).write_text(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {name}\n")
    return p


def validate(tmp_path, *args):
    return F.main(["--validate-hooks", "--hooks-dir", str(tmp_path / "hooks"), *args])


GOOD = hook("argala", [entry(["argala_natal_matrix"])])


def test_3_valid_directory_passes_and_writes_json(tmp_path, capsys):
    write_hooks(tmp_path, GOOD, TIERS)
    out = tmp_path / "v.json"
    assert validate(tmp_path, "--require-lanes", "argala,tiers", "--out", str(out)) == 0
    rep = json.loads(out.read_text())
    assert rep["verdict"] == "PASS" and rep["valid_lanes"] == ["argala", "tiers"] and rep["errors"] == []
    assert "valid hook lanes: ['argala', 'tiers']" in capsys.readouterr().out


def test_3_missing_required_lane_fails(tmp_path, capsys):
    write_hooks(tmp_path, GOOD)
    assert validate(tmp_path, "--require-lanes", "argala,daridra") == 2
    assert "MISSING HOOK: lane 'daridra'" in capsys.readouterr().out
    assert validate(tmp_path, "--require-lanes", "argala") == 0
    hooks, errs = F.load_hooks(str(tmp_path / "hooks"), required=["argala", "daridra", "tiers"])
    assert len(errs) == 2 and all("MISSING HOOK" in e for e in errs)


def test_3_a_required_lane_with_an_invalid_hook_counts_as_missing(tmp_path):
    bad = hook("daridra", [])
    write_hooks(tmp_path, GOOD, bad)
    hooks, errs = F.load_hooks(str(tmp_path / "hooks"), required=["daridra"])
    assert any("MISSING HOOK" in e for e in errs) and any("may_change" in e for e in errs)


def test_3_malformed_json_fails(tmp_path, capsys):
    write_hooks(tmp_path, GOOD)
    (tmp_path / "hooks" / "broken.json").write_text("{not json")
    assert validate(tmp_path) == 2
    assert "broken.json: not valid JSON" in capsys.readouterr().out


MALFORMED = {
    "empty_may_change": hook("empty_may_change", []),
    "no_category": hook("no_category", [{"table": "chart_facts", "categories": []}]),
    "no_categories_key": hook("no_categories_key", [{"table": "chart_facts"}]),
    "regex_category": hook("regex_category", [entry(["argala.*"])]),
    "bad_table": hook("bad_table", [entry(["a"], table="charts")]),
    "bad_change_type": hook("bad_change_type", [entry(["a"], ["changed"])]),
    "dasha_value_kind": hook("dasha_value_kind", [entry(["vimshottari"], ["value"], table="chart_dashas")]),
    "bad_count": hook("bad_count", [entry(["a"], expected_count={"exact": 1, "max": 2})]),
    "optional_not_bool": hook("optional_not_bool", [entry(["a"], optional="yes")]),
    "unknown_entry_field": hook("unknown_entry_field", [entry(["a"], guess="x")]),
    "bad_shift": hook("bad_shift", [{"table": "chart_dashas", "kind": "dasha_shift", "systems": ["vimshottari"], "shift_range_sec": [5, 1]}]),
    "shift_wrong_table": hook("shift_wrong_table", [{"table": "chart_facts", "kind": "dasha_shift", "systems": ["vimshottari"], "shift_range_sec": [1, 5]}]),
}


@pytest.mark.parametrize("name", sorted(MALFORMED))
def test_3_malformed_hook_is_rejected(tmp_path, name):
    write_hooks(tmp_path, MALFORMED[name])
    hooks, errs = F.load_hooks(str(tmp_path / "hooks"))
    assert errs and not hooks, name
    assert validate(tmp_path) == 2


@pytest.mark.parametrize("field", ["ruling", "description", "pr", "may_change"])
def test_3_each_required_top_level_field_is_required(tmp_path, field):
    h = copy.deepcopy(GOOD)
    del h[field]
    write_hooks(tmp_path, h)
    hooks, errs = F.load_hooks(str(tmp_path / "hooks"))
    assert errs and not hooks and any(field in e for e in errs)


def test_3_blank_description_and_lane_stem_mismatch_and_unknown_field(tmp_path):
    for label, mut in (("blank", lambda h: h.update(description="  ")), ("stem", lambda h: h.update(lane="other")), ("unknown", lambda h: h.update(extra=1)),
                       ("charts", lambda h: h.update(charts=["abc"]))):
        h = copy.deepcopy(GOOD)
        mut(h)
        d = tmp_path / f"d_{label}"
        d.mkdir()
        (d / "argala.json").write_text(json.dumps(h))
        hooks, errs = F.load_hooks(str(d))
        assert errs and not hooks, label


def test_3_missing_empty_and_nested_directories(tmp_path):
    hooks, errs = F.load_hooks(str(tmp_path / "nope"))
    assert errs and "HOOKS DIR NOT FOUND" in errs[0]
    (tmp_path / "empty").mkdir()
    hooks, errs = F.load_hooks(str(tmp_path / "empty"))
    assert errs and "NO HOOK FILES" in errs[0]
    d = write_hooks(tmp_path, GOOD)
    (d / "evidence").mkdir()
    (d / "evidence" / "junk.json").write_text("{not json")  # sub-folders are evidence, never hooks
    (d / "README.md").write_text("x")
    hooks, errs = F.load_hooks(str(d))
    assert not errs and [h["lane"] for h in hooks] == ["argala"]


def test_3_default_hooks_dir_is_the_slhooks_folder():
    assert F.DEFAULT_HOOKS_DIR.endswith(os.path.join("00_ARCHITECTURE", "briefs", "suvarna", "exec", "s_l1_attribution_hooks"))


# ----------------------------------------------------------------------------------------------- real hook files
REAL_LANES = sorted(f.stem for f in REAL_HOOKS.glob("*.json"))  # the integration's 24 hook files (fa2_ga_vargas, the 24th, landed in the hook directory with the F-A2 hook commit)
PENDING_HOOKS = ()  # empty: F-A2 (PR 2858) LANDED, so no hook file may be absent from the hook directory; test_f12 enforces hooks_real == the hook directory byte for byte, with no exception
INTEGRATION_LANES = [n for n in REAL_LANES if n + ".json" not in PENDING_HOOKS]


def test_real_hook_files_validate(capsys):
    assert F.main(["--validate-hooks", "--hooks-dir", str(REAL_HOOKS), "--require-lanes", ",".join(REAL_LANES)]) == 0
    assert F.main(["--validate-hooks", "--hooks-dir", str(REAL_HOOKS), "--require-lanes", "daridra"]) == 2
    assert "MISSING HOOK: lane 'daridra'" in capsys.readouterr().out


def test_old_schema_hook_files_are_rejected(capsys):
    """argala.json on branch TI-argala-l1-001 and fa2_ga_vargas.json (TI-l1-fa2-key-001) predate the validator's schema (no may_change)."""
    hooks, errs = F.load_hooks(str(OLD_SCHEMA_HOOKS))
    assert not hooks
    assert any("argala.json" in e and "may_change" in e for e in errs)
    assert any("fa2_ga_vargas.json" in e and "may_change" in e for e in errs)
    assert F.main(["--validate-hooks", "--hooks-dir", str(OLD_SCHEMA_HOOKS)]) == 2
    capsys.readouterr()


# ----------------------------------------------------------------------------------------------- golden on real hooks
def real_hooks(tmp_path, lanes, patch=None):
    d = tmp_path / "golden_hooks"
    d.mkdir(exist_ok=True)
    for lane in lanes:
        h = json.loads((REAL_HOOKS / f"{lane}.json").read_text())
        if patch and lane in patch:
            patch[lane](h)
        (d / f"{lane}.json").write_text(json.dumps(h))
    hooks, errs = F.load_hooks(str(d), lanes)
    assert not errs, errs
    return hooks


GOLDEN_LANES = ["argala", "gandanta", "sun_required_rupa", "tiers"]
SE1_LANE = "ephemeris_backend_shift"


def golden_before():
    s = base_state()
    for ay in F.AYANS:
        for subj in ("SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN", "RAHU", "KETU", "LAGNA"):
            s["chart_facts"].append([ay, "graha_gandanta", subj, "is_gandanta", "false", "", "single"])
        s["chart_facts"].append([ay, "graha_shadbala_total", "SUN", "ratio", "", "1.694", "two_pass_verified"])
        s["chart_facts"].append([ay, "graha_shadbala_cheshta", "SUN", "cheshta", "", "40", "two_pass_verified"])
        s["chart_facts"].append([ay, "graha_in_house_composite_strength", "SUN_IN_HOUSE_1", "bphs_weighted", "", "0.81", "single"])
    s["chart_facts"].append(["INVARIANT", "graha_shadbala_total", "SUN", "required_rupa", "", "5", "classical_match"])
    for ay in F.AYANS:
        for n in range(49):                                                                  # special_lagna: 49 subjects x 5 ayanamshas = 245 rows (tiers[3] expects exactly 245)
            s["chart_facts"].append([ay, "special_lagna", f"SL{n:02d}", "sign", "Aries", "", "two_pass_verified"])
        for cusp in range(12):                                                               # kp_cuspal_significators: 12 cusps x 5 keys x 5 ayanamshas = 300 rows (tiers[4])
            for key in ("sign_lord", "star_lord", "sub_lord", "sub_sub_lord", "cusp_degree_text"):
                s["chart_facts"].append([ay, "kp_cuspal_significators", f"CUSP{cusp + 1}", key, "Sun", "", "two_pass_verified"])
    s["dashas"].append(["lahiri_chitrapaksha", "mudda", 1, "/Sun", "2000-01-01T06:00:00+00:00", "2001-01-01T06:00:00+00:00"])
    return s


def golden_after():
    s = golden_before()
    extra = []
    for r in s["chart_facts"]:
        if r[1] == "graha_gandanta" and r[3] == "is_gandanta":
            extra.append(list(r[:4]) + ["false", "", "single"])  # strict_0_48 twin: the key now has two occurrences (50 keys)
    s["chart_facts"] += extra
    change_argala(s, "3")                                                                   # argala lane: 5 value changes
    for r in s["chart_facts"]:
        if r[1] == "graha_shadbala_total" and r[3] == "required_rupa":
            r[5] = "6.5"                                                                    # sun_required_rupa: 5 -> 6.5, ayanamsha INVARIANT
        if r[1] == "graha_shadbala_total" and r[3] == "ratio":
            r[5] = "1.3031"                                                                 # continuous: not a class change
        if r[1] == "graha_shadbala_cheshta":
            r[6] = "single"                                                                 # tiers lane: 5 tier changes
        if r[1] == "graha_shadbala_total" and r[3] == "total":
            r[6] = "classical_match"                                                        # tiers lane: 5 tier changes
        if r[1] in ("special_lagna", "kp_cuspal_significators"):
            r[6] = "single"                                                                 # tiers lane: 245 + 300 tier changes (exact counts in tiers[3], tiers[4])
        if r[3] == "longitude_sidereal":
            r[5] = "327.055415"                                                             # continuous: ignored
    return s


def summarize(rep):
    return {"verdict": rep["verdict"], "failure_counts": rep["failure_counts"], "warnings": rep["warnings"], "not_checked": [[n["id"], n["declared_by_lanes"]] for n in rep["not_checked"]],
            "changes_total": rep["changes_total"], "by_table_category_change_lane": rep["by_table_category_change_lane"],
            "absent": rep["failures"]["DECLARED_BUT_ABSENT"], "exit_default": F.exit_code(rep), "exit_allow_not_checked": F.exit_code(rep, True)}


def strip_counts(h):
    """Attribution-only variant of a real hook: every entry optional and without expected_count, so the golden shows WHICH lane each change goes to
    independently of the lane's production row counts (which synthetic data cannot honour)."""
    for e in h["may_change"]:
        e.pop("expected_count", None)
        e["optional"] = True


def golden_cases(tmp_path):
    verbatim = real_hooks(tmp_path, GOLDEN_LANES)
    stripped = real_hooks(tmp_path, GOLDEN_LANES, patch={lane: strip_counts for lane in GOLDEN_LANES})
    all_hooks, errs = F.load_hooks(str(REAL_HOOKS), REAL_LANES)
    assert not errs
    wo_se1 = [h for h in all_hooks if h["lane"] != SE1_LANE]                                # the 22 integration hooks that predate ephemeris_backend_shift + pending fa2: the original case, unchanged
    # the lane as the original 24-hook case saw it: entries 0 to 26 (six dasha_shift, the 20 per-ayanamsha level-4 counts, the exact-0 row-set entry). Entries 27 to 29 (the
    # composite label+number COUNT bounds, added after the P4 finding of the Linux rehearsal) are a separate case below, so the golden stays add-only.
    pre_composite = [dict(h, may_change=h["may_change"][:27]) if h["lane"] == SE1_LANE else h for h in all_hooks]
    out = {"all_23_hooks_unchanged_native_chart": summarize(run(base_state(), base_state(), wo_se1)),
           "all_24_hooks_unchanged_native_chart": summarize(run(base_state(), base_state(), pre_composite)),   # + ephemeris_backend_shift (entries 0 to 26): its 4 non-optional dasha_shift entries read DECLARED_BUT_ABSENT by design
           "all_24_hooks_unchanged_native_chart_with_composite_entries": summarize(run(base_state(), base_state(), all_hooks)),   # + entries 27 to 29: two more EXPECTATION_MISMATCH (their minimum is positive: varga_position 900, sensitive_degree_check 10)
           "four_lanes_verbatim_synthetic_changes": summarize(run(golden_before(), golden_after(), verbatim)),
           "four_lanes_counts_stripped": summarize(run(golden_before(), golden_after(), stripped))}

    def noisy(s):
        change_mar_pada(s)                                                                  # undeclared (no lane declares graha_position)
        for r in s["chart_facts"]:
            if r[1] == "graha_shadbala_cheshta":
                r[5] = "41"                                                                 # tiers declares tier only: kind mismatch (5)
        shift_vimshottari(s)                                                                # no ephemeris hook loaded: undeclared dasha shift
    out["noisy_counts_stripped"] = summarize(run(golden_before(), mutate(golden_after(), noisy), stripped))
    return out


def test_golden_real_hooks_flip_report(tmp_path):
    got = golden_cases(tmp_path)
    if os.environ.get("FLIP_DETECTOR_REGEN_GOLDEN") == "1":
        GOLDEN.write_text(json.dumps(got, indent=1, sort_keys=True) + "\n")
    want = json.loads(GOLDEN.read_text())
    assert json.loads(json.dumps(got, sort_keys=True)) == want


def test_golden_semantics_read_by_a_human(tmp_path):
    """The golden file is not trusted blindly: restate its meaning independently of the pinned numbers."""
    cases = golden_cases(tmp_path)
    u = cases["all_23_hooks_unchanged_native_chart"]
    # every shipped integration hook is explicit about absence (count or optional): an unchanged chart is judged by the counts, never as 'absent'
    assert u["absent"] == [] and u["verdict"] == "FAIL" and u["failure_counts"]["EXPECTATION_MISMATCH"] > 0
    assert sum(v for k, v in u["failure_counts"].items() if k != "EXPECTATION_MISMATCH") == 0
    v = cases["four_lanes_verbatim_synthetic_changes"]
    assert v["verdict"] == "FAIL" and v["failure_counts"]["EXPECTATION_MISMATCH"] > 0   # synthetic data cannot honour production row counts
    c = cases["four_lanes_counts_stripped"]
    assert c["verdict"] == "NOT_CHECKED" and c["exit_default"] == 4 and c["exit_allow_not_checked"] == 0 and c["absent"] == []
    assert sum(c["failure_counts"].values()) == 0 and c["changes_total"] == 611
    by = {tuple(k[:3]) + (k[3],): n for k, n in c["by_table_category_change_lane"]}
    assert by[("chart_facts", "special_lagna", "tier", "tiers")] == 245 and by[("chart_facts", "kp_cuspal_significators", "tier", "tiers")] == 300
    assert by[("chart_facts", "graha_gandanta", "occurrence_count", "gandanta")] == 50 and by[("chart_facts", "argala_natal_matrix", "value", "argala")] == 5
    n = cases["noisy_counts_stripped"]
    assert n["verdict"] == "FAIL" and n["failure_counts"]["UNDECLARED_CHANGE"] == 1
    assert n["failure_counts"]["KIND_MISMATCH"] == 5 and n["failure_counts"]["DASHA_SHIFT_UNDECLARED"] == 1
    # all 24 files = the 23 above + ephemeris_backend_shift: the ONLY change in the report is the se1 hook's own entries (a rebuild that did not run on se1 fails)
    w = cases["all_24_hooks_unchanged_native_chart"]
    assert [x.split(": the hook declares")[0] for x in w["absent"]] == [f"DECLARED BUT ABSENT ephemeris_backend_shift[{i}] (chart_dashas:{sysid})" for i, sysid in
                                                                          enumerate(("vimshottari", "vimshottari_kp", "kalachakra", "kalachakra"))]
    assert w["verdict"] == "FAIL" and w["failure_counts"]["DECLARED_BUT_ABSENT"] == 4 and w["changes_total"] == 0
    assert w["failure_counts"]["EXPECTATION_MISMATCH"] == u["failure_counts"]["EXPECTATION_MISMATCH"] + 20   # the 20 exact per-ayanamsha level-4 membership entries; entry 26 (exact 0) holds
    assert sum(v for k, v in w["failure_counts"].items() if k not in ("EXPECTATION_MISMATCH", "DECLARED_BUT_ABSENT")) == 0
    assert w["not_checked"] == u["not_checked"] and w["by_table_category_change_lane"] == u["by_table_category_change_lane"] == []
    assert [x.split(" (")[0] for x in w["warnings"]] == ["OPTIONAL_ABSENT ephemeris_backend_shift[4]", "OPTIONAL_ABSENT ephemeris_backend_shift[5]"] and u["warnings"] == []
    assert w["exit_default"] == 2 and w["exit_allow_not_checked"] == 2
    # the same 24 hooks with the lane's composite entries 27 to 29 (count bounds on rows that carry a label AND a number): the ONLY differences are the two entries with a
    # positive minimum (27: varga_position min 900, 28: sensitive_degree_check min 10; 29: ayurdaya allows 0) reading EXPECTATION_MISMATCH on an unchanged chart
    wc = cases["all_24_hooks_unchanged_native_chart_with_composite_entries"]
    assert wc["failure_counts"]["EXPECTATION_MISMATCH"] == w["failure_counts"]["EXPECTATION_MISMATCH"] + 2
    assert {k: v for k, v in wc["failure_counts"].items() if k != "EXPECTATION_MISMATCH"} == {k: v for k, v in w["failure_counts"].items() if k != "EXPECTATION_MISMATCH"}
    assert wc["absent"] == w["absent"] and wc["warnings"] == w["warnings"] and wc["changes_total"] == 0 and wc["verdict"] == "FAIL"
    for case in cases.values():
        assert [x[0] for x in case["not_checked"]][:2] == ["chart_dashas.tier", "l1_tajik_varsha_year_lords.tier"]
        if case["verdict"] == "FAIL":
            assert case["exit_default"] == 2 and case["exit_allow_not_checked"] == 2  # failures are never softened by the flag
    assert dict(c["not_checked"])["chart_dashas.tier"] == ["tiers"] and dict(c["not_checked"])["l1_tajik_varsha_year_lords.tier"] == ["tiers"]


def test_golden_clean_run_attributes_every_change(tmp_path):
    hooks = real_hooks(tmp_path, GOLDEN_LANES, patch={lane: strip_counts for lane in GOLDEN_LANES})
    rep = run(golden_before(), golden_after(), hooks)
    assert [c["lanes"] for c in rep["changes"] if c["category"] == "graha_gandanta"] == [["gandanta"]] * 50
    assert all(c["lanes"] for c in rep["changes"])


# The ONLY entries that read DECLARED_BUT_ABSENT on an unchanged chart, on purpose (SS ruling 2026-10-03, S-L1 integration): the four non-optional dasha_shift entries of
# ephemeris_backend_shift. They declare that the rebuild ran on the canonical Swiss .se1 backend, which moves the Moon and so translates the Moon-anchored dasha timelines
# (Vimshottari, its KP sub-periods, Kalachakra). A rebuild that did NOT run on se1 shifts nothing, and these entries are the proof that such a rebuild FAILS.
# The set is pinned by (lane, entry index, systems, ayanamsha_ids): any other non-optional dasha_shift entry, or any other absent entry, is a failure of this test.
EXPECTED_SHIFT_PROOF_ENTRIES = (
    ("ephemeris_backend_shift", 0, ["vimshottari"], None),
    ("ephemeris_backend_shift", 1, ["vimshottari_kp"], None),
    ("ephemeris_backend_shift", 2, ["kalachakra"], ["lahiri_chitrapaksha", "krishnamurti", "raman", "true_chitra"]),
    ("ephemeris_backend_shift", 3, ["kalachakra"], ["surya_siddhanta_classical"]),
)


def shift_proof_labels(hooks):
    by_lane = {h["lane"]: h for h in hooks}
    return [f"DECLARED BUT ABSENT {lane}[{i}] (chart_dashas:{','.join(by_lane[lane]['may_change'][i]['systems'])})" for lane, i, _s, _a in EXPECTED_SHIFT_PROOF_ENTRIES]


def test_the_four_se1_shift_proof_entries_exist_and_are_non_optional():
    """The four entries that must read DECLARED_BUT_ABSENT on an unchanged chart exist, are chart_dashas dasha_shift entries, are NOT optional and carry a shift range,
    and they are the ONLY non-optional dasha_shift entries in the whole shipped hook set (so the exemption below cannot quietly widen)."""
    hooks, errs = F.load_hooks(str(REAL_HOOKS), REAL_LANES)
    assert not errs
    by_lane = {h["lane"]: h for h in hooks}
    for lane, i, systems, ayans in EXPECTED_SHIFT_PROOF_ENTRIES:
        e = by_lane[lane]["may_change"][i]
        assert e["table"] == "chart_dashas" and e["kind"] == "dasha_shift" and e["systems"] == systems, (lane, i)
        assert e.get("optional", False) is False, f"{lane}[{i}] must be non-optional: it is the proof that a rebuild that did not run on se1 fails"
        assert e.get("ayanamsha_ids") == ayans and "expected_count" not in e and len(e["shift_range_sec"]) == 2 and e["shift_range_sec"][0] > 0, (lane, i)
    non_optional = sorted((h["lane"], i) for h in hooks for i, e in enumerate(h["may_change"]) if e.get("kind") == "dasha_shift" and not e.get("optional"))
    assert non_optional == sorted((lane, i) for lane, i, _s, _a in EXPECTED_SHIFT_PROOF_ENTRIES)
    assert 4 == len(EXPECTED_SHIFT_PROOF_ENTRIES) and by_lane["ephemeris_backend_shift"]["charts"] == ["482012f1"]


def test_every_integration_hook_states_its_absence_rule(tmp_path):
    """Every entry of every shipped hook either declares an expected_count, is optional, is a dasha_shift marked optional, or is an entry the detector cannot observe:
    none reads DECLARED_BUT_ABSENT on an unchanged chart (the review finding that drove the lane authors' fixes), EXCEPT the four non-optional dasha_shift entries of
    ephemeris_backend_shift on the native chart, which read DECLARED_BUT_ABSENT by design (see EXPECTED_SHIFT_PROOF_ENTRIES). Nothing else is exempt."""
    hooks, errs = F.load_hooks(str(REAL_HOOKS), REAL_LANES)
    assert not errs
    for chart in (OTHER, "cb73cd3d-9eba-4220-9902-0de91566e980"):
        rep = run(base_state(), base_state(), hooks, chart=chart, standing_not_checked=NO_STANDING)
        assert rep["failures"]["DECLARED_BUT_ABSENT"] == [], (chart, rep["failures"]["DECLARED_BUT_ABSENT"])   # the se1 hook is scoped to the native chart only
    nat = run(base_state(), base_state(), hooks, standing_not_checked=NO_STANDING)
    got = nat["failures"]["DECLARED_BUT_ABSENT"]
    want = [w + ": the hook declares this change and nothing changed" for w in shift_proof_labels(hooks)]
    assert len(got) == len(want) == 4 and sorted(m.split(" (mark the entry")[0] for m in got) == sorted(want), (got, want)   # exactly the four named entries, no more, no fewer
    assert any(m.startswith("EXPECTATION MISMATCH tiers[3]") for m in nat["failures"]["EXPECTATION_MISMATCH"])  # exact 245 special_lagna tier changes, none happened here
    assert "tiers[1]" in [n["id"] for n in nat["not_checked"]]  # the chart_dashas tier-only entry is NOT CHECKED, never absent
    # the rule is not weakened for any other hook: without the se1 hook loaded no entry of the remaining 23 files reads absent on the native chart
    others = [h for h in hooks if h["lane"] != "ephemeris_backend_shift"]
    rest = run(base_state(), base_state(), others, standing_not_checked=NO_STANDING)
    assert rest["failures"]["DECLARED_BUT_ABSENT"] == []


def se1_shifted_pair(unshifted=()):
    """A before / after pair in which the dasha rows the four shift-proof entries watch really moved by the measured se1 amounts (Vimshottari and its KP sub-periods
    +6,992 s; Kalachakra +145,090 s, Surya Siddhanta +150,309 s), on top of base_state(). `unshifted` names systems whose rows stay put (a rebuild that did not move them)."""
    before, after = base_state(), base_state()
    for system, ay, level, sec in (("vimshottari", "lahiri_chitrapaksha", 4, 6992), ("vimshottari_kp", "lahiri_chitrapaksha", 3, 6992),
                                   ("kalachakra", "raman", 4, 145090), ("kalachakra", "surya_siddhanta_classical", 4, 150309)):
        for j in range(3):
            start = F.ts_parse(f"2010-0{j + 1}-01T00:00:00+00:00")
            end = start + timedelta(days=20)
            moved = 0 if (system, ay) in unshifted or system in unshifted else sec + j
            before["dashas"].append([ay, system, level, f"/L{j}", start.isoformat(), end.isoformat()])
            after["dashas"].append([ay, system, level, f"/L{j}", (start + timedelta(seconds=moved)).isoformat(), (end + timedelta(seconds=moved)).isoformat()])
    return before, after


def test_the_four_se1_shift_proof_entries_read_present_when_the_rows_really_shifted():
    """The pair of the exemption above: on a chart whose Moon-anchored dasha rows moved by the measured amounts the same four entries are NOT absent, so the
    exemption cannot hide a hook that never fires. And each of the four reads absent on its own when only ITS rows stay put."""
    hooks, errs = F.load_hooks(str(REAL_HOOKS), REAL_LANES)
    assert not errs
    se1 = [h for h in hooks if h["lane"] == SE1_LANE]
    before, after = se1_shifted_pair()
    rep = run(before, after, se1, standing_not_checked=NO_STANDING)
    assert rep["failures"]["DECLARED_BUT_ABSENT"] == [] and rep["failure_counts"]["DASHA_SHIFT_UNDECLARED"] == 0
    assert not any(m.startswith(f"EXPECTATION MISMATCH {SE1_LANE}[{i}]") for m in rep["failures"]["EXPECTATION_MISMATCH"] for i in (0, 1, 2, 3))
    moved = {k: v for k, v in rep["dashas"].items() if v.get("rows_shifted")}
    assert sorted(moved) == ["lahiri_chitrapaksha|vimshottari", "lahiri_chitrapaksha|vimshottari_kp", "raman|kalachakra", "surya_siddhanta_classical|kalachakra"]
    assert all(v["lanes"] == [SE1_LANE] and v["rows_outside_every_declared_range"] == 0 for v in moved.values()), moved
    # each entry, taken alone, can still read absent: leave exactly one watched group unshifted and exactly that entry fails
    for (system, ay), idx in ((("vimshottari", "lahiri_chitrapaksha"), 0), (("vimshottari_kp", "lahiri_chitrapaksha"), 1),
                              (("kalachakra", "raman"), 2), (("kalachakra", "surya_siddhanta_classical"), 3)):
        before, after = se1_shifted_pair(unshifted=((system, ay),))
        rep = run(before, after, se1, standing_not_checked=NO_STANDING)
        absent = rep["failures"]["DECLARED_BUT_ABSENT"]
        assert len(absent) == 1 and absent[0].startswith(f"DECLARED BUT ABSENT {SE1_LANE}[{idx}] "), (system, ay, absent)


# ----------------------------------------------------------------------------------------------- unchanged safety properties
@pytest.mark.parametrize("bad", ["update chart_facts set x=1", "delete from chart_facts", "insert into x values (1)", "drop table x", "with a as (select 1) delete from x",
                                 "select 1; delete from chart_facts", "select 1;update x set y=2", "SELECT 1 ; DROP TABLE x"])
def test_read_only_guard(bad, tmp_path, monkeypatch):
    """The guard must refuse BEFORE any process is started. A stub psql on PATH proves it (and keeps this test fast, with no 30 s retry
    sleeps, even when the guard is mutated away: the stub exits 0, so the call returns instead of raising and the test fails at once)."""
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    log = tmp_path / "psql_calls.log"
    stub = stub_dir / "psql"
    stub.write_text(f"#!/bin/sh\necho called >> {log}\nexit 0\n")
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.delenv("FLIP_READER", raising=False)
    monkeypatch.setattr(F.time, "sleep", lambda *_: None)
    with pytest.raises(RuntimeError, match="read-only"):
        ORIG_Q(bad)
    assert not log.exists(), "a refused statement must never reach psql"


def test_read_only_guard_allows_one_select_with_a_trailing_semicolon(tmp_path, monkeypatch):
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    stub = stub_dir / "psql"
    stub.write_text("#!/bin/sh\nprintf 'a\\tb\\n'\n")
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.delenv("FLIP_READER", raising=False)
    assert ORIG_Q("select 1;") == [["a", "b"]]


def test_compare_against_other_chart_snapshot_is_refused(tmp_path, capsys):
    d = write_hooks(tmp_path, ARGALA)
    a = snapshot_file(tmp_path, "a.json.gz", base_state(), chart=NATIVE)
    b = snapshot_file(tmp_path, "b.json.gz", base_state(), chart=OTHER)
    assert F.main(["--compare", str(a), "--against", str(b), "--hooks-dir", str(d), "--out", str(tmp_path / "x.json")]) == 2
    assert "not" in capsys.readouterr().err


def test_mode_exclusivity():
    with pytest.raises(SystemExit):
        F.main(["--validate-hooks", "--compare", "x"])
    with pytest.raises(SystemExit):
        F.main(["--against", "x", "--validate-hooks"])


# ----------------------------------------------------------------------------------------------- review fixes (independent review of #2945)
def nonint_state():
    """base_state with an occupied argala cell holding a NON-INTEGRAL score (the a29 failure shape: a number that can become NULL)."""
    return mutate(base_state(), lambda s: [r.__setitem__(5, "1.5") for r in s["chart_facts"] if r[1] == "argala_natal_matrix"])


def set_argala(s, num="", text=""):
    for r in s["chart_facts"]:
        if r[1] == "argala_natal_matrix":
            r[4], r[5] = text, num


# --- MED-1: a continuous value judged by its snapshot side only was invisible when it became NULL / text / vanished
def test_med1_continuous_number_becoming_null_is_a_value_change():
    rep = run(nonint_state(), mutate(nonint_state(), lambda s: set_argala(s, "", "")), [])
    assert counts(rep) == {"UNDECLARED_CHANGE": 5} and rep["verdict"] == "FAIL"
    assert {c["change"] for c in rep["changes"]} == {"value"} and rep["changes"][0]["before"] == ["", "1.5"] and rep["changes"][0]["after"] == ["", ""]
    cont = rep["continuous"]["chart_facts"]
    assert cont["to_non_numeric"] == 5 and cont["changed"] == 5


def test_med1_continuous_number_becoming_text_is_a_value_change(tmp_path):
    rep = run(nonint_state(), mutate(nonint_state(), lambda s: set_argala(s, "", "no_data")), [])
    assert counts(rep) == {"UNDECLARED_CHANGE": 5}
    declared = run(nonint_state(), mutate(nonint_state(), lambda s: set_argala(s, "", "no_data")), loaded(tmp_path, ARGALA), standing_not_checked=NO_STANDING)
    assert declared["verdict"] == "PASS" and all(c["lanes"] == ["argala"] for c in declared["changes"])
    wrong_kind = hook("argala", [entry(["argala_natal_matrix"], ["appeared"])])
    kind = run(nonint_state(), mutate(nonint_state(), lambda s: set_argala(s, "", "no_data")), loaded(tmp_path, wrong_kind))
    assert kind["failure_counts"]["KIND_MISMATCH"] == 5


def test_med1_continuous_number_to_another_number_is_still_not_a_class_change():
    rep = run(nonint_state(), mutate(nonint_state(), lambda s: set_argala(s, "2.5")), [], standing_not_checked=NO_STANDING)
    assert rep["verdict"] == "PASS" and rep["changes_total"] == 0
    assert rep["continuous"]["chart_facts"]["changed"] == 5 and rep["continuous"]["chart_facts"]["to_non_numeric"] == 0


def test_med1_whole_continuous_category_disappearing_is_five_changes(tmp_path):
    def drop(s):
        s["chart_facts"] = [r for r in s["chart_facts"] if r[1] != "graha_shadbala_total"]
    rep = run(base_state(), mutate(base_state(), drop), [])
    assert counts(rep) == {"UNDECLARED_CHANGE": 5}
    assert {(c["category"], c["fact_key"], c["change"]) for c in rep["changes"]} == {("graha_shadbala_total", "total", "disappeared")}
    assert rep["continuous"]["chart_facts"]["keys_disappeared"] == 5
    assert any("keys appeared 0 disappeared 5" in ln for ln in F.render_summary(rep))
    h = hook("tiers", [entry(["graha_shadbala_total"], ["disappeared"])])
    ok = run(base_state(), mutate(base_state(), drop), loaded(tmp_path, h), standing_not_checked=NO_STANDING)
    assert ok["verdict"] == "PASS" and all(c["lanes"] == ["tiers"] for c in ok["changes"])


def test_med1_continuous_key_appearing_is_a_change_and_can_be_declared_or_missing(tmp_path):
    def drop(s):
        s["chart_facts"] = [r for r in s["chart_facts"] if r[1] != "graha_shadbala_total"]
    rep = run(mutate(base_state(), drop), base_state(), [])
    assert counts(rep) == {"UNDECLARED_CHANGE": 5} and rep["continuous"]["chart_facts"]["keys_appeared"] == 5
    declared_but_nothing = hook("tiers", [entry(["graha_shadbala_total"], ["appeared"])])
    assert counts(run(base_state(), base_state(), loaded(tmp_path, declared_but_nothing))) == {"DECLARED_BUT_ABSENT": 1}
    wrong_kind = hook("tiers", [entry(["graha_shadbala_total"], ["value"])])
    assert run(mutate(base_state(), drop), base_state(), loaded(tmp_path, wrong_kind))["failure_counts"]["KIND_MISMATCH"] == 5


def test_med1_timestamp_keys_appearing_stay_ignored_but_are_counted():
    def add(s):
        s["chart_facts"].append(["INVARIANT", "birth_time_facts", "BIRTH", "utc", "2026-01-01T00:00:00+00:00", "", "single"])
    rep = run(base_state(), mutate(base_state(), add), [], standing_not_checked=NO_STANDING)
    assert rep["changes_total"] == 0 and rep["continuous"]["chart_facts"]["time_keys_appeared"] == 1 and rep["verdict"] == "PASS"


# --- MED-2: empty reads must not pass
EMPTY_KEYS = [("chart_facts", {"chart_facts": []}), ("chart_divisionals", {"divisionals": []}), ("chart_dashas", {"dashas": []}), ("panchanga_daily", {"daily": []})]


@pytest.mark.parametrize("label,blank", EMPTY_KEYS, ids=[k[0] for k in EMPTY_KEYS])
@pytest.mark.parametrize("sides", ["both", "snapshot", "current"])
def test_med2_a_compared_table_with_zero_rows_is_a_failure(label, blank, sides):
    snap, cur = base_state(), base_state()
    if sides in ("both", "snapshot"):
        snap.update(copy.deepcopy(blank))
    if sides in ("both", "current"):
        cur.update(copy.deepcopy(blank))
    rep = run(snap, cur, [], chart=OTHER)
    assert rep["failure_counts"]["EMPTY_READ"] == (2 if sides == "both" else 1)
    assert rep["verdict"] == "FAIL" and F.exit_code(rep) == 2 and F.exit_code(rep, allow_not_checked=True) == 2
    assert all(label in m for m in rep["failures"]["EMPTY_READ"])


def test_med2_everything_empty_on_a_non_native_chart_is_not_clean():
    empty = {"chart_facts": [], "divisionals": [], "dashas": [], "daily": []}
    rep = run(copy.deepcopy(empty), copy.deepcopy(empty), [], chart=OTHER)
    assert rep["changes_total"] == 0 and rep["failure_counts"]["EMPTY_READ"] == 8
    assert F.exit_code(rep, allow_not_checked=True) == 2


def test_med2_tables_not_compared_are_not_required_to_have_rows():
    snap, cur = base_state(), base_state()
    snap["dashas"], cur["dashas"], snap["daily"], cur["daily"] = [], [], [], []
    rep = run(snap, cur, [], chart=OTHER, have_dash=False, have_daily=False, standing_not_checked=NO_STANDING)
    assert counts(rep) == {}  # no EMPTY_READ for tables that were not compared; but they are NOT CHECKED, never a pass
    assert rep["verdict"] == "NOT_CHECKED" and [n["id"] for n in rep["not_checked"]] == ["chart_dashas.not_compared", "panchanga_daily.not_compared"]


def test_med2_cli_empty_snapshots_exit_2_even_with_allow_not_checked(tmp_path, capsys):
    d = write_hooks(tmp_path, ARGALA_OPT)
    empty = {"chart_facts": [], "divisionals": [], "dashas": [], "daily": []}
    a, b = snapshot_file(tmp_path, "a.json.gz", empty, chart=OTHER), snapshot_file(tmp_path, "b.json.gz", empty, chart=OTHER)
    out = tmp_path / "r.json"
    code = F.main(["--compare", str(a), "--against", str(b), "--hooks-dir", str(d), "--out", str(out), "--allow-not-checked"])
    text = capsys.readouterr().out
    assert code == 2 and "FAIL EMPTY_READ" in text and json.loads(out.read_text())["verdict"] == "FAIL"


# --- LOW-3 / LOW-4: chart id validation and normalisation
@pytest.mark.parametrize("bad", ["abc", "x'; drop table chart_facts; --", NATIVE + "'", NATIVE[:-1], "", "native; select 1", NATIVE.replace("-", "")])
def test_low3_chart_id_must_be_a_uuid(bad):
    with pytest.raises(ValueError):
        F.resolve(bad)
    with pytest.raises(ValueError):
        F.read_state(bad)  # raises before any SQL is built (the tripwire would raise AssertionError otherwise)
    with pytest.raises(ValueError):
        run(base_state(), base_state(), [], chart=bad)


def test_low3_snapshot_names_and_uuids_resolve():
    assert F.resolve("native") == NATIVE and F.resolve("Native") == NATIVE and F.resolve(OTHER) == OTHER
    assert F.resolve(" {" + NATIVE.upper() + "} ") == NATIVE


def test_low3_cli_refuses_a_bad_snapshot_target(capsys):
    with pytest.raises(SystemExit) as ei:
        F.main(["--snapshot", "x'; drop table t; --"])
    assert ei.value.code == 2


@pytest.mark.parametrize("form", [NATIVE.upper(), "{" + NATIVE + "}", "  " + NATIVE.upper() + " "])
def test_low4_uppercase_or_braced_chart_id_still_gets_the_anchor_check(form):
    def f(s):
        for r in s["chart_facts"]:
            if r[0] == "lahiri_chitrapaksha" and r[1] == "graha_position" and r[2] == "LAGNA":
                r[4] = "Taurus"
    rep = run(base_state(), mutate(base_state(), f), [], chart=form)
    assert rep["verdict"] == "ALERT" and rep["chart_id"] == NATIVE and F.exit_code(rep) == 3


def test_low4_hook_chart_prefix_matches_regardless_of_case(tmp_path):
    h = copy.deepcopy(ARGALA)
    h["charts"] = [NATIVE[:8].upper()]
    hooks = loaded(tmp_path, h)
    rep = run(base_state(), mutate(base_state(), change_argala), hooks, chart=NATIVE.upper(), standing_not_checked=NO_STANDING)
    assert rep["verdict"] == "PASS"


def test_low4_snapshot_with_uppercase_chart_id_in_meta_is_normalised(tmp_path, capsys):
    d = write_hooks(tmp_path, ARGALA_OPT)
    a = snapshot_file(tmp_path, "a.json.gz", base_state(), chart=NATIVE.upper())
    b = snapshot_file(tmp_path, "b.json.gz", base_state(), chart=NATIVE)
    out = tmp_path / "r.json"
    assert F.main(["--compare", str(a), "--against", str(b), "--hooks-dir", str(d), "--out", str(out), "--allow-not-checked"]) == 0
    rep = json.loads(out.read_text())
    assert rep["chart_id"] == NATIVE and "anchors" in rep  # native-only anchor check ran
    capsys.readouterr()


# --- LOW-5: empty lists broaden, so they are rejected
@pytest.mark.parametrize("name,bad", [
    ("empty_fact_keys", hook("empty_fact_keys", [entry(["a"], fact_keys=[])])),
    ("empty_ayanamsha_ids", hook("empty_ayanamsha_ids", [entry(["a"], ayanamsha_ids=[])])),
    ("empty_charts", hook("empty_charts", [entry(["a"])], charts=[])),
    ("blank_fact_key", hook("blank_fact_key", [entry(["a"], fact_keys=[""])])),
    ("non_hex_chart", hook("non_hex_chart", [entry(["a"])], charts=["zzzzzzzz"]))])
def test_low5_empty_lists_are_rejected(tmp_path, name, bad):
    write_hooks(tmp_path, bad)
    hooks, errs = F.load_hooks(str(tmp_path / "hooks"))
    assert errs and not hooks, name
    assert validate(tmp_path) == 2


# --- LOW-6: empty --hooks-dir / --require-lanes must not silently fall back
@pytest.mark.parametrize("args", [["--validate-hooks", "--hooks-dir", ""], ["--validate-hooks", "--hooks-dir", "   "],
                                  ["--validate-hooks", "--hooks-dir", "x", "--require-lanes", ""], ["--compare", "x", "--hooks-dir", ""]])
def test_low6_empty_hooks_dir_or_lanes_is_refused(args):
    with pytest.raises(SystemExit) as ei:
        F.main(args)
    assert ei.value.code == 2


# --- survivors: narrowing fields of an entry
def test_hook_ayanamsha_narrowing_is_honoured(tmp_path):
    raman_only = hook("posn", [entry(["graha_position"], ["value"], ayanamsha_ids=["raman"])])
    rep = run(base_state(), mutate(base_state(), change_mar_pada), loaded(tmp_path, raman_only))  # the pada change is lahiri only
    assert counts(rep) == {"UNDECLARED_CHANGE": 1, "DECLARED_BUT_ABSENT": 1}
    assert rep["failures"]["UNDECLARED_CHANGE"][0]["ayanamsha"] == "lahiri_chitrapaksha"
    lahiri = hook("posn", [entry(["graha_position"], ["value"], ayanamsha_ids=["lahiri_chitrapaksha"])])
    ok = run(base_state(), mutate(base_state(), change_mar_pada), loaded(tmp_path, lahiri), standing_not_checked=NO_STANDING)
    assert ok["verdict"] == "PASS"


def test_hook_fact_key_narrowing_is_honoured(tmp_path):
    sign_only = hook("posn", [entry(["graha_position"], ["value"], fact_keys=["sign"])])
    rep = run(base_state(), mutate(base_state(), change_mar_pada), loaded(tmp_path, sign_only))  # the change is key 'pada'
    assert counts(rep) == {"UNDECLARED_CHANGE": 1, "DECLARED_BUT_ABSENT": 1}
    pada = hook("posn", [entry(["graha_position"], ["value"], fact_keys=["pada"])])
    assert run(base_state(), mutate(base_state(), change_mar_pada), loaded(tmp_path, pada), standing_not_checked=NO_STANDING)["verdict"] == "PASS"


# --- a malformed or tampered report is never PASS and never a crash
@pytest.mark.parametrize("rep", [{}, None, {"verdict": "PASS"}, {"verdict": "PASS", "failure_counts": {}, "not_checked": [], "chart_id": "x"},
                                 {"verdict": "PASS", "failures": [], "failure_counts": {}, "not_checked": [], "chart_id": "x"},
                                 {"verdict": "PASS", "failures": {}, "failure_counts": {}, "not_checked": None, "chart_id": "x"},
                                 {"verdict": "PASS", "failures": {}, "failure_counts": {}, "not_checked": "", "chart_id": "x"},
                                 {"verdict": "PASS", "failures": {}, "failure_counts": {}, "not_checked": {}, "chart_id": "x"},
                                 {"verdict": "PASS", "failures": {}, "failure_counts": [], "not_checked": [], "chart_id": "x"}])
def test_malformed_report_is_a_clean_failure_not_a_keyerror(rep):
    assert F.decide_verdict(rep) == "FAIL"
    assert F.exit_code(rep) == 2 and F.exit_code(rep, allow_not_checked=True) == 2
    assert F.render_summary(rep)[0].startswith("VERDICT: FAIL") and "MALFORMED REPORT" in F.render_summary(rep)[0]


def test_saved_report_json_verdict_field_is_not_trusted(tmp_path):
    rep = run(base_state(), mutate(base_state(), change_mar_pada), [])
    saved = json.loads(json.dumps(rep))
    saved["verdict"] = "PASS"
    del saved["failures"]  # a hand-edited / truncated saved report
    assert F.exit_code(saved, allow_not_checked=True) == 2


# --- F1 (delta review): a timestamp-valued fact that loses its timestamp
def time_state():
    return mutate(base_state(), lambda s: s["chart_facts"].append(["INVARIANT", "birth_time_facts", "BIRTH", "utc", "2026-01-01T00:00:00+00:00", "", "single"]))


@pytest.mark.parametrize("after", [("", ""), ("no_data", ""), ("", "7")], ids=["null", "text", "number"])
def test_f1_timestamp_becoming_null_or_text_is_a_value_change(after, tmp_path):
    def lose(s):
        for r in s["chart_facts"]:
            if r[1] == "birth_time_facts":
                r[4], r[5] = after
    rep = run(time_state(), mutate(time_state(), lose), [])
    assert counts(rep) == {"UNDECLARED_CHANGE": 1} and rep["changes"][0]["change"] == "value"
    assert rep["continuous"]["chart_facts"]["time_to_non_time"] == 1
    h = hook("birth", [entry(["birth_time_facts"], ["value"])])
    assert run(time_state(), mutate(time_state(), lose), loaded(tmp_path, h), standing_not_checked=NO_STANDING)["verdict"] == "PASS"


def test_f1_timestamp_to_another_timestamp_is_still_ignored():
    def move(s):
        for r in s["chart_facts"]:
            if r[1] == "birth_time_facts":
                r[4] = "2026-02-02T00:00:00+00:00"
    rep = run(time_state(), mutate(time_state(), move), [], standing_not_checked=NO_STANDING)
    assert rep["verdict"] == "PASS" and rep["changes_total"] == 0 and rep["continuous"]["chart_facts"]["time_to_non_time"] == 0


# --- direction limit and the sun_required_rupa note
def test_direction_limit_integral_to_continuous_is_seen_but_continuous_to_integral_is_not():
    def val(v):
        return mutate(base_state(), lambda s: s["chart_facts"].append(["INVARIANT", "graha_shadbala_total", "SUN", "required_rupa", "", v, "single"]))
    forward = run(val("5"), val("6.5"), [], standing_not_checked=NO_STANDING)
    assert counts(forward) == {"UNDECLARED_CHANGE": 1} and forward["changes"][0]["fact_key"] == "required_rupa"
    reverse = run(val("6.5"), val("5"), [], standing_not_checked=NO_STANDING)  # the snapshot side is continuous: invisible, documented in the README
    assert reverse["changes_total"] == 0 and reverse["continuous"]["chart_facts"]["changed"] == 1
    assert "Direction limit" in (GOV_DIR / "FLIP_DETECTOR_README.md").read_text()


# =============================================================================================== second independent review (R-T2) + SS rulings
FAKE_PSQL = r"""#!__PY__
import sys, os, json, re, time
args = sys.argv[1:]
script = sys.stdin.read() if "-f" in args else (args[args.index("-c") + 1] if "-c" in args else args[0])
d = os.environ["FAKE_DIR"]
with open(d + "/calls.log", "a") as lg:
    lg.write(json.dumps({"pgoptions": os.environ.get("PGOPTIONS", ""), "script": script}) + chr(10))
mode = os.environ.get("FAKE_MODE", "")
if mode == "fail":
    sys.stderr.write(os.environ.get("FAKE_STDERR", "boom")); sys.exit(2)
if mode == "sleep":
    time.sleep(5)
st = json.load(open(d + "/state.json"))["charts"]
stmts = [x.strip() for x in script.split(";" + chr(10)) if x.strip()]
out = []
def rows_for(table, sql):
    m = re.search(r"chart_id='([^']*)'", sql)
    ids = [m.group(1)] if (m and os.environ.get("FAKE_NOFILTER") != "1") else list(st)
    res = []
    for cid in ids:
        c = st.get(cid, {})
        if table == "chart_facts": res += c.get("chart_facts", [])
        elif table == "chart_divisionals": res += c.get("divisionals", [])
        elif table == "chart_dashas":
            res += [[r[0], r[1], r[2], r[3].split("/")[-1], "", "", "", r[4], r[5], "id%d" % i, ""] for i, r in enumerate(c.get("dashas", []))]
        elif table == "panchanga_daily": res += c.get("daily", [])
    return res
for sql in stmts:
    flat = re.sub(r"\s+", " ", sql)
    if flat.upper().startswith("BEGIN") or flat.upper() == "COMMIT":
        continue
    m = re.match(r"^select '(@@END:[a-z_]+@@)'$", flat)
    if m:
        out.append([[m.group(1)]]); continue
    if "current_setting('transaction_read_only')" in flat:
        on = "default_transaction_read_only=on" in os.environ.get("PGOPTIONS", "") and mode != "rw"
        out.append([["on" if on else "off"]]); continue
    if flat.startswith("select current_user"):
        out.append([["fake_reader"]]); continue
    tbl = re.search(r"from (chart_facts|chart_divisionals|chart_dashas|panchanga_daily)", flat).group(1)
    r = rows_for(tbl, flat)
    if mode == "tabbed" and tbl == "chart_facts" and r:
        r = [list(r[0]) + ["extra"]] + r[1:]
    out.append(r)
if mode == "last_only":
    out = out[-1:]
tags = mode == "tags" or "-q" not in args
if tags:
    print("BEGIN")
for rs in out:
    for r in rs:
        print("\t".join(str(x) for x in r))
if tags:
    print("COMMIT")
"""


def fake_db(tmp_path, monkeypatch, charts=None, mode="", env=None):
    """A fake psql on PATH (no database): serves per-chart rows, records every call. Returns the call-log reader."""
    d = tmp_path / "fakedb"
    d.mkdir(exist_ok=True)
    bindir = d / "bin"
    bindir.mkdir(exist_ok=True)
    stub = bindir / "psql"
    stub.write_text(FAKE_PSQL.replace("__PY__", sys.executable))
    stub.chmod(0o755)
    (d / "state.json").write_text(json.dumps({"charts": charts if charts is not None else {NATIVE: base_state()}}))
    monkeypatch.setattr(F, "q", ORIG_Q)
    monkeypatch.setattr(F.time, "sleep", lambda *_: None)
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.delenv("FLIP_READER", raising=False)
    monkeypatch.setenv("FAKE_DIR", str(d))
    monkeypatch.setenv("FAKE_MODE", mode)
    for k, v in (env or {}).items():
        monkeypatch.setenv(k, v)

    def calls():
        p = d / "calls.log"
        return [json.loads(ln) for ln in p.read_text().splitlines()] if p.exists() else []
    return calls


# --- F7 / F8 / F18: one repeatable-read read-only transaction, read-only session proven, timeout, defined exit
def test_f7_read_state_is_one_repeatable_read_read_only_transaction(tmp_path, monkeypatch):
    calls = fake_db(tmp_path, monkeypatch)
    st = F.read_state(NATIVE)
    assert st["chart_facts"] == base_state()["chart_facts"] and st["dashas"] == base_state()["dashas"] and st["daily"] == base_state()["daily"]
    c = calls()
    assert len(c) == 1, "all tables must be read in ONE psql session"
    stmts = [x.strip() for x in c[0]["script"].split(";\n") if x.strip()]
    assert stmts[0] == "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY" and stmts[-1] == "COMMIT"
    inner = [re.sub(r"\s+", " ", x) for x in stmts[1:-1]]
    assert inner and all(x.lower().startswith("select") for x in inner)
    assert sum(1 for x in inner if "from chart_facts" in x) == 1 and sum(1 for x in inner if "from chart_dashas" in x) == 1
    assert "default_transaction_read_only=on" in c[0]["pgoptions"]


def test_f8_operator_pgoptions_are_kept_and_read_only_is_added(tmp_path, monkeypatch):
    calls = fake_db(tmp_path, monkeypatch, env={"PGOPTIONS": "-c statement_timeout=5000"})
    F.read_state(NATIVE)
    assert calls()[0]["pgoptions"] == "-c statement_timeout=5000 -c default_transaction_read_only=on"


def test_f8_a_session_that_is_not_read_only_reads_nothing(tmp_path, monkeypatch):
    fake_db(tmp_path, monkeypatch, mode="rw")
    with pytest.raises(F.ReadError, match="not read-only"):
        F.read_state(NATIVE)


def test_f7_timeout_and_persistent_failure_have_a_defined_exit_and_a_report(tmp_path, monkeypatch, capsys):
    snap = snapshot_file(tmp_path, "s.json.gz", base_state())
    d = write_hooks(tmp_path, ARGALA_OPT)
    fake_db(tmp_path, monkeypatch, mode="sleep", env={"FLIP_TIMEOUT_SEC": "0.3"})
    out = tmp_path / "r.json"
    code = F.main(["--compare", str(snap), "--hooks-dir", str(d), "--out", str(out), "--allow-not-checked"])
    assert code == 5 and F.EXIT_READ_ERROR == 5
    rep = json.loads(out.read_text())
    assert rep["verdict"] == "READ_ERROR" and rep["exit_code"] == 5 and "timed out" in rep["error"]
    assert "READ_ERROR" in capsys.readouterr().out


def test_f7_error_text_is_cut_to_200_chars_and_never_shows_a_dsn_or_password(tmp_path, monkeypatch, capsys):
    pw = "Sup3r" + "SecretPw"  # assembled at run time: the repo's secret scan must not see a literal DSN or password in this file
    secret = ('psql: error: connection to "' + "post" + "gres://suvarna_reader:" + pw + '@db.example:5432/x" failed: ' + "pass" + "word=" + pw + " " + "x" * 400)
    fake_db(tmp_path, monkeypatch, mode="fail", env={"FAKE_STDERR": secret})
    with pytest.raises(F.ReadError) as ei:
        F.read_state(NATIVE)
    msg = str(ei.value)
    assert pw not in msg and "suvarna_reader" not in msg
    assert len(msg.split(": ", 1)[1]) <= 200 + len("read failed after 4 attempts: ")
    assert F.main(["--snapshot", "native", "--out", str(tmp_path / "x.json.gz")]) == 5
    assert pw not in capsys.readouterr().err


def test_f7_a_reader_that_prints_only_the_last_result_set_is_an_incomplete_read(tmp_path, monkeypatch):
    fake_db(tmp_path, monkeypatch, mode="last_only")
    with pytest.raises(F.ReadError, match="incomplete read"):
        F.read_state(NATIVE)


def test_f18_a_row_with_the_wrong_column_count_is_a_read_error(tmp_path, monkeypatch):
    fake_db(tmp_path, monkeypatch, mode="tabbed")
    with pytest.raises(F.ReadError, match="columns"):
        F.read_state(NATIVE)


def test_f4_read_state_filters_by_chart_and_reads_only_that_chart(tmp_path, monkeypatch):
    other = mutate(base_state(), lambda s: s["chart_facts"].append(["lahiri_chitrapaksha", "graha_position", "KETU", "pada", "", "4", "single"]))
    fake_db(tmp_path, monkeypatch, charts={NATIVE: base_state(), OTHER: other})
    assert F.read_state(NATIVE)["chart_facts"] == base_state()["chart_facts"]
    assert F.read_state(OTHER)["chart_facts"] == other["chart_facts"]
    assert len(F.read_state(NATIVE, dashas=False, daily=False)) == 2  # only facts + divisionals when the others are skipped


def test_f4_read_state_with_no_dashas_sends_no_dasha_statement(tmp_path, monkeypatch):
    calls = fake_db(tmp_path, monkeypatch)
    F.read_state(NATIVE, dashas=False, daily=False)
    assert "chart_dashas" not in calls()[0]["script"] and "panchanga_daily" not in calls()[0]["script"]


def test_f8_phantom_chart_id_is_refused_whatever_the_shape(tmp_path):
    for bad in ("362f9f17-0000-0000-0000-000000000000", "362F9F17-aaaa-bbbb-cccc-dddddddddddd", "{362f9f17-1111-2222-3333-444444444444}", "362f9f17", "362f9f170000000000000000000000"):
        with pytest.raises(ValueError, match="phantom"):
            F.normalize_chart_id(bad)
        with pytest.raises(ValueError):
            F.read_state(bad)
        with pytest.raises(ValueError):
            F.resolve(bad)
    snap = snapshot_file(tmp_path, "p.json.gz", base_state(), chart="362f9f17-1111-2222-3333-444444444444")
    assert F.main(["--compare", str(snap), "--against", str(snap), "--hooks-dir", str(write_hooks(tmp_path, ARGALA_OPT)), "--out", str(tmp_path / "o.json")]) == 2
    bad_hook = hook("phantom", [entry(["a"])], charts=["362f9f17"])
    write_hooks(tmp_path, bad_hook, name="ph")
    assert F.load_hooks(str(tmp_path / "ph"))[1]


def test_f15_snapshot_meta_carries_the_tool_version(tmp_path, monkeypatch, capsys):
    fake_db(tmp_path, monkeypatch)
    out = tmp_path / "snap.json.gz"
    assert F.main(["--snapshot", "native", "--out", str(out)]) == 0
    capsys.readouterr()
    meta = json.load(gzip.open(out, "rt"))["meta"]
    assert meta["tool_version"] == F.TOOL_VERSION and meta["single_transaction"] == "REPEATABLE READ READ ONLY" and meta["db_user"] == "fake_reader"


# --- F6: never overwrite a baseline; verify the sidecar on compare
def test_f6_snapshot_never_overwrites_a_baseline(tmp_path, monkeypatch, capsys):
    fake_db(tmp_path, monkeypatch)
    out = tmp_path / "base.json.gz"
    assert F.main(["--snapshot", "native", "--out", str(out)]) == 0
    first = out.read_bytes()
    first_sha = (tmp_path / "base.json.gz.sha256").read_text()
    changed = mutate(base_state(), change_argala)
    (tmp_path / "fakedb" / "state.json").write_text(json.dumps({"charts": {NATIVE: changed}}))
    assert F.main(["--snapshot", "native", "--out", str(out)]) == 6 and F.EXIT_REFUSED == 6
    assert out.read_bytes() == first and (tmp_path / "base.json.gz.sha256").read_text() == first_sha
    assert "never overwritten" in capsys.readouterr().err
    out.with_name("base.json.gz.sha256").unlink()
    assert F.main(["--snapshot", "native", "--out", str(out)]) == 6  # the file alone is enough to refuse


def test_f6_compare_verifies_the_sha256_sidecar(tmp_path, capsys):
    d = write_hooks(tmp_path, ARGALA_OPT)
    good = snapshot_file(tmp_path, "g.json.gz", base_state())
    other = snapshot_file(tmp_path, "o.json.gz", base_state())
    out = tmp_path / "r.json"
    assert F.main(["--compare", str(good), "--against", str(other), "--hooks-dir", str(d), "--out", str(out), "--allow-not-checked"]) == 0
    assert json.loads(out.read_text())["meta"]["snapshot_sha256"] == {"snapshot": "ok", "against": "ok"}
    # alter the baseline (a different valid snapshot under the same name, keeping the sidecar written for the original): the digest no longer matches
    tampered = snapshot_file(tmp_path, "t.json.gz", mutate(base_state(), change_argala), sha=False)
    (tmp_path / "t.json.gz.sha256").write_text((tmp_path / "g.json.gz.sha256").read_text().replace("g.json.gz", "t.json.gz"))
    code = F.main(["--compare", str(tampered), "--against", str(other), "--hooks-dir", str(d), "--out", str(out), "--allow-not-checked"])
    rep = json.loads(out.read_text())
    assert code == 2 and rep["verdict"] == "FAIL" and any("SNAPSHOT INTEGRITY" in m for m in rep["failures"]["HOOK_ERROR"])


def test_f6_a_snapshot_without_a_sidecar_is_not_checked_not_verified(tmp_path, capsys):
    d = write_hooks(tmp_path, ARGALA_OPT)
    a = snapshot_file(tmp_path, "a.json.gz", base_state(), sha=False)
    b = snapshot_file(tmp_path, "b.json.gz", base_state())
    out = tmp_path / "r.json"
    assert F.main(["--compare", str(a), "--against", str(b), "--hooks-dir", str(d), "--out", str(out)]) == 4
    rep = json.loads(out.read_text())
    assert "snapshot.sha256" in [n["id"] for n in rep["not_checked"]] and rep["meta"]["snapshot_sha256"]["snapshot"] == "absent"
    assert "NOT CHECKED snapshot.sha256" in capsys.readouterr().out


# --- F1 (MED): a check that did not run prints NOT CHECKED, never a green ok
def dasha_changed_pair():
    return base_state(), mutate(base_state(), shift_vimshottari)


def test_f1_no_dashas_makes_a_real_dasha_change_not_checked_and_never_green(tmp_path):
    snap, cur = dasha_changed_pair()
    rep = run(snap, cur, [], have_dash=False, standing_not_checked=NO_STANDING)
    assert rep["verdict"] == "NOT_CHECKED" and rep["changes_total"] == 0 and F.exit_code(rep) == 4
    row = [n for n in rep["not_checked"] if n["id"] == "chart_dashas.not_compared"]
    assert len(row) == 1 and "NOT CHECKED" == row[0]["status"]
    lines = F.render_summary(rep)
    assert not any(ln.startswith("ok   DASHA_SHIFT_UNDECLARED") for ln in lines)
    assert any(ln.startswith("n/a  DASHA_SHIFT_UNDECLARED: NOT EVALUATED") for ln in lines)
    assert any(ln.startswith("NOT CHECKED chart_dashas.not_compared") for ln in lines)
    assert rep["compared"] == {"chart_facts": True, "chart_divisionals": True, "chart_dashas": False, "panchanga_daily": True}
    # the same pair, compared, is a failure: the skip really hid it
    assert run(snap, cur, [], standing_not_checked=NO_STANDING)["verdict"] == "FAIL"
    full = F.render_summary(run(base_state(), base_state(), [], standing_not_checked=NO_STANDING))
    assert any(ln.startswith("ok   DASHA_SHIFT_UNDECLARED: 0") for ln in full)


def test_f1_no_daily_makes_a_real_panchanga_change_not_checked(tmp_path):
    cur = mutate(base_state(), lambda s: s["daily"][0].__setitem__(9, "Shashthi"))
    rep = run(base_state(), cur, [], have_daily=False, standing_not_checked=NO_STANDING)
    assert rep["verdict"] == "NOT_CHECKED" and rep["changes_total"] == 0
    assert [n["id"] for n in rep["not_checked"]] == ["panchanga_daily.not_compared"]
    assert any(ln.startswith("n/a  panchanga_daily: NOT COMPARED") for ln in F.render_summary(rep))
    assert run(base_state(), cur, [], standing_not_checked=NO_STANDING)["verdict"] == "FAIL"


def test_f1_cli_records_flags_and_skipped_sections_in_meta(tmp_path, capsys):
    d = write_hooks(tmp_path, ARGALA_OPT)
    snap = snapshot_file(tmp_path, "s.json.gz", base_state())
    cur = snapshot_file(tmp_path, "c.json.gz", mutate(base_state(), shift_vimshottari))
    out = tmp_path / "r.json"
    assert F.main(["--compare", str(snap), "--against", str(cur), "--hooks-dir", str(d), "--out", str(out), "--no-dashas", "--allow-not-checked"]) == 0
    meta = json.loads(out.read_text())["meta"]
    assert meta["flags"]["no_dashas"] is True and meta["flags"]["no_daily"] is False and meta["skipped_sections"] == ["chart_dashas"]
    assert "--no-dashas" in [n for n in json.loads(out.read_text())["not_checked"] if n["id"] == "chart_dashas.not_compared"][0]["reason"]
    # without the flag the same files fail on the dasha shift: the saved evidence of the two runs can be told apart
    out2 = tmp_path / "r2.json"
    assert F.main(["--compare", str(snap), "--against", str(cur), "--hooks-dir", str(d), "--out", str(out2), "--allow-not-checked"]) == 2
    meta2 = json.loads(out2.read_text())["meta"]
    assert meta2["flags"]["no_dashas"] is False and meta2["skipped_sections"] == []
    capsys.readouterr()


@pytest.mark.parametrize("missing,which", [("dashas", "snapshot"), ("dashas", "against"), ("daily", "snapshot"), ("daily", "against")])
def test_f1_a_section_missing_from_a_snapshot_is_not_checked(tmp_path, capsys, missing, which):
    d = write_hooks(tmp_path, ARGALA_OPT)
    full = base_state()
    lacking = {k: v for k, v in base_state().items() if k != missing}
    a = snapshot_file(tmp_path, "a.json.gz", lacking if which == "snapshot" else full)
    b = snapshot_file(tmp_path, "b.json.gz", lacking if which == "against" else full)
    out = tmp_path / "r.json"
    assert F.main(["--compare", str(a), "--against", str(b), "--hooks-dir", str(d), "--out", str(out), "--allow-not-checked"]) == 0
    rep = json.loads(out.read_text())
    table = "chart_dashas" if missing == "dashas" else "panchanga_daily"
    row = [n for n in rep["not_checked"] if n["id"] == f"{table}.not_compared"]
    assert row and "lacks the section" in row[0]["reason"] and rep["meta"]["skipped_sections"] == [table]
    capsys.readouterr()


def test_f4_against_with_both_sections_compares_dashas(tmp_path, capsys):
    """M20: --against must not switch the dasha comparison off by itself."""
    d = write_hooks(tmp_path, ARGALA_OPT)
    a = snapshot_file(tmp_path, "a.json.gz", base_state())
    b = snapshot_file(tmp_path, "b.json.gz", mutate(base_state(), shift_vimshottari))
    out = tmp_path / "r.json"
    assert F.main(["--compare", str(a), "--against", str(b), "--hooks-dir", str(d), "--out", str(out)]) == 2
    rep = json.loads(out.read_text())
    assert rep["compared"]["chart_dashas"] is True and rep["failure_counts"]["DASHA_SHIFT_UNDECLARED"] == 1
    capsys.readouterr()


# --- SS ruling: the window must not skip dashas by habit
def window_files(tmp_path):
    d = write_hooks(tmp_path, ARGALA_OPT)
    return d, snapshot_file(tmp_path, "s.json.gz", base_state()), snapshot_file(tmp_path, "c.json.gz", base_state())


@pytest.mark.parametrize("skip", ["--no-dashas", "--no-daily"])
def test_ss_skipping_with_require_lanes_is_refused_unless_acknowledged(tmp_path, capsys, skip):
    d, a, b = window_files(tmp_path)
    out = tmp_path / "r.json"
    base = ["--compare", str(a), "--against", str(b), "--hooks-dir", str(d), "--out", str(out), "--allow-not-checked"]
    assert F.main(base + [skip, "--require-lanes", "argala"]) == 6
    assert not out.exists() and "REFUSED" in capsys.readouterr().err
    assert F.main(base + [skip, "--require-lanes", "argala", "--i-know-dashas-are-not-compared"]) == 0
    rep = json.loads(out.read_text())
    assert rep["meta"]["flags"]["i_know_dashas_are_not_compared"] is True and rep["meta"]["skipped_sections"]
    out.unlink()
    assert F.main(base + [skip]) == 0 and out.exists()                             # a skip without --require-lanes is not the S-L1 window
    out.unlink()
    assert F.main(base + ["--require-lanes", "argala"]) == 0                       # require-lanes without a skip is the window: allowed
    assert F.main(base + ["--require-lanes", "argala", "--no-dashas", "--no-daily"]) == 6   # both flags, still refused
    capsys.readouterr()


def test_ss_the_acknowledgement_flag_alone_changes_nothing(tmp_path, capsys):
    d, a, b = window_files(tmp_path)
    out = tmp_path / "r.json"
    assert F.main(["--compare", str(a), "--against", str(b), "--hooks-dir", str(d), "--out", str(out), "--i-know-dashas-are-not-compared", "--allow-not-checked"]) == 0
    assert json.loads(out.read_text())["compared"]["chart_dashas"] is True
    capsys.readouterr()


# --- F3 / F16: validator
@pytest.mark.parametrize("name,bad", [
    ("shift_count", hook("shift_count", [{"table": "chart_dashas", "kind": "dasha_shift", "systems": ["vimshottari"], "shift_range_sec": [1, 5], "expected_count": {"exact": 100}}])),
    ("shift_count_min0", hook("shift_count_min0", [{"table": "chart_dashas", "kind": "dasha_shift", "systems": ["vimshottari"], "shift_range_sec": [1, 5], "expected_count": {"min": 0}}])),
    ("exact_true", hook("exact_true", [entry(["a"], expected_count={"exact": True})])),
    ("min_gt_max", hook("min_gt_max", [entry(["a"], expected_count={"min": 5, "max": 2})])),
    ("max_false", hook("max_false", [entry(["a"], expected_count={"max": False})]))])
def test_f3_f16_expected_count_misuse_is_rejected(tmp_path, name, bad):
    write_hooks(tmp_path, bad)
    hooks, errs = F.load_hooks(str(tmp_path / "hooks"))
    assert errs and not hooks and any("expected_count" in e for e in errs), name


def test_f16_valid_expected_counts_still_pass(tmp_path):
    write_hooks(tmp_path, hook("ok", [entry(["a"], expected_count={"exact": 0}), entry(["b"], expected_count={"min": 2, "max": 2}), entry(["c"], expected_count={"min": 1})]))
    assert F.load_hooks(str(tmp_path / "hooks"))[1] == []


# --- F9: row order from the database must not matter, including the tier
def test_f9_equal_rows_differing_only_in_tier_pair_in_a_fixed_order():
    def two(order):
        return mutate(base_state(), lambda s: s["chart_facts"].extend(
            [["lahiri_chitrapaksha", "esoteric_point_yogi", "YOGI", "name", "Pushya", "", t] for t in order]))
    rep = run(two(["single", "classical_match"]), two(["classical_match", "single"]), [], standing_not_checked=NO_STANDING)
    assert rep["changes_total"] == 0 and rep["verdict"] == "PASS"
    assert run(two(["single", "single"]), two(["single", "classical_match"]), [])["failure_counts"]["UNDECLARED_CHANGE"] == 1


# --- F5: only a FULL ISO timestamp is a timestamp
@pytest.mark.parametrize("text,kind", [("2026-01-01T00:00:00+00:00", "time"), ("2026-01-01 00:00:00+00", "time"), ("2026-01-01T00:00:00Z", "time"), ("2026-01-01T00:00", "time"),
                                       ("2026-01-01T00:00:00.123456+05:30", "time"), ("2026-01-01T00:00 is the muhurta", "class_text"),
                                       ("2026-01-01T00:00:00+00:00 until dusk", "class_text"), ("2026-01-01", "class_text"), ("Shukla Tritiya", "class_text")])
def test_f5_kind_of_requires_a_full_iso_timestamp(text, kind):
    assert F.kind_of(text, "", "k") == kind


def test_f5_a_text_fact_that_starts_like_a_timestamp_is_a_class_change():
    def with_text(t):
        return mutate(base_state(), lambda s: s["chart_facts"].append(["INVARIANT", "muhurta_label", "M", "note", t, "", "single"]))
    rep = run(with_text("2026-01-01T00:00 auspicious"), with_text("2026-01-01T00:00 inauspicious"), [])
    assert rep["failure_counts"]["UNDECLARED_CHANGE"] == 1


# --- F4: M10 / M15 / M18
def test_f4_an_anchor_row_missing_from_the_current_state_is_an_alert():
    cur = mutate(base_state(), lambda s: s.__setitem__("chart_facts", [r for r in s["chart_facts"] if not (r[1] == "graha_position" and r[2] == "SUN" and r[0] == "raman")]))
    rep = run(base_state(), cur, [])
    assert rep["verdict"] == "ALERT" and F.exit_code(rep, allow_not_checked=True) == 3
    assert any(not a["ok"] and a["ayanamsha"] == "raman" and a["values"] == [] for a in rep["anchors"])


def test_f21_an_empty_current_native_is_an_empty_read_not_an_alert():
    cur = mutate(base_state(), lambda s: s.__setitem__("chart_facts", []))
    rep = run(base_state(), cur, [])
    assert rep["verdict"] == "FAIL" and F.exit_code(rep) == 2 and rep["failure_counts"]["EMPTY_READ"] == 1
    assert rep["ALERT_anchor_changed"] is False and rep["anchors"] == []


def test_f4_dasha_shift_threshold_is_two_seconds():
    for sec, bad in ((0, False), (1, False), (2, False), (3, True), (-3, True), (6993, True)):
        rep = run(base_state(), mutate(base_state(), lambda s: shift_vimshottari(s, sec)), [], standing_not_checked=NO_STANDING)
        assert (rep["failure_counts"]["DASHA_SHIFT_UNDECLARED"] == 1) is bad, sec


def test_f4_the_never_counted_as_passing_line_is_printed():
    rep = run(base_state(), base_state(), [])
    assert "NOT CHECKED items are never counted as passing" in F.render_summary(rep)
    assert "NOT CHECKED items are never counted as passing; exit 0 only because --allow-not-checked was passed" in F.render_summary(rep, True)
    clean = run(base_state(), base_state(), [], standing_not_checked=NO_STANDING)
    assert not any("never counted as passing" in ln for ln in F.render_summary(clean))


# --- F10: the standing registry
def test_f10_standing_registry_names_every_known_unobserved_scope():
    ids = [n["id"] for n in F.STANDING_NOT_CHECKED]
    for want in ("chart_dashas.tier", "l1_tajik_varsha_year_lords.tier", "chart_vichara", "ga_yoga_firings.strength", "bodha_msr_signals", "bodha_rm_resonances",
                 "ga_condition_composite", "ga_medical", "ga_vastu_*", "ga_prashna_*", "prashna_charts"):
        assert want in ids
    assert len(ids) == len(set(ids))
    assert all(n["readback"] and n["reason"] and n["what"] for n in F.STANDING_NOT_CHECKED)
    vich = [n for n in F.STANDING_NOT_CHECKED if n["id"] == "chart_vichara"][0]
    assert "PR 2970" in vich["readback"]  # the SQL file exists only on that branch until the integration brings it
    assert "compares dasha row sets" not in [n for n in F.STANDING_NOT_CHECKED if n["id"] == "chart_dashas.tier"][0]["reason"]


# --- F12 (SS ruling): hooks_real are BYTE COPIES of the integration's hook directory, checked live
def hook_dir_differences(src, fixtures, pending=()):
    """[] when the two directories hold the same top-level *.json hook files byte for byte, except that the names in `pending` may be ABSENT from `src`
    (a lane PR that has not landed yet). A pending file that IS present in `src` must still be byte-equal and present in the fixtures: pending never hides drift."""
    a = {f.name: f.read_bytes() for f in pathlib.Path(src).glob("*.json")}
    b = {f.name: f.read_bytes() for f in pathlib.Path(fixtures).glob("*.json")}
    diff = [f"only in the real hook directory: {n}" for n in sorted(set(a) - set(b))]
    diff += [f"only in hooks_real fixtures: {n}" for n in sorted(set(b) - set(a)) if n not in pending]
    diff += [f"bytes differ: {n}" for n in sorted(set(a) & set(b)) if a[n] != b[n]]
    return diff


def test_f12_the_comparison_helper_detects_missing_extra_and_changed_files(tmp_path):
    src, fx = tmp_path / "src", tmp_path / "fx"
    src.mkdir(), fx.mkdir()
    (src / "a.json").write_text("1"), (fx / "a.json").write_text("1")
    assert hook_dir_differences(src, fx) == []
    (src / "b.json").write_text("2")
    assert hook_dir_differences(src, fx) == ["only in the real hook directory: b.json"]
    (fx / "b.json").write_text("3"), (fx / "c.json").write_text("4")
    assert hook_dir_differences(src, fx) == ["only in hooks_real fixtures: c.json", "bytes differ: b.json"]
    (src / "evidence").mkdir(), (src / "evidence" / "x.json").write_text("n")  # sub-folders are never hooks
    assert hook_dir_differences(src, fx) == ["only in hooks_real fixtures: c.json", "bytes differ: b.json"]


def test_f12_pending_files_may_be_absent_but_never_hide_drift(tmp_path):
    src, fx = tmp_path / "src", tmp_path / "fx"
    src.mkdir(), fx.mkdir()
    (src / "a.json").write_text("1"), (fx / "a.json").write_text("1"), (fx / "p.json").write_text("P")
    assert hook_dir_differences(src, fx, ("p.json",)) == []                                   # pending: absent from the repo directory, carried by hooks_real
    assert hook_dir_differences(src, fx) == ["only in hooks_real fixtures: p.json"]            # the same state without the pending list is drift
    (src / "p.json").write_text("P")
    assert hook_dir_differences(src, fx, ("p.json",)) == []                                    # landed and byte-equal: fine
    (src / "p.json").write_text("P2")
    assert hook_dir_differences(src, fx, ("p.json",)) == ["bytes differ: p.json"]              # landed but different: drift, pending does not excuse it
    (src / "p.json").write_text("P")
    (fx / "p.json").unlink()
    assert hook_dir_differences(src, fx, ("p.json",)) == ["only in the real hook directory: p.json"]   # landed but hooks_real lacks it: drift
    (src / "p.json").unlink()
    (fx / "q.json").write_text("Q")
    assert hook_dir_differences(src, fx, ("p.json",)) == ["only in hooks_real fixtures: q.json"]       # a non-pending extra is drift
    (src / "r.json").write_text("R")
    assert hook_dir_differences(src, fx, ("p.json",)) == ["only in the real hook directory: r.json", "only in hooks_real fixtures: q.json"]


# The 24 stems the integration's hook directory carries today, by name (not a count): a hook added, dropped or renamed is a deliberate edit of this tuple.
INTEGRATION_STEMS = (
    "argala", "argala_other_charts", "ashtakavarga_bindu_contributor", "band_table", "chandra_bala_birth_moon_sign", "dasha_scope_cap", "ephemeris_backend_shift",
    "fa2_ga_vargas", "ga_condition_fallback", "ga_strength_invariant_rows", "ga_structural_chart_geometry", "ga_vargas_invariant_sentinels", "gandanta", "karaka_dasha_roles",
    "karaka_roles", "karaka_web_order", "karaka_web_order_other_charts", "sade_sati_placeholder_null", "special_lagna_offset", "special_lagna_offset_other_charts",
    "sun_required_rupa", "tiers", "tiers_other_charts", "yamakantaka")


def test_f12_the_pending_list_is_short_and_explicit():
    assert PENDING_HOOKS == ()
    assert (REAL_HOOKS / "fa2_ga_vargas.json").exists()
    assert len(INTEGRATION_STEMS) == 24 and len(set(INTEGRATION_STEMS)) == 24 and "fa2_ga_vargas" in INTEGRATION_STEMS
    assert sorted(f.stem for f in REAL_HOOKS.glob("*.json")) == sorted(INTEGRATION_STEMS)   # 24 files = the 24 named stems (fa2_ga_vargas landed)
    assert sorted(INTEGRATION_LANES) == sorted(INTEGRATION_STEMS)


def test_f12_hooks_real_are_byte_copies_of_the_integration_hook_directory():
    """LIVE when the directory exists. FLIP_INTEGRATION_HOOKS_DIR (explicit path) must exist; otherwise the repo's own s_l1_attribution_hooks/ is used.
    Skipped ONLY when that repo directory is not in the tree yet (nothing to compare). Once it exists this never skips, in CI or locally.
    PENDING_HOOKS is empty (fa2_ga_vargas.json landed with PR 2858's hook): every file must be present in both places and byte-equal.
    Refresh procedure: FLIP_DETECTOR_README.md section 'Refreshing hooks_real'."""
    env = os.environ.get("FLIP_INTEGRATION_HOOKS_DIR")
    real = pathlib.Path(env) if env else pathlib.Path(F.DEFAULT_HOOKS_DIR)
    if env:
        assert real.is_dir(), f"FLIP_INTEGRATION_HOOKS_DIR={env} does not exist"
    elif not real.is_dir():
        pytest.skip(f"the integration hook directory is not in this tree yet: {real}; set FLIP_INTEGRATION_HOOKS_DIR to compare against another checkout")
    diffs = hook_dir_differences(real, REAL_HOOKS, PENDING_HOOKS)
    assert not diffs, "hooks_real drifted from the hook directory (refresh per README 'Refreshing hooks_real', then regenerate the golden file):\n" + "\n".join(diffs)


def test_f12_readme_documents_the_refresh_procedure_and_the_copy_shas():
    text = (GOV_DIR / "FLIP_DETECTOR_README.md").read_text()
    assert "Refreshing hooks_real" in text and "FLIP_INTEGRATION_HOOKS_DIR" in text and "FLIP_DETECTOR_REGEN_GOLDEN=1" in text
    assert "c3213fc98" in text and "406437e05eba" in text and "TI-s-l1-integration-001" in text
    assert "fa2_ga_vargas" in text and "PENDING_HOOKS" in text and "2858" in text


def test_ss_the_readme_w7_command_is_complete_and_its_lanes_validate(capsys):
    text = (GOV_DIR / "FLIP_DETECTOR_README.md").read_text()
    block = text.split("### The W7 command (S-L1 window), written in full", 1)[1].split("```", 2)[1]
    assert "--no-dashas" not in block and "--no-daily" not in block
    assert "--hooks-dir 00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks" in block and "--compare" in block
    lanes = re.search(r"--require-lanes (\S+)", block).group(1)
    assert len(lanes.split(",")) == 24 and "fa2_ga_vargas" in lanes.split(",") and "ephemeris_backend_shift" in lanes.split(",") and sorted(lanes.split(",")) == sorted(INTEGRATION_LANES)
    assert F.main(["--validate-hooks", "--hooks-dir", str(REAL_HOOKS), "--require-lanes", lanes]) == 0
    after = text.split("### The W7 command (S-L1 window), written in full", 1)[1]
    assert "24 hook files" in after and "fa2_ga_vargas" in after and "LANDED" in after
    capsys.readouterr()


def test_f7_psql_runs_quiet_and_command_tags_are_never_data(tmp_path, monkeypatch):
    """Found against a real PG15: psql prints BEGIN / COMMIT tags unless -q. The tool passes -q (the fake prints tags without it) and also tolerates a
    wrapper that prints them regardless (mode 'tags')."""
    fake_db(tmp_path, monkeypatch)
    assert F.read_state(NATIVE)["chart_facts"] == base_state()["chart_facts"]  # would raise on a stray BEGIN row if -q were missing
    fake_db(tmp_path, monkeypatch, mode="tags")
    assert F.read_state(NATIVE)["chart_facts"] == base_state()["chart_facts"]


def test_ss_the_readme_states_the_final_dasha_tier_literals():
    text = (GOV_DIR / "FLIP_DETECTOR_README.md").read_text()
    assert "| `mudda` | `classical_match` |" in text
    assert "| `narayana`, `yogini`, `ashtottari`, `chara_karaka`, `naisargika` | `single` |" in text
    assert "| `vimshottari` (non-KP) | `two_pass_verified` |" in text
    assert "tiers_evidence_v1_3" in text
    for sysid in ("mudda", "narayana", "yogini", "ashtottari", "chara_karaka", "naisargika", "vimshottari"):
        assert f"'{sysid}'" in text.split("`chart_dashas` (level 1 of every system", 1)[1].split("```", 2)[1]
    assert "narayana 105 level-1 rows" not in text and "two_pass_verified` to `classical_match`; `l1_tajik" not in text


# --- SS ruling (LOW-2 in code): a baseline of an empty read is refused, and nothing is written
@pytest.mark.parametrize("blank", ["chart_facts", "divisionals", "dashas", "daily"])
def test_ss_a_snapshot_of_an_empty_read_is_refused_and_writes_nothing(tmp_path, monkeypatch, capsys, blank):
    state = base_state()
    state[blank] = []
    fake_db(tmp_path, monkeypatch, charts={NATIVE: state})
    outdir = tmp_path / "snaps"
    outdir.mkdir()
    assert F.main(["--snapshot", "native", "--out", str(outdir / "base.json.gz")]) == 5
    assert list(outdir.iterdir()) == [], "no snapshot, no .sha256, no temporary file"
    err = capsys.readouterr().err
    assert "EMPTY READ" in err and "no snapshot was written" in err
    # the default store behaves the same
    monkeypatch.setenv("FLIP_SNAPSHOT_DIR", str(outdir))
    assert F.main(["--snapshot", "native"]) == 5 and list(outdir.iterdir()) == []


def test_ss_an_empty_table_that_is_not_read_does_not_block_a_snapshot(tmp_path, monkeypatch, capsys):
    state = base_state()
    state["dashas"], state["daily"] = [], []
    fake_db(tmp_path, monkeypatch, charts={NATIVE: state})
    out = tmp_path / "ok.json.gz"
    assert F.main(["--snapshot", "native", "--out", str(out), "--no-dashas", "--no-daily"]) == 0
    assert sorted(p.name for p in tmp_path.iterdir() if p.name.startswith("ok")) == ["ok.json.gz", "ok.json.gz.sha256"]
    capsys.readouterr()


def test_ss_snapshot_write_is_atomic_and_leaves_no_temporary_file(tmp_path, monkeypatch, capsys):
    fake_db(tmp_path, monkeypatch)
    outdir = tmp_path / "snaps"
    outdir.mkdir()
    assert F.main(["--snapshot", "native", "--out", str(outdir / "a.json.gz")]) == 0
    assert sorted(p.name for p in outdir.iterdir()) == ["a.json.gz", "a.json.gz.sha256"]
    real_link = os.link

    def failing_link(src, dst, *a, **k):
        if str(dst).endswith(".sha256"):
            raise OSError("disk full")
        return real_link(src, dst, *a, **k)
    monkeypatch.setattr(F.os, "link", failing_link)
    with pytest.raises(OSError):
        F.main(["--snapshot", "native", "--out", str(outdir / "b.json.gz")])
    assert sorted(p.name for p in outdir.iterdir()) == ["a.json.gz", "a.json.gz.sha256"], "a failed write leaves neither half a baseline nor temporary files"
    capsys.readouterr()


def test_ss_the_readme_states_the_operator_steps_and_known_limits():
    text = (GOV_DIR / "FLIP_DETECTOR_README.md").read_text()
    for needle in ("FLIP_TIMEOUT_SEC", "connect directly", "PgBouncer", "W0 baseline", "HOOKS_W7_HAND_READBACK_v1_0.md", "before W1 is merged", "re-take it under a new name",
                   "Known limits (post-window hardening list)", "grandchild", "N1, N7, N11, N15, N16", "traceback", "applies only with `--require-lanes`"):
        assert needle in text, needle
