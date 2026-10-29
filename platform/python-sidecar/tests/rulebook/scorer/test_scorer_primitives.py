"""Scorer primitives: blocks, percentiles, OR, p-values, min-p, Holm, outcome rule, MDE, instability mask."""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import make_blocks, min_p_adjusted, or_values, percentile_curve, pool_p, pool_p_all
from services.rulebook.scorer.model import ScorerError, mask_unstable
from services.rulebook.scorer.outcome import (
    CHANCE,
    LABEL_CHOSEN_DATES,
    LABEL_INCLUDES_CHOSEN,
    LABEL_NOT_DIRECTION,
    MIDDLE,
    STRONG,
    decide,
    holm_adjust,
    mde_from_power,
    mde_report,
)


def _prefix(states):
    a = np.asarray(states)
    ok = a >= 0
    T = np.concatenate([[0.0], np.cumsum(np.where(ok, a, 0).astype(float))])
    A = np.concatenate([[0.0], np.cumsum(ok.astype(float))])
    return T, A


# ── blocks ───────────────────────────────────────────────────────────────────
def test_blocks_basic_and_final_merge():
    assert make_blocks(1826, 1826, 913) == [(0, 1825)]
    assert make_blocks(1826 * 2, 1826, 913) == [(0, 1825), (1826, 3651)]
    # remainder 912 (< 913) merges into the previous block; 913 stands alone
    assert make_blocks(1826 + 912, 1826, 913) == [(0, 1825 + 912)]
    assert make_blocks(1826 + 913, 1826, 913) == [(0, 1825), (1826, 2738)]
    # a horizon shorter than one block is one block, however short
    assert make_blocks(400, 1826, 913) == [(0, 399)]
    assert make_blocks(0, 1826, 913) == []


def test_blocks_cover_every_day_exactly_once():
    for n in (1, 913, 1826, 1827, 2738, 2739, 3652, 9000, 20000):
        for bd, mb in ((1826, 913), (5479, 2739)):
            bl = make_blocks(n, bd, mb)
            days = [d for a, b in bl for d in range(a, b + 1)]
            assert days == list(range(n))


# ── percentile curve: the definition, checked against a brute-force reference ─
def _brute_pct(states, bl, bh, L):
    from fractions import Fraction

    covs = []
    for s in range(bl, bh - L + 2):
        w = states[s : s + L]
        asses = int((w >= 0).sum())
        covs.append(None if asses * 2 < L else Fraction(int((w == 1).sum()), asses))
    ref = [c for c in covs if c is not None]
    out = []
    for c in covs:
        if c is None or len(set(ref)) <= 1:
            out.append(np.nan)
        else:
            out.append((sum(1 for r in ref if r < c) + 0.5 * sum(1 for r in ref if r == c)) / len(ref))
    return np.array(out)


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("L", [3, 31, 17])
def test_percentile_curve_matches_brute_force(seed, L):
    rng = np.random.default_rng(seed)
    n = 240
    st = (rng.random(n) < 0.3).astype(np.int8)
    if seed % 2:
        st[rng.integers(0, n, 40)] = -1  # NOT_ASSESSED days
    T, A = _prefix(st)
    got = percentile_curve(T, A, 20, 220, L)
    want = _brute_pct(st, 20, 220, L)
    assert got.shape == want.shape
    assert np.allclose(got, want, atol=1e-6, equal_nan=True)


def test_percentile_mean_is_exactly_one_half_under_ties():
    rng = np.random.default_rng(3)
    st = (rng.random(500) < 0.2).astype(np.int8)  # many tied coverages at L=3
    T, A = _prefix(st)
    c = percentile_curve(T, A, 0, 499, 3)
    assert abs(np.nanmean(c.astype(np.float64)) - 0.5) < 1e-6


def test_member_identical_in_every_window_is_dropped():
    for const in (0, 1):
        st = np.full(300, const, dtype=np.int8)
        T, A = _prefix(st)
        assert np.isnan(percentile_curve(T, A, 0, 299, 3)).all()


def test_half_assessed_window_is_not_scored():
    st = np.array([1, 1, -1, -1, -1, 0, 0, 1, 0, 1] * 10, dtype=np.int8)
    T, A = _prefix(st)
    c = percentile_curve(T, A, 0, 99, 3)
    for s in range(98):
        asses = int((st[s : s + 3] >= 0).sum())
        assert np.isnan(c[s]) == (asses * 2 < 3)  # fewer than half of 3 days assessed => not scored


def test_percentile_reference_stays_inside_the_block():
    # a burst of TRUE outside the block must not change the ranks inside it
    st = np.zeros(400, dtype=np.int8)
    st[100:104] = 1
    st[300:330] = 1
    T, A = _prefix(st)
    inside = percentile_curve(T, A, 0, 199, 3)
    alone = percentile_curve(*_prefix(st[:200]), 0, 199, 3)
    assert np.allclose(inside, alone, equal_nan=True)


# ── OR of groups ──────────────────────────────────────────────────────────────
def _kleene(vals):
    if any(v == 1 for v in vals):
        return 1.0
    if any(np.isnan(v) for v in vals):
        return np.nan
    return 0.0


def test_or_of_singleton_groups_is_kleene_or():
    for combo in itertools.product([0.0, 1.0, np.nan], repeat=3):
        arrs = [[np.array([v])] for v in combo]
        got = or_values(arrs)[0]
        want = _kleene(combo)
        assert (np.isnan(got) and np.isnan(want)) or got == want


def test_or_group_value_is_share_of_assessed_members():
    g1 = [np.array([1.0, 1.0, np.nan]), np.array([0.0, 1.0, np.nan])]
    g2 = [np.array([0.0, 0.0, 0.0])]
    got = or_values([g1, g2])
    assert np.allclose(got[:2], [0.5, 1.0])
    assert np.isnan(got[2])  # group 1 unassessed, group 2 FALSE: Kleene says unknown


# ── p-values and min-p ─────────────────────────────────────────────────────────
def test_pool_p_counts_observed_as_one_of_the_pool():
    pool = np.array([5.0, 1.0, 2.0, 3.0, 4.0])  # observed is the largest
    assert pool_p(pool) == 1 / 5
    pool = np.array([0.0, 1.0, 2.0, 3.0, 4.0])  # observed is the smallest
    assert pool_p(pool) == 1.0
    pool = np.array([2.0, 2.0, 2.0, 2.0, 2.0])  # all tied: p = 1
    assert pool_p(pool) == 1.0
    assert np.allclose(pool_p_all(np.array([3.0, 1.0, 2.0, 2.0])), [0.25, 1.0, 0.75, 0.75])


def test_min_p_single_statistic_equals_its_own_p():
    rng = np.random.default_rng(1)
    pool = rng.normal(size=1001)
    adj, per = min_p_adjusted({"T": pool})
    assert adj == pytest.approx(per["T"]) == pytest.approx(pool_p(pool))


def test_min_p_is_conservative_for_independent_statistics_and_valid_under_null():
    rng = np.random.default_rng(2)
    rej = 0
    for _ in range(600):
        pools = {k: rng.normal(size=400) for k in "ABCD"}  # exchangeable: observed is index 0
        adj, _ = min_p_adjusted(pools)
        rej += adj <= 0.05
    assert 0.02 <= rej / 600 <= 0.08  # exact level 5%, Monte Carlo band


def test_min_p_adjusted_never_below_the_smallest_single_p():
    rng = np.random.default_rng(3)
    for _ in range(50):
        pools = {k: rng.normal(size=300) for k in "AB"}
        adj, per = min_p_adjusted(pools)
        assert adj >= min(per.values()) - 1e-12


# ── Holm and the outcome rule ───────────────────────────────────────────────────
def test_holm_two_families():
    h = holm_adjust({"dasha": 0.02, "transit": 0.04})
    assert h["dasha"] == pytest.approx(0.04) and h["transit"] == pytest.approx(0.04)  # step 2 never below step 1
    h = holm_adjust({"dasha": 0.03, "transit": 0.20})
    assert h["dasha"] == pytest.approx(0.06) and h["transit"] == pytest.approx(0.20)
    assert holm_adjust({"x": 0.4}) == {"x": 0.4}
    # smallest p against 0.025, then 0.05 (v1.1 D6)
    assert holm_adjust({"a": 0.025, "b": 0.9})["a"] == pytest.approx(0.05)


def _fam(p1, p2, p3, pd, extra=None):
    d = {"p1": p1, "p2": p2, "p3": p3, "p_dir": pd}
    d.update(extra or {})
    return d


def test_outcome_strong_needs_all_four():
    t = {"dasha": True, "transit": True}
    v = decide({"dasha": _fam(0.01, 0.04, 0.04, 0.04), "transit": _fam(0.5, 0.5, 0.5, 0.5)}, t)
    assert v["outcome"] == STRONG and v["m"] == 2
    for bad in [(0.01, 0.06, 0.04, 0.04), (0.01, 0.04, 0.06, 0.04)]:
        v = decide({"dasha": _fam(*bad), "transit": _fam(0.5, 0.5, 0.5, 0.5)}, t)
        assert v["outcome"] == MIDDLE  # still within 0.10 on every check
    # Holm: p1 = 0.03 with two families adjusts to 0.06: not STRONG, but MIDDLE
    v = decide({"dasha": _fam(0.03, 0.01, 0.01, 0.01), "transit": _fam(0.5, 0.5, 0.5, 0.5)}, t)
    assert v["outcome"] == MIDDLE
    # with one testable family the same p1 is STRONG
    v = decide({"dasha": _fam(0.03, 0.01, 0.01, 0.01)}, {"dasha": True})
    assert v["outcome"] == STRONG and v["m"] == 1


def test_old_holm_pass_but_p2_fails_clause_is_removed():
    # v1.0 called "Holm pass, p2 > 0.05" MIDDLE whatever p2 was; v1.1 needs p2 <= 0.10 as well
    v = decide({"dasha": _fam(0.001, 0.30, 0.01, 0.01)}, {"dasha": True})
    assert v["outcome"] == CHANCE
    v = decide({"dasha": _fam(0.001, 0.01, 0.30, 0.01)}, {"dasha": True})
    assert v["outcome"] == CHANCE
    v = decide({"dasha": _fam(0.001, 0.08, 0.08, 0.01)}, {"dasha": True})
    assert v["outcome"] == MIDDLE


def test_strong_failing_only_direction_is_middle_with_label():
    v = decide({"dasha": _fam(0.001, 0.01, 0.01, 0.5)}, {"dasha": True})
    assert v["outcome"] == MIDDLE and LABEL_NOT_DIRECTION in v["labels"]
    v = decide({"dasha": _fam(0.001, 0.01, 0.01, None)}, {"dasha": True})  # no direction check possible: not STRONG
    assert v["outcome"] == MIDDLE


def test_fallback_consistency_and_label():
    r = _fam(0.001, 0.01, 0.01, 0.01, {"nonschedulable_above_null_mean": False})
    v = decide({"dasha": r}, {"dasha": True}, fallback_primary_set=True)
    assert v["outcome"] == MIDDLE and LABEL_CHOSEN_DATES in v["labels"] and LABEL_INCLUDES_CHOSEN in v["labels"]
    r = _fam(0.001, 0.01, 0.01, 0.01, {"nonschedulable_above_null_mean": True})
    v = decide({"dasha": r}, {"dasha": True}, fallback_primary_set=True)
    assert v["outcome"] == STRONG and v["labels"] == [LABEL_INCLUDES_CHOSEN]
    v = decide({"dasha": _fam(0.001, 0.01, 0.01, 0.01)}, {"dasha": True}, fallback_primary_set=False)
    assert v["outcome"] == STRONG and v["labels"] == []


def test_untestable_family_does_not_enter_holm_and_cannot_pass():
    v = decide({"dasha": _fam(0.03, 0.01, 0.01, 0.01), "transit": _fam(0.0001, 0.0001, 0.0001, 0.0001)}, {"dasha": True, "transit": False})
    assert v["m"] == 1 and v["outcome"] == STRONG and "transit" not in v["families"]
    assert decide({}, {})["outcome"] == CHANCE
    assert decide({"dasha": _fam(None, None, None, None)}, {"dasha": True})["outcome"] == CHANCE


def test_chance_level():
    assert decide({"dasha": _fam(0.4, 0.4, 0.4, 0.4), "transit": _fam(0.2, 0.3, 0.3, 0.3)}, {"dasha": True, "transit": True})["outcome"] == CHANCE


# ── minimum detectable effect ─────────────────────────────────────────────────────
def test_mde_interpolates_and_divides_by_extraction_noise():
    qs, pw = [0.05, 0.10, 0.15, 0.20], [0.10, 0.50, 0.90, 1.0]
    assert mde_from_power(qs, pw) == pytest.approx(0.1375)
    rep = mde_report(qs, pw)
    assert rep["mde_as_is"] == pytest.approx(0.1375)
    assert rep["mde_divided_by_0_67"] == pytest.approx(0.1375 / 0.67)
    assert mde_from_power([0.05, 0.1], [0.1, 0.5]) is None
    assert mde_report([0.05, 0.1], [0.1, 0.5])["mde_divided_by_0_67"] is None
    assert mde_from_power([0.1, 0.2], [0.9, 1.0]) == 0.1


# ── birth-time stability mask (v1.1 C2) ─────────────────────────────────────────────
def test_mask_unstable_marks_days_that_differ_across_builds():
    a = np.array([1, 1, 0, 0, -1, 1], dtype=np.int8)
    b = np.array([1, 0, 0, 1, -1, 1], dtype=np.int8)
    c = np.array([1, 1, 0, 0, 1, 1], dtype=np.int8)
    m = mask_unstable([a, b, c])
    assert m.tolist() == [1, -1, 0, -1, -1, 1]
    assert a.tolist() == [1, 1, 0, 0, -1, 1]  # inputs untouched
    with pytest.raises(ScorerError):
        mask_unstable([a])
    with pytest.raises(ScorerError):
        mask_unstable([a, b[:3]])


def test_config_matches_the_locked_text():
    assert C.BLOCK_DAYS_5Y == 1826 and C.BLOCK_DAYS_15Y == 5479 and C.MERGE_BELOW_5Y == 913
    assert C.TOUCH_RATE_GATE == 0.60 and C.EXTRACTION_NOISE == 0.67
    assert C.SCHEMES[C.FAMILY_DASHA][0][0] == "5y" and [s[0] for s in C.SCHEMES[C.FAMILY_DASHA]] == ["5y", "15y"]
    assert [s[0] for s in C.SCHEMES[C.FAMILY_TRANSIT]] == ["5y"]
    assert C.GATE_PER_FAMILY == 0.02 and C.GATE_OVERALL == 0.03 and C.GATE_MIN_STUDIES == 5000
