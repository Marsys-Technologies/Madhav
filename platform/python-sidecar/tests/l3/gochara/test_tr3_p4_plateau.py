"""SR-TR3-P4-PLATEAU (TR3 DEFECT E) — the verifier's tie scan no longer refines a certified-constant stretch of a max-min (P4) window down to LEAF_S.

Defect: in the final TR 28 P4 windows (decade-long: Jupiter or Saturn activity a constant above the other agent's tent for days on end) were demoted as
`verifier_budget_exhausted` — `window_solver_check._points` bisected every stretch whose upper bound reached the tie threshold down to LEAF_S = 0.0864 s,
~1e6 leaves per day of plateau, > the 2e6-evaluation budget. The fix is a PRUNING the bound allows (`_flat`): on a stretch of a mixed piece every member is monotone,
so reduce(member minima) <= F <= reduce(member maxima); when the two are within PLATEAU_EPS the stretch is one plateau by `_extrema`'s own definition, and its two end
samples stand for it. The budget, the tolerances and the bound are unchanged.

Claims (D-OWNER-TESTS-20261016; ONE oracle and ONE planted reversion each, the reversion a single textual change to the checker's source, as in test_od1_s2_solver_check):

  P-1  a P4 window whose maximum is a long plateau (> the budget at LEAF_S) certifies, with the earliest tie still the plateau's start
  P-2  a stretch whose enclosure is NOT tight is still searched: a kinked crest inside a mixed piece is located (the lower end of the enclosure is the member MINIMA)
  P-3  a stretch touching a station zone is never taken as flat (the longitude is non-monotone there by up to NEAR_END_NOISE_DEG)
  P-4  the budget cap is unchanged: a P4 window that genuinely needs more evaluations than `max_evals` is INCONCLUSIVE `verifier_budget_exhausted`, never a pass
  P-5  a true exceedance on a plateau window is still REFUTED (objective_exceeds_stored_maximum) — the pruning hides nothing above the stored maximum

Doctrine / analytic source: the plateau world below is closed-form (Jupiter const 0.5 record + a rising tent kept under it, Saturn a slowly falling tent kept over it): F = 0.5
exactly on the whole window, so the maximum is 0.5, the earliest tie is the window's start (the frozen earliest-tie rule, plan §2.1; `_extrema`: "a plateau's instant is its start").
"""
from __future__ import annotations

import pytest

from services.gochara_kernel import window_cert_check as cc
from services.gochara_kernel import window_solver_check as chk

from .test_od1_s2_solver_check import at, codes, reverted_module, run, sky, stored, w_p4, DELTA, M_P4, T_P4

DAYS = 20.0
BUDGET = 300_000                       # < 20 d x 86400 s / LEAF_S = 2e7 leaves: the pre-fix scan cannot finish inside it


def w_plateau(m, *, j_const=0.4, days=DAYS):
    """P4 on [0, days): Jupiter = max(const 0.5, 0.4 x a tent RISING from 0.1 to 0.3), Saturn = a tent FALLING from 1 to 0.67 — so the piece is mixed (one tent rises, one falls)
    and F = min(0.5, S) = 0.5 on the whole window. `j_const` > 0.5 lets the Jupiter tent rise above the constant near the end instead (a real maximum later than the plateau)."""
    sup = ((at(0), at(days)),)
    pos = sky(J=lambda t: 100.0 + t, S=lambda t: 200.0 - t - 0.5)
    recs = [m.CheckRecord("jc", "RJ", "jupiter", sup, constant=0.5),
            m.CheckRecord("jt", "RJ", "jupiter", sup, constant=j_const, tent=m.TentFactor("J", 130.0, 40.0)),
            m.CheckRecord("s", "RS", "saturn", sup, constant=1.0, tent=m.TentFactor("S", 200.0, 60.0))]
    return {"lo": at(0), "hi": at(days), "records": recs, "pos": pos, "objective": m.OBJ_MAXMIN}


PLATEAU_OLD = ("return self._reduce_upper(pc, v1, v2) - lower <= PLATEAU_EPS", "return False")
CLAIMS: dict = {}


def claim(cid, old, new):
    def deco(fn):
        CLAIMS[cid] = (fn, old, new)
        return fn
    return deco


@claim("P-1", *PLATEAU_OLD)
def oracle_plateau_certifies(m):
    """A 20-day plateau of F = 0.5 (closed form) is proved inside the budget, at the plateau's START; a stored instant mid-plateau is the later tie and is refuted."""
    w = w_plateau(m)
    ok = run(m, w, stored(m, 0.0, 0.5), max_evals=BUDGET)
    assert ok.status == m.VERIFIED, (ok.status, ok.unverified, ok.findings)
    assert ok.evals < 5_000, ok.evals
    late = run(m, w, stored(m, 10.0, 0.5), max_evals=BUDGET)
    assert late.status == m.REFUTED and chk.F_INSTANT in codes(late), (late.status, codes(late))


@claim("P-2", "lower = self._reduce(pc, [min(a, b) for a, b in zip(v1, v2)])", "lower = self._reduce(pc, [max(a, b) for a, b in zip(v1, v2)])")
def oracle_loose_enclosure_is_searched(m):
    """Jupiter rising through its level and Saturn falling: min(fJ, fS) is an inverted V whose crest (a kink narrower than any sample) is the maximum — M_P4 at T_P4 (closed form,
    test_od1_s2_solver_check.w_p4). Both end values are low and equal-ish; only the member MINIMA make the enclosure wide, so the stretch is searched and the crest proved."""
    w = w_p4(m)
    assert run(m, w, stored(m, at(T_P4), M_P4)).status == m.VERIFIED
    bad = run(m, w, stored(m, at(T_P4), M_P4 - 1e-3))
    assert bad.status == m.REFUTED and chk.F_VALUE in codes(bad)


@claim("P-3", "if any(r > zl and l < zh for zl, zh, _n in self.zones):", "if False:")
def oracle_station_zone_is_never_flat(m):
    """A flat stretch is flat; the same stretch inside a station zone (|longitude| non-monotone up to NEAR_END_NOISE_DEG there) is not taken as flat."""
    w = w_plateau(m, days=1.0)
    eng = m._Engine(w["lo"], w["hi"], w["records"], w["objective"], stored(m, 0.0, 0.5), w["pos"], peak_tolerance_s=1.0, max_evals=BUDGET, event_class=None,
                    against_evaluated=False)
    xs = eng._cuts()
    eng.pieces = [eng._make_piece(l, r) for l, r in zip(xs, xs[1:])]
    pc = next(p for p in eng.pieces if p.defined and not p.pure)
    assert eng._flat(pc, pc.vl, pc.vr, pc.l, pc.r)
    eng.zones.append((pc.l + 10.0, pc.l + 20.0, 1e-9))
    assert not eng._flat(pc, pc.vl, pc.vr, pc.l, pc.r)
    assert eng._flat(pc, pc.vl, pc.vr, pc.l + 30.0, pc.r)                       # a stretch clear of the zone is still flat


@claim("P-4", "if self.evals >= self.max_evals:", "if self.evals >= self.max_evals * 1000:")
def oracle_cap_hit_is_inconclusive(m):
    """The budget is unchanged: the kinked P4 world needs ~1e2 evaluations; with a cap of 20 the check is UNVERIFIED `verifier_budget_exhausted` (never VERIFIED), and the
    certificate layer reads that as INCONCLUSIVE (R-6), not a DISAGREEMENT."""
    w = w_p4(m)
    rep = run(m, w, stored(m, at(T_P4), M_P4), max_evals=20)
    assert rep.status == m.UNVERIFIED and [r for r, _ in rep.unverified] == [chk.U_BUDGET], (rep.status, rep.unverified)
    assert cc.classify(rep) == cc.INCONCLUSIVE


@claim("P-5", "return v if (v is not None and v > thr) else None", "return None")
def oracle_true_exceedance_still_refutes(m):
    """Jupiter's tent (constant 0.9) climbs through the 0.5 plateau near the window's end, so the real maximum is above 0.5: the plateau value stored as the maximum is REFUTED."""
    w = w_plateau(m, j_const=0.9)
    rep = run(m, w, stored(m, 0.0, 0.5), max_evals=BUDGET)
    assert rep.status == m.REFUTED and chk.F_ABOVE in codes(rep), (rep.status, codes(rep))
    assert cc.classify(rep) == cc.DISAGREEMENT


@pytest.mark.parametrize("cid", sorted(CLAIMS))
def test_oracle_passes_on_the_real_checker(cid):
    CLAIMS[cid][0](chk)


@pytest.mark.parametrize("cid", sorted(CLAIMS))
def test_the_single_planted_reversion_fails_the_oracle(cid):
    oracle, old, new = CLAIMS[cid]
    reverted = reverted_module(old, new)
    with pytest.raises(AssertionError):
        oracle(reverted)
