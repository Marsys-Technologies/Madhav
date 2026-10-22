"""HARNESS-3.2 (PRETR-3a D-8, D-9, D-10): one oracle per distinct claim, each failing on its single planted reversion (`mutants_h32.py`).

H-a   (D-8)  the cross-check rebuilds a P2 vedha-bearing numbered window QUALIFIED: the vedha source is the writer's `vedha_source()` bound per grain with
             `for_grain(..., position_at=)` (the post-od1-vedha-residence signature), never the module constant `VEDHA_SOURCE` (None).
             [PLAN_v2 §4.4 G-6: re-solve from the stored members; ka_gochara_v5._run_window_phase]
H-a2  (D-8)  the same function binds the P1 operand sources of a P1 grain, and runs under `rule_profile(final_rules=True)` like `verify_stage`.
H-b   (D-9)  G-4's verdict is scoped to the trial classes. [numerical_window_gate.generation_verdict(classes=): "limits it to a class subset"; TR_DRYRUN gap 7]
H-c   (D-10) G-5's projection reads NOT_EVALUATED — never FAIL or PASS — for a slice smaller than the trial and for a run measured on a loaded machine;
             a quiet 12-class run is computed exactly as before.  [§N.8: a signal needs a detector that can read false]

The writer is a stand-in for the post-merge head (the base of this harness may predate it); the sweep primitives (`window_sweep`) and `rule_registry` are the real ones."""
import copy
import sys
import types
from datetime import datetime, timedelta, timezone

import pytest

import fixtures as fx
import gates
import trial_eval as te
import trial_slice as ts
from gates import FAIL, NOT_EVALUATED, PASS

ws = pytest.importorskip("services.gochara_kernel.window_sweep")
rr = pytest.importorskip("services.gochara_kernel.rule_registry")

T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)
HOUR = timedelta(hours=1)


# ── the cross-check world (H-a, H-a2) ───────────────────────────────────────────────────────────────────────────

class _Cur:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows

    def cursor(self):
        return self


class _Conn:
    def __init__(self, ids):
        self.ids = ids

    def execute(self, sql, args=()):
        assert "ka_gochara_eval_window_record" in sql
        return _Cur([(i,) for i in self.ids])

    def cursor(self):
        return "cursor"


def _record(rid, path, *, complete=True):
    """A record with a vedha-bearing (state-valued) factor; its state boundaries are asserted complete only when `complete` (a P1 record built without its operand
    sources has no such assertion — the store attaches the per-factor sources only when `p1=` is passed)."""
    return ws.SweepRecord(record_id=rid, root_id="root-" + rid, path_id=path, rule_version="1.3.0", relation="conjunction", object_kind="point_longitude", agent="jupiter",
                          operator_role="scored", admission_state="admitted", supports=((T0, T0 + HOUR),), house_from_frame=2,
                          state_boundaries=(lambda lo, hi: []) if complete else None, state_boundaries_complete=complete)


def _final_active() -> bool:
    """The active rule profile, read the way the writer reads it (`final_rules_active()` after od1-vedha-residence; the context variable before it)."""
    reader = getattr(rr, "final_rules_active", None)
    return reader() if reader else rr._FINAL_RULES.get()


VEDHA_ROW = {"factor_id": "vedha_attenuation", "rule_version": "1.3.0", "null_state": ws.UNQUALIFIED}


class _Overlay:
    """The writer's vedha source: `vedha_source()` of the active rule profile → a source with `for_grain`, whose signature is the post-od1-vedha-residence one
    (`vedha_source.py` VedhaSource.for_grain @ d4144bedb)."""

    def __init__(self):
        self.calls = []

    def for_grain(self, conn, *, chart_id: str, generation: str, event_class: str, records, moon_sign: int | None = None, position_at=None):
        self.calls.append({"chart_id": chart_id, "generation": generation, "event_class": event_class, "records": list(records), "position_at": position_at})
        return lambda rec, t: 0.5            # the derived overlay: obstruction attenuates to 0.5 over the support


class _Store:
    def __init__(self, path):
        self.path, self.seen = path, []

    def read_grain(self, *, chart_id, generation, event_class, path_id, rule_version, position_at=None, p1=None, speed_at=None):
        self.seen.append({"path_id": path_id, "p1": p1, "position_at": position_at})
        # contract (window_store.read_grain): `p1` "adds the P1 factors' per-factor sources to the P1 records; absent, the records are exactly what they were"
        return [_record("r1", path_id, complete=(path_id != "P1" or p1 is not None))]


def _env(path, overlay, *, p1_value_rules=None):
    env = object.__new__(ts._CrosscheckEnv)
    env.conn, env.ws, env.records = _Conn(["r1"]), ws, {}
    env.position_at = lambda body, t: 0.0
    env.store = _Store(path)

    def bound_rows(path_id, version):
        if not _final_active():
            raise KeyError(f"no bound factor rows for {(path_id, version)} outside the final profile")
        return [dict(VEDHA_ROW, **({"form_b": True} if path_id == "P1" else {}))]
    env.bound_rows = bound_rows
    env.w = types.SimpleNamespace(DRISHTI_SOURCE=None, VEDHA_SOURCE=None, P1_VALUE_RULES=p1_value_rules,
                                  vedha_source=lambda: overlay if _final_active() else None)
    return env


def _win(path):
    return {"window_id": "w1", "event_class": "bereavement", "path_id": path, "rule_version": "1.3.0", "lo": T0, "hi": T0 + HOUR}


def test_h_a_the_cross_check_rebuilds_a_vedha_bearing_p2_window_with_the_per_grain_derived_overlay():
    overlay = _Overlay()
    env = _env("P2", overlay)
    pieces = env.pieces(_win("P2"))
    assert pieces and pieces[0]["live"], "the numbered window re-solves into pieces with a live member"
    (call,) = overlay.calls
    assert call["chart_id"] == ts.CHART and call["generation"] == ts.GENERATION and call["event_class"] == "bereavement"
    assert [r.record_id for r in call["records"]] == ["r1"] and call["position_at"] is env.position_at      # post-merge signature: position_at= is the harness's own probe
    t = T0 + HOUR / 2
    assert pieces[0]["live"][0].outcomes[0].fn(t) == pytest.approx(0.5)        # the member's vedha factor IS the derived overlay


def test_h_a2_a_p1_grain_is_read_with_the_writers_p1_operand_sources(monkeypatch):
    seen = {}

    class P1Operands:
        def __init__(self, l0, position_at, *, rules, form_b):
            seen.update(l0=l0, position_at=position_at, rules=rules, form_b=form_b)
    p1o = types.ModuleType("services.gochara_kernel.p1_operands")
    p1o.form_b_mapping = lambda rows: {"table": "B"} if any(r.get("form_b") for r in rows) else None
    p1o.load_p1_l0 = lambda cur: ("L0", cur)
    p1o.P1Operands = P1Operands
    monkeypatch.setitem(sys.modules, "services.gochara_kernel.p1_operands", p1o)
    monkeypatch.setattr(sys.modules["services.gochara_kernel"], "p1_operands", p1o, raising=False)
    # the sweep of this base cannot place a P1 record in a channel or solve its objective (P1 is categorical here): the binding is what is under test, so the two
    # downstream steps are stood in for; an UNQUALIFIED member still raises first
    monkeypatch.setattr(ws, "_program_channel", lambda event_class, rec, qualified: ws.CHANNEL_FOR)
    monkeypatch.setattr(ts.cx, "pieces_of", lambda *a, **k: ["pieces"])
    env = _env("P1", _Overlay())
    assert env.pieces(_win("P1")), "a P1 numbered window with Form B operands re-solves qualified"
    assert isinstance(env.store.seen[0]["p1"], P1Operands)
    assert seen["l0"] == ("L0", "cursor") and seen["position_at"] is env.position_at and seen["form_b"] == {"table": "B"} and seen["rules"] is None
    other = _env("P2", _Overlay())
    other.pieces(_win("P2"))
    assert other.store.seen[0]["p1"] is None                           # only a P1 grain carries the operand sources


def test_h_a2_the_cross_check_runs_under_the_final_rule_profile_and_leaves_none_behind():
    env = _env("P2", _Overlay())
    assert _final_active() is False
    assert env.pieces(_win("P2")), "final-profile factor rows and the profile's vedha source are found"
    assert _final_active() is False


# ── H-b: G-4's verdict is scoped to the trial classes ───────────────────────────────────────────────────────────

UNIVERSE = [f"universe_class_{i:02d}" for i in range(14)] + list(gates.TRIAL_CLASSES_12)       # the verifier's pinned 26-class universe


def _scoped_nwg(attested):
    """The documented contract of `numerical_window_gate.generation_verdict` (:151, 386, 393, 410): `classes=None` is the aggregate over the pinned universe — a class
    that is not built is 'no search-path pin at all'; `classes=[...]` limits the verdict to that subset."""
    def generation_verdict(conn, chart_id, generation, classes=None):
        scope = UNIVERSE if classes is None else list(classes)
        problems = [f"{c}: no search-path pin at all" if classes is None else f"{c}: no window verification row" for c in scope if c not in attested]
        return {"status": "FAILED" if problems else "PASSED", "numbered_windows": 10, "judgment_flags": [], "problems": problems}
    return generation_verdict


def _verify(monkeypatch, tmp_path, attested):
    import test_t1b_fix as t1b
    _, _, conn = t1b._verify_world(monkeypatch, {})
    sys.modules["services.gochara_kernel.numerical_window_gate"].generation_verdict = _scoped_nwg(set(attested))
    state = {"classes": list(gates.TRIAL_CLASSES_12), "verification": {"classes": {}, "ran": False}}
    assert ts.verify_stage(state, tmp_path, conn, None) is True
    return state["verification"]


def test_h_b_a_12_class_generation_is_judged_on_its_12_classes_not_the_26_class_universe(monkeypatch, tmp_path):
    v = _verify(monkeypatch, tmp_path, gates.TRIAL_CLASSES_12)
    assert v["generation_verdict"]["status"] == "PASSED" and not v["generation_verdict"]["problems"], v["generation_verdict"]
    assert v["generation_verdict_scope"]["classes"] == sorted(gates.TRIAL_CLASSES_12) and "aggregate-only" in v["generation_verdict_scope"]["not_part_of_this_reading"]
    r, b, p = fx.good()
    r["verification"] = {**r["verification"], "generation_verdict_scope": v["generation_verdict_scope"]}
    assert gates.evaluate(r, b, p)["gates"]["G-4"]["verdict_scope"]["scoped"] is True        # the report line reaches the gate record


def test_h_b_a_class_the_trial_did_not_attest_still_fails_the_scoped_verdict(monkeypatch, tmp_path):
    v = _verify(monkeypatch, tmp_path, [c for c in gates.TRIAL_CLASSES_12 if c != "parental_event"])
    assert v["generation_verdict"]["status"] == "FAILED" and v["generation_verdict"]["problems"] == ["parental_event: no window verification row"]


# ── H-c: G-5 is NOT_EVALUATED unless the measurement is of the full trial on a quiet machine ───────────────────────

PROJECTION = "projected century writer time ≤ limit"
#: PRETR-3a PROJ A: base 3,773.4 s (head 2,214 s) + solver 349.1 s → (3,773.4 + 349.1) × 26 ≈ 107,185 s for a ONE-class slice
SLICE_KINDS = {"body": 2214.0, "record": 1559.4, "window": 349.1}
#: a 12-class build slow enough to be over the limit (43,200 s) when it IS a valid measurement: (2,214 + 18,000 + 1,500) × 26 / 12 = 47,047 s
SLOW_KINDS = {"body": 2214.0, "record": 18000.0, "window": 1500.0}
FAST_KINDS = {"body": 330.0, "record": 800.0, "window": 50.0}


def _g5(classes, kinds, load=fx.QUIET_LOAD, profile=None):
    r = fx.a10_report()
    r["config"]["classes"] = list(classes)
    r["runtime_s"]["by_step_kind"] = dict(kinds)
    r["effective_wall"]["stages"] = {f"build:{k}": {"wall_s": v, "lock_wait_s": 0.0, "compute_s": v, "max_load_per_core": load} for k, v in kinds.items()}
    g = gates.g5_runtime(r, profile or fx.profile(), r["verification"])
    return next(c for c in g["checks"] if c["claim"] == PROJECTION), g


def test_h_c_a_slice_smaller_than_the_trial_is_not_evaluated_not_failed():
    c, g = _g5(["major_loss"], SLICE_KINDS)
    assert c["status"] == NOT_EVALUATED and c["observed"] == {"trial_classes": 1, "required": 12}, c
    assert g["projection"]["projected_writer_s"] == pytest.approx(107185.0, abs=0.1)        # the number is still reported, as informational, beside the unevaluated claim


def test_h_c_a_run_measured_on_a_loaded_machine_is_not_evaluated_and_a_quiet_one_is_computed_as_before():
    quiet_slow, _ = _g5(gates.TRIAL_CLASSES_12, SLOW_KINDS)
    assert quiet_slow["status"] == FAIL and quiet_slow["observed"] == pytest.approx(47047.0, abs=0.5)        # a valid, slow measurement still reads FAIL
    quiet_fast, _ = _g5(gates.TRIAL_CLASSES_12, FAST_KINDS)
    assert quiet_fast["status"] == PASS and quiet_fast["observed"] == pytest.approx((330 + 800 + 50) * 26 / 12, abs=0.1)
    loaded, g = _g5(gates.TRIAL_CLASSES_12, SLOW_KINDS, load=2.4)
    assert loaded["status"] == NOT_EVALUATED and "load" in loaded["note"], loaded
    assert g["projection"]["load"]["max_load_per_core"] == 2.4 and g["projection"]["load"]["bound_per_core"] == 1.0
    assert len(g["projection"]["load"]["stages_over_bound"]) == len(SLOW_KINDS)


def test_h_c_a_run_that_recorded_no_load_is_unknown_never_quiet_and_a_final_profile_must_state_the_bound():
    unmeasured, _ = _g5(gates.TRIAL_CLASSES_12, FAST_KINDS, load=None)
    assert unmeasured["status"] == NOT_EVALUATED
    r = fx.a10_report()
    del r["effective_wall"]
    assert next(c for c in gates.g5_runtime(r, fx.profile(), r["verification"])["checks"] if c["claim"] == PROJECTION)["status"] == NOT_EVALUATED
    final = fx.profile(final=True)
    del final["runtime"]["max_load_per_core"]
    c, g = _g5(gates.TRIAL_CLASSES_12, FAST_KINDS, profile=final)
    assert c["status"] == NOT_EVALUATED and any(k["status"] == FAIL and "load bound is explicit" in k["claim"] for k in g["checks"])
    stated, _ = _g5(gates.TRIAL_CLASSES_12, FAST_KINDS, profile=fx.profile(final=True))
    assert stated["status"] == PASS                                   # the shipped profile carries the (placeholder) bound


def test_h_c_the_shipped_profiles_carry_a_named_placeholder_for_the_surrogate_ruling():
    import json
    for name in ("gate_profile.plan_defaults.json", "gate_profile.owner_proposal.json"):
        rt = json.loads((fx.HARNESS / name).read_text())["runtime"]
        assert rt["max_load_per_core"] == 1.0 and rt["max_load_per_core_ruling"].startswith("PLACEHOLDER-SURROGATE-RULING-G5-MAX-LOAD-PER-CORE")


def test_h_c_the_clock_records_the_busiest_load_per_core_of_every_stage_and_keeps_it_across_a_resume():
    calls = iter([0.3, 2.5])
    c = te.StageClock(lambda: False, interval_s=0.02, load_probe=lambda: next(calls, 0.4))
    with c.measure("build:record"):
        pass
    quiet = te.StageClock(lambda: False, interval_s=0.02, load_probe=lambda: 0.1)
    with quiet.measure("build:body"):
        pass
    s = c.record()["stages"]["build:record"]
    assert s["max_load_per_core"] == 2.5 and s["load_samples"] >= 2
    assert quiet.record()["stages"]["build:body"]["max_load_per_core"] == 0.1
    again = te.StageClock(lambda: False)
    again.load(copy.deepcopy(c.record()))
    assert again.record()["stages"]["build:record"]["max_load_per_core"] == 2.5
    peaks = iter([2.5, 2.5, 0.1, 0.1])                                                    # the same stage recurs per substep: the busiest of its measurements is kept
    twice = te.StageClock(lambda: False, interval_s=0.02, load_probe=lambda: next(peaks, 0.1))
    for _ in range(2):
        with twice.measure("build:record"):
            pass
    assert twice.record()["stages"]["build:record"]["max_load_per_core"] == 2.5
    blind = te.StageClock(lambda: False, load_probe=lambda: None)
    with blind.measure("build:body"):
        pass
    assert blind.record()["stages"]["build:body"]["max_load_per_core"] is None            # an unanswerable sample is unknown, not 0


# ── H-c on the A10.1 evaluator: gates.evaluate(..., decision_table=...) is what the trial driver always runs (review 3879 B-1) ──

EFFECTIVE = "projected effective wall (compute + lock wait) ≤ limit"


def _g5_a10(classes, kinds, load=fx.QUIET_LOAD):
    r = fx.a10_report()
    r["config"]["classes"] = list(classes)
    r["runtime_s"]["by_step_kind"] = dict(kinds)
    r["effective_wall"]["stages"] = {f"build:{k}": {"wall_s": v, "lock_wait_s": 0.0, "compute_s": v, "max_load_per_core": load} for k, v in kinds.items()}
    v = gates.evaluate(r, fx.a10_baseline(), fx.profile(), decision_table=fx.decision_table(), dispatch_digests=fx.dispatch_digests(), verification=r["verification"])
    g5 = v["gates"]["G-5"]
    return g5, next(c for c in g5["checks"] if c["claim"] == EFFECTIVE)


def test_h_c_a10_a_one_class_slice_reads_g5_not_evaluated_through_gates_evaluate():
    g5, c = _g5_a10(["major_loss"], SLICE_KINDS)        # the 26× head scaling would be 107,185 s > 43,200 s: FAIL for the slice, not the build
    assert c["status"] == NOT_EVALUATED and c["observed"] == {"trial_classes": 1, "required": 12}, c
    assert g5["status"] == NOT_EVALUATED, g5["status"]


def test_h_c_a10_a_loaded_12_class_run_reads_g5_not_evaluated_and_a_quiet_one_is_computed_as_before():
    g5, c = _g5_a10(gates.TRIAL_CLASSES_12, SLOW_KINDS, load=2.4)
    assert c["status"] == NOT_EVALUATED and "load" in c["note"], c
    assert g5["status"] == NOT_EVALUATED, g5["status"]
    _, quiet_slow = _g5_a10(gates.TRIAL_CLASSES_12, SLOW_KINDS)
    assert quiet_slow["status"] == FAIL
    g5_fast, quiet_fast = _g5_a10(gates.TRIAL_CLASSES_12, FAST_KINDS)
    assert quiet_fast["status"] == PASS and g5_fast["status"] == PASS
