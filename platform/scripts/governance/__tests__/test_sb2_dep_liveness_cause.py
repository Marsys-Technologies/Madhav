"""test_sb2_dep_liveness_cause.py -- Build.dep_liveness says WHICH declared dependency is not lit and WHY (verdict logic unchanged).

Pure functions on hand-built records, plus the measure() wiring (offline harness as test_r99_*). No database, no network.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

CH = "482012f1-710e-4a25-994a-93821f5871aa"


def rec(state="lit", built="2026-10-01", epoch=1000.0, **kw):
    return dict(state=state, last_built=built, built_epoch=str(epoch), n_rows=1, ambiguous=False, **kw)


GRAPH = {"d": ["u1"], "u1": ["u2"], "u2": [], "x": []}


def test_stale_cause_names_the_upstream_built_after_it():
    recs = {"d": {CH: rec("stale", "2026-10-01", 1000)}, "u1": {CH: rec("lit", "2026-10-03", 2000)}, "u2": {CH: rec("lit", "2026-09-01", 10)}}
    c = ac.stale_dependency_causes(["d"], GRAPH, recs, CH)["d"]
    assert "u1 (built 2026-10-03, state lit)" in c and "u2" not in c, c


def test_stale_cause_when_no_upstream_is_later_says_so_plainly():
    recs = {"d": {CH: rec("stale", "2026-10-01", 1000)}, "u1": {CH: rec("lit", built="2026-09-01", epoch=10)}}
    c = ac.stale_dependency_causes(["d"], GRAPH, recs, CH)["d"]
    assert "no asset in its upstream closure has a build record later" in c and "not come from a recorded upstream rebuild" in c, c


def test_stale_cause_uses_the_chart_row_else_the_global_row_and_ignores_other_charts():
    recs = {"d": {"": rec("stale", epoch=1000)}, "u1": {"other-chart": rec(epoch=9999), "": rec(built="2026-10-05", epoch=2000)}}
    c = ac.stale_dependency_causes(["d"], GRAPH, recs, CH)["d"]
    assert "u1 (built 2026-10-05" in c, c
    recs = {"d": {CH: rec("stale", epoch=1000)}, "u1": {"other-chart": rec(epoch=9999)}}
    assert "no asset in its upstream closure" in ac.stale_dependency_causes(["d"], GRAPH, recs, CH)["d"]


def test_unreadable_inputs_are_not_determinable_never_a_guess():
    assert "not determinable: psql down" in ac.stale_dependency_causes(["d"], None, None, CH, "psql down")["d"]
    assert "own build time is not recorded" in ac.stale_dependency_causes(["d"], GRAPH, {"d": {CH: rec("stale", epoch="")}}, CH)["d"]


def test_more_than_five_upstreams_are_counted_not_listed():
    g = {"d": [f"u{i}" for i in range(8)], **{f"u{i}": [] for i in range(8)}}
    recs = {"d": {CH: rec("stale", epoch=1)}, **{f"u{i}": {CH: rec(epoch=100 + i)} for i in range(8)}}
    assert "+3 more" in ac.stale_dependency_causes(["d"], g, recs, CH)["d"]


def test_upstream_closure_is_transitive_nearest_first_and_cycle_safe():
    assert ac._upstream_closure(GRAPH, "d") == ["u1", "u2"]
    assert ac._upstream_closure({"a": ["b"], "b": ["a"]}, "a") == ["b"]


# ───────────── the verdict is NOT moved by the cause text ─────────────

def test_verdicts_are_unchanged_with_and_without_causes():
    cases = {
        "PASS": {"a": {CH: rec("lit")}},
        "PARTIAL": {"a": {CH: rec("stale")}},
        "FAIL": {"a": {CH: rec("error")}},
        "FAIL2": {},
    }
    for name, dp in cases.items():
        plain = ac._grade_dep_liveness(["a"], dp, CH)
        with_c = ac._grade_dep_liveness(["a"], dp, CH, {"a": "stale because x"})
        assert plain["v"] == with_c["v"], name
    assert ac._grade_dep_liveness(["a"], cases["PASS"], CH)["v"] == ac.PASS
    assert ac._grade_dep_liveness(["a"], cases["PARTIAL"], CH)["v"] == ac.PARTIAL
    assert ac._grade_dep_liveness(["a"], cases["FAIL"], CH)["v"] == ac.FAIL
    assert ac._grade_dep_liveness(["a"], {"a": {CH: dict(rec(), ambiguous=True, n_rows=2)}}, CH)["v"] == ac.ERRORED


def test_the_cell_names_the_dependency_its_state_scope_date_and_cause():
    r = ac._grade_dep_liveness(["a", "b"], {"a": {CH: rec("stale", "2026-10-01")}, "b": {CH: rec("lit")}}, CH, {"a": "stale because upstream built after it: u1"})
    assert r["v"] == ac.PARTIAL and "1/2 declared dependencies lit" in r["measured"]
    assert "a (stale, chart 482012f1; last built 2026-10-01; stale because upstream built after it: u1)" in r["measured"], r
    r = ac._grade_dep_liveness(["a"], {"a": {CH: rec("error", "2026-09-30")}}, CH)
    assert "a (error, chart 482012f1; last built 2026-09-30)" in r["measured"], r


def test_service_ok_is_live_for_a_service_dependency_by_the_engine_rule():
    dp = {"svc": {CH: rec("service_ok")}}
    assert ac._grade_dep_liveness(["svc"], dp, CH, None, {"svc": "service"})["v"] == ac.PASS
    r = ac._grade_dep_liveness(["svc"], dp, CH, None, {"svc": "data"})
    assert r["v"] == ac.FAIL and "service_ok is live only for a registry asset_kind 'service'" in r["measured"] and "kind is data" in r["measured"], r
    r = ac._grade_dep_liveness(["svc"], dp, CH)                       # kind not read: never assumed
    assert r["v"] == ac.FAIL and "not read" in r["measured"], r


def test_service_ok_rule_does_not_leak_to_other_states():
    for st in ("error", "dormant", "building", "stale"):
        assert ac._grade_dep_liveness(["s"], {"s": {CH: rec(st)}}, CH, None, {"s": "service"})["v"] != ac.PASS, st


# ───────────── measure() wiring ─────────────

def _reg_row(aid, deps):
    return dict(asset_id=aid, has_writer=True, target_table="ga_t", count_sql="SELECT count(*) FROM ga_t", has_integrity=False, integrity_sql=None,
                depends_on=deps, target_floor="5", catalog_status="CURRENT", asset_kind="data")


def _stub(monkeypatch, tmp_path, records, graph):
    reg = {"ga_x": _reg_row("ga_x", ["ga_dep"])}
    rec_x = dict(rec("lit"), rows_written="5", rps="", _key=(0.0, 0.0), duration=None)
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(reg), dict(registry_total=1, active=1, excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists={"ga_t"}, cols={"ga_t": ["id"]}, keys={"ga_t": []}))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: 5 for x in r}, {}))
    asked = []

    def thru(prefix, ids=None, *a, **k):
        asked.append(list(ids or []))
        if ids and set(ids) <= set(records):
            return {i: records[i] for i in ids}
        return {"ga_x": {"": dict(rec_x)}, **{i: records[i] for i in (ids or []) if i in records}}
    monkeypatch.setattr(ac, "throughput", thru)
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={}, global_runs=0, global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    monkeypatch.setattr(ac, "dependency_graph", lambda: graph, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=0, full=[], never=list(c), note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)
    return asked


def _cell(census):
    return next(a for a in census["assets"] if a["asset_id"] == "ga_x")["measurements"]["Build.dep_liveness"]


def test_measure_names_the_rebuilt_upstream_of_a_stale_dependency(monkeypatch, tmp_path):
    records = {"ga_dep": {CH: rec("stale", "2026-10-01", 1000)}, "ga_up": {CH: rec("lit", "2026-10-04", 5000)}}
    asked = _stub(monkeypatch, tmp_path, records, {"ga_x": ["ga_dep"], "ga_dep": ["ga_up"], "ga_up": []})
    c = _cell(ac.measure("L1"))
    assert c["v"] == ac.PARTIAL and "ga_up (built 2026-10-04, state lit)" in c["measured"], c
    assert ["ga_up"] in asked                                       # the closure was read in one batch


def test_measure_with_an_unreadable_graph_says_not_determinable_and_keeps_the_verdict(monkeypatch, tmp_path):
    records = {"ga_dep": {CH: rec("stale", "2026-10-01", 1000)}}
    _stub(monkeypatch, tmp_path, records, {})
    monkeypatch.setattr(ac, "dependency_graph", lambda: (_ for _ in ()).throw(ac.Unknown("graph read failed")), raising=False)
    c = _cell(ac.measure("L1"))
    assert c["v"] == ac.PARTIAL and "cause not determinable: the dependency graph could not be read" in c["measured"], c


def test_measure_reads_no_closure_when_nothing_is_stale(monkeypatch, tmp_path):
    asked = _stub(monkeypatch, tmp_path, {"ga_dep": {CH: rec("lit")}}, {"ga_x": ["ga_dep"], "ga_dep": []})
    assert _cell(ac.measure("L1"))["v"] == ac.PASS
    assert all(a != ["ga_up"] for a in asked) and len(asked) == 2     # the layer's own read and the dependency read; no closure read


def test_measure_reads_the_dependency_kind_so_a_service_ok_service_dependency_is_live(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, {"ga_dep": {CH: rec("service_ok")}}, {"ga_x": ["ga_dep"], "ga_dep": []})
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: [["ga_dep", "service"]] if "asset_kind" in sql else [])
    assert _cell(ac.measure("L1"))["v"] == ac.PASS
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: [["ga_dep", "data"]] if "asset_kind" in sql else [])
    assert _cell(ac.measure("L1"))["v"] == ac.FAIL
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: (_ for _ in ()).throw(ac.Unknown("down")))
    assert _cell(ac.measure("L1"))["v"] == ac.FAIL
