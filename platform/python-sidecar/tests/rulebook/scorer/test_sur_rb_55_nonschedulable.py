"""SUR-RB-55: the fallback direction-consistency statistic is T on a SEPARATELY formed non-schedulable episode list
(count_blind's primary_nonschedulable: drop schedulable occurrences before the horizon trim and the merge). It is used
for nothing else; its condition is T above 0.5 (the null mean, v1.0 section 3.2 step 4); an empty scored list fails
closed. Before the claim the list goes through the same edge rules and its per-chart aggregates must equal
count_blind's primary_nonschedulable rows."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import FamilyContext, score_family
from services.rulebook.scorer.model import Episode
from services.rulebook.scorer.outcome import LABEL_CHOSEN_DATES, MIDDLE, STRONG, decide
from services.rulebook.scorer.runner import RunRefused, prepare_episodes, recount_rows

from ._toy import planted_episodes, random_episodes, toy_world
from .test_review_fixes import AREAS, _cfg, _claims, _lock, _two_families, lockfiles, score_sample  # noqa: F401  (fixture re-used)


def _world(seed=90):
    tls, units = toy_world(seed, n_charts=12, years=25, n_units=8)
    return FamilyContext(C.FAMILY_DASHA, tls, units), tls, units


def test_the_statistic_is_T_on_the_separate_list_and_the_flags_on_the_main_list_are_ignored():
    ctx, tls, units = _world()
    main = random_episodes(np.random.default_rng(2), tls, 8, AREAS)
    ns = planted_episodes(np.random.default_rng(3), tls, units, 8, 0.7, AREAS)
    cfg = C.ScoreConfig(draws=200, seed=1, fallback_primary_set=True)
    r = score_family(ctx, main, cfg, ns_episodes=ns)
    alone = score_family(ctx, ns, C.ScoreConfig(draws=50, seed=1))  # T of the list itself, as v1.0 section 3.2
    assert r["T_nonschedulable"] == pytest.approx(alone["T"], abs=1e-12)
    assert r["nonschedulable_above_null_mean"] is (alone["T"] > 0.5) and r["nonschedulable_above_null_mean"] is True
    assert r["nonschedulable_episodes_scored"] == alone["episodes_scored"]
    # schedulable labels on the main episodes play no part any more
    flipped = [replace(e, schedulable=not e.schedulable) for e in main]
    r2 = score_family(ctx, flipped, cfg, ns_episodes=ns)
    assert r2["T_nonschedulable"] == r["T_nonschedulable"]


def test_the_separate_list_changes_nothing_else():
    ctx, tls, units = _world()
    main = planted_episodes(np.random.default_rng(4), tls, units, 8, 0.4, AREAS)
    ns_a = random_episodes(np.random.default_rng(5), tls, 6, AREAS)
    ns_b = planted_episodes(np.random.default_rng(6), tls, units, 6, 0.9, AREAS)
    cfg = C.ScoreConfig(draws=200, seed=1, fallback_primary_set=True)
    ra = score_family(ctx, main, cfg, ns_episodes=ns_a)
    rb = score_family(ctx, main, cfg, ns_episodes=ns_b)
    for k in ("T", "p1", "p2", "p3", "p_dir", "T2", "T3", "stats", "z25_units", "episodes_scored", "donor_floor_ok", "dir_testable"):
        assert ra[k] == rb[k], k
    assert ra["T_nonschedulable"] != rb["T_nonschedulable"]


def test_the_null_mean_is_exactly_one_half_and_an_empty_list_fails_closed(monkeypatch):
    ctx, tls, units = _world()
    main = random_episodes(np.random.default_rng(2), tls, 8, AREAS)
    cfg = C.ScoreConfig(draws=100, seed=1, fallback_primary_set=True)
    for ns in (None, []):
        r = score_family(ctx, main, cfg, ns_episodes=ns)
        assert r["nonschedulable_above_null_mean"] is False and r["T_nonschedulable"] is None and r["nonschedulable_episodes_scored"] == 0
    # a list with nothing scored (here: only charts outside the admitted set) fails closed too
    from services.rulebook.scorer.core import nonschedulable_statistic

    ns0 = planted_episodes(np.random.default_rng(3), tls, units, 8, 0.7, AREAS)
    only0 = [e for e in ns0 if e.chart == 0]
    r = nonschedulable_statistic(ctx, only0, cfg, admitted=[1, 2, 3])
    assert r == {"T_nonschedulable": None, "nonschedulable_episodes_scored": 0, "nonschedulable_above_null_mean": False}
    assert nonschedulable_statistic(ctx, only0, cfg, admitted=[0])["nonschedulable_episodes_scored"] > 0
    # exactly 0.5 is NOT above the null mean
    import services.rulebook.scorer.core as core

    real = core.run_scheme

    def half(ctx_, scheme, eps, draws, rng, want_dir, want_fallback, z25_units=None, dir_eligible=None):
        res = real(ctx_, scheme, eps, draws, rng, want_dir, want_fallback, z25_units, dir_eligible)
        res.pools["T"] = np.full_like(res.pools["T"], 0.5)
        return res

    ns = planted_episodes(np.random.default_rng(3), tls, units, 8, 0.7, AREAS)
    monkeypatch.setattr(core, "run_scheme", half)
    assert score_family(ctx, main, cfg, ns_episodes=ns)["nonschedulable_above_null_mean"] is False
    assert C.NONSCHEDULABLE_NULL_MEAN == 0.5


def test_without_the_fallback_no_statistic_is_computed():
    ctx, tls, units = _world()
    main = random_episodes(np.random.default_rng(2), tls, 8, AREAS)
    r = score_family(ctx, main, C.ScoreConfig(draws=50, seed=1), ns_episodes=main)
    assert "T_nonschedulable" not in r and "nonschedulable_above_null_mean" not in r


def test_a_failed_condition_turns_strong_into_middle_with_the_label():
    r = {"p1": 0.001, "p2": 0.01, "p3": 0.01, "p_dir": 0.01, "dir_testable": True, "nonschedulable_above_null_mean": False}
    v = decide({"dasha": r}, {"dasha": True}, fallback_primary_set=True)
    assert v["outcome"] == MIDDLE and LABEL_CHOSEN_DATES in v["labels"]
    v2 = decide({"dasha": dict(r, nonschedulable_above_null_mean=True)}, {"dasha": True}, fallback_primary_set=True)
    assert v2["outcome"] == STRONG


# ── the runner: the list travels in the lock, is validated, and its aggregates must equal count_blind's ──────
def _ns_world(lock, ctx, eps):
    """A separately formed list per family (here: a different random subset) and its count_blind-format rows."""
    ns, rows = {}, {}
    for f, c in ctx.items():
        sub = [e for i, e in enumerate(eps[f]) if i % 3 == 0]
        ns[f] = sub
        kept, _ = prepare_episodes(c, sub)
        rows[f] = [{"chart_id": k[0], "area": k[1], "direction": k[2], "grade": k[3], **v} for k, v in recount_rows(c, kept).items()]
    return replace(lock, fallback_primary_set=True, count_set="all", nonschedulable_episodes=ns, nonschedulable_count_rows=rows)


def test_the_runner_scores_the_list_from_the_lock(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _ns_world(_lock(ctx, eps, lockfiles, tmp_path), ctx, eps)
    res = score_sample(ctx, eps, _cfg(fallback_primary_set=True), lock)
    for f in ctx:
        if f in res.get("families", {}):
            fr = res["families"][f]
            assert fr["nonschedulable_episodes_scored"] > 0 and fr["T_nonschedulable"] is not None
    assert len(_claims(tmp_path)) == 1


@pytest.mark.parametrize("break_it,msg", [
    ("rows", "primary_nonschedulable"),
    ("episode", "primary_nonschedulable"),
    ("missing_list", "non-schedulable episode list"),
    ("missing_rows", "non-schedulable episode list"),
    ("no_fallback", "only with the A7 fallback"),
])
def test_the_runner_refuses_before_the_claim(tmp_path, lockfiles, break_it, msg):
    ctx, eps = _two_families()
    lock = _ns_world(_lock(ctx, eps, lockfiles, tmp_path), ctx, eps)
    cfg = _cfg(fallback_primary_set=True)
    if break_it == "rows":
        rows = {f: [dict(r) for r in v] for f, v in lock.nonschedulable_count_rows.items()}
        rows[C.FAMILY_DASHA][0]["episodes"] += 1
        lock = replace(lock, nonschedulable_count_rows=rows)
    elif break_it == "episode":
        ns = {f: list(v) for f, v in lock.nonschedulable_episodes.items()}
        ns[C.FAMILY_TRANSIT] = ns[C.FAMILY_TRANSIT][:-1]
        lock = replace(lock, nonschedulable_episodes=ns)
    elif break_it == "missing_list":
        ns = dict(lock.nonschedulable_episodes)
        ns.pop(C.FAMILY_DASHA)
        lock = replace(lock, nonschedulable_episodes=ns)
    elif break_it == "missing_rows":
        lock = replace(lock, nonschedulable_count_rows={})
    elif break_it == "no_fallback":
        lock = replace(lock, fallback_primary_set=False, count_set="primary_nonschedulable")
        cfg = _cfg()
    with pytest.raises(RunRefused, match=msg):
        score_sample(ctx, eps, cfg, lock)
    assert _claims(tmp_path) == []


def test_the_list_goes_through_the_same_edge_rules(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _ns_world(_lock(ctx, eps, lockfiles, tmp_path), ctx, eps)
    t = ctx[C.FAMILY_DASHA].tl[0]
    mixed = Episode(0, AREAS[0], "mixed", C.G2, *_month_inside(t))
    ns = {f: list(v) + ([mixed] if f == C.FAMILY_DASHA else []) for f, v in lock.nonschedulable_episodes.items()}
    res = score_sample(ctx, eps, _cfg(fallback_primary_set=True), replace(lock, nonschedulable_episodes=ns))
    assert res["validation_drops_nonschedulable"][C.FAMILY_DASHA]["dropped_mixed"] == 1


def _month_inside(t):
    from datetime import date

    d = date.fromordinal(t.h_start + 400)
    from ._toy import month_window

    return month_window(d.year, d.month)
