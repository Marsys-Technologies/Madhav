"""Driver pieces that need no database: the solver probe, the baseline oracle, the baseline writer, the evaluate command, the job-report normaliser, the
wall-clock column filter.  (The SQL and the stages are exercised by the real runs recorded in TRIAL_HARNESS_V2.md.)"""
import copy
import json
import sys
import types

import pytest

import fixtures as fx
import gates
import trial_slice as ts


# ── probe_solver: counts calls into a solver module, including through an imported alias ────────────────────────

def _fake_solver(monkeypatch):
    name = "services.gochara_kernel.window_solver"
    mod = types.ModuleType(name)

    def solve_window(x):
        return x + 1
    solve_window.__module__ = name
    mod.solve_window = solve_window
    holder = types.ModuleType("services.gochara_kernel.fake_holder")
    holder.solve_window = solve_window                               # the `from .window_solver import solve_window` binding
    monkeypatch.setitem(sys.modules, name, mod)
    monkeypatch.setitem(sys.modules, "services.gochara_kernel.fake_holder", holder)
    return mod, holder, solve_window


def test_probe_counts_calls_through_module_and_alias_and_restores(monkeypatch):
    mod, holder, original = _fake_solver(monkeypatch)
    calls = {}
    with ts.probe_solver(calls) as present:
        assert present is True
        assert holder.solve_window(1) == 2 and mod.solve_window(2) == 3
    assert calls == {"solve_window": 2}
    assert holder.solve_window is original and mod.solve_window is original            # restored
    holder.solve_window(5)
    assert calls == {"solve_window": 2}                                                 # not counted outside the probe


def test_probe_reports_present_and_counts_calls_at_a_head_that_carries_the_real_solver():
    """Claim (PLAN §2.7): at a solver-carrying head the probe reports the solver PRESENT and counts calls into the checkout's real `window_solver` (the
    peaks-need-a-search detector reads these counts).  Built from the checkout's own module, not a stand-in; restored afterwards."""
    from conftest import CHECKOUT
    if not (CHECKOUT / "platform" / "python-sidecar").is_dir():
        pytest.skip("no checkout export")
    assert (CHECKOUT / "platform" / "python-sidecar" / "services" / "gochara_kernel" / "window_solver.py").is_file(), "the checkout under test must carry the solver"
    from services.gochara_kernel import window_solver as ws
    original = ws.constant_step                                      # a public function DEFINED in the solver module
    calls = {}
    with ts.probe_solver(calls) as present:
        assert present is True
        ws.constant_step(1.0)
    assert calls == {"constant_step": 1}
    assert ws.constant_step is original                              # restored


def test_probe_reports_absent_and_counts_nothing_when_the_checkout_has_no_solver_module(monkeypatch, tmp_path):
    """Claim: where the checkout carries no `window_solver` (a head before it), the probe reports ABSENT and counts nothing.  The no-solver checkout is a package
    copy under tmp_path that holds no window_solver.py, resolved by the default module name."""
    pkg = tmp_path / "services" / "gochara_kernel"
    pkg.mkdir(parents=True)
    for name, path in (("services", tmp_path / "services"), ("services.gochara_kernel", pkg)):
        stub = types.ModuleType(name)
        stub.__path__ = [str(path)]
        monkeypatch.setitem(sys.modules, name, stub)
    monkeypatch.delitem(sys.modules, "services.gochara_kernel.window_solver", raising=False)
    assert not (pkg / "window_solver.py").exists()
    calls = {}
    with ts.probe_solver(calls) as present:
        assert present is False
    assert calls == {}


# ── the wall-clock column filter (G-7 compares window rows, not insertion stamps) ───────────────────────────────

@pytest.mark.parametrize("col,excluded", [("created_at", True), ("updated_at", True), ("verified_at", True), ("inserted_utc", True), ("peak_instant", False),
                                          ("interval", False), ("objective_value", False), ("window_id", False), ("qualification", False)])
def test_nondeterministic_column_filter(col, excluded):
    assert bool(ts.NONDETERMINISTIC_COLUMN.search(col)) is excluded


# ── the baseline oracle ─────────────────────────────────────────────────────────────────────────────────────────

def all_null_report():
    classes = {}
    for c in ts.CLASSES:
        n = ts.PRIOR_4CLASS_WINDOWS.get(c, 120)
        classes[c] = {"windows_total": n, "blank": n, "by_path": {"P1": {"windows": n}}}
    total = sum(v["windows_total"] for v in classes.values())
    return {"classes": classes,
            "totals": {"windows_total": total, "blank": total, "with_peak": 0, "with_score": 0, "with_evidence_for": 0, "with_severity": 0, "with_any_number": 0,
                       "valence": {"unqualified": total}, "blank_reasons": {"all_null_candidate_policy": total}},
            "policy_effect": {"manifest_policy": "all_null_candidate/1", "window_qualification_policies": {"all_null_candidate/1": total}},
            "build": {"defects": [], "aborted": None, "substeps_planned": 144, "substeps_done": 144, "observed": {"maximise_earliest_calls": 0}}}


STATE = {"classes": list(ts.CLASSES)}


def test_oracle_passes_on_a_clean_all_null_run():
    assert ts.baseline_oracle(all_null_report(), STATE)["passed"]


@pytest.mark.parametrize("mutate,needle", [
    (lambda r: r["totals"].update(blank=r["totals"]["blank"] - 1), "blank"),
    (lambda r: r["totals"].update(with_peak=1), "with_peak"),
    (lambda r: r["totals"]["valence"].update(favourable=1), "valence"),
    (lambda r: r["totals"]["blank_reasons"].update(value_mapping_undeclared=1), "blank reason"),
    (lambda r: r["policy_effect"].update(manifest_policy="window_qualification/1"), "manifest policy"),
    (lambda r: r["build"].update(substeps_done=143), "substeps"),
    (lambda r: r["build"]["observed"].update(maximise_earliest_calls=3), "maximise_earliest"),
    (lambda r: r["classes"]["bereavement"].update(windows_total=398), "bereavement"),
    (lambda r: r["classes"]["spiritual_turn"].update(windows_total=0), "spiritual_turn"),
    (lambda r: r["build"].update(defects=[{"step": "x"}]), "defect"),
])
def test_oracle_reads_false_for_each_broken_claim(mutate, needle):
    r = all_null_report()
    mutate(r)
    o = ts.baseline_oracle(r, STATE)
    assert not o["passed"] and any(needle in p for p in o["problems"]), o


# ── baseline writer refuses a run that cannot vouch for itself ──────────────────────────────────────────────────

def _write(tmp_path, name, obj):
    p = tmp_path / name
    p.write_text(json.dumps(obj))
    return str(p)


def full_report(passed=True):
    r = all_null_report()
    r.update({"oracle": {"passed": passed, "problems": [] if passed else ["x"]}, "config": {"classes": list(ts.CLASSES)}, "code": {"head": "a" * 40, "branch": "HEAD"},
              "paths": {"P1": {"windows": r["totals"]["windows_total"]}}, "runtime_s": {"by_step_kind": {"window": 1.0}, "build_substeps_sum": 1.0, "load_average_at_report": [1, 1, 1]},
              "window_rows_digest": {"sha256": "f" * 64}})
    for c in r["classes"].values():
        c.update({"valence": {"unqualified": c["windows_total"]}, "blank_reasons": {"all_null_candidate_policy": c["windows_total"]}})
    return r


def test_baseline_is_written_from_a_passed_12_class_run(tmp_path):
    rep = _write(tmp_path, "rep.json", full_report())
    out = tmp_path / "baseline_12.json"
    ns = ts.build_parser().parse_args(["baseline", "--report", rep, "--out", str(out)])
    assert ts.cmd_baseline(ns) == 0
    b = json.loads(out.read_text())
    assert b["schema"] == "ky.trial_baseline/2" and len(b["classes"]) == 12 and b["totals"]["prior_4class_windows"] == 1672
    assert b["classes"]["bereavement"]["group"] == "prior_4class" and b["classes"]["spiritual_turn"]["group"] == "new_8"


def test_baseline_refuses_when_the_oracle_did_not_pass(tmp_path):
    rep = _write(tmp_path, "rep.json", full_report(passed=False))
    ns = ts.build_parser().parse_args(["baseline", "--report", rep, "--out", str(tmp_path / "b.json")])
    with pytest.raises(SystemExit) as e:
        ts.cmd_baseline(ns)
    assert e.value.code == 2 and not (tmp_path / "b.json").exists()


def test_baseline_refuses_an_8_class_run(tmp_path):
    r = full_report()
    r["config"]["classes"] = r["config"]["classes"][:8]
    ns = ts.build_parser().parse_args(["baseline", "--report", _write(tmp_path, "rep.json", r), "--out", str(tmp_path / "b.json")])
    with pytest.raises(SystemExit):
        ts.cmd_baseline(ns)


# ── evaluate command, end to end on files ───────────────────────────────────────────────────────────────────────

def test_evaluate_command_writes_the_verdict_and_exits_nonzero_when_not_dispatchable(tmp_path, capsys):
    r, b, p = fx.a10_good()                  # the CLI applies the G-3 decision table on every run, so its world is the A10.1 one
    files = dict(report=_write(tmp_path, "r.json", r), baseline=_write(tmp_path, "b.json", b), profile=_write(tmp_path, "p.json", p),
                 second=_write(tmp_path, "s.json", fx.second()), mods=_write(tmp_path, "m.json", fx.dispatch_modules()),
                 digests=_write(tmp_path, "d.json", fx.dispatch_digests()))
    out = tmp_path / "v.json"
    ns = ts.build_parser().parse_args(["evaluate", "--report", files["report"], "--baseline", files["baseline"], "--profile", files["profile"],
                                       "--second-report", files["second"], "--dispatch-modules", files["mods"], "--dispatch-digests", files["digests"], "--out", str(out)])
    assert ts.cmd_evaluate(ns) == 3                                   # all gates pass, but the placeholder profile is not final -> not dispatchable
    v = json.loads(out.read_text())
    assert v["overall"] == "ALL_GATES_PASS_PROFILE_NOT_FINAL" and v["inputs"]["report_sha256"]
    assert "G-8 Head identity" in capsys.readouterr().out


# ── the real job's report → G-4 shape ───────────────────────────────────────────────────────────────────────────

JOB = {"classes": {"bereavement": {"status": "VERIFIED", "windows": [{"path_id": "P1", "status": "VERIFIED", "windows": 10}]},
                   "major_loss": {"status": "UNVERIFIED_DYNAMIC", "windows": [{"path_id": "P3", "status": "UNVERIFIED_DYNAMIC", "windows": 7}]}},
       "numerical_window_gate": {"status": "PASSED", "numbered_windows": 4, "judgment_flags": []}}


def test_job_report_normaliser_counts_unverified_windows_and_never_invents_a_recount():
    v = gates.verification_from_job_report(JOB)
    assert v["ran"] and v["unverified_windows"] == 7 and v["attestation_recount"] is None
    assert v["classes"]["major_loss"]["status"] == "UNVERIFIED_DYNAMIC"
    r, b, p = fx.good()
    r["verification"] = v
    out = gates.evaluate(r, b, p)
    assert out["gates"]["G-4"]["status"] == gates.FAIL                  # unverified windows and a non-VERIFIED class
    clean = copy.deepcopy(JOB)
    clean["classes"]["major_loss"] = {"status": "VERIFIED", "windows": [{"path_id": "P3", "status": "VERIFIED", "windows": 7}]}
    r["verification"] = gates.verification_from_job_report(clean)
    assert gates.evaluate(r, b, p)["gates"]["G-4"]["status"] == gates.NOT_EVALUATED     # no independent recount supplied


# ── the honest partial baseline (no 12-class run possible) ──────────────────────────────────────────────────────

def test_partial_baseline_has_the_4_prior_classes_and_nulls_for_the_8_and_g1_reads_it_as_not_evaluated(tmp_path):
    prior = tmp_path / "prior.json"
    prior.write_text((fx.HARNESS / "baseline_report_4class.json").read_text())
    out = tmp_path / "baseline_12.json"
    ns = ts.build_parser().parse_args(["baseline", "--from-prior-only", "--prior-4class", str(prior), "--out", str(out)])
    assert ts.cmd_baseline(ns) == 0
    b = json.loads(out.read_text())
    assert b["status"] == "PARTIAL_PRIOR_ONLY" and b["totals"]["prior_4class_windows"] == 1672 and b["totals"]["windows_total"] is None
    assert [c for c, v in b["classes"].items() if v["windows_total"] is None] == [c for c in ts.CLASSES if c in ts.NEW_8]
    r, _, p = fx.good()
    for c, n in ts.PRIOR_4CLASS_WINDOWS.items():
        r["classes"][c]["windows_total"] = n                                  # the 4 measured classes agree with the baseline ...
    assert gates.evaluate(r, b, p)["gates"]["G-1"]["status"] == gates.NOT_EVALUATED        # ... the 8 unmeasured ones make G-1 unevaluable, never a pass
    r["classes"]["bereavement"]["windows_total"] += 1
    assert gates.evaluate(r, b, p)["gates"]["G-1"]["status"] == gates.FAIL                  # a measured disagreement still FAILS


# ── G-8 digests on a real checkout export ───────────────────────────────────────────────────────────────────────

def test_module_digests_of_a_real_checkout_are_complete_deterministic_and_g8_reads_them():
    from conftest import CHECKOUT
    if not (CHECKOUT / "platform" / "python-sidecar").is_dir():
        pytest.skip("no checkout export")
    a, b = ts.module_digests(CHECKOUT), ts.module_digests(CHECKOUT)
    assert a == b and len(a) >= 60 and "MISSING" not in a.values()
    assert "pipeline.orchestrator.writers.ka_gochara_v5" in a and "services.gochara_kernel.window_sweep" in a
    r, _, _ = fx.good()
    r["code"]["implementation_modules"] = a
    assert gates.g8_head_identity(r, dict(a))["status"] == gates.PASS
    other = dict(a)
    other["services.gochara_kernel.window_sweep"] = "0" * 64
    assert gates.g8_head_identity(r, other)["status"] == gates.FAIL
