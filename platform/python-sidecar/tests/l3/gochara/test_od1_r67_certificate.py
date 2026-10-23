"""SR-OD1 R67 — the solver CERTIFICATE, the verifier's check of it, the per-window budget, DISAGREEMENT vs INCONCLUSIVE, and the demotion of INCONCLUSIVE
windows to a named blank (rulings R-6, R-7 of SR-PLAN-REVIEW-RECONCILED; Fable B-2/B-3, GPT B8).

No database and no Swiss ephemeris: every world is analytic (a stub sky with a closed-form answer, the S1 harness's polynomial tents), built ONCE and handed
to BOTH sides — the builder as `window_solver.Problem`, the independent verifier as `window_solver_check` records — so the certificate is checked against the
sky and never against the builder's own output.

How a claim is tested (the S2 pattern). Each claim has ONE oracle taking the module under test and asserting what the claim says, and ONE planted reversion
`(module, old, new)` — a single textual change to that module's source. `test_oracle_passes_on_the_real_code` runs every oracle on the real modules;
`test_the_single_planted_reversion_fails_the_oracle` loads a COPY of the source with that one change (it must match exactly once) and requires the SAME oracle
to fail. A claim whose reversion does not fail its oracle is a claim nothing measures (CLAUDE.md §N.8).

Claims (the cited rule is the ruling or classical definition the oracle is built from):

  K-1  the certificate states the evaluation count and the declared PER-WINDOW budget                                   R-6/R-7
  K-2  a solved certificate's cells tile every mixed piece (the verifier needs a complete partition to seed from)       R-7
  K-3  a budget-exhausted blank's certificate lists its OPEN cells                                                      R-6
  K-4  the certificate separates the geometry from the values: same sky, other values ⇒ same geometry digest (R-10)     R-7/R-10
  V-1  a cell's claimed bound the sky contradicts is a DISAGREEMENT                                                     R-7 (K12: own enclosure)
  V-2  a certificate that disagrees with the stored value is a DISAGREEMENT                                             R-7
  V-3  a certificate that assumes a weaker tie than the policy's is a DISAGREEMENT                                      R-7 (limits assumed)
  V-4  the G-6 sample re-solves from scratch and ignores the certificate                                                R-7
  V-5  a failed certificate check is re-solved from scratch and THAT outcome stands                                     R-7
  V-6  the verifier's search starts from the certificate's partition                                                    R-7
  V-7  a blank declaring a per-window budget below the policy's is a DISAGREEMENT (no easy window blanked cheaply)      R-6/GPT B8
  V-8  a blank showing fewer evaluations than it declares is a DISAGREEMENT                                             R-6
  V-9  a blank with no open cell the verifier cannot discharge is a DISAGREEMENT                                        R-6
  C-1  the verifier's own budget running out is INCONCLUSIVE, not a refusal                                             R-6
  C-2  an UNVERIFIED reason that is not a named INCONCLUSIVE one blocks (DISAGREEMENT)                                  R-6
  C-3  INCONCLUSIVE is derived from the reasons that make it so (end to end through `check_numbered`)                   R-6
  C-4  a bound that cannot be pushed under M + tol, with no point above it, is INCONCLUSIVE; a real exceedance DISAGREES   R-6 (SR-TR2-DEFECT-B)
  G-1  populations are matched AFTER classification (stored numbered = reproduced + demoted)                            R-6
  G-2  a demoted window is attested as a BLANK under its named reason                                                   R-6
  G-3  the demoted share is capped at 0.5 % of all windows; above it the verdict FAILS                                  R-6
  G-4  only the named INCONCLUSIVE reasons may demote                                                                   R-6
  W-1  a DISAGREEMENT from the solver check raises in the verifier (the seal is blocked, always)                        R-6
  W-2  an INCONCLUSIVE window is reproduced-as-blank, never numeric                                                     R-6
  W-3  the certificate rides in the qualification record without disturbing the provenance comparison                   R-7
  S-1  the sweep attaches the solver's certificate to the window it solved                                              R-7
  V-10 a seeded refutation an evaluated point witnesses stands as a DISAGREEMENT (not re-solved, not softened)          R-6 (lane review N-1)
  V-11 the fallback re-solve is from scratch (the deciding run used no certificate partition)                           R-7 (lane review N-4)
  D-1  the grain attestation NAMES the demoted windows: sorted {window_id, reason}                                      R-6 (lane review B-1 a)
  D-2  the gate refuses a demoted-window list that disagrees with the attested counts                                   R-6 (B-1 b)
  D-3  the gate refuses a demoted window that is not a stored NUMBERED window of the grain                              R-6 (B-1 b)
  D-4  a demoted window is served as the named blank: every number null, valence unqualified, reason = the attested     R-6 / §N.7.6 (B-1 c)
  D-5  the demotions are read back from the VERIFIED grains' attestations, under the numerical policy only             R-6 (B-1 c)
  (D-6, the wiring of the blank into `read_v5` — the finished window list passes through it — is in test_w1_serving_reader.py, on the real database)
plus the end-to-end fixture (first window exhausts, the next window is easy), guards for the verifier's independence, and the literals the two sides restate.
"""
from __future__ import annotations

import ast
import copy
import json
import struct
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.gochara_kernel import numerical_window_gate as nwg
from services.gochara_kernel import serving_reader as rd
from services.gochara_kernel import window_cert_check as cc
from services.gochara_kernel import window_solver as sol
from services.gochara_kernel import window_solver_check as chk
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel import window_verifier as wv

from .od1_solver_harness import crest_member, member, poly_tent
from .test_a53_window_sweep import _d, _draft, _rec, _rows_declared

T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)
PKG = "services.gochara_kernel"


def at(seconds: float = 0.0) -> datetime:
    return T0 + timedelta(seconds=seconds)


# ── one analytic hump world, handed to both sides ────────────────────────────────────────────────────────────────────────────────

ORB, SIGMA, A0, B0 = 1.0, 0.25, 0.95, 0.10


class Hump:
    """A rising linear tent A plus a falling quadratic tent B (plan C-S1 / spec O-SM-4): F(τ) = 2 − (a0+b0) + lift + σ·τ(1−τ) on τ = t/T ∈ [0,1], maximum
    M = 2 − a0 − b0 + lift + σ/4 at t* = T/2 — closed form, no search needed to know the answer. `h4=False` withholds the builder's kinematic bound (the limb-window case:
    first-order only, which is where the budget decides). `scale` multiplies every record's value (a different doctrine VALUE, the same geometry)."""

    def __init__(self, T=2.0e5, *, h4=True, scale=1.0):
        self.T, self.scale = T, scale
        v, k = SIGMA * ORB / T, SIGMA * ORB / (T * T)
        steps = () if scale == 1.0 else (sol.constant_step(scale),)
        sup = ((0.0, T),)
        self.members = (member("A", "rA", sup, poly_tent(ORB, A0 * ORB, -v, 0.0, h4=h4), steps=steps),
                        member("B", "rB", sup, poly_tent(ORB, B0 * ORB, 0.0, k, h4=h4), steps=steps))
        self.M = (2.0 - A0 - B0 + SIGMA / 4.0) * scale
        self.t_star = T / 2.0
        self._lam = {"A": lambda t: 100.0 + A0 * ORB - v * t, "B": lambda t: 200.0 + B0 * ORB + k * t * t}

    def problem(self):
        return sol.Problem(0.0, self.T, sol.OBJECTIVE_SUM, self.members)

    def pos(self, body, d):
        return self._lam[body]((d - T0).total_seconds()) % 360.0

    def records(self, lo=0.0):
        sup = ((at(lo), at(lo + self.T)),)
        return [chk.CheckRecord("A", "rA", "A", sup, constant=self.scale, tent=chk.TentFactor("A", 100.0, ORB)),
                chk.CheckRecord("B", "rB", "B", sup, constant=self.scale, tent=chk.TentFactor("B", 200.0, ORB))]

    def solve(self, **kw):
        res = sol.solve(self.problem(), **kw)
        return res, sol.stored_certificate(res, objective=sol.OBJECTIVE_SUM, t0_iso=T0.isoformat())

    def stored(self, res):
        return chk.StoredWindow(at(res.instant), res.value)

    def check(self, m_cc, cert, res=None, **kw):
        res = res or self.solve()[0]
        return m_cc.check_numbered(lo=at(0), hi=at(self.T), records=self.records(), objective=chk.OBJ_SUM, stored=self.stored(res),
                                   position_at=self.pos, certificate=cert, **kw)

    def check_blank(self, m_cc, cert, **kw):
        return m_cc.check_budget_blank(lo=at(0), hi=at(self.T), records=self.records(), objective=chk.OBJ_SUM, position_at=self.pos,
                                       certificate=cert, **kw)


_CACHE: dict = {}


def solved_hump():
    """The solved hump world (T = 2e5 s, H4 supplied) and its stored certificate — solved once."""
    if "solved" not in _CACHE:
        h = Hump()
        res, cert = h.solve()
        assert res.status == sol.SOLVED and res.value == pytest.approx(h.M, abs=1e-9)
        _CACHE["solved"] = (h, res, cert)
    h, res, cert = _CACHE["solved"]
    return h, res, copy.deepcopy(cert)


def exhausted_hump():
    """A genuinely hard window: no H4 bound, so only the first-order enclosure; the REAL per-window budget (500,000) runs out. Its blank certificate is the partial tree."""
    if "hard" not in _CACHE:
        h = Hump(h4=False)
        res, cert = h.solve()
        assert res.status == sol.BLANK and res.reason == sol.REASON_BUDGET and res.evals == sol.MAX_EVALS_WINDOW
        _CACHE["hard"] = (h, res, cert)
    h, res, cert = _CACHE["hard"]
    return h, res, copy.deepcopy(cert)


# ── the claims ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────

CLAIMS: dict = {}


def claim(cid, module, old, new):
    def deco(fn):
        assert cid not in CLAIMS
        CLAIMS[cid] = (fn, module, old, new)
        return fn
    return deco


def M(mods, name):
    return mods[name]


# K-1 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("K-1", "window_solver", '"evals": ctx.evals, "max_evals": ctx.max_evals,', '"evals": 0, "max_evals": ctx.max_evals,')
def oracle_k1(mods):
    """R-6/R-7: the certificate states how many ephemeris calls the answer cost and the per-WINDOW budget it ran under (`budget_scope: window`) — the diagnostics
    MAX_EVALS tuning needs and what a budget blank's justification is checked against."""
    s = M(mods, "window_solver")
    h = Hump()
    res = s.solve(h.problem())
    cert = s.stored_certificate(res, objective=s.OBJECTIVE_SUM, t0_iso=T0.isoformat())
    assert res.evals > 100 and cert["evals"] == res.evals
    assert cert["max_evals"] == s.MAX_EVALS_WINDOW == 500_000 and cert["budget_scope"] == "window"


# K-2 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("K-2", "window_solver", 'tr.cells.append(["dead", l, r, u])', "pass")
def oracle_k2(mods):
    """R-7: the cells of a solved certificate tile every piece of its geometry: between the cuts nothing is left unaccounted for (a hole would be an unproved
    stretch the verifier must search blind). The tiling is computed here from the certificate's own `geometry.pieces`, independently of the solver."""
    s = M(mods, "window_solver")
    h = Hump()
    res = s.solve(h.problem())
    cert = s.stored_certificate(res, objective=s.OBJECTIVE_SUM, t0_iso=T0.isoformat())
    assert not cert["truncated"] and cert["outcome"] == "solved"
    for a, b, kind in cert["geometry"]["pieces"]:
        covered = sorted((c[1], c[2]) for c in cert["cells"] if c[2] > a and c[1] < b or (c[1] == a and c[2] == b))
        assert covered, (a, b, kind)
        edge = a
        for l, r in covered:
            assert l <= edge + 1e-6, f"a hole in [{a}, {b}] at {edge}..{l}"
            edge = max(edge, r)
        assert edge >= b - 1e-6, f"[{a}, {b}] is covered only to {edge}"


# K-3 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("K-3", "window_solver", "heapq.nsmallest(MAX_OPEN_CELLS, tr.heap, key=lambda e: (e[0], e[1]))", "[]")
def oracle_k3(mods):
    """R-6: a budget-exhausted blank carries the partial tree AND its open cells (the work that was left); the verifier then confirms the exhaustion was real. Here the REAL
    500,000-call budget of a first-order-only window runs out in pass 1, the live heap is the open set, and the verifier agrees the blank is borne out."""
    s = M(mods, "window_solver")
    h = Hump(h4=False)
    res = s.solve(h.problem())
    cert = s.stored_certificate(res, objective=s.OBJECTIVE_SUM, t0_iso=T0.isoformat())
    assert res.reason == s.REASON_BUDGET and cert["outcome"] == "blank" and cert["evals"] == 500_000
    assert len(cert["open"]) == s.MAX_OPEN_CELLS and cert["open_total"] > 10 * s.MAX_OPEN_CELLS       # the live heap: hundreds of thousands of cells, the widest bounds listed
    rep = h.check_blank(cc, cert)
    assert rep.classification == cc.AGREED, (rep.findings, rep.inconclusive)


# K-4 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("K-4", "window_solver", 'blob = json.dumps(geometry, sort_keys=True', 'blob = json.dumps([geometry, tree["value"]], sort_keys=True')
def oracle_k4(mods):
    """R-7/R-10: the cuts and piece kinds depend on the tents and step boundaries only, so a re-evaluation under other doctrine VALUES (every record's value × 0.8) reuses
    them: the geometry digest is equal, and the VALUE claims (the maximum, the cell bounds) are not."""
    s = M(mods, "window_solver")
    a, b = Hump(scale=1.0), Hump(scale=0.8)
    ca = s.stored_certificate(s.solve(a.problem()), objective=s.OBJECTIVE_SUM, t0_iso=T0.isoformat())
    cb = s.stored_certificate(s.solve(b.problem()), objective=s.OBJECTIVE_SUM, t0_iso=T0.isoformat())
    assert ca["geometry"] == cb["geometry"] and ca["geometry_digest"] == cb["geometry_digest"]
    assert cb["value"] == pytest.approx(0.8 * ca["value"], abs=1e-9) and cb["value"] != ca["value"]


# V-1 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("V-1", "window_cert_check", 'if v is not None and v > u + _tol("bound", u):', "if False:")
def oracle_v1(mods):
    """R-7 / K12: the verifier does not take a cell's claimed bound on trust: it evaluates the sky at the cell's ends and middle. A `dead` cell claiming the objective is at
    most 0.5 where the (analytic) objective is 0.95 is a DISAGREEMENT, whatever the maximum."""
    c = M(mods, "window_cert_check")
    h, res, cert = solved_hump()
    assert h.check(c, cert, res).classification == c.AGREED
    bad = copy.deepcopy(cert)
    first = next(x for x in bad["cells"] if x[0] == "dead")
    first[3] = 0.5
    rep = h.check(c, bad, res)
    assert rep.classification == c.DISAGREEMENT and c_codes(rep) == ["certificate_bound_violated"], (rep.classification, rep.findings)


def c_codes(rep):
    return [code for code, _ in rep.findings]


# V-2 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("V-2", "window_cert_check", 'abs(certificate["value"] - stored.objective_value) > _tol("value", stored.objective_value)', "False")
def oracle_v2(mods):
    """R-7: the certificate must be the certificate of THIS window: its maximum is the stored objective value (float4 round trip, 1e-6). A certificate whose maximum is 1e-3
    off the stored one — another window's, or a tampered row — is a DISAGREEMENT."""
    c = M(mods, "window_cert_check")
    h, res, cert = solved_hump()
    assert h.check(c, cert, res).classification == c.AGREED
    bad = copy.deepcopy(cert)
    bad["value"] = cert["value"] - 1e-3
    rep = h.check(c, bad, res)
    assert rep.classification == c.DISAGREEMENT and "certificate_disagrees_with_stored_window" in c_codes(rep), (rep.classification, rep.findings)


# T-1 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("T-1", "window_cert_check", "return max(chk.VALUE_TOL, chk._f4_tol(x))", "return chk.VALUE_TOL")
def oracle_t1(mods):
    """R-1 / GPT B2 (float4 class), adopted by the certificate check at the merge-back (R67 lane review N-5): the stored objective value is a REAL (float4), so its distance from the
    certificate's double maximum is half a float4 spacing at the value's magnitude — 1.9e-6 for a sum of 32 or more, which a fixed 1e-6 refuses. 33 roots each at 0.97 sum to 32.01;
    float4(32.01) is 1.68e-6 below it. The window is correct, its certificate is correct, the stored REAL is the correct rounding: it is AGREED (not a DISAGREEMENT
    `certificate_disagrees_with_stored_window`). The same call with a stored value 1e-3 off still disagrees (the interval widens the tolerance, it does not remove it)."""
    c = M(mods, "window_cert_check")
    T, per_root = 2.0e5, 0.97
    sup = ((0.0, T),)
    res = sol.solve(sol.Problem(0.0, T, sol.OBJECTIVE_SUM, tuple(member(f"c{i}", f"r{i}", sup, steps=(sol.constant_step(per_root),)) for i in range(33))))
    assert res.status == sol.SOLVED and res.value == pytest.approx(32.01, abs=1e-9)
    stored_real = struct.unpack("f", struct.pack("f", res.value))[0]
    assert 1.2e-6 < abs(stored_real - res.value) < 1.9e-6, "the world must sit between the fixed tolerance and half a float4 spacing"
    cert = sol.stored_certificate(res, objective=sol.OBJECTIVE_SUM, t0_iso=T0.isoformat())
    recs = [chk.CheckRecord(f"c{i}", f"r{i}", f"B{i}", ((at(0), at(T)),), constant=per_root) for i in range(33)]

    def check(value):
        return c.check_numbered(lo=at(0), hi=at(T), records=recs, objective=chk.OBJ_SUM, stored=chk.StoredWindow(at(res.instant), value),
                                position_at=lambda body, d: 0.0, certificate=cert)
    rep = check(stored_real)
    assert rep.classification == c.AGREED, (rep.classification, rep.findings)
    off = check(stored_real - 1e-3)
    assert off.classification == c.DISAGREEMENT, off.classification


# V-3 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("V-3", "window_cert_check", 'lim["TIE"] != OWN_TIE or lim["QUANT"] != OWN_QUANT', 'lim["QUANT"] != OWN_QUANT')
def oracle_v3(mods):
    """R-7 (limits assumed): the certificate records the limits it assumed; the frozen tie rule is 1e-9 (N-11). A certificate that assumed a 1e-6 tie — which would call two
    distinct maxima one — is refused outright."""
    c = M(mods, "window_cert_check")
    h, res, cert = solved_hump()
    cert["limits"]["TIE"] = 1e-6
    rep = h.check(c, cert, res)
    assert rep.classification == c.DISAGREEMENT and "certificate_limits_not_the_policy" in c_codes(rep), (rep.classification, rep.findings)


# V-4 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("V-4", "window_cert_check", "    if resolve:\n        eng, rep = run(None)", "    if False:\n        eng, rep = run(None)")
def oracle_v4(mods):
    """R-7 (G-6): the sampled window is re-solved from scratch, the certificate unused — so it still verifies with NO certificate at all (None), while the ordinary path with
    no certificate is a DISAGREEMENT (a numbered window must carry one)."""
    c = M(mods, "window_cert_check")
    h, res, _cert = solved_hump()
    sampled = h.check(c, None, res, resolve=True)
    assert sampled.classification == c.AGREED and sampled.resolved and not sampled.used_certificate, (sampled.findings,)
    plain = h.check(c, None, res)
    assert plain.classification == c.DISAGREEMENT and "certificate_schema_invalid" in c_codes(plain)


# V-5 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("V-5", "window_cert_check", "    if rep.status == chk.VERIFIED:\n        return _from_inner(rep, used_certificate=True, fell_back=False",
       "    if True:\n        return _from_inner(rep, used_certificate=True, fell_back=False")
def oracle_v5(mods):
    """R-7: the verifier re-solves ONLY when the certificate-seeded check does not verify. A sound certificate is NOT re-solved; the same window with a verifier budget of 300
    evaluations (the seeded check cannot finish: UNVERIFIED) IS re-solved from scratch, and that outcome — here the same budget running out — stands, saying it re-solved."""
    c = M(mods, "window_cert_check")
    h, res, cert = solved_hump()
    ok = h.check(c, cert, res)
    assert ok.classification == c.AGREED and ok.used_certificate and not ok.fell_back
    rep = h.check(c, cert, res, max_evals=300)
    assert rep.fell_back and rep.classification == c.INCONCLUSIVE, (rep.classification, rep.fell_back, rep.codes())


# V-10 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _wrong_max(h, res, cert):
    """A stored maximum 1e-3 below the true one, the certificate agreeing with the stored row on the wrong number (so only the SKY can refute it)."""
    wrong = chk.StoredWindow(at(res.instant), res.value - 1e-3)
    cert["value"] = res.value - 1e-3
    return wrong, cert


@claim("V-10", "window_cert_check", "    if rep.status == chk.REFUTED and any(f.code in WITNESSED_REFUTATIONS for f in rep.findings):", "    if False:")
def oracle_v10(mods):
    """R-6 (lane review N-1): a refutation the verifier's own EVALUATION witnessed — here the objective reaches a point above a stored maximum 1e-3 too low — is a DISAGREEMENT as
    it stands. It is not re-solved: a from-scratch run that merely exhausted its budget would turn a proven DISAGREEMENT into an INCONCLUSIVE window the gate demotes."""
    c = M(mods, "window_cert_check")
    h, res, cert = solved_hump()
    wrong, cert = _wrong_max(h, res, cert)
    rep = c.check_numbered(lo=at(0), hi=at(h.T), records=h.records(), objective=chk.OBJ_SUM, stored=wrong, position_at=h.pos, certificate=cert)
    assert rep.classification == c.DISAGREEMENT and "objective_exceeds_stored_maximum" in c_codes(rep), (rep.classification, rep.codes())
    assert not rep.fell_back and rep.used_certificate, "a witnessed refutation was re-solved"


# V-11 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("V-11", "window_cert_check", "    eng2, rep2 = run(None)", "    eng2, rep2 = run(cells)")
def oracle_v11(mods):
    """R-7 (lane review N-4): 'solve from scratch' means the re-solve starts from the whole piece, not from the certificate's partition. The seeded check of the solved hump
    starts from its certificate's cells (`seeds` > 0); when it cannot finish and the window is re-solved, the deciding run used NO seed."""
    c = M(mods, "window_cert_check")
    h, res, cert = solved_hump()
    assert h.check(c, cert, res).seeds > 5
    rep = h.check(c, cert, res, max_evals=300)
    assert rep.fell_back and rep.seeds == 0, (rep.fell_back, rep.seeds)


# V-6 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("V-6", "window_cert_check", "        if not self.cells:\n            return super()._seeds(pc)", "        if True:\n            return super()._seeds(pc)")
def oracle_v6(mods):
    """R-7: the verifier's search over a mixed piece starts from the certificate's partition (one sub-interval per gap between certificate cell edges), not from the whole piece."""
    c = M(mods, "window_cert_check")
    h, res, cert = solved_hump()
    rep = h.check(c, cert, res)
    assert rep.classification == c.AGREED and rep.seeds >= len(cert["cells"]) // 2 > 5, (rep.seeds, len(cert["cells"]))
    assert h.check(c, cert, res, resolve=True).seeds == 0


# V-7 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("V-7", "window_cert_check", 'if certificate["max_evals"] != POLICY_MAX_EVALS_WINDOW:', "if False:")
def oracle_v7(mods):
    """R-6 / GPT B8: a blank is justified by its certificate, not by the reason string. A builder that declares a per-window budget of 50 and 'exhausts' it blanks an easy window
    cheaply; the verifier's own literal of the policy budget (500,000) refuses it."""
    c = M(mods, "window_cert_check")
    h = Hump(h4=False)
    res, cert = h.solve(max_evals=50)
    assert res.reason == sol.REASON_BUDGET and cert["max_evals"] == 50 and cert["evals"] == 50
    rep = h.check_blank(c, cert)
    assert rep.classification == c.DISAGREEMENT and "budget_declared_below_policy" in c_codes(rep), (rep.classification, rep.findings)


# V-8 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("V-8", "window_cert_check", 'if certificate["evals"] < certificate["max_evals"]:', "if False:")
def oracle_v8(mods):
    """R-6: 'the evaluation count reached the declared budget'. The genuine exhausted certificate is borne out; the same certificate claiming 10,000 evaluations, or one evaluation
    short of the declared budget, is a DISAGREEMENT."""
    c = M(mods, "window_cert_check")
    h, _res, cert = exhausted_hump()
    assert h.check_blank(c, cert).classification == c.AGREED
    for short in (10_000, cert["max_evals"] - 1):                    # far below, and one evaluation short of the declared budget (lane review N-2)
        cert["evals"] = short
        rep = h.check_blank(c, cert)
        assert rep.classification == c.DISAGREEMENT and "budget_blank_evals_below_declared" in c_codes(rep), (short, rep.classification, rep.findings)


# V-9 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("V-9", "window_cert_check", "    if not alive:\n", "    if False:\n")
def oracle_v9(mods):
    """R-6: an exhaustion is real only if work was left. The genuine certificate's open cells straddle the maximum (the verifier's own enclosure cannot discharge them); the same
    certificate whose only open cell is a stretch near t = 0, where the objective is 0.95 against a maximum of 1.0125, has nothing left to do: the builder stopped with the work done."""
    c = M(mods, "window_cert_check")
    h, _res, cert = exhausted_hump()
    assert h.check_blank(c, cert).classification == c.AGREED
    cert["open"] = [[0.0, 100.0]]
    rep = h.check_blank(c, cert)
    assert rep.classification == c.DISAGREEMENT and "budget_blank_without_open_cell" in c_codes(rep), (rep.classification, rep.findings)


# C-1 / C-2 / C-3 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _unverified(*reasons):
    return chk.CheckReport(chk.UNVERIFIED, (), tuple((r, "") for r in reasons), 0, {})


@claim("C-1", "window_cert_check", "frozenset({chk.U_BUDGET, ", "frozenset({")
def oracle_c1(mods):
    """R-6: the verifier's own budget running out (`verifier_budget_exhausted`) — and R-1/R-3's `tie_ambiguous` / `tie_isolation_unresolved` — are INCONCLUSIVE: demoted at seal,
    never a refusal."""
    c = M(mods, "window_cert_check")
    for reason in ("verifier_budget_exhausted", "tie_ambiguous", "tie_isolation_unresolved"):
        assert c.classify(_unverified(reason)) == c.INCONCLUSIVE, reason
    assert c.classify(chk.CheckReport(chk.VERIFIED, (), (), 0, {})) == c.AGREED


@claim("C-2", "window_cert_check", "or any(r not in INCONCLUSIVE_REASONS for r, _d in report.unverified)", "")
def oracle_c2(mods):
    """R-6: only the NAMED reasons are demoted. An UNVERIFIED window for any other reason (here the tie scan reaching no extremum, `tie_scan_inconclusive`) blocks the seal, and a
    window with a refutation is a DISAGREEMENT even when it is also inconclusive. (`solver_certificate_incomplete` was the example here until SR-TR2-DEFECT-B: claim C-4.)"""
    c = M(mods, "window_cert_check")
    assert c.classify(_unverified(chk.U_TIE)) == c.DISAGREEMENT
    assert c.classify(_unverified("verifier_budget_exhausted", chk.U_TIE)) == c.DISAGREEMENT
    refuted = chk.CheckReport(chk.REFUTED, (chk.Finding(chk.F_ABOVE, "x"),), (("verifier_budget_exhausted", ""),), 0, {})
    assert c.classify(refuted) == c.DISAGREEMENT


@claim("C-3", "window_cert_check", "    inconclusive = [(r, d) for r, d in inner.unverified if r in INCONCLUSIVE_REASONS] if cls == INCONCLUSIVE else []",
       "    inconclusive = []")
def oracle_c3(mods):
    """R-6 end to end: the verifier given a budget it cannot finish on (300 evaluations for a window that needs thousands) returns INCONCLUSIVE naming
    `verifier_budget_exhausted` — not AGREED, not a DISAGREEMENT."""
    c = M(mods, "window_cert_check")
    h, res, cert = solved_hump()
    rep = h.check(c, cert, res, max_evals=300)
    assert rep.classification == c.INCONCLUSIVE and [r for r, _ in rep.inconclusive] == ["verifier_budget_exhausted"] and not rep.findings, (rep.classification, rep.codes())


# C-4 (SR-TR2-DEFECT-B) ─────────────────────────────────────────────────────────────────────────────────────────────────────────────

class RoundingEdgeWorld:
    """The shape the trial found on a real window (foreign_settlement/P3, two bodies): a fast body A climbing to its crest (tent = 1) at `t_c` while a slow body B falls, so the
    sum F = tentA + tentB peaks AT the crest, F* = 1 + tentB(t_c) = 2 - B0 (orb 1, so a tent is 1 - |offset|). The stored maximum is a float4: `M4`, with F* = M4 + `err_of_half` x half a
    float4 spacing (2^-24 in [1, 2)). The verifier's bound is the sum of each body's larger end value, which exceeds F by B's fall across a leaf (VEL_B x width); the search stops at
    MIN_WIDTH_S = 1 ms (VEL_B x 1 ms = 1.2e-8 here, against a margin to M4 + tol of (1 - err_of_half) x 2^-24 + 1e-10). With `err_of_half` = 0.98 the margin is ~1.2e-9: every point is at or
    under M4 + tol, and the bound cannot show it."""
    ORB = 1.0
    VEL_A, VEL_B = 1.8e-4, 1.157e-5          # deg/s: Mercury-like, Sun-like (the trial's two bodies)
    HALF_F4 = 2.0 ** -24                     # half a float4 spacing in [1, 2)

    def __init__(self, err_of_half: float, *, t_c: float = 3000.0):
        import struct
        self.t_c = t_c
        self.M4 = struct.unpack("f", struct.pack("f", 1.76))[0]
        self.f_star = self.M4 + err_of_half * self.HALF_F4
        self.b0 = 2.0 - self.f_star                 # B's offset (deg) at the crest: tentB = 1 - b0

    def pos(self, body, d):
        t = (d - T0).total_seconds()
        return (100.0 + self.VEL_A * (t - self.t_c)) % 360.0 if body == "A" else (200.0 + self.b0 + self.VEL_B * (t - self.t_c)) % 360.0

    def records(self):
        sup = ((at(0.0), at(2 * self.t_c)),)
        return [chk.CheckRecord("A", "rA", "A", sup, constant=1.0, tent=chk.TentFactor("A", 100.0, self.ORB)),
                chk.CheckRecord("B", "rB", "B", sup, constant=1.0, tent=chk.TentFactor("B", 200.0, self.ORB))]

    def classify(self, m_cc, stored_value):
        return m_cc.check_numbered(lo=at(0), hi=at(2 * self.t_c), records=self.records(), objective=chk.OBJ_SUM,
                                   stored=chk.StoredWindow(at(self.t_c), stored_value), position_at=self.pos, certificate=None, resolve=True)


@claim("C-4", "window_cert_check", "chk.U_BUDGET, chk.U_CERT, ", "chk.U_BUDGET, ")
def oracle_c4(mods):
    """SR-TR2-DEFECT-B, both directions. (i) A stored float4 whose rounding error is 98 % of its limit leaves the exact maximum 1.2e-9 under M + tol; the verifier's cross-body bound
    cannot show that at its 1 ms floor, and no point it evaluates is above the threshold — so the window is INCONCLUSIVE naming `solver_certificate_incomplete` (demoted to the named blank), with no
    finding: the sky does not contradict the number. (ii) The same world with the stored maximum one float4 spacing too low is a real exceedance: DISAGREEMENT, whatever else is open."""
    c = M(mods, "window_cert_check")
    w = RoundingEdgeWorld(0.98)
    assert abs(w.f_star - w.M4) < chk._f4_tol(w.M4) and chk._f4_tol(w.M4) - (w.f_star - w.M4) < 2e-9      # the premise: the margin to the threshold is ~1.2e-9, a true maximum under it
    rep = w.classify(c, w.M4)
    assert rep.classification == c.INCONCLUSIVE and [r for r, _ in rep.inconclusive] == [chk.U_CERT] and not rep.findings, (rep.classification, rep.codes())
    low = w.classify(c, w.M4 - 2.0 ** -23)                 # one float4 spacing below: F* - stored = 1.98 half-spacings, outside the tolerance
    assert low.classification == c.DISAGREEMENT and low.findings, (low.classification, low.codes())


# G-1 .. G-4: the gate, over a stored census and a re-derivation report ───────────────────────────────────────────────────────────

def _census(numbered=10, blank=None, valence=None, no_score=0, windows=None):
    blank = {"value_mapping_undeclared": 2} if blank is None else blank
    return {"windows": numbered + sum(blank.values()) if windows is None else windows, "numbered": numbered, "numbered_without_score": no_score,
            "valence": {"favourable": numbered} if valence is None else valence, "blank": blank, "problems": []}


def _report(numeric, windows, demoted=(), prefix="w"):
    return {"policy_version": nwg.POLICY_QUALIFICATION, "status": "VERIFIED", "unverified_windows": [], "fully_reproduced": windows, "numeric_reproduced": numeric,
            "dynamic_enabled": True,       # S3: the gate refuses a re-derivation that did not run under the solver table
            "inconclusive_windows": [{"window": f"2030-01-0{i + 1}T00:00:00+00:00", "window_id": f"{prefix}-{i}", "reason": r, "stored_numbered": True, "valence": "favourable",
                                      "had_score": True} for i, r in enumerate(demoted)]}


def _attest(m, census, report):
    m.census = lambda *a, **k: census
    return m.grain_attestation(None, chart_id="c", generation="g", event_class="marriage", path_id="P3", rule_version="1.0.0", report=report,
                               policy=m.POLICY_QUALIFICATION)


@claim("G-1", "numerical_window_gate", 'if report.get("numeric_reproduced", 0) + sum(d["demoted"].values()) != c["numbered"]:',
       'if report.get("numeric_reproduced", 0) != c["numbered"]:')
def oracle_g1(mods):
    """R-6: the gate matches populations AFTER classification. 10 stored numbered windows, 9 reproduced numerically and 1 demoted: attested. The same census with the demotion
    missing from the report (9 + 0 ≠ 10) — a number nobody reproduced and nobody classified — is refused."""
    m = M(mods, "numerical_window_gate")
    att = _attest(m, _census(10), _report(9, 12, ("verifier_budget_exhausted",)))
    assert att["status"] == m.PASSED and att["stored_numbered"] == 10 and att["numbered"] == 9
    with pytest.raises(m.NumericalGateDisagrees, match="reproduced 9 numbered"):
        _attest(m, _census(10), _report(9, 12))


@claim("G-2", "numerical_window_gate", 'blank[r] = blank.get(r, 0) + k', "pass")
def oracle_g2(mods):
    """R-6: the demoted window is attested as a BLANK under its named reason (disclosed in the honest nulls, counted by reason), not left in the numbered population."""
    m = M(mods, "numerical_window_gate")
    att = _attest(m, _census(10), _report(8, 12, ("verifier_budget_exhausted", "tie_ambiguous")))
    assert att["numbered"] == 8 and att["demoted"] == {"tie_ambiguous": 1, "verifier_budget_exhausted": 1}
    assert att["blank"] == {"tie_ambiguous": 1, "value_mapping_undeclared": 2, "verifier_budget_exhausted": 1}
    assert att["valence"] == {"favourable": 8}


class _Conn:
    """The two reads `generation_verdict` makes through `_rows` (pins; verification rows), answered from the test's own attestations."""

    def __init__(self, pins, rows):
        self.pins, self.rows = pins, rows


def _verdict(m, windows_per_grain, demoted_per_grain, numbered_ids=None, tamper=None):
    """`generation_verdict` over grains of `windows_per_grain` numbered windows each, `demoted_per_grain` of them demoted (a census, an attestation and a verification row per grain)."""
    grains = [("marriage", f"P{i + 1}", "1.0.0") for i in range(len(windows_per_grain))]
    census = {g: _census(w) for g, w in zip(grains, windows_per_grain)}
    runner = {}
    for g, w, dem in zip(grains, windows_per_grain, demoted_per_grain):
        census[g] = _census(w, blank={})
        report = _report(w - dem, w, ("verifier_budget_exhausted",) * dem, prefix=g[1])
        runner[g] = m.runner_with_attestation({}, _attest(m, census[g], report))
    if tamper is not None:
        tamper(runner)
    sql_pins = [(c, p, v) for c, p, v in grains]
    sql_ver = [(c, p, v, "VERIFIED", m.POLICY_QUALIFICATION, windows_per_grain[i], runner[(c, p, v)]) for i, (c, p, v) in enumerate(grains)]

    def rows(conn, sql, params=()):
        if "SELECT window_id::text" in sql:                      # the grain's stored numbered windows: `<path>-0 … <path>-(w-1)`
            path = params[3]
            return [(f"{path}-{i}",) for i in range(windows_per_grain[int(path[1:]) - 1])] if numbered_ids is None else numbered_ids(path)
        return sql_pins if "search_path_pin" in sql else sql_ver
    m._rows = rows
    m.census = lambda conn, chart, gen, cls, path, ver: census[(cls, path, ver)]
    from services.gochara_kernel import result_policy as rp
    saved = rp.manifest_vector
    rp.manifest_vector = lambda conn, chart, gen: {"result_policy": m.POLICY_QUALIFICATION, "qualification_table": m.table_binding()}
    try:
        return m.generation_verdict(None, "c", "g", classes=("marriage",))      # the subset verdict (R8): the shard/epoch checks are not what this tallies
    finally:
        rp.manifest_vector = saved


@claim("G-3", "numerical_window_gate", 'if total["demoted"] * 1000 > total["windows"] * INCONCLUSIVE_SHARE_CAP_PER_MILLE:', "if False:")
def oracle_g3(mods):
    """R-6: the demoted share is capped at 0.5 % of all windows, compared in integers: 5 of 1,000 passes, 6 of 1,000 FAILS and says so (the seal refuses a FAILED verdict:
    `require_passed`). The brief carries the count, the reasons and a judgment flag."""
    m = M(mods, "numerical_window_gate")
    ok = _verdict(m, [500, 500], [3, 2])
    assert ok["status"] == m.PASSED and ok["demoted_windows"] == 5 and ok["demoted_by_reason"] == {"verifier_budget_exhausted": 5}
    assert ok["numbered_windows"] == 995 and ok["blank_windows"] == 5 and "windows_demoted_to_named_blank" in ok["judgment_flags"]
    assert [h["reason"] for h in ok["honest_nulls"]] == ["verifier_budget_exhausted", "verifier_budget_exhausted"]
    bad = _verdict(m, [500, 500], [3, 3])
    assert bad["status"] == m.FAILED and any("above the 0.5 % cap" in p for p in bad["problems"]), bad["problems"]


@claim("G-4", "numerical_window_gate", 'if any(r not in INCONCLUSIVE_REASONS for r in d["demoted"]):', "if False:")
def oracle_g4(mods):
    """R-6: only the named INCONCLUSIVE reasons may demote a number. A report that demotes a window under `monotone_arc_not_established` — a real, blocking refusal — is not attested."""
    m = M(mods, "numerical_window_gate")
    with pytest.raises(m.NumericalGateDisagrees, match="only .* may demote"):
        _attest(m, _census(10), _report(9, 12, ("monotone_arc_not_established",)))


# D-1 .. D-5: the demoted windows are NAMED, checked at the gate, and served as the blank (lane review B-1, ruling SR-R67-B1-OWNER) ──────────────────────────

@claim("D-1", "numerical_window_gate", '            ids.append({"window_id": w["window_id"], "reason": w["reason"]})\n', "")
def oracle_d1(mods):
    """R-6 (B-1 a): demotion is a fact about NAMED windows. The attestation of a grain whose verifier demoted two windows lists them — sorted, each with its stored window_id and its
    reason — beside the counts; a demoted window the report cannot name (no stored id) is not attested at all."""
    m = M(mods, "numerical_window_gate")
    att = _attest(m, _census(10), _report(8, 12, ("verifier_budget_exhausted", "tie_ambiguous")))
    assert att["demoted_windows"] == [{"window_id": "w-0", "reason": "verifier_budget_exhausted"}, {"window_id": "w-1", "reason": "tie_ambiguous"}], att["demoted_windows"]
    swapped = _report(8, 12, ("verifier_budget_exhausted", "tie_ambiguous"))
    swapped["inconclusive_windows"].reverse()
    assert _attest(m, _census(10), swapped)["demoted_windows"] == att["demoted_windows"]           # sorted: the same set is the same attestation
    nameless = _report(9, 12, ("verifier_budget_exhausted",))
    del nameless["inconclusive_windows"][0]["window_id"]
    with pytest.raises(m.NumericalGateDisagrees, match="no stored window_id"):
        _attest(m, _census(10), nameless)


@claim("D-2", "numerical_window_gate", "    out += _demoted_window_list_problems(d)\n", "")
def oracle_d2(mods):
    """R-6 (B-1 b): the persisted list must AGREE with the counts. An attestation whose list names one window while the counts say two were demoted — or the reverse, a list under a
    reason the counts do not carry, or one window listed twice — makes the generation verdict FAIL (the seal refuses)."""
    m = M(mods, "numerical_window_gate")
    assert _verdict(m, [500, 500], [3, 2])["status"] == m.PASSED

    def drop_one(runner):
        att = runner[("marriage", "P1", "1.0.0")][m.ATTESTATION_KEY]
        del att["demoted_windows"][-1]
    bad = _verdict(m, [500, 500], [3, 2], tamper=drop_one)
    assert bad["status"] == m.FAILED and any("list" in p and "counts" in p for p in bad["problems"]), bad["problems"]

    def twice(runner):
        att = runner[("marriage", "P1", "1.0.0")][m.ATTESTATION_KEY]
        att["demoted_windows"][-1] = dict(att["demoted_windows"][0])
    assert _verdict(m, [500, 500], [3, 2], tamper=twice)["status"] == m.FAILED

    def other_reason(runner):
        att = runner[("marriage", "P1", "1.0.0")][m.ATTESTATION_KEY]
        att["demoted_windows"][0]["reason"] = "tie_ambiguous"
    assert _verdict(m, [500, 500], [3, 2], tamper=other_reason)["status"] == m.FAILED

    def not_a_list(runner):
        runner[("marriage", "P1", "1.0.0")][m.ATTESTATION_KEY]["demoted_windows"] = "w-0"
    assert _verdict(m, [500, 500], [3, 2], tamper=not_a_list)["status"] == m.FAILED


@claim("D-3", "numerical_window_gate", "        if stray:\n", "        if False:\n")
def oracle_d3(mods):
    """R-6 (B-1 b): each attested window must be a stored NUMBERED window of THAT grain. A demoted id the grain does not hold as a numbered window — a blank, another grain's window,
    an id that does not exist — makes the verdict FAIL, naming it."""
    m = M(mods, "numerical_window_gate")
    assert _verdict(m, [500, 500], [3, 2])["status"] == m.PASSED
    # the stored P1 windows are `P1-0 … P1-499` less the first, which is now a blank: the attestation still demotes it
    gone = _verdict(m, [500, 500], [3, 2], numbered_ids=lambda path: [(f"{path}-{i}",) for i in range(1, 500)] if path == "P1" else [(f"{path}-{i}",) for i in range(500)])
    assert gone["status"] == m.FAILED and any("'P1-0'" in p and "not stored numbered windows of this grain" in p for p in gone["problems"]), gone["problems"]


class _Fake:
    """A connection answering the one query `_demoted_windows` makes, with the attestation rows the test supplies (and recording that it asked)."""

    def __init__(self, rows):
        self.rows, self.asked = rows, []

    def execute(self, sql, params=()):
        self.asked.append((sql, params))
        return _Rows(self.rows)


def _identity(*pairs):
    return ({"commit": "x", "numerical_window_gate": {"status": "PASSED", "demoted_windows": [{"window_id": w, "reason": r} for w, r in pairs]}},)


def _served_window(wid, **extra):
    return {"window_id": wid, "event_class": "marriage", "peak_instant": "2030-01-01T00:00:00+00:00", "score": 0.5, "evidence_for": 1.25, "evidence_against": 0.25,
            "severity": 0.5, "outcome_valence_for_native": "favourable", "objective": "evidence_for_per_root_sum", "objective_value": 1.25,
            "qualification": {"policy": "window_qualification/1", "unqualified_reason": None, "solver_certificate": {"value": 1.25, "instant": 0.0}},
            "unqualified_reason": None, "demoted_at_seal": False, **extra}


@claim("D-4", "serving_reader", "w.update(peak_instant=None, score=None, evidence_for=None, evidence_against=None, severity=None, objective_value=None,\n"
       "                 outcome_valence_for_native='unqualified', unqualified_reason=reason, demoted_at_seal=True)",
       "w.update(unqualified_reason=reason, demoted_at_seal=True)")
def oracle_d4(mods):
    """R-6 / CLAUDE.md §N.7.6 (B-1 c): a demoted window is SERVED as the named blank it was sealed as — every numeric field null (the page's columns, the constructor's
    `objective_value`, and the builder's certificate whose value and instant are the unverified number), the valence `unqualified`, `unqualified_reason` the attested reason. A window
    the attestation does not list is served exactly as stored."""
    r = M(mods, "serving_reader")
    listed, other = _served_window("w-0"), _served_window("w-1")
    before = copy.deepcopy(other)
    r._serve_demoted_as_blank([listed, other], {"w-0": "verifier_budget_exhausted"})
    assert all(listed[k] is None for k in ("peak_instant", "score", "evidence_for", "evidence_against", "severity", "objective_value")), listed
    assert listed["outcome_valence_for_native"] == "unqualified" and listed["unqualified_reason"] == "verifier_budget_exhausted" and listed["demoted_at_seal"] is True
    assert listed["qualification"]["unqualified_reason"] == "verifier_budget_exhausted" and "solver_certificate" not in listed["qualification"]
    assert other == before


@claim("D-5", "serving_reader", "    if policy != POLICY_QUALIFICATION:\n        return {}", "    if False:\n        return {}")
def oracle_d5(mods):
    """R-6 (B-1 c): the reader takes the demotions from the generation's VERIFIED grains' persisted attestations, under the numerical policy only — the all-NULL policy has no number
    to blank and the reader does not even ask. Two grains' lists merge; a malformed entry is ignored (the gate refuses to seal one), never guessed."""
    r = M(mods, "serving_reader")
    conn = _Fake([_identity(("w-0", "tie_ambiguous")), _identity(("w-9", "verifier_budget_exhausted"))])
    assert r._demoted_windows(conn, "c", "g", "window_qualification/1") == {"w-0": "tie_ambiguous", "w-9": "verifier_budget_exhausted"}
    sql = conn.asked[0][0]
    assert "status = 'VERIFIED'" in sql and "ka_gochara_eval_window_verification" in sql
    silent = _Fake([_identity(("w-0", "tie_ambiguous"))])
    assert r._demoted_windows(silent, "c", "g", "all_null_candidate/1") == {} and silent.asked == []
    messy = _Fake([({"numerical_window_gate": {"demoted_windows": [{"window_id": 7, "reason": "x"}, {"window_id": "w-1"}, "w-2", {"window_id": "w-3", "reason": "tie_ambiguous"}]}},),
                   ({"commit": "x"},)])
    assert r._demoted_windows(messy, "c", "g", "window_qualification/1") == {"w-3": "tie_ambiguous"}


# W-1 .. W-3: the verifier seam ───────────────────────────────────────────────────────────────────────────────────────────────────

class _Rows:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None


class ProvConn:
    """The SQL surface `verify_window_semantics` reads, answered from lists — WITH the provenance columns, so `qualification` is compared."""

    def __init__(self, windows, records, links):
        self.windows, self.records, self.links = windows, records, links

    def execute(self, sql, params=()):
        if "kala_gochara_publication" in sql or "kala_gochara_coverage" in sql:
            return _Rows([])
        if "pg_attribute" in sql:
            return _Rows([(3,)])
        if "ka_gochara_eval_window_record" in sql:
            return _Rows(self.links)
        if "ka_gochara_relationship_record" in sql:
            return _Rows(self.records)
        if "ka_gochara_eval_window" in sql:
            return _Rows(self.windows)
        raise AssertionError(sql)


GRAIN = dict(chart_id="c", generation="g", event_class="marriage", path_id="P3", rule_version="1.0.0")


class Verdict:
    def __init__(self, classification, findings=(), inconclusive=()):
        self.classification, self.findings, self.inconclusive = classification, tuple(findings), tuple(inconclusive)


def _fn_windows(verdicts, *, qualification_extra=None, n=1):
    """`n` function-valued windows (one record each, days 0-10, 20-30, …) drafted by the REAL sweep and stored in the shape the verifier reads; the verifier seam answers
    `verdicts[i]` for window i. Returns the verify report."""
    recs = [_rec(f"k{i}", path="P3", version="1.0.0", relation="conjunction", kind="house_lord", supports=((20 * i, 20 * i + 10),),
                 delta_lambda_at=lambda t: 1.0) for i in range(n)]
    drafts, _ = _draft(recs, lambda p, v: _rows_declared(p, v, orb=5.0))
    assert len(drafts) == n
    stored, records, links = [], [], []
    for i, d in enumerate(drafts):
        lo, hi = d.interval
        q = d.qualification()
        q.update(qualification_extra or {})
        stored.append((f"w{i}", lo, hi, d.peak_instant, d.score, d.evidence_for, d.evidence_against, None, list(d.null_states_used),
                       d.outcome_valence_for_native, d.objective, d.objective_value, q))
        records.append((f"k{i}", f"root-k{i}", "conjunction", "house_lord", "jupiter", None, lo, hi))
        links.append((f"w{i}", f"k{i}"))
    calls = []

    def fn(window):
        calls.append(window)
        return verdicts[len(calls) - 1]

    return wv.verify_window_semantics(ProvConn(stored, records, links), factor_rows=_rows_declared("P3", "1.0.0", orb=5.0), dynamic_enabled=True,
                                      policy=wv.POLICY_VERSION, solver_check_fn=fn, **GRAIN), calls


@claim("W-1", "window_verifier", 'if cls == "DISAGREEMENT":', 'if cls == "DISAGREEMENT" and False:')
def oracle_w1(mods):
    """R-6: a DISAGREEMENT from the independent solver check is a problem the verification raises — the seal is blocked, always (nothing is demoted or persisted)."""
    v = M(mods, "window_verifier")
    with pytest.raises(RuntimeError, match="the independent solver check DISAGREES — certificate_bound_violated: x"):
        _fn_windows_with(v, [Verdict("DISAGREEMENT", [("certificate_bound_violated", "x")])])


def _fn_windows_with(v, verdicts, **kw):
    saved = globals()["wv"]
    globals()["wv"] = v
    try:
        return _fn_windows(verdicts, **kw)
    finally:
        globals()["wv"] = saved


@claim("W-2", "window_verifier", "fully_reproduced += 1                  # reproduced as the named blank it will be served as", "pass")
def oracle_w2(mods):
    """R-6: an INCONCLUSIVE window is DEMOTED — counted as reproduced (as the named blank it will be served as, so the grain can verify), listed with its stored window_id, its reason and the valence it
    carried, and never counted among the numerically reproduced. An AGREED numbered window is numeric. The report stays VERIFIED."""
    v = M(mods, "window_verifier")
    rep, calls = _fn_windows_with(v, [Verdict("INCONCLUSIVE", inconclusive=[("verifier_budget_exhausted", "")]), Verdict("AGREED")], n=2)
    assert rep["status"] == "VERIFIED" and rep["windows"] == 2 and rep["fully_reproduced"] == 2 and rep["numeric_reproduced"] == 1, rep
    assert rep["solver_checked_windows"] == 2 and rep["unverified_dynamic"] == 0
    assert rep["inconclusive_windows"] == [{"window": calls[0]["window"], "window_id": "w0", "reason": "verifier_budget_exhausted",
                                            "stored_numbered": True, "valence": calls[0]["valence"], "had_score": True}]


@claim("W-3", "window_verifier", 'if {k: v for k, v in s_qual.items() if k != "solver_certificate"} != want_q:', "if s_qual != want_q:")
def oracle_w3(mods):
    """R-7: the builder's certificate rides inside the `qualification` record; the verifier's provenance comparison (policy, reason, unresolved, members …) must not trip on it —
    and must still catch a changed member count beside it."""
    v = M(mods, "window_verifier")
    rep, _ = _fn_windows_with(v, [Verdict("AGREED")], qualification_extra={"solver_certificate": {"schema": sol.CERT_SCHEMA}})
    assert rep["status"] == "VERIFIED" and rep["numeric_reproduced"] == 1
    with pytest.raises(RuntimeError, match="qualification .* != re-derived"):
        _fn_windows_with(v, [Verdict("AGREED")], qualification_extra={"solver_certificate": {"schema": sol.CERT_SCHEMA}, "members": 9})


# S-1 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

@claim("S-1", "window_sweep", "objective_value=best,\n            solver_certificate=solver_certificate, sliver_pieces_excluded=piece_slivers, **base))", "objective_value=best, sliver_pieces_excluded=piece_slivers, **base))")
def oracle_s1(mods):
    """R-7: the sweep stores the solver's certificate in the window's `qualification` — for the numbered window and for the named blank alike — and a solver blank is a NAMED blank
    (its reason, the unqualified valence, no number); without the seam a function-valued window is still blank under the dynamic switch."""
    w = M(mods, "window_sweep")
    rec = _rec("k", path="P3", version="1.0.0", relation="conjunction", kind="house_lord", supports=((0, 10),), delta_lambda_at=lambda t: 1.0)
    cert = {"schema": sol.CERT_SCHEMA, "marker": 1}
    out = types.SimpleNamespace(status="solved", value=0.8, instant=_d(5), reason=None, certificate=cert)
    (numbered,), _ = w.draft_windows("marriage", [rec], lambda p, v: _rows_declared(p, v, orb=5.0), window_solver=lambda ctx: out)
    assert numbered.peak_instant == _d(5) and numbered.objective_value == 0.8 and numbered.qualification()["solver_certificate"] == cert
    blank = types.SimpleNamespace(status="blank", value=None, instant=None, reason=sol.REASON_BUDGET, certificate=cert)
    (b,), _ = w.draft_windows("marriage", [rec], lambda p, v: _rows_declared(p, v, orb=5.0), window_solver=lambda ctx: blank)
    assert b.peak_instant is None and b.score is None and b.unqualified_reason == sol.REASON_BUDGET and b.solver_certificate == cert
    assert b.qualification()["unresolved"] == {sol.REASON_BUDGET: 1} and b.outcome_valence_for_native == "unqualified"


# ── the harness ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────

_COUNT = [0]
_PATHS = {"window_solver": sol, "window_cert_check": cc, "numerical_window_gate": nwg, "window_verifier": wv, "window_sweep": ws, "serving_reader": rd}


def _load(name: str, source: str):
    _COUNT[0] += 1
    mod = types.ModuleType(f"_r67_{name}_{_COUNT[0]}")
    mod.__file__ = _PATHS[name].__file__
    mod.__package__ = PKG
    sys.modules[mod.__name__] = mod                   # dataclasses resolve their annotations through sys.modules
    try:
        exec(compile(source, mod.__file__, "exec"), mod.__dict__)
    finally:
        sys.modules.pop(mod.__name__, None)
    return mod


def real_modules():
    return dict(_PATHS)


def reverted_modules(module: str, old: str, new: str):
    src = Path(_PATHS[module].__file__).read_text()
    assert old != new and src.count(old) == 1, f"the planted reversion must match exactly once, matched {src.count(old)}x: {old[:80]!r}"
    mods = real_modules()
    mods[module] = _load(module, src.replace(old, new))
    return mods


@pytest.fixture(autouse=True)
def _restore_gate_and_registry():
    saved = {k: getattr(nwg, k) for k in ("census", "_rows")}
    from services.gochara_rules import registry as reg
    factors = dict(reg.FACTORS)
    yield
    for k, v in saved.items():
        setattr(nwg, k, v)
    reg.FACTORS.clear()
    reg.FACTORS.update(factors)


@pytest.mark.parametrize("cid", sorted(CLAIMS))
def test_oracle_passes_on_the_real_code(cid):
    CLAIMS[cid][0](real_modules())


@pytest.mark.parametrize("cid", sorted(CLAIMS))
def test_the_single_planted_reversion_fails_the_oracle(cid):
    oracle, module, old, new = CLAIMS[cid]
    mods = reverted_modules(module, old, new)         # built OUTSIDE the raises-block: a reversion that no longer matches is an ERROR, not a pass
    with pytest.raises((Exception, pytest.fail.Exception)) as info:
        oracle(mods)
    assert not isinstance(info.value, (SyntaxError, NameError, ImportError)), f"the reversion broke the module instead of the claim: {info.value!r}"


def test_every_claim_has_exactly_one_reversion_and_one_oracle():
    assert set(CLAIMS) == {"K-1", "K-2", "K-3", "K-4", "V-1", "V-2", "V-3", "V-4", "V-5", "V-6", "V-7", "V-8", "V-9", "C-1", "C-2", "C-3", "C-4", "G-1", "G-2", "G-3", "G-4",
                           "W-1", "W-2", "W-3", "S-1", "V-10", "V-11", "D-1", "D-2", "D-3", "D-4", "D-5", "T-1"}
    assert len({(m, old) for _, m, old, _ in CLAIMS.values()}) == len(CLAIMS)             # no two claims share a reversion site


# ── end to end: the first window exhausts its budget, the next one is easy (R-6) ─────────────────────────────────────────────────────

def _easy_world():
    """One tent crossing its target at the middle of a 10-day window at 1e-5 deg/s (orb 1): the kernel is 1 − |offset|/orb, a single crest of 1.0 — closed form."""
    T = 864000.0
    m = crest_member("e", "rE", ORB, t_crest=T / 2.0, speed=1e-5, support=(0.0, T))
    lam = lambda t: 100.0 + 1e-5 * (t - T / 2.0)                                       # noqa: E731
    rec = chk.CheckRecord("e", "rE", "E", ((at(0), at(T)),), tent=chk.TentFactor("E", 100.0, ORB))
    return T, (m,), rec, (lambda body, d: lam((d - T0).total_seconds()) % 360.0)


def test_end_to_end_the_first_window_exhausts_and_the_next_easy_window_is_still_solved_and_verified():
    """R-6 (GPT B8): with the grain-level budget the first window's exhaustion blanked every later window, and nothing independent could say whether that was honest. Now: window 1
    (first-order only, genuinely hard) exhausts ITS budget → a named blank carrying its partial tree; window 2 (easy) is solved with its own full budget → a number carrying its
    tree. Both go through the REAL sweep seam, both are checked by the verifier's own code (the blank's exhaustion confirmed, the number proved), the verification report is
    VERIFIED, and the gate's populations after classification read 1 numbered / 1 blank-by-exhaustion. Solving window 2 first changes nothing."""
    hard = Hump(T=864000.0, h4=False)
    T2, easy_members, easy_rec, easy_pos = _easy_world()
    solved_alone = sol.solve(sol.Problem(0.0, T2, sol.OBJECTIVE_SUM, easy_members))

    def build(ctx):
        lo = ctx["lo"]
        t0 = lo.astimezone(timezone.utc).isoformat()
        is_hard = lo == _d(0)
        problem = hard.problem() if is_hard else sol.Problem(0.0, T2, sol.OBJECTIVE_SUM, easy_members)
        res = sol.solve(problem)                                                           # its own budget: nothing carried over from window 1
        cert = sol.stored_certificate(res, objective=sol.OBJECTIVE_SUM, t0_iso=t0)
        return types.SimpleNamespace(status="solved" if res.status == sol.SOLVED else "blank", value=res.value,
                                     instant=None if res.instant is None else lo + timedelta(seconds=res.instant), reason=res.reason, certificate=cert)

    recs = [_rec("hard", path="P3", version="1.0.0", relation="conjunction", kind="house_lord", supports=((0, 10),), delta_lambda_at=lambda t: 1.0),
            _rec("easy", path="P3", version="1.0.0", relation="conjunction", kind="house_lord", supports=((20, 30),), delta_lambda_at=lambda t: 1.0)]
    drafts, _ = ws.draft_windows("marriage", recs, lambda p, v: _rows_declared(p, v, orb=5.0), window_solver=build)
    first, second = drafts
    assert (first.peak_instant, first.unqualified_reason) == (None, sol.REASON_BUDGET) and first.solver_certificate["evals"] == sol.MAX_EVALS_WINDOW
    assert second.unqualified_reason is None and second.peak_instant is not None and second.solver_certificate["outcome"] == "solved"
    assert second.objective_value == solved_alone.value and second.solver_certificate["evals"] == solved_alone.evals     # order-independent

    # the verifier: its own check of both certificates, through the seam
    def check(window):
        lo, hi, q = window["lo"], window["hi"], window["qualification"]["solver_certificate"]
        if window["peak"] is None:
            return cc.check_budget_blank(lo=lo, hi=hi, records=_records_for(window, lo, hard, easy_rec), objective=chk.OBJ_SUM,
                                         position_at=_pos_for(lo, hard, easy_pos), certificate=q)
        stored = chk.StoredWindow(window["peak"], window["objective_value"])
        return cc.check_numbered(lo=lo, hi=hi, records=_records_for(window, lo, hard, easy_rec), objective=chk.OBJ_SUM, stored=stored,
                                 position_at=_pos_for(lo, hard, easy_pos), certificate=q)

    stored_rows, records, links = [], [], []
    for i, d in enumerate(drafts):
        lo, hi = d.interval
        stored_rows.append((f"w{i}", lo, hi, d.peak_instant, d.score, d.evidence_for, d.evidence_against, None, list(d.null_states_used),
                            d.outcome_valence_for_native, d.objective, d.objective_value, d.qualification()))
        records.append((("hard", "easy")[i], f"root-{('hard', 'easy')[i]}", "conjunction", "house_lord", "jupiter", None, lo, hi))
        links.append((f"w{i}", ("hard", "easy")[i]))
    report = wv.verify_window_semantics(ProvConn(stored_rows, records, links), factor_rows=_rows_declared("P3", "1.0.0", orb=5.0), dynamic_enabled=True,
                                        policy=wv.POLICY_VERSION, solver_check_fn=check, **GRAIN)
    assert report["status"] == "VERIFIED" and report["solver_checked_windows"] == 2 and report["fully_reproduced"] == 2
    assert report["numeric_reproduced"] == 1 and report["inconclusive_windows"] == [] and wv.satisfies_gate(report)

    # the gate, after classification: 2 windows, 1 numbered, 1 blank by solver exhaustion — a named, justified blank
    census = {"windows": 2, "numbered": 1, "numbered_without_score": 0, "valence": {second.outcome_valence_for_native: 1},
              "blank": {sol.REASON_BUDGET: 1}, "problems": []}
    nwg.census = lambda *a, **k: census
    att = nwg.grain_attestation(None, report=report, policy=nwg.POLICY_QUALIFICATION, **GRAIN)
    assert (att["windows"], att["numbered"], att["blank"], att["demoted"]) == (2, 1, {sol.REASON_BUDGET: 1}, {})
    assert nwg.reason_group(sol.REASON_BUDGET) == nwg.SOLVER


def _records_for(window, lo, hard, easy_rec):
    if lo == _d(0):
        return [dataclasses_replace_times(r, lo) for r in hard.records()]
    return [dataclasses_replace_times(easy_rec, lo)]


def dataclasses_replace_times(rec, lo):
    """The analytic records are built for an origin of T0; the sweep's windows start at their own `lo`: shift the support."""
    import dataclasses
    shift = lo - T0
    return dataclasses.replace(rec, supports=tuple((a + shift, b + shift) for a, b in rec.supports))


def _pos_for(lo, hard, easy_pos):
    shift = lo - T0
    base = hard.pos if lo == _d(0) else easy_pos
    return lambda body, d: base(body, d - shift)


def test_a_planted_unnecessary_blank_is_refused_end_to_end():
    """R-6: the stored reason string alone cannot bypass the detector — an EASY window whose builder blanks it `solver_budget_exhausted` after declaring a 50-call budget is a
    DISAGREEMENT, so `verify_window_semantics` raises and nothing is sealed (the gate's older refusal, 'a blank where the table yields a value', now has a numerical twin)."""
    easy = Hump(T=864000.0)                         # H4 supplied: an easy window
    res, cert = easy.solve(max_evals=50)
    assert res.reason == sol.REASON_BUDGET
    rep = easy.check_blank(cc, cert)
    assert rep.classification == cc.DISAGREEMENT
    with pytest.raises(RuntimeError, match="DISAGREES — budget_declared_below_policy"):
        _fn_windows([Verdict(rep.classification, rep.findings)])


# ── guards (no reversion: they measure a property of the code) ───────────────────────────────────────────────────────────────────────

def test_the_certificate_check_imports_nothing_of_the_builder():
    src = Path(cc.__file__).read_text()
    bad = []
    for node in ast.walk(ast.parse(src)):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = "." * node.level + (node.module or "")
            names = [base] + [f"{base}.{a.name}" for a in node.names]
        bad += [n for n in names if "window_sweep" in n or "kernel_factor" in n or n.rsplit(".", 1)[-1] == "window_solver"]
    assert bad == []
    import subprocess
    root = str(Path(__file__).resolve().parents[3])
    # `-I` drops the user site and PYTHONPATH (where a CI runner's pyswisseph can live) and the package `__init__` imports `knots`: hand the child the parent's import path and a
    # swisseph stand-in, as `test_od1_s2_solver_check` does, so only OUR import closure is measured
    code = (f"import sys; sys.path[:0] = {[root, *sys.path]!r}\n"
            "try:\n    import swisseph\nexcept ImportError:\n    from unittest import mock; sys.modules['swisseph'] = mock.MagicMock()\n"
            "from services.gochara_kernel import window_cert_check\n"
            "bad = [m for m in ('services.gochara_kernel.window_sweep', 'services.gochara_kernel.window_solver') if m in sys.modules]\n"
            "print('LOADED', bad) if bad else print('CLEAN')\n")
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, cwd=root)
    assert out.stdout.strip() == "CLEAN", out.stdout + out.stderr


def test_the_verifier_that_hosts_the_g6_resolver_imports_nothing_of_the_builder_solver():
    """K12 (review N-1): `window_verifier` now hosts `g6_resolver`, so the builder's `window_solver` / `window_sweep` must be unreachable from it, statically (any import, lazy ones included)
    and at load time."""
    src = Path(wv.__file__).read_text()
    bad = []
    for node in ast.walk(ast.parse(src)):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = "." * node.level + (node.module or "")
            names = [base] + [f"{base}.{a.name}" for a in node.names]
        bad += [n for n in names if "window_sweep" in n or "kernel_factor" in n or n.rsplit(".", 1)[-1] == "window_solver"]
    assert bad == []
    import subprocess
    root = str(Path(__file__).resolve().parents[3])
    # `-I` drops the user site and PYTHONPATH (where a CI runner's pyswisseph can live) and the package `__init__` imports `knots`: hand the child the parent's import path and a
    # swisseph stand-in, as `test_od1_s2_solver_check` does, so only OUR import closure is measured
    code = (f"import sys; sys.path[:0] = {[root, *sys.path]!r}\n"
            "try:\n    import swisseph\nexcept ImportError:\n    from unittest import mock; sys.modules['swisseph'] = mock.MagicMock()\n"
            "from services.gochara_kernel import window_verifier\n"
            "bad = [m for m in ('services.gochara_kernel.window_sweep', 'services.gochara_kernel.window_solver') if m in sys.modules]\n"
            "print('LOADED', bad) if bad else print('CLEAN')\n")
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, cwd=root)
    assert out.stdout.strip() == "CLEAN", out.stdout + out.stderr


def test_the_two_sides_restate_the_same_literals():
    assert cc.SCHEMA == sol.CERT_SCHEMA and cc.BUDGET_REASON == sol.REASON_BUDGET
    assert cc.POLICY_MAX_EVALS_WINDOW == sol.MAX_EVALS_WINDOW == 500_000
    assert cc.OWN_QUANT == sol.QUANT and cc.OWN_TIE == sol.TIE and cc.OWN_H1_SPACING_S == sol.H1_SPACING_S
    assert cc.OBJECTIVE_NAMES == {chk.OBJ_SUM: sol.OBJECTIVE_SUM, chk.OBJ_MAXMIN: sol.OBJECTIVE_MINMAX}
    assert nwg.INCONCLUSIVE_REASONS == cc.INCONCLUSIVE_REASONS
    assert {chk.U_BUDGET, chk.U_CERT} <= cc.INCONCLUSIVE_REASONS and chk.U_TIE not in cc.INCONCLUSIVE_REASONS
    assert all(nwg.reason_group(r) == nwg.SOLVER for r in cc.INCONCLUSIVE_REASONS | {sol.REASON_BUDGET, sol.REASON_MONOTONE, sol.REASON_CERTIFICATE})


def test_the_certificate_is_json_and_small_even_for_a_window_that_exhausted_its_budget():
    h, res, cert = solved_hump()
    _h, _r, blank = exhausted_hump()
    for c in (cert, blank):
        text = json.dumps(c, allow_nan=False)
        assert json.loads(text) == c and len(text) < 40_000, len(text)
    assert len(blank["cells"]) <= sol.MAX_CERT_CELLS and len(blank["open"]) <= sol.MAX_OPEN_CELLS


def test_a_certificate_larger_than_the_cap_is_coarsened_soundly_and_flagged_when_cells_are_dropped():
    cells = [["dead", float(i), i + 0.5, 0.1 * (i % 7)] for i in range(1000)]          # gaps between them: nothing merges
    out, truncated = sol._coarsen(cells, 100)
    assert truncated and len(out) == 100
    adjacent = [["dead", i * 1.0, i + 1.0, 0.1 * (i % 7)] for i in range(1000)]
    merged, truncated = sol._coarsen(adjacent, 100)
    assert not truncated and len(merged) == 1 and merged[0][1:3] == [0.0, 1000.0] and merged[0][3] == pytest.approx(0.6)       # a bound of the union: the larger
