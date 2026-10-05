"""test_e1_1_scorecard.py -- E1.1 `nikasha_scorecard.py`: the machine-readable T1-T5 scorecard.

Earned-signal tests (CLAUDE.md section N.8). Every verdict the generator emits must come from a detector that can
fail: each rule below has a SEEDED-DEFECT test that flips one input and asserts the verdict moves, and a
MISSING-INPUT test that asserts the cell reads UNMEASURED / NO_DETECTOR, never PASS.

Every test builds a throw-away git repository from synthetic files (the generator reads ONLY `git show <ref>:path`,
never the working tree) and, where a census is needed, a synthetic census directory whose registry stamp is computed from the
synthetic inspector at that ref. Nothing here touches the real repository's files, a database or a credential.
"""
import copy
import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
GEN_PATH = HERE.parent / "nikasha_scorecard.py"

_spec = importlib.util.spec_from_file_location("nikasha_scorecard", GEN_PATH)
sc = importlib.util.module_from_spec(_spec)
sys.modules["nikasha_scorecard"] = sc
_spec.loader.exec_module(sc)

P = "00_ARCHITECTURE/"
N = P + "briefs/nirmana/"
GAPS = P + "control/asset_gaps.jsonl"
CERTS = P + "control/asset_certs.jsonl"
REGISTER = N + "NIKASHA_CHANGE_REGISTER_v2_0.md"
T1D = P + "MADHAV_PRODUCT_DEFINITION_FINAL.md"
T2D = N + "MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md"
T3D = N + "LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md"
T4D = N + "ASSET_ELEVATION_TEMPLATE_v2_0.md"
L0D = N + "MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md"
PILOT = N + "l0_assets/BG_ONTOLOGY_ELEVATION_BRIEF_v1_0.md"
TRACKER = P + "control/asset_elevation_tracker.py"
MANIFEST = P + "CAPABILITY_MANIFEST.json"
INSPECTOR = "platform/scripts/governance/asset_census.py"
WRITERS = "platform/python-sidecar/pipeline/orchestrator/writers/"
GATES = ["Ldgr", "Idem", "Earn", "Null", "Vocab", "Carr", "Narr", "Dens", "Build"]


# ───────────────────────────── fixture construction ─────────────────────────────

HARNESS_REL = "platform/scripts/governance/nikasha_plant.py"
D1_REL = "platform/scripts/governance/carriage_d1.py"
HARNESS_SRC = "# the plant harness\n"
D1_SRC = "# the D1 engine\n"
DECL_REL_ = "platform/scripts/governance/asset_declarations.json"


def fixture_runtime_text(rel):
    return D1_SRC if rel == D1_REL else '{"version": "0"}' if rel == DECL_REL_ else f"# {rel}\n"

INSPECTOR_SRC = '''\
import hashlib, json
REGISTRY_REVISION = 15
CELL_GATES = ("Ldgr", "Idem", "Earn", "Null", "Vocab", "Carr", "Narr", "Dens", "Build")
ROLLUP_ORDER = ("FAIL", "ERRORED", "NO_DETECTOR", "PARTIAL", "PASS")
RETIRED_CRITERIA = {"Carr.detector": {"revision": 8}}
_M = "asset_census.py:measure()"
CRITERION_REGISTRY = {
    "Build.registered": {"gate": "Build", "check": "registered", "detector": _M, "layers": ("L0", "L1", "L2", "L3", "L4", "L5"), "revision": 1},
    "Build.contract": {"gate": "Build", "check": "contract", "detector": _M, "layers": ("L0", "L1", "L2", "L3", "L4", "L5"), "revision": 1},
    "Idem.pattern": {"gate": "Idem", "check": "pattern", "detector": _M, "layers": ("L0", "L1", "L2", "L3", "L4", "L5"), "revision": 2},
    "Carr.D2": {"gate": "Carr", "check": "D2", "detector": "NONE", "layers": ("L1",), "revision": 1},
}
NA_RULE_DECISIONS = {}
NA_CAUSES = {}
def registry_fingerprint():
    blob = json.dumps(dict(registry=CRITERION_REGISTRY, na_rules=NA_RULE_DECISIONS, na_causes=NA_CAUSES,
                           cell_gates=list(CELL_GATES), rollup_order=list(ROLLUP_ORDER)),
                      sort_keys=True, default=list, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
'''

TRACKER_SRC = '''\
# The certified gates. Nine, not thirty-three.
GATES = [
 ("Ldgr","derivation ledger","always","x"),
 ("Idem","idempotency","always","x"),
 ("Earn","earned signal","always","x"),
 ("Null","honest null","always","x"),
 ("Vocab","vocabulary","always","x"),
 ("Carr","carriage","always","x"),
 ("Narr","narration","conditional","x"),
 ("Dens","density","conditional","x"),
 ("Build","buildability","always","x"),
]
'''


def _gate_rows(style):
    return "\n".join(f"| **{g}** {style} | x |" for g in GATES)


def register_text(rows):
    head = "---\nartifact: NIKASHA_CHANGE_REGISTER\nversion: \"2.8\"\n---\n\n| id | what | source | severity | depends | effort | state |\n|---|---|---|---|---|---|---|\n"
    out = [head]
    for rid, source, sev, state in rows:
        out.append(f"| {rid} | text of {rid} | {source} | {sev} | — | 1 | {state} |\n")
    return "".join(out)


CLEAN_ROWS = [
    ("R52", "nikasha-test P2 T1 plant build_completion_truncate", "BLOCKS_FREEZE", "CLOSED 2026-09-27 — fixed"),
    ("R55", "nikasha-test P2 T1 plant earn_cost_signal", "DEGRADES", "OPEN — kept"),
    ("R42", "nikasha-test P2 handverify L1/L2/L4/L5", "BLOCKS_FREEZE", "CLOSED 2026-09-27 — fixed"),
    ("R43", "nikasha-test P2 handverify L4/L5", "BLOCKS_LAYER", "DONE"),
    ("R40", "nikasha-test P2 T2 sweep", "BLOCKS_LAYER", "CLOSED 2026-09-27 — fixed"),
    ("R41", "nikasha-test P2 T2 sweep (L3 + all killed)", "BLOCKS_FREEZE", "CLOSED 2026-09-27 — fixed"),
    ("R57", "nikasha-test P3 T3", "BLOCKS_FREEZE", "CLOSED 2026-09-27 — fixed"),
    ("R58", "nikasha-test P3 T3", "BLOCKS_FREEZE", "CLOSED 2026-09-27 — fixed"),
    ("R24", "—", "BLOCKS_FREEZE", "CLOSED 2026-10-03 — census re-run"),
    ("R63", "nikasha-test P5 T5", "BLOCKS_LAYER", "CLOSED 2026-09-28 — fixed"),
    ("R71", "nikasha-test P5 T5", "BLOCKS_FREEZE", "CLOSED 2026-10-03 — reopened tier"),
    ("R90", "nikasha-test P4 derivability L1", "BLOCKS_LAYER", "OPEN"),
]


def clean_files():
    """A synthetic repo in which every repo-derivable cell is in its clean state."""
    f = {}
    f[INSPECTOR] = INSPECTOR_SRC
    f[TRACKER] = TRACKER_SRC
    f[REGISTER] = register_text(CLEAN_ROWS)
    f[T1D] = "---\nreview_record: briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md  # ok\n---\nbody\n"
    f[P + "briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md"] = "review\n"
    f[T2D] = ("---\ndocument_reviews:\n  - reviews/REVIEW_DATA_PLANE_v3_0.md  # REJECT, 2 BLOCKER + 9 MAJOR + 10 MINOR\n"
              "changelog:\n  - \"(f) §13.3 is ten elements and says so\"\n"
              "  - \"was: 2 BLOCKER + 10 MAJOR + 11 MINOR (REVIEW_DATA_PLANE_FINAL summary)\"\n---\n"
              "| Presentation parity **[TRANSFERS]** | x |\n**Ten elements.** x\n")
    f[T3D] = ("---\nchangelog:\n  - \"v1.1: an eight-row map is enforceable; NO DETECTOR is never a pass; the eight gates\"\n"
              "  - \"**Presentation parity** holds (old wording)\"\n---\n"
              "## §5.2 the nine gates\n" + _gate_rows("· gate") + "\n"
              "4. **Presentation fields carried** by the layer.\n5. **The gate map exists.** §5.2's nine-row map\n"
              "result `NO_DETECTOR` is an honest null\n")
    f[T4D] = ("---\ninherits: layer 5.2 (a) the nine gates\nchangelog:\n  - \"was: the eight gates; NA if never run\"\n---\n"
              "## §4 · Asset conformance — the nine gates\n" + _gate_rows("gate") + "\n"
              "### 4.1 x\n### 4.2 · Buildability — the nine checks, and what is NOT a gap\nN/A if never run\n")
    f[L0D] = "Nine gates × 40 assets = 360. 0/360 gates certified.\n"
    f[PILOT] = "## §4 · The nine gates\nrows\n"
    f[WRITERS + "bg_a.py"] = "@register('bg_a')\nclass A: pass\n"
    f[WRITERS + "ga_b.py"] = '@register("ga_b")\nclass B: pass\n'
    f[WRITERS + "ga_x.py"] = "@register('ga_x')\nclass X: pass\n"
    f[WRITERS + "bo_a.py"] = "@register('bo_a')\nclass C: pass\n"
    f[WRITERS + "ka_a.py"] = "ASSET_ID = 'ka_a'\n@register(ASSET_ID)\nclass D: pass\n"
    f[WRITERS + "ph_a.py"] = "@register('ph_a')\nclass E: pass\n"
    f[WRITERS + "mi_a.py"] = "from x import register\nclass F:\n    @register(\"mi_a\")\n    def g(self): pass\n"
    f[WRITERS + "README.md"] = "@register('not_python')\n"
    f[WRITERS + "tests/test_x.py"] = "@register('ga_x')\nclass T: pass\n"
    schema = {"asset": "_schema", "_doc": "x"}
    rows = [schema,
            {"asset": "ga_b", "gap_id": "ga_b-Idem.pattern", "kind": "gap", "criterion": "Idem.pattern", "what": "measured: x / required: y", "state": "OPEN"},
            {"asset": "ga_b", "gap_id": "ga_b-Idem.pattern", "kind": "gap", "criterion": "Idem.pattern", "what": "CLOSED by measurement: ok / required: y", "state": "CLOSED"},
            {"asset": "bg_a", "gap_id": "bg_a-Carr.detector", "kind": "gap", "criterion": "Carr.detector", "what": "measured: x / required: y", "state": "OPEN"},
            {"asset": "bg_a", "gap_id": "bg_a-Carr.detector", "kind": "gap", "criterion": "Carr.detector", "what": "CLOSED by retirement of criterion Carr.detector", "state": "CLOSED", "closed_by": "retirement"},
            {"asset": "ga_x", "gap_id": "ga_x-Build.contract", "kind": "gap", "criterion": "Build.contract", "what": "measured: x / required: y", "state": "OPEN"}]
    f[GAPS] = "".join(json.dumps(r) + "\n" for r in rows)
    f[CERTS] = json.dumps({"asset": "_schema"}) + "\n"
    f[HARNESS_REL] = HARNESS_SRC
    for rel in sc.T1_REQUIRED_RUNTIME_FILES:
        if rel not in (INSPECTOR, HARNESS_REL):
            f[rel] = fixture_runtime_text(rel)
    f[MANIFEST] = manifest_text(f)
    return f


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout.strip()


def _commit(path, msg):
    _git(path, "-c", "user.email=t@example.invalid", "-c", "user.name=t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", msg)


def commit_repo(path, files):
    path = pathlib.Path(path)
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    for rel, text in files.items():
        if text is None:
            continue
        p = path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    _git(path, "add", "-A")
    _commit(path, "fixture")
    return _git(path, "rev-parse", "HEAD")


def manifest_text(files, entries=None):
    entries = entries if entries is not None else [{"canonical_id": "OTHER", "version": "1"}]
    fp = hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()[:16]
    return json.dumps({"generated_at": "x", "entry_count": len(entries), "fingerprint": fp, "entries": entries}, indent=2)


def stub_fingerprint(tmp_path):
    d = tmp_path / "fpstub"
    d.mkdir(exist_ok=True)
    (d / "asset_census.py").write_text(INSPECTOR_SRC)
    out = subprocess.run([sys.executable, "-I", "-c", "import sys; sys.path.insert(0, '.'); import asset_census as a; print(a.registry_fingerprint())"],
                         cwd=d, capture_output=True, text=True, check=True).stdout.strip()
    return out


def census_layer(layer, assets, fp, rev=15, dirty=False, tool=None, decl=None, generated="2026-10-02T10:00:00+05:30"):
    return {layer: {"generated": generated, "layer": layer, "n_assets": len(assets),
                    "population_active": len(assets), "registry_revision": rev, "registry_fingerprint": fp,
                    "tool_commit": tool, "tool_dirty": dirty, "declarations_sha256": decl, "assets": assets},
            "rollup": {}, "rollup_excluded": {}}


def asset(aid, has_writer=True, reg="PASS", idem="PASS", contract="PASS"):
    m = {"Build.registered": {"v": reg, "measured": "x"}, "Build.contract": {"v": contract, "measured": "x"},
         "Idem.pattern": {"v": idem, "measured": "x"}}
    return {"asset_id": aid, "has_writer": has_writer, "measurements": m}


LAYER_ASSETS = {
    "L0": [asset("bg_a"), asset("bg_s", has_writer=False, reg="N/A", idem="N/A", contract="N/A")],
    "L1": [asset("ga_b"), asset("ga_x")],
    "L2": [asset("bo_a")], "L3": [asset("ka_a")], "L4": [asset("ph_a")], "L5": [asset("mi_a")],
}


def write_census(dirpath, fp, assets=None, rev=15, skip=(), dirty=False, tool=None, decl="DEFAULT", generated="2026-10-02T10:00:00+05:30", prefix="census_"):
    dirpath = pathlib.Path(dirpath)
    dirpath.mkdir(parents=True, exist_ok=True)
    if decl == "DEFAULT":
        decl = hashlib.sha256(fixture_runtime_text(DECL_REL_).encode()).hexdigest()
    assets = assets or LAYER_ASSETS
    for layer, rows in assets.items():
        if layer in skip:
            continue
        (dirpath / f"{prefix}{layer}.json").write_text(json.dumps(census_layer(layer, copy.deepcopy(rows), fp, rev, dirty, tool, decl, generated)))
    return dirpath


@pytest.fixture
def env(tmp_path):
    files = clean_files()
    repo = tmp_path / "repo"
    sha = commit_repo(repo, files)
    fp = stub_fingerprint(tmp_path)
    cdir = write_census(tmp_path / "census", fp, tool=sha)
    return dict(files=files, repo=repo, sha=sha, fp=fp, cdir=cdir, tmp=tmp_path)


def run(env, **kw):
    return sc.build_scorecard(env["repo"], env["sha"], census_dir=kw.get("census_dir", env["cdir"]),
                              t1_evidence=kw.get("t1_evidence"))


def remake(env, mutate=None, delete=(), census=True, **cw):
    """New repo from the clean files with `mutate(files)` applied; returns a fresh env."""
    files = copy.deepcopy(env["files"])
    if mutate:
        mutate(files)
    for d in delete:
        files.pop(d, None)
    tmp = env["tmp"]
    n = sum(1 for _ in tmp.iterdir())
    repo = tmp / f"repo{n}"
    sha = commit_repo(repo, files)
    e = dict(env, files=files, repo=repo, sha=sha)
    if census:
        e["cdir"] = write_census(tmp / f"census{n}", env["fp"], tool=sha, **cw)
    return e


def cell(card, test, name):
    return card["tests"][test]["cells"][name]


def t5(card, name):
    return card["tests"]["T5"]["cells"][name]


# ───────────────────────────── combine() ─────────────────────────────

def C(kind, v):
    return {"kind": kind, "verdict": v}


def test_combine_rules():
    f = sc.combine
    assert f({"a": C("measurement", "PASS"), "b": C("precondition", "PASS")}) == "PASS"
    assert f({"a": C("measurement", "PASS"), "b": C("measurement", "FAIL")}) == "FAIL"
    assert f({"a": C("precondition", "FAIL"), "b": C("measurement", "PASS")}) == "FAIL"
    assert f({"a": C("measurement", "PASS"), "b": C("measurement", "UNMEASURED")}) == "PARTIAL"
    assert f({"a": C("measurement", "PASS"), "b": C("measurement", "NO_DETECTOR")}) == "PARTIAL"
    assert f({"a": C("measurement", "PASS"), "b": C("precondition", "PARTIAL")}) == "PARTIAL"
    # a precondition PASS alone never makes a test partial-measured
    assert f({"a": C("measurement", "UNMEASURED"), "b": C("precondition", "PASS")}) == "UNMEASURED"
    assert f({"a": C("measurement", "NO_DETECTOR"), "b": C("measurement", "UNMEASURED")}) == "UNMEASURED"
    assert f({}) == "UNMEASURED"


def test_combine_never_passes_on_a_non_pass_cell():
    for v in ("FAIL", "PARTIAL", "NO_DETECTOR", "UNMEASURED"):
        assert sc.combine({"a": C("measurement", "PASS"), "b": C("measurement", v)}) != "PASS"


# ───────────────────────────── shape, determinism, provenance ─────────────────────────────

def test_clean_fixture_shape_and_provenance(env):
    card = run(env)
    assert card["schema"] == "nikasha_scorecard/1"
    assert card["generator"] == "platform/scripts/governance/nikasha_scorecard.py"
    assert card["generator_sha256"] == hashlib.sha256(GEN_PATH.read_bytes()).hexdigest()
    assert card["generator_at_ref_sha256"] is None  # the fixture repo has no generator
    assert card["ref"] == env["sha"] and len(card["ref"]) == 40
    assert card["inspector_commit"] == _git(env["repo"], "log", "-1", "--format=%H", "--", INSPECTOR)
    assert card["inspector_blob_sha256"] == hashlib.sha256(INSPECTOR_SRC.encode()).hexdigest()
    assert card["registry"] == {"revision": 15, "fingerprint": env["fp"]}
    assert card["measured_offline"] is True
    assert card["change_register"]["version"] == "2.8"
    assert set(card["tests"]) == {"T1", "T2", "T3", "T4", "T5"}
    for t, body in card["tests"].items():
        assert body["verdict"] in sc.VERDICTS, t
        assert {"definition", "population", "cells", "evidence", "unmeasured_cells"} <= set(body)
        for name, c in body["cells"].items():
            assert c["verdict"] in sc.VERDICTS and c["kind"] in ("measurement", "precondition"), (t, name)
        assert body["unmeasured_cells"] == sorted(n for n, c in body["cells"].items() if c["verdict"] in ("UNMEASURED", "NO_DETECTOR"))
    assert set(card["engine_build_checks"]) == {"Build.registered", "Build.contract"}
    assert str(env["tmp"]) not in sc.render(card), "no absolute path may leak into the scorecard"


def test_inspector_commit_is_the_inspectors_last_commit_not_the_ref(env):
    (env["repo"] / "later.txt").write_text("x")
    _git(env["repo"], "add", "-A")
    _commit(env["repo"], "later")
    later = _git(env["repo"], "rev-parse", "HEAD")
    card = sc.build_scorecard(env["repo"], later, census_dir=env["cdir"])
    assert card["ref"] == later != env["sha"]
    assert card["inspector_commit"] == env["sha"]


def test_registry_facts_are_per_inspector_content_not_cached_across_refs(env):
    # two different inspectors in one process must each report their own revision (the facts cache is content-keyed)
    e2 = remake(env, mutate=lambda f: f.__setitem__(INSPECTOR, INSPECTOR_SRC.replace("REGISTRY_REVISION = 15", "REGISTRY_REVISION = 99")))
    a, b = run(env), run(e2)
    assert a["registry"]["revision"] == 15 and b["registry"]["revision"] == 99
    assert a["inspector_blob_sha256"] != b["inspector_blob_sha256"]


def test_unimportable_inspector_leaves_registry_null_and_cells_unmeasured(env):
    e = remake(env, mutate=lambda f: f.__setitem__(INSPECTOR, "raise RuntimeError('no')\n"))
    card = run(e)
    assert card["registry"] == {"revision": None, "fingerprint": None}
    assert all(i["fresh"] is False for i in card["inputs"]["census"])
    assert cell(card, "T4", "L1")["verdict"] == "UNMEASURED"
    assert t5(card, "gate_set_agreement")["verdict"] == "UNMEASURED"


def test_same_inputs_byte_identical(env):
    a = sc.render(run(env))
    b = sc.render(run(env))
    assert a == b and a.endswith("\n")
    assert json.loads(a)["generator_sha256"]


def test_generator_at_ref_recorded_when_present(env):
    e = remake(env, mutate=lambda f: f.__setitem__("platform/scripts/governance/nikasha_scorecard.py", GEN_PATH.read_text()))
    assert run(e)["generator_at_ref_sha256"] == hashlib.sha256(GEN_PATH.read_bytes()).hexdigest()


# ───────────────────────────── the clean fixture: what each test says ─────────────────────────────

def test_clean_fixture_verdicts_are_honest_not_green(env):
    card = run(env)
    tests = card["tests"]
    # T5 is fully computable from the repo, but drift_detector needs a database: never PASS offline
    assert t5(card, "drift_detector")["verdict"] == "UNMEASURED"
    non_drift = {n: c for n, c in tests["T5"]["cells"].items() if n != "drift_detector"}
    assert all(c["verdict"] in ("PASS", "NO_DETECTOR") for c in non_drift.values()), {n: c["verdict"] for n, c in non_drift.items()}
    assert tests["T5"]["verdict"] == "PARTIAL"
    # no test is PASS offline: each has at least one cell no offline detector can decide
    assert all(t["verdict"] != "PASS" for t in tests.values())
    assert tests["T1"]["verdict"] == "UNMEASURED" and cell(card, "T1", "plant_suite")["verdict"] == "NO_DETECTOR"
    assert cell(card, "T2", "build_registered_rederivation")["verdict"] == "PASS"
    assert cell(card, "T2", "handverify_sample")["verdict"] == "NO_DETECTOR"
    assert tests["T2"]["verdict"] == "PARTIAL"
    assert cell(card, "T3", "closure_by_measurement")["verdict"] == "PASS"
    assert cell(card, "T3", "closures_earned")["verdict"] == "PASS"
    assert cell(card, "T3", "regression_reopen")["verdict"] == "NO_DETECTOR"
    assert cell(card, "T3", "tracker_moves")["verdict"] == "NO_DETECTOR"
    for layer in ("L1", "L2", "L3", "L4", "L5"):
        assert cell(card, "T4", layer)["verdict"] == "PASS"
    assert "L0" not in tests["T4"]["cells"]
    assert cell(card, "T4", "production_provenance")["verdict"] == "NO_DETECTOR"
    for t in ("T1", "T2", "T3", "T4", "T5"):
        assert cell(card, t, "known_defect_rows")["verdict"] == "PASS", t
    assert card["engine_build_checks"] == {"Build.registered": "PASS", "Build.contract": "PASS"}


# ───────────────────────────── register rows (precondition) ─────────────────────────────

@pytest.mark.parametrize("rid,test", [("R52", "T1"), ("R42", "T2"), ("R57", "T3"), ("R24", "T4"), ("R63", "T5")])
def test_open_blocking_row_fails_its_test_precondition(env, rid, test):
    def mut(f):
        rows = [(r, s, v, "OPEN — reopened by the test" if r == rid else st) for r, s, v, st in CLEAN_ROWS]
        f[REGISTER] = register_text(rows)
    e = remake(env, mut)
    card = run(e)
    c = cell(card, test, "known_defect_rows")
    assert c["verdict"] == "FAIL" and rid in c["open"]
    assert card["tests"][test]["verdict"] == "FAIL"


def test_row_binding_is_by_source_and_explicit_t4_extras(env):
    card = run(env)
    assert cell(card, "T1", "known_defect_rows")["rows"] == {"R52": "CLOSED"}
    assert set(cell(card, "T2", "known_defect_rows")["rows"]) == {"R42", "R43"}
    assert set(cell(card, "T4", "known_defect_rows")["rows"]) == {"R24", "R40", "R41"}
    assert set(cell(card, "T5", "known_defect_rows")["rows"]) == {"R63", "R71"}
    # non-blocking rows (DEGRADES R55) and P4 inventions never bind
    assert "R55" not in json.dumps(cell(card, "T1", "known_defect_rows")["rows"])
    assert cell(card, "T1", "known_defect_rows")["nonblocking_open"] == ["R55"]


def test_t3_binding_is_explicit_not_by_source(env):
    # a P3 T3 row that is a data defect (R59 class) must not bind T3; R57/R58 do
    def mut(f):
        f[REGISTER] = register_text([x for x in CLEAN_ROWS if x[0] != "R58"] + [("R59", "nikasha-test P3 T3", "BLOCKS_LAYER", "OPEN"), ("R58", "nikasha-test P3 T3", "BLOCKS_FREEZE", "OPEN")])
    c = cell(run(remake(env, mut)), "T3", "known_defect_rows")
    assert c["open"] == ["R58"] and set(c["rows"]) == {"R57", "R58"}


def test_closed_on_branch_and_deferred_rows_are_partial_never_pass(env):
    for word in ("CLOSED_ON_BRANCH — engine A1", "PARTIAL — honest", "DEFERRED — while withheld", "MEASURED in P6"):
        def mut(f, word=word):
            f[REGISTER] = register_text([(r, s, v, word if r == "R57" else st) for r, s, v, st in CLEAN_ROWS])
        card = run(remake(env, mut))
        assert cell(card, "T3", "known_defect_rows")["verdict"] == "PARTIAL", word


def test_bound_explicit_row_absent_from_register_is_unmeasured(env):
    def mut(f):
        f[REGISTER] = register_text([x for x in CLEAN_ROWS if x[0] != "R24"])
    c = cell(run(remake(env, mut)), "T4", "known_defect_rows")
    assert c["verdict"] == "UNMEASURED" and c["missing_rows"] == ["R24"]


def test_partial_cells_are_not_listed_as_unmeasured(env):
    def mut(f):
        f[REGISTER] = register_text([(r, s, v, "PARTIAL — honest" if r == "R57" else st) for r, s, v, st in CLEAN_ROWS])
    card = run(remake(env, mut))
    assert cell(card, "T3", "known_defect_rows")["verdict"] == "PARTIAL"
    assert "known_defect_rows" not in card["tests"]["T3"]["unmeasured_cells"]
    assert card["summary"]["unmeasured_cells_total"] == sum(len(t["unmeasured_cells"]) for t in card["tests"].values())


def test_register_missing_is_unmeasured_not_pass(env):
    card = run(remake(env, delete=[REGISTER]))
    for t in ("T1", "T2", "T3", "T4", "T5"):
        assert cell(card, t, "known_defect_rows")["verdict"] == "UNMEASURED"
    assert card["change_register"]["sha256"] is None


# ───────────────────────────── census freshness ─────────────────────────────

def test_stale_census_is_unmeasured_with_observed_never_a_verdict(env):
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / "stale", "0" * 64, rev=10)
    card = run(e)
    for layer in ("L1", "L2", "L3", "L4", "L5"):
        c = cell(card, "T4", layer)
        assert c["verdict"] == "UNMEASURED" and c["observed_on_stale_input"] == "would_be_PASS" and "stale_census" in c["reason"]
    assert cell(card, "T2", "build_registered_rederivation")["verdict"] == "UNMEASURED"
    assert cell(card, "T3", "closure_by_measurement")["verdict"] == "UNMEASURED"
    assert card["engine_build_checks"]["Build.registered"] == "UNMEASURED"
    assert all(i["fresh"] is False for i in card["inputs"]["census"])
    assert card["tests"]["T4"]["verdict"] == "UNMEASURED"


def test_scoped_census_is_stale(env):
    e = remake(env, census=False)
    cdir = write_census(env["tmp"] / "scoped", env["fp"], tool=e["sha"])
    doc = json.loads((cdir / "census_L1.json").read_text())
    doc["L1"]["scope"] = {"assets": ["ga_b"], "partial": True}
    (cdir / "census_L1.json").write_text(json.dumps(doc))
    e["cdir"] = cdir
    c = cell(run(e), "T4", "L1")
    assert c["verdict"] == "UNMEASURED" and "scoped_census" in c["reason"]


def test_dirty_census_tool_is_stale(env):
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / "dirty", env["fp"], tool=e["sha"], dirty=True)
    assert cell(run(e), "T4", "L1")["verdict"] == "UNMEASURED"


def test_missing_census_dir_is_unmeasured_everywhere(env):
    card = run(env, census_dir=None)
    for layer in ("L1", "L2", "L3", "L4", "L5"):
        assert cell(card, "T4", layer)["verdict"] == "UNMEASURED"
    assert card["inputs"]["census"] == []
    assert card["tests"]["T4"]["verdict"] == "UNMEASURED"


def test_one_missing_layer_file_is_unmeasured_for_that_layer_only(env):
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / "partial", env["fp"], tool=e["sha"], skip=("L3",))
    card = run(e)
    assert cell(card, "T4", "L3")["verdict"] == "UNMEASURED" and "missing" in cell(card, "T4", "L3")["reason"]
    assert cell(card, "T4", "L2")["verdict"] == "PASS"
    assert card["tests"]["T4"]["verdict"] == "PARTIAL"
    assert cell(card, "T2", "build_registered_rederivation")["verdict"] == "UNMEASURED"


def test_malformed_census_is_a_script_error(env):
    (env["cdir"] / "census_L2.json").write_text("{not json")
    with pytest.raises(sc.ScorecardError):
        run(env)


def test_appended_run_newest_full_census_wins_and_names_are_not_recorded(env):
    assets = copy.deepcopy(LAYER_ASSETS)
    assets["L1"][0]["measurements"]["Idem.pattern"]["v"] = "FAIL"
    old = write_census(env["tmp"] / "two", env["fp"], tool=env["sha"], assets=assets, generated="2026-10-01T09:00:00+05:30", prefix="asset_census_old_")
    write_census(old, env["fp"], tool=env["sha"], generated="2026-10-02T09:00:00+05:30", prefix="asset_census_new_")
    card = run(env, census_dir=old)
    assert cell(card, "T4", "L1")["verdict"] == "PASS"  # the newer run (all PASS) won over the older one
    blob = sc.render(card)
    assert "asset_census_" not in blob and '"file"' not in blob
    assert [i["layer"] for i in card["inputs"]["census"]] == ["L0", "L1", "L2", "L3", "L4", "L5"]


def test_same_stamp_different_bytes_is_refused_not_picked(env):
    assets = copy.deepcopy(LAYER_ASSETS)
    assets["L1"][0]["measurements"]["Idem.pattern"]["v"] = "FAIL"
    d = write_census(env["tmp"] / "tie", env["fp"], tool=env["sha"], prefix="asset_census_a_")
    write_census(d, env["fp"], tool=env["sha"], assets=assets, prefix="asset_census_b_")
    with pytest.raises(sc.ScorecardError) as ei:
        run(env, census_dir=d)
    assert "newest head stamp" in str(ei.value)


def test_identical_duplicate_files_are_not_a_conflict(env):
    d = write_census(env["tmp"] / "same", env["fp"], tool=env["sha"], prefix="asset_census_a_")
    write_census(d, env["fp"], tool=env["sha"], prefix="asset_census_b_")
    assert cell(run(env, census_dir=d), "T4", "L1")["verdict"] == "PASS"


def test_scoped_census_never_displaces_a_full_one(env):
    d = write_census(env["tmp"] / "sc", env["fp"], tool=env["sha"], prefix="asset_census_full_")
    doc = json.loads((d / "asset_census_full_L1.json").read_text())
    doc["L1"]["scope"] = {"assets": ["ga_b"], "partial": True}
    doc["L1"]["generated"] = "2030-01-01T00:00:00+00:00"   # newer, but scoped
    (d / "asset_census_scoped_L1.json").write_text(json.dumps(doc))
    assert cell(run(env, census_dir=d), "T4", "L1")["verdict"] == "PASS"


def test_default_census_is_the_repo_copy_at_the_ref_and_check_needs_no_flags(env, tmp_path):
    def mut(f):
        pass
    e = remake(env, mut, census=False)
    # commit censuses into the repo at the control/census directory, then measure the NEW commit
    cdir = e["repo"] / "00_ARCHITECTURE/control/census"
    write_census(cdir, env["fp"], tool=e["sha"], prefix="asset_census_2026_")
    _git(e["repo"], "add", "-A")
    _commit(e["repo"], "censuses")
    sha2 = _git(e["repo"], "rev-parse", "HEAD")
    # fresh requires tool_commit's inspector blob == ref's blob: unchanged by the commit, so still fresh
    out = tmp_path / "default.json"
    assert sc.main(["--repo", str(e["repo"]), "--ref", sha2, "--out", str(out)]) == 0
    card = json.loads(out.read_text())
    assert [c["verdict"] for n, c in card["tests"]["T4"]["cells"].items() if n in ("L1", "L2", "L3", "L4", "L5")] == ["PASS"] * 5
    assert sc.main(["--repo", str(e["repo"]), "--out", str(out), "--check"]) == 0
    # the same bytes from an outside directory give the same scorecard
    out2 = tmp_path / "outside.json"
    assert sc.main(["--repo", str(e["repo"]), "--ref", sha2, "--census-dir", str(cdir), "--out", str(out2)]) == 0
    assert out.read_text() == out2.read_text()


# ───────────────────────────── T4 ─────────────────────────────

def test_t4_errored_cell_fails_that_layer(env):
    assets = copy.deepcopy(LAYER_ASSETS)
    assets["L3"][0]["measurements"]["Idem.pattern"] = {"v": "ERRORED", "measured": "timeout"}
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / "err", env["fp"], tool=e["sha"], assets=assets)
    card = run(e)
    c = cell(card, "T4", "L3")
    assert c["verdict"] == "FAIL" and c["errored_cells"] == 1
    assert cell(card, "T4", "L2")["verdict"] == "PASS"
    assert card["tests"]["T4"]["verdict"] == "FAIL"


def test_t4_unmeasured_active_asset_fails(env):
    e = remake(env, census=False)
    cdir = write_census(env["tmp"] / "short", env["fp"], tool=e["sha"])
    doc = json.loads((cdir / "census_L1.json").read_text())
    doc["L1"]["population_active"] = 3  # three active, two measured
    (cdir / "census_L1.json").write_text(json.dumps(doc))
    e["cdir"] = cdir
    c = cell(run(e), "T4", "L1")
    assert c["verdict"] == "FAIL" and "population" in c["reason"]


def test_t4_empty_layer_fails(env):
    assets = copy.deepcopy(LAYER_ASSETS)
    assets["L4"] = []
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / "empty", env["fp"], tool=e["sha"], assets=assets)
    assert cell(run(e), "T4", "L4")["verdict"] == "FAIL"


# ───────────────────────────── T2 ─────────────────────────────

def test_t2_rederivation_catches_a_census_claim_the_code_contradicts(env):
    # the census says ga_x's writer is registered; the code at the ref has no @register for it
    e = remake(env, delete=[WRITERS + "ga_x.py"])
    c = cell(run(e), "T2", "build_registered_rederivation")
    assert c["verdict"] == "FAIL" and c["disagreements"] == [{"asset": "ga_x", "layer": "L1", "census": "PASS", "rederived": "FAIL"}]


def test_t2_rederivation_catches_a_census_fail_the_code_does_not_support(env):
    assets = copy.deepcopy(LAYER_ASSETS)
    assets["L1"][0]["measurements"]["Build.registered"]["v"] = "FAIL"  # invented failure on a registered writer
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / "inv", env["fp"], tool=e["sha"], assets=assets)
    c = cell(run(e), "T2", "build_registered_rederivation")
    assert c["verdict"] == "FAIL" and c["disagreements"][0]["asset"] == "ga_b"


def test_t2_registry_code_disagreement_expects_fail(env):
    # code registers a writer the census registry row says does not exist: expected FAIL (R43 class)
    assets = copy.deepcopy(LAYER_ASSETS)
    assets["L0"][1] = asset("bg_a", has_writer=False, reg="FAIL")
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / "dis", env["fp"], tool=e["sha"], assets=assets)
    c = cell(run(e), "T2", "build_registered_rederivation")
    assert c["verdict"] == "PASS", c  # code hit + has_writer False => FAIL expected and the census said FAIL


def test_t2_non_python_files_never_count_as_writers(env):
    # make ga_x appear only in a markdown file
    e2 = remake(env, mutate=lambda f: (f.__setitem__(WRITERS + "ga_x.py", "# nothing\n"), f.__setitem__(WRITERS + "x.md", "@register('ga_x')\n")))
    assert cell(run(e2), "T2", "build_registered_rederivation")["verdict"] == "FAIL"


def test_t2_docstring_mention_and_unresolved_constant_are_not_registrations(env):
    e = remake(env, mutate=lambda f: f.__setitem__(WRITERS + "ga_x.py", '"""The @register(\'ga_x\') decorator fires on import."""\n'))
    assert cell(run(e), "T2", "build_registered_rederivation")["verdict"] == "FAIL"
    e2 = remake(env, mutate=lambda f: f.__setitem__(WRITERS + "ga_x.py", "@register(SOME_OTHER)\nclass X: pass\n"))
    assert cell(run(e2), "T2", "build_registered_rederivation")["verdict"] == "FAIL"


def test_t2_asset_id_constant_form_is_resolved(env):
    # ka_a registers through `@register(ASSET_ID)` in the clean fixture; renaming the constant must break the match
    e = remake(env, mutate=lambda f: f.__setitem__(WRITERS + "ka_a.py", "ASSET_ID = 'ka_other'\n@register(ASSET_ID)\nclass D: pass\n"))
    c = cell(run(e), "T2", "build_registered_rederivation")
    assert c["verdict"] == "FAIL" and c["disagreements"][0]["asset"] == "ka_a"


def test_t2_unparsable_module_is_counted_not_fatal(env):
    e = remake(env, mutate=lambda f: f.__setitem__(WRITERS + "broken.py", "def (:\n register\n"))
    c = cell(run(e), "T2", "build_registered_rederivation")
    assert c["verdict"] == "PASS" and c["unparsable_modules"] == 1


def test_t2_absent_census_cell_is_a_disagreement_not_a_skip(env):
    assets = copy.deepcopy(LAYER_ASSETS)
    del assets["L2"][0]["measurements"]["Build.registered"]  # R56 class: a check silently absent
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / "absent", env["fp"], tool=e["sha"], assets=assets)
    c = cell(run(e), "T2", "build_registered_rederivation")
    assert c["verdict"] == "FAIL" and c["disagreements"][0]["census"] == "ABSENT"


# ───────────────────────────── T3 ─────────────────────────────

def test_t3_unearned_closure_fails(env):
    assets = copy.deepcopy(LAYER_ASSETS)
    assets["L1"][0]["measurements"]["Idem.pattern"]["v"] = "FAIL"  # the ledger says CLOSED, the census says FAIL
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / "unearned", env["fp"], tool=e["sha"], assets=assets)
    c = cell(run(e), "T3", "closures_earned")
    assert c["verdict"] == "FAIL" and c["unearned"] == ["ga_b-Idem.pattern"]
    assert cell(run(e), "T3", "closure_by_measurement")["verdict"] == "PASS"


@pytest.mark.parametrize("v", ["PASS", "N/A"])
def test_t3_closable_allowlist_is_pass_and_na(env, v):
    assets = copy.deepcopy(LAYER_ASSETS)
    assets["L1"][0]["measurements"]["Idem.pattern"]["v"] = v
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / f"ok{v[0]}", env["fp"], tool=e["sha"], assets=assets)
    assert cell(run(e), "T3", "closures_earned")["verdict"] == "PASS"


@pytest.mark.parametrize("v", ["PARTIAL", "NO_DETECTOR", "ERRORED", "NOT_GENERIC"])
def test_t3_nothing_else_closes(env, v):
    assets = copy.deepcopy(LAYER_ASSETS)
    assets["L1"][0]["measurements"]["Idem.pattern"]["v"] = v
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / f"bad{v}", env["fp"], tool=e["sha"], assets=assets)
    assert cell(run(e), "T3", "closures_earned")["verdict"] == "FAIL"


def test_t3_no_closure_in_ledger_is_unmeasured_not_fail_not_pass(env):
    def mut(f):
        rows = [json.loads(x) for x in f[GAPS].splitlines()]
        f[GAPS] = "".join(json.dumps(r) + "\n" for r in rows if not r.get("what", "").startswith("CLOSED by measurement"))
    card = run(remake(env, mut))
    assert cell(card, "T3", "closure_by_measurement")["verdict"] == "UNMEASURED"
    assert cell(card, "T3", "closures_earned")["verdict"] == "UNMEASURED"


def test_t3_retirement_closures_are_not_measurement_closures(env):
    def mut(f):
        rows = [json.loads(x) for x in f[GAPS].splitlines()]
        f[GAPS] = "".join(json.dumps(r) + "\n" for r in rows if not r.get("what", "").startswith("CLOSED by measurement"))
    c = cell(run(remake(env, mut)), "T3", "closure_by_measurement")
    assert c["retirement_closures"] == 1 and c["measurement_closures"] == 0


def test_t3_unjoinable_closure_is_unmeasured(env):
    def mut(f):
        f[GAPS] += json.dumps({"asset": "ga_gone", "gap_id": "ga_gone-Idem.pattern", "criterion": "Idem.pattern", "what": "x", "state": "OPEN"}) + "\n"
        f[GAPS] += json.dumps({"asset": "ga_gone", "gap_id": "ga_gone-Idem.pattern", "criterion": "Idem.pattern", "what": "CLOSED by measurement: x", "state": "CLOSED"}) + "\n"
    c = cell(run(remake(env, mut)), "T3", "closures_earned")
    assert c["verdict"] == "UNMEASURED" and c["unjoinable"] == ["ga_gone-Idem.pattern"]


def test_t3_closure_requires_a_prior_open_row_flip(env):
    def mut(f):
        rows = [json.loads(x) for x in f[GAPS].splitlines()]
        rows = [r for r in rows if not (r.get("gap_id") == "ga_b-Idem.pattern" and r.get("state") == "OPEN")]
        f[GAPS] = "".join(json.dumps(r) + "\n" for r in rows)
    assert cell(run(remake(env, mut)), "T3", "closure_by_measurement")["verdict"] == "UNMEASURED"


def test_t3_regression_reopen_observed_passes_and_final_state_is_last_wins(env):
    def mut(f):
        f[GAPS] += json.dumps({"asset": "ga_b", "gap_id": "ga_b-Idem.pattern", "criterion": "Idem.pattern", "what": "RE-OPENED by measurement: x / required: y", "state": "OPEN"}) + "\n"
    card = run(remake(env, mut))
    assert cell(card, "T3", "regression_reopen")["verdict"] == "PASS"
    # the gap is OPEN again: it is no longer a closure whose census cell must be PASS
    assert cell(card, "T3", "closures_earned")["verdict"] in ("PASS", "UNMEASURED")


def test_t3_reopen_before_any_closure_is_not_a_regression(env):
    def mut(f):
        rows = [json.loads(x) for x in f[GAPS].splitlines()]
        reopen = {"asset": "ga_x", "gap_id": "ga_x-Build.contract", "criterion": "Build.contract", "what": "RE-OPENED by measurement: x", "state": "OPEN"}
        f[GAPS] = "".join(json.dumps(r) + "\n" for r in rows) + json.dumps(reopen) + "\n"
    assert cell(run(remake(env, mut)), "T3", "regression_reopen")["verdict"] == "NO_DETECTOR"


# ───────────────────────────── T1 evidence ─────────────────────────────

def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def seal(d):
    """Recompute the record hash exactly as the plant harness defines it (written out independently of the generator)."""
    rec = {
        "harness_file_sha256": d.get("harness_file_sha256"), "runtime_files_sha256": d.get("runtime_files_sha256"),
        "inspector_tree_dirty": d.get("inspector_tree_dirty"), "runtime_files_dirty": d.get("runtime_files_dirty"),
        "inspector_blob_sha256": d["inspector_blob_sha256"], "registry": d["registry"], "partial": d.get("partial", False),
        "plants": [{k: r.get(k) for k in ("id", "check", "asset", "planted", "detected", "verdict_before", "verdict_after", "collateral",
                                           "same_asset_effects", "restore_ok", "error")} for r in d["plants"]],
        "unplantable": d["unplantable"], "unplantable_stale": d["unplantable_stale"], "uncovered_required": d["uncovered_required"],
        "mutation": {"suite_notices": d["mutation"].get("suite_notices"),
                     "mutants": [{k: m.get(k) for k in ("id", "check", "plant", "file", "noticed", "mutant_detected", "mutant_verdict_after")}
                                 for m in d["mutation"].get("mutants", [])]}}
    d["harness_sha256"] = hashlib.sha256(json.dumps(rec, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return d


def new_shape_evidence(**over):
    files = {rel: _sha(INSPECTOR_SRC if rel == INSPECTOR else HARNESS_SRC if rel == HARNESS_REL else fixture_runtime_text(rel))
             for rel in sc.T1_REQUIRED_RUNTIME_FILES}
    ev = {"schema": "nikasha_t1_evidence/1", "inspector_blob_sha256": files[INSPECTOR], "harness_file_sha256": files[HARNESS_REL],
          "runtime_files_sha256": files, "inspector_tree_dirty": False, "runtime_files_dirty": [],
          "registry": {"revision": 15, "fingerprint": "f" * 64}, "partial": False,
          "plants": [{"id": f"p{i}", "check": c, "asset": "ga_b", "planted": True, "detected": True, "collateral": [], "restore_ok": True}
                     for i, c in enumerate(["Build.registered", "Build.contract", "Idem.pattern"])],
          "unplantable": {}, "unplantable_stale": [], "uncovered_required": [],
          "mutation": {"suite_notices": True, "mutants": [{"id": "m1", "check": "Idem.pattern", "plant": "p2", "file": INSPECTOR,
                                                           "noticed": True, "mutant_detected": False, "mutant_verdict_after": "PASS"}]}}
    ev.update(over)
    return ev


def t1_evidence(env, sealed=True, **over):
    ev = new_shape_evidence(**over)
    if sealed:
        seal(ev)
    p = env["tmp"] / f"t1_{len(list(env['tmp'].iterdir()))}.json"
    p.write_text(json.dumps(ev))
    return p


def edit_ev(path, fn, sealed=True):
    d = json.loads(path.read_text())
    fn(d)
    if sealed:
        seal(d)
    path.write_text(json.dumps(d))
    return path


def plant_cell(env, ev):
    return cell(run(env, t1_evidence=ev), "T1", "plant_suite")


def test_t1_full_plant_evidence_passes_the_measurement_cells(env):
    card = run(env, t1_evidence=t1_evidence(env))
    assert cell(card, "T1", "plant_suite")["verdict"] == "PASS"
    assert cell(card, "T1", "mutation_notice")["verdict"] == "PASS"
    assert card["tests"]["T1"]["verdict"] == "PASS" and card["tests"]["T1"]["detail"] == "PASS"
    assert card["inputs"]["t1_evidence"]["sha256"] and "file" not in card["inputs"]["t1_evidence"]


def test_t1_zero_plants_never_passes_even_with_every_check_declared_unplantable(env):
    # H1 repro: plants [] + every required check "unplantable: x" + mutation notices => was PASS
    ev = t1_evidence(env, plants=[], unplantable={c: "x" for c in ("Build.registered", "Build.contract", "Idem.pattern")})
    card = run(env, t1_evidence=ev)
    assert cell(card, "T1", "plant_suite")["verdict"] == "UNMEASURED" and "no plant" in cell(card, "T1", "plant_suite")["reason"]
    assert card["tests"]["T1"]["verdict"] != "PASS"
    assert cell(card, "T1", "mutation_notice")["verdict"] == "UNMEASURED"


def test_t1_forged_harness_hash_of_zeros_is_not_a_measurement(env):
    # the review's forge repro: hand-written evidence with harness_sha256 all zeros
    ev = t1_evidence(env, sealed=False, harness_sha256="0" * 64)
    card = run(env, t1_evidence=ev)
    c = cell(card, "T1", "plant_suite")
    assert c["verdict"] == "UNMEASURED" and "recomputed from the record" in c["reason"]
    assert cell(card, "T1", "mutation_notice")["verdict"] == "UNMEASURED" and card["tests"]["T1"]["verdict"] != "PASS"


def test_t1_an_edited_result_breaks_the_record_hash(env):
    ev = edit_ev(t1_evidence(env), lambda d: d["plants"][0].update(detected=False), sealed=False)  # flipped after sealing
    assert plant_cell(env, ev)["verdict"] == "UNMEASURED"


def test_t1_older_evidence_shape_is_unmeasured_with_a_reason(env):
    old = {"schema": "nikasha_t1_evidence/1", "inspector_blob_sha256": _sha(INSPECTOR_SRC), "harness_sha256": "ab" * 32,
           "plants": new_shape_evidence()["plants"], "unplantable": {}, "mutation": {"suite_notices": True}}
    p = env["tmp"] / "old_shape.json"
    p.write_text(json.dumps(old))
    c = plant_cell(env, p)
    assert c["verdict"] == "UNMEASURED" and "older evidence shape" in c["reason"]


def test_t1_runtime_file_that_differs_from_the_ref_is_unmeasured_and_named(env):
    def mut(d):
        d["runtime_files_sha256"][D1_REL] = "1" * 64
    c = plant_cell(env, edit_ev(t1_evidence(env), mut))
    assert c["verdict"] == "UNMEASURED" and D1_REL in c["reason"]


def test_t1_harness_file_hash_must_match_the_blob_at_the_ref(env):
    def mut(d):
        d["harness_file_sha256"] = "2" * 64
        d["runtime_files_sha256"][HARNESS_REL] = "2" * 64
    c = plant_cell(env, edit_ev(t1_evidence(env), mut))
    assert c["verdict"] == "UNMEASURED" and HARNESS_REL in c["reason"]


def test_t1_harness_hash_field_must_equal_its_runtime_entry(env):
    c = plant_cell(env, edit_ev(t1_evidence(env), lambda d: d.update(harness_file_sha256="3" * 64)))
    assert c["verdict"] == "UNMEASURED" and "harness_file_sha256 does not equal" in c["reason"]


def test_t1_evidence_that_omits_the_inspector_or_harness_entry_is_unmeasured(env):
    for rel in (INSPECTOR, HARNESS_REL):
        def mut(d, rel=rel):
            d["runtime_files_sha256"].pop(rel)
        c = plant_cell(env, edit_ev(t1_evidence(env), mut))
        assert c["verdict"] == "UNMEASURED" and f"does not name {rel}" in c["reason"], rel


@pytest.mark.parametrize("field,val", [("inspector_tree_dirty", True), ("inspector_tree_dirty", None),
                                        ("runtime_files_dirty", [D1_REL]), ("runtime_files_dirty", None)])
def test_t1_dirty_or_unknown_tree_is_unmeasured(env, field, val):
    c = plant_cell(env, edit_ev(t1_evidence(env), lambda d: d.update({field: val})))
    assert c["verdict"] == "UNMEASURED" and "dirty or unknown tree" in c["reason"]


def test_t1_declared_unplantable_with_retest_counts_and_prints_the_count(env):
    ev = t1_evidence(env)
    edit_ev(ev, lambda d: d.update(plants=d["plants"][:1],
                                   unplantable={"Build.contract": "constant_verdict_no_per_asset_input", "Idem.pattern": "reported_not_graded"},
                                   unplantable_stale=[]))
    card = run(env, t1_evidence=ev)
    c = cell(card, "T1", "plant_suite")
    assert c["verdict"] == "PASS" and c["declared_unplantable"] == ["Build.contract", "Idem.pattern"] and c["detail"] == "PASS, 2 declared unplantable"
    assert card["tests"]["T1"]["detail"] == "PASS, 2 declared unplantable" and card["summary"]["details"]["T1"] == "PASS, 2 declared unplantable"
    assert card["tests"]["T1"]["verdict"] == "PASS"


def test_t1_cli_prints_the_declared_count_not_a_bare_pass(env, tmp_path, capsys):
    ev = t1_evidence(env)
    edit_ev(ev, lambda d: d.update(plants=d["plants"][:2], unplantable={"Idem.pattern": "reported_not_graded"}, unplantable_stale=[]))
    assert cli(env, "--t1-evidence", str(ev), out=tmp_path / "o.json")[0] == 0
    assert "PASS, 1 declared unplantable" in capsys.readouterr().out


def test_t1_record_missing_the_retest_field_cannot_be_read(env):
    ev = t1_evidence(env)
    d = json.loads(ev.read_text())
    d.pop("unplantable_stale")                      # the record hash cannot be recomputed without the re-test field
    ev.write_text(json.dumps(d))
    c = plant_cell(env, ev)
    assert c["verdict"] == "UNMEASURED" and "malformed" in c["reason"]


def test_t1_declaration_whose_retest_found_it_stale_is_not_coverage(env):
    ev = t1_evidence(env)
    def mut(d):
        d.update(plants=d["plants"][:2], unplantable={"Idem.pattern": "reported_not_graded"},
                 unplantable_stale=["Idem.pattern reads ['PASS'] (declared reported_not_graded: it must read only NOT_GENERIC)"])
    c = plant_cell(env, edit_ev(ev, mut))
    assert c["verdict"] == "PARTIAL" and c["uncovered"] == ["Idem.pattern"]
    assert c["declared_unplantable_refused"] == {"Idem.pattern": "the harness's re-test found the claim stale"}


def test_t1_declaration_reason_outside_the_closed_list_is_refused(env):
    ev = t1_evidence(env)
    edit_ev(ev, lambda d: d.update(plants=d["plants"][:2], unplantable={"Idem.pattern": "x"}))
    c = plant_cell(env, ev)
    assert c["verdict"] == "PARTIAL" and c["declared_unplantable_refused"] == {"Idem.pattern": "reason outside the closed list"}
    assert c["declared_unplantable"] == [] and c["detail"] == "PARTIAL"


def test_t1_retest_present_but_not_a_list_is_no_coverage(env):
    ev = t1_evidence(env)
    edit_ev(ev, lambda d: d.update(plants=d["plants"][:2], unplantable={"Idem.pattern": "reported_not_graded"}, unplantable_stale="none"))
    c = plant_cell(env, ev)
    assert c["verdict"] == "PARTIAL" and c["declared_unplantable_refused"]["Idem.pattern"] == "no re-test of the claim in the evidence"


def test_t1_declaration_of_a_non_required_check_does_not_count(env):
    ev = t1_evidence(env)
    edit_ev(ev, lambda d: d.update(plants=d["plants"][:2], unplantable={"Carr.D2": "reported_not_graded"}))
    c = plant_cell(env, ev)
    assert c["verdict"] == "PARTIAL" and c["declared_unplantable"] == [] and c["uncovered"] == ["Idem.pattern"]


def test_t1_undetected_declared_plus_plants_zero_never_passes(env):
    ev = t1_evidence(env)
    edit_ev(ev, lambda d: d.update(plants=[], unplantable={c: "reported_not_graded" for c in ("Build.registered", "Build.contract", "Idem.pattern")},
                                   unplantable_stale=[]))
    assert plant_cell(env, ev)["verdict"] == "UNMEASURED"


def test_t1_evidence_without_a_harness_run_is_unmeasured(env):
    ev = t1_evidence(env)
    edit_ev(ev, lambda d: d.pop("harness_sha256"), sealed=False)
    card = run(env, t1_evidence=ev)
    assert cell(card, "T1", "plant_suite")["verdict"] == "UNMEASURED" and "harness" in cell(card, "T1", "plant_suite")["reason"]
    assert cell(card, "T1", "mutation_notice")["verdict"] == "UNMEASURED"


@pytest.mark.parametrize("bad", ["x", "AB" * 32, "ab" * 31, 5])
def test_t1_malformed_harness_hash_is_a_script_error(env, bad):
    ev = t1_evidence(env, sealed=False, harness_sha256=bad)
    with pytest.raises(sc.ScorecardError):
        run(env, t1_evidence=ev)


def test_t1_undetected_plant_fails(env):
    ev = edit_ev(t1_evidence(env), lambda d: d["plants"][1].update(detected=False))
    c = plant_cell(env, ev)
    assert c["verdict"] == "FAIL" and c["undetected"] == ["p1"]


def test_t1_collateral_fails(env):
    ev = edit_ev(t1_evidence(env), lambda d: d["plants"][0].update(collateral=["ga_x"]))
    assert plant_cell(env, ev)["verdict"] == "FAIL"


def test_t1_uncovered_check_is_partial_and_named(env):
    ev = edit_ev(t1_evidence(env), lambda d: d.update(plants=d["plants"][:2]))
    c = plant_cell(env, ev)
    assert c["verdict"] == "PARTIAL" and c["uncovered"] == ["Idem.pattern"]


def test_t1_evidence_for_another_inspector_blob_is_stale(env):
    ev = t1_evidence(env, inspector_blob_sha256="f" * 64)
    c = plant_cell(env, ev)
    assert c["verdict"] == "UNMEASURED" and "stale" in c["reason"]
    assert cell(run(env, t1_evidence=ev), "T1", "mutation_notice")["verdict"] == "UNMEASURED"


def test_t1_unrestored_plant_is_unmeasured(env):
    ev = edit_ev(t1_evidence(env), lambda d: d["plants"][2].update(restore_ok=False))
    assert plant_cell(env, ev)["verdict"] == "UNMEASURED"


def test_t1_mutation_not_noticed_fails(env):
    ev = t1_evidence(env, mutation={"suite_notices": False, "mutants": []})
    assert cell(run(env, t1_evidence=ev), "T1", "mutation_notice")["verdict"] == "FAIL"


def test_t1_malformed_evidence_is_a_script_error(env):
    p = env["tmp"] / "bad_t1.json"
    p.write_text(json.dumps({"schema": "wrong"}))
    with pytest.raises(sc.ScorecardError):
        run(env, t1_evidence=p)


def test_t1_open_blocking_row_still_fails_the_test_despite_passing_plants(env):
    def mut(f):
        f[REGISTER] = register_text([(r, s, v, "OPEN" if r == "R52" else st) for r, s, v, st in CLEAN_ROWS])
    e = remake(env, mut)
    assert run(e, t1_evidence=t1_evidence(e))["tests"]["T1"]["verdict"] == "FAIL"


# ───────────────────────────── review round 3: T1 reader hardening ─────────────────────────────

class _StubRepo:
    """A ref whose file bytes are the fixture's: enough for t1_cells, which only asks `sha256(path)`."""
    def sha256(self, path):
        if path == INSPECTOR:
            return _sha(INSPECTOR_SRC)
        if path == HARNESS_REL:
            return _sha(HARNESS_SRC)
        return _sha(fixture_runtime_text(path)) if path in sc.T1_REQUIRED_RUNTIME_FILES else None


def t1_direct(facts, **over):
    doc = seal(new_shape_evidence(**over))
    return sc.t1_cells(dict(doc=doc), facts, _sha(INSPECTOR_SRC), _StubRepo())


FACTS_OK = {"criteria": {c: {"detector": sc.MEASURE_DETECTOR} for c in ("Build.registered", "Build.contract", "Idem.pattern")}}


def test_med1_empty_required_set_is_unmeasured_for_both_cells():
    plant_only_zzz = [{"id": "z", "check": "Zzz", "asset": "a", "planted": True, "detected": True, "collateral": [], "restore_ok": True}]
    for facts in ({"criteria": {"A.b": {"detector": "renamed"}}}, {}, {"criteria": {}}):
        plant, mut, _ = t1_direct(facts, plants=plant_only_zzz)
        assert plant["verdict"] == "UNMEASURED" and mut["verdict"] == "UNMEASURED", facts
        assert "required set is empty" in plant["reason"] or "not readable" in plant["reason"]


def test_med1_through_the_full_scorecard_a_renamed_detector_never_reads_covered(env):
    def mut(f):
        f[INSPECTOR] = INSPECTOR_SRC.replace('_M = "asset_census.py:measure()"', '_M = "renamed"')
    e = remake(env, mut)
    # the evidence must name the ref's inspector blob: rebuild it from the renamed source
    renamed = INSPECTOR_SRC.replace('_M = "asset_census.py:measure()"', '_M = "renamed"')
    ev = new_shape_evidence(inspector_blob_sha256=_sha(renamed))
    ev["runtime_files_sha256"][INSPECTOR] = _sha(renamed)
    seal(ev)
    p = e["tmp"] / "renamed_ev.json"
    p.write_text(json.dumps(ev))
    c = cell(run(e, t1_evidence=p), "T1", "plant_suite")
    assert c["verdict"] == "UNMEASURED" and "required set is empty" in c["reason"]


BAD_PLANT = {"id": "px", "check": "Build.registered", "asset": "ga_b", "planted": False, "detected": False, "collateral": [],
             "restore_ok": True, "error": "HarnessError: boom"}


def test_med2_a_plant_that_was_not_planted_or_errored_fails_the_cell():
    for extra in ({"planted": False, "detected": False}, {"error": "HarnessError: boom"}, {"harness_error": "boom"},
                  {"planted": False, "detected": True}):
        bad = {**BAD_PLANT, **{"planted": True, "detected": True, "error": None}, **extra}
        ev_plants = new_shape_evidence()["plants"][1:] + [bad]
        plant, _m, _n = t1_direct(FACTS_OK, plants=ev_plants)
        assert plant["verdict"] == "FAIL" and plant["faulty_plants"] == ["px"], extra


def test_med2_the_reviewers_record_never_passes_even_when_the_check_is_declared_unplantable():
    plants = new_shape_evidence()["plants"][1:] + [BAD_PLANT]
    plant, _m, _n = t1_direct(FACTS_OK, plants=plants,
                              unplantable={"Build.registered": "reported_not_graded"}, unplantable_stale=[])
    assert plant["verdict"] == "FAIL" and plant["faulty_plants"] == ["px"]
    assert plant["declared_unplantable"] == ["Build.registered"]   # the declaration is honoured; the faulty plant still fails the cell


@pytest.mark.parametrize("planted", [None, "yes", 0, 1])
def test_med2_planted_must_be_exactly_true(planted):
    plants = new_shape_evidence()["plants"]
    plants[0] = {**plants[0], "planted": planted}
    plant, _m, _n = t1_direct(FACTS_OK, plants=plants)
    assert plant["verdict"] == "FAIL" and plant["faulty_plants"] == ["p0"]


def test_med2_a_faulty_plant_is_not_coverage():
    only_bad = [{**BAD_PLANT, "planted": True, "detected": True, "error": "boom"}]
    plant, _m, _n = t1_direct(FACTS_OK, plants=only_bad)
    assert plant["verdict"] == "FAIL" and "Build.registered" in plant["uncovered"]


@pytest.mark.parametrize("entry", ["Idem.pattern", "Idem.pattern: stale", "Idem.pattern\treads x", "  Idem.pattern reads ['PASS']",
                                    "Idem.pattern."])
def test_low1_every_way_of_naming_the_check_refuses_the_declaration(entry):
    plants = new_shape_evidence()["plants"][:2]
    plant, _m, _n = t1_direct(FACTS_OK, plants=plants, unplantable={"Idem.pattern": "reported_not_graded"}, unplantable_stale=[entry])
    assert plant["verdict"] == "PARTIAL" and plant["declared_unplantable_refused"] == {"Idem.pattern": "the harness's re-test found the claim stale"}


@pytest.mark.parametrize("entry", ["Idem.patternX reads x", "Idem.pattern.sub reads x", "Other.check reads x", "xIdem.pattern"])
def test_low1_a_longer_name_does_not_name_the_check(entry):
    plants = new_shape_evidence()["plants"][:2]
    plant, _m, _n = t1_direct(FACTS_OK, plants=plants, unplantable={"Idem.pattern": "reported_not_graded"}, unplantable_stale=[entry])
    assert plant["verdict"] == "PASS" and plant["declared_unplantable"] == ["Idem.pattern"]


@pytest.mark.parametrize("bad", [{"check": "Idem.pattern"}, ["Idem.pattern"], 5, None])
def test_low1_a_non_string_retest_entry_refuses_every_declaration(bad):
    plants = new_shape_evidence()["plants"][:1]
    plant, _m, _n = t1_direct(FACTS_OK, plants=plants,
                              unplantable={"Build.contract": "reported_not_graded", "Idem.pattern": "reported_not_graded"},
                              unplantable_stale=["unrelated text", bad])
    assert plant["verdict"] == "PARTIAL" and plant["declared_unplantable"] == []
    assert set(plant["declared_unplantable_refused"].values()) == {"the re-test carries a non-string entry: unreadable"}


def test_low2_partial_run_is_not_a_t1_record():
    plant, mut, _ = t1_direct(FACTS_OK, partial=True)
    assert plant["verdict"] == "UNMEASURED" and "partial" in plant["reason"] and mut["verdict"] == "UNMEASURED"


def test_low2_harness_reported_uncovered_required_is_not_a_pass():
    plant, mut, _ = t1_direct(FACTS_OK, uncovered_required=["Idem.pattern"])
    assert plant["verdict"] == "UNMEASURED" and "uncovered required" in plant["reason"] and mut["verdict"] == "UNMEASURED"


def test_low2_suite_notices_true_needs_listed_mutants_all_noticed():
    _p, mut, _ = t1_direct(FACTS_OK, mutation={"suite_notices": True, "mutants": []})
    assert mut["verdict"] == "UNMEASURED" and "lists no mutant" in mut["reason"]
    good = new_shape_evidence()["mutation"]["mutants"][0]
    _p, mut, _ = t1_direct(FACTS_OK, mutation={"suite_notices": True, "mutants": [good, {**good, "id": "m2", "noticed": False}]})
    assert mut["verdict"] == "FAIL" and "not noticed" in mut["reason"]
    _p, mut, _ = t1_direct(FACTS_OK, mutation={"suite_notices": True, "mutants": [good, {**good, "id": "m2", "noticed": "yes"}]})
    assert mut["verdict"] == "FAIL"
    _p, mut, _ = t1_direct(FACTS_OK, mutation={"suite_notices": True, "mutants": [good]})
    assert mut["verdict"] == "PASS"


def test_low2_choice_documented_suite_notices_not_claimed_keeps_todays_reading():
    # mutants empty is acceptable ONLY when no notice is claimed: the cell stays NO_DETECTOR (never PASS)
    _p, mut, _ = t1_direct(FACTS_OK, mutation={"suite_notices": None, "mutants": []})
    assert mut["verdict"] == "NO_DETECTOR"


@pytest.mark.parametrize("val", [False, None, "true", 1, 0])
def test_low2_restore_ok_must_be_exactly_true(val):
    plants = new_shape_evidence()["plants"]
    plants[0] = {**plants[0], "restore_ok": val}
    plant, _m, _n = t1_direct(FACTS_OK, plants=plants)
    assert plant["verdict"] == "UNMEASURED" and "not restored" in plant["reason"]


@pytest.mark.parametrize("val", [None, "ga_x", {"a": 1}, 0])
def test_low2_collateral_must_be_a_list(val):
    plants = new_shape_evidence()["plants"]
    plants[0] = {**plants[0], "collateral": val}
    plant, mut, _ = t1_direct(FACTS_OK, plants=plants)
    assert plant["verdict"] == "UNMEASURED" and "collateral is not a list" in plant["reason"] and mut["verdict"] == "UNMEASURED"


def test_low3_every_required_runtime_file_must_be_named():
    for rel in sc.T1_REQUIRED_RUNTIME_FILES:
        def drop(rel=rel):
            ev = new_shape_evidence()
            ev["runtime_files_sha256"].pop(rel)
            if rel == INSPECTOR:
                return None
            return seal(ev)
        doc = drop()
        if doc is None:
            continue
        plant, _m, _n = sc.t1_cells(dict(doc=doc), FACTS_OK, _sha(INSPECTOR_SRC), _StubRepo())
        assert plant["verdict"] == "UNMEASURED" and f"does not name {rel}" in plant["reason"], rel


def test_low3_extra_runtime_files_are_allowed_when_they_match_the_ref():
    extra = "platform/scripts/governance/cited_by_the_d1_declaration.py"

    class Repo(_StubRepo):
        def sha256(self, path):
            return _sha("# extra\n") if path == extra else super().sha256(path)
    doc = new_shape_evidence()
    doc["runtime_files_sha256"][extra] = _sha("# extra\n")
    seal(doc)
    plant, _m, _n = sc.t1_cells(dict(doc=doc), FACTS_OK, _sha(INSPECTOR_SRC), Repo())
    assert plant["verdict"] == "PASS"


def _importable_harness():
    import os
    cand = [os.environ.get("NIKASHA_PLANT_MODULE"), str(HERE.parent / "nikasha_plant.py")]
    for c in cand:
        if c and pathlib.Path(c).is_file():
            spec = importlib.util.spec_from_file_location("nikasha_plant_under_test", c)
            m = importlib.util.module_from_spec(spec)
            sys.modules["nikasha_plant_under_test"] = m
            spec.loader.exec_module(m)
            return m
    return None


HARNESS_SKIP = ("the plant harness (nikasha_plant.py, PR #3088) is not on this branch: the scorecard keeps its own named constant and "
                "record-hash definition, and this agreement test runs when the harness is importable (set NIKASHA_PLANT_MODULE)")


def test_low3_required_file_constant_agrees_with_the_harness_constants_when_importable():
    h = _importable_harness()
    if h is None:
        pytest.skip(HARNESS_SKIP)
    static = set(h.RUNTIME_FILES) | {h.DECLARATIONS_REL, h.D1_FIXTURE_REL, h.GEN_REL}
    assert set(sc.T1_REQUIRED_RUNTIME_FILES) == static
    assert sc.HARNESS_REL == h.GEN_REL and sc.E1_T1_SCHEMA == h.SCHEMA


def test_record_hash_definition_agrees_with_the_harness_when_importable():
    h = _importable_harness()
    if h is None:
        pytest.skip(HARNESS_SKIP)
    doc = seal(new_shape_evidence(plants=new_shape_evidence()["plants"] + [{**BAD_PLANT, "same_asset_effects": {"x": "a->b"}}]))
    assert sc.t1_record_sha256(doc) == h.run_record_sha256(doc) == doc["harness_sha256"]
    doc["plants"][0]["detected"] = False
    assert sc.t1_record_sha256(doc) == h.run_record_sha256(doc) != doc["harness_sha256"]


def test_the_record_hash_is_defined_once_in_the_harness_and_imported_by_the_scorecard():
    """SS review of #3043: no second definition that could drift. The scorecard's function is a thin import of the harness's own."""
    src = (HERE.parent / "nikasha_scorecard.py").read_text(encoding="utf-8")
    assert "harness_file_sha256=doc.get" not in src and "run_record_sha256" in src
    h = _importable_harness()
    if h is None:
        pytest.skip("the plant harness is not importable here")
    doc = seal(new_shape_evidence())
    assert sc.t1_record_sha256(doc) == h.run_record_sha256(doc) == doc["harness_sha256"]


def test_an_unloadable_harness_makes_the_evidence_unmeasured_not_silently_trusted(env, monkeypatch):
    def boom():
        raise sc.ScorecardError("the plant harness (nikasha_plant.py) cannot be loaded, so the evidence record hash cannot be recomputed: blocked for the test")
    monkeypatch.setattr(sc, "_plant_module", boom)
    card = run(env, t1_evidence=t1_evidence(env))
    t1 = card["tests"]["T1"]
    assert t1["verdict"] == "UNMEASURED" and "cannot be loaded" in json.dumps(t1)


def test_low4_summary_carries_the_declared_count_and_the_note(env):
    ev = t1_evidence(env)
    edit_ev(ev, lambda d: d.update(plants=d["plants"][:2], unplantable={"Idem.pattern": "reported_not_graded"}, unplantable_stale=[]))
    card = run(env, t1_evidence=ev)
    assert card["summary"]["t1_declared_unplantable"] == 1 and "t1_declared_unplantable" in card["summary"]["all_tests_pass_note"]
    assert run(env)["summary"]["t1_declared_unplantable"] == 0
    clean = run(env, t1_evidence=t1_evidence(env))
    assert clean["summary"]["t1_declared_unplantable"] == 0


# ───────────────────────────── T5 seeded defects ─────────────────────────────

def _sub(path, old, new):
    def m(f):
        assert old in f[path], (path, old)
        f[path] = f[path].replace(old, new)
    return m


def _append(path, text):
    def m(f):
        f[path] += text
    return m


T5_SEEDS = [
    ("eight_gates_text", _append(T4D, "the eight gates\n")),
    ("eight_gates_text", _append(PILOT, "## §4 · the eight gates\n")),
    ("eight_gates_text", _append(L0D, "the eight gates\n")),
    ("t4_heading_checks", _append(T4D, "### 4.2 · Buildability — the six checks, and what\n")),
    ("tracker_comment", _append(TRACKER, "# The certified gates. Eight, not thirty-three.\n")),
    ("t3_gate_map_count", _append(T3D, "§5.2's eight-row map\n")),
    ("verdict_spelling", _append(T3D, "result is NO DETECTOR here\n")),
    ("verdict_spelling", _append(T4D, "NA if never run\n")),
    ("l0_denominator", _append(L0D, "gates certified 0/320\n")),
    ("t1_review_record", _sub(T1D, "REVIEW_PRODUCT_DEFINITION_v3_1.md", "REVIEW_MISSING.md")),
    ("t2_review_counts", _sub(T2D, "2 BLOCKER + 9 MAJOR + 10 MINOR", "2 BLOCKER + 10 MAJOR + 11 MINOR")),
    ("t2_element_count", _sub(T2D, "§13.3 is ten elements", "§13.3 is nine elements")),
    ("eight_gates_text", _sub(T4D, "inherits: layer 5.2 (a) the nine gates", "inherits: layer 5.2 (a) the eight gates")),
    ("transfers_contradiction", _append(T3D, "4. **Presentation parity** holds for the layer's served surface.\n")),
    ("gate_set_agreement", _sub(TRACKER, '("Build","buildability","always","x"),\n', "")),
    ("gate_set_agreement", _sub(TRACKER, '("Null","honest null","always","x"),\n', '("Null","honest null","always","x"),\n ("Fct","extra","always","x"),\n')),
    ("gate_set_agreement", _sub(T4D, "| **Dens** gate | x |\n", "")),
    ("manifest_root_fingerprint", _sub(MANIFEST, '"entry_count": 1', '"entry_count": 2')),
    ("ledger_criteria_registered", _append(GAPS, json.dumps({"asset": "bg_a", "gap_id": "bg_a-G01", "criterion": "Hand.invented", "what": "x", "state": "OPEN"}) + "\n")),
    ("ledger_state_vocabulary", _append(GAPS, json.dumps({"asset": "bg_a", "gap_id": "bg_a-Idem.pattern", "criterion": "Idem.pattern", "what": "x", "state": "DONE"}) + "\n")),
]


@pytest.mark.parametrize("name,mut", T5_SEEDS, ids=[f"{n}-{i}" for i, (n, _) in enumerate(T5_SEEDS)])
def test_t5_seeded_defect_flips_its_cell(env, name, mut):
    clean = run(env)
    assert t5(clean, name)["verdict"] == "PASS", t5(clean, name)
    card = run(remake(env, mut))
    assert t5(card, name)["verdict"] == "FAIL", t5(card, name)
    assert card["tests"]["T5"]["verdict"] == "FAIL"
    # only the seeded cell moved to FAIL among the repo-derived cells
    others = [n for n, c in card["tests"]["T5"]["cells"].items() if c["verdict"] == "FAIL" and n != name]
    assert others == [], others


def test_t5_removing_an_input_is_unmeasured_not_pass(env):
    for path, cellname in [(T4D, "eight_gates_text"), (T3D, "t3_gate_map_count"), (TRACKER, "tracker_comment"), (L0D, "l0_denominator"),
                           (T2D, "t2_review_counts"), (T1D, "t1_review_record"), (MANIFEST, "manifest_root_fingerprint"),
                           (GAPS, "ledger_criteria_registered")]:
        card = run(remake(env, delete=[path]))
        assert t5(card, cellname)["verdict"] in ("UNMEASURED", "NO_DETECTOR"), (path, cellname, t5(card, cellname))
        assert card["tests"]["T5"]["verdict"] != "PASS"


def test_t5_transfers_resolved_either_way_passes(env):
    # remedy A: T3 test 4 reworded; remedy B: T2 un-marks parity. Both clear the contradiction.
    a = run(env)
    assert t5(a, "transfers_contradiction")["verdict"] == "PASS"
    def mut(f):
        f[T3D] += "4. **Presentation parity** holds for the layer's served surface.\n"
        f[T2D] = f[T2D].replace("**[TRANSFERS]**", "")
    assert t5(run(remake(env, mut)), "transfers_contradiction")["verdict"] == "PASS"


def test_t5_manifest_tier_entries_detector(env):
    assert t5(run(env), "manifest_tier_entries")["verdict"] == "NO_DETECTOR"
    good = hashlib.sha256(env["files"][T4D].encode()).hexdigest()
    def with_entry(fp):
        def mut(f):
            entries = [{"canonical_id": "ASSET_ELEVATION_TEMPLATE", "path": T4D, "fingerprint_sha256": fp}]
            f[MANIFEST] = manifest_text(f, entries)
        return mut
    assert t5(run(remake(env, with_entry(good))), "manifest_tier_entries")["verdict"] == "PASS"
    assert t5(run(remake(env, with_entry("0" * 64))), "manifest_tier_entries")["verdict"] == "FAIL"


def test_t5_review_record_renamed_to_document_reviews(env):
    def mut(f):
        f[T1D] = "---\ndocument_reviews:\n  - briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md\n---\n"
    assert t5(run(remake(env, mut)), "t1_review_record")["verdict"] == "PASS"
    def bad(f):
        f[T1D] = "---\ndocument_reviews:\n  - briefs/reviews/NOPE.md\n---\n"
    assert t5(run(remake(env, bad)), "t1_review_record")["verdict"] == "FAIL"
    def none(f):
        f[T1D] = "---\ntitle: x\n---\n"
    assert t5(run(remake(env, none)), "t1_review_record")["verdict"] == "NO_DETECTOR"


def test_t5_every_cell_names_its_register_row_or_finding(env):
    for name, c in run(env)["tests"]["T5"]["cells"].items():
        if c["kind"] == "measurement":
            assert c.get("binds"), name


# ───────────────────────────── engine_build_checks ─────────────────────────────

def test_engine_build_checks_aggregate(env):
    assets = copy.deepcopy(LAYER_ASSETS)
    assets["L3"][0]["measurements"]["Build.contract"]["v"] = "FAIL"
    assets["L4"][0]["measurements"]["Build.registered"]["v"] = "NO_DETECTOR"
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / "ebc", env["fp"], tool=e["sha"], assets=assets)
    card = run(e)
    assert card["engine_build_checks"]["Build.contract"] == "FAIL"
    assert card["engine_build_checks"]["Build.registered"] == "NO_DETECTOR"
    assert card["engine_claims_not_covered"]


def test_engine_build_checks_come_from_registry_build_gate_only(env):
    assert set(run(env)["engine_build_checks"]) == {"Build.registered", "Build.contract"}  # Idem.pattern is not a Build check


# ───────────────────────────── CLI: generate / --check ─────────────────────────────

def cli(env, *extra, out=None):
    out = out or (env["tmp"] / "out.json")
    argv = ["--repo", str(env["repo"]), "--ref", env["sha"], "--census-dir", str(env["cdir"]), "--out", str(out), *extra]
    return sc.main(argv), out


def test_cli_generate_writes_only_the_out_file(env, capsys):
    before = _git(env["repo"], "status", "--porcelain")
    rc, out = cli(env)
    assert rc == 0 and out.exists()
    assert _git(env["repo"], "status", "--porcelain") == before == ""
    assert json.loads(out.read_text())["ref"] == env["sha"]
    assert "T1" in capsys.readouterr().out


def test_cli_check_exit_codes(env, capsys):
    rc, out = cli(env)
    assert rc == 0
    assert cli(env, "--check", out=out)[0] == 0
    # a hand-edited verdict (the scorecard lying) is exit 2
    d = json.loads(out.read_text())
    d["tests"]["T5"]["verdict"] = "PASS"
    out.write_text(sc.render(d))
    rc, _ = cli(env, "--check", out=out)
    assert rc == 2
    assert "T5" in capsys.readouterr().out
    # a flipped census cell changes the fresh recompute: stale committed scorecard is exit 2
    rc, out2 = cli(env, out=env["tmp"] / "out2.json")
    doc = json.loads((env["cdir"] / "census_L1.json").read_text())
    doc["L1"]["assets"][0]["measurements"]["Idem.pattern"]["v"] = "ERRORED"
    (env["cdir"] / "census_L1.json").write_text(json.dumps(doc))
    assert cli(env, "--check", out=out2)[0] == 2


def test_cli_check_uses_the_recorded_ref(env):
    rc, out = cli(env)
    # a later commit must not change what the committed scorecard recomputes to
    (env["repo"] / "later.txt").write_text("x")
    _git(env["repo"], "add", "-A")
    _commit(env["repo"], "later")
    argv = ["--repo", str(env["repo"]), "--census-dir", str(env["cdir"]), "--out", str(out), "--check"]
    assert sc.main(argv) == 0


def test_cli_check_errors_are_exit_5(env, capsys):
    rc, out = cli(env)
    assert sc.main(["--repo", str(env["repo"]), "--out", str(env["tmp"] / "missing.json"), "--check"]) == 5
    assert sc.main(["--repo", str(env["repo"]), "--ref", "nonexistent-ref", "--out", str(env["tmp"] / "x.json")]) == 5
    bad = env["tmp"] / "bad.json"
    bad.write_text("{nope")
    assert sc.main(["--repo", str(env["repo"]), "--out", str(bad), "--check"]) == 5
    assert "nikasha_scorecard" in capsys.readouterr().err
    # a list / foreign JSON is named as not-a-scorecard, not a stack trace
    lst = env["tmp"] / "list.json"
    lst.write_text("[1, 2]")
    assert sc.main(["--repo", str(env["repo"]), "--out", str(lst), "--check"]) == 5
    assert "not a scorecard" in capsys.readouterr().err
    # recorded T1 evidence but none supplied: refuse rather than recompute without it
    ev = t1_evidence(env)
    out2 = env["tmp"] / "withev.json"
    assert cli(env, "--t1-evidence", str(ev), out=out2)[0] == 0
    assert cli(env, "--check", out=out2)[0] == 5


def test_cli_check_detects_a_generator_change(env, monkeypatch):
    rc, out = cli(env)
    d = json.loads(out.read_text())
    d["generator_sha256"] = "0" * 64
    out.write_text(sc.render(d))
    assert cli(env, "--check", out=out)[0] == 2


# ───────────────────────────── the real repository ─────────────────────────────

def _real_repo_is_shallow():
    p = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--is-shallow-repository"], capture_output=True, text=True)
    return p.stdout.strip() == "true"


SHALLOW_SKIP = ("the real checkout is a shallow clone (CI's default fetch-depth 1): the generator refuses a shallow repository by "
                "design, so a test that needs the real history cannot run; E1.7's CI job uses fetch-depth: 0")


def test_real_repo_without_census_has_no_census_cell_passing(tmp_path):
    if _real_repo_is_shallow():
        pytest.skip(SHALLOW_SKIP)
    card = sc.build_scorecard(REPO, "HEAD", census_dir=tmp_path, t1_evidence=None)
    for layer in ("L1", "L2", "L3", "L4", "L5"):
        assert card["tests"]["T4"]["cells"][layer]["verdict"] == "UNMEASURED"
    assert card["tests"]["T2"]["cells"]["build_registered_rederivation"]["verdict"] == "UNMEASURED"
    assert card["tests"]["T3"]["cells"]["closure_by_measurement"]["verdict"] == "UNMEASURED"
    assert all(t["verdict"] != "PASS" for t in card["tests"].values())
    src = subprocess.run(["git", "-C", str(REPO), "show", "HEAD:" + INSPECTOR], capture_output=True, text=True, check=True).stdout
    assert card["registry"]["revision"] == int(re.search(r"(?m)^REGISTRY_REVISION = (\d+)", src).group(1))
    assert len(card["registry"]["fingerprint"]) == 64
    json.dumps(card)


# ───────────────────────────── review round (H2, H4, H5, M1-M5, LOW) ─────────────────────────────

DECL = "platform/scripts/governance/asset_declarations.json"


def _census_env(env, name, **kw):
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / name, env["fp"], **{"tool": e["sha"], **kw})
    return e


def test_h2_repro_ref_fingerprint_but_zero_tool_commit_and_foreign_declarations_is_stale(env):
    e = remake(env, mutate=lambda f: f.__setitem__(DECL, '{"version": "1"}'), census=False)
    e["cdir"] = write_census(env["tmp"] / "h2", env["fp"], tool="0" * 40, decl="f" * 64)
    card = run(e)
    for lyr in ("L1", "L2", "L3", "L4", "L5"):
        c = cell(card, "T4", lyr)
        assert c["verdict"] == "UNMEASURED" and c["observed_on_stale_input"] == "would_be_PASS", (lyr, c)
    assert all(i["fresh"] is False for i in card["inputs"]["census"])


@pytest.mark.parametrize("tool", [None, "", "abc123", "0" * 40, "g" * 40])
def test_h2_missing_or_malformed_tool_commit_is_stale(env, tool):
    c = cell(run(_census_env(env, "tc", tool=tool)), "T4", "L1")
    assert c["verdict"] == "UNMEASURED" and "tool_commit missing" in c["reason"]


def test_h2_tool_commit_not_in_the_repository_is_stale(env):
    c = cell(run(_census_env(env, "nr", tool="1" * 40)), "T4", "L1")
    assert c["verdict"] == "UNMEASURED" and "not in this repository" in c["reason"]


def test_h2_inspector_blob_at_tool_commit_must_equal_the_blobs_at_the_ref(env):
    # same registry fingerprint (the inspector's detector code changed, the registry did not): the fingerprint alone says fresh
    def mut(f):
        f[INSPECTOR] = INSPECTOR_SRC + "\n# detector SQL changed here\n"
    e2 = remake(env, mut, census=False)
    # census claims the OLD commit (original inspector) as its tool_commit
    e2["cdir"] = write_census(env["tmp"] / "blob", env["fp"], tool=env["sha"])
    # the old commit is not in e2's repository; rebuild so it is: add a commit to the ORIGINAL repo changing the inspector
    (env["repo"] / INSPECTOR).write_text(INSPECTOR_SRC + "\n# detector SQL changed here\n")
    _git(env["repo"], "add", "-A")
    _commit(env["repo"], "inspector detector changed")
    later = _git(env["repo"], "rev-parse", "HEAD")
    card = sc.build_scorecard(env["repo"], later, census_dir=env["cdir"])
    c = cell(card, "T4", "L1")
    assert c["verdict"] == "UNMEASURED" and "inspector blob at tool_commit differs" in c["reason"]
    assert card["registry"]["fingerprint"] == env["fp"]   # the registry fingerprint did NOT move: only the blob compare catches it


def test_h2_declarations_sha_must_equal_the_declarations_blob_at_the_ref(env):
    decl = '{"version": "1.0"}'
    e = remake(env, mutate=lambda f: f.__setitem__(DECL, decl), census=False)
    good = hashlib.sha256(decl.encode()).hexdigest()
    e["cdir"] = write_census(env["tmp"] / "dg", env["fp"], tool=e["sha"], decl=good)
    assert cell(run(e), "T4", "L1")["verdict"] == "PASS"
    e["cdir"] = write_census(env["tmp"] / "db", env["fp"], tool=e["sha"], decl="0" * 63 + "1")
    c = cell(run(e), "T4", "L1")
    assert c["verdict"] == "UNMEASURED" and "declarations_sha256" in c["reason"]
    e["cdir"] = write_census(env["tmp"] / "dn", env["fp"], tool=e["sha"], decl=None)   # census predates the stamp
    assert cell(run(e), "T4", "L1")["verdict"] == "UNMEASURED"


def test_h2_census_inputs_record_the_identities_checked(env):
    rec = run(env)["inputs"]["census"][0]
    assert {"tool_commit", "declarations_sha256", "registry_fingerprint", "sha256", "fresh"} <= set(rec)


def test_h4_gate_set_cell_is_not_bound_to_the_open_six_static_checks_row(env):
    b = t5(run(env), "gate_set_agreement")["binds"]
    assert "R65" not in b and "R67" not in b


def test_h5_historical_changelog_wording_never_counts_but_body_wording_does(env):
    clean = run(env)
    assert "an eight-row map" in env["files"][T3D] and "NO DETECTOR is never a pass" in env["files"][T3D]
    assert "the eight gates" in env["files"][T4D] and "NA if never run" in env["files"][T4D]
    for n in ("t3_gate_map_count", "verdict_spelling", "eight_gates_text", "transfers_contradiction"):
        assert t5(clean, n)["verdict"] == "PASS", n
    # a body hit still fails, with the historical frontmatter hit present alongside it
    card = run(remake(env, _append(T3D, "§5.2's eight-row map\n")))
    assert t5(card, "t3_gate_map_count")["verdict"] == "FAIL"


def test_h5_applying_exactly_the_registers_fixes_takes_every_subcheck_to_pass(env):
    # the PRE-fix state: every register defect in the body, historical lines in the frontmatter (as in the real documents)
    def prefix(f):
        for _n, m in T5_SEEDS:
            m(f)
    pre = run(remake(env, prefix))
    failing = {n for n, c in pre["tests"]["T5"]["cells"].items() if c["verdict"] == "FAIL" and c["kind"] == "measurement"}
    assert {"t3_gate_map_count", "verdict_spelling", "t2_review_counts", "t2_element_count", "eight_gates_text", "l0_denominator",
            "transfers_contradiction", "t1_review_record", "tracker_comment", "t4_heading_checks"} <= failing
    # the POST-fix state is the clean fixture, which still carries every historical quotation
    post = run(env)
    assert {n for n, c in post["tests"]["T5"]["cells"].items() if c["kind"] == "measurement" and c["verdict"] == "FAIL"} == set()


def test_h5_r75_annotation_remedy_is_accepted(env):
    def mut(f):
        f[T2D] = f[T2D].replace("§13.3 is ten elements and says so", "§13.3 is nine elements and says so (1b added after this entry)")
    assert t5(run(remake(env, mut)), "t2_element_count")["verdict"] == "PASS"
    def bad(f):
        f[T2D] = f[T2D].replace("§13.3 is ten elements and says so", "§13.3 is nine elements and says so")
    assert t5(run(remake(env, bad)), "t2_element_count")["verdict"] == "FAIL"


def test_h5_r73_only_the_v3_review_line_counts(env):
    # the historical "was: ... 10 MAJOR + 11 MINOR" changelog line is present in the clean fixture and passes
    assert "10 MAJOR + 11 MINOR" in env["files"][T2D] and t5(run(env), "t2_review_counts")["verdict"] == "PASS"


def test_m1_fail_basis_distinguishes_precondition_from_measured(env):
    def mut(f):
        f[REGISTER] = register_text([(r, s, v, "OPEN" if r == "R24" else st) for r, s, v, st in CLEAN_ROWS])
    card = run(remake(env, mut))
    t4 = card["tests"]["T4"]
    assert t4["verdict"] == "FAIL" and t4["fail_basis"] == "precondition: known_defect_rows (R24 open)"
    assert card["tests"]["T3"]["fail_basis"] is None
    card2 = run(remake(env, _append(T4D, "the eight gates\n")))
    assert card2["tests"]["T5"]["fail_basis"].startswith("measured: eight_gates_text")


def test_m2_t4_layer_requires_unique_ids_and_a_measured_cell_per_asset(env):
    assets = copy.deepcopy(LAYER_ASSETS)
    assets["L2"] = [asset("bo_a"), asset("bo_a")]
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / "dup", env["fp"], tool=e["sha"], assets=assets)
    c = cell(run(e), "T4", "L2")
    assert c["verdict"] == "FAIL" and c["duplicate_asset_ids"] == ["bo_a"]
    assets = copy.deepcopy(LAYER_ASSETS)
    assets["L4"][0]["measurements"] = {}
    e["cdir"] = write_census(env["tmp"] / "nocell", env["fp"], tool=e["sha"], assets=assets)
    c = cell(run(e), "T4", "L4")
    assert c["verdict"] == "FAIL" and c["assets_without_a_measured_cell"] == ["ph_a"]
    assets = copy.deepcopy(LAYER_ASSETS)
    assets["L4"][0]["measurements"] = {"Idem.pattern": {"v": "ERRORED"}}
    e["cdir"] = write_census(env["tmp"] / "allerr", env["fp"], tool=e["sha"], assets=assets)
    assert cell(run(e), "T4", "L4")["verdict"] == "FAIL"


def test_m3_shallow_clone_is_refused(env, tmp_path):
    (env["repo"] / "more.txt").write_text("x")
    _git(env["repo"], "add", "-A")
    _commit(env["repo"], "second")
    clone = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "1", "file://" + str(env["repo"]), str(clone)], check=True)
    with pytest.raises(sc.ScorecardError) as ei:
        sc.build_scorecard(clone, "HEAD")
    assert "shallow" in str(ei.value) and "fetch-depth: 0" in str(ei.value)
    assert sc.main(["--repo", str(clone), "--out", str(tmp_path / "s.json")]) == 5


def test_m4_generator_at_ref_is_reconciled(env):
    gen = GEN_PATH.read_text()
    same = remake(env, mutate=lambda f: f.__setitem__("platform/scripts/governance/nikasha_scorecard.py", gen))
    assert run(same)["generator_matches_ref"] is True
    diff = remake(env, mutate=lambda f: f.__setitem__("platform/scripts/governance/nikasha_scorecard.py", gen + "\n# other\n"))
    card = run(diff)
    assert card["generator_matches_ref"] is False and card["summary"]["warnings"]
    assert run(env)["generator_matches_ref"] is None and run(env)["summary"]["warnings"] == []


def test_m5_registry_subprocess_gets_a_scrubbed_environment(env, monkeypatch):
    guard = INSPECTOR_SRC + "\nimport os\nif os.environ.get('DATABASE_URL') or os.environ.get('PGPASSWORD') or os.environ.get('GITHUB_TOKEN'):\n    raise RuntimeError('credential in environment')\n"
    e = remake(env, mutate=lambda f: f.__setitem__(INSPECTOR, guard))
    monkeypatch.setenv("DATABASE_URL", "postgres://x")
    monkeypatch.setenv("PGPASSWORD", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    sc._FACTS_CACHE.clear()
    card = run(e)
    assert card["registry"]["revision"] == 15, "the ref's inspector saw a credential-bearing environment"


def test_low_out_refuses_to_overwrite_a_foreign_file_and_writes_atomically(env, tmp_path, capsys):
    foreign = tmp_path / "precious.json"
    foreign.write_text('{"keep": "me"}')
    assert cli(env, out=foreign)[0] == 5
    assert foreign.read_text() == '{"keep": "me"}' and "refusing to overwrite" in capsys.readouterr().err
    notjson = tmp_path / "notes.txt"
    notjson.write_text("notes")
    assert cli(env, out=notjson)[0] == 5 and notjson.read_text() == "notes"
    rc, out = cli(env)
    assert rc == 0 and cli(env, out=out)[0] == 0          # an existing scorecard is replaceable
    assert not list(tmp_path.glob("*.tmp")) and not list(env["tmp"].glob("*.tmp"))


def test_low_ref_beginning_with_dashes_is_not_an_option(env, tmp_path):
    assert sc.main(["--repo", str(env["repo"]), "--ref=--all", "--out", str(tmp_path / "o.json")]) == 5
    with pytest.raises(sc.ScorecardError):
        sc.resolve_ref(env["repo"], "--help")


def test_low_unknown_register_state_word_is_unmeasured_not_a_guessed_fail(env):
    def mut(f):
        f[REGISTER] = register_text([(r, s, v, "WITHDRAWN — by ruling" if r == "R57" else st) for r, s, v, st in CLEAN_ROWS])
    c = cell(run(remake(env, mut)), "T3", "known_defect_rows")
    assert c["verdict"] == "UNMEASURED" and c["unknown_state"] == ["R57"] and "WITHDRAWN" in c["reason"]
    def both(f):
        f[REGISTER] = register_text([(r, s, v, "WITHDRAWN" if r == "R57" else "OPEN" if r == "R58" else st) for r, s, v, st in CLEAN_ROWS])
    assert cell(run(remake(env, both)), "T3", "known_defect_rows")["verdict"] == "FAIL"   # a real open row still decides


def test_low_manifest_tier_entries_match_by_path_only(env):
    good = hashlib.sha256(env["files"][T4D].encode()).hexdigest()
    def mut(f):
        f[MANIFEST] = manifest_text(f, [{"canonical_id": "ASSET_ELEVATION_TEMPLATE", "path": "somewhere/else.md", "fingerprint_sha256": "0" * 64}])
    assert t5(run(remake(env, mut)), "manifest_tier_entries")["verdict"] == "NO_DETECTOR"
    def byid(f):
        f[MANIFEST] = manifest_text(f, [{"canonical_id": "ASSET_ELEVATION_TEMPLATE", "fingerprint_sha256": good}])
    assert t5(run(remake(env, byid)), "manifest_tier_entries")["verdict"] == "NO_DETECTOR"


def test_low_vocabulary_extension_is_recorded_in_the_schema(env):
    v = run(env)["vocabulary"]
    assert v["verdicts"] == list(sc.VERDICTS) and "NO_DETECTOR" in v["extension"] and "UNMEASURED" in v["extension"]


# survivors named by the independent review

def test_survivor_test_prefixed_module_outside_a_tests_dir_is_not_a_writer(env):
    e = remake(env, mutate=lambda f: (f.__setitem__(WRITERS + "ga_x.py", "# nothing\n"),
                                      f.__setitem__(WRITERS + "test_ga_x.py", "@register('ga_x')\nclass T: pass\n")))
    assert cell(run(e), "T2", "build_registered_rederivation")["verdict"] == "FAIL"


def test_survivor_transfers_with_no_t2_row_is_no_detector_not_pass(env):
    def mut(f):
        f[T3D] += "4. **Presentation parity** holds for the layer's served surface.\n"
        f[T2D] = f[T2D].replace("| Presentation parity **[TRANSFERS]** | x |\n", "")
    c = t5(run(remake(env, mut)), "transfers_contradiction")
    assert c["verdict"] == "NO_DETECTOR"


def test_survivor_build_check_fail_outranks_no_detector(env):
    assets = copy.deepcopy(LAYER_ASSETS)
    assets["L3"][0]["measurements"]["Build.contract"]["v"] = "FAIL"
    assets["L4"][0]["measurements"]["Build.contract"]["v"] = "NO_DETECTOR"
    e = remake(env, census=False)
    e["cdir"] = write_census(env["tmp"] / "prec", env["fp"], tool=e["sha"], assets=assets)
    assert run(e)["engine_build_checks"]["Build.contract"] == "FAIL"


def test_survivor_tracker_gate_order_is_compared(env):
    def mut(f):
        f[TRACKER] = f[TRACKER].replace('("Ldgr","derivation ledger","always","x"),\n ("Idem","idempotency","always","x"),',
                                        '("Idem","idempotency","always","x"),\n ("Ldgr","derivation ledger","always","x"),')
    assert t5(run(remake(env, mut)), "gate_set_agreement")["verdict"] == "FAIL"


# the committed scorecard itself

def test_committed_scorecard_has_the_schema_and_is_reproduced_from_repository_contents():
    path = REPO / "00_ARCHITECTURE/control/NIKASHA_T1_T5_SCORECARD.json"
    if not path.exists():
        pytest.skip("no committed scorecard in this tree")
    doc = json.loads(path.read_text())
    assert doc["schema"] == "nikasha_scorecard/1" and doc["measured_offline"] is True
    assert set(doc["tests"]) == {"T1", "T2", "T3", "T4", "T5"} and "vocabulary" in doc
    assert doc["generator"] == "platform/scripts/governance/nikasha_scorecard.py" and len(doc["ref"]) == 40
    assert not any("file" in i for i in doc["inputs"]["census"]) and "/Users/" not in path.read_text()
    if _real_repo_is_shallow():
        pytest.skip(SHALLOW_SKIP)
    reachable = subprocess.run(["git", "-C", str(REPO), "cat-file", "-e", doc["ref"] + "^{commit}"], capture_output=True).returncode == 0
    if not reachable:
        pytest.skip("the scorecard's recorded ref is not an object in this checkout (a full clone that lacks it)")
    # --check uses the RECORDED ref and the censuses committed at that ref: repository contents alone
    assert sc.main(["--repo", str(REPO), "--out", str(path), "--check"]) == 0
