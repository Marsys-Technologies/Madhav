"""NO-SELECTION-ON-STATE invariant (SUR-RB-35; CLAUDE.md N.8 detector).

Permuting each member's TRUE/FALSE days within a chart (NOT_ASSESSED days fixed) changes nothing a rule "says",
but keeps every assessed mask, horizon, area tag and window. So every SELECTION the scorer and the harness make
before the statistics (which episodes are applicable, which charts are admitted by exclusion 5, which donors are
eligible for checks (b) and (c), the D7 counts for p_dir and Z25, the footprint inputs) must come out identical.
If one of them reads a TRUE/FALSE state, the permutation moves it and this test fails the build.

Carve-outs, by the yardstick's own definitions, each pinned by a test below so it cannot spread:
* the percentile-scored set inside check (a) (v1.0 3.2: a member identical in every window of its block is
  dropped) is state-dependent by definition; it is used only inside the statistic, whose null is conditional on it;
* the D8 footprint gate's touch RATES are state-defined (they measure busyness); its INPUTS are not, and it never
  sees an episode.
"""

from __future__ import annotations

import inspect
import types
from dataclasses import replace

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer import core
from services.rulebook.scorer.core import (
    FamilyContext,
    applicable_mask,
    d7_from_counts,
    direction_counts,
    donor_eligibility_counts,
    run_donor_check,
    scorable_mask,
    score_family,
    unit_applicable_counts,
)
from services.rulebook.scorer.footprint import family_testable, touch_rates
from services.rulebook.scorer.model import ChartTimeline, Episode, MemberSpec, UnitSpec
from services.rulebook.scorer_calib import harness as H

from ._toy import BASE, month_window, random_episodes, runs_series, toy_world

AREAS = ["career_adv_change_entry", "illness_chronic_surgery"]


# ── the permutation ────────────────────────────────────────────────────────────────────────────────
def permute_states(tls, seed):
    """Copy of the timelines with each member's TRUE/FALSE values shuffled over its assessed days."""
    rng = np.random.default_rng(seed)
    out = []
    for t in tls:
        st = {}
        for rid, a in t.states.items():
            b = a.copy()
            idx = np.nonzero(b >= 0)[0]
            b[idx] = b[idx][rng.permutation(idx.size)]
            st[rid] = b
        out.append(ChartTimeline(t.code, t.birth, t.h_start, t.h_end, st))
    return out


# ── configurations (including the shapes of the two defects already fixed) ─────────────────────────
def _unit(uid, pol, groups, plane=C.FAMILY_DASHA):
    gs = tuple(tuple(MemberSpec(r, frozenset(tags)) for r, tags in g) for g in groups)
    return UnitSpec(uid, plane, pol, "cluster" if len(gs) > 1 or len(gs[0]) > 1 else "conflict_free", gs)


def cfg_plain(seed):
    return toy_world(seed, n_charts=18, years=25, n_units=10)


def cfg_not_assessed(seed):
    return toy_world(seed, n_charts=18, years=25, n_units=10, na_frac=0.08)  # NOT_ASSESSED stretches (node-lord days, C2 masks)


def cfg_patchy(seed):
    """Defect shape 1 and 2: rules silent in about half of the 5-year blocks (block activity drives scoring)."""
    rng = np.random.default_rng(seed)
    units = [_unit(f"U{k}", "promotive" if k % 2 == 0 else "obstructive", [[(f"M{k}", [C.GENERAL] if k % 3 == 0 else [AREAS[k % 2]])]]) for k in range(10)]
    tls = []
    for c in range(18):
        n = 40 * 365
        t = ChartTimeline(f"c{c}", BASE - 9000 + 37 * c, BASE + 11 * c, BASE + 11 * c + n - 1)
        for u in units:
            st = np.zeros(n, dtype=np.int8)
            for b0 in range(0, n, C.BLOCK_DAYS_5Y):
                if rng.random() < 0.5:
                    st[b0 : b0 + C.BLOCK_DAYS_5Y] = runs_series(rng, min(C.BLOCK_DAYS_5Y, n - b0), 0.3, 40)
            if rng.random() < 0.3:
                s0 = int(rng.integers(0, n - 600))
                st[s0 : s0 + 500] = -1
            t.states[u.members()[0].rid] = st
        tls.append(t)
    return tls, units


def cfg_clusters(seed):
    """Rival groups, disjoint OR groups, area-filtered members, an always-TRUE member of another area."""
    rng = np.random.default_rng(seed)
    units = [
        _unit("R1", "promotive", [[("r1", [AREAS[0]]), ("r2", [AREAS[0], AREAS[1]])]]),
        _unit("E1", "promotive", [[("e1", [AREAS[0]])], [("e2", [AREAS[1]])]]),
        _unit("X1", "promotive", [[("x1", [AREAS[0]]), ("x2", [AREAS[0]])], [("x3", [C.GENERAL])]]),
        _unit("O1", "obstructive", [[("o1", [C.GENERAL])]]),
        _unit("O2", "obstructive", [[("o2", [AREAS[1]])], [("o3", [AREAS[0]])]]),
    ] + [_unit(f"G{k}", "promotive" if k % 2 else "obstructive", [[(f"g{k}", [C.GENERAL])]]) for k in range(6)]
    tls = []
    for c in range(18):
        n = 30 * 365 - 97 * c  # different horizons: donor eligibility varies
        t = ChartTimeline(f"c{c}", BASE - 7000 - 211 * c, BASE + 13 * c, BASE + 13 * c + n - 1)
        for u in units:
            for m in u.members():
                t.states[m.rid] = runs_series(rng, n, 0.2, 18, na_frac=0.04 if m.rid in ("r2", "x2") else 0.0)
        t.states["e2"] = np.ones(n, dtype=np.int8)  # defective: always TRUE
        tls.append(t)
    return tls, units


CONFIGS = {"plain": cfg_plain, "not_assessed": cfg_not_assessed, "patchy": cfg_patchy, "clusters": cfg_clusters}


def _episodes(tls, seed, per_chart=14):
    eps = random_episodes(np.random.default_rng(seed), tls, per_chart, AREAS + ["other"])
    # a few windows straddling NOT_ASSESSED stretches and horizon-late windows
    return eps


# ── every selection stage, as data ───────────────────────────────────────────────────────────────────
def _as_transit(units):
    return [replace(u, plane=C.FAMILY_TRANSIT) for u in units]


def selection_stages(tls, units, eps, gate_drop):
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units, gate_drop)
    ctx_t = FamilyContext(C.FAMILY_TRANSIT, tls, _as_transit(units), gate_drop)
    out = {}
    out["applicable"] = applicable_mask(ctx, eps)
    out["unit_applicable_counts"] = unit_applicable_counts(ctx, [e for e, ok in zip(eps, out["applicable"]) if ok])
    out["d7"] = d7_from_counts(ctx, eps)
    out["direction"] = direction_counts(ctx, [e for e, ok in zip(eps, out["applicable"]) if ok])
    # exclusion 5 per family (v1.2 K8), every candidate threshold, through the harness's own admission code
    fake = types.SimpleNamespace(ctx={C.FAMILY_DASHA: ctx, C.FAMILY_TRANSIT: ctx_t})
    for thr in (3, 5, 8):
        kept, adm = H.Calibration.admit(fake, {C.FAMILY_DASHA: eps, C.FAMILY_TRANSIT: eps}, thr)
        out[f"admitted_{thr}"] = {f: (tuple(adm[f]), len(kept[f])) for f in adm}
    # donor eligibility for (b) and (c), counts and the actual included / excluded charts
    out["donor_counts"] = donor_eligibility_counts(ctx, eps)
    for name, age in (("b", False), ("c", True)):
        r = run_donor_check(ctx, eps, 5, np.random.default_rng(0), age)
        out[f"donors_{name}"] = (tuple(r["included_charts"]), tuple(r["excluded_charts"]))
    # D7 testability, from counts and horizons
    ft = family_testable(ctx, eps, min_episodes=50, min_charts=10)
    out["testable"] = {k: v for k, v in ft.items() if k != "reasons"}
    # what score_family itself reports for the D7 decisions (p_dir eligibility, Z25 unit set, donor floors)
    sf = score_family(ctx, eps, C.ScoreConfig(draws=20, seed=1))
    out["score_family_d7"] = (sf.get("dir_testable"), sf.get("dir_episodes"), sf.get("dir_charts"), sf.get("z25_units"), sf.get("b_charts"), sf.get("c_charts"), sf.get("donor_floor_ok"))
    # footprint INPUTS: which units and window classes are measured, over which horizons (the rates are state-defined)
    out["footprint_inputs"] = (tuple(sorted(u.unit_id for u in ctx.units)), tuple(sorted(C.WINDOW_CLASS_OF_GRADE.values())), tuple((t.h_start, t.h_end) for t in tls))
    return out


@pytest.mark.parametrize("config", sorted(CONFIGS))
@pytest.mark.parametrize("seed", [1, 2])
def test_no_selection_stage_reads_a_true_false_state(config, seed):
    tls, units = CONFIGS[config](seed)
    eps = _episodes(tls, 100 + seed)
    # a fixed gate (the footprint gate is state-defined by D8; hold it fixed so the selections can be compared)
    gate = {units[0].unit_id: frozenset({C.G1})}
    base = selection_stages(tls, units, eps, gate)
    for k in range(3):
        perm = selection_stages(permute_states(tls, 1000 * seed + k), units, eps, gate)
        for stage in base:
            assert perm[stage] == base[stage], f"{config}/seed {seed}/perm {k}: stage '{stage}' moved when only TRUE/FALSE states moved"
    # the selections are not trivially empty
    assert sum(base["applicable"]) > 50
    assert base["donor_counts"]["b"] > 0 and any(v[0] for v in base["admitted_3"].values())


# ── the detector is live: it catches the defect class ───────────────────────────────────────────────────
def test_the_permutation_moves_state_dependent_sets_so_the_detector_can_fail():
    tls, units = cfg_patchy(5)
    eps = _episodes(tls, 7)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    ctxp = FamilyContext(C.FAMILY_DASHA, permute_states(tls, 9), units)
    # the percentile-scored set DOES move: an admission rule built on it (the simulation error found in Part F)
    # would fail the invariant above
    assert scorable_mask(ctx, eps) != scorable_mask(ctxp, eps)
    def old_exclusion5_counts(c):  # per-chart "usable" counts on the scored set: the defective admission input
        n = {}
        for e, ok in zip(eps, scorable_mask(c, eps)):
            n[e.chart] = n.get(e.chart, 0) + int(ok)
        return n

    assert old_exclusion5_counts(ctx) != old_exclusion5_counts(ctxp)
    # and the old check (b)/(c) episode set (the percentile-scored set) would move the donor-check inputs too
    assert [e for e, ok in zip(eps, scorable_mask(ctx, eps)) if ok] != [e for e, ok in zip(eps, scorable_mask(ctxp, eps)) if ok]


# ── carve-outs pinned ─────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "fn",
    [applicable_mask, unit_applicable_counts, d7_from_counts, direction_counts, donor_eligibility_counts, family_testable, H.Calibration.admit],
)
def test_no_selection_function_calls_the_percentile_scored_set(fn, monkeypatch):
    """N.8: the state-dependent scored set may feed only the statistics. Every selection runs with it disabled."""

    def boom(*a, **k):
        raise AssertionError(f"{fn.__name__} reached scorable_mask: a selection depends on TRUE/FALSE states")

    monkeypatch.setattr(core, "scorable_mask", boom)
    import services.rulebook.scorer.footprint as F

    monkeypatch.setattr(F, "scorable_mask", boom, raising=False)
    tls, units = cfg_clusters(3)
    eps = _episodes(tls, 3)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    if fn is H.Calibration.admit:
        fake = types.SimpleNamespace(ctx={C.FAMILY_DASHA: ctx, C.FAMILY_TRANSIT: FamilyContext(C.FAMILY_TRANSIT, tls, _as_transit(units))})
        fn(fake, {C.FAMILY_DASHA: eps, C.FAMILY_TRANSIT: eps}, 5)
    elif fn in (unit_applicable_counts, direction_counts):
        fn(ctx, [e for e, ok in zip(eps, applicable_mask(ctx, eps)) if ok])
    else:
        fn(ctx, eps)


def test_footprint_gate_never_sees_an_episode():
    """D8: the touch rates are state-defined but computed from timelines and units alone, before any episode."""
    params = list(inspect.signature(touch_rates).parameters)
    assert params == ["timelines", "units"]
    from services.rulebook.scorer.footprint import build_family_context

    assert list(inspect.signature(build_family_context).parameters) == ["family", "timelines", "units"]


def test_a_member_constant_after_permutation_stays_constant():
    """Sanity of the permutation itself: counts of TRUE, FALSE and NOT_ASSESSED per member are preserved."""
    tls, units = cfg_not_assessed(4)
    p = permute_states(tls, 1)
    for a, b in zip(tls, p):
        for rid in a.states:
            for code in (-1, 0, 1):
                assert int((a.states[rid] == code).sum()) == int((b.states[rid] == code).sum())
            assert np.array_equal(a.states[rid] == -1, b.states[rid] == -1)
