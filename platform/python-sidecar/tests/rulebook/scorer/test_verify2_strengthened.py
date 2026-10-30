"""Tests strengthened after SCORER_REVIEW_VERIFY2 section 4: each fails under the mutation the reviewer applied."""

from __future__ import annotations

from datetime import date

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import FamilyContext, applicable_mask, donor_sets, reading_coverage, run_donor_check
from services.rulebook.scorer.model import ChartTimeline, Episode
from services.rulebook.scorer.runner import prepare_episodes

from ._toy import BASE, make_units, month_window, runs_series

CAREER = "career_adv_change_entry"


# ── P2 imputation at its CALL SITE (mutations: other donors' mean, zero, the chart's base rate) ───────────────
def _p2_world():
    n = 365 * 10
    rng = np.random.default_rng(11)
    units = make_units([("U0", "promotive", [[("M0", [C.GENERAL])]])])
    tls = [ChartTimeline(f"c{c}", BASE - 9000 + 50 * c, BASE, BASE + n - 1, {"M0": runs_series(rng, n, 0.25, 12)}) for c in range(8)]
    # chart 0: ten month episodes (ten cells, one unit); donor 3 has one of those windows unassessed: 90% defined
    months = [(1992, m) for m in range(1, 11)]
    lo0, hi0 = month_window(*months[4])
    tls[3].states["M0"][lo0 - BASE : hi0 - BASE + 1] = -1
    eps = [Episode(0, CAREER, C.FAVOURABLE, C.G2, *month_window(*ym)) for ym in months]
    eps += [Episode(c, CAREER, C.FAVOURABLE, C.G2, *month_window(1995, c)) for c in range(1, 8)]
    return FamilyContext(C.FAMILY_DASHA, tls, units), eps, (lo0, hi0)


def _expected_T(ctx, eps):
    """T2 recomputed by hand from the helpers: a donor's undefined cell takes THAT DONOR's own block base rate."""
    sets = donor_sets(ctx, eps, False, rule="p2_90")
    vals0 = []
    for c, d in sets.items():
        if d["elig"].size < C.MIN_ELIGIBLE_DONORS:
            continue
        choices = np.concatenate([[c], d["elig"]])
        M = []
        for j in range(len(d["eps"])):
            lo, hi = d["dlo"][j][choices], d["dhi"][j][choices]
            U = ctx.unit_coverages(d["units"][j], lo, hi, choices)
            for ui, v in enumerate(d["units"][j]):
                for ci in range(1, choices.size):
                    if not np.isfinite(U[ui, ci]):
                        U[ui, ci] = ctx.block_base_rate(int(choices[ci]), v, int(hi[0] - lo[0] + 1), int((lo[ci] + hi[ci]) // 2))
            M.append(U.mean(axis=0))
        M = np.array(M)
        vals0.append((M[:, 0] - M[:, 1:].mean(axis=1)).mean())
    return float(np.mean(vals0))


def test_p2_call_site_uses_the_donors_own_base_rate():
    ctx, eps, _w = _p2_world()
    assert 3 in donor_sets(ctx, eps, False, rule="p2_90")[0]["elig"] and 3 not in donor_sets(ctx, eps, False, rule="m3")[0]["elig"]
    r = run_donor_check(ctx, eps, 50, np.random.default_rng(1), False, rule="p2_90")
    assert r["T"] == pytest.approx(_expected_T(ctx, eps), abs=1e-12)
    assert r["imputed_share"] > 0


def test_p2_call_site_differs_from_each_wrong_imputation():
    """The three mutations give a different T: zero, the other donors' mean, and the CHART's own base rate."""
    ctx, eps, (lo, hi) = _p2_world()
    good = run_donor_check(ctx, eps, 20, np.random.default_rng(1), False, rule="p2_90")["T"]
    v = ctx.units[0].variant(CAREER, True)
    donor_rate = ctx.block_base_rate(3, v, hi - lo + 1, (lo + hi) // 2)
    chart_rate = ctx.block_base_rate(0, v, hi - lo + 1, (lo + hi) // 2)
    assert donor_rate != pytest.approx(0.0) and donor_rate != pytest.approx(chart_rate)  # the mutations would change T
    orig = ctx.block_base_rate
    for wrong in (lambda chart, var, L, mid: 0.0, lambda chart, var, L, mid: orig(0, var, L, mid)):
        ctx.block_base_rate = wrong
        try:
            bad = run_donor_check(ctx, eps, 20, np.random.default_rng(1), False, rule="p2_90")["T"]
        finally:
            ctx.block_base_rate = orig
        assert bad != pytest.approx(good, abs=1e-12)


# ── horizon END edges (mutations: end-side month condition removed; strict inequality at the end) ──────────────
def _chart():
    n = 365 * 4
    start = date(1990, 1, 10).toordinal()
    end = start + n - 1  # 1994-01-08
    units = make_units([("U0", "promotive", [[("M0", [C.GENERAL])]])])
    t = ChartTimeline("c0", start - 9000, start, end, {"M0": runs_series(np.random.default_rng(1), n, 0.2, 10)})
    return FamilyContext(C.FAMILY_DASHA, [t], units), t


def test_end_edge_day_on_the_last_day_is_clipped_and_kept_and_the_day_after_is_dropped():
    ctx, t = _chart()
    last = Episode(0, CAREER, C.FAVOURABLE, C.G1, t.h_end - 1, t.h_end + 1)  # day = h_end
    after = Episode(0, CAREER, C.FAVOURABLE, C.G1, t.h_end, t.h_end + 2)  # day = h_end + 1
    kept, drops = prepare_episodes(ctx, [last, after])
    assert [(e.lo, e.hi) for e in kept] == [(t.h_end - 1, t.h_end)] and drops["dropped_horizon"] == 1 and drops["clipped_day_windows"] == 1


def test_end_edge_month_straddling_the_end_is_dropped_and_a_month_inside_is_kept():
    ctx, t = _chart()
    e = date.fromordinal(t.h_end)
    straddle = Episode(0, CAREER, C.FAVOURABLE, C.G2, *month_window(e.year, e.month))  # January 1994 crosses the end
    inside = Episode(0, CAREER, C.FAVOURABLE, C.G2, *month_window(1993, 12))
    assert straddle.lo <= t.h_end < straddle.hi
    kept, drops = prepare_episodes(ctx, [straddle, inside])
    assert kept == [inside] and drops["dropped_horizon"] == 1


# ── a reading's day set excludes days that every passing member leaves unassessed ───────────────────────────
def test_reading_day_set_excludes_days_no_passing_member_assessed():
    a = np.array([1, -1, -1, 0], dtype=np.int8)  # passes: 2 of 4 assessed
    b = np.array([-1, 0, -1, 1], dtype=np.int8)  # passes: 2 of 4 assessed
    cov = reading_coverage([a, b], np.array([0]), 4)[0]
    assert cov == pytest.approx(2 / 3)  # day set = days 0, 1, 3 (day 2 nobody assessed), TRUE on 0 and 3
    assert cov != pytest.approx(2 / 4)


# ── applicability never reads a TRUE day (mutation: a member passes when its window has a TRUE day) ──────────────
def test_a_member_under_half_assessed_with_a_true_day_does_not_pass():
    a = np.array([1, -1, -1, -1], dtype=np.int8)  # TRUE on its only assessed day: under half assessed
    b = np.array([0, 0, 0, 0], dtype=np.int8)
    assert reading_coverage([a, b], np.array([0]), 4)[0] == 0.0  # a does not pass; only b counts
    assert np.isnan(reading_coverage([a], np.array([0]), 4)[0])  # alone, a does not apply at all


def test_an_episode_is_not_applicable_because_of_a_true_day_in_an_under_assessed_window():
    n = 400
    st = np.full(n, -1, dtype=np.int8)
    st[100] = 1  # one TRUE day, otherwise not assessed
    units = make_units([("U0", "promotive", [[("M0", [C.GENERAL])]])])
    t = ChartTimeline("c0", BASE - 9000, BASE, BASE + n - 1, {"M0": st})
    ctx = FamilyContext(C.FAMILY_DASHA, [t], units)
    ep = Episode(0, CAREER, C.FAVOURABLE, C.G1, BASE + 99, BASE + 101)
    assert applicable_mask(ctx, [ep]) == [False]
    t.states["M0"][99] = 0  # now 2 of 3 days assessed: applicable, whatever the states
    assert applicable_mask(FamilyContext(C.FAMILY_DASHA, [t], units), [ep]) == [True]
