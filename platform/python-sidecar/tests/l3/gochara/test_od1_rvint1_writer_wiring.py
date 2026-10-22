"""RV-INT part 1, B5 — the build→verify WIRING of the Form B / S3 / C1 / R4 seams in the Gochara writer's window phase.

The C1 and S3 merge-backs had to union exactly these lines of `ka_gochara_v5._run_window_phase`; five of six planted reversions of them survived the whole runnable suite, and the one
oracle that looked (`"speed_at" in src`) was satisfied by the `def speed_at` a few lines above (root CLAUDE.md §N.8: a signal whose check cannot read false is null, not green).
This oracle is structural (AST on the writer source, no database): each claim is the keyword that carries a seam INTO the call that consumes it, and each is paired with the single
planted reversion (a textual edit of the real source) that the detector must report — so the detector itself is shown to be able to read false.

Claims (each: what the writer must hand over; what is lost when it does not — doctrine: SR-OD1 D2/Q3C Form B, R4/SR-Q6-L1-AMEND, C1 vedha grain binding, S3 solver; B.3, B.10, §N.5):
  W1 `read_grain(p1=p1_ops)`           — the P1 operands reach the stored windows' operand reads; without it Form B P1 windows are blank
  W2 `read_grain(speed_at=speed_at)`   — the speed seam reaches the reads that need a body's speed
  W3 `draft_windows(combustion_inheritance=inherited)` — R4: every Form B window records the combustion authority it was derived from (the verifier refuses windows that record none)
  W4 `verify_window_semantics(p1_check=p1_check)` — D2: the in-build self-check re-derives P1 from the verifier's OWN sky + L0 reads
  W5 `vedha = vedha.for_grain(...)` is reachable (guarded only by hasattr) — C1: the vedha source is bound to its grain
  W6 `draft_windows(solver=PRODUCTION_SOLVER)` — S3: windows are SOLVED, never the retired dynamic switch
  W7 `draft_windows(vedha=vedha)` — the grain-bound source is the one that reaches the draft
"""
from __future__ import annotations

import ast
import inspect

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer


def _name(call: ast.Call) -> str:
    return getattr(call.func, "attr", getattr(call.func, "id", ""))


def wiring_problems(src: str) -> list[str]:
    """Every wiring claim the source of `_run_window_phase` does not meet (an empty list is the only green)."""
    phase = next((n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "_run_window_phase"), None)
    if phase is None:
        return ["_run_window_phase not found"]
    calls = [n for n in ast.walk(phase) if isinstance(n, ast.Call)]

    def one(name: str):
        found = [c for c in calls if _name(c) == name]
        return {k.arg: ast.unparse(k.value) for k in found[0].keywords} if len(found) == 1 else None

    bad: list[str] = []
    for fn, wanted in (("read_grain", {"p1": "p1_ops", "speed_at": "speed_at"}),
                       ("draft_windows", {"solver": "gk_window_sweep.PRODUCTION_SOLVER", "combustion_inheritance": "inherited", "vedha": "vedha"}),
                       ("verify_window_semantics", {"p1_check": "p1_check"})):
        kws = one(fn)
        if kws is None:
            bad.append(f"{fn}: not called exactly once in the window phase")
            continue
        bad += [f"{fn}({k}=…) is {kws.get(k)!r}, not {v!r}" for k, v in wanted.items() if kws.get(k) != v]
    # the values those keywords carry come from the right producers
    assigns = {t.id: ast.unparse(n.value) for n in ast.walk(phase) if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
    for var, needle in (("p1_ops", "p1_operands_for(version)"), ("inherited", "grain_inheritance(p1_ops)"), ("p1_check", "P1Check.from_conn")):
        if needle not in assigns.get(var, ""):
            bad.append(f"{var} is not derived from {needle!r}")
    # W5: the grain binding exists, assigns back to `vedha`, takes the grain identity and the records, and is guarded by nothing but `hasattr(vedha, 'for_grain')`
    guards = [n for n in ast.walk(phase) if isinstance(n, ast.If) and ast.unparse(n.test) == "hasattr(vedha, 'for_grain')"]
    bound = [s for g in guards for s in g.body if isinstance(s, ast.Assign) and [ast.unparse(t) for t in s.targets] == ["vedha"]
             and isinstance(s.value, ast.Call) and _name(s.value) == "for_grain"
             and {"chart_id", "generation", "event_class", "records"} <= {k.arg for k in s.value.keywords}]
    if len(bound) != 1:
        bad.append("vedha = vedha.for_grain(chart_id, generation, event_class, records) is not bound under hasattr(vedha, 'for_grain') alone")
    return bad


def test_the_writer_window_phase_hands_every_seam_to_the_call_that_consumes_it():
    assert wiring_problems(inspect.getsource(writer)) == []


# one planted reversion per claim — the textual edit that undoes just that wiring line; the detector must name it
REVERSIONS = [
    ("W1", "position_at=position_at, p1=p1_ops, speed_at=speed_at)", "position_at=position_at, speed_at=speed_at)", "read_grain(p1"),
    ("W2", "position_at=position_at, p1=p1_ops, speed_at=speed_at)", "position_at=position_at, p1=p1_ops)", "read_grain(speed_at"),
    ("W3", "policy=policy, combustion_inheritance=inherited)", "policy=policy)", "draft_windows(combustion_inheritance"),
    ("W4", "solver_check=False, p1_check=p1_check)", "solver_check=False)", "verify_window_semantics(p1_check"),
    ("W5", 'if hasattr(vedha, "for_grain"):', 'if False and hasattr(vedha, "for_grain"):', "for_grain"),
    ("W6", "solver=gk_window_sweep.PRODUCTION_SOLVER, ", "", "draft_windows(solver"),
    ("W7", "drishti=DRISHTI_SOURCE, vedha=vedha,", "drishti=DRISHTI_SOURCE,", "draft_windows(vedha"),
]


@pytest.mark.parametrize("claim,old,new,named", REVERSIONS, ids=[r[0] for r in REVERSIONS])
def test_each_planted_reversion_of_a_wiring_line_is_reported(claim, old, new, named):
    src = inspect.getsource(writer)
    assert src.count(old) == 1, f"{claim}: the wiring line changed shape; re-point this oracle ({old!r} found {src.count(old)}×)"
    problems = wiring_problems(src.replace(old, new))
    assert any(named in p for p in problems), f"{claim}: reverting {old!r} left the detector green ({problems})"
