"""SR-OD1 S1 — the window solver (`services.gochara_kernel.window_solver`), proved on ANALYTIC worlds (plan §2.4, §2.6).

No database, no Swiss, no doctrine value: every world is a polynomial-offset tent (the point activity kernel `1 − |offset|/orb`, the
arithmetic of `kernel_factor.activity_kernel`) with a closed-form maximum on paper, the orb a parameter over {0.5, 1, 2, 5}. The
oracles are the FROZEN objective definitions the registry/sweep already cite (never a captured output):

  evidence-for  F(t) = Σ_roots max_members v(t)           (`window_sweep.OBJECTIVE_EVIDENCE`, S:321 evidence_for)
  max-min       F(t) = min(act_Jupiter, act_Saturn)       (spec O-RP-3, S:321-323; `window_sweep.OBJECTIVE_P4`)
  maximum       the global one, interior extrema included (spec §7.3 O-SM-4, f(t) = t(1−t))
  tie rule      the EARLIEST of the distinct local extrema within 1e-9 of the top (spec §7.2 inv. 2 plateau rule; N-11 — never moved
                along one smooth hump); the frozen `_TIE`

Claims — each with ONE doctrine/analytic oracle that fails on its single planted reversion (plan §2.4; reversion named per test):

  C-S1  interior maxima are found                      (revert: evaluate the endpoints only)
  C-S2  the maximum is global, not first-found         (revert: search the first mixed piece only)
  C-S3  earliest among ties                            (revert: no tolerance — the strictly highest wins)
  C-S4  the tie rule is between extrema, not shoulders (revert: earliest sampled instant within 1e-9 of the top)
  C-S5  a stored `t_exact` is not trusted              (revert: use the hint as the crest cut)
  C-S6  the bound is rigorous on rising AND falling    (revert: the bound uses the left endpoint only)
  C-S7  P4 is max-min, not a sum                       (revert: sum the agents)
  C-S8  steps are exact                                (revert: ignore a step's boundary list)
  C-S9  incomplete boundaries ⇒ blank                  (revert: treat an incomplete list as complete)
  C-S10 H1 failure ⇒ blank                             (revert: skip the monotone-arc check)
  C-S11 budget exhaustion ⇒ blank, never a number      (revert: return a number on exhaustion)

C-S12 (builder ↔ verifier differential) is S2/S3; C-S13 (solver ≥ the legacy sampler) is S3. The randomised run at the bottom compares the
solver against an INDEPENDENT dense numpy scan of the model (a lower bound that converges to the maximum).
"""
from __future__ import annotations

import math
import random

import numpy as np
import pytest

from services.gochara_kernel import window_solver as sol

from .od1_solver_harness import (DAY, ORBS, Piecewise, crest_member, dense_max, hump_world, member, objective_values, poly_tent,
                                 sinusoid_tent)

T = 2.0e5                      # one hump's span (s) ≈ 2.3 days
SUM, MINMAX = sol.OBJECTIVE_SUM, sol.OBJECTIVE_MINMAX


def run(ms, lo, hi, objective=SUM, **kw):
    return sol.solve(sol.Problem(lo, hi, objective, tuple(ms)), **kw)


# ── C-S1 interior maxima are found ──────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("orb", ORBS)
@pytest.mark.parametrize("sigma", [0.25, 0.6])
def test_cs1_interior_maximum_of_rising_linear_plus_falling_quadratic(orb, sigma):
    """A rising linear tent + a falling quadratic tent: F = 2 − (a0+b0) + σ·τ(1−τ) (spec O-SM-4 shape), maximum 2 − a0 − b0 + σ/4 at the
    MIDDLE of the window — strictly above both ends (F(0) = F(T) = 2 − a0 − b0 up to the quadratic's own end term)."""
    ms, m_true, t_true = hump_world(orb, T=T, sigma=sigma)
    r = run(ms, 0.0, T)
    assert r.status == sol.SOLVED, (r.reason, r.detail)
    assert r.value == pytest.approx(m_true, abs=1e-10)
    assert r.instant == pytest.approx(t_true, abs=1e-3)
    # both ends sit σ/4 BELOW the maximum (τ(1−τ) = 0 there): an endpoint-only search cannot reach it
    f_ends = max(objective_values(sol.Problem(0.0, T, SUM, tuple(ms)), np.array([0.0, T - sol.QUANT])))
    assert r.value >= f_ends + sigma / 4.0 - 1e-6


def test_cs1_without_the_kinematic_bound_the_answer_is_exact_or_blank_never_wrong():
    """H4 absent ⇒ only the first-order bound: slower, still rigorous. The budget may exhaust (blank); a number must still be right."""
    ms, m_true, t_true = hump_world(1.0, T=T, h4=False)
    r = run(ms, 0.0, T, max_evals=20_000)
    if r.status == sol.SOLVED:
        assert r.value == pytest.approx(m_true, abs=1e-10) and r.instant == pytest.approx(t_true, abs=1e-3)
    else:
        assert r.reason in (sol.REASON_BUDGET, sol.REASON_CERTIFICATE) and r.value is None and r.instant is None


# ── C-S2 the maximum is global, not first-found ─────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("later_higher", [True, False])
def test_cs2_global_maximum_over_two_disjoint_humps(later_higher):
    """Two humps in consecutive supports (one connected window); the HIGHER one wins wherever it is (the later one at +0.02)."""
    lift1, lift2 = (0.0, 0.02) if later_higher else (0.02, 0.0)
    m1, v1, t1 = hump_world(1.0, T=T, t_start=0.0, lift=lift1, group_a="r1", group_b="r2", key="p")
    m2, v2, t2 = hump_world(1.0, T=T, t_start=T, lift=lift2, group_a="r3", group_b="r4", key="q")
    r = run(m1 + m2, 0.0, 2 * T)
    assert r.status == sol.SOLVED, (r.reason, r.detail)
    want_v, want_t = (v2, t2) if later_higher else (v1, t1)
    assert r.value == pytest.approx(want_v, abs=1e-10)
    assert r.instant == pytest.approx(want_t, abs=1e-3)


# ── C-S3 earliest among ties ─────────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("orb", ORBS)
def test_cs3_two_exact_crossings_both_one_earliest_wins(orb):
    """Two bodies each cross their target exactly (kernel 1.0 at the crest) in consecutive supports: F = 1.0 at both instants, the
    plateau rule takes the EARLIER one (spec §7.2 inv. 2)."""
    t1, t2 = 4.0e4, 1.6e5
    ms = (crest_member("c1", "r1", orb, t_crest=t1, speed=1.0e-5 * orb, support=(0.0, 1.0e5)),
          crest_member("c2", "r2", orb, t_crest=t2, speed=2.0e-5 * orb, support=(1.0e5, 2.0e5)))
    r = run(ms, 0.0, 2.0e5)
    assert r.status == sol.SOLVED, (r.reason, r.detail)
    assert r.value == pytest.approx(1.0, abs=1e-10)
    assert r.instant == pytest.approx(t1, abs=1e-3)
    assert r.certificate["ties"] == 2


def test_cs3_humps_within_the_tolerance_earliest_wins_beyond_it_the_higher():
    """Two interior humps whose peaks differ by 5e-10 (< the frozen 1e-9) are ONE tie class: the EARLIER hump's instant is stored with
    the global maximum as the value. At 5e-9 apart they are not tied: the higher (later) hump wins."""
    for gap, want_first in ((5e-10, True), (5e-9, False)):
        m1, v1, t1 = hump_world(1.0, T=T, t_start=0.0, group_a="r1", group_b="r2", key="p")
        m2, v2, t2 = hump_world(1.0, T=T, t_start=T, lift=gap, group_a="r3", group_b="r4", key="q")
        r = run(m1 + m2, 0.0, 2 * T)
        assert r.status == sol.SOLVED, (r.reason, r.detail)
        assert r.value == pytest.approx(v2, abs=2e-11) and v2 - v1 == pytest.approx(gap, abs=1e-12)
        assert r.instant == pytest.approx(t1 if want_first else t2, abs=1e-3), gap


@pytest.mark.parametrize("seed", range(6))
def test_cs3_many_crossings_with_equal_and_unequal_strengths_earliest_of_the_strongest(seed):
    """Six disjoint supports, each holding one exact crossing (kernel 1.0 at the crest) scaled by a step strength in {0.5, 0.75, 1.0}:
    F's local maxima are the six crests, valued by their strengths; the stored instant is the EARLIEST crest of the strongest class."""
    rng = random.Random(seed)
    slot = 1.0e5
    strengths = [rng.choice((0.5, 0.75, 1.0)) for _ in range(6)]
    crests = [i * slot + rng.uniform(0.2, 0.8) * slot for i in range(6)]
    ms = tuple(member(f"c{i}", f"r{i}", ((i * slot, (i + 1) * slot),), poly_tent(1.0, 0.0, 1.0e-5, 0.0, t0=crests[i]),
                      steps=(sol.constant_step(strengths[i]),)) for i in range(6))
    r = run(ms, 0.0, 6 * slot)
    assert r.status == sol.SOLVED, (r.reason, r.detail)
    top = max(strengths)
    assert r.value == pytest.approx(top, abs=1e-10)
    assert r.instant == pytest.approx(min(c for c, s in zip(crests, strengths) if s == top), abs=1e-3)
    assert r.certificate["ties"] == strengths.count(top)


def test_the_sinusoid_world_with_listed_stations_ties_the_crossings_and_takes_the_first():
    """A body oscillating about its target (offset R·sin(ωt+φ), half-period 25 d > the 5-day sampling): kernel 1.0 at each zero crossing
    (three in the window, exact ties) → the first, (π − φ)/ω. With the stations LISTED the window solves; unlisted, H1 blanks it."""
    omega, phase, radius, orb = math.pi / (25 * DAY), 0.3, 3.0, 1.0
    stations = [(math.pi / 2 - phase + m * math.pi) / omega for m in range(3)]
    window = 3 * math.pi / omega
    support = ((0.0, window),)
    r = run((member("s", "r", support, sinusoid_tent(orb, radius, omega, phase, stations=stations)),), 0.0, window)
    assert r.status == sol.SOLVED, (r.reason, r.detail)
    assert r.value == pytest.approx(1.0, abs=1e-10)
    assert r.instant == pytest.approx((math.pi - phase) / omega, abs=1e-3)
    assert r.certificate["ties"] == 3
    blank = run((member("s", "r", support, sinusoid_tent(orb, radius, omega, phase)),), 0.0, window)
    assert (blank.status, blank.reason) == (sol.BLANK, sol.REASON_MONOTONE)


# ── C-S4 the tie rule is between extrema, not on a shoulder (N-11) ──────────────────────────────────────────────────────────────

def test_cs4_one_smooth_hump_stores_the_crest_not_the_first_instant_within_1e9():
    """On F = C + σ·τ(1−τ) the set {F ≥ M − 1e-9} starts T·√(1e-9/σ) ≈ 12.6 s BEFORE the crest; the frozen tie rule is applied between
    DISTINCT extrema only, so the stored instant is the crest to the location tolerance (the old 27-second shift)."""
    sigma = 0.25
    ms, m_true, t_true = hump_world(1.0, T=T, sigma=sigma)
    shoulder = T * math.sqrt(sol.TIE / sigma)
    assert shoulder > 10.0
    r = run(ms, 0.0, T)
    assert r.status == sol.SOLVED
    assert abs(r.instant - t_true) < 1e-3 < shoulder / 1000


# ── C-S5 a stored t_exact is not trusted ────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("error", [1.0, -1.0, 1.0e3])
def test_cs5_the_stored_exact_instant_is_not_the_crest(error):
    """The tent's crest is RE-DERIVED by bisection on the monotone offset; a stored `t_exact` that is wrong by 1 s (or 1000 s) changes
    nothing."""
    t_c = 6.0e4
    ms = (crest_member("c", "r", 1.0, t_crest=t_c, speed=2.0e-5, support=(0.0, 1.5e5), hint=t_c + error),)
    r = run(ms, 0.0, 1.5e5)
    assert r.status == sol.SOLVED
    assert r.value == pytest.approx(1.0, abs=1e-10)
    assert r.instant == pytest.approx(t_c, abs=1e-3)


# ── C-S6 the bound is rigorous on decreasing and increasing terms ─────────────────────────────────────────────────────────────────

def _piece_of(problem):
    ctx = sol._Ctx(10 ** 7, None)
    _ordered, pieces = sol._build(problem, ctx)
    return [p for p in pieces if p is not None], ctx


@pytest.mark.parametrize("h4", [True, False])
@pytest.mark.parametrize("which", ["rising", "falling", "mixed"])
def test_cs6_upper_bound_dominates_the_dense_maximum_of_every_subinterval(which, h4):
    """`bound(l, r)` is the certificate every pruning rests on: it must dominate F on [l, r] for a RISING term (whose supremum is the
    right end), a FALLING term (the left end) and a mixed pair — with and without the second-order (H4) refinement."""
    orb = 1.0
    if which == "rising":
        ms = (member("a", "r", ((0.0, T),), poly_tent(orb, 0.9 * orb, -1.0e-6 * orb, 0.0, h4=h4)),)
    elif which == "falling":
        ms = (member("a", "r", ((0.0, T),), poly_tent(orb, 0.1 * orb, 1.0e-6 * orb, 0.0, h4=h4)),)
    else:
        ms = hump_world(orb, T=T, h4=h4)[0]
    problem = sol.Problem(0.0, T, SUM, tuple(ms))
    (piece,), _ = _piece_of(problem)
    rng = random.Random(7)
    for _ in range(60):
        l = rng.uniform(piece.a, piece.b_eff)
        r = min(piece.b_eff, l + 10 ** rng.uniform(0, 5.3))
        if r - l < 1e-3:
            continue
        ts = np.linspace(l, r, 4001)
        dense = float(np.max(objective_values(problem, ts)))
        assert piece.bound(l, r) >= dense - 1e-12, (which, h4, l, r)


# ── C-S7 P4 is max-min, not a sum ───────────────────────────────────────────────────────────────────────────────────────────────

def test_cs7_p4_objective_is_the_minimum_of_the_two_agents():
    """Jupiter's kernel RISES, Saturn's FALLS (fractions of the orb per second, vj = 2e-6, vs = 3e-6): fJ = 0.2 + vj·t, fS = 0.9 − vs·t.
    min(fJ, fS) peaks where they cross, t = 0.7/(vj+vs) = 1.4e5 s, value 0.48 (spec O-RP-3: one agent's strength never makes up for the
    other's absence). A SUM would fall monotonically from 1.1 at t = 0."""
    orb, vj, vs = 1.0, 2.0e-6, 3.0e-6
    ms = (member("J", "jupiter", ((0.0, T),), poly_tent(orb, 0.8 * orb, -vj * orb)),
          member("S", "saturn", ((0.0, T),), poly_tent(orb, 0.1 * orb, vs * orb)))
    t_x = 0.7 / (vj + vs)
    r = run(ms, 0.0, T, objective=MINMAX)
    assert r.status == sol.SOLVED, (r.reason, r.detail)
    assert r.value == pytest.approx(0.2 + vj * t_x, abs=1e-10)
    assert r.instant == pytest.approx(t_x, abs=1e-3)


def test_cs7_p4_needs_both_agents_live_a_piece_with_one_is_outside_the_domain():
    orb = 1.0
    ms = (member("J", "jupiter", ((0.0, T),), poly_tent(orb, 0.2 * orb, 1e-6 * orb, 0.0)),
          member("S", "saturn", ((T / 2, T),), poly_tent(orb, 0.3 * orb, 0.0, 0.0, velocity=True)))
    # Saturn's offset is constant (zero velocity): H1 refuses it — the window is blank with the named reason, not scored
    r = run(ms, 0.0, T, objective=MINMAX)
    assert r.status == sol.BLANK and r.reason == sol.REASON_MONOTONE


# ── C-S8 steps are exact ─────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _island_world(**kw):
    """A rising tent (u = 0.1 + 1.5e-6·t on [0, 2e5]) times a step: 0.4, except a 3-second ISLAND of 1.0 at [7e4, 7e4+3). Base ≤ 0.4·0.4 =
    0.16; the island's right end gives 0.1 + 1.5e-6·(7e4 + 3 − 1µs) = 0.2050045 — the maximum, at that instant."""
    step = Piecewise((7.0e4, 7.0e4 + 3.0), (0.4, 1.0, 0.4), **kw)
    tent = poly_tent(1.0, 0.9, -1.5e-6, 0.0)
    return (member("m", "r", ((0.0, 2.0e5),), tent, steps=(step,)),)


def test_cs8_a_one_piece_island_of_a_step_factor_is_found_exactly():
    r = run(_island_world(), 0.0, 2.0e5)
    assert r.status == sol.SOLVED, (r.reason, r.detail)
    t_end = 7.0e4 + 3.0 - sol.QUANT
    assert r.value == pytest.approx(0.1 + 1.5e-6 * t_end, abs=1e-12)
    assert r.instant == pytest.approx(t_end, abs=1e-9)


# ── C-S9 incomplete boundaries ⇒ blank ───────────────────────────────────────────────────────────────────────────────────────────

def test_cs9_a_boundary_list_not_asserted_complete_blanks_the_window():
    r = run(_island_world(complete=False), 0.0, 2.0e5)
    assert (r.status, r.reason, r.value, r.instant) == (sol.BLANK, sol.REASON_BOUNDARIES, None, None)


def test_cs9_a_state_factor_with_no_boundary_provider_blanks_the_window():
    r = run(_island_world(list_edges=False), 0.0, 2.0e5)
    assert (r.status, r.reason) == (sol.BLANK, sol.REASON_BOUNDARIES)


def test_cs9_an_unlisted_change_that_a_piece_sample_sees_blanks_even_when_asserted_complete():
    """The second, independent detector: a change the list omits, at an instant the piece's own samples straddle, is caught."""
    step = sol.Step(value_at=lambda t: 0.4 if t < 5.0e4 else 1.0, boundaries=lambda lo, hi: [], complete=True)
    ms = (member("m", "r", ((0.0, 2.0e5),), poly_tent(1.0, 0.9, -1.5e-6, 0.0), steps=(step,)),)
    r = run(ms, 0.0, 2.0e5)
    assert (r.status, r.reason) == (sol.BLANK, sol.REASON_BOUNDARIES)


def test_cs9_an_undeterminable_step_blanks_with_its_own_reason_or_the_generic_one():
    named = sol.Step(value_at=lambda t: None, constant=True, unknown_reason=lambda t: "vedha_overlay_not_bound")
    bare = sol.Step(value_at=lambda t: None, constant=True)
    ms = lambda st: (member("m", "r", ((0.0, 10.0),), None, steps=(st,)),)          # noqa: E731
    assert run(ms(named), 0.0, 10.0).reason == "vedha_overlay_not_bound"
    assert run(ms(bare), 0.0, 10.0).reason == sol.REASON_UNKNOWN


# ── C-S10 H1 failure ⇒ blank ────────────────────────────────────────────────────────────────────────────────────────────────────

W = 3.0e5
TS = 6.0e4


def _station_world(**kw):
    """offset = 0.3 + κ·(t − ts)², κ = 5e-12 per orb·s²: the body turns round at ts (a station) at offset 0.3 — kernel 0.7 there. On [0, W]
    the kernel at 0, mid and end is 0.682 > 0.6595 > 0.412 — it LOOKS monotone falling to a 3-point sample, while the true maximum, 0.7, is
    interior. Only the velocity-sign (H1) check sees the hidden turnaround."""
    return (member("m", "r", ((0.0, W),), poly_tent(1.0, 0.3, 0.0, 5.0e-12, t0=TS, **kw)),)


def test_cs10_a_station_inside_a_support_blanks_the_window_it_must_not_report_the_endpoint():
    r = run(_station_world(), 0.0, W)
    assert (r.status, r.reason, r.value, r.instant) == (sol.BLANK, sol.REASON_MONOTONE, None, None)


def test_cs10_the_same_station_listed_is_a_cut_and_the_peak_is_exact():
    r = run(_station_world(stations=(TS,)), 0.0, W)
    assert r.status == sol.SOLVED, (r.reason, r.detail)
    assert r.value == pytest.approx(0.7, abs=1e-10)
    assert r.instant == pytest.approx(TS, abs=2e-6)


@pytest.mark.parametrize("kw,why", [({"velocity": False}, "no velocity operand"), ({"spacing": None}, "no audited station spacing"),
                                    ({"spacing": 3 * DAY}, "audited spacing ≤ the 5-day sampling")])
def test_cs10_the_arc_cannot_be_established_without_its_operands(kw, why):
    r = run(_station_world(stations=(TS,), **kw), 0.0, W)
    assert (r.status, r.reason) == (sol.BLANK, sol.REASON_MONOTONE), why


# ── C-S11 budget exhaustion ⇒ blank, never a number ──────────────────────────────────────────────────────────────────────────────

def test_cs11_a_hard_world_with_a_tiny_budget_is_blank_not_best_found():
    ms, m_true, _t = hump_world(1.0, T=T)
    ok = run(ms, 0.0, T)
    assert ok.status == sol.SOLVED and ok.evals > 60                       # the world does need work …
    r = run(ms, 0.0, T, max_evals=40)                                       # … so 40 calls cannot settle it
    assert (r.status, r.reason, r.value, r.instant, r.certificate) == (sol.BLANK, sol.REASON_BUDGET, None, None, None)
    assert r.evals == 40


def test_cs11_the_grain_budget_is_shared_across_windows():
    ms, _m, _t = hump_world(1.0, T=T)
    need = run(ms, 0.0, T).evals
    grain = sol.Budget(int(need * 1.5))
    first = run(ms, 0.0, T, grain=grain)
    second = run(ms, 0.0, T, grain=grain)
    assert first.status == sol.SOLVED
    assert (second.status, second.reason, second.value) == (sol.BLANK, sol.REASON_BUDGET, None)
    assert grain.spent == first.evals + second.evals


# ── supporting behaviour the integration (S3) relies on ───────────────────────────────────────────────────────────────────────────

def test_a_right_open_end_is_evaluated_one_microsecond_inside():
    """A rising kernel to the window end: the supremum is not attained; the µs-quantised domain's maximum is at `hi − 1 µs`."""
    ms = (member("m", "r", ((0.0, 1.0e5),), poly_tent(1.0, 0.9, -1.0e-6, 0.0)),)
    r = run(ms, 0.0, 1.0e5)
    assert r.instant == pytest.approx(1.0e5 - sol.QUANT, abs=1e-9)
    assert r.value == pytest.approx(0.1 + 1.0e-6 * (1.0e5 - sol.QUANT), abs=1e-12)


def test_a_support_that_ends_while_the_kernel_still_rises_peaks_at_its_last_microsecond():
    ms = (member("a", "r1", ((0.0, 5.0e4),), poly_tent(1.0, 0.9, -1.0e-6, 0.0)),
          member("b", "r2", ((5.0e4, 1.0e5),), poly_tent(1.0, 0.95, -1.0e-7, 0.0)))
    r = run(ms, 0.0, 1.0e5)
    assert r.instant == pytest.approx(5.0e4 - sol.QUANT, abs=1e-9)             # the drop at 5e4 makes 5e4−1µs the local maximum


def test_a_constant_objective_is_one_plateau_whose_earliest_instant_is_the_window_start():
    ms = (member("m", "r", ((0.0, 100.0),), None, steps=(sol.constant_step(0.5),)),)
    r = run(ms, 0.0, 100.0)
    assert (r.value, r.instant) == (0.5, 0.0)


def test_roots_add_and_records_of_one_root_take_the_maximum():
    one_root = (member("a", "r", ((0.0, 10.0),), None, steps=(sol.constant_step(0.5),)),
                member("b", "r", ((0.0, 10.0),), None, steps=(sol.constant_step(0.25),)))
    two_roots = (member("a", "r1", ((0.0, 10.0),), None, steps=(sol.constant_step(0.5),)),
                 member("b", "r2", ((0.0, 10.0),), None, steps=(sol.constant_step(0.25),)))
    assert run(one_root, 0.0, 10.0).value == 0.5
    assert run(two_roots, 0.0, 10.0).value == 0.75


def test_a_malformed_step_value_is_refused_loudly():
    ms = (member("m", "r", ((0.0, 10.0),), None, steps=(sol.constant_step(1.5),)),)
    with pytest.raises(sol.SolverRefusal):
        run(ms, 0.0, 10.0)


def test_grain_budget_sizing_matches_the_s0_measurements():
    """S0 §1: MAX_EVALS_GRAIN = floor(18,000 s / (104 grains × c)) — c = 100 µs → 1.7e6, 48 µs → 3.6e6, 2.1 µs → 8.2e7."""
    assert sol.grain_budget_evals(18000.0, 104, 100e-6) == 1_730_769
    assert sol.grain_budget_evals(18000.0, 104, 48e-6) // 10 ** 5 == 36
    assert sol.grain_budget_evals(18000.0, 104, 2.1e-6) // 10 ** 6 == 82


def test_the_kinematic_bound_is_withheld_without_a_limb_window_list_and_inside_one():
    assert sol.accel_bound_provider("jupiter", None)(0.0, 1.0) is None
    prov = sol.accel_bound_provider("jupiter", [(1000.0, 2000.0)])
    assert prov(0.0, 500.0) == pytest.approx(0.0035 * 1.25 / 86400.0 ** 2)
    assert prov(500.0, 1500.0) is None and prov(1999.0, 3000.0) is None


# ── randomised differential against an independent dense scan ────────────────────────────────────────────────────────────────────

def _random_world(rng: random.Random, objective: str):
    wlen = 3000.0
    members = []
    n = rng.randint(2, 5)
    groups = ["jupiter", "saturn"] if objective == MINMAX else ["r1", "r2", "r3"]
    for i in range(n):
        orb = rng.choice((0.5, 1.0, 2.0))
        o1 = rng.choice((-1, 1)) * rng.uniform(1.0e-4, 6.0e-4)
        o2 = rng.uniform(-0.4, 0.4) * abs(o1) / (2.0 * wlen)
        mid_off = rng.uniform(-1.2, 1.2) * orb
        o0 = mid_off - o1 * (wlen / 2) - o2 * (wlen / 2) ** 2
        a = rng.uniform(0, wlen * 0.6)
        sup = [(a, rng.uniform(a + 300, wlen))]
        if rng.random() < 0.4:
            b = rng.uniform(sup[0][1], wlen)
            sup.append((b, rng.uniform(b + 50, wlen + 1)))
        steps = ()
        if rng.random() < 0.4:
            edges = sorted(rng.uniform(0, wlen) for _ in range(rng.randint(1, 2)))
            steps = (Piecewise(edges, [rng.choice((0.3, 0.6, 1.0)) for _ in range(len(edges) + 1)]),)
        members.append(member(f"m{i}", groups[i % len(groups)] if objective == MINMAX else rng.choice(groups), sup,
                              poly_tent(orb, o0, o1, o2), steps))
    return sol.Problem(0.0, wlen, objective, tuple(members))


@pytest.mark.parametrize("objective", [SUM, MINMAX])
def test_randomised_worlds_agree_with_the_dense_scan(objective):
    rng = random.Random(20261021 + (objective == MINMAX))
    solved = 0
    for k in range(25):
        problem = _random_world(rng, objective)
        dense_v, _dt = dense_max(problem, dt=0.02)
        if dense_v < 0:                                   # (min objective: no piece with both agents live)
            continue
        r = sol.solve(problem)
        assert r.status == sol.SOLVED, (k, r.reason, r.detail)
        solved += 1
        assert r.value >= dense_v - 1e-9, (k, r.value, dense_v)            # the solver is never below a value F really takes
        assert r.value <= dense_v + 1e-7, (k, r.value, dense_v)            # … and is the maximum (the scan polished to ~1e-8)
        f_at = float(objective_values(problem, np.array([r.instant]))[0])
        assert f_at >= r.value - 2e-9, (k, "the stored instant does not attain the stored maximum")
    assert solved >= 15
