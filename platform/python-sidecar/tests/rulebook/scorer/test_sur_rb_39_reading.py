"""SUR-RB-39 (1) and (2). Full ruling: (1) masks-only reading rule for coverage, percentiles and D8; (2) the own chart's applicable unit set
defines the (b)/(c) coverage and donor eligibility; (3) p_dir averages only episodes with defined own and opposite
scores; (4) the q = 30% sanity check per testable family, with the q-curve on a shortfall."""

from __future__ import annotations

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import FamilyContext, assemble, donor_sets, reading_coverage, run_donor_check, scorable_mask
from services.rulebook.scorer.footprint import unit_touch
from services.rulebook.scorer.model import ChartTimeline, Episode, MemberSpec, UnitSpec

from ._toy import BASE, month_window, runs_series

CAREER = "career_adv_change_entry"


def _unit(uid, groups, pol="promotive", tags=None):
    gs = tuple(tuple(MemberSpec(r, frozenset(tags or [C.GENERAL])) for r in g) for g in groups)
    return UnitSpec(uid, C.FAMILY_DASHA, pol, "cluster", gs)


# ── (1) the reading rule, in percentiles and in D8 ────────────────────────────────────────────────────────
def test_1_or_unit_percentile_uses_only_members_that_pass_and_their_union():
    n = 365 * 6
    rng = np.random.default_rng(1)
    a = runs_series(rng, n, 0.25, 10)
    b = runs_series(rng, n, 0.25, 10)
    b[400:800] = -1  # B not assessed over a stretch: windows there are scored on A alone
    t = ChartTimeline("c", BASE - 9000, BASE, BASE + n - 1, {"A": a, "B": b})
    ctx = FamilyContext(C.FAMILY_DASHA, [t], [_unit("E", [["A"], ["B"]])])
    cov = ctx.comp_coverage("5y", 0, 0, 3, ("or", ("A", "B")))
    for s in (100, 500, 700, 1000):
        w_a, w_b = a[s : s + 3], b[s : s + 3]
        passing = [w for w in (w_a, w_b) if (w >= 0).sum() * 2 >= 3]
        days = np.zeros(3, bool)
        true = np.zeros(3, bool)
        for w in passing:
            days |= w >= 0
            true |= w == 1
        assert cov[s] == pytest.approx(true.sum() / days.sum())


def test_1_r_unit_averages_over_the_members_that_pass():
    n = 365 * 6
    rng = np.random.default_rng(2)
    a, b = runs_series(rng, n, 0.25, 10), runs_series(rng, n, 0.25, 10)
    b[300:900] = -1
    t = ChartTimeline("c", BASE - 9000, BASE, BASE + n - 1, {"A": a, "B": b})
    ctx = FamilyContext(C.FAMILY_DASHA, [t], [_unit("R", [["A", "B"]])])
    v = ctx.units[0].variant(CAREER, True)
    u = ctx.unit_curve("5y", 0, 0, 3, v)
    pa, pb = ctx.comp_curve("5y", 0, 0, 3, ("m", "A")), ctx.comp_curve("5y", 0, 0, 3, ("m", "B"))
    assert np.isnan(pb[500]) and u[500] == pytest.approx(pa[500])  # B does not pass: A alone
    both = 1200
    assert u[both] == pytest.approx((pa[both] + pb[both]) / 2)


def test_1_d8_touch_uses_the_same_rule():
    n = 600
    a = np.zeros(n, dtype=np.int8)
    b = np.full(n, -1, dtype=np.int8)
    b[::3] = 1  # B is TRUE often but never half assessed in any 3-day window: it never passes
    t = ChartTimeline("c", BASE, BASE, BASE + n - 1, {"A": a, "B": b})
    assert unit_touch(t, _unit("E", [["A"], ["B"]]), "3d") == 0.0  # Kleene OR would have touched every window
    b2 = np.full(n, -1, dtype=np.int8)
    b2[100:103] = 1  # B passes in one window, TRUE there
    t2 = ChartTimeline("c", BASE, BASE, BASE + n - 1, {"A": a, "B": b2})
    r = unit_touch(t2, _unit("E", [["A"], ["B"]]), "3d")
    assert 0 < r < 0.02


def test_1_true_na_and_false_na_days_in_the_scorer_and_in_d8():
    # TRUE/N reads TRUE, FALSE/N reads FALSE, never NOT_ASSESSED, for a reading whose members both pass
    a = np.array([1, 0, 0, 0, 0, 0], dtype=np.int8)
    b = np.array([-1, -1, 0, 0, 0, 0], dtype=np.int8)
    assert reading_coverage([a, b], np.array([0]), 4)[0] == pytest.approx(1 / 4)
    a2 = np.array([0, 0, 0, 0, 0, 0], dtype=np.int8)
    assert reading_coverage([a2, b], np.array([0]), 4)[0] == 0.0
    t = ChartTimeline("c", BASE, BASE, BASE + 5, {"A": a, "B": b})
    assert unit_touch(t, _unit("E", [["A"], ["B"]]), "3d") == pytest.approx(1 / 4)  # windows 0..3: only the first touched


# ── (2) the own chart's applicable unit set defines the (b)/(c) coverage and eligibility ───────────────────
def test_2_a_unit_not_applicable_on_the_own_chart_is_left_out_of_every_coverage():
    rng = np.random.default_rng(3)
    n = 365 * 12
    units = [_unit("U1", [["M1"]]), _unit("U2", [["M2"]])]
    tls = []
    for c in range(8):
        t = ChartTimeline(f"c{c}", BASE - 9000 + c, BASE, BASE + n - 1, {"M1": runs_series(rng, n, 0.2, 12), "M2": runs_series(rng, n, 0.2, 12)})
        tls.append(t)
    lo, hi = month_window(1993, 5)
    tls[0].states["M2"][lo - BASE : hi - BASE + 1] = -1  # U2 does not apply to chart 0's episode on chart 0
    for c in range(1, 8):
        tls[c].states["M2"][lo - BASE : hi - BASE + 1] = 1  # ... while every donor's U2 is fully TRUE there
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = [Episode(0, CAREER, C.FAVOURABLE, C.G2, lo, hi)] + [Episode(c, CAREER, C.FAVOURABLE, C.G2, *month_window(1994, c)) for c in range(1, 8)]
    d = donor_sets(ctx, eps, False)[0]
    assert [v.unit_id for v in d["units"][0]] == ["U1"]  # the own chart's applicable set
    choices = np.concatenate([[0], d["elig"]])
    cov = ctx.episode_coverage(d["units"][0], d["dlo"][0][choices], d["dhi"][0][choices], choices)
    want = [(tls[c].states["M1"][lo - BASE : hi - BASE + 1] == 1).mean() for c in choices]
    assert np.allclose(cov, want)  # U2 (fully TRUE on donors) never enters
    r = run_donor_check(ctx, eps, 50, np.random.default_rng(1), False)
    assert 0 in r["included_charts"]


def test_2_a_donor_needs_every_unit_of_the_own_set_defined():
    rng = np.random.default_rng(4)
    n = 365 * 12
    units = [_unit("U1", [["M1"]]), _unit("U2", [["M2"]])]
    tls = [ChartTimeline(f"c{c}", BASE - 9000 + c, BASE, BASE + n - 1, {"M1": runs_series(rng, n, 0.2, 12), "M2": runs_series(rng, n, 0.2, 12)}) for c in range(8)]
    lo, hi = month_window(1993, 5)
    tls[5].states["M2"][lo - BASE : hi - BASE + 1] = -1  # donor 5: U2 undefined in chart 0's window
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = [Episode(0, CAREER, C.FAVOURABLE, C.G2, lo, hi)]
    assert 5 not in donor_sets(ctx, eps, False)[0]["elig"]
    tls[0].states["M2"][lo - BASE : hi - BASE + 1] = -1  # now U2 is not in the OWN set: donor 5 needs U1 only
    ctx2 = FamilyContext(C.FAMILY_DASHA, tls, units)
    assert 5 in donor_sets(ctx2, eps, False)[0]["elig"]


