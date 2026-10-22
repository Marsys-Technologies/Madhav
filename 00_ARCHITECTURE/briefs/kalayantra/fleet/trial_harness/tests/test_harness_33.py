"""HARNESS-3.3 (item harness-33; PRETR-early O-1 / O-2): two correctness changes in the trial harness's build loop, one oracle per distinct claim, each failing on its
single planted reversion (`mutants_h33.py`, ids H33-*).  The build loop is run for real (`trial_slice.build`); only the sidecar (writer, `build_slice`, psycopg) is a
stand-in, and the stand-in `build_slice` is the real one's loop (j4d_slice_qualify.build_slice: one transaction per step, a raise is a `substep_raised` defect that stops
that call).

H33-1  (O-1) a window substep that RAISES is booked under stage kind `window` (wall, state, report), status `failed` — never under `empty`.
H33-2  (O-2) COLLECT: a class with defects on two different paths reports BOTH, every remaining grain of the class still runs, and the class is failed at the END.
H33-3  (O-2) without COLLECT the first defect closes the class (unchanged TR behaviour) and the grains never run are named in the report.
H33-4  (O-2) the mode is explicit — `--collect` or TRIAL_COLLECT=1; default is the TR shape — and the report names it.
H33-5  (O-2) a class-less substep that raises still aborts the build in COLLECT mode (nothing downstream of the head can be trusted).
H33-6  (O-2) a COLLECT run is never a QUALIFYING_CANDIDATE, however clean.
[the doctrine behind the claims is the plan v3.0 / PRETR_EARLY.md §3 O-1, O-2 ruling (madhav-44 18:58Z); N.8 — a stage kind and a mode are measured, not defaulted]"""
import contextlib
import copy
import datetime as dt
import subprocess
import sys
import time
import types
from pathlib import Path

import pytest

import fixtures as fx
import trial_eval as te
import trial_slice as ts

HARNESS = Path(__file__).resolve().parents[1]
PE, PA = "parental_event", "property_acquisition"


class _Step:
    def __init__(self, key):
        self.key = key


class _Result:
    def __init__(self):
        self.rows_inserted, self.notes = 1, ""


class _Fake(types.ModuleType):
    pass


def class_of_grain(key):
    parts = key.split(":")
    return parts[1] if parts[0] in ("window", "record", "verify") else None


class World:
    """A stand-in sidecar: a writer whose plan is `plan`, whose steps in `fail` raise (after `sleep_s`), and a `build_slice` that is the real one's loop."""

    def __init__(self, monkeypatch, plan, fail=(), sleep_s=0.0, state=None):
        self.ran, self.fail, self.sleep_s, self.state, self.dead_when_ran = [], set(fail), sleep_s, state, {}
        world = self

        class Writer:
            def plan_substeps(self, ctx):
                return [_Step(k) for k in plan]

            def run_substep(self, ctx, step):
                world.ran.append(step.key)
                world.dead_when_ran[step.key] = list((world.state or {}).get("dead_classes", []))
                if step.key in world.fail:
                    time.sleep(world.sleep_s)
                    raise RuntimeError(f"planted defect in {step.key}")
                return _Result()

        writer_mod = _Fake("pipeline.orchestrator.writers.ka_gochara_v5")
        writer_mod.GocharaV5Writer, writer_mod._class_of_grain, writer_mod.DEFER_VERIFY_KEY = Writer, class_of_grain, "defer_verify"
        q = _Fake("scripts.kala_gochara_cutover.j4d_slice_qualify")

        def build_slice(conn, *, chart_id, horizon, classes, ephe_path, build_id, final_rules, result_policy, on_step=None):
            w, ctx = writer_mod.GocharaV5Writer(), types.SimpleNamespace(config={})
            plan_ = [s for s in w.plan_substeps(ctx) if class_of_grain(s.key) in set(classes) | {None}]
            steps, defects = [], []
            for step in plan_:
                try:
                    result = w.run_substep(ctx, step)
                except Exception as exc:                                                    # the real loop's shape
                    defects.append({"step": step.key, "defect": "substep_raised", "detail": f"{type(exc).__name__}: {exc}"})
                    break
                steps.append({"step": step.key, "rows": result.rows_inserted})
            return {"steps": steps, "defects": defects, "observed": {"certification_policies": [], "maximise_earliest_calls": 0}, "near_miss_layer": "layer"}
        q.build_slice = build_slice

        psycopg = _Fake("psycopg")
        psycopg.connect = lambda dsn, **kw: contextlib.nullcontext(object())
        mods = {"pipeline": _Fake("pipeline"), "pipeline.orchestrator": _Fake("pipeline.orchestrator"), "pipeline.orchestrator.writers": _Fake("pipeline.orchestrator.writers"),
                "pipeline.orchestrator.writers.ka_gochara_v5": writer_mod, "scripts": _Fake("scripts"), "scripts.kala_gochara_cutover": _Fake("scripts.kala_gochara_cutover"),
                "scripts.kala_gochara_cutover.j4d_slice_qualify": q, "psycopg": psycopg}
        mods["pipeline.orchestrator.writers"].ka_gochara_v5 = writer_mod
        mods["scripts.kala_gochara_cutover"].j4d_slice_qualify = q
        for k, m in mods.items():
            monkeypatch.setitem(sys.modules, k, m)
        self.clock = te.StageClock(lambda: False, interval_s=0.5)
        monkeypatch.setattr(ts, "make_clock", lambda state: self.clock)

        class Meter:
            @contextlib.contextmanager
            def measure(self, stage):
                yield {"cpu_s": None}

            def record(self):
                return {}

            def close(self):
                pass
        monkeypatch.setattr(ts, "make_cpu_meter", lambda state: Meter())
        monkeypatch.setattr(ts, "ruled_horizon", lambda: (dt.datetime(1998, 1, 1, tzinfo=dt.timezone.utc), dt.datetime(1999, 1, 1, tzinfo=dt.timezone.utc)))
        monkeypatch.setattr(ts, "probe_solver", lambda calls, name=None: contextlib.nullcontext(False))


def run_build(monkeypatch, tmp_path, plan, classes, *, fail=(), collect=False, sleep_s=0.0):
    state = {"classes": classes, "requested_policy": "default", "steps": [], "defects": [], "db": "ky_trial_x", "collect": collect}
    world = World(monkeypatch, plan, fail, sleep_s, state)
    complete = ts.build(state, tmp_path, None)
    return state, world, complete


# ── H33-1 (O-1) ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_h33_1_a_window_substep_that_raises_is_booked_under_window_failed_never_under_empty(monkeypatch, tmp_path):
    """O-1: the harness booked a failed window substep under `empty` because the kind was learnt only from a SUCCESSFUL step.  The kind now comes from the plan, before the
    step runs: the failing step's wall is in `build:window`, its defect row reads kind `window`, status `failed`, and the report's failed-by-kind block says so."""
    state, world, complete = run_build(monkeypatch, tmp_path, [f"window:{PE}:P1"], [PE], fail=[f"window:{PE}:P1"], sleep_s=0.08)
    assert complete is True
    stages = world.clock.stages
    assert stages["build:window"]["wall_s"] >= 0.08                                   # the raise burned its wall in `window`
    assert stages.get("build:empty", {"wall_s": 0.0})["wall_s"] < 0.05                # ... and not in `empty` (only the closing no-op iteration is there)
    d = state["defects"][0]
    assert (d["kind"], d["status"], d["defect"]) == ("window", "failed", "substep_raised")
    failed = ts.failed_steps_by_kind(state)
    assert set(failed) == {"window"} and failed["window"]["steps"] == 1 and failed["window"]["secs"] >= 0.08


# ── H33-2 / H33-3 (O-2) ─────────────────────────────────────────────────────────────────────────────────────────

PLAN = ["rules", f"window:{PE}:P1", f"window:{PE}:P2", f"window:{PE}:P3", f"window:{PE}:P4", f"window:{PA}:P1", f"window:{PA}:P2"]
TWO_DEFECTS = [f"window:{PE}:P1", f"window:{PE}:P2"]                                  # two defects on different paths of ONE class (PRETR-early D-A / D-B)


def test_h33_2_collect_reports_both_defects_of_a_class_runs_the_rest_and_fails_the_class_at_the_end(monkeypatch, tmp_path):
    """O-2: with COLLECT the first defect of parental_event does not hide the second; P3 and P4 of it still run; the class is in `dead_classes` only when the build ends
    (it was not yet failed while P3 ran), with every defect listed under it; the other class is untouched."""
    state, world, complete = run_build(monkeypatch, tmp_path, PLAN, [PE, PA], fail=TWO_DEFECTS, collect=True)
    assert complete is True
    assert [d["step"] for d in state["defects"]] == TWO_DEFECTS
    assert {f"window:{PE}:P3", f"window:{PE}:P4"} <= set(world.ran)                   # the remaining grains were evaluated
    assert world.dead_when_ran[f"window:{PE}:P3"] == []                                 # "marked failed at the END"
    assert state["dead_classes"] == [PE]
    assert [x["step"] for x in ts.defects_by_class(state)[PE]] == TWO_DEFECTS
    assert ts.untested_after_defect(state) == []                                        # nothing was left untested
    assert {f"window:{PA}:P1", f"window:{PA}:P2"} <= set(world.ran)


def test_h33_3_without_collect_the_first_defect_closes_the_class_and_the_report_names_what_never_ran(monkeypatch, tmp_path):
    """Unchanged TR behaviour: the class's first defect closes it; its later grains are never run; and (new, data not narration) the report lists them as untested."""
    state, world, complete = run_build(monkeypatch, tmp_path, PLAN, [PE, PA], fail=TWO_DEFECTS)
    assert complete is True
    assert [d["step"] for d in state["defects"]] == TWO_DEFECTS[:1]
    assert not ({f"window:{PE}:P2", f"window:{PE}:P3", f"window:{PE}:P4"} & set(world.ran))
    assert state["dead_classes"] == [PE]
    assert ts.untested_after_defect(state) == [f"window:{PE}:P2", f"window:{PE}:P3", f"window:{PE}:P4"]
    assert {f"window:{PA}:P1", f"window:{PA}:P2"} <= set(world.ran)


def test_h33_5_a_class_less_substep_that_raises_still_aborts_in_collect_mode(monkeypatch, tmp_path):
    state, world, complete = run_build(monkeypatch, tmp_path, PLAN, [PE, PA], fail=["rules"], collect=True)
    assert complete is True and state["aborted"] == "class-less substep rules raised"
    assert world.ran == ["rules"]


# ── H33-4 (O-2) the explicit mode ───────────────────────────────────────────────────────────────────────────────

def _args(*extra):
    return ts.build_parser().parse_args(["run", "--checkout", "c", "--result-policy", "default", "--out", "o", *extra])


def test_h33_4_collect_is_explicit_default_is_stop_at_first_and_the_launcher_passes_it(monkeypatch, tmp_path):
    monkeypatch.delenv("TRIAL_COLLECT", raising=False)
    assert ts.collect_requested(_args()) is False
    assert ts.collect_requested(_args("--collect")) is True
    monkeypatch.setenv("TRIAL_COLLECT", "1")
    assert ts.collect_requested(_args()) is True
    monkeypatch.setenv("TRIAL_COLLECT", "0")
    assert ts.collect_requested(_args()) is False

    def dry(env_extra):
        import os
        env = {k: v for k, v in os.environ.items() if not k.startswith("TRIAL_")}
        env.update({"TRIAL_DRY_RUN": "1", "TRIAL_PYTHON": "py", **env_extra})
        return subprocess.run(["bash", str(HARNESS / "run_trial.sh"), str(tmp_path), str(tmp_path / "out")], env=env, capture_output=True, text=True, timeout=30).stdout.split()
    assert "--collect" in dry({"TRIAL_COLLECT": "1"})
    assert "--collect" not in dry({})


def test_h33_4_the_report_names_the_build_mode(monkeypatch, tmp_path):
    """`build.mode`, `config.collect` and the defect grouping come out of the report builder itself (the DB-bound parts — gate, analysis — are the existing tests' stand-ins)."""
    import test_analyse as ta
    monkeypatch.setattr(ts, "run_gate", lambda conn, sidecar, explicit: {"status": "PASSED", "gate_s": 0.0})
    canned = ta.run()                                                                  # computed BEFORE the stand-in replaces `analyse`
    monkeypatch.setattr(ts, "analyse", lambda conn, state, mods: copy.deepcopy(canned))
    for k in ("services", "services.gochara_kernel", "services.gochara_kernel.result_policy"):
        monkeypatch.setitem(sys.modules, k, _Fake(k))
    sys.modules["services.gochara_kernel"].result_policy = sys.modules["services.gochara_kernel.result_policy"]

    def report(collect):
        state, _, _ = run_build(monkeypatch, tmp_path, PLAN, [PE, PA], fail=TWO_DEFECTS, collect=collect)
        state.update({"label": "t", "code": {}, "lane": {"setup_s": 0.0}, "observed": {"certification_policies": [], "maximise_earliest_calls": 0, "near_miss_layer": [],
                                                                                        "solver_calls": {}}, "window_rows_digest": {"stub": 1}, "requested_policy": "window_qualification/1"})
        return ts.build_report(state, tmp_path, None, tmp_path, None, None)
    rc, rs = report(True), report(False)
    assert (rc["build"]["mode"], rc["config"]["collect"]) == ("collect", True)
    assert (rs["build"]["mode"], rs["config"]["collect"]) == ("stop_at_first_defect", False)
    assert [x["step"] for x in rc["build"]["defects_by_class"][PE]] == TWO_DEFECTS
    assert rs["build"]["untested_after_defect"] and not rc["build"]["untested_after_defect"]
    assert rc["runtime_s"]["failed_by_step_kind"]["window"]["steps"] == 2
    assert rc["qualification"]["mode"] == "collect"


# ── H33-6 ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_h33_6_a_collect_run_is_never_a_qualifying_candidate_however_clean(monkeypatch):
    rep = {"trial_ready": fx.trial_ready(), "code": {"head": "a" * 40}, "config": {"classes": []}, "build": {"defects": [], "aborted": None, "mode": "stop_at_first_defect"}}
    assert te.qualification_block(rep)["qualifying"] is True                             # the control: this evidence does qualify
    rep["build"]["mode"] = "collect"
    q = te.qualification_block(rep)
    assert q["qualifying"] is False and q["label"] == "DIAGNOSTIC" and q["g0"] == "PASS"
