"""test_e6_na_pin10.py: REGISTRY_REVISION 10, SS N-72. Two rules declared on top of the six N-65 ones.

  S4  Build.dep_liveness#measured:no-declared-dependencies   (N-22 row 23 re-proposed): N/A only when the declared dependency list
      is EMPTY and the reads-match detector (the asset's own Build.dag) is PASS; else NO_DETECTOR, never N/A.
  NS  Earn.service_state#measured:not-a-service              (N-22 row 9): N/A only for a DECLARED kind that is not `service`
      (and that the registry does not call a service); services and undeclared kinds keep reading NO_DETECTOR.
Offline. The saved-census test skips when the evidence directory is absent (CI)."""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e6_a_na_causes as na_causes  # noqa: E402
import test_e6_na_r01_03 as r13  # noqa: E402

NA, NO_DET = ac.NA, ac.NO_DET
S4 = "Build.dep_liveness#measured:no-declared-dependencies"
NS = "Earn.service_state#measured:not-a-service"
NON_SERVICE_KINDS = ("data", "static", "view", "rider", "probe", "user_data")


def _na(cause, crit="Build.dep_liveness"):
    return dict(v=NA, measured="m", cause=cause)


def _check(cells, gate, crit):
    return next(c for c in cells[gate]["checks"] if c["criterion"] == crit)


# ───────────────────────── the declared rules ─────────────────────────

def test_the_two_pin10_rules_are_declared_with_their_decisions_and_the_cause_is_registered():
    assert {S4, NS} <= set(ac.NA_RULE_DECISIONS) and r13.PIN10_IDS == {S4, NS}
    assert "N-22" in ac.NA_RULE_DECISIONS[S4] and "N-72" in ac.NA_RULE_DECISIONS[S4] and "row 23" in ac.NA_RULE_DECISIONS[S4]
    assert "N-22" in ac.NA_RULE_DECISIONS[NS] and "N-72" in ac.NA_RULE_DECISIONS[NS] and "row 9" in ac.NA_RULE_DECISIONS[NS]
    assert "no-declared-dependencies" in ac.NA_CAUSES["Build.dep_liveness"]
    assert ac.NA_CAUSES["Earn.service_state"] == ("not-a-service",)
    ac.validate_na_rule_decisions()
    assert ac.REGISTRY_REVISION >= 10


# ───────────────────────── S4: the reads-match guard ─────────────────────────

def test_S4_empty_dependency_list_with_a_clean_dag_reads_na():
    rec = ac._grade_dep_liveness_none(dict(v=ac.PASS, measured="0 declared edge(s); ..."))
    assert rec["v"] == NA and rec["cause"] == "no-declared-dependencies"
    assert "reads-match" in rec["measured"]
    chk = _check(ac.rollup_asset("L0", {"Build.dep_liveness": rec}), "Build", "Build.dep_liveness")
    assert chk["v"] == NA and chk["rule_id"] == S4


def test_S4_a_ruled_bedrock_exempt_read_is_noted_but_does_not_withhold():
    rec = ac._grade_dep_liveness_none(dict(v=ac.PASS, bedrock_exempt=[dict(table="brahma_ontology")], measured="m"))
    assert rec["v"] == NA and "bedrock_exempt" in rec["measured"]


@pytest.mark.parametrize("dag", [
    None,                                                                                                      # dag not measured at all
    dict(v=ac.FAIL, missing_edges=[dict(table="t_other", kind="missing_edge")], measured="missing depends_on edge"),   # an undeclared read
    dict(v=ac.FAIL, missing_edges=[dict(kind="back_read")], measured="back-read"),
    dict(v=ac.PARTIAL, measured="parse incomplete"),
    dict(v=NO_DET, measured="not established: the parse is incomplete"),
    dict(v=ac.ERRORED, measured="check errored: reads-match scan failed"),
    dict(v=ac.PASS, missing_edges=[dict(table="t")], measured="inconsistent record: PASS with a finding"),
])
def test_S4_without_a_clean_reads_match_the_reading_is_no_detector_never_na(dag):
    rec = ac._grade_dep_liveness_none(dag)
    assert rec["v"] == NO_DET and "cause" not in rec and "did not establish" in rec["measured"]
    chk = _check(ac.rollup_asset("L0", {"Build.dep_liveness": rec}), "Build", "Build.dep_liveness")
    assert chk["v"] == NO_DET


def test_S4_cause_emitted_but_rule_not_declared_is_no_na(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {k: v for k, v in ac.NA_RULE_DECISIONS.items() if k != S4})
    chk = _check(ac.rollup_asset("L0", {"Build.dep_liveness": _na("no-declared-dependencies")}), "Build", "Build.dep_liveness")
    assert chk["v"] == NO_DET and "undecided" in chk["reason"]


def test_S4_measure_emits_na_for_a_clean_no_dependency_asset_and_leaves_a_dependent_asset_alone(monkeypatch, tmp_path):
    reg = {"x": na_causes._reg_row("x"), "y": na_causes._reg_row("y", depends_on=["x"])}
    ms = na_causes._m(monkeypatch, tmp_path, reg, hist={"x": na_causes._h_unstarted(), "y": na_causes._h_unstarted()})
    assert ms["x"]["Build.dep_liveness"]["v"] == NA and ms["x"]["Build.dep_liveness"]["cause"] == "no-declared-dependencies"
    assert ms["y"]["Build.dep_liveness"]["v"] != NA and "cause" not in ms["y"]["Build.dep_liveness"]    # a non-empty list: graded as before


def test_S4_measure_withholds_the_na_when_the_asset_reads_an_undeclared_table(monkeypatch, tmp_path):
    reg = {"x": na_causes._reg_row("x")}
    na_causes._stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "_measure_dag", lambda *a, **k: dict(
        v=ac.FAIL, measured="missing depends_on edge: x -> y (reads t_y)", missing_edges=[dict(table="t_y", kind="missing_edge")]))
    m = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}["x"]
    assert m["Build.dag"]["v"] == ac.FAIL
    assert m["Build.dep_liveness"]["v"] == NO_DET and "cause" not in m["Build.dep_liveness"]
    assert ac.rollup_asset("L0", m)["Build"]["v"] == ac.FAIL                                              # the FAIL still holds the cell


def test_S4_measure_withholds_the_na_when_the_scan_is_unavailable(monkeypatch, tmp_path):
    reg = {"x": na_causes._reg_row("x")}
    na_causes._stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "_measure_dag", lambda *a, **k: dict(v=ac.ERRORED, measured="check errored: reads-match scan failed"))
    m = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}["x"]
    assert m["Build.dep_liveness"]["v"] == NO_DET


def test_S4_a_build_cell_never_reads_na_from_this_rule_alone():
    cells = ac.rollup_asset("L0", {"Build.dep_liveness": _na("no-declared-dependencies"), "Build.dag": dict(v=ac.PASS, measured="m")})
    assert cells["Build"]["v"] == NO_DET and _check(cells, "Build", "Build.dep_liveness")["v"] == NA      # other Build checks unmeasured


def test_S4_ledger_closes_the_open_row_of_a_released_na_only(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    rows = [r13._row("bg_x", "Build.dep_liveness"), r13._row("bg_y", "Build.dep_liveness")]
    r13._ledger(tmp_path, rows)
    ac.emit_gaps(r13._census(bg_x={"Build.dep_liveness": _na("no-declared-dependencies")},
                             bg_y={"Build.dep_liveness": ac._grade_dep_liveness_none(dict(v=ac.FAIL, missing_edges=[1]))}))
    assert r13._closed(tmp_path) == ["bg_x-Build.dep_liveness"]


# ───────────────────────── NS: not-a-service keyed on the declared kind ─────────────────────────

@pytest.mark.parametrize("kind", NON_SERVICE_KINDS)
def test_NS_a_declared_non_service_kind_reads_na_not_a_service(kind):
    rec = ac._service_state_na(kind, "data")
    assert rec["v"] == NA and rec["cause"] == "not-a-service" and kind in rec["measured"]
    chk = _check(ac.rollup_asset("L0", {"Earn.service_state": rec}), "Earn", "Earn.service_state")
    assert chk["v"] == NA and chk["rule_id"] == NS


@pytest.mark.parametrize("declared, registry", [
    ("service", "service"), ("service", "data"),          # a declared service never reads N/A
    (None, "data"), (None, "service"), (None, ""),        # an undeclared / null kind never reads N/A (the census does not guess)
    ("data", "service"),                                  # the registry calls it a service: the disagreement is not resolved by N/A
    ("static", "service"),
])
def test_NS_services_undeclared_kinds_and_a_contradicting_registry_are_never_na(declared, registry):
    assert ac._service_state_na(declared, registry) is None


def test_NS_cause_emitted_but_rule_not_declared_is_no_na(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {k: v for k, v in ac.NA_RULE_DECISIONS.items() if k != NS})
    chk = _check(ac.rollup_asset("L0", {"Earn.service_state": ac._service_state_na("data", "data")}), "Earn", "Earn.service_state")
    assert chk["v"] == NO_DET and "undecided" in chk["reason"]


def test_NS_a_service_with_no_measurement_keeps_reading_no_detector():
    chk = _check(ac.rollup_asset("L0", {}, dict(asset_kind="service")), "Earn", "Earn.service_state")
    assert chk["v"] == NO_DET and chk["state"] == "APPLIES"


def test_NS_the_earn_cell_does_not_move_while_build_record_is_unmeasured():
    cells = ac.rollup_asset("L0", {"Earn.service_state": ac._service_state_na("data", "data")})
    assert cells["Earn"]["v"] == NO_DET and _check(cells, "Earn", "Earn.service_state")["v"] == NA


def test_NS_measure_emits_the_candidate_only_for_a_declared_non_service_kind(monkeypatch, tmp_path):
    reg = {"d": na_causes._reg_row("d", asset_kind="data"), "s": na_causes._reg_row("s", asset_kind="service"),
           "u": na_causes._reg_row("u", asset_kind="data"), "c": na_causes._reg_row("c", asset_kind="service")}
    decl = {"d": dict(kind="data"), "s": dict(kind="service"), "u": dict(kind=None), "c": dict(kind="data")}      # c: declared data, registry service
    na_causes._stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: decl)
    ms = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}
    assert ms["d"]["Earn.service_state"]["v"] == NA and ms["d"]["Earn.service_state"]["cause"] == "not-a-service"
    for aid in ("s", "u", "c"):
        assert "Earn.service_state" not in ms[aid], aid


def test_NS_with_the_real_declarations_file_118_assets_read_na_8_services_and_1_undeclared_do_not():
    kinds = {a: ac._declared_kind(ac.load_asset_declarations(), a) for a in ac.load_asset_declarations()}
    assert len(kinds) == 127
    na = [a for a, k in kinds.items() if ac._service_state_na(k, "data") is not None]
    svc = [a for a, k in kinds.items() if k == "service"]
    unk = [a for a, k in kinds.items() if k is None]
    assert (len(na), len(svc), len(unk)) == (118, 8, 1) and unk == ["mi_vistara"]      # the "119 expected" includes mi_vistara, whose kind is undeclared


def test_NS_ledger_closes_an_open_earn_service_state_row_only_for_a_released_na(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    r13._ledger(tmp_path, [r13._row("bg_x", "Earn.service_state"), r13._row("bg_s", "Earn.service_state")])
    ac.emit_gaps(r13._census(bg_x={"Earn.service_state": ac._service_state_na("data", "data")}, bg_s={}))
    assert r13._closed(tmp_path) == ["bg_x-Earn.service_state"]
