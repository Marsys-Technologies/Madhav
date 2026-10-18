"""test_n514_cost_baseline.py: Cost.baseline for the two cases the Earn.build_record rules already settled (SS N-514, REGISTRY_REVISION 29).

(1) SIBLING CREDIT (N-236). bg_nakshatra_medical rides bg_medical_mappings' writer class and bg_transit_engine rides bg_transit_rules'. The orchestrator never runs a rider, so its own attempt log is empty and
    Cost.baseline read FAIL "no sanctioned baseline build on record" although the PRIMARY's baseline reads PASS. The cell is now credited like the other three: it FOLLOWS the primary's verdict (PASS credits,
    FAIL stays FAIL, an unmeasured primary reads NO_DETECTOR), only for the exact "no attempt of my own" shape, and only for a verified rider.
(2) NO-WRITER. An asset that declares `has_writer: false` and whose registry row and @register scan agree has no build, so no baseline of a build applies: Cost.baseline reads N/A (cause
    no-writer-registry-agrees) exactly where Earn.build_record reads its released no-writer N/A, and never otherwise (a writer-backed asset without a baseline keeps FAIL; a contradicted declaration keeps
    the cell as measured).

Offline: the pure functions, the rollup / ledger release, and measure() through the same stubs test_ss_build_record_no_writer uses. No database."""
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
CRIT = "Cost.baseline"
NO_BASELINE = "no sanctioned baseline build on record"      # the literal the classifier has always written (kept literal here so the tests do not depend on the new constant)
OK = dict(declared=True, registry_has_writer=False, register_files=0, register_mentions=[])


# ───────────────────────── (1) sibling credit ─────────────────────────

def _rider(registered=None, has_writer=False, cost=None):
    reg = registered if registered is not None else dict(v=PASS, measured="@register shared", writer_sibling=dict(verified=True, primary="prim", tables=["t"], files=["w.py"], writer_class="W"))
    return dict(asset_id="rider", has_writer=has_writer, measurements={
        "Build.registered": reg,
        CRIT: cost if cost is not None else dict(v=FAIL, measured=NO_BASELINE)})


def _prim(cost=None):
    return dict(asset_id="prim", has_writer=True, measurements={CRIT: cost if cost is not None else dict(v=PASS, measured="sanctioned baseline: rate=12.5 (attempt abcdef01, 3d old)")})


def _run(rider, prim=None):
    ac.credit_sibling_cells([rider] + ([prim] if prim is not None else []))
    return rider["measurements"]


def test_cost_baseline_is_a_sibling_credit_cell():
    assert CRIT in ac.SIBLING_CREDIT_CELLS


def test_a_verified_sibling_of_a_primary_with_a_baseline_is_credited():
    got = _run(_rider(), _prim())[CRIT]
    assert got["v"] == PASS and "inherited from the verified sibling primary prim" in got["measured"] and "rate=12.5" in got["measured"], got
    assert got["sibling_credit"]["primary"] == "prim" and got["sibling_credit"]["criterion"] == CRIT and got["sibling_credit"]["primary_verdict"] == PASS


def test_the_credit_follows_the_primary_it_does_not_manufacture_a_pass():
    got = _run(_rider(), _prim(cost=dict(v=FAIL, measured=NO_BASELINE)))[CRIT]
    assert got["v"] == FAIL and "inherited from the verified sibling primary prim" in got["measured"] and got["sibling_credit"]["primary_verdict"] == FAIL, got


@pytest.mark.parametrize("pcost", [dict(v=NO_DET, measured="NO_DETECTOR — instrument absent"), dict(v=NA, measured="n/a", cause="no-writer-registry-agrees"), dict(v="ERRORED", measured="x"), {}])
def test_MUTATION_an_unmeasured_primary_credits_nothing_and_reads_no_detector(pcost):
    got = _run(_rider(), _prim(cost=pcost))[CRIT]
    assert got["v"] == NO_DET and "carries no verdict" in got["measured"], got


def test_MUTATION_the_primary_missing_from_the_census_scope_credits_nothing():
    got = _run(_rider(), None)[CRIT]
    assert got["v"] == NO_DET and "not in this census scope" in got["measured"], got


@pytest.mark.parametrize("reg", [
    dict(v=FAIL, measured="the two do not share a writer class", writer_sibling=dict(verified=True, primary="prim")),
    dict(v=PASS, measured="x"),
    dict(v=PASS, measured="x", writer_sibling=dict(verified=False, primary="prim")),
    dict(v=NO_DET, measured="x", writer_sibling=dict(verified=True, primary="prim")),
])
def test_MUTATION_a_relationship_that_is_not_verified_credits_nothing(reg):
    r = _rider(registered=reg)
    before = copy.deepcopy(r["measurements"])
    assert _run(r, _prim()) == before and r["measurements"][CRIT]["v"] == FAIL


def test_MUTATION_a_rider_with_a_writer_of_its_own_is_never_credited():
    r = _rider(has_writer=True)
    before = copy.deepcopy(r["measurements"])
    assert _run(r, _prim()) == before


@pytest.mark.parametrize("own", [
    dict(v=FAIL, measured=NO_BASELINE + "; latest attempt at chart 482012f1: run abcdef01 complete/probe_green (2026-09-07)"),     # the rider HAS an attempt of its own: its reading is not "none"
    dict(v=NO_DET, measured="NO_DETECTOR — instrument absent (migration 1094), scoped to this run"),
    dict(v=PASS, measured="sanctioned baseline: rate=1.0 (attempt 12345678, 1d old)"),
])
def test_a_rider_cell_that_is_not_the_no_attempt_shape_keeps_its_own_reading(own):
    r = _rider(cost=own)
    before = copy.deepcopy(r["measurements"])
    assert _run(r, _prim()) == before


def test_the_credited_cell_is_what_the_ledger_and_the_cost_rollup_read():
    m = _run(_rider(), _prim())
    assert ac._na_released(CRIT, m[CRIT]) is True            # a PASS releases; the credited record is a plain PASS verdict
    assert m[CRIT]["v"] == PASS


def test_the_real_riders_are_exactly_the_two_declared_siblings():
    decl = json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))["assets"]
    assert {a: e["writer_sibling"]["primary"] for a, e in decl.items() if e.get("writer_sibling")} == {"bg_nakshatra_medical": "bg_medical_mappings", "bg_transit_engine": "bg_transit_rules"}


# ───────────────────────── (2) no-writer ─────────────────────────

def _earn_na(cause="no-writer-registry-agrees", block=None):
    return dict(ac._na("no writer: no build record applies", cause), no_writer=dict(block if block is not None else OK))


def _cost(measured=NO_BASELINE, v=FAIL):
    return dict(v=v, measured=measured)


def test_the_rule_row_the_cause_and_the_guard_are_registered():
    assert ac.NA_CAUSES[CRIT] == ("no-writer-registry-agrees",)
    assert ac.NA_RULE_DECISIONS[f"{CRIT}#measured:no-writer-registry-agrees"].startswith("SS N-514")
    assert ac.NO_WRITER_CAUSES[CRIT] == ("no-writer-registry-agrees",)
    assert ac.CRITERION_REGISTRY[CRIT]["revision"] == 2 and "SS N-514" in ac.CRITERION_REGISTRY[CRIT]["applicability"]
    ac.validate_na_rule_decisions()


@pytest.mark.parametrize("cause", ["no-writer-registry-agrees", "declared-probe-runs-verified"])
def test_an_agreeing_no_writer_asset_whose_build_record_is_released_reads_na(cause):
    block = dict(OK) if cause == "no-writer-registry-agrees" else dict(OK, probe_attempts=True, verified=True, service=True, runs=["abcdef0123456789"])
    got = ac.cost_baseline_no_writer(_cost(NO_BASELINE + "; latest attempt at chart 482012f1: run abcdef01 complete/probe_green (2026-09-07)"), _earn_na(cause, block))
    assert got["v"] == NA and got["cause"] == "no-writer-registry-agrees" and got["no_writer"] == block, got
    assert "no build exists to baseline" in got["measured"] and "has_writer: false" in got["measured"]
    assert ac._na_released(CRIT, got) is True


@pytest.mark.parametrize("earn", [
    dict(v=FAIL, measured="declared has_writer: false but a NEWER build attempt contradicts it", no_writer=dict(OK, attempts=1)),       # the declaration is contradicted: a build exists, the cell stays as measured
    dict(v=NO_DET, measured="NO_DETECTOR — attempts could not be read", no_writer=dict(OK)),
    dict(v=NA, measured="never attempted", cause="never-attempted"),                                                                      # the old un-ruled cause: no agreeing block, no release
    dict(v=NA, measured="healthy non-execution", cause="healthy-non-execution"),
    dict(v=PASS, measured="completion write with duration=3s"),
    {},
])
def test_MUTATION_a_build_record_that_is_not_the_released_no_writer_na_leaves_the_cell_as_measured(earn):
    cost = _cost()
    assert ac.cost_baseline_no_writer(dict(cost), earn) == cost


@pytest.mark.parametrize("mut", [dict(declared=False), dict(registry_has_writer=True), dict(register_files=1), dict(register_mentions=["x.py"]), dict(declared=None)])
def test_MUTATION_without_all_four_agreeing_facts_the_cell_is_unchanged(mut):
    cost = _cost()
    assert ac.cost_baseline_no_writer(dict(cost), _earn_na(block=dict(OK, **mut))) == cost


def test_MUTATION_a_probe_release_without_its_verification_does_not_release_cost():
    cost = _cost()
    assert ac.cost_baseline_no_writer(dict(cost), _earn_na("declared-probe-runs-verified", dict(OK, probe_attempts=True, verified=False, service=True, runs=["x"]))) == cost


def test_a_measured_baseline_is_never_replaced_by_the_no_writer_rule():
    cost = dict(v=PASS, measured="sanctioned baseline: rate=1.0 (attempt 12345678, 400d old)")
    assert ac.cost_baseline_no_writer(dict(cost), _earn_na()) == cost


def test_the_released_record_needs_its_block_to_close_a_ledger_row():
    good = ac.cost_baseline_no_writer(_cost(), _earn_na())
    assert ac._na_released(CRIT, good) is True and ac.no_writer_na_problem(CRIT, good) is None
    assert ac._na_released(CRIT, dict(good, no_writer=dict(OK, register_files=1))) is False
    assert ac._na_released(CRIT, {k: v for k, v in good.items() if k != "no_writer"}) is False
    assert ac._na_released(CRIT, dict(good, cause="never-attempted")) is False


# ───────────── measure(): the wiring, through the stubs of test_ss_build_record_no_writer ─────────────

def _reg_row(aid, has_writer, kind):
    return dict(asset_id=aid, has_writer=has_writer, target_table=None, count_sql="", has_integrity=False, integrity_sql=None, depends_on=[], target_floor=None, catalog_status="CURRENT", asset_kind=kind)


def _stub(monkeypatch, tmp_path, aid, has_writer, kind="service", decl=None, disp="", ep=9e9):
    """`disp` "" is the engine's probe-green row (complete, no disposition, a provenance receipt, from the disposition era on); "build" is a writer completion."""
    receipt = disp == ""
    h = dict(runs=1, error=0, aborted=0, complete=1, queued=0, skipped=0, blocked=0, scopes={"chart"}, last_state="complete", last_when="2026-08-27", last_disposition=disp,
             sample_error="", sample_blocked="", executed=1, executed_scopes={"chart"}, last_executed_when="2026-08-27", states={"complete": 1}, sample_error_when="")
    attempt = dict(run_id="abcdef0123456789", state="complete", disposition=disp, ended_epoch="", created_epoch=ep, when="2026-08-27", receipt=receipt)
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    monkeypatch.setattr(ac, "registry", lambda k: ({aid: _reg_row(aid, has_writer, kind)}, dict(registry_total=1, active=1, excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists=set(), cols={}, keys={}, views=set()))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: None for x in r}, {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={aid: h}, global_runs=0, global_with_layer=0, lit=set()))
    log = [dict(scope="chart", state="complete", disposition=disp, when="2026-08-27", error="", started=True, epoch=ep, receipt=receipt)]
    monkeypatch.setattr(ac, "build_attempt_log", lambda prefix, ids=None: {aid: log})
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({aid: {ac.CHART_ID: attempt}}, 100.0))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {aid: []}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: True)            # the instrument exists (as live): the cell is graded, not NO_DETECTOR "instrument absent"
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=0, full=[], never=list(c), note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: ({aid: decl} if decl is not None else {}))
    bw = ac._lint_module("build_window")
    monkeypatch.setattr(bw.WindowReader, "__init__", lambda self, *a, **k: None)
    monkeypatch.setattr(bw.WindowReader, "has_writer_commit", lambda self, a: (1000.0, "f" * 40, "migration set has_writer = false"))
    monkeypatch.setattr(bw.WindowReader, "registry_commit", lambda self, a: (1000.0, "f" * 40, "registry"))
    monkeypatch.setattr(bw.WindowReader, "commit_epoch", lambda self, sha: 0)
    monkeypatch.setattr(bw, "compute_window", lambda reader, a, paths: dict(ok=False, reason="stub"))
    monkeypatch.setattr(ac, "_writer_code_paths", lambda a, f, h: ["x"])
    monkeypatch.setattr(ac, "register_call_mentions", lambda a: [])


def _cells(c, aid):
    return next(a for a in c["assets"] if a["asset_id"] == aid)["measurements"]


def test_measure_a_declared_no_writer_service_with_only_probe_attempts_reads_na_on_both_cells(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, "bg_svc", has_writer=False, decl={"kind": "service", "has_writer": False})
    cells = _cells(ac.measure("L0"), "bg_svc")
    assert cells["Earn.build_record"]["v"] == NA, cells["Earn.build_record"]
    assert cells[CRIT]["v"] == NA and cells[CRIT]["cause"] == "no-writer-registry-agrees" and cells[CRIT]["no_writer"]["registry_has_writer"] is False, cells[CRIT]
    assert ac._na_released(CRIT, cells[CRIT]) is True


def test_measure_a_writer_backed_asset_with_no_baseline_still_fails(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, "bg_svc", has_writer=True, decl={"kind": "service"})
    cells = _cells(ac.measure("L0"), "bg_svc")
    assert cells[CRIT]["v"] == FAIL and NO_BASELINE in cells[CRIT]["measured"] and "cause" not in cells[CRIT], cells[CRIT]


def test_measure_a_writer_backed_asset_that_wrongly_declares_no_writer_is_not_released(monkeypatch, tmp_path):
    """the registry row (has_writer true) disagrees with the declaration: neither Earn.build_record nor Cost.baseline reads the no-writer N/A"""
    _stub(monkeypatch, tmp_path, "bg_svc", has_writer=True, decl={"kind": "service", "has_writer": False})
    cells = _cells(ac.measure("L0"), "bg_svc")
    assert cells[CRIT]["v"] == FAIL and cells["Earn.build_record"].get("cause") not in ac.NO_WRITER_CAUSES["Earn.build_record"], (cells[CRIT], cells["Earn.build_record"])


def test_measure_an_undeclared_no_writer_row_is_not_released(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, "bg_svc", has_writer=False, decl=None)
    cells = _cells(ac.measure("L0"), "bg_svc")
    assert cells[CRIT]["v"] == FAIL, cells[CRIT]


def test_measure_a_contradicted_no_writer_declaration_leaves_the_cell_as_measured(monkeypatch, tmp_path):
    """a build attempt NEWER than the no-writer definition contradicts the declaration (Earn.build_record FAIL): a build exists, so Cost.baseline is not released"""
    _stub(monkeypatch, tmp_path, "bg_svc", has_writer=False, decl={"kind": "service", "has_writer": False}, disp="build", ep=5000.0)
    cells = _cells(ac.measure("L0"), "bg_svc")
    assert cells["Earn.build_record"]["v"] == FAIL and cells[CRIT]["v"] != NA, (cells["Earn.build_record"], cells[CRIT])


def test_the_real_declarations_name_exactly_the_no_writer_assets_the_rule_can_release():
    decl = json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))["assets"]
    no_writer = sorted(a for a, e in decl.items() if e.get("has_writer") is False)
    assert no_writer == ["bg_ephemeris_engine", "bg_gochara_citation_resolution", "bg_panchanga"]
    assert [a for a in no_writer if decl[a].get("kind") == "service" and decl[a].get("probe_attempts")] == ["bg_ephemeris_engine", "bg_panchanga"]
