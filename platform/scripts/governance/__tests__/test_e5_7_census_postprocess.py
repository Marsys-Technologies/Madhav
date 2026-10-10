"""test_e5_7_census_postprocess.py: the census post-processor (`census_postprocess.py`, N-152: one line per asset, no ledger).

Positive fixtures: the three committed rev-25 L0/L1/L2 census files (read directly; no database).  Synthetic fixtures: tiny layer files
built here, one seeded defect per refusal / per certification rule.  The MUTANTS list at the bottom names each source mutation the
suite must kill (the suite is re-run against a mutated copy of the module via CENSUS_PP_PATH; see `_load`).  Offline: no database, no network.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
CENSUS_DIR = REPO / "00_ARCHITECTURE" / "control" / "census"
REAL = [CENSUS_DIR / f"asset_census_2026-10-04T{t}+0530.json" for t in ("193639", "194909", "195251")]


def _load():
    p = os.environ.get("CENSUS_PP_PATH") or str(HERE.parent / "census_postprocess.py")
    spec = importlib.util.spec_from_file_location("census_postprocess_under_test", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


cp = _load()
FP = "ab" * 32
DB = {"schema": "nikasha_db_identity/1", "database": "amjis", "system_id_sha256": "cd" * 32}
CRIT = ["Build.history", "Idem.pattern", "Carr.D1", "Carr.D2", "Carr.D3", "Ldgr.source_presence"]      # a 6-criterion fixture registry (N-233 R3: a ruled N/A is checked against the engine's closed rule list AND its own criterion, so the fixture carries the Carr rows)


def cell(name, v="PASS", state="MEASURED", **extra):
    return {"criterion": name, "v": v, "state": state, "reason": "measured", **extra}


def ruled(name):
    """A RULED N/A the engine's closed list backs (N-233 R3): the first measured rule of the criterion, with the engine's own decision text."""
    rid = next(r for r in cp.engine_rule_decisions() if r.startswith(name + "#measured:"))
    return cell(name, "N/A", rule_id=rid, decision=cp.engine_rule_decisions()[rid])


def eng(rid, name=None):
    """A ruled N/A cell for engine rule id `rid` with the engine's decision text."""
    return cell(name or rid.split("#")[0], "N/A", rule_id=rid, decision=cp.engine_rule_decisions()[rid])


def layer_file(layer, assets, rev=25, fp=FP, db=DB, **head_extra):
    """assets: aid -> {criterion: cell}; the file has the real shape: head with assets[].measurements + rollup.layers."""
    roll = {aid: {"G": dict(gate="G", v="PASS", registry_revision=rev, registry_fingerprint=fp, checks=list(cells.values()))}
            for aid, cells in assets.items()}
    head = dict(layer=layer, registry_revision=rev, registry_fingerprint=fp, db_identity=db,
                assets=[dict(asset_id=aid, measurements={n: dict(v=c["v"], measured=f"measured text of {n}") for n, c in cells.items()})
                        for aid, cells in assets.items()], **head_extra)
    head.setdefault("census_target", dict(declared="production", warning="w"))      # SS N-332: every current census states its target (production unless a test says otherwise)
    head.setdefault("eval_copy_probe", dict(checked=True, marker_present=False))      # SS N-327: every census from the current tool carries the looked-for copy marker (absent = read as production)
    return {layer: head, "rollup": dict(registry_revision=rev, registry_fingerprint=fp, layers={layer: roll}), "rollup_excluded": {layer: {}}}


def good_cells(**over):
    c = {n: cell(n) for n in CRIT}
    c.update(over)
    return c


def world(tmp_path, spec=None, **kw):
    """three layer files: L0 {a1,a2}, L1 {b1}, L2 {c1}; spec: aid -> cells.  Returns (paths, kw for main)."""
    spec = spec or {}
    layers = {"L0": ["a1", "a2"], "L1": ["b1"], "L2": ["c1"]}
    paths = []
    for l, aids in layers.items():
        p = tmp_path / f"census_{l}.json"
        p.write_text(json.dumps(layer_file(l, {a: spec.get(a, good_cells()) for a in aids}, **kw.get(l, {}))))
        paths.append(p)
    return paths


def run(paths, tmp_path, *extra, date="2026-10-05"):
    out = tmp_path / "out"
    rc = cp.main(["--census", *map(str, paths), "--date", date, "--out-dir", str(out), *extra])
    return rc, out


def refused(capsys, paths, tmp_path, needle, *extra):
    rc, out = run(paths, tmp_path, *extra)
    err = capsys.readouterr().err
    assert rc == 2 and err.startswith("REFUSED: ") and err.count("\n") == 1 and needle in err, err
    assert not out.exists()      # a refusal writes nothing


def rewrite(path, fn):
    d = json.loads(path.read_text())
    fn(d)
    path.write_text(json.dumps(d))


# ───────────────────────────── positive: the real rev-25 files ─────────────────────────────

@pytest.fixture(scope="module")
def real_run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("real")
    rc, out = run(REAL, tmp, "--assets-expected", "82", "--criteria-expected", "25", "--bar", "strict", "--allow-legacy-census")      # N-268: the older strict reading is what these rev-25 expectations were written against
    return rc, out, json.loads((out / "FIX_LIST.json").read_text())


def test_real_files_zero_certified_82_assets(real_run):
    rc, out, fix = real_run
    assert rc == 0 and fix["assets"] == 82 and len(fix["fix_list"]) == 82
    assert json.loads((out / "CERTIFIED_LIST.json").read_text())["certified"] == []
    assert fix["registry_revision"] == 25


def test_real_files_verdict_totals_match_plan(real_run):
    """ENGINE_100_PLAN_L0_L2 cell totals: NO_DETECTOR / FAIL / PARTIAL per layer (N-154: a ruled N/A on Build.history counts, so no N/A item)."""
    _, _, fix = real_run
    n = {}
    for items in fix["fix_list"].values():
        for i in items:
            n[(i["layer"], i["verdict"])] = n.get((i["layer"], i["verdict"]), 0) + 1
    assert n == {("L0", "NO_DETECTOR"): 446, ("L0", "FAIL"): 36, ("L0", "PARTIAL"): 33,
                 ("L1", "NO_DETECTOR"): 149, ("L1", "FAIL"): 2, ("L1", "PARTIAL"): 71,
                 ("L2", "NO_DETECTOR"): 187, ("L2", "FAIL"): 12, ("L2", "PARTIAL"): 104}
    assert not any(i["cause_class"] == cp.UNCLASSIFIED for items in fix["fix_list"].values() for i in items)


def test_real_files_deterministic(tmp_path, real_run):
    rc, out2 = run(REAL, tmp_path, "--bar", "strict", "--allow-legacy-census")
    _, out1, _ = real_run
    assert rc == 0
    for f in ("CERTIFIED_LIST.md", "CERTIFIED_LIST.json", "FIX_LIST.md", "FIX_LIST.json"):
        assert (out1 / f).read_bytes() == (out2 / f).read_bytes()
    assert not re.search(r"\d{2}:\d{2}:\d{2}", (out1 / "FIX_LIST.md").read_text())      # no timestamps in the body


def test_real_file_order_independent(tmp_path, real_run):
    rc, out2 = run(list(reversed(REAL)), tmp_path, "--bar", "strict", "--allow-legacy-census")
    assert rc == 0 and (out2 / "FIX_LIST.json").read_bytes() == (real_run[1] / "FIX_LIST.json").read_bytes()


# ───────────────────────────── the cause-class mapping ─────────────────────────────

@pytest.mark.parametrize("crit,v,state,text,cls", [
    ("Narr.lint", "NO_DETECTOR", "MEASURED", "NO_DETECTOR — prose_fields is undeclared for this asset", "(b) declaration missing: prose_fields"),
    ("Vocab.alias", "NO_DETECTOR", "NOT_APPLICABLE", "N/A rule undecided (N-22): columns match none", "(c) ruling or declaration"),
    ("Ldgr.source_presence", "NO_DETECTOR", "APPLIES", "applicability undecidable", "(c) ruling or declaration"),
    ("Earn.build_record", "NO_DETECTOR", "MEASURED", "NO_DETECTOR — unclassified NULL (completion w", "(d) needs a rebuild"),
    ("Earn.build_record", "NO_DETECTOR", "MEASURED", "no recorded duration for the run", "(d) needs a rebuild"),
    ("Carr.D1", "NO_DETECTOR", "APPLIES", "not measured (applies)", "(a) detector/declaration (carriage)"),
    ("Ldgr.source_presence", "NO_DETECTOR", "APPLIES", "not measured (applies)", "(a) detector"),         # same text off Carr.*: plain detector
    ("Build.completion", "FAIL", "MEASURED", "build record rows_written=10 disagrees with live=17", "(e) defect in data or code"),
    ("Null.blank_rows", "PARTIAL", "MEASURED", "no blank row among the checkable rows", "(e) defect in data or code"),
    ("Dens.served", "NO_DETECTOR", "MEASURED", "NO_DETECTOR — no module in the serving roots", "(a) detector"),
    ("Build.history", "FAIL", "APPLIES", "x", "(a) detector"),                                         # FAIL not measured with data: detector
    ("Null.blank_rows", "PARTIAL", "MEASURED", "no blank row; writer literal fallbacks are not measured, so this is never PASS", "(a) detector"),
    ("Narr.fidelity_test", "PARTIAL", "MEASURED", "tests call the builder; structural only, never PASS", "(a) detector"),
    ("Narr.fidelity_test", "PARTIAL", "MEASURED", "whether the assertion grades the sentence is not read, so this never reads PASS", "(a) detector"),
    ("Idem.pattern", "INCONCLUSIVE", "MEASURED", "INCONCLUSIVE: no row data was read", cp.UNCLASSIFIED),   # unknown verdict: visible
    ("Idem.pattern", "N/A", "MEASURED", "no rule id on this N/A", "(c) ruling or declaration"),
])
def test_classify(crit, v, state, text, cls):
    assert cp.classify(crit, v, state, text) == cls


def test_unknown_text_is_visible_not_dropped(tmp_path, capsys):
    paths = world(tmp_path, {"a1": good_cells(**{"Idem.pattern": cell("Idem.pattern", "WEIRD")})})
    rc, out = run(paths, tmp_path)
    fix = json.loads((out / "FIX_LIST.json").read_text())["fix_list"]
    assert [i["cause_class"] for i in fix["a1"]] == [cp.UNCLASSIFIED]
    assert "(?) unclassified" in (out / "FIX_LIST.md").read_text()


def test_cause_text_prefers_measurement_then_rollup_reason(tmp_path):
    paths = world(tmp_path, {"a1": good_cells(**{"Idem.pattern": cell("Idem.pattern", "FAIL"),
                                                 "Carr.D1": cell("Carr.D1", "NO_DETECTOR", "APPLIES", reason="not measured (applies)")})})
    rc, out = run(paths, tmp_path)
    items = {i["criterion"]: i for i in json.loads((out / "FIX_LIST.json").read_text())["fix_list"]["a1"]}
    assert items["Idem.pattern"]["cause"] == "measured text of Idem.pattern"       # MEASURED: the measurements entry
    assert items["Carr.D1"]["cause"] == "not measured (applies)"                    # not measured: the rollup reason
    assert items["Carr.D1"]["cause_class"] == "(a) detector/declaration (carriage)"


KNOWN = pathlib.Path("/Users/Dev/suvarna-evidence/E5.7/known_findings.json")


@pytest.mark.skipif(not (KNOWN.exists() and all(p.exists() for p in REAL)), reason="the E5.7 known-findings evidence file is not on this machine (CI)")
def test_findings_accepts_exactly_the_shape_of_the_known_findings_file(tmp_path):
    """The reviewed known_findings.json is {asset: 'one sentence'} (31 assets): `--findings` takes it as is and each sentence lands on that asset's line, verbatim."""
    raw = json.loads(KNOWN.read_text(encoding="utf-8"))
    assert isinstance(raw, dict) and len(raw) == 31 and all(isinstance(k, str) and isinstance(v, str) and v for k, v in raw.items())
    rc, out = run(REAL, tmp_path, "--assets-expected", "82", "--criteria-expected", "25", "--findings", str(KNOWN), "--allow-legacy-census")
    assert rc == 0                                                                          # accepted whole: no refusal for the real file against the real census
    merged = tmp_path / "merged.json"                                                      # a sentence lands only on a CERTIFIED asset (none is at rev 25): prove the flow with a synthetic certified asset
    merged.write_text(json.dumps({**raw, "a1": "PG339 citation finding"}))
    (tmp_path / "w").mkdir()
    paths = world(tmp_path / "w", {"a1": good_cells()})
    rc, out2 = run(paths, tmp_path / "w", "--assets-expected", "4", "--criteria-expected", "6", "--findings", str(merged))
    cert = json.loads((out2 / "CERTIFIED_LIST.json").read_text())
    assert rc == 0 and cert["certified"][0]["asset"] == "a1" and cert["certified"][0]["findings"] == "PG339 citation finding"


# ───────────────────────────── the CERTIFIED rule ─────────────────────────────

def test_all_pass_and_ruled_na_certifies(tmp_path):
    paths = world(tmp_path, {"a1": good_cells(**{"Carr.D1": ruled("Carr.D1"), "Ldgr.source_presence": ruled("Ldgr.source_presence")})})
    (tmp_path / "f.json").write_text(json.dumps({"a1": "PG339 citation finding"}))
    rc, out = run(paths, tmp_path, "--assets-expected", "4", "--criteria-expected", "6", "--findings", str(tmp_path / "f.json"))
    cert = json.loads((out / "CERTIFIED_LIST.json").read_text())
    assert rc == 0 and [c["asset"] for c in cert["certified"]] == ["a1", "a2", "b1", "c1"]
    a1 = cert["certified"][0]
    assert (a1["measured_pass"], a1["ruled_na"], a1["revision"], a1["date"], a1["findings"]) == (4, 2, 25, "2026-10-05", "PG339 citation finding")
    assert cert["certified"][1]["findings"] == "" and cert["certified"][1]["measured_pass"] == 6
    sha = hashlib.sha256(paths[0].read_bytes()).hexdigest()[:12]
    assert a1["census"] == f"census_L0.json#{sha}"
    assert "PG339 citation finding" in (out / "CERTIFIED_LIST.md").read_text()
    assert json.loads((out / "FIX_LIST.json").read_text())["fix_list"] == {}


def test_mutant_ruled_na_without_rule_id_counted_as_certified(tmp_path):
    bad = cell("Carr.D1", "N/A", decision="N-1")
    rc, out = run(world(tmp_path, {"a1": good_cells(**{"Carr.D1": bad})}), tmp_path)
    assert "a1" in json.loads((out / "FIX_LIST.json").read_text())["fix_list"]


def test_mutant_ruled_na_without_decision_counted_as_certified(tmp_path):
    bad = cell("Carr.D1", "N/A", rule_id="Carr.D1#x")
    rc, out = run(world(tmp_path, {"a1": good_cells(**{"Carr.D1": bad})}), tmp_path)
    assert "a1" in json.loads((out / "FIX_LIST.json").read_text())["fix_list"]


@pytest.mark.parametrize("v", ["NO_DETECTOR", "PARTIAL", "FAIL", "INCONCLUSIVE", "UNKNOWN", ""])
def test_mutant_non_pass_verdict_counted_as_pass(tmp_path, v):
    rc, out = run(world(tmp_path, {"a1": good_cells(**{"Idem.pattern": cell("Idem.pattern", v)})}), tmp_path)
    fix = json.loads((out / "FIX_LIST.json").read_text())["fix_list"]
    assert list(fix) == ["a1"] and fix["a1"][0]["verdict"] == v
    assert [c["asset"] for c in json.loads((out / "CERTIFIED_LIST.json").read_text())["certified"]] == ["a2", "b1", "c1"]


def test_ceilings_come_from_the_ruled_na_rule_ids_and_are_counted(tmp_path):
    d3 = eng("Carr.D3#measured:single-derivation")
    d1 = eng("Carr.D1#measured:transcription-not-verified")
    other = eng("Ldgr.source_presence#measured:no-data")
    spec = {"a1": good_cells(**{"Carr.D3": d3, "Carr.D1": d1}), "a2": good_cells(**{"Ldgr.source_presence": other}), "b1": good_cells(**{"Carr.D3": d3})}
    rc, out = run(world(tmp_path, spec), tmp_path)
    cert = {c["asset"]: c for c in json.loads((out / "CERTIFIED_LIST.json").read_text())["certified"]}
    assert rc == 0 and cert["a1"]["ceilings"] == ["Carr: single-derivation", "D1: unverified transcription"]
    assert cert["a2"]["ceilings"] == [] and cert["b1"]["ceilings"] == ["Carr: single-derivation"] and cert["c1"]["ceilings"] == []
    md = (out / "CERTIFIED_LIST.md").read_text()
    assert "ceilings: 2 of 4 certified assets are at a declared ceiling (Carr: single-derivation 1; D1: unverified transcription 0; both 1; Ldgr: unsourced (declared) 0; Ratified judgment (N-235) 0)" in md and "Carr: single-derivation; D1: unverified transcription" in md
    assert json.loads((out / "CERTIFIED_LIST.json").read_text())["certified_at_a_ceiling"] == 2


def test_summary_counts_d3_only_d1_only_and_both(tmp_path):
    d3 = eng("Carr.D3#measured:single-derivation")
    d1 = eng("Carr.D1#measured:transcription-not-verified")
    spec = {"a1": good_cells(**{"Carr.D3": d3}), "a2": good_cells(**{"Carr.D1": d1}), "b1": good_cells(**{"Carr.D3": d3, "Carr.D1": d1})}
    rc, out = run(world(tmp_path, spec), tmp_path)
    md = (out / "CERTIFIED_LIST.md").read_text()
    assert "ceilings: 3 of 4 certified assets are at a declared ceiling (Carr: single-derivation 1; D1: unverified transcription 1; both 1; Ldgr: unsourced (declared) 0; Ratified judgment (N-235) 0)" in md


def test_the_ldgr_unsourced_declared_residual_is_a_ceiling_printed_like_the_carr_ceilings(tmp_path):
    """N-177: a ruled N/A under Ldgr.source_presence#measured:unsourced-declared certifies the asset AT the 'Ldgr: unsourced (declared)' ceiling; it prints in the asset's line and in the summary exactly as the
    Carr ceilings do, and the Carr counts are unchanged by it (an asset at the Ldgr ceiling AND the D3 ceiling counts once in each family)."""
    uns = eng("Ldgr.source_presence#measured:unsourced-declared")
    d3 = eng("Carr.D3#measured:single-derivation")
    spec = {"a1": good_cells(**{"Ldgr.source_presence": uns}), "a2": good_cells(**{"Ldgr.source_presence": uns, "Carr.D3": d3}), "b1": good_cells(**{"Carr.D3": d3})}
    rc, out = run(world(tmp_path, spec), tmp_path)
    cert = {c["asset"]: c for c in json.loads((out / "CERTIFIED_LIST.json").read_text())["certified"]}
    assert rc == 0 and cert["a1"]["ceilings"] == ["Ldgr: unsourced (declared)"] and cert["a2"]["ceilings"] == ["Carr: single-derivation", "Ldgr: unsourced (declared)"]
    assert cert["b1"]["ceilings"] == ["Carr: single-derivation"] and cert["c1"]["ceilings"] == []
    md = (out / "CERTIFIED_LIST.md").read_text()
    assert "ceilings: 3 of 4 certified assets are at a declared ceiling (Carr: single-derivation 2; D1: unverified transcription 0; both 0; Ldgr: unsourced (declared) 2; Ratified judgment (N-235) 0)" in md
    assert "Carr: single-derivation; Ldgr: unsourced (declared)" in md
    assert json.loads((out / "CERTIFIED_LIST.json").read_text())["certified_at_a_ceiling"] == 3
    assert cp.CEILING_RULES["Carr.D3#measured:single-derivation"] == "Carr: single-derivation" and cp.CEILING_RULES["Carr.D1#measured:transcription-not-verified"] == "D1: unverified transcription"


def test_d2_is_a_header_line_and_never_a_ceiling(tmp_path):
    d2 = lambda: eng("Carr.D2#measured:no-per-witness-values")
    # every asset ruled N/A on D2 (the fixture registry gets a Carr.D2 row on each asset)
    spec = {a: good_cells(**{"Carr.D2": d2()}) for a in ("a1", "a2", "b1", "c1")}
    rc, out = run(world(tmp_path, spec), tmp_path)
    md = (out / "CERTIFIED_LIST.md").read_text()
    assert "Carr.D2: N/A on every asset (no per-witness values stored, N-156)" in md and "ceilings: 0 of 4" in md
    cert = json.loads((out / "CERTIFIED_LIST.json").read_text())
    assert all(c["ceilings"] == [] for c in cert["certified"]) and cert["carr_d2"] == dict(assets=4, na_no_per_witness=4, other={})


def test_d2_header_states_the_exceptions(tmp_path):
    d2 = eng("Carr.D2#measured:no-per-witness-values")
    spec = {"a1": good_cells(**{"Carr.D2": d2}), "a2": good_cells(**{"Carr.D2": d2}), "b1": good_cells(**{"Carr.D2": cell("Carr.D2", "NO_DETECTOR", "APPLIES")}), "c1": good_cells(**{"Carr.D2": d2})}
    rc, out = run(world(tmp_path, spec), tmp_path)
    md = (out / "CERTIFIED_LIST.md").read_text()
    assert "Carr.D2: ruled N/A (no per-witness values stored, N-156) on 3 of 4 assets; NO_DETECTOR 1 on the rest" in md


def test_not_a_transcription_is_a_plain_na_with_no_ceiling(tmp_path):
    plain = eng("Carr.D1#measured:not-a-transcription")
    rc, out = run(world(tmp_path, {"a1": good_cells(**{"Carr.D1": plain})}), tmp_path)
    cert = {c["asset"]: c for c in json.loads((out / "CERTIFIED_LIST.json").read_text())["certified"]}
    assert cert["a1"]["ceilings"] == [] and cert["a1"]["ruled_na"] == 1                       # certified, counted as a ruled N/A, no ceiling


def test_a_ruled_na_the_engine_declares_but_the_ceiling_list_does_not_name_is_not_a_ceiling(tmp_path):
    odd = eng("Carr.D3#measured:not-the-declared-carriage")
    rc, out = run(world(tmp_path, {"a1": good_cells(**{"Carr.D3": odd})}), tmp_path)
    assert next(c for c in json.loads((out / "CERTIFIED_LIST.json").read_text())["certified"] if c["asset"] == "a1")["ceilings"] == []


def test_build_history_ruled_na_certifies_n154(tmp_path):
    rc, out = run(world(tmp_path, {"a1": good_cells(**{"Build.history": ruled("Build.history")})}), tmp_path)
    assert json.loads((out / "FIX_LIST.json").read_text())["fix_list"] == {}


def test_build_history_unruled_na_or_no_detector_blocks(tmp_path):
    for bad in (cell("Build.history", "N/A"), cell("Build.history", "NO_DETECTOR")):
        rc, out = run(world(tmp_path, {"a1": good_cells(**{"Build.history": bad})}), tmp_path)
        assert list(json.loads((out / "FIX_LIST.json").read_text())["fix_list"]) == ["a1"]


def test_header_records_tool_commit_and_dirty_without_refusing(tmp_path):
    paths = world(tmp_path, L0=dict(tool_commit="400c8556c205dfde", tool_dirty=True), L1=dict(tool_commit=None, tool_dirty=None))
    rc, out = run(paths, tmp_path)
    assert rc == 0
    head = json.loads((out / "FIX_LIST.json").read_text())["tool"]
    assert {"tool_commit": "400c8556c205dfde", "tool_dirty": True} in head and {"tool_commit": None, "tool_dirty": None} in head
    assert "400c8556c(dirty)" in (out / "CERTIFIED_LIST.md").read_text().splitlines()[1]


def test_real_files_header_has_tool_commit(real_run):
    assert real_run[2]["tool"] == [{"tool_commit": "400c8556c205dfde0a386504eef837e710df9a13", "tool_dirty": False}]


def test_real_files_by_design_partials_are_detector_class(real_run):
    items = [i for v in real_run[2]["fix_list"].values() for i in v]
    by_design = [i for i in items if i["verdict"] == "PARTIAL" and re.search(r"never PASS|never reads PASS|structural only", i["cause"])]
    assert len(by_design) > 50 and {i["cause_class"] for i in by_design} == {"(a) detector"}


def test_mutant_build_history_missing_counted_as_certified(tmp_path):
    cells = good_cells()
    del cells["Build.history"]
    paths = world(tmp_path, {"a1": cells})
    rc, out = run(paths, tmp_path)         # a non-uniform criterion set refuses (never silently certifies)
    assert rc == 2


def test_one_bad_cell_blocks_only_that_asset(tmp_path):
    rc, out = run(world(tmp_path, {"b1": good_cells(**{"Carr.D1": cell("Carr.D1", "NO_DETECTOR", "APPLIES")})}), tmp_path)
    assert list(json.loads((out / "FIX_LIST.json").read_text())["fix_list"]) == ["b1"]


# ───────────────────────────── Build.completion counts-only (reporting only) ─────────────────────────────

COUNTS_ONLY = "Build.completion: counts only (no integrity statement)"
HOLDS_TEXT = "rows_written=5 = live=5; the declared integrity_check_sql holds (first column of the first row = t) [integrity_check_sql sha256:0123456789ab, 0.1s]"
COUNTS_TEXT = "rows_written=0 = live=0 (count_sql over the target table; global); zero rows declared complete by target_floor"


def bc_world(tmp_path, texts, bad=()):
    """four assets a1 a2 (L0), b1 (L1), c1 (L2), each with a Build.completion cell: `texts` aid -> its measured text; `bad` aids get a NO_DETECTOR elsewhere (not certifiable)."""
    spec = {}
    for aid in ("a1", "a2", "b1", "c1"):
        spec[aid] = good_cells(**{"Build.completion": cell("Build.completion")})
        if aid in bad:
            spec[aid]["Carr.D1"] = cell("Carr.D1", "NO_DETECTOR")
    paths = world(tmp_path, spec)
    for p in paths:
        def put(d):
            for a in d[next(k for k in d if k.startswith("L"))]["assets"]:
                a["measurements"]["Build.completion"]["measured"] = texts[a["asset_id"]]
        rewrite(p, put)
    return paths


def test_counts_only_completion_pass_is_visible_on_the_certified_line_and_counted(tmp_path):
    texts = dict(a1=COUNTS_TEXT, a2=HOLDS_TEXT, b1=HOLDS_TEXT, c1=HOLDS_TEXT)
    rc, out = run(bc_world(tmp_path, texts), tmp_path)
    assert rc == 0
    md = (out / "CERTIFIED_LIST.md").read_text()
    line = {l.split("|")[1].strip(): l for l in md.splitlines() if l.startswith("| a") or l.startswith("| b") or l.startswith("| c")}
    assert COUNTS_ONLY in line["a1"]                                        # the counts-only asset carries the limitation on its own line
    assert all(COUNTS_ONLY not in line[a] for a in ("a2", "b1", "c1"))      # an integrity-holds asset does not
    assert "Build.completion counts only (no integrity statement): 1 of 4 assets" in md.splitlines()[:6]
    assert "- a1 (L0; CERTIFIED)" in md and "- a2" not in md                    # the footer lists exactly the counts-only asset
    cert = {c["asset"]: c for c in json.loads((out / "CERTIFIED_LIST.json").read_text())["certified"]}
    assert cert["a1"]["limitations"] == [COUNTS_ONLY] and cert["a2"]["limitations"] == []
    head = json.loads((out / "CERTIFIED_LIST.json").read_text())["build_completion_counts_only"]
    assert head == dict(limitation=COUNTS_ONLY, assets_of=4, count=1, assets=[dict(asset="a1", layer="L0", certified=True)])


def test_counts_only_summary_line_is_printed(tmp_path, capsys):
    rc, out = run(bc_world(tmp_path, dict(a1=COUNTS_TEXT, a2=COUNTS_TEXT, b1=HOLDS_TEXT, c1=HOLDS_TEXT)), tmp_path)
    assert rc == 0 and "Build.completion counts only (no integrity statement): 2 of 4 assets" in capsys.readouterr().out


def test_counts_only_is_reporting_only_no_verdict_or_certification_changes(tmp_path):
    texts = dict(a1=COUNTS_TEXT, a2=COUNTS_TEXT, b1=HOLDS_TEXT, c1=HOLDS_TEXT)
    rc, out = run(bc_world(tmp_path, texts), tmp_path)
    assert [c["asset"] for c in json.loads((out / "CERTIFIED_LIST.json").read_text())["certified"]] == ["a1", "a2", "b1", "c1"]      # still certified: count equality is still a PASS
    assert json.loads((out / "FIX_LIST.json").read_text())["fix_list"] == {}


def test_counts_only_asset_on_the_fix_list_is_listed_with_where_it_sits(tmp_path):
    rc, out = run(bc_world(tmp_path, dict(a1=COUNTS_TEXT, a2=HOLDS_TEXT, b1=HOLDS_TEXT, c1=HOLDS_TEXT), bad=("a1",)), tmp_path)
    fix_md = (out / "FIX_LIST.md").read_text()
    assert "- a1 (L0; on the FIX_LIST)" in fix_md and "## a1 (1 open)\n- known limitation: " + COUNTS_ONLY in fix_md
    assert "Build.completion counts only (no integrity statement): 1 of 4 assets" in fix_md
    assert [c["asset"] for c in json.loads((out / "CERTIFIED_LIST.json").read_text())["certified"]] == ["a2", "b1", "c1"]


def test_only_a_build_completion_pass_can_be_counts_only(tmp_path):
    """A Build.completion that is not a PASS (FAIL / PARTIAL / NO_DETECTOR) is never labelled counts-only, whatever its text; nor is any other criterion."""
    spec = {a: good_cells(**{"Build.completion": cell("Build.completion", "PARTIAL")}) for a in ("a1", "a2", "b1", "c1")}
    paths = world(tmp_path, spec)
    rc, out = run(paths, tmp_path)
    head = json.loads((out / "FIX_LIST.json").read_text())["build_completion_counts_only"]
    assert head["count"] == 0 and head["assets"] == []
    assert "- (none)" in (out / "FIX_LIST.md").read_text()
    assert not cp.is_counts_only_completion({"Idem.pattern": dict(v="PASS", cause="counts")})        # another criterion
    assert not cp.is_counts_only_completion({})                                                      # no Build.completion cell


def test_real_interim_census_has_exactly_one_counts_only_asset():
    interim = pathlib.Path("/Users/Dev/suvarna-evidence/census_interim/e718a9b15")
    files = [interim / f"census_L{n}.json" for n in range(3)]
    if not all(f.exists() for f in files):
        pytest.skip("the interim census evidence is not on this machine (CI)")
    r = cp.build(files, ["L0", "L1", "L2"], 83, 25, "2026-10-06", {}, allow_legacy=True)      # an interim census from before the evaluation-copy proof (SS N-327)
    c = r["build_completion_counts_only"]
    assert (c["count"], c["assets_of"], [x["asset"] for x in c["assets"]]) == (1, 83, ["bg_sarvatobhadra_grid"])


# ───────────────────────────── refusals ─────────────────────────────

def test_refuse_unstamped_no_db_identity(tmp_path, capsys):
    paths = world(tmp_path)
    rewrite(paths[0], lambda d: d["L0"].pop("db_identity"))
    refused(capsys, paths, tmp_path, "unstamped")


def test_refuse_unstamped_unavailable_identity(tmp_path, capsys):
    paths = world(tmp_path)
    rewrite(paths[1], lambda d: d["L1"].update(db_identity=dict(DB, system_id_sha256=None, unavailable="x")))
    refused(capsys, paths, tmp_path, "unstamped")


def test_refuse_unstamped_registry_revision(tmp_path, capsys):
    paths = world(tmp_path)
    rewrite(paths[2], lambda d: d["L2"].pop("registry_fingerprint"))
    refused(capsys, paths, tmp_path, "unstamped")


def test_refuse_unstamped_gate(tmp_path, capsys):
    paths = world(tmp_path)
    rewrite(paths[0], lambda d: d["rollup"]["layers"]["L0"]["a1"]["G"].pop("registry_revision"))
    refused(capsys, paths, tmp_path, "gate")


@pytest.mark.parametrize("mut", [lambda h: h.update(synthetic=True), lambda h: h.update(label="scratch census"),
                                 lambda h: h.update(scope=dict(assets=["a1"], partial=True))])
def test_refuse_synthetic_scratch_or_scoped(tmp_path, capsys, mut):
    paths = world(tmp_path)
    rewrite(paths[0], lambda d: mut(d["L0"]))
    refused(capsys, paths, tmp_path, "synthetic, scratch or scoped")


def test_refuse_scratch_database_identity(tmp_path, capsys):
    paths = world(tmp_path)
    rewrite(paths[0], lambda d: d["L0"].update(db_identity=dict(DB, database="nt_base")))
    refused(capsys, paths, tmp_path, "scratch database")


def test_refuse_different_revisions(tmp_path, capsys):
    paths = world(tmp_path, L2=dict(rev=26))
    refused(capsys, paths, tmp_path, "different registry revisions")


def test_refuse_different_fingerprints_same_revision(tmp_path, capsys):
    paths = world(tmp_path, L1=dict(fp="ef" * 32))
    refused(capsys, paths, tmp_path, "different registry revisions or fingerprints")


def test_refuse_different_databases(tmp_path, capsys):
    paths = world(tmp_path, L1=dict(db=dict(DB, system_id_sha256="01" * 32)))
    refused(capsys, paths, tmp_path, "different db_identity")


def test_refuse_missing_required_layer(tmp_path, capsys):
    refused(capsys, world(tmp_path)[:2], tmp_path, "missing required layer")


def test_refuse_extra_layer_and_duplicate_layer(tmp_path, capsys):
    paths = world(tmp_path)
    p3 = tmp_path / "census_L3.json"
    p3.write_text(json.dumps(layer_file("L3", {"d1": good_cells()})))
    refused(capsys, paths + [p3], tmp_path, "outside the required layer set")
    refused(capsys, paths + [paths[0]], tmp_path, "more than one file")


def test_refuse_head_stamp_vs_own_rollup(tmp_path, capsys):
    paths = world(tmp_path)
    rewrite(paths[0], lambda d: d["rollup"].update(registry_fingerprint="ef" * 32))
    refused(capsys, paths, tmp_path, "does not match the file's own rollup")
    paths = world(tmp_path)
    rewrite(paths[0], lambda d: d["rollup"].update(registry_revision=24))
    refused(capsys, paths, tmp_path, "does not match the file's own rollup")


def test_refuse_duplicate_asset_across_files(tmp_path, capsys):
    paths = world(tmp_path)
    p = tmp_path / "census_L1.json"
    p.write_text(json.dumps(layer_file("L1", {"a1": good_cells()})))          # a1 is also in the L0 file
    refused(capsys, paths, tmp_path, "more than one file")


def test_refuse_asset_in_rollup_not_in_layer_list(tmp_path, capsys):
    paths = world(tmp_path)
    rewrite(paths[0], lambda d: d["L0"]["assets"].pop())
    refused(capsys, paths, tmp_path, "only one of the layer list and the rollup")


def test_refuse_asset_in_layer_list_not_in_rollup(tmp_path, capsys):
    paths = world(tmp_path)
    rewrite(paths[0], lambda d: d["rollup"]["layers"]["L0"].pop("a2"))
    refused(capsys, paths, tmp_path, "only one of the layer list and the rollup")


def test_refuse_asset_count_mismatch(tmp_path, capsys):
    paths = world(tmp_path)
    refused(capsys, paths, tmp_path, "expected 82 assets, the files carry 4", "--assets-expected", "82")
    rc, out = run(paths, tmp_path, "--assets-expected", "4")
    assert rc == 0


def test_refuse_non_uniform_criterion_set_and_criteria_expected(tmp_path, capsys):
    paths = world(tmp_path)
    refused(capsys, paths, tmp_path, "not uniform", "--criteria-expected", "25")


def test_refuse_duplicate_criterion_in_asset(tmp_path, capsys):
    paths = world(tmp_path)
    rewrite(paths[0], lambda d: d["rollup"]["layers"]["L0"]["a1"]["G"]["checks"].append(cell("Idem.pattern")))
    refused(capsys, paths, tmp_path, "twice")


def test_refuse_bad_date_and_unreadable_input(tmp_path, capsys):
    rc = cp.main(["--census", *map(str, world(tmp_path)), "--date", "05-10-2026", "--out-dir", str(tmp_path / "o")])
    assert rc == 2 and "--date must be" in capsys.readouterr().err
    rc = cp.main(["--census", str(tmp_path / "nope.json"), "--date", "2026-10-05", "--out-dir", str(tmp_path / "o")])
    assert rc == 2 and capsys.readouterr().err.startswith("REFUSED: ")
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert cp.main(["--census", str(bad), "--date", "2026-10-05", "--out-dir", str(tmp_path / "o")]) == 2


def test_refuse_real_file_mutated_unstamped(tmp_path, capsys):
    d = json.loads(REAL[0].read_text())
    d["L0"].pop("db_identity")
    p = tmp_path / "L0.json"
    p.write_text(json.dumps(d))
    refused(capsys, [p, REAL[1], REAL[2]], tmp_path, "unstamped")


def test_no_clock_read_in_source():
    src = pathlib.Path(cp.__file__).read_text()
    assert not re.search(r"\b(datetime|time)\.(now|time|today|strftime)|import datetime|import time\b", src)


# MUTANTS (each is a one-line source change the suite above must fail on; run via CENSUS_PP_PATH, see the PR notes):
#  M1 is_ruled_na ignores rule_id          -> test_mutant_ruled_na_without_rule_id_counted_as_certified
#  M2 is_ruled_na ignores decision         -> test_mutant_ruled_na_without_decision_counted_as_certified
#  M3 NO_DETECTOR counted as pass          -> test_mutant_non_pass_verdict_counted_as_pass[NO_DETECTOR]
#  M4 PARTIAL / FAIL counted as pass       -> test_mutant_non_pass_verdict_counted_as_pass[PARTIAL|FAIL]
#  M6 db_identity check removed            -> test_refuse_unstamped_*
#  M7 revision/fingerprint mix allowed     -> test_refuse_different_revisions / _fingerprints_same_revision
#  M8 head-vs-rollup stamp check removed   -> test_refuse_head_stamp_vs_own_rollup
#  M9 duplicate-asset check removed        -> test_refuse_duplicate_asset_across_files
#  M10 asset-set equality check removed    -> test_refuse_asset_in_rollup_not_in_layer_list / _layer_list_not_in_rollup
#  M11 assets-expected check removed       -> test_refuse_asset_count_mismatch
#  M12 missing-layer check removed         -> test_refuse_missing_required_layer
#  M13 scratch/synthetic/scoped check removed -> test_refuse_synthetic_scratch_or_scoped / _scratch_database_identity
#  M14 unclassified falls into a class     -> test_classify[INCONCLUSIVE] / test_unknown_text_is_visible_not_dropped
#  M15 counts-only test ignores the holds text / PASS requirement -> test_counts_only_* / test_only_a_build_completion_pass_can_be_counts_only
