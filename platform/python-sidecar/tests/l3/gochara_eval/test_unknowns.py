"""SI addendum v1.3 §4 — the production unknown-competitor bounds (services/gochara_eval/unknowns.py).

The three worked cases are Codex round 7/8's arithmetic; the cross-checks run an INDEPENDENT dense-grid brute force and require
the production placement-class enumeration to bound exactly the same set of verdicts.
"""
from __future__ import annotations

import random
from itertools import combinations_with_replacement

import pytest

from services.gochara_eval.registry import TIE_TOL
from services.gochara_eval.unknowns import (BudgetExceeded, assignments, groups, percentile_of, percentile_range,
                                            plateau_fraction, plateau_fractions, placements)


class TestWorkedCases:
    def test_a_matched_above_the_unknowns_reach(self):
        lo, hi, _ = percentile_range([2.0, 1.0, 0.0], 0, 2)
        assert (lo, hi) == (0.0, 40.0)

    def test_b_zero_boundary(self):
        lo, hi, vals = percentile_range([0.0, 2.0, 1.0], 0, 2)
        assert (lo, hi) == (60.0, 80.0), vals
        assert 70.0 in vals          # one tied with the matched, one strictly above (avg rank 4.5)

    def test_c_tie_group_bridge_makes_the_plateau_verdict_non_invariant(self):
        fr = plateau_fractions([0.0, 0.0, 1.5e-9, 1.5e-9, 1.0, 2.0, 3.0], 1)
        assert 0.375 in fr and 0.25 in fr and 0.625 in fr
        assert {f >= 0.5 for f in fr} == {True, False}

    def test_no_unknown_is_a_single_point(self):
        lo, hi, vals = percentile_range([2.0, 1.0, 0.0], 0, 0)
        assert lo == hi == 0.0 and len(vals) == 1


class TestGrouping:
    def test_adjacent_gap_chain_is_one_group(self):
        v = [0.0, 0.75e-9, 1.5e-9]
        assert sorted(len(g) for g in groups(v)) == [3]
        assert plateau_fraction(v) == 1.0

    def test_gap_of_exactly_the_tolerance_cuts(self):
        assert len(groups([0.0, TIE_TOL])) == 2

    def test_average_rank(self):
        assert percentile_of([1.0, 1.0, 0.5], 0) == pytest.approx(100 * (1.5 - 1) / 3)


def _brute_values(known, k):
    """Independent enumeration: a dense grid of quarter-tolerance offsets around every anchor, plus 0 and a far-above value."""
    anchors = {0.0, 1000.0, *known}
    ks = sorted(set(known))
    anchors |= {(a + b) / 2 for a, b in zip(ks, ks[1:])}
    grid = set()
    for a in anchors:
        for q in range(-6 * (k + 1), 6 * (k + 1) + 1):
            v = a + q * 0.25 * TIE_TOL
            if v >= 0:
                grid.add(v)
    return sorted(grid)


class TestAgainstBruteForce:
    @pytest.mark.parametrize("seed", range(12))
    def test_percentile_and_plateau_verdicts_match_dense_grid(self, seed):
        rng = random.Random(seed)
        pool = [0.0, 0.0, 1.0e-9, 1.5e-9, 0.5, 0.5, 2.0, 2.0 + 0.8e-9]
        known = [rng.choice(pool) for _ in range(rng.randint(2, 4))]
        k = rng.randint(1, 2)
        idx = rng.randrange(len(known))
        grid = _brute_values(known, k)
        brute_p, brute_v = set(), set()
        for combo in combinations_with_replacement(grid, k):
            vec = known + list(combo)
            brute_p.add(round(percentile_of(vec, idx), 9))
            brute_v.add(plateau_fraction(vec) < 0.5)
        lo, hi, prod_p = percentile_range(known, idx, k)
        prod_v = {f < 0.5 for f in plateau_fractions(known, k)}
        assert (lo, hi) == (min(brute_p), max(brute_p)), (known, k, idx)
        assert prod_v == brute_v, (known, k)
        assert brute_p <= set(prod_p)          # every grid-attainable percentile is among the production-enumerated ones

    def test_unknowns_can_chain_with_each_other_not_only_with_known_values(self):
        # known 0 and 5 only; two unknowns at 0.4e-9 and 1.2e-9 chain with 0 and with each other: one group of 3 of 4
        fr = plateau_fractions([0.0, 5.0], 2)
        assert 0.75 in fr
        assert 0.25 in fr      # all separated

    def test_all_unknown_candidate_set(self):
        fr = plateau_fractions([], 3)
        assert 1.0 in fr
        assert any(abs(f - 1 / 3) < 1e-9 for f in fr)

    def test_placement_set_contains_the_boundary_and_above_everything(self):
        pl = placements([1.0, 2.0], 1)
        assert 0.0 in pl and max(pl) >= 1000.0
        assert all(p >= 0 for p in pl)


class TestBudget:
    def test_refuses_before_enumerating(self):
        with pytest.raises(BudgetExceeded):
            next(assignments([float(i) for i in range(30)], [6], budget=1000))

    def test_empty_groups_yield_one_assignment(self):
        assert len(list(assignments([1.0], [0, 0]))) == 1
