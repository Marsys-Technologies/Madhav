"""Checks (a), (b), (c), the direction check and Z25: mechanics, level under the null, power under a planted effect."""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import FamilyContext, assemble, run_donor_check, scorable_mask, score_family
from services.rulebook.scorer.model import ChartTimeline, Episode, MemberSpec, UnitSpec

from ._toy import BASE, make_units, month_window, planted_episodes, random_episodes, runs_series, toy_world

AREAS = ["career_adv_change_entry", "illness_chronic_surgery"]
CAREER, ILLNESS = AREAS


# ── check (b) / (c): the statistic and the donor draw ───────────────────────────────
def _donor_world(seed, births, n=365 * 16, shifts=None):
    rng = np.random.default_rng(seed)
    units = make_units([(f"U{k}", "promotive" if k % 2 == 0 else "obstructive", [[(f"M{k}", [C.GENERAL])]]) for k in range(4)])
    tls = []
    for c, b in enumerate(births):
        t = ChartTimeline(f"c{c}", b, BASE + 5 * c, BASE + 5 * c + n - 1)
        for u in units:
            t.states[u.members()[0].rid] = runs_series(rng, n, 0.2, 15)
        tls.append(t)
    return tls, units


def _naive_cov(tl, units_for, lo, hi):
    """pooled share of assessed class-days that are TRUE (weights: every member 1)."""
    tr = asd = 0
    for rid in units_for:
        w = tl.states[rid][lo - tl.h_start : hi - tl.h_start + 1]
        tr += int((w == 1).sum())
        asd += int((w >= 0).sum())
    return tr / asd


def test_T2_matches_a_naive_calculation_and_p2_matches_exact_enumeration():
    # a chart needs MIN_ELIGIBLE_DONORS = 5 other charts with covering horizons: use 7 charts
    births = [BASE - 9000 + 17 * c for c in range(7)]
    tls, units = _donor_world(1, births, n=365 * 6)
    eps = []
    for c, t in enumerate(tls):
        for yr in (1992, 1994):
            lo, hi = month_window(yr, 4 + (c % 6))
            eps.append(Episode(c, CAREER, C.FAVOURABLE, C.G2, lo, hi))
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    out = run_donor_check(ctx, eps, 20000, np.random.default_rng(3), age_matched=False)
    assert out["included_charts"] == list(range(7)) and out["excluded_charts"] == []
    rids = ["M0", "M2"]
    n = len(tls)
    V = []
    for c in range(n):
        mine = [e for e in eps if e.chart == c]
        donors = [d for d in range(n) if d != c]  # all horizons cover the 1992-94 windows
        vals = {}
        for d in donors + [c]:
            dev = []
            for e in mine:
                m_e = np.mean([_naive_cov(tls[x], rids, e.lo, e.hi) for x in donors])
                dev.append(_naive_cov(tls[d], rids, e.lo, e.hi) - m_e)
            vals[d] = float(np.mean(dev))
        V.append(([c] + donors, [vals[d] for d in [c] + donors]))
    T_naive = float(np.mean([v[1][0] for v in V]))
    assert out["T"] == pytest.approx(T_naive, abs=1e-9)
    # exact p over all donor combinations (7 charts, 7 choices each = 823,543 combinations)
    grids = np.meshgrid(*[np.asarray(v[1]) for v in V], indexing="ij")
    exact = np.mean(sum(grids) / n >= T_naive - 1e-12)
    assert abs(out["p"] - exact) < 0.012


def test_age_matched_check_reads_donors_at_the_same_age():
    # every chart's timeline is the SAME function of age; calendar dates differ. Age matching must see no difference.
    n = 365 * 16
    rng = np.random.default_rng(5)
    base_series = {f"M{k}": runs_series(rng, n + 4000, 0.2, 15) for k in range(4)}
    units = make_units([(f"U{k}", "promotive" if k % 2 == 0 else "obstructive", [[(f"M{k}", [C.GENERAL])]]) for k in range(4)])
    births = [BASE - 9000 + 311 * c for c in range(7)]
    tls = []
    for c, b in enumerate(births):
        t = ChartTimeline(f"c{c}", b, b + 3000, b + 3000 + n - 1)  # horizon = age 3000 days onward
        for k in range(4):
            t.states[f"M{k}"] = base_series[f"M{k}"][:n].copy()  # identical in the age frame
        tls.append(t)
    eps = []
    for c, t in enumerate(tls):
        for k in range(3):
            lo, hi = t.h_start + 400 + 900 * k, t.h_start + 400 + 900 * k + 2
            eps.append(Episode(c, CAREER, C.FAVOURABLE, C.G1, lo, hi))
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    rc = run_donor_check(ctx, eps, 200, np.random.default_rng(1), age_matched=True)
    assert rc["T"] == pytest.approx(0.0, abs=1e-12) and rc["p"] == 1.0  # nothing to tell the own chart from its age-mates
    rb = run_donor_check(ctx, eps, 200, np.random.default_rng(1), age_matched=False)
    assert rb["T"] != pytest.approx(0.0, abs=1e-6)  # calendar matching does see differences


def test_own_timeline_aligned_with_episodes_gives_the_smallest_possible_p2():
    births = [BASE - 9000 + 17 * c for c in range(8)]
    tls, units = _donor_world(2, births, n=365 * 8)
    eps = []
    for c, t in enumerate(tls):
        for k, yr in enumerate((1992, 1993, 1995)):
            lo, hi = month_window(yr, 1 + (3 * c + 5 * k) % 12)  # different months for different charts
            eps.append(Episode(c, CAREER, C.FAVOURABLE, C.G2, lo, hi))
            t.states["M0"][lo - t.h_start : hi - t.h_start + 1] = 1  # the own chart is TRUE in its own episode window
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    out = run_donor_check(ctx, eps, 999, np.random.default_rng(4), age_matched=False)
    assert out["p"] < 0.01


def test_chart_with_fewer_than_five_eligible_donors_is_left_out_and_listed():
    births = [BASE - 9000 + 17 * c for c in range(8)]
    tls, units = _donor_world(3, births, n=365 * 8)
    # shorten four charts so their horizons do not reach chart 0's late episode
    for c in (1, 2, 3, 4):
        t = tls[c]
        keep = 365 * 3
        t.h_end = t.h_start + keep - 1
        t.states = {k: v[:keep].copy() for k, v in t.states.items()}
    eps = []
    for c, t in enumerate(tls):
        lo, hi = month_window(1990 if c else 1996, 6)
        if c == 0:
            lo, hi = month_window(1996, 6)
        else:
            lo, hi = month_window(1990, 6 + (c % 5))
        eps.append(Episode(c, CAREER, C.FAVOURABLE, C.G2, lo, hi))
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    out = run_donor_check(ctx, eps, 100, np.random.default_rng(1), age_matched=False)
    assert 0 in out["excluded_charts"]  # only charts 5, 6, 7 reach 1996: 3 donors < 5
    assert 0 not in out["included_charts"]


# ── level under the null, power under a planted effect ──────────────────────────────────
def test_p_values_hold_their_level_under_the_null():
    rej = {"p1": 0, "p2": 0, "p3": 0, "p_dir": 0}
    seen = {k: 0 for k in rej}
    n_studies = 240
    ctx = None
    for study in range(n_studies):
        if study % 20 == 0:
            tls, units = toy_world(2000 + study // 20, n_charts=16, years=25)
            ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
        eps = random_episodes(np.random.default_rng(study), tls, 10, AREAS)
        r = score_family(ctx, eps, C.ScoreConfig(draws=300, seed=study))
        for k in rej:
            if r[k] is not None:  # p_dir is not testable below 100 episodes in 15 charts (v1.2 K4)
                seen[k] += 1
                rej[k] += r[k] <= 0.05
    for k, v in rej.items():
        assert seen[k] >= 0.8 * n_studies, (k, seen[k])
        assert v / seen[k] <= 0.10, (k, v / seen[k])  # nominal 5% (min-p is conservative); Monte Carlo band
    # and the tests are not dead: the mean rejection is not far below nominal for the single-statistic checks
    assert rej["p2"] / seen["p2"] > 0.01


def test_a_planted_effect_is_found():
    hits = 0
    for seed in range(6):
        tls, units = toy_world(30 + seed, n_charts=12, years=25, n_units=8)
        ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
        eps = planted_episodes(np.random.default_rng(seed), tls, units, 10, 0.5, AREAS)
        r = score_family(ctx, eps, C.ScoreConfig(draws=600, seed=seed))
        hits += r["p1"] <= 0.01 and r["p2"] <= 0.05 and r["p3"] <= 0.05
    assert hits >= 5


def test_Z25_sees_a_sparse_effect_better_than_T():
    z_better = 0
    for seed in range(6):
        tls, units = toy_world(60 + seed, n_charts=12, years=25, n_units=10)
        ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
        eps = planted_episodes(np.random.default_rng(seed), tls, units, 12, 0.7, AREAS, only_units=["U0"])
        r = score_family(ctx, eps, C.ScoreConfig(draws=600, seed=seed))
        z_better += r["p_stat"]["Z25-5y"] <= r["p_stat"]["T-5y"]
    assert z_better >= 5


def test_direction_check_separates_own_polarity_from_opposite():
    # an effect that lights both polarities equally is a timing association that is not direction-specific
    rng = np.random.default_rng(8)
    tls, units = toy_world(80, n_charts=18, years=25, n_units=8)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = planted_episodes(rng, tls, units, 12, 0.6, AREAS)
    r = score_family(ctx, eps, C.ScoreConfig(draws=600, seed=1))
    assert r["dir_testable"] and r["p_dir"] <= 0.05 and r["T_dir"] > 0
    # make every opposite-polarity member copy its own-polarity partner: no direction left to find
    for t in tls:
        for k in range(1, 8, 2):
            t.states[f"M{k}"] = t.states[f"M{k - 1}"].copy()
    ctx2 = FamilyContext(C.FAMILY_DASHA, tls, units)
    r2 = score_family(ctx2, eps, C.ScoreConfig(draws=600, seed=1))
    assert abs(r2["T_dir"]) < 0.02 and r2["p_dir"] > 0.05


# ── NOT_ASSESSED ───────────────────────────────────────────────────────────────────────
def test_not_assessed_stretch_makes_episodes_unscorable_and_shifts_avoid_it():
    rng = np.random.default_rng(3)
    n = 365 * 10
    u = make_units([("U0", "promotive", [[("M0", [C.GENERAL])]])])
    t = ChartTimeline("c0", BASE - 5000, BASE, BASE + n - 1)
    st = runs_series(rng, n, 0.25, 12)
    st[900:1500] = -1  # 600 days not assessed (a node-lord stretch, say)
    t.states["M0"] = st
    ctx = FamilyContext(C.FAMILY_DASHA, [t], u)
    inside = Episode(0, CAREER, C.FAVOURABLE, C.G2, *month_window(1992, 8))  # ~ day 940: inside the stretch
    ok1 = Episode(0, CAREER, C.FAVOURABLE, C.G2, *month_window(1991, 3))
    ok2 = Episode(0, CAREER, C.FAVOURABLE, C.G1, BASE + 200, BASE + 202)
    assert (inside.lo - BASE) in range(900, 1500)
    assert scorable_mask(ctx, [inside, ok1, ok2]) == [False, True, True]
    asm = assemble(ctx, "5y", [ok1, ok2], False, False)
    r = asm.recs[0]
    # a shift that would drop one of the episodes into the unassessed stretch is not drawn
    sh = r["shifts"]
    assert sh.size < (sh.max() - sh.min() + 1)
    for s in sh:
        for e in (ok1, ok2):
            w = st[e.lo - BASE + int(s) : e.hi - BASE + int(s) + 1]
            assert (w >= 0).sum() * 2 >= w.size  # at least half assessed at every drawn placement


def test_episode_whose_units_are_all_uninformative_is_not_scored():
    n = 365 * 8
    u = make_units([("U0", "promotive", [[("M0", [C.GENERAL])]]), ("U1", "obstructive", [[("M1", [C.GENERAL])]])])
    t = ChartTimeline("c0", BASE - 5000, BASE, BASE + n - 1)
    t.states["M0"] = np.zeros(n, dtype=np.int8)  # never on: no information
    t.states["M1"] = runs_series(np.random.default_rng(1), n, 0.3, 10)
    ctx = FamilyContext(C.FAMILY_DASHA, [t], u)
    fav = Episode(0, CAREER, C.FAVOURABLE, C.G2, *month_window(1991, 4))
    unf = Episode(0, CAREER, C.UNFAVOURABLE, C.G2, *month_window(1991, 4))
    assert scorable_mask(ctx, [fav, unf]) == [False, True]


# ── fallback consistency (v1.1 A7) ──────────────────────────────────────────────────────────
def test_fallback_direction_consistency_uses_the_nonschedulable_subset():
    """SUR-RB-55: the subset is a separate list (count_blind's primary_nonschedulable), not labels on the main list."""
    tls, units = toy_world(90, n_charts=12, years=25, n_units=8)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    rng = np.random.default_rng(2)
    base = random_episodes(rng, tls, 8, AREAS)
    # effect carried by the non-schedulable list: its T lies above the null mean 0.5
    eps_ns = planted_episodes(np.random.default_rng(3), tls, units, 8, 0.7, AREAS)
    cfg = C.ScoreConfig(draws=500, seed=1, fallback_primary_set=True)
    r = score_family(ctx, base, cfg, ns_episodes=eps_ns)
    assert r["nonschedulable_above_null_mean"] is True and r["T_nonschedulable"] > 0.5
    # a non-schedulable list without the effect: no excess
    noise = random_episodes(np.random.default_rng(4), tls, 8, AREAS)
    r2 = score_family(ctx, base, cfg, ns_episodes=noise)
    assert r2["T_nonschedulable"] < r["T_nonschedulable"] - 0.05
    assert "T_nonschedulable" not in score_family(ctx, base, C.ScoreConfig(draws=100, seed=1))


# ── regressions found by the Part F calibration ───────────────────────────────────────────────
def _patchy_world(seed, n_charts=14, years=40):
    """Each rule is silent (never TRUE) in about half of the 5-year blocks and active in the rest: an episode is
    scored only where its units are informative in its block, so scoring selects episodes by block activity."""
    rng = np.random.default_rng(seed)
    units = make_units([(f"U{k}", "promotive" if k % 2 == 0 else "obstructive", [[(f"M{k}", [C.GENERAL])]]) for k in range(6)])
    tls = []
    for c in range(n_charts):
        n = years * 365
        t = ChartTimeline(f"c{c}", BASE - 9000 + c, BASE + 7 * c, BASE + 7 * c + n - 1)
        for u in units:
            st = np.zeros(n, dtype=np.int8)
            for b0 in range(0, n, C.BLOCK_DAYS_5Y):
                if rng.random() < 0.5:
                    st[b0 : b0 + C.BLOCK_DAYS_5Y] = runs_series(rng, min(C.BLOCK_DAYS_5Y, n - b0), 0.3, 40)
            t.states[u.members()[0].rid] = st
        tls.append(t)
    return tls, units


def test_episodes_selected_by_block_activity_do_not_bias_the_15_year_scheme_or_checks_b_and_c():
    rej = {"T-15y": 0, "T-5y": 0, "p2": 0, "p3": 0}
    n_studies = 120
    ps2 = []
    for study in range(n_studies):
        if study % 20 == 0:
            tls, units = _patchy_world(500 + study // 20)
            ctx = FamilyContext(C.FAMILY_DASHA, tls, units)  # dasha family: 5-year and 15-year schemes
        eps = random_episodes(np.random.default_rng(study), tls, 10, AREAS)
        r = score_family(ctx, eps, C.ScoreConfig(draws=300, seed=study))
        rej["T-15y"] += r["p_stat"]["T-15y"] <= 0.05
        rej["T-5y"] += r["p_stat"]["T-5y"] <= 0.05
        rej["p2"] += r["p2"] <= 0.05
        rej["p3"] += r["p3"] <= 0.05
        ps2.append(r["p2"])
    for k, v in rej.items():
        assert v / n_studies <= 0.11, (k, v / n_studies)  # nominal 5%
    assert np.mean(ps2) > 0.3  # p2 is not piled up near zero


def test_each_scheme_scores_its_own_set_of_episodes():
    tls, units = _patchy_world(9)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = random_episodes(np.random.default_rng(1), tls, 12, AREAS)
    m5 = scorable_mask(ctx, eps, "5y")
    m15 = scorable_mask(ctx, eps, "15y")
    assert m5 != m15 and scorable_mask(ctx, eps) == m5  # the default is the primary scheme
    assert sum(m15) > sum(m5)  # a 15-year block holds activity somewhere in more places than a 5-year one
