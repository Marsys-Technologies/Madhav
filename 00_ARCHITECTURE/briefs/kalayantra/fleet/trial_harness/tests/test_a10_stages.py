"""A10.1 stages (task T1B): TRIAL_READY/1 through the MERGED evaluator, EQUIVALENCE_RECORD/1 through the MERGED tool, the driver wiring that makes the G-3 table apply on
every run, the amd64 readiness record (T24 prep) and the natural-key SQL.  The two tools are run from `tests/vendor/` (copies of origin/main, see its README) or
from KY_TOOLS_DIR.  Every repository here is synthetic; no personal datum."""
import ast
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

import fixtures as fx
import gates
import trial_eval as te
import trial_slice as ts

HERE = Path(__file__).resolve().parent
TOOLS = Path(os.environ.get("KY_TOOLS_DIR") or HERE / "vendor")
TR_TOOL, EQ_TOOL = TOOLS / "trial_ready.py", TOOLS / "equivalence_record.py"
HEAD = "a" * 40


def clean_env():
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def git(repo, *args):
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "-C", str(repo), *args], capture_output=True, text=True,
                       env=clean_env(), timeout=60)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def put(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ── TRIAL_READY/1: the merged evaluator, run by the harness ────────────────────────────────────────────────────────────────────────────────────────

def ready_repo(tmp_path, skip=(), name="repo"):
    """A git repo whose registry binds each of T01..T25 to a `git_file` part reading one marker line; `skip` leaves a marker out (that check reads false)."""
    root = tmp_path / name
    root.mkdir()
    git(root, "init", "-q")
    put(root, "marker.txt", "".join(f"{i} ok\n" for i in gates.TRIAL_READY_IDS if i not in skip))
    reg = {"checks": [{"id": i, "claim": f"{i} claim", "parts": [{"kind": "git_file", "path": "marker.txt", "contains": [f"{i} ok"]}]} for i in gates.TRIAL_READY_IDS]}
    put(root, "platform/scripts/governance/trial_ready_checks.json", json.dumps(reg))
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "x")
    return root, git(root, "rev-parse", "HEAD")


@pytest.mark.skipif(not TR_TOOL.is_file(), reason="the merged trial_ready.py is not available")
def test_trial_ready_is_evaluated_by_the_merged_tool_and_enters_g0(tmp_path):
    """PLAN_A10_1 §2: TRIAL_READY/1 is evaluated by the merged evaluator over ONE commit; the report embeds it (G-0)."""
    repo, head = ready_repo(tmp_path)
    doc = te.run_trial_ready(repo, head, tmp_path / "out" / "trial_ready.json", python=sys.executable, tool=TR_TOOL, timeout_s=120)
    assert doc["predicate"] == "TRIAL_READY/1" and doc["head_sha"] == head and doc["ready"] is True and len(doc["checks"]) == 25
    r = fx.a10_report()
    r["code"]["head"], r["trial_ready"] = head, doc
    assert gates.g0_trial_ready(r)["status"] == gates.PASS


@pytest.mark.skipif(not TR_TOOL.is_file(), reason="the merged trial_ready.py is not available")
def test_one_false_check_makes_the_embedded_evaluation_not_ready_and_g0_fail(tmp_path):
    repo, head = ready_repo(tmp_path, skip=("T14",))
    doc = te.run_trial_ready(repo, head, tmp_path / "out" / "trial_ready.json", python=sys.executable, tool=TR_TOOL, timeout_s=120)
    assert doc["ready"] is False and [c["id"] for c in doc["checks"] if c["value"] is False] == ["T14"] and doc["evaluator_exit"] == 1
    r = fx.a10_report()
    r["code"]["head"], r["trial_ready"] = head, doc
    assert gates.g0_trial_ready(r)["status"] == gates.FAIL


def test_trial_ready_that_cannot_start_is_a_not_run_document_never_a_pass(tmp_path):
    for repo, head, tool in ((None, HEAD, None), (tmp_path, None, None), (tmp_path, HEAD, tmp_path / "missing.py")):
        doc = te.run_trial_ready(repo, head, tmp_path / "t.json", tool=tool)
        assert doc["ready"] is False and doc["checks"] == [] and doc["not_run_reason"]
        r = fx.a10_report()
        r["trial_ready"] = doc
        assert gates.g0_trial_ready(r)["status"] == gates.NOT_EVALUATED


def test_an_evaluator_that_refuses_is_a_not_run_document(tmp_path):
    tool = tmp_path / "fake_tr.py"
    tool.write_text("import sys\nprint('cannot resolve', file=sys.stderr)\nsys.exit(2)\n")
    doc = te.run_trial_ready(tmp_path, HEAD, tmp_path / "t.json", python=sys.executable, tool=tool)
    assert doc["ready"] is False and "refused (exit 2)" in doc["not_run_reason"]


def test_a_stale_ready_true_file_is_never_taken_when_the_evaluator_did_not_write_one(tmp_path):
    """The real evaluator unlinks --out first; the harness must not read a pre-existing file when the tool exits 2."""
    out = tmp_path / "t.json"
    out.write_text(json.dumps(fx.trial_ready()))
    tool = tmp_path / "fake_tr.py"
    tool.write_text("import sys\nsys.exit(2)\n")
    doc = te.run_trial_ready(tmp_path, HEAD, out, python=sys.executable, tool=tool)
    assert doc["ready"] is False and doc["not_run_reason"]


# ── EQUIVALENCE_RECORD/1: the merged tool, run by the harness ───────────────────────────────────────────────────────────────────────────────────────

SC = "platform/python-sidecar"
K = SC + "/services/gochara_kernel/"
LISTS = {"geometry": ["services.gochara_kernel.arcs", "services.gochara_kernel.ids", "services.gochara_kernel.convention", "services.gochara_kernel.record_store"],
         "evaluation": ["services.gochara_kernel.evaluator", "services.gochara_kernel.dasha_read", "services.gochara_kernel.chart_context",
                        "pipeline.orchestrator.writers.ka_gochara_v5", "services.gochara_rules.score"],
         "window": ["services.gochara_kernel.result_policy", "services.gochara_kernel.window_sweep", "services.gochara_kernel.window_solver",
                    "services.gochara_kernel.window_solver_check"]}


def h(x):
    return hashlib.sha256(x.encode()).hexdigest()


def make_world(root):
    """A miniature sidecar tree (adapted from the merged tool's own test world, #3855)."""
    for pkg in ("services", "services/gochara_kernel", "services/gochara_rules", "pipeline", "pipeline/orchestrator", "pipeline/orchestrator/writers"):
        put(root, f"{SC}/{pkg}/__init__.py", "")
    put(root, K + "input_vector.py",
        '_K, _R = "services.gochara_kernel.", "services.gochara_rules."\nIMPLEMENTATION_MODULES = {\n'
        '    "geometry": tuple(_K + m for m in ("arcs", "ids", "convention", "record_store")),\n'
        '    "evaluation": tuple(_K + m for m in ("evaluator", "dasha_read", "chart_context")) + ("pipeline.orchestrator.writers.ka_gochara_v5",) + tuple(_R + m for m in ("score",)),\n'
        '    "window": tuple(_K + m for m in ("result_policy", "window_sweep", "window_solver", "window_solver_check")),\n}\n')
    put(root, K + "arcs.py", "ARC = 1\n")
    put(root, K + "ids.py", "ID = 1\n")
    put(root, K + "convention.py", 'ORB_TABLE = {"conjunction": {"orb": 8.0}, "aspect": {"orb": 6.0}}\n')
    put(root, K + "record_store.py", 'POINT_ORB_SOURCE = {"conjunction": "orb_conj_slow"}\nKALA_CONVENTION_VECTOR = {"zodiac": "sidereal", "node_model": "mean", "epoch_convention": "noon_ut_knot_abscissa"}\n')
    put(root, K + "evaluator.py", "from . import ids\nEVAL = 1\n")
    put(root, K + "dasha_read.py", "DASHA = 1\n")
    put(root, K + "dasha_settlement.json", '{"settled": []}\n')
    put(root, K + "chart_context.py", "CTX = 1\n")
    put(root, K + "result_policy.py", 'POLICY_QUALIFICATION = "window_qualification/1"\nRESULT_POLICIES = ("all_null_candidate/1", POLICY_QUALIFICATION)\n'
                                      'QUALIFICATION_TABLE = {"policy": POLICY_QUALIFICATION, "rules": [{"n": 1, "then": "unqualified"}]}\n')
    put(root, K + "window_sweep.py", "from . import arcs\nBISECT_SECONDS = 1.0\nMIN_EXCURSION_SECONDS = 60\n")
    put(root, K + "window_solver.py", "MAX_EVALS = 40_000\n")
    put(root, K + "window_solver_check.py", "TIE = 1e-9\nGREY = 2e-10\nLEAF_S = 0.5\nF4_ABS_SLACK = 1e-7\nISOLATION_S = 30\n")
    put(root, SC + "/services/gochara_rules/score.py", "SCORE = 1\n")
    put(root, SC + "/pipeline/orchestrator/writers/ka_gochara_v5.py", "from services.gochara_kernel import arcs, evaluator, window_sweep\nfrom services.gochara_rules import score\n")
    put(root, SC + "/requirements.txt", "pyswisseph==2.10.3.2\n")
    put(root, "platform/migrations/1240_gate.sql", "CREATE OR REPLACE FUNCTION public.ka_gochara_window_qualification_ok(q jsonb)\nRETURNS boolean LANGUAGE sql AS $$\n"
                                                    "  SELECT q IS NULL OR jsonb_typeof(q) = 'object';\n$$;\n")


def stage_digests(root):
    out = {}
    for stage, names in LISTS.items():
        d = {}
        for m in names:
            p = Path(root) / SC / (m.replace(".", "/") + ".py")
            src = p.read_text(encoding="utf-8")
            if m == "services.gochara_kernel.dasha_read":
                src += "\0" + p.with_name("dasha_settlement.json").read_text(encoding="utf-8")
            d[m] = hashlib.sha256(src.encode()).hexdigest()
        out[stage] = hashlib.sha256(json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    return out


CLASSES = [f"class_{i:02d}" for i in range(26)]
E3A = {"l0_rows": {"bg_transit_rules": {"rahu_taurus": {"rung": "EX"}, "rahu_gemini": {"rung": "MT"}}},
       "l1_facts": {"fact_1": {"content": {"sign": "A"}, "provenance": "ga_x"}},
       "dasha": {"population": {"d1": {"lord": "Ju", "end": "2030-01-01"}}, "held_state": {"held": "d1"}}, "av_declarations": {"av_1": {"declared": True}}}


def vector(root):
    return {"schema": "ka_gochara_input_vector/3", "stored_scope": "trial_slice", "result_policy": "window_qualification/1",
            "sky_convention": {"id": "sky/1", "content_digest": h("sky")}, "registry": {"digest": h("registry"), "census": [["P1", "1.3.0"]]},
            "node": {"model": "mean", "source": "swiss", "zodiac": "sidereal", "ayanamsha": "lahiri"},
            "ephemeris": {"backend": "swieph", "swe_version": "2.10.03", "library_sha256": h("lib"), "platform": "Linux-x86_64",
                          "files": {"sepl_18.se1": h("f1")}, "probe_digest": h("probe")},
            "l0": {"bg_transit_rules": h("l0")}, "orb_policy": {"admission_digest": h("adm"), "activity": {"1.3.0": {"orb_deg": "1.0"}}},
            "rulings_digest": h("rulings"), "implementation": stage_digests(root), "scored_classes": CLASSES[:12], "test_slice": {"classes": 12},
            "horizon_basis": {"kind": "configured"}, "near_miss_layer_version": 1, "qualification_table": h("qt")}


def century_extra():
    pop = {"l0:bg_transit_rules:rahu_taurus": {"rung": "EX"}, "l0:bg_transit_rules:rahu_gemini": {"rung": "MT"}, "l1:fact_1": {"content": {"sign": "A"}, "provenance": "ga_x"},
           "dasha:population:d1": {"lord": "Ju", "end": "2030-01-01"}, "dasha:held_state": {"held": "d1"}, "av:av_1": {"declared": True}, "l1:fact_extra": {"content": {"sign": "C"}}}
    return {"rules": {"selection": {"selected_rule_version": "1.3.0", "profile": "final"}, "declared_accuracy": {"peak_instant_seconds": "1", "q13": "declared"}},
            "inputs": {"e3a": E3A, "e3b_population": pop},
            "century_config": {"stored_scope": "stored_non_moon", "horizon": {"start": "1998-01-01T00:00:00+00:00", "end": "2050-01-01T00:00:00+00:00"},
                               "horizon_basis": "configured", "final_rules": "true", "result_policy": "window_qualification/1", "in_build_verify": "deferred",
                               "budgets": {"per_window": "40000", "verifier": "600"}, "classes": CLASSES,
                               "verification_plan": {"mode": "one_execution", "shard_plan_digest": None, "g6_sampling_rule": "3pct+top5", "seed_rule": "generation_id"}},
            "runtime": {"kind": "qualifying_run", "arch": "linux/amd64", "python": "3.13.7", "dependency_lock_digest": h("lock")}}


@pytest.fixture
def eq_world(tmp_path):
    root = tmp_path / "eqrepo"
    root.mkdir()
    git(root, "init", "-q")
    make_world(root)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "world")
    return root, git(root, "rev-parse", "HEAD")


def emit(tmp_path, root, head, vec=None, extra=None):
    pinned = te.pinned_inputs(vec if vec is not None else vector(root), trial_horizon=["2020-01-01", "2021-01-01"],
                              provenance={"branch": "kalayantra/od1-integration", "image_digest": ""}, extra=extra)
    return te.emit_equivalence_record(root, head, pinned, tmp_path / "eq", python=sys.executable, tool=EQ_TOOL, timeout_s=120)


@pytest.mark.skipif(not EQ_TOOL.is_file(), reason="the merged equivalence_record.py is not available")
def test_the_trial_head_record_is_emitted_by_the_merged_tool_incomplete_when_only_the_trial_can_speak(tmp_path, eq_world):
    """PLAN_A10_1 §3 / N.7.6: from what the trial can read (the stored vector, its own horizon, a ROLLING arm64/darwin runtime) the tool writes E1 and nothing it must
    not guess: E2/E3/E4/E5 are NULL with their reasons, the record is INCOMPLETE and its E6 names the head."""
    root, head = eq_world
    out = emit(tmp_path, root, head)
    assert out["status"] == "INCOMPLETE" and out["exit"] == 2 and out["complete"] is False and out["record_digest"] is None
    assert set(out["unreadable"]) == {"E2", "E3", "E4", "E5"}
    rec = json.loads(Path(out["record_file"]).read_text())
    assert rec["categories"]["E1"]["digest"] and rec["E6"]["commit"] == head and rec["runtime_kind"] == "rolling_diagnostic"


@pytest.mark.skipif(not EQ_TOOL.is_file(), reason="the merged equivalence_record.py is not available")
def test_the_record_is_complete_when_the_operator_supplies_what_only_the_dispatch_config_can_say(tmp_path, eq_world):
    root, head = eq_world
    out = emit(tmp_path, root, head, extra=century_extra())
    assert out["status"] == "COMPLETE" and out["exit"] == 0 and out["complete"] is True and len(out["record_digest"]) == 64 and not any(out["unreadable"].values())


@pytest.mark.skipif(not EQ_TOOL.is_file(), reason="the merged equivalence_record.py is not available")
def test_a_vector_that_is_not_the_commits_is_refused_not_recorded(tmp_path, eq_world):
    """EQ-10: the pinned vector's implementation digests must be the ones recomputed from the commit's bytes."""
    root, head = eq_world
    vec = vector(root)
    vec["implementation"]["window"] = h("some other commit")
    out = emit(tmp_path, root, head, vec=vec, extra=century_extra())
    assert out["status"] == "REFUSED" and out["exit"] == 1 and "record_file" not in out


@pytest.mark.skipif(not EQ_TOOL.is_file(), reason="the merged equivalence_record.py is not available")
def test_the_record_follows_the_head_the_harness_names(tmp_path, eq_world):
    """The same inputs on a head whose solver checker differs by one byte give a different E1 (the tool's EQ-1 reached through the harness call)."""
    root, head = eq_world
    a = emit(tmp_path, root, head, extra=century_extra())
    put(root, K + "window_solver_check.py", "TIE = 1e-8\nGREY = 2e-10\nLEAF_S = 0.5\nF4_ABS_SLACK = 1e-7\nISOLATION_S = 30\n")
    git(root, "commit", "-aq", "-m", "tie")
    head2 = git(root, "rev-parse", "HEAD")
    (tmp_path / "eq2").mkdir()
    pinned = te.pinned_inputs(vector(root), trial_horizon=None, provenance={"branch": "b", "image_digest": ""}, extra=century_extra())
    b = te.emit_equivalence_record(root, head2, pinned, tmp_path / "eq2", python=sys.executable, tool=EQ_TOOL, timeout_s=120)
    ra, rb = (json.loads(Path(x["record_file"]).read_text()) for x in (a, b))
    assert ra["categories"]["E1"]["digest"] != rb["categories"]["E1"]["digest"] and rb["E6"]["commit"] == head2


def test_the_emission_that_cannot_start_is_not_run_never_complete(tmp_path):
    pinned = {"schema": te.PINNED_SCHEMA}
    for repo, head, pin, tool in ((None, HEAD, pinned, None), (tmp_path, None, pinned, None), (tmp_path, HEAD, None, None), (tmp_path, HEAD, pinned, tmp_path / "missing.py")):
        out = te.emit_equivalence_record(repo, head, pin, tmp_path / "eq", tool=tool)
        assert out["status"] == "NOT_RUN" and out["reason"]


@pytest.mark.parametrize("code,status", [(0, "COMPLETE"), (2, "INCOMPLETE"), (1, "REFUSED")])
def test_the_tools_exit_codes_map_to_the_three_statuses(tmp_path, code, status):
    """equivalence_record.py: 0 complete, 2 written but INCOMPLETE, 1 refused (nothing written)."""
    tool = tmp_path / "fake_eq.py"
    tool.write_text("import json, sys\nout = sys.argv[sys.argv.index('--out') + 1]\ncode = %d\n"
                    "if code != 1:\n    open(out, 'w').write('{}')\n"
                    "print(json.dumps({'out': out, 'complete': code == 0, 'record_digest': 'd' * 64 if code == 0 else None, 'unreadable': {}}))\n"
                    "print('REFUSED: x', file=sys.stderr) if code == 1 else None\nsys.exit(code)\n" % code)
    out = te.emit_equivalence_record(tmp_path, HEAD, {"schema": te.PINNED_SCHEMA}, tmp_path / "eq", python=sys.executable, tool=tool)
    assert out["status"] == status and out["exit"] == code


def test_the_pinned_inputs_merge_keeps_the_stored_vector_and_lets_extra_replace_only_what_it_names():
    vec = {"schema": "ka_gochara_input_vector/3"}
    p = te.pinned_inputs(vec, trial_horizon=["a", "b"], provenance={"branch": "b"}, extra={"input_vector": {"evil": 1}, "runtime": {"kind": "qualifying_run", "arch": "linux/amd64"},
                                                                                     "rules": {"selection": {}}})
    assert p["input_vector"] is vec and p["runtime"]["kind"] == "qualifying_run" and p["runtime"]["arch"] == "linux/amd64" and "python" in p["runtime"]
    assert p["rules"] == {"selection": {}} and p["trial_scope"] == {"horizon": ["a", "b"]}


# ── amd64 readiness (T24 prep; SR-AMD64-PER-HEAD) ────────────────────────────────────────────────────────────────────────────────────────────

IMG = "sha256:" + "c" * 64


def test_amd64_slice_is_ready_only_with_a_head_and_an_immutable_image_digest():
    """T24 detector: 'the amd64 slice cannot start' reads false when an input is missing.  The record is NOT a run."""
    ok = te.amd64_readiness(HEAD, IMG)
    assert ok["ready"] is True and ok["not_run"] is True
    for head, img in ((None, IMG), (HEAD, None), (HEAD, "latest"), ("abc", IMG), (HEAD, "sha256:short")):
        assert te.amd64_readiness(head, img)["ready"] is False, (head, img)


def test_the_amd64_command_binds_the_head_the_four_class_slice_and_the_harness_launcher():
    cmd = te.amd64_readiness(HEAD, IMG)["in_image_command"]
    assert f"TRIAL_CODE_HEAD={HEAD}" in cmd and "TRIAL_CLASSES=bereavement,chronic_onset,illness_acute,major_loss" in cmd and "TRIAL_VERIFY=1" in cmd
    assert cmd[-3].endswith("run_trial.sh") and cmd[-4] == "bash"
    argv = te.amd64_readiness(HEAD, IMG)["example_runner"]["argv"]
    assert "--platform" in argv and argv[argv.index("--platform") + 1] == "linux/amd64" and IMG in argv


def test_the_amd64_command_is_accepted_by_the_launcher_and_the_driver_parser():
    """The in-image environment is made only of options run_trial.sh knows; the launcher's dry run builds a command the driver's parser accepts."""
    env = dict(a.split("=", 1) for a in te.amd64_readiness(HEAD, IMG)["in_image_command"] if "=" in a and not a.startswith("/"))
    r = subprocess.run(["bash", str(fx.HARNESS / "run_trial.sh"), "/x/code", "/x/out"], capture_output=True, text=True, timeout=30,
                       env={**os.environ, **env, "TRIAL_DRY_RUN": "1"})
    assert r.returncode == 0, r.stderr
    argv = r.stdout.splitlines()
    ns = ts.build_parser().parse_args(argv[argv.index("run"):])
    assert ns.code_head == HEAD and ns.classes == env["TRIAL_CLASSES"] and ns.verify and ns.label == "amd64_slice"


def test_amd64_readiness_command_exit_codes(tmp_path, capsys):
    out = tmp_path / "r.json"
    assert ts.main(["amd64-readiness", "--head", HEAD, "--image-digest", IMG, "--out", str(out)]) == 0 and json.loads(out.read_text())["ready"] is True
    assert ts.main(["amd64-readiness", "--head", HEAD]) == 3


# ── the driver: the G-3 table applies on EVERY run; the baseline carries the snapshot; the report is relabelled when TRIAL_READY arrives ─────────────────

def test_every_gate_evaluation_in_the_driver_passes_the_decision_table():
    """'Checked on every run': no call of gates.evaluate inside trial_slice.py may omit decision_table (a call without one is the pre-A10.1 evaluator)."""
    tree = ast.parse(Path(ts.__file__).read_text())
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "evaluate"
             and isinstance(n.func.value, ast.Name) and n.func.value.id == "gates"]
    assert len(calls) >= 2 and all("decision_table" in [k.arg for k in c.keywords] for c in calls)


def test_an_unusable_decision_table_refuses_a_run_before_any_work(tmp_path, capsys):
    bad = tmp_path / "t.json"
    raw = json.loads(fx.TABLE_PATH.read_text())
    raw["allowed_reasons"].append(raw["forbidden_reasons"][0])
    bad.write_text(json.dumps(raw))
    with pytest.raises(SystemExit) as e:
        ts.main(["run", "--checkout", str(tmp_path), "--result-policy", "window_qualification/1", "--out", str(tmp_path / "o"), "--decision-table", str(bad)])
    assert e.value.code == 2 and "G-3 decision table" in capsys.readouterr().err        # refused FOR the table, not for some later reason
    assert not (tmp_path / "o" / "state.json").exists()
    with pytest.raises(SystemExit):
        ts.load_decision_table(str(tmp_path / "missing.json"))


def test_check_table_prints_the_digest_of_the_shipped_table(capsys):
    assert ts.main(["check-table"]) == 0
    assert fx.decision_table()["sha256"] in capsys.readouterr().out


def test_evaluate_command_applies_the_table_to_a_planted_forbidden_reason(tmp_path):
    """T14 end to end on files: the CLI verdict reads NO_DISPATCH for a planted forbidden reason, exit 3."""
    r, b, p = fx.a10_good()
    r["reason_windows_any"]["orb_not_ratified"] = 1
    def w(name, obj):
        (tmp_path / name).write_text(json.dumps(obj))
        return str(tmp_path / name)
    out = tmp_path / "v.json"
    rc = ts.main(["evaluate", "--report", w("r.json", r), "--baseline", w("b.json", b), "--profile", w("p.json", fx.profile(final=True)), "--second-report", w("s.json", fx.second()),
                  "--dispatch-modules", w("m.json", fx.dispatch_modules()), "--dispatch-digests", w("d.json", fx.dispatch_digests()), "--out", str(out)])
    v = json.loads(out.read_text())
    assert rc == 3 and v["overall"] == "NO_DISPATCH" and "G-3" in v["failed"] and v["inputs"]["decision_table_sha256"] == fx.decision_table()["sha256"]


def test_the_baseline_command_carries_the_noninterference_snapshot(tmp_path):
    import test_driver
    rep = test_driver.full_report()
    rep["noninterference"] = fx.snapshot()
    rp = tmp_path / "rep.json"
    rp.write_text(json.dumps(rep))
    out = tmp_path / "b.json"
    assert ts.main(["baseline", "--report", str(rp), "--out", str(out)]) == 0
    assert json.loads(out.read_text())["noninterference"] == fx.snapshot()


def _run_dir(tmp_path):
    out = tmp_path / "run"
    out.mkdir()
    rep = fx.a10_report()
    rep["trial_ready"] = None
    state = {"label": "trial", "code": {"head": "a" * 40, "branch": "b"}, "image_digest": None}
    (out / "state.json").write_text(json.dumps(state))
    for name in ("trial_report.json", "report.json"):
        (out / name).write_text(json.dumps(rep))
    return out


@pytest.mark.skipif(not TR_TOOL.is_file(), reason="the merged trial_ready.py is not available")
def test_trial_ready_command_attaches_the_evaluation_and_flips_the_label(tmp_path):
    repo, head = ready_repo(tmp_path)
    out = _run_dir(tmp_path)
    st = json.loads((out / "state.json").read_text())
    st["code"]["head"] = head
    (out / "state.json").write_text(json.dumps(st))
    for name in ("trial_report.json", "report.json"):
        rep = json.loads((out / name).read_text())
        rep["code"]["head"] = head
        (out / name).write_text(json.dumps(rep))
    assert json.loads((out / "report.json").read_text()).get("qualification") is None
    # the command resolves the evaluator inside --repo: place the tool there as the repository would carry it
    shutil.copy(TR_TOOL, repo / "platform/scripts/governance/trial_ready.py")
    shutil.copy(TOOLS / "git_env_scrub.py", repo / "platform/scripts/governance/git_env_scrub.py")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "tool")
    head2 = git(repo, "rev-parse", "HEAD")
    for name in ("state.json", "trial_report.json", "report.json"):                       # the trial's head is the repo's current head
        p = out / name
        txt = p.read_text().replace(head, head2)
        p.write_text(txt)
    assert ts.main(["trial-ready", "--out", str(out), "--repo", str(repo)]) == 0
    rep = json.loads((out / "report.json").read_text())
    assert rep["trial_ready"]["ready"] is True and rep["qualification"]["qualifying"] is True and rep["qualification"]["head"] == head2


def test_trial_ready_command_refuses_a_ref_that_is_not_the_trials_head(tmp_path):
    out = _run_dir(tmp_path)
    with pytest.raises(SystemExit) as e:
        ts.main(["trial-ready", "--out", str(out), "--repo", str(tmp_path), "--ref", "b" * 40])
    assert e.value.code == 2


def test_a_run_without_trial_ready_is_labelled_diagnostic_in_its_report(tmp_path):
    out = _run_dir(tmp_path)
    ts.attach_to_report(out, "equivalence_record", {"status": "NOT_RUN", "reason": "x"})
    rep = json.loads((out / "report.json").read_text())
    assert rep["qualification"]["label"] == "DIAGNOSTIC" and rep["qualification"]["qualifying"] is False and rep["equivalence_record"]["status"] == "NOT_RUN"


def test_the_launcher_passes_every_a10_option_and_the_parser_accepts_them():
    env = {"TRIAL_DECISION_TABLE": "/t.json", "TRIAL_DISPATCH_DIGESTS": "/d.json", "TRIAL_READY_REPO": "/r", "TRIAL_READY_JSON": "/tr.json", "TRIAL_READY_TIMEOUT_S": "99",
           "TRIAL_EQ_REPO": "/e", "TRIAL_EQ_TOOL": "/e.py", "TRIAL_EQ_PINNED_EXTRA": "/x.json", "TRIAL_IMAGE_DIGEST": IMG}
    r = subprocess.run(["bash", str(fx.HARNESS / "run_trial.sh"), "/x/code", "/x/out"], capture_output=True, text=True, timeout=30, env={**os.environ, **env, "TRIAL_DRY_RUN": "1"})
    assert r.returncode == 0, r.stderr
    argv = r.stdout.splitlines()
    ns = ts.build_parser().parse_args(argv[argv.index("run"):])
    assert (ns.decision_table, ns.dispatch_digests, ns.trial_ready_repo, ns.trial_ready_json, ns.trial_ready_timeout_s) == ("/t.json", "/d.json", "/r", "/tr.json", 99)
    assert (ns.eq_repo, ns.eq_tool, ns.eq_pinned_extra, ns.image_digest) == ("/e", "/e.py", "/x.json", IMG)


# ── the natural-key SQL, on a disposable database of the local lane cluster (skipped when the cluster is not there) ─────────────────────────────────

DDL = """
CREATE TABLE public.ka_gochara_eval_window (window_id uuid PRIMARY KEY, chart_id uuid, generation text, event_class text, path_id text, rule_version text, interval tstzrange);
CREATE TABLE public.ka_gochara_relationship_record (record_id uuid PRIMARY KEY, chart_id uuid, generation text, contact_id uuid, event_class text, affected_person text,
  frame_kind text, frame_arg text, agent text, relation text, object_id uuid, object_role text, path_id text, rule_version text, temporal_support_intervals tstzrange[],
  source_text text, operator_role text, admission_state text);
CREATE TABLE public.ka_gochara_eval_window_record (window_id uuid, record_id uuid, chart_id uuid, generation text, event_class text, path_id text, rule_version text);
CREATE TABLE public.ka_gochara_contact (chart_id uuid, generation text, contact_id uuid, t_in timestamptz, t_out timestamptz, t_exact timestamptz, delta_lambda real);
"""
ADMIN = "postgresql://postgres@127.0.0.1:55433/postgres"
CHART_A, CHART_B = str(uuid.UUID(int=1)), str(uuid.UUID(int=2))
OBJ, CONTACT = str(uuid.UUID(int=77)), str(uuid.UUID(int=88))


@pytest.fixture(scope="module")
def lane_db():
    psycopg = pytest.importorskip("psycopg")
    try:
        admin = psycopg.connect(ADMIN, autocommit=True, connect_timeout=3)
    except Exception:                                                                    # noqa: BLE001
        pytest.skip("the local lane cluster 127.0.0.1:55433 is not reachable")
    name = "ky_t1b_" + uuid.uuid4().hex[:8]
    admin.execute(f'CREATE DATABASE "{name}"')
    admin.execute(f"COMMENT ON DATABASE \"{name}\" IS 'ky.job=t1b-evaluator-tests'")
    try:
        with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{name}", autocommit=True) as c:
            c.execute(DDL)
        yield name
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')                  # only the database this fixture created
        admin.close()


def populate(conn, chart, generation, *, end="1998-02-01T00:00:00+00:00", rule_version="1.2.0", contact_t_in="1998-01-01T00:00:00+00:00", pair=True):
    wid, rid = str(uuid.uuid4()), str(uuid.uuid4())
    conn.execute("INSERT INTO ka_gochara_eval_window VALUES (%s,%s,%s,'bereavement','P1',%s, tstzrange('1998-01-01T00:00:00+00:00'::timestamptz, %s::timestamptz))",
                 (wid, chart, generation, rule_version, end))
    conn.execute("INSERT INTO ka_gochara_relationship_record VALUES (%s,%s,%s,%s,'bereavement','native','house','4','Sun','conj',%s,'karaka','P1',%s,"
                 " ARRAY[tstzrange('1998-01-01T00:00:00+00:00'::timestamptz, '1998-01-10T00:00:00+00:00'::timestamptz)],'src','scored','admitted')",
                 (rid, chart, generation, CONTACT, OBJ, rule_version))
    if pair:
        conn.execute("INSERT INTO ka_gochara_eval_window_record VALUES (%s,%s,%s,%s,'bereavement','P1',%s)", (wid, rid, chart, generation, rule_version))
    conn.execute("INSERT INTO ka_gochara_contact VALUES (%s,%s,%s,%s,NULL,NULL,0.5)", (chart, generation, CONTACT, contact_t_in))


def snap(db, chart, generation, tz=None):
    import psycopg
    with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{db}", autocommit=True) as c:
        if tz:
            c.execute(f"SET TIME ZONE '{tz}'")
        return te.capture_noninterference(c, chart, generation, ["bereavement"], "g" * 64)


def fresh(db):
    import psycopg
    c = psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{db}", autocommit=True)
    for t in ("ka_gochara_eval_window_record", "ka_gochara_contact", "ka_gochara_relationship_record", "ka_gochara_eval_window"):
        c.execute(f"TRUNCATE public.{t}")
    return c


def test_sql_two_stored_builds_differing_only_in_chart_and_generation_have_equal_keys(lane_db):
    """MEASURING_BUILD_CONTRACT T3.1 / MB-3.2: the key is the natural-key columns minus chart_id/generation; surrogate ids (window_id, record_id) are not in it."""
    c = fresh(lane_db)
    populate(c, CHART_A, "5.0")
    populate(c, CHART_B, "5.1")
    a, b = snap(lane_db, CHART_A, "5.0"), snap(lane_db, CHART_B, "5.1")
    assert a["kinds"] == b["kinds"] and all(a["kinds"][k]["count"] == 1 for k in gates.NONINTERFERENCE_KINDS)


def test_sql_a_moved_window_end_changes_windows_and_membership_but_not_contacts(lane_db):
    c = fresh(lane_db)
    populate(c, CHART_A, "5.0")
    populate(c, CHART_B, "5.1", end="1998-02-02T00:00:00+00:00")
    a, b = snap(lane_db, CHART_A, "5.0"), snap(lane_db, CHART_B, "5.1")
    differ = [k for k in gates.NONINTERFERENCE_KINDS if a["kinds"][k]["sha256"] != b["kinds"][k]["sha256"]]
    assert differ == ["windows", "membership"]


def test_sql_a_moved_contact_instant_is_seen_and_the_rule_version_is_not_in_any_key(lane_db):
    c = fresh(lane_db)
    populate(c, CHART_A, "5.0")
    populate(c, CHART_B, "5.1", rule_version="1.3.0", contact_t_in="1998-01-01T00:00:01+00:00")
    a, b = snap(lane_db, CHART_A, "5.0"), snap(lane_db, CHART_B, "5.1")
    assert [k for k in gates.NONINTERFERENCE_KINDS if a["kinds"][k]["sha256"] != b["kinds"][k]["sha256"]] == ["contacts"]
    assert a["rule_versions"] == {"P1": ["1.2.0"]} and b["rule_versions"] == {"P1": ["1.3.0"]}


def test_sql_the_session_time_zone_does_not_change_a_key(lane_db):
    c = fresh(lane_db)
    populate(c, CHART_A, "5.0")
    assert snap(lane_db, CHART_A, "5.0", tz="Asia/Kolkata") == snap(lane_db, CHART_A, "5.0", tz="UTC")


def test_sql_membership_is_read_through_the_join_not_inferred_from_the_two_sets(lane_db):
    """A window and a record that exist but are NOT paired have no membership key (two equal sets can hide a changed pairing)."""
    c = fresh(lane_db)
    populate(c, CHART_A, "5.0", pair=False)
    s = snap(lane_db, CHART_A, "5.0")
    assert s["kinds"]["membership"]["count"] == 0 and s["kinds"]["windows"]["count"] == 1 and s["kinds"]["supports"]["count"] == 1


def test_sql_membership_counts_the_pairs_not_the_cross_product_of_a_class_and_path(lane_db):
    """Two windows and two records of one class and path, each pair stored once: membership has 2 keys (a join on class/path alone would give 4)."""
    c = fresh(lane_db)
    populate(c, CHART_A, "5.0")
    populate(c, CHART_A, "5.0", end="1998-03-01T00:00:00+00:00")
    s = snap(lane_db, CHART_A, "5.0")
    assert s["kinds"]["membership"]["count"] == 2 and s["kinds"]["windows"]["count"] == 2


def test_capture_a10_reads_the_stored_vector_and_the_four_key_sets_into_the_state(lane_db, tmp_path):
    """The driver's capture step: the manifest vector (through the checkout's own `result_policy.manifest_vector`) → digests record + input_vector.json; the DB →
    the snapshot, bound to the geometry configuration of that vector."""
    import types
    import psycopg
    c = fresh(lane_db)
    populate(c, ts.CHART, ts.GENERATION)
    make_world(tmp_path / "w")
    vec = vector(tmp_path / "w")
    fake = types.SimpleNamespace(manifest_vector=lambda conn, chart, generation: vec)
    state = {"classes": ["bereavement"], "horizon": {"start": "1998-01-01", "end": "2084-02-05"}}
    (tmp_path / "o").mkdir()
    with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{lane_db}", autocommit=True) as conn:
        ts.capture_a10(state, tmp_path / "o", conn, {"result_policy": fake})
    assert set(state["digests_record"]["components"]) == set(gates.DIGEST_COMPONENTS) and json.loads((tmp_path / "o" / "input_vector.json").read_text()) == vec
    snap_ = state["noninterference"]
    assert snap_["geometry_config"] and snap_["kinds"]["windows"]["count"] == 1 and snap_["rule_versions"] == {"P1": ["1.2.0"]} and "a10_errors" not in state


def test_capture_a10_records_an_unreadable_vector_as_null_not_as_equal(lane_db, tmp_path):
    import types
    import psycopg
    fresh(lane_db)

    def boom(conn, chart, generation):
        raise RuntimeError("no manifest")
    state = {"classes": ["bereavement"], "horizon": {"start": "a", "end": "b"}}
    (tmp_path / "o").mkdir()
    with psycopg.connect(f"postgresql://postgres@127.0.0.1:55433/{lane_db}", autocommit=True) as conn:
        ts.capture_a10(state, tmp_path / "o", conn, {"result_policy": types.SimpleNamespace(manifest_vector=boom)})
    assert state["digests_record"] is None and state["noninterference"]["geometry_config"] is None and state["a10_errors"]["manifest_vector"] == "RuntimeError"
