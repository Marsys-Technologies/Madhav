"""test_n236_sibling_credit.py: a verified writer_sibling rider is credited with its primary's runs (SS N-236).

bg_nakshatra_medical rides bg_medical_mappings' writer class, bg_transit_engine rides bg_transit_rules'. Their own attempt logs are empty, so Build.exercised / Build.history / Earn.build_record read "never run / never
attempted". `credit_sibling_cells` credits them from the PRIMARY only when Build.registered PASSED with a verified writer_sibling block; every broken link is a mutation that must NOT credit. Offline over hand-built
measurement dicts (the pure function), plus a check that the real declarations carry exactly the two riders and that Build.registered verifies them from source.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

PASS, PARTIAL, FAIL, NO_DET, NA = ac.PASS, ac.PARTIAL, ac.FAIL, ac.NO_DET, ac.NA


def _rider(registered=None, has_writer=False):
    reg = registered if registered is not None else dict(v=PASS, measured="@register shared", writer_sibling=dict(verified=True, primary="prim", tables=["t"], files=["w.py"], writer_class="W"))
    return dict(asset_id="rider", has_writer=has_writer, measurements={
        "Build.registered": reg,
        "Build.exercised": ac._na("never run, and it has no writer — consistent", "never-run-no-writer"),
        "Build.history": ac._na("never run; check 7 owns this", "never-run"),
        "Earn.build_record": ac._na("never attempted — see Build.exercised", "never-attempted")})


def _prim(exercised=PASS, history=PASS, earn=PASS):
    return dict(asset_id="prim", has_writer=True, measurements={
        "Build.exercised": dict(v=exercised, measured="5 executed run(s)"), "Build.history": dict(v=history, measured="5 complete, no error"), "Earn.build_record": dict(v=earn, measured="completion write with duration")})


def _run(rider, prim=None):
    assets = [rider] + ([prim] if prim is not None else [])
    ac.credit_sibling_cells(assets)
    return rider["measurements"]


def test_a_verified_sibling_of_an_exercised_primary_is_credited_on_all_three_cells():
    m = _run(_rider(), _prim())
    for crit in ("Build.exercised", "Build.history", "Earn.build_record"):
        assert m[crit]["v"] == PASS and "inherited from the verified sibling primary prim" in m[crit]["measured"], (crit, m[crit])
        assert m[crit]["sibling_credit"]["primary"] == "prim" and m[crit]["sibling_credit"]["criterion"] == crit


def test_history_and_earn_inherit_the_primary_s_non_pass_verdicts_honestly():
    m = _run(_rider(), _prim(history=PARTIAL, earn=FAIL))
    assert m["Build.exercised"]["v"] == PASS and m["Build.history"]["v"] == PARTIAL and m["Earn.build_record"]["v"] == FAIL


# ───────────────────────── MUTATIONS: every broken link credits nothing ─────────────────────────

@pytest.mark.parametrize("prim", [_prim(exercised=NO_DET), _prim(exercised=FAIL), _prim(exercised=NA), _prim(history=NO_DET)])
def test_MUTATION_a_primary_that_is_not_exercised_in_its_window_does_not_exercise_the_rider(prim):
    m = _run(_rider(), prim)
    assert m["Build.exercised"]["v"] == NO_DET and "not shown exercised inside its history window" in m["Build.exercised"]["measured"], m["Build.exercised"]


def test_MUTATION_a_primary_with_no_verdict_on_history_or_earn_credits_neither():
    m = _run(_rider(), _prim(history=NO_DET, earn=NO_DET))
    assert m["Build.history"]["v"] == NO_DET and m["Earn.build_record"]["v"] == NO_DET


def test_MUTATION_the_primary_missing_from_the_census_scope_credits_nothing():
    m = _run(_rider(), None)
    assert all(m[c]["v"] == NO_DET and "not in this census scope" in m[c]["measured"] for c in ("Build.exercised", "Build.history", "Earn.build_record"))


@pytest.mark.parametrize("reg", [
    dict(v=FAIL, measured="the two do not share a writer class", writer_sibling=dict(verified=True, primary="prim")),     # the relationship does not verify
    dict(v=PASS, measured="x"),                                                                                              # no sibling block at all (a declaration alone is nothing)
    dict(v=PASS, measured="x", writer_sibling=dict(verified=False, primary="prim")),
    dict(v=NO_DET, measured="x", writer_sibling=dict(verified=True, primary="prim")),
])
def test_MUTATION_a_relationship_that_is_not_verified_credits_nothing(reg):
    r = _rider(registered=reg)
    before = copy.deepcopy(r["measurements"])
    m = _run(r, _prim())
    assert m == before                                                                         # untouched: the cells keep their "never run" reading


def test_MUTATION_a_rider_that_has_a_writer_of_its_own_is_never_credited():
    r = _rider(has_writer=True)
    before = copy.deepcopy(r["measurements"])
    assert _run(r, _prim()) == before


def test_a_rider_with_an_attempt_of_its_own_keeps_its_own_cell():
    r = _rider()
    r["measurements"]["Build.exercised"] = dict(v=PASS, measured="1 executed run(s) of its own")
    r["measurements"]["Earn.build_record"] = dict(v=FAIL, measured="its own record")
    m = _run(r, _prim())
    assert m["Build.exercised"]["measured"] == "1 executed run(s) of its own" and m["Earn.build_record"]["v"] == FAIL and m["Build.history"]["v"] == PASS


def test_the_credit_never_touches_a_primary_or_an_asset_without_a_sibling_declaration():
    prim = _prim()
    before = copy.deepcopy(prim["measurements"])
    plain = dict(asset_id="plain", has_writer=False, measurements={"Build.exercised": ac._na("never run", "never-run-no-writer"), "Build.registered": dict(v=PASS, measured="x")})
    ac.credit_sibling_cells([prim, plain])
    assert prim["measurements"] == before and plain["measurements"]["Build.exercised"]["v"] == NA


# ───────────────────────── the real declarations ─────────────────────────

def test_the_real_declarations_name_exactly_the_two_riders():
    decl = json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))["assets"]
    riders = {a: e["writer_sibling"]["primary"] for a, e in decl.items() if e.get("writer_sibling")}
    assert riders == {"bg_nakshatra_medical": "bg_medical_mappings", "bg_transit_engine": "bg_transit_rules"}


def test_the_real_riders_verify_from_source_through_build_registered():
    """The relationship the credit rests on is the one Build.registered verifies: both @register decorators on ONE class (read from the writer files)."""
    for rider, prim in (("bg_nakshatra_medical", "bg_medical_mappings"), ("bg_transit_engine", "bg_transit_rules")):
        files = ac.registered_ids("bg_")
        assert files[rider] == files[prim] and len(files[rider]) == 1, (rider, files[rider], files[prim])
        cs, cp = ac._writer_class(ac._writer_path(files[rider][0]), rider), ac._writer_class(ac._writer_path(files[prim][0]), prim)
        assert cs is not None and (cs.name, cs.lineno) == (cp.name, cp.lineno)
