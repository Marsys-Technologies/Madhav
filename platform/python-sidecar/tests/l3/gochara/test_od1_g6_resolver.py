"""SR-OD1 R8X review S-1 — the PRODUCTION G-6 resolver (`window_verifier.g6_resolver`, bound per grain by `verification_job`).

R8X made G-6 compulsory in the verifier's pinned plan (`g6_plan`) but shipped no resolver: every real certified generation's aggregate refused ("is None, not AGREED"). The verifier now
re-solves the plan's selected windows FROM SCRATCH — `window_cert_check.check_numbered(resolve=True)`, no builder certificate — and persists the evidence where the aggregate reads it
(the 1240 row's `runner_identity.g6_evidence`).

Claims — each has ONE oracle here and the single planted reversion that must make it fail (applied to a copy under the job folder; see result.json):
  G1  a certified generation's compulsory sample is re-solved by the verifier's own solver path and every selected window AGREES; the certificate plays no part   — revert: no production resolver (`_verify_class` passes the injected None through)
  G2  a window whose stored maximum is wrong, with a builder certificate that agrees with it, is a DISAGREEMENT at G-6 even when the certificate check accepted it    — revert: the adapter returns AGREED
  G3  a real certified generation's AGGREGATE passes with the production resolver wired (end to end: the entry point's `vj.run`, the persisted evidence, `generation_verdict`) — revert: as G1
  G4  an omitted or stale sample is refused by the aggregate: a resolver that covers nothing, evidence deleted from the rows, a population that grew after the run       — revert: the evidence check skips a missing window (covered by test_od1_r8x_aggregate T18c/T18d)
  G5  a production-resolver DISAGREEMENT blocks the class at the `g6_resample` stage and persists nothing for it                                                        — revert: as G2
  G6  a selected P1 (Form B, step-valued) window is re-solved from scratch from the verifier's OWN P1 derivation and reads AGREED; a stored value that is not the table's reads DISAGREEMENT; a P1 record
      with no P1 binding is a named refusal (None, unresolved) — never a raise that stage() would call DISAGREE                                                  — revert: `_checker_records` raises on the P1 rows again
Doctrine: §N.8 (a green comes from a detector that can read false: a re-solve that ran and agreed), §N.7.6 (a window the resolver cannot cover is None, never a pass), A10.1 B5 / PLAN_A10_1 §4
(G-6: the independent from-scratch re-solve of a deterministic 3 % + the five mixed-heaviest windows). The numbers are the S3 closed-form P4 world (`test_od1_s3_integration`): the max-min of two
tents, d* = 10/3 d, M = 5/6.
"""
from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

import pytest

from services.gochara_kernel import g6_plan
from services.gochara_kernel import window_cert_check as cc
from services.gochara_kernel import window_verifier as wv

from .test_a53_window_sweep import _restore_factor_registry  # noqa: F401  (autouse in the S3 suite: synthetic registry rows never outlive their test)
from .test_od1_s3_integration import GRAIN_P4, P4_MAX, ROWS, _d, _jup, _lie, _p4_records, _position, _sat, _solve, _verify

# G3-G5 (a real certified generation end to end, through `vj.run`, the persisted evidence and the aggregate) live in test_od1_r8x_aggregate.py: that suite holds the one-class world's
# census opt-out and the pinned-universe seam. This file is the part that needs no database.

# ── G1 / G2: the real builder's certificates, the verifier's own re-solve ─────────────────────────────────────────────────────────────────────

def _sel(draft):
    """The plan's selection over the ONE real window of the S3 world (forced in through the top-mixed rule: a window that carries a mixed piece, per its REAL stored certificate)."""
    grain = (GRAIN_P4["event_class"], GRAIN_P4["path_id"], GRAIN_P4["rule_version"])
    key = g6_plan.window_key("c", "g", *grain, "2010-01-01T00:00:00.000000Z", "2010-01-11T00:00:00.000000Z")
    mixed = g6_plan.mixed_pieces(draft.qualification())
    sel = g6_plan.Selection([{"key": key, "window_id": "w0", "grain": grain, "mixed": max(mixed, 1)}])
    assert key in sel.for_grain(grain)
    return grain, sel, dict(chart_id="c", generation="g", grain=GRAIN_P4, sel=sel)


def _stub_agreed(window):
    return SimpleNamespace(classification="AGREED", findings=(), inconclusive=())


def test_g1_the_verifiers_own_solver_path_resolves_the_selected_certified_window_without_the_certificate(monkeypatch):
    recs = _p4_records()
    (draft,) = _solve(recs)
    assert draft.solver_certificate is not None and draft.peak_instant == _d(0) + timedelta(hours=80)       # a real, numbered, certified window (closed form: d* = 80 h)
    grain, sel, kw = _sel(draft)
    inputs: dict = {}
    pos = _position({"jupiter": _jup, "saturn": _sat})
    assert _verify([draft], recs, ROWS("P4", "1.0.0"), pos, resolve_inputs=inputs)["status"] == "VERIFIED"
    assert set(inputs) == {"w0"}                                                                            # every NUMBERED window of the grain is registered, nothing else
    calls = []
    real = cc.check_numbered
    monkeypatch.setattr(wv._cc, "check_numbered", lambda **k: calls.append(k) or real(**k))
    ev = g6_plan.collect(resolver=wv.g6_resolver(inputs), **kw)
    assert ev["windows"][next(iter(sel.for_grain(grain)))]["result"] == "AGREED" and g6_plan.evidence_problems("t", ev, grain, sel) == []
    assert len(calls) == 1 and calls[0]["resolve"] is True and calls[0]["certificate"] is None              # from scratch: the certificate is not even passed
    # …and a builder certificate that is GARBAGE changes nothing: the re-solve is the verifier's alone (the certificate check would refuse this window at its schema)
    import dataclasses
    junk = dataclasses.replace(draft, solver_certificate={"schema": "nonsense"})
    inputs2: dict = {}
    _verify([junk], recs, ROWS("P4", "1.0.0"), pos, solver_check_fn=_stub_agreed, resolve_inputs=inputs2)
    ev2 = g6_plan.collect(resolver=wv.g6_resolver(inputs2), **kw)
    assert g6_plan.evidence_problems("t", ev2, grain, sel) == []


def test_g1_a_window_the_grain_did_not_verify_as_numbered_is_not_covered_never_a_pass():
    """No thunk for the window (blank, or never reached): the resolver answers None, which the plan records as unresolved and the aggregate refuses."""
    assert wv.g6_resolver({})({"window_id": "nope"}) is None


def test_g2_a_stored_maximum_the_certificate_agrees_with_but_the_sky_does_not_is_a_g6_disagreement_even_when_the_certificate_check_accepted_it():
    recs = _p4_records()
    (draft,) = _solve(recs)
    liar = _lie(draft, objective_value=P4_MAX - 1e-3, score=P4_MAX - 1e-3)       # stored maximum below the true one; the builder's certificate says the same
    grain, sel, kw = _sel(draft)
    inputs: dict = {}
    # the certificate check is told to accept (the case G-6 exists for): the window passes the semantic verification…
    report = _verify([liar], recs, ROWS("P4", "1.0.0"), _position({"jupiter": _jup, "saturn": _sat}), solver_check_fn=_stub_agreed, resolve_inputs=inputs)
    assert report["status"] == "VERIFIED"
    # …and the from-scratch re-solve refuses it, naming the defect: a DISAGREEMENT raises, so the verification job blocks the seal
    with pytest.raises(RuntimeError, match=r"G-6 from-scratch re-solve of window w0 DISAGREES.*(objective_exceeds_stored_maximum|peak_value_mismatch)"):
        g6_plan.collect(resolver=wv.g6_resolver(inputs), **kw)


# ── G6: a P1 Form-B window (review B-1) ──────────────────────────────────────────────────────────────────────────────────────────────────────

def _p1_g6_world(objective_value):
    """The P1c suite's Form-B world: Jupiter (benefic) DEBILITATED in Capricorn until it enters Aquarius on day 5 (ANSWERS.md §B.3: adverse 1.0 before, NEU favourable 0.125 after), a gain class —
    so the objective's maximum is 0.125 at the day-5 ingress. `objective_value` is what the stored 1240 provenance carries."""
    from .test_od1_p1c_operands_check import _Conn as P1Conn, _jupiter_world, _verify as p1_verify, _d as p1_d
    sky, _conn, stored = _jupiter_world()
    row = list(stored)
    row[11] = objective_value
    conn = P1Conn([tuple(row)], [("r1", "root1", "residence", "sign_span", "jupiter", None, p1_d(0), p1_d(10))], [("w", "r1")])
    inputs: dict = {}
    assert p1_verify(conn, sky, resolve_inputs=inputs, position_at=sky)["status"] == "VERIFIED"
    assert set(inputs) == {"w"}
    return inputs


def test_g6_a_selected_p1_form_b_window_is_re_solved_from_the_verifiers_own_p1_derivation_and_agrees():
    inputs = _p1_g6_world(0.125)
    out = wv.g6_resolver(inputs)({"window_id": "w"})
    assert out is not None and out.classification == "AGREED", out


def test_g6_a_p1_window_whose_stored_value_is_not_the_tables_is_a_g6_disagreement():
    inputs = _p1_g6_world(0.25)                                                           # the table's maximum is 0.125, not 0.25
    out = wv.g6_resolver(inputs)({"window_id": "w"})
    assert out is not None and out.classification == "DISAGREEMENT", out


def test_g6_a_p1_record_with_no_p1_binding_is_a_named_refusal_not_a_raise():
    inputs = _p1_g6_world(0.125)
    thunk = inputs["w"]
    inputs["w"] = lambda: thunk.func(*thunk.args, **{**thunk.keywords, "p1": None})       # the P1 rows are declared, but nothing here can derive them
    assert wv.g6_resolver(inputs)({"window_id": "w"}) is None                             # unresolved (the aggregate refuses "None, not AGREED"); never VerificationDisagrees
