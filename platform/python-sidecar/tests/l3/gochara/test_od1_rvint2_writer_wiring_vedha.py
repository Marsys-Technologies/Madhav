"""RV-INT part 2, F-4 extension of the part-1 B5 wiring oracle (test_od1_rvint1_writer_wiring.py, 7 claims W1-W7).

od1-vedha-residence edits `ka_gochara_v5._run_window_phase` at TWO call sites that none of W1-W7 constrain (W5 requires only the keywords chart_id/generation/event_class/records on the
`for_grain` call, W4 only `p1_check` on `verify_window_semantics`):
  W8  `vedha.for_grain(..., position_at=position_at)` — the builder's vedha source derives the obstructors' residence from THIS substep's ephemeris probe (SR-VEDHA-RESIDENCE-SOURCE; without it
      the source has no sky to derive from and every vedha-bearing record is `obstructor_residence_unknown`);
  W9  `verify_window_semantics(..., ephe_path=ephe_path)` — the in-build self-check hands the verifier the ephemeris DIRECTORY its OWN Swiss reader (vedha_verifier.swiss_longitude) needs
      (without it the verifier falls back to the environment, which a mis-provisioned job does not carry; the builder and verifier then disagree on where the sky is).
Same method as part 1: AST on the writer source, no database, each claim has its single textual reversion (W8: drop `position_at=position_at`; W9: drop `ephe_path=ephe_path`).
Doctrine: SR-VEDHA-RESIDENCE-SOURCE (surrogate ruling 2026-10-22), Phaladipika XXVI.3-8 / ND-NODE-VEDHA; root CLAUDE.md §N.8."""
from __future__ import annotations

import ast
import inspect

from pipeline.orchestrator.writers import ka_gochara_v5 as writer


def _phase():
    src = inspect.getsource(writer)
    return next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "_run_window_phase")


def _kw(call: ast.Call) -> dict:
    return {k.arg: ast.unparse(k.value) for k in call.keywords}


def _calls(phase, name):
    return [c for c in ast.walk(phase) if isinstance(c, ast.Call) and getattr(c.func, "attr", getattr(c.func, "id", "")) == name]


def test_w8_the_grain_bound_vedha_source_is_handed_this_substeps_position_probe():
    (call,) = _calls(_phase(), "for_grain")
    assert _kw(call).get("position_at") == "position_at", _kw(call)


def test_w9_the_in_build_verifier_is_handed_the_ephemeris_directory():
    (call,) = _calls(_phase(), "verify_window_semantics")
    assert _kw(call).get("ephe_path") == "ephe_path", _kw(call)
