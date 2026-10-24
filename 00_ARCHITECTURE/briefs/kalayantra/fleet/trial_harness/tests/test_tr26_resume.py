"""TR-26 kill+resume leg (SR-RESUME-NOW (i)(ii)): the deterministic abort, the harness's own producer-execution log, the writer-resume mode and the G-7 checks that read them.  A stand-in writer (test_harness_33.World)
gives the plan; the ledger-aware variant below is what the writer PR (kalayantra/century-resume-writer, not yet written at c718a5535) is specified to do — the oracles prove the DETECTORS (a writer that does not skip
what it committed reads FAIL), not that writer.  One oracle per distinct claim; the single planted reversion is named in each docstring."""
import copy
import sys
import types

import pytest

import fixtures as fx
import gates
import test_harness_33 as h33
import trial_slice as ts
from gates import FAIL, NOT_EVALUATED, PASS

A, B = "bereavement", "major_loss"
PLAN = ["rules", "convention", "body:Sun", "manifest", "snapshot", f"record:{A}", f"window:{A}", f"verify:{A}", f"record:{B}", f"window:{B}", f"verify:{B}"]


def ledger_aware(world, committed):
    """Make the stand-in writer behave as the resume writer is specified to: plan_substeps skips what its ledger holds; a substep is committed when it completes."""
    mod = sys.modules["pipeline.orchestrator.writers.ka_gochara_v5"]
    base = mod.GocharaV5Writer

    class Ledgered(base):
        def plan_substeps(self, ctx):
            return [s for s in base.plan_substeps(self, ctx) if s.key not in committed]

        def run_substep(self, ctx, step):
            r = base.run_substep(self, ctx, step)
            committed.add(step.key)
            return r
    mod.GocharaV5Writer = Ledgered


def leg(monkeypatch, tmp_path, *, ledger):
    """Kill a fresh build, then resume it; returns the resumed state."""
    committed: set = set()
    state = {"classes": [A, B], "requested_policy": "default", "steps": [], "defects": [], "db": "ky_trial_x", "collect": False}
    w = h33.World(monkeypatch, PLAN, (), 0.0, state)
    if ledger:
        ledger_aware(w, committed)
    assert ts.build(state, tmp_path, None, abort_after="auto") is False
    w2 = h33.World(monkeypatch, PLAN, (), 0.0, state)
    if ledger:
        ledger_aware(w2, committed)
    state["writer_resumed"] = True
    assert ts.build(state, tmp_path, None, writer_resume=True) is True
    return state


def test_the_abort_point_is_a_pure_function_of_the_plan_inside_the_window_sweep_with_a_class_committed():
    """The kill lands where a class is fully committed and a `window:` substep of another class is next.  Reversion: return the first index (1) -> no committed class behind it."""
    n = ts.choose_abort_substep(PLAN, [A, B])
    assert n == 9 and PLAN[n] == f"window:{B}" and ts.classes_committed(PLAN, PLAN[:n], [A, B]) == [A]
    kind_major = [f"record:{A}", f"record:{B}", f"window:{A}", f"window:{B}", f"verify:{A}", f"verify:{B}"]
    assert ts.choose_abort_substep(kind_major, [A, B]) is None            # no class is complete before a window substep: nothing to kill honestly


def test_build_kills_after_n_substeps_keeps_the_log_and_refuses_when_the_plan_has_no_abort_point(monkeypatch, tmp_path):
    state = {"classes": [A, B], "requested_policy": "default", "steps": [], "defects": [], "db": "ky_trial_x", "collect": False}
    h33.World(monkeypatch, PLAN, (), 0.0, state)
    assert ts.build(state, tmp_path, None, abort_after="auto") is False
    assert state["killed_after_substep"] == 9 and state["abort_next_step"] == f"window:{B}" and state["classes_committed_at_abort"] == [A]
    assert [e["step"] for e in state["executed_log"]] == PLAN[:9] and {e["phase"] for e in state["executed_log"]} == {"initial"} and state["plan_substeps"] == PLAN
    bad = {"classes": [A, B], "requested_policy": "default", "steps": [], "defects": [], "db": "ky_trial_x", "collect": False}
    h33.World(monkeypatch, [f"window:{A}", f"window:{B}", f"verify:{A}", f"verify:{B}"], (), 0.0, bad)
    with pytest.raises(ts.Refused):
        ts.build(bad, tmp_path, None, abort_after="auto")


def test_a_ledger_aware_writer_resumes_without_re_running_and_the_log_proves_it(monkeypatch, tmp_path):
    """before-kill ∪ after-resume == the plan, with no substep in both.  Reversion: make the harness skip by its own `done` on resume (the harness, not the writer, would then be what skips)."""
    state = leg(monkeypatch, tmp_path, ledger=True)
    rl = ts.resume_leg_section(state)
    assert rl["executed_before_abort"] == PLAN[:9] and rl["executed_after_resume"] == PLAN[9:] and rl["rerun_after_resume"] == [] and rl["resumed"] is True


def test_a_writer_that_does_not_skip_what_it_committed_reads_as_re_running_every_substep(monkeypatch, tmp_path):
    """Today's writer (no ledger): the resume re-runs the whole plan.  The log must show it — the detector can read false.  Reversion: skip the log append in run_deferring."""
    state = leg(monkeypatch, tmp_path, ledger=False)
    rl = ts.resume_leg_section(state)
    assert rl["rerun_after_resume"] == sorted(PLAN[:9]) and len(rl["executed_after_resume"]) == len(PLAN)


# ── G-7: the kill+resume checks ─────────────────────────────────────────────────────────────────────────────────

CLASSES = [A, B]


def profile():
    p = fx.profile(trial_classes=CLASSES)
    p["determinism"] = {"kill_resume": {"required": True, "refusal_message_contains": "digest"}}
    return p


def digest(sha="a" * 64, per=None, mem="m" * 64):
    return {"sha256": sha, "windows": 10, "per_class": per or {A: "1" * 64, B: "2" * 64}, "memberships_sha256": mem, "memberships": 5}


PROBE = {"attempted": True, "refused": True, "refusal_name": "ProgramDigestMismatch", "message": "resume refused: the program digest differs from the ledger's", "executed_substeps": 0}


def pair(monkeypatch, tmp_path, *, ledger=True, probe=PROBE, resumed_digest=None):
    state = leg(monkeypatch, tmp_path, ledger=ledger)
    state["refusal_probe"] = copy.deepcopy(probe)
    fresh, second = fx.report(), fx.report()
    fresh["window_rows_digest"] = digest()
    second["window_rows_digest"] = resumed_digest or digest()
    second["resume_leg"] = ts.resume_leg_section(state)
    return fresh, second


def g7(a, b):
    return gates.g7_determinism(a, b, profile())


def claim(g, part):
    return next(c for c in g["checks"] if part in c["claim"])


def test_g7_passes_a_resumed_leg_that_skipped_what_it_committed_is_byte_identical_and_refused_a_different_digest(monkeypatch, tmp_path):
    a, b = pair(monkeypatch, tmp_path)
    g = g7(a, b)
    assert g["status"] == PASS, [c for c in g["checks"] if c["status"] != PASS]


def test_g7_fails_when_the_resume_re_ran_a_substep_it_had_already_run(monkeypatch, tmp_path):
    """SR-RESUME-NOW (i): the skipped substeps must provably not have re-run.  Reversion: drop the before∩after check in g7_kill_resume_checks."""
    a, b = pair(monkeypatch, tmp_path, ledger=False)
    c = claim(g7(a, b), "did not re-run")
    assert c["status"] == FAIL and c["observed"]["rerun"] == 9


def test_g7_fails_when_one_class_of_the_resumed_generation_differs_by_a_byte(monkeypatch, tmp_path):
    """Byte identity per class over the full output.  Reversion: compare only the total sha256."""
    a, b = pair(monkeypatch, tmp_path, resumed_digest=digest(per={A: "1" * 64, B: "3" * 64}))
    c = claim(g7(a, b), "byte-identical to the fresh one")
    assert c["status"] == FAIL and c["observed"]["differing_classes"] == [B]


def test_g7_does_not_accept_a_leg_that_covers_fewer_classes_than_the_trial(monkeypatch, tmp_path):
    """The surrogate's condition: the leg stands in for the plain second run ONLY over the full class set.  Reversion: compare the classes both sides happen to have."""
    a, b = pair(monkeypatch, tmp_path, resumed_digest=digest(per={A: "1" * 64}))
    assert claim(g7(a, b), "compared over every trial class")["status"] == NOT_EVALUATED


def test_g7_requires_the_kill_inside_the_window_sweep_with_a_committed_class(monkeypatch, tmp_path):
    a, b = pair(monkeypatch, tmp_path)
    b["resume_leg"]["abort_next_step"] = f"record:{B}"
    assert claim(g7(a, b), "kill landed inside the window sweep")["status"] == FAIL
    a, b = pair(monkeypatch, tmp_path)
    b["resume_leg"]["classes_committed_at_abort"] = []
    assert claim(g7(a, b), "kill landed inside the window sweep")["status"] == FAIL


def test_g7_fails_a_resume_that_was_not_refused_by_name_when_the_digest_differs(monkeypatch, tmp_path):
    """SR-RESUME-NOW (ii): a resume with a different program digest must refuse BY NAME before running anything.  Reversion: accept `refused` alone."""
    for bad in ({**PROBE, "refused": False}, {**PROBE, "executed_substeps": 3}, {**PROBE, "refusal_name": "RuntimeError"}, {**PROBE, "message": "boom"}):
        a, b = pair(monkeypatch, tmp_path, probe=bad)
        assert claim(g7(a, b), "different program digest refuses by name")["status"] == FAIL, bad


def test_g7_is_not_evaluated_without_a_resume_leg_or_a_probe(monkeypatch, tmp_path):
    a, b = pair(monkeypatch, tmp_path)
    del b["resume_leg"]
    assert g7(a, b)["status"] == NOT_EVALUATED
    a, b = pair(monkeypatch, tmp_path)
    b["resume_leg"]["refusal_probe"] = None
    assert claim(g7(a, b), "different program digest refuses by name")["status"] == NOT_EVALUATED
    a, b = pair(monkeypatch, tmp_path)
    b["resume_leg"]["resumed"] = False
    assert g7(a, b)["status"] == NOT_EVALUATED


def test_the_tr26_profile_requires_the_kill_resume_leg():
    import json
    prof = json.loads((ts.HERE / "gate_profile.tr26.json").read_text())
    assert prof["determinism"]["kill_resume"]["required"] is True and prof["determinism"]["verifier_repeat"]["required"] is True
