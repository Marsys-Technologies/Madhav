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
                        lambda d, t, **kw: dict(cap) if cap is not None else dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=48, full=list(c), never=[], note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)
    monkeypatch.setattr(ac, "idem_scan", lambda *a, **k: ("PASS", ["stub"]))
    monkeypatch.setattr(ac, "contract_scan", lambda a, f: ("PASS", []))

    def fake_psql(sql, sep="\x1f", timeout=None):
        if "format_type(a.atttypid" in sql:                 # C2(ii): the citation column's type
            return [["text"]]
        if "jsonb_build_object('rows'" in sql:              # C2(ii): rows / NULL / placeholder counts, one read
            return [['{"rows":48,"null":0,"placeholder":0}']]
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
    ("dens-no-module", "Dens.served", "no-served-surface",
     {"x": _reg_row("x")}, dict(cap=dict(scanned=True, modules=[], density=0, note=""))),
    ("exercised-never-run", "Build.exercised", "never-run-no-writer",
     {"x": _reg_row("x")}, {}),
    ("exercised-never-executed", "Build.exercised", "never-executed-no-writer",
     {"x": _reg_row("x")}, dict(hist={"x": _h_unstarted()})),
    # F5 (SS N-65): `never-run` needs the history source demonstrably present: another asset of the census has rows
    ("history-never-run", "Build.history", "never-run",
     {"x": _reg_row("x"), "y": _reg_row("y")}, dict(hist={"y": _h_unstarted()})),
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


# ───────────────────────── (1b) no registered cause is unused ─────────────────────────
# NA_CAUSES is what a declared rule id may name, and it is fingerprinted. A cause registered with no emitting site is
# a rule the inspector can never trigger: it would read as coverage in the N-22 table and do nothing. Two detectors:
#   (a) SOURCE SCAN: every slug in NA_CAUSES is a literal cause argument of some `_na(...)` call in asset_census.py
#       (an ast walk, so a slug chosen by a conditional expression counts for each branch);
#   (b) HARNESS: executing the offline sites (SITES + the Earn classifier cases) observes every (criterion, cause)
#       pair in NA_CAUSES, so the pair is emitted under that criterion, not just somewhere.

import ast  # noqa: E402

EARN_CASES = [
    None,
    dict(disposition="skip_no_delta", has_writer=True, reached_completion_write=True),
    dict(disposition="", has_writer=False, state="error", reached_completion_write=False),
    dict(disposition="build", has_writer=True, state="error", reached_completion_write=False),
]


def _scanned_cause_slugs(src: str) -> set:
    """Every str literal inside the cause argument (2nd positional, or cause=) of a `_na(...)` call."""
    out = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_na":
            arg = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "cause"), None)
            if arg is not None:
                out |= {n.value for n in ast.walk(arg) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    return out


def _unemitted(src: str, na_causes: dict) -> set:
    scanned = _scanned_cause_slugs(src)
    return {(c, k) for c, ks in na_causes.items() for k in ks if k not in scanned}


ASSET_CENSUS_SRC = (HERE.parent / "asset_census.py").read_text(encoding="utf-8")


def test_every_registered_cause_has_an_emitting_site_in_the_source():
    assert _unemitted(ASSET_CENSUS_SRC, ac.NA_CAUSES) == set()


def test_the_scanner_finds_an_unused_registered_cause():
    """Mutants of the scanner's input: each must be reported (a scan that cannot fail proves nothing)."""
    assert _unemitted(ASSET_CENSUS_SRC, {**ac.NA_CAUSES, "Build.history": ac.NA_CAUSES["Build.history"] + ("ghost",)}) \
        == {("Build.history", "ghost")}
    mutated = ASSET_CENSUS_SRC.replace('"no-declared-dependencies")', '"nodeps")')
    assert mutated != ASSET_CENSUS_SRC
    assert _unemitted(mutated, ac.NA_CAUSES) == {("Build.dep_liveness", "no-declared-dependencies")}
    # a slug that appears only in a comment, a string, or a non-_na call is not an emitting site
    decoy = "def f():\n    # _na('x', 'ghost')\n    s = 'ghost'\n    return dict(cause='ghost')\n"
    assert _unemitted(decoy, {"C": ("ghost",)}) == {("C", "ghost")}
    # ... while a conditional cause counts for both branches, and cause= counts
    cond = "x = _na('t', 'a' if p else 'b')\ny = _na('t', cause='c')\n"
    assert _unemitted(cond, {"C": ("a", "b", "c")}) == set()


def test_every_registered_cause_is_observed_emitted_under_its_criterion(monkeypatch, tmp_path):
    observed = set()
    for _sid, crit, _cause, reg, kw in SITES:
        rec = _m(monkeypatch, tmp_path, reg, **kw)["x"][crit]
        assert rec["v"] == NA, (crit, rec)
        observed.add((crit, rec["cause"]))
    _blk = dict(declared=True, registry_has_writer=False, register_files=0, register_mentions=[])
    rec = ac.earn_build_record_no_writer(dict(v="N/A", cause="never-attempted", measured="m"), {}, _blk)        # SS 2026-10-05: the no-writer / static release
    assert rec["v"] == NA, rec
    observed.add(("Earn.build_record", rec["cause"]))
    for _c in ac.NO_TABLE_CRITERIA:                          # SS 2026-10-05 no-table-no-prose: emitted by `no_table_records` (tested in test_ss_default_rulings)
        _nt = ac.no_table_records("bg_x", dict(kind="service", has_writer=False, prose_fields=None, no_table=dict(why="the service owns no table here at all", evidence="platform/scripts/seed/asset_registry_seed.ts:465")),
                                   ac.no_table_block(dict(kind="service", has_writer=False, prose_fields=None, no_table=dict(why="the service owns no table here at all", evidence="platform/scripts/seed/asset_registry_seed.ts:465")), "service", False, None, [], 0, []))
        assert _nt[_c]["v"] == NA, _nt[_c]
        observed.add((_c, _nt[_c]["cause"]))
    _uo = ac._na("update-only by declared intent", "update-only-by-intent")
    assert _uo["cause"] in ac.NA_CAUSES["Idem.pattern"]
    observed.add(("Idem.pattern", _uo["cause"]))          # SS 2026-10-05 Idem update-only: emitted by `_measure_idem` (tested in test_ss_idem_update_only)
    # SS 2026-10-05 R-c / R-d: the causes emitted by measure() on the no-writer / service / static assets (tested in test_ss_build_record_no_writer.py and test_ss_rd_service_static.py)
    import test_ss_rd_service_static as rd  # noqa: PLC0415
    rd._stub(monkeypatch, tmp_path, {rd.SVC: rd._row(rd.SVC, "service"), rd.STA: rd._row(rd.STA, "data", deps=["bg_dep"], target_table="bg_static_tbl"), "bg_dep": rd._row("bg_dep", "data", has_writer=True)},
             {**rd.SVC_DECL, **rd.STA_DECL, "bg_dep": {"kind": "data"}})
    _rm = ac.measure("L0")
    for _aid, _crit in ((rd.SVC, "Build.completion"), (rd.SVC, "Build.count_integrity"), (rd.STA, "Build.dep_liveness")):
        _rec = rd._cells(_rm, _aid)[_crit]
        assert _rec["v"] == NA, (_aid, _crit, _rec)
        observed.add((_crit, _rec["cause"]))
    import test_ss_probe_attempts as pa  # noqa: PLC0415
    _pc = pa._measure(monkeypatch, tmp_path, [pa.row()], [pa.rcpt()])                                  # SS 2026-10-05 probe_attempts: Earn.build_record
    assert _pc["v"] == NA, _pc
    observed.add(("Earn.build_record", _pc["cause"]))
    import test_ss_build_record_no_writer as br  # noqa: PLC0415
    br._stub(monkeypatch, tmp_path, ep=500.0, reg_epoch=1000.0)
    _ex = br._cells(ac.measure("L0"))["Build.exercised"]
    assert _ex["v"] == NA, _ex
    observed.add(("Build.exercised", _ex["cause"]))
    _dn_ev = "platform/python-sidecar/pipeline/orchestrator/writers/bg_sky_calendar.py:163"                         # SS N-211: the checked dens_not_served forms emit their two causes
    for _dn, _kw in ((dict(why="no served capability reads this table at all", evidence=_dn_ev), dict(table_shared=False)),
                     (dict(why="the table is shared and the sibling owns its cell", evidence=_dn_ev, owned_by="bg_y"), dict(table_shared=True, owner_row=dict(target_table="t_x")))):
        _rec = ac.dens_not_served_record("bg_sky_calendar", dict(dens_not_served=_dn), "t_x", dict(scanned=True, outside=[], unparsed=[], served_at=[]), **_kw)
        assert _rec["v"] == NA, _rec
        observed.add(("Dens.served", _rec["cause"]))
    for attempt in EARN_CASES:
        rec = ac._grade_earn_cost(attempt, True, None, attempt_linkage_wired=True)[0]
        assert rec["v"] == NA, rec
        observed.add(("Earn.build_record", rec["cause"]))
    pn_decl = {"prose_fields": [], "evidence": {"prose_fields": "w.py:1"}, "prose_none": dict(why="the reviewed reason this declaration is true", closed_columns=[])}
    for crit, rec in ac.grade_prose_none("x", pn_decl, {"t": (["id"], {"id": "integer"}, None)}, "t", {}).items():     # N-150 R1: the checked declared-none form emits the Narr and the Null causes
        assert rec["v"] == NA, rec
        observed.add((crit, rec["cause"]))
    observed.add(("Earn.service_state", ac._service_state_na("data", "data")["cause"]))     # S4/N-72: keyed on the declared kind
    _lw = tmp_path / "lint_w.py"
    _lw.write_text("def f(x):\n    return x\n")
    _ln = ac.narr_lint_scan([_lw], ["citation_human"], dict(why="the writer selects no chart_facts by fact_category", evidence="platform/scripts/governance/asset_census.py:1"))
    assert _ln["v"] == NA, _ln                                                               # N-150 R2: declared lint_none AND the scan agrees
    observed.add(("Narr.lint", _ln["cause"]))
    _src_ev = "platform/scripts/governance/asset_census.py:1"
    for na_form, kw2 in (("no_data", dict(table=None, cols=None)),                               # N-151: the two checked source N/A words
                         ("no_claims", dict(table="t", cols=["id", "name"], prose_record=dict(v=NA, prose_none=dict(checked=True))))):
        got = ac.source_declared_check("x", dict(na=na_form, why="a reviewed reason for this word", evidence=_src_ev), kw2["table"], kw2["cols"],
                                       prose_record=kw2.get("prose_record"))
        assert got["Ldgr.source_presence"]["v"] == NA, got
        observed.add(("Ldgr.source_presence", got["Ldgr.source_presence"]["cause"]))
    for got in (ac.vocab_alias_declared_check("x", dict(na="no_alias_class", why="w", evidence="e:1"), "t", ["id"]),   # S3: the declared N/A words
                ac.ldgr_source_declared_check("x", dict(na="no_classical_claim", why="w", evidence="e:1"), "t", ["id"])):
        for crit, rec in got.items():
            assert rec["v"] == NA, rec
            observed.add((crit, rec["cause"]))
    for car in (dict(nature="derivation", applies="D3", why="w", evidence="e:1"),                           # S2: a declared carriage check
                dict(nature="transcription", applies="D1", citation_state="sourced", why="w", evidence="e:1"),
                dict(nature="ratified_judgment", ruling="N-73", why="w", evidence="e:1"),
                dict(nature="single_derivation", applies="D3", why="w", evidence="e:1", per_witness_values=False),          # N-156: the three declared ceilings
                dict(nature="unverified_transcription", applies="D1", why="w", evidence="e:1", per_witness_values=False),
                dict(nature="not_a_transcription", applies="D1", why="w", evidence="e:1", per_witness_values=False)):          # N-156 C8 (source passed above: K2)
        for crit, rec in ac.carriage_declared_checks("x", car, None, column_types=None, prose_columns=[],
                                                     source=(dict(level="table", kind="K1", citation="BPHS", locus="ch.3", citation_state="sourced") if car["nature"] == "unverified_transcription"
                                                             else dict(level="table", kind="K2", decision_id="N-156"))).items():
            if rec["v"] == NA:
                observed.add((crit, rec["cause"]))
    for crit, rec in ac.carr_checks(dict(declared_terminal_by_construction="writer x.py:1 writes nothing read",
                                         blocking_radius=dict(direct=0, transitive=0),
                                         measured_served=NA)).items():
        assert rec["v"] == NA, rec           # E6 item (f): the declared no-carriage candidates on Carr.D1-D3
        observed.add((crit, rec["cause"]))
    import test_sb4_zero_row_convention as zr          # N-149: Count.floor on a chart with a VERIFIED declared zero-row convention
    zr._stub(monkeypatch, tmp_path, zr._reg(), zr.DECL)
    zr._fake(monkeypatch)
    rec = zr._cells(ac.measure("L1"))["Count.floor"]
    assert rec["v"] == NA, rec
    observed.add(("Count.floor", rec["cause"]))
    # N-176 (Vocab.alias, value-keyed) and N-177 (the UNSOURCED_DECLARED residual): emitted by `vocab_values_record` / `grade_unsourced_declared` (tested in test_n176_vocab_values / test_n177_unsourced_declared)
    _vr = ac.vocab_values_record([dict(table="t", column="c", kind="text", rows_sampled=3, complete=True, carries=False, read="whole column")], [], ["t"])
    assert _vr["v"] == NA, _vr
    observed.add(("Vocab.alias", _vr["cause"]))
    _ud = ac.grade_unsourced_declared(dict(columns=[dict(column="c", kinds=["K1"])], why="w", evidence="e:1"), dict(judged=True, carrying=[], lacking=True, marked=False, has_keys=False), "t", {})
    assert _ud["v"] == NA, _ud
    observed.add(("Ldgr.source_presence", _ud["cause"]))
    registered = {(c, k) for c, ks in ac.NA_CAUSES.items() for k in ks}
    assert registered - observed == set(), "registered but never emitted by the offline harness"
    assert observed - registered == set(), "emitted but not registered"


def test_the_harness_coverage_check_fails_for_an_unused_registered_cause(monkeypatch, tmp_path):
    monkeypatch.setitem(ac.NA_CAUSES, "Build.history", ac.NA_CAUSES["Build.history"] + ("ghost",))
    with pytest.raises(AssertionError):
        test_every_registered_cause_is_observed_emitted_under_its_criterion(monkeypatch, tmp_path)


# ───────────────────────── (2) the rollup keys the rule id by cause ─────────────────────────

def _na(cause="__absent__"):
    r = dict(v=NA, measured="m", no_writer=dict(declared=True, registry_has_writer=False, register_files=0, register_mentions=[]))     # N-150 R5: the three facts a no-writer release rests on (inert for any other cause)
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


def test_a_cause_becomes_the_rule_id_and_an_undeclared_one_reads_no_detector(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {})                 # N-150 R5 declares this rule in production: the undeclared reading is the emptied table
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
    """Two layers of defence: the validator refuses the declaration outright (see the (3b) tests), and, were it
    ever bypassed, the per-check decision still does not read the retired id."""
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Build.registered#measured": "N-22/test"})
    with pytest.raises(ValueError):
        _chk(_build_ms(**{"Build.registered": _na("no-writer-registry-agrees")}))
    with_cause = ac._check_contribution("Build.registered", "L2", _na("no-writer-registry-agrees"), None)
    without = ac._check_contribution("Build.registered", "L2", _na(), None)
    assert with_cause["v"] == "NO_DETECTOR" and without["v"] == "NO_DETECTOR"
    assert not ac._na_released("Build.registered", _na("no-writer-registry-agrees"))


def test_na_without_a_cause_reads_no_detector_even_when_every_id_is_declared(monkeypatch):
    every = {f"{c}#measured:{k}": "d" for c, ks in ac.NA_CAUSES.items() for k in ks}    # every VALID id
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
    # declaring it is refused outright (validate_na_rule_decisions); with no such declaration the N/A is undecided,
    # and the per-check "not a registered cause" guard still holds if the validator were ever bypassed.
    _, c = _chk(_build_ms(**{"Build.registered": _na("invented")}))
    assert c["v"] == "NO_DETECTOR" and "not a registered cause" in c["reason"]
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Build.registered#measured:invented": "d"})
    with pytest.raises(ValueError):
        _chk(_build_ms(**{"Build.registered": _na("invented")}))
    c = ac._check_contribution("Build.registered", "L2", _na("invented"), None)
    assert c["v"] == "NO_DETECTOR" and "not a registered cause" in c["reason"]


def test_a_cause_on_a_non_na_record_is_ignored_and_changes_nothing(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Build.registered#measured:no-writer-registry-agrees": "d"})
    ms = _build_ms(**{"Build.registered": dict(v="FAIL", measured="m", cause="no-writer-registry-agrees")})
    cell, c = _chk(ms)
    assert cell["v"] == "FAIL" and c["v"] == "FAIL" and "cause" not in c


def test_a_gate_is_na_only_when_every_check_is_na_by_a_declared_cause(monkeypatch):
    crits = [c for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Idem"]
    ms = {c: _na("no-writer-registry-agrees") for c in crits}
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {})                 # N-150 R5 declares this rule in production
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


def test_na_rule_decisions_is_exactly_the_approved_set():
    import test_e6_na_r01_03 as r13
    assert set(ac.NA_RULE_DECISIONS) == r13.DECLARED_IDS, "only the N-65 approved rules may be declared"
    ac.validate_na_rule_decisions()    # and the production table is well-formed


# ───────────────────────── (3b) the declared rule table is validated, not trusted ─────────────────────────
# The standing invariant "every `#measured` id is <crit>#measured:<registered cause>" used to loop over the EMPTY
# production dict and so checked nothing. It is now an enforced function, called by rollup_asset and emit_gaps,
# and tested here against monkeypatched declarations.

VALID_DECLS = {
    "Build.registered#measured:no-writer-registry-agrees": "N-22/test",
    "Build.target#measured:service-no-target-table": "N-22/test",
    "Earn.build_record#measured:no-registered-writer": "N-22/test",
    "Ldgr.source_presence#columns_any": "N-22/test",          # the fact-disproved applicability form
}

BAD_DECLS = [
    pytest.param("Build.registered#measured", id="retired-uncaused-id"),
    pytest.param("Build.registered#measured:", id="empty-cause"),
    pytest.param("Build.registered#measured:invented", id="unregistered-cause"),
    pytest.param("Build.target#measured:no-writer-registry-agrees", id="cause-registered-for-another-criterion"),
    pytest.param("Nope.crit#measured:no-writer-registry-agrees", id="unregistered-criterion"),
    pytest.param("Build.registered#measured: no-writer-registry-agrees", id="whitespace-in-cause"),
    pytest.param("Build.registered#measured:No-Writer", id="non-slug-cause"),
    pytest.param("Build.registered#columns_any", id="columns_any-rule-on-a-criterion-with-no-column-pattern"),
    pytest.param("Build.registered#asset_kinds", id="asset_kinds-rule-on-a-criterion-with-no-kind-pattern"),
    pytest.param("Build.registered", id="no-rule-suffix"),
    pytest.param("Build.registered#whatever", id="unknown-rule-kind"),
    pytest.param("#measured:no-writer-registry-agrees", id="empty-criterion"),
]


def test_validate_accepts_empty_and_every_well_formed_declaration(monkeypatch):
    ac.validate_na_rule_decisions()
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", dict(VALID_DECLS))
    ac.validate_na_rule_decisions()
    # every registered (criterion, cause) pair is declarable
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {f"{c}#measured:{k}": "d" for c, ks in ac.NA_CAUSES.items() for k in ks})
    ac.validate_na_rule_decisions()


@pytest.mark.parametrize("bad", BAD_DECLS)
def test_validate_rejects_a_malformed_declaration_even_beside_valid_ones(monkeypatch, bad):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {**VALID_DECLS, bad: "N-22/test"})
    with pytest.raises(ValueError) as e:
        ac.validate_na_rule_decisions()
    assert bad in str(e.value)


@pytest.mark.parametrize("decision", ["", "   ", None, 5, ["N-22"]])
def test_validate_rejects_a_declaration_with_no_decision_id(monkeypatch, decision):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Build.registered#measured:no-writer-registry-agrees": decision})
    with pytest.raises(ValueError):
        ac.validate_na_rule_decisions()


@pytest.mark.parametrize("key", [None, 5, ("Build.registered", "x"), b"Build.registered#measured:x"])
def test_validate_rejects_a_non_str_rule_id(monkeypatch, key):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {key: "N-22/test"})
    with pytest.raises(ValueError):
        ac.validate_na_rule_decisions()


def test_validate_reports_every_bad_id_not_just_the_first(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Build.registered#measured": "d", "Build.target#measured:nope": "d"})
    with pytest.raises(ValueError) as e:
        ac.validate_na_rule_decisions()
    assert "Build.registered#measured" in str(e.value) and "Build.target#measured:nope" in str(e.value)


@pytest.mark.parametrize("bad", BAD_DECLS)
def test_rollup_asset_refuses_a_malformed_declaration(monkeypatch, bad):
    """A bad declaration must fail LOUD where a cell is computed, not sit inert (the retired uncaused id used to
    be silently ignored, which is how a typo'd rule reads as 'declared' in review and does nothing)."""
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {bad: "N-22/test"})
    with pytest.raises(ValueError):
        ac.rollup_asset("L2", {})
    with pytest.raises(ValueError):
        ac.rollup_census(dict(layer="L2", assets=[dict(asset_id="x", layer="L2", measurements={})]))


@pytest.mark.parametrize("bad", BAD_DECLS)
def test_emit_gaps_refuses_a_malformed_declaration_and_writes_nothing(monkeypatch, tmp_path, bad):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {bad: "N-22/test"})
    cen = dict(layer="L0", assets=[dict(asset_id="bg_x", measurements={"Build.registered": dict(v="FAIL", measured="m")})])
    with pytest.raises(ValueError):
        ac.emit_gaps(cen)
    assert not (tmp_path / "asset_gaps.jsonl").exists() or (tmp_path / "asset_gaps.jsonl").read_text() == ""


def test_valid_declarations_do_not_stop_the_rollup_or_emit(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", dict(VALID_DECLS))
    assert ac.rollup_asset("L2", {})["Build"]["v"] == "NO_DETECTOR"
    cen = dict(layer="L0", assets=[dict(asset_id="bg_x", measurements={"Build.registered": dict(v="FAIL", measured="m")})])
    assert ac.emit_gaps(cen)[0] == 1


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
    cell = ac.rollup_asset("L2", {"Carr.D1": rec})["Carr"]      # E6 item i: Carr.detector is retired; D1 is the check a _D1 script feeds
    chk = next(c for c in cell["checks"] if c["criterion"] == "Carr.D1")
    assert chk["v"] == "NO_DETECTOR" and "N/A without a declared cause" in chk["reason"]
