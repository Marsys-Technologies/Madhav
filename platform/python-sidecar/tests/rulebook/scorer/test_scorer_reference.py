"""The scorer against an independent, deliberately naive re-implementation of the yardstick text.

The naive code below shares nothing with ``core`` except ``make_blocks`` (tested on its own): it ranks windows
by exact integer cross-multiplication, builds OR states day by day, and scores a translated episode from first
principles. Agreement is required on the observed T, on every valid shift's block contribution, on the unit
scores behind Z25, and on the direction statistic.
"""

from __future__ import annotations

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import FamilyContext, assemble, make_blocks, run_scheme, scorable_mask, score_family
from services.rulebook.scorer.model import ChartTimeline, Episode, MemberSpec, UnitSpec

from ._toy import BASE, month_window, runs_series

CAREER = "career_adv_change_entry"
ILLNESS = "illness_chronic_surgery"


def _spec(uid, pol, groups):
    gs = tuple(tuple(MemberSpec(r, frozenset(t)) for r, t in g) for g in groups)
    return UnitSpec(uid, C.FAMILY_DASHA, pol, "cluster", gs)


def _world(seed):
    rng = np.random.default_rng(seed)
    units = [
        _spec("S1", "promotive", [[("a1", [CAREER])]]),
        _spec("S2", "promotive", [[("a2", [C.GENERAL])]]),
        _spec("R1", "promotive", [[("r1", [CAREER]), ("r2", [CAREER, ILLNESS])]]),  # rival readings
        _spec("E1", "promotive", [[("e1", [CAREER])], [("e2", [CAREER])]]),  # disjoint claims, OR
        _spec("O1", "obstructive", [[("o1", [CAREER])]]),
        _spec("O2", "obstructive", [[("o2", [C.GENERAL])]]),
        _spec("O3", "obstructive", [[("o3", [ILLNESS])]]),
    ]
    tls = []
    for c in range(3):
        n = 365 * 13 + 40 * c
        t = ChartTimeline(f"c{c}", BASE - 9000 - 100 * c, BASE + 10 * c, BASE + 10 * c + n - 1)
        for u in units:
            for m in u.members():
                t.states[m.rid] = runs_series(rng, n, 0.25, 12, na_frac=0.05 if m.rid in ("r2", "a2") else 0.0)
        tls.append(t)
    return tls, units


def _episodes(rng, tls):
    eps = []
    for c, t in enumerate(tls):
        for k in range(7):
            area = CAREER if k % 3 else ILLNESS
            direction = C.FAVOURABLE if k % 2 == 0 else C.UNFAVOURABLE
            if k % 2:
                d = int(rng.integers(t.h_start + 5, t.h_end - 5))
                eps.append(Episode(c, area, direction, C.G1, d - 1, d + 1))
            else:
                while True:
                    from datetime import date

                    dd = date.fromordinal(int(rng.integers(t.h_start, t.h_end)))
                    lo, hi = month_window(dd.year, dd.month)
                    if lo >= t.h_start and hi <= t.h_end:
                        break
                eps.append(Episode(c, area, direction, C.G2, lo, hi))
    return eps


# ── naive scorer ──────────────────────────────────────────────────────────────────
def naive_pct(states, bl, bh, L, start):
    """Mid-rank percentile of the window at ``start`` among all windows of length L in [bl, bh]; None if undefined."""
    starts = range(bl, bh - L + 2)
    tr = np.array([int((states[s : s + L] == 1).sum()) for s in starts], dtype=np.int64)
    ad = np.array([int((states[s : s + L] >= 0).sum()) for s in starts], dtype=np.int64)
    ok = ad * 2 >= L
    if not ok.any():
        return None
    t, a = tr[ok], ad[ok]
    # all windows have the same coverage <=> every pair cross-multiplies equal
    if np.all(t[:, None] * a[None, :] == t[None, :] * a[:, None]):
        return None
    i = start - bl
    if not ok[i]:
        return None
    ti, ai = tr[i], ad[i]
    less = int(np.sum(t * ai < ti * a))
    eq = int(np.sum(t * ai == ti * a))
    return (less + 0.5 * eq) / t.size


def naive_reading_window(arrays, s, L):
    """(TRUE days, days) of an OR reading in window [s, s+L), SUR-RB-39 (1): only members at least half assessed in
    the window count; days = union of their assessed days; TRUE when any of them is TRUE. None if none passes."""
    passing = [a for a in arrays if int((a[s : s + L] >= 0).sum()) * 2 >= L]
    if not passing:
        return None
    tr = ad = 0
    for d in range(s, s + L):
        vals = [int(a[d]) for a in passing if a[d] >= 0]
        if vals:
            ad += 1
            tr += int(1 in vals)
    return tr, ad


def naive_reading_pct(arrays, bl, bh, L, start):
    starts = list(range(bl, bh - L + 2))
    w = [naive_reading_window(arrays, s, L) for s in starts]
    ref = [x for x in w if x is not None]
    if not ref:
        return None
    t = np.array([x[0] for x in ref], dtype=np.int64)
    a = np.array([x[1] for x in ref], dtype=np.int64)
    if np.all(t[:, None] * a[None, :] == t[None, :] * a[:, None]):
        return None
    me = w[start - bl]
    if me is None:
        return None
    ti, ai = me
    less = int(np.sum(t * ai < ti * a))
    eq = int(np.sum(t * ai == ti * a))
    return (less + 0.5 * eq) / t.size


def naive_unit_pct(unit, t, area, grade, bl, bh, L, start):
    groups = [[m for m in g if (area in m.area_tags or C.GENERAL in m.area_tags)] for g in unit.groups]
    groups = [g for g in groups if g]
    if not groups:
        return None
    if len(groups) == 1:
        ps = [naive_pct(t.states[m.rid], bl, bh, L, start) for m in groups[0]]
        ps = [p for p in ps if p is not None]
        return sum(ps) / len(ps) if ps else None
    assert all(len(g) == 1 for g in groups), "the naive OR handles singleton groups only"
    return naive_reading_pct([t.states[g[0].rid] for g in groups], bl, bh, L, start)


def naive_episode_score(units, t, ep, polarity, shift, scheme_block):
    lo, hi = ep.lo - t.h_start, ep.hi - t.h_start
    bl, bh = scheme_block
    a, b = max(lo, bl), min(hi, bh)
    L = b - a + 1
    start = a + shift
    ps = []
    for u in units:
        if u.polarity != polarity:
            continue
        p = naive_unit_pct(u, t, ep.area, ep.grade, bl, bh, L, start)
        if p is not None:
            ps.append(p)
    return (sum(ps) / len(ps)) if ps else None


def _block_of(ctx, ep):
    t = ctx.tl[ep.chart]
    mid = ((ep.lo - t.h_start) + (ep.hi - t.h_start)) // 2
    for bi, (bl, bh) in enumerate(make_blocks(t.n_days, C.BLOCK_DAYS_5Y, C.MERGE_BELOW_5Y)):
        if bl <= mid <= bh:
            return bi, (bl, bh)


@pytest.mark.parametrize("seed", [1, 2])
def test_observed_T_and_every_valid_shift_match_the_naive_scorer(seed):
    tls, units = _world(seed)
    eps = _episodes(np.random.default_rng(100 + seed), tls)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    mask = scorable_mask(ctx, eps)
    # the naive scorer decides scorability too
    for ep, ok in zip(eps, mask):
        bi, blk = _block_of(ctx, ep)
        nv = naive_episode_score(units, tls[ep.chart], ep, C.POLARITY_OF_DIRECTION[ep.direction], 0, blk)
        assert (nv is not None) == ok
    scored = [e for e, ok in zip(eps, mask) if ok]
    assert len(scored) >= 12
    asm = assemble(ctx, "5y", scored, True, False)
    per_chart = {}
    for e in scored:
        per_chart[e.chart] = per_chart.get(e.chart, 0) + 1
    nch = len(per_chart)
    # observed T
    T_naive = 0.0
    for e in scored:
        bi, blk = _block_of(ctx, e)
        T_naive += naive_episode_score(units, tls[e.chart], e, C.POLARITY_OF_DIRECTION[e.direction], 0, blk) / (nch * per_chart[e.chart])
    T_scorer = sum(r["BT"][r["i0"]] for r in asm.recs)
    assert T_scorer == pytest.approx(T_naive, abs=2e-6)
    # block contributions at several shifts (translated episodes), valid ones only
    checked = 0
    rng = np.random.default_rng(7)
    for r in asm.recs:
        eps_b = [e for e in scored if e.chart == r["chart"] and _block_of(ctx, e)[0] == r["blk"]]
        blk = ctx.blocks("5y", r["chart"])[r["blk"]]
        picks = {0, int(r["shifts"].min()), int(r["shifts"].max())} | {int(s) for s in rng.choice(r["shifts"], size=min(4, r["shifts"].size))}
        for s in sorted(picks):
            pos = np.nonzero(r["shifts"] == s)[0]
            assert pos.size == 1, "shift not in the valid list"
            want = 0.0
            for e in eps_b:
                v = naive_episode_score(units, tls[e.chart], e, C.POLARITY_OF_DIRECTION[e.direction], s, blk)
                assert v is not None  # valid shifts keep every episode scorable
                want += v / (nch * per_chart[e.chart])
            assert r["BT"][pos[0]] == pytest.approx(want, abs=2e-6)
            checked += 1
    assert checked >= 20


def test_shifts_that_would_leave_the_block_or_unscorable_positions_are_not_valid():
    tls, units = _world(3)
    eps = _episodes(np.random.default_rng(55), tls)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    scored = [e for e, ok in zip(eps, scorable_mask(ctx, eps)) if ok]
    asm = assemble(ctx, "5y", scored, True, False)
    for r in asm.recs:
        bl, bh = ctx.blocks("5y", r["chart"])[r["blk"]]
        eps_b = [e for e in scored if e.chart == r["chart"] and _block_of(ctx, e)[0] == r["blk"]]
        lows = []
        for e in eps_b:
            lo, hi = e.lo - tls[e.chart].h_start, e.hi - tls[e.chart].h_start
            a, b = max(lo, bl), min(hi, bh)
            lows.append((a, b))
        smin_all = max(bl - a for a, b in lows)
        smax_all = min(bh - b for a, b in lows)
        assert r["shifts"].min() >= smin_all and r["shifts"].max() <= smax_all  # never leaves the block
        assert r["shifts"][r["i0"]] == 0  # the observed placement is in the set
        # no wrap: every translated window lies wholly inside the block
        for s in (int(r["shifts"].min()), int(r["shifts"].max())):
            for a, b in lows:
                assert bl <= a + s and b + s <= bh


def test_unit_scores_behind_Z25_are_pooled_means_over_applicable_episodes():
    tls, units = _world(4)
    eps = _episodes(np.random.default_rng(66), tls)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    scored = [e for e, ok in zip(eps, scorable_mask(ctx, eps)) if ok]
    asm = assemble(ctx, "5y", scored, False, False)
    for p, uid in enumerate(asm.unit_ids):
        s = c = 0.0
        for r in asm.recs:
            if p in r["us"]:
                s += r["us"][p][0][r["i0"]]
                c += r["us"][p][1][r["i0"]]
        naive = []
        for e in scored:
            bi, blk = _block_of(ctx, e)
            u = ctx.unit_by_id[uid]
            if u.polarity != C.POLARITY_OF_DIRECTION[e.direction]:
                continue
            v = naive_unit_pct(u, tls[e.chart], e.area, e.grade, blk[0], blk[1], min(e.hi - tls[e.chart].h_start, blk[1]) - max(e.lo - tls[e.chart].h_start, blk[0]) + 1, max(e.lo - tls[e.chart].h_start, blk[0]) + 0)
            if v is not None:
                naive.append(v)
        assert int(c) == len(naive)
        if naive:
            assert s / c == pytest.approx(np.mean(naive), abs=2e-6)


def test_direction_statistic_is_own_minus_opposite_polarity_score():
    tls, units = _world(5)
    eps = _episodes(np.random.default_rng(77), tls)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    scored = [e for e, ok in zip(eps, scorable_mask(ctx, eps)) if ok]
    asm = assemble(ctx, "5y", scored, True, False)
    assert asm.has_dir
    dirs = []
    for e in scored:
        bi, blk = _block_of(ctx, e)
        own = naive_episode_score(units, tls[e.chart], e, C.POLARITY_OF_DIRECTION[e.direction], 0, blk)
        opp = naive_episode_score(units, tls[e.chart], e, C.POLARITY_OF_DIRECTION[C.OPPOSITE_DIRECTION[e.direction]], 0, blk)
        if opp is not None:
            dirs.append((e.chart, own - opp))
    by = {}
    for c, v in dirs:
        by.setdefault(c, []).append(v)
    want = np.mean([np.mean(v) for v in by.values()])
    got = sum(r["BD"][r["i0"]] for r in asm.recs)
    assert got == pytest.approx(want, abs=2e-6)


def test_T_weights_each_chart_once_however_many_episodes_it_has():
    tls, units = _world(6)
    eps = _episodes(np.random.default_rng(88), tls)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    scored = [e for e, ok in zip(eps, scorable_mask(ctx, eps)) if ok]
    base = sum(r["BT"][r["i0"]] for r in assemble(ctx, "5y", scored, False, False).recs)
    # duplicate every episode of chart 0: its weight inside T must not grow
    extra = [e for e in scored if e.chart == 0]
    both = sum(r["BT"][r["i0"]] for r in assemble(ctx, "5y", scored + extra, False, False).recs)
    assert both == pytest.approx(base, abs=1e-9)


def test_same_seed_same_answer_and_different_seed_different_draws():
    tls, units = _world(7)
    eps = _episodes(np.random.default_rng(99), tls)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    a = score_family(ctx, eps, C.ScoreConfig(draws=300, seed=5))
    b = score_family(FamilyContext(C.FAMILY_DASHA, tls, units), eps, C.ScoreConfig(draws=300, seed=5))
    c = score_family(ctx, eps, C.ScoreConfig(draws=300, seed=6))
    assert a == b
    # T does not depend on the draws; Z25 is standardised by them, so it does
    assert a["stats"]["T-5y"] == c["stats"]["T-5y"] and a["stats"]["T-15y"] == c["stats"]["T-15y"]
    assert a["null_mean"] != c["null_mean"]
