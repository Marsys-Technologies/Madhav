"""test_e6_a_na_causes.py — E6 packet (a): the cause-keyed N/A encoding (N-22 ruling principle 2).

The inspector emits a `cause` on EVERY measured N/A verdict (and on no other record); the rollup turns it into the
rule id `<criterion>#measured:<cause>`. One id per criterion used to release every measured N/A of that criterion
(`<criterion>#measured`); a cause narrows the release to the condition the code itself named. An N/A with no usable
cause reads fail-closed NO_DETECTOR ("N/A without a declared cause"), and `NA_RULE_DECISIONS` is still EMPTY (the
N-22 rule table is not approved), so no cell can read N/A.

Offline: the same `_stub_layer` harness as packet 1 / 2a. No database.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

FIXTURE = json.loads((HERE / "fixtures" / "census_cells_2026-09-30.json").read_text(encoding="utf-8"))

NA = "N/A"


# ───────────────────────── offline measure() harness ─────────────────────────

def _reg_row(aid, target_table=None, has_writer=False, count_sql="", asset_kind="", depends_on=(), target_floor=None,
             has_integrity=False):
    return dict(asset_id=aid, has_writer=has_writer, target_table=target_table, count_sql=count_sql,
                has_integrity=has_integrity, depends_on=list(depends_on), target_floor=target_floor,
                catalog_status="", asset_kind=asset_kind)


def _stub_layer(monkeypatch, ctrl, reg, tables=None, *, registered=None, live=None, hist=None, cap=None):
    tables = tables or {}
    monkeypatch.setattr(ac, "CTRL", ctrl)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(reg), dict(registry_total=len(reg), active=len(reg),
                                                                    excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists=set(tables),
                                                       cols={t: c for t, (c, _k) in tables.items()},
                                                       keys={t: k for t, (_c, k) in tables.items()}, views=set()))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: dict(registered or {}))
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: (dict(live or {x: None for x in r}), {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per=dict(hist or {}), global_runs=0,
                                                                         global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {a: [] for a in reg}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan",
                        lambda d, t: dict(cap) if cap is not None else dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=48, full=list(c), never=[], note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)
    monkeypatch.setattr(ac, "idem_scan", lambda *a, **k: ("PASS", ["stub"]))
    monkeypatch.setattr(ac, "contract_scan", lambda a, f: ("PASS", []))

    def fake_psql(sql, sep="\x1f", timeout=None):
        if "IS NOT NULL" in sql:
            return [["48"]]
        if "EXISTS" in sql:
            return [["f"]]
        raise AssertionError(f"unexpected query: {sql[:100]}")
    monkeypatch.setattr(ac, "psql", fake_psql)
    monkeypatch.setattr(ac, "scalar", lambda sql: (fake_psql(sql) or [[None]])[0][0])


def _m(monkeypatch, tmp_path, reg, **kw):
    _stub_layer(monkeypatch, tmp_path, reg, **kw)
    c = ac.measure("L0")
    return {a["asset_id"]: a["measurements"] for a in c["assets"]}


def _h_unstarted():
    """A build_history per-asset dict: rows exist, none ever STARTED (C1)."""
    return dict(runs=2, executed=0, states="queued", error=0, blocked=0, aborted=0, complete=0, skipped=0,
                last_state="queued", last_disposition="", last_when="", sample_blocked="", executed_scopes=set(),
                last_executed_when="")


# ───────────────────────── (1) every emission site carries its cause ─────────────────────────

SITES = [
    # (id, criterion, expected cause, registry rows, kwargs to the stub)
    ("registered-no-writer", "Build.registered", "no-writer-registry-agrees",
     {"x": _reg_row("x")}, {}),
    ("contract-no-writer", "Build.contract", "no-writer-registry-agrees",
     {"x": _reg_row("x")}, {}),
    ("idem-no-writer", "Idem.pattern", "no-writer-registry-agrees",
     {"x": _reg_row("x")}, {}),
    ("target-service", "Build.target", "service-no-target-table",
     {"x": _reg_row("x", asset_kind="service", has_writer=True)}, {}),
    ("target-no-writer", "Build.target", "no-writer-no-target-table",
     {"x": _reg_row("x", asset_kind="data", has_writer=False)}, {}),
    ("target-service-and-no-writer-is-service", "Build.target", "service-no-target-table",
     {"x": _reg_row("x", asset_kind="service", has_writer=False)}, {}),
    ("count-integrity", "Build.count_integrity", "no-writer-no-count-sql",
     {"x": _reg_row("x")}, {}),
    ("completion-no-writer", "Build.completion", "no-writer-no-count-sql",
     {"x": _reg_row("x")}, {}),
    ("completion-service", "Build.completion", "service-no-target-table-no-count-sql",
     {"x": _reg_row("x", asset_kind="service", has_writer=True)}, {}),
    ("count-floor-zero", "Count.floor", "target-floor-zero",
     {"x": _reg_row("x", target_floor="0")}, {}),
    ("dens-no-module", "Dens.served", "no-module-references-target",
     {"x": _reg_row("x")}, dict(cap=dict(scanned=True, modules=[], density=0, note=""))),
    ("exercised-never-run", "Build.exercised", "never-run-no-writer",
     {"x": _reg_row("x")}, {}),
    ("exercised-never-executed", "Build.exercised", "never-executed-no-writer",
     {"x": _reg_row("x")}, dict(hist={"x": _h_unstarted()})),
    ("history-never-run", "Build.history", "never-run",
     {"x": _reg_row("x")}, {}),
    ("dep-liveness-none", "Build.dep_liveness", "no-declared-dependencies",
     {"x": _reg_row("x")}, {}),
]


@pytest.mark.parametrize("sid,crit,cause,reg,kw", SITES, ids=[s[0] for s in SITES])
def test_each_measure_na_site_emits_its_named_cause(monkeypatch, tmp_path, sid, crit, cause, reg, kw):
    rec = _m(monkeypatch, tmp_path, reg, **kw)["x"][crit]
    assert rec["v"] == NA, rec
    assert rec["cause"] == cause
    assert cause in ac.NA_CAUSES[crit]


def test_earn_build_record_causes_come_from_the_d6_classifier():
    g = lambda attempt: ac._grade_earn_cost(attempt, True, None, attempt_linkage_wired=True)[0]   # noqa: E731
    never = g(None)
    assert never["v"] == NA and never["cause"] == "never-attempted"
    skip = g(dict(disposition="skip_no_delta", has_writer=True, reached_completion_write=True))
    assert skip["v"] == NA and skip["cause"] == "healthy-non-execution"
    probe = g(dict(disposition="probe_green", has_writer=True))
    assert probe["v"] == NA and probe["cause"] == "healthy-non-execution"
    nowriter = g(dict(disposition="", has_writer=False))
    assert nowriter["v"] == NA and nowriter["cause"] == "no-registered-writer"
    # the review's case: an ERRORED attempt on an asset with no registered writer is not a healthy non-execution
    nowriter_err = g(dict(disposition="", has_writer=False, state="error", reached_completion_write=False))
    assert nowriter_err["v"] == NA and nowriter_err["cause"] == "no-registered-writer"
    assert "healthy" not in nowriter_err["measured"] and "error" in nowriter_err["measured"]
    # healthy-non-execution is the DISPOSITION's claim only: a skip/probe on a no-writer asset is still that claim
    nowriter_skip = g(dict(disposition="skip_no_delta", has_writer=False))
    assert nowriter_skip["v"] == NA and nowriter_skip["cause"] == "healthy-non-execution"
    for k in ("never-attempted", "healthy-non-execution", "before-completion-write", "no-registered-writer"):
        assert k in ac.NA_CAUSES["Earn.build_record"]
    early = g(dict(disposition="build", has_writer=True, state="error", reached_completion_write=False))
    assert early["v"] == NA and early["cause"] == "before-completion-write"


def test_no_non_na_record_carries_a_cause_and_every_na_record_does(monkeypatch, tmp_path):
    """Emitted ONLY on N/A; the verdict and text of every other record are untouched. Runs every SITES registry
    row together plus non-N/A shapes, then checks the invariant over all measurements."""
    reg = {f"a{i}": r for i, (_s, _c, _k, rows, _kw) in enumerate(SITES) for r in [next(iter(rows.values()))]}
    reg = {aid: dict(row, asset_id=aid) for aid, row in reg.items()}
    reg["w"] = _reg_row("w", "t", True, "SELECT count(*) FROM t", "data", has_integrity=True, depends_on=["a0"])
    recs = _m(monkeypatch, tmp_path, reg, tables={"t": (["id", "classical_citation"], [["id"]])},
              registered={"w": ["w.py"]}, live={"w": 48})
    seen_na = seen_other = 0
    for aid, ms in recs.items():
        for crit, r in ms.items():
            if r["v"] == NA:
                seen_na += 1
                assert isinstance(r.get("cause"), str) and r["cause"].strip(), (aid, crit, r)
                assert r["cause"] in ac.NA_CAUSES[crit], (aid, crit, r["cause"])
            else:
                seen_other += 1
                assert "cause" not in r, (aid, crit, r)
    assert seen_na >= 10 and seen_other >= 10


def test_na_causes_are_well_formed_slugs_keyed_by_registered_criteria():
    slug = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
    assert ac.NA_CAUSES
    for crit, causes in ac.NA_CAUSES.items():
        assert crit in ac.CRITERION_REGISTRY, crit
        assert causes and len(set(causes)) == len(causes), crit
        for c in causes:
            assert slug.match(c), (crit, c)


# ───────────────────────── (2) the rollup keys the rule id by cause ─────────────────────────

def _na(cause="__absent__"):
    r = dict(v=NA, measured="m")
    if cause != "__absent__":
        r["cause"] = cause
    return r


def _build_ms(**over):
    ms = {c: dict(v="PASS", measured="m") for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Build"}
    ms.update(over)
    return ms


def _chk(ms, crit="Build.registered", layer="L2"):
    cell = ac.rollup_asset(layer, ms)["Build"]
    return cell, next(c for c in cell["checks"] if c["criterion"] == crit)


def test_a_cause_becomes_the_rule_id_and_an_undeclared_one_reads_no_detector():
    cell, c = _chk(_build_ms(**{"Build.registered": _na("no-writer-registry-agrees")}))
    assert cell["v"] == "NO_DETECTOR"
    assert c["v"] == "NO_DETECTOR" and c["state"] == "MEASURED"
    assert c["rule_id"] == "Build.registered#measured:no-writer-registry-agrees"
    assert c["cause"] == "no-writer-registry-agrees"
    assert "N/A rule undecided" in c["reason"]


def test_a_declared_cause_rule_releases_only_that_cause(monkeypatch):
    rid = "Build.registered#measured:no-writer-registry-agrees"
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {rid: "N-22/test"})
    cell, c = _chk(_build_ms(**{"Build.registered": _na("no-writer-registry-agrees")}))
    assert cell["v"] == "PASS" and c["v"] == NA and c["decision"] == "N-22/test" and c["rule_id"] == rid
    assert c["cause"] == "no-writer-registry-agrees"


def test_one_declared_cause_does_not_release_another_cause_of_the_same_criterion(monkeypatch):
    """The review's finding: one id per criterion released EVERY measured N/A of it."""
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Build.target#measured:service-no-target-table": "N-22/test"})
    _, served = _chk(_build_ms(**{"Build.target": _na("service-no-target-table")}), "Build.target")
    _, other = _chk(_build_ms(**{"Build.target": _na("no-writer-no-target-table")}), "Build.target")
    assert served["v"] == NA
    assert other["v"] == "NO_DETECTOR" and "undecided" in other["reason"]


def test_the_retired_uncaused_id_releases_nothing(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Build.registered#measured": "N-22/test"})
    _, with_cause = _chk(_build_ms(**{"Build.registered": _na("no-writer-registry-agrees")}))
    _, without = _chk(_build_ms(**{"Build.registered": _na()}))
    assert with_cause["v"] == "NO_DETECTOR" and without["v"] == "NO_DETECTOR"


def test_na_without_a_cause_reads_no_detector_even_when_every_id_is_declared(monkeypatch):
    every = {f"{c}#measured": "d" for c in ac.CRITERION_REGISTRY}
    every.update({f"{c}#measured:{k}": "d" for c, ks in ac.NA_CAUSES.items() for k in ks})
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", every)
    cell, c = _chk(_build_ms(**{"Build.registered": _na()}))
    assert cell["v"] == "NO_DETECTOR" and c["v"] == "NO_DETECTOR"
    assert "N/A without a declared cause" in c["reason"]
    assert c.get("rule_id") is None and c.get("decision") is None


@pytest.mark.parametrize("bad", [None, "", "   ", "\t\n", 5, 1.5, True, ["no-writer-registry-agrees"],
                                 {"x": 1}, b"no-writer-registry-agrees"])
def test_an_empty_blank_or_non_str_cause_is_no_cause(monkeypatch, bad):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {f"Build.registered#measured:{k}": "d"
                                                  for k in ac.NA_CAUSES["Build.registered"]})
    cell, c = _chk(_build_ms(**{"Build.registered": _na(bad)}))
    assert cell["v"] == "NO_DETECTOR" and c["v"] == "NO_DETECTOR"
    assert "N/A without a declared cause" in c["reason"]


@pytest.mark.parametrize("bad", [" no-writer-registry-agrees", "no-writer-registry-agrees ", "No-Writer",
                                 "a:b", "a#b", "a b", "-lead", "x/y"])
def test_a_malformed_cause_is_not_a_slug_and_reads_as_no_cause(monkeypatch, bad):
    """A cause that could collide with the id separators, or carries whitespace/case, is not honoured (and is
    never silently normalised into a different id)."""
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Build.registered#measured:no-writer-registry-agrees": "d"})
    _, c = _chk(_build_ms(**{"Build.registered": _na(bad)}))
    assert c["v"] == "NO_DETECTOR" and "N/A without a declared cause" in c["reason"]


def test_a_well_formed_cause_the_registry_does_not_list_is_not_honoured(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Build.registered#measured:invented": "d"})
    cell, c = _chk(_build_ms(**{"Build.registered": _na("invented")}))
    assert cell["v"] == "NO_DETECTOR" and c["v"] == "NO_DETECTOR"
    assert "not a registered cause" in c["reason"]


def test_a_cause_on_a_non_na_record_is_ignored_and_changes_nothing(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Build.registered#measured:no-writer-registry-agrees": "d"})
    ms = _build_ms(**{"Build.registered": dict(v="FAIL", measured="m", cause="no-writer-registry-agrees")})
    cell, c = _chk(ms)
    assert cell["v"] == "FAIL" and c["v"] == "FAIL" and "cause" not in c


def test_a_gate_is_na_only_when_every_check_is_na_by_a_declared_cause(monkeypatch):
    crits = [c for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Idem"]
    ms = {c: _na("no-writer-registry-agrees") for c in crits}
    assert ac.rollup_asset("L2", ms)["Idem"]["v"] == "NO_DETECTOR"
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {f"{c}#measured:no-writer-registry-agrees": "d" for c in crits})
    assert ac.rollup_asset("L2", ms)["Idem"]["v"] == NA
    ms2 = {c: _na() for c in crits}
    assert ac.rollup_asset("L2", ms2)["Idem"]["v"] == "NO_DETECTOR"


# ───────────────────────── (3) registry revision discipline ─────────────────────────

def test_the_fingerprint_covers_the_causes(monkeypatch):
    fp = ac.registry_fingerprint()
    monkeypatch.setattr(ac, "NA_CAUSES", {**ac.NA_CAUSES, "Build.registered": ac.NA_CAUSES["Build.registered"] + ("x",)})
    assert ac.registry_fingerprint() != fp


def test_the_cause_encoding_bumped_the_registry_revision():
    assert ac.REGISTRY_REVISION >= 2, "what a cell means changed (rule ids are cause-keyed): revision must be bumped"


def test_na_rule_decisions_is_still_empty_and_would_only_hold_well_formed_ids():
    assert ac.NA_RULE_DECISIONS == {}, "the N-22 rule table is not approved: nothing may be declared"
    # the standing invariant for when it is filled: every `#measured` id is crit#measured:<registered cause>
    for rid in ac.NA_RULE_DECISIONS:
        if "#measured" in rid:
            crit, _, cause = rid.partition("#measured:")
            assert cause in ac.NA_CAUSES.get(crit, ()), rid


# ───────────────────────── (4) the saved census: nothing can read N/A ─────────────────────────

def test_saved_census_n_a_records_have_no_cause_and_no_cell_reads_na():
    """The committed cell fixture (and the six saved census JSONs) predate the cause: every N/A in them reads
    'N/A without a declared cause' -> NO_DETECTOR, exactly the NO_DETECTOR an N/A read before (empty rule set)."""
    n_na = 0
    for layer, assets in FIXTURE["layers"].items():
        for aid, cells in assets.items():
            ms = {}
            for crit, v in cells.items():
                if crit in ac.CRITERION_REGISTRY:
                    ms[crit] = dict(v=v, measured="fixture")
                    n_na += v == NA
            for gate, cell in ac.rollup_asset(layer, ms).items():
                assert cell["v"] != NA, (layer, aid, gate)
                for c in cell["checks"]:
                    if c["state"] == "MEASURED" and ms.get(c["criterion"], {}).get("v") == NA:
                        assert c["v"] == "NO_DETECTOR"
                        assert "N/A without a declared cause" in c["reason"]
    assert n_na > 0


# ───────────────────────── (5) a per-asset detector's N/A has no inspector cause ─────────────────────────

def test_carr_detector_na_from_a_detector_script_carries_no_cause(monkeypatch, tmp_path):
    """`_run_carriage_detector` adopts a D1/D2/D3 detector script's verdict. The script names no inspector cause
    (and one it tried to smuggle in its output is not carried): its N/A reads 'N/A without a declared cause'."""
    det = tmp_path / "detectors"
    det.mkdir()
    (det / "bg_x_D1.py").write_text(
        "import json\nprint(json.dumps(dict(verdict='N/A', measured='nothing downstream', "
        "cause='no-carriage')))\n")
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    rec = ac._run_carriage_detector("bg_x")
    assert rec["v"] == NA and "cause" not in rec
    cell = ac.rollup_asset("L2", {"Carr.detector": rec})["Carr"]
    chk = next(c for c in cell["checks"] if c["criterion"] == "Carr.detector")
    assert chk["v"] == "NO_DETECTOR" and "N/A without a declared cause" in chk["reason"]
