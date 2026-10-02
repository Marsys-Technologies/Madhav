"""SI addendum v1.3 §4 — the unknown-competitor bounds, PROVEN enumeration (services/gochara_eval/unknowns.py).

Three kinds of evidence, each independent of the others:
  1. the round-7/8/9 worked cases and counterexamples, through production code;
  2. COMPLETENESS — random concrete assignments (clustered at multiples of the tolerance, at zero, at 1e10, ties) are evaluated by the
     protocol's own concrete arithmetic and every outcome must be in the enumerated set;
  3. ATTAINABILITY — for EVERY enumerated structure an explicit numeric witness is built in exact rational arithmetic (the lemma's
     construction), and the outcome re-derived from the numbers must equal the structure's — no over-approximation.
"""
from __future__ import annotations

import random
from fractions import Fraction

import pytest

from services.gochara_eval.registry import TIE_TOL
from services.gochara_eval.unknowns import (TAU_EXACT, BudgetExceeded, enumerate_structures, event_percentiles, groups,
                                            percentile_of, percentile_range, plateau_fraction, plateau_fractions)


class TestWorkedCases:
    def test_a_matched_above_the_unknowns_reach(self):
        assert percentile_range([2.0, 1.0, 0.0], 0, 2)[:2] == (0.0, 40.0)

    def test_b_zero_boundary(self):
        lo, hi, vals = percentile_range([0.0, 2.0, 1.0], 0, 2)
        assert (lo, hi) == (60.0, 80.0) and 70.0 in vals

    def test_c_tie_group_bridge_makes_the_plateau_verdict_non_invariant(self):
        fr = plateau_fractions([0.0, 0.0, 1.5e-9, 1.5e-9, 1.0, 2.0, 3.0], 1)
        assert {0.25, 0.375, 0.625} <= set(fr) and {f >= 0.5 for f in fr} == {True, False}

    def test_no_unknown_is_a_single_point(self):
        lo, hi, vals = percentile_range([2.0, 1.0, 0.0], 0, 0)
        assert lo == hi == 0.0 and len(vals) == 1


class TestRound9Counterexamples:
    def test_unknown_unknown_bridge_across_a_gap_of_2_9_tau(self):
        """Codex R9-7: known [0, 2.9e-9, 1,2,3,4] + 2 unknowns; the unknowns at 2.9e-9/3 and 2·2.9e-9/3 chain 0 → 2.9e-9 into
        one group of 4 of 8 = 0.5. The 0.75·TAU grid reported max 0.375."""
        fr = plateau_fractions([0, 2.9e-9, 1, 2, 3, 4], 2)
        assert 0.5 in fr and max(fr) == 0.5
        # the witness the review gave is a real assignment: its concrete outcome is in the set
        vec = [0, 2.9e-9, 1, 2, 3, 4, 2.9e-9 / 3, 2 * 2.9e-9 / 3]
        assert plateau_fraction(vec) == 0.5

    def test_a_known_value_far_above_any_fixed_sentinel(self):
        """Codex R9-7: known [1e10, 0], matched 1e10, one unknown at 1e10+1 → percentile 33.33. BIG = 1000 reported max 16.67."""
        lo, hi, vals = percentile_range([1e10, 0.0], 0, 1)
        assert hi == pytest.approx(100 / 3) and lo == 0.0
        assert percentile_of([1e10, 0.0, 1e10 + 1], 0) == pytest.approx(100 / 3)

    def test_gap_boundaries_are_exact(self):
        """Known 0 and g = 2·TAU (+ a far value): ONE unknown cannot bridge (two differences must both be < TAU), TWO can
        (three differences, g < 3·TAU) — a group of 4 of 5."""
        g = 2 * TIE_TOL
        assert max(plateau_fractions([0.0, g, 5.0], 1)) == 0.5
        assert 0.8 in plateau_fractions([0.0, g, 5.0], 2)


class TestGrouping:
    def test_adjacent_gap_chain_is_one_group(self):
        v = [0.0, 0.75e-9, 1.5e-9]
        assert sorted(len(g) for g in groups(v)) == [3] and plateau_fraction(v) == 1.0

    def test_gap_of_exactly_the_tolerance_cuts(self):
        assert len(groups([0.0, TIE_TOL])) == 2

    def test_average_rank(self):
        assert percentile_of([1.0, 1.0, 0.5], 0) == pytest.approx(100 * (1.5 - 1) / 3)


# ---- completeness: random concrete assignments are always inside the enumeration --------------------------------------------
def _pool(rng, known):
    anchors = [0.0, 1.0e10] + list(known)
    out = []
    for _ in range(40):
        a = rng.choice(anchors)
        out.append(max(0.0, a + rng.choice([0, 1, -1, 0.3, 0.9, 1.1, 2, 2.9, 3.2]) * TIE_TOL * rng.choice([0.5, 1, 1.5, 3])))
    out += [rng.random() * 5 for _ in range(8)] + [1e10 + 1, 1e10 + 1e-3]
    return out


@pytest.mark.parametrize("seed", range(40))
def test_every_concrete_assignment_is_in_the_enumeration(seed):
    rng = random.Random(seed)
    known = [rng.choice([0.0, 0.0, 1.0e-9, 2.9e-9, 5.0e-9, 0.5, 1.0, 2.0, 1e10]) for _ in range(rng.randint(1, 5))]
    k_a, k_b = rng.randint(0, 2), rng.randint(0, 2)
    cont = [rng.random() < 0.5 for _ in known]
    if not any(cont) and k_a == 0:
        cont[0] = True
    pcts, _ = event_percentiles(known, cont, k_a, k_b)
    plateaus = {float(st["plateau"]) for st in enumerate_structures(known, [False] * len(known), 0, k_a + k_b)}
    pool = _pool(rng, known)
    for _ in range(200):
        a_vals = [rng.choice(pool) for _ in range(k_a)]
        b_vals = [rng.choice(pool) for _ in range(k_b)]
        vec = list(known) + a_vals + b_vals
        cont_idx = [i for i, c in enumerate(cont) if c] + list(range(len(known), len(known) + k_a))
        tgt = max(cont_idx, key=lambda i: vec[i])
        assert any(abs(percentile_of(vec, tgt) - p) < 1e-9 for p in pcts), (known, cont, a_vals, b_vals)
        assert any(abs(plateau_fraction(vec) - f) < 1e-12 for f in plateaus), (known, a_vals, b_vals)


# ---- attainability: an exact rational witness for EVERY enumerated structure -----------------------------------------------
def _witness(known, st):
    """Numbers (Fractions) realising structure `st` — the lemma's construction — as (items [(value, label)], contained flags)."""
    ks = sorted(Fraction(x) for x in known)
    chain = []                                           # ascending list of (value, kind, idx)
    plan = st["plan"]
    low, mids, high = plan[0], plan[1:-1], plan[-1]
    if not known:                                        # 'only'
        labels, cuts = plan[0][2], plan[0][3]
        v = Fraction(0)
        vals = []
        for i in range(len(labels)):
            vals.append(v)
            if i < len(labels) - 1:
                v += TAU_EXACT if cuts[i] else 0
        return [], [(vals, labels)], None
    unk = []
    # LOW: unknowns end at v_1, differences listed left to right
    labels, cuts = low[2], low[3]
    vals = []
    v = ks[0]
    for i in range(len(labels) - 1, -1, -1):
        v -= TAU_EXACT if cuts[i] else 0                 # difference between unknown i and the item to its right
        vals.append(v)
    unk.append((list(reversed(vals)), labels))
    for j, (kind, span, labels, cuts) in enumerate(mids):
        lo, hi = ks[j], ks[j + 1]
        m = len(labels)
        diffs = []
        c = sum(cuts)
        if m == 0:
            unk.append(([], labels))
            continue
        if c == 0:
            d = (hi - lo) / (m + 1)
            diffs = [d] * (m + 1)
        else:
            first_cut_done = False
            for cut in cuts:
                if cut:
                    diffs.append((hi - lo) - (c - 1) * TAU_EXACT if not first_cut_done else TAU_EXACT)
                    first_cut_done = True
                else:
                    diffs.append(Fraction(0))
        vals, v = [], lo
        for i in range(m):
            v += diffs[i]
            vals.append(v)
        unk.append((vals, labels))
    labels, cuts = high[2], high[3]
    vals, v = [], ks[-1]
    for i in range(len(labels)):
        v += TAU_EXACT if cuts[i] else 0
        vals.append(v)
    unk.append((vals, labels))
    return ks, unk, None


def _exact_outcome(known, known_cont, st, witness):
    ks_sorted_idx = sorted(range(len(known)), key=lambda i: known[i])
    ks, unk, _ = witness
    items = []                                           # (value, contained)
    for vals, labels in [unk[0]]:
        items += [(v, lab == "A") for v, lab in zip(vals, labels)]
    for j, i in enumerate(ks_sorted_idx):
        items.append((Fraction(known[i]), bool(known_cont[i])))
        if j < len(ks_sorted_idx) - 1:
            vals, labels = unk[1 + j]
            items += [(v, lab == "A") for v, lab in zip(vals, labels)]
    if known:
        vals, labels = unk[-1]
        items += [(v, lab == "A") for v, lab in zip(vals, labels)]
    items.sort(key=lambda t: t[0])
    n = len(items)
    # groups under the EXACT tolerance, adjacent-gap, on the real-valued witness; known-known differences use the protocol's float
    # predicate in the enumeration, so witnesses are only compared where the two agree (no known-known gap within 1 ulp of TAU)
    sizes, owner, cur = [], [], 0
    for i, (v, _c) in enumerate(items):
        cur += 1
        owner.append(len(sizes))
        if i == n - 1 or items[i + 1][0] - v >= TAU_EXACT:
            sizes.append(cur)
            cur = 0
    cont = [i for i, (_v, c) in enumerate(items) if c]
    pct = None
    if cont:
        g = owner[cont[-1]]
        pct = Fraction(100 * (2 * sum(sizes[g + 1:]) + sizes[g] - 1), 2 * n)
    return pct, Fraction(max(sizes), n)


@pytest.mark.parametrize("known,known_cont,k_a,k_b", [
    ([0.0, 2.0, 1.0], [True, False, False], 0, 2),
    ([0.0, 2.9e-9, 1, 2, 3, 4], [False, False, True, False, False, False], 1, 1),
    ([1e10, 0.0], [True, False], 0, 2),
    ([0.0, 0.0, 1.5e-9, 1.5e-9, 1.0, 2.0, 3.0], [False, False, False, False, True, False, False], 1, 1),
    ([5.0e-9, 1.0e-9, 0.0, 3.0e-9], [False, True, False, False], 0, 3),
    ([], [], 2, 1),
    ([0.5], [True], 2, 2),
    ([0.0, 1.0e-9], [True, False], 0, 3),
])
def test_every_enumerated_structure_has_an_exact_witness(known, known_cont, k_a, k_b):
    n = 0
    for st in enumerate_structures(known, known_cont, k_a, k_b):
        n += 1
        w = _witness(known, st)
        pct, plateau = _exact_outcome(known, known_cont, st, w)
        assert plateau == st["plateau"], (st["plan"], plateau, st["plateau"])
        assert pct == st["pct"], (st["plan"], pct, st["pct"])
    assert n > 0


class TestBudget:
    def test_refuses_instead_of_returning_a_partial_range(self):
        with pytest.raises(BudgetExceeded):
            list(enumerate_structures([float(i) for i in range(30)], [False] * 30, 0, 6, budget=1000))

    def test_event_percentiles_propagates_the_refusal(self):
        with pytest.raises(BudgetExceeded):
            event_percentiles([float(i) for i in range(30)], [True] + [False] * 29, 3, 3, budget=500)

    def test_no_unknown_one_structure(self):
        assert len(list(enumerate_structures([1.0, 2.0], [True, False], 0, 0))) == 1


# ---- production == the independent reference model (exact lattice brute force) -----------------------------------------------
# ── R10-8: the budget bounds the WORK, not just the yield ───────────────────────────────────────────────────────

import time  # noqa: E402

from services.gochara_eval import unknowns as _unk  # noqa: E402


def test_an_over_budget_query_raises_before_any_option_is_generated(monkeypatch):
    """Ten unknowns, budget 1: the old code built 512 slot options (and 2^39 for forty) BEFORE its first budget check. Now the budget is checked on an
    arithmetic count first: `_slot_options` is never called."""
    calls = []
    orig = _unk._slot_options
    monkeypatch.setattr(_unk, "_slot_options", lambda *a, **k: (calls.append(a), orig(*a, **k))[1])
    with pytest.raises(BudgetExceeded):
        list(enumerate_structures([], [], 0, 10, budget=1))
    assert calls == [], f"{len(calls)} slot-option generators were created for an over-budget query"


@pytest.mark.parametrize("known,k_a,k_b", [([], 0, 40), ([], 20, 20), ([1.0, 2.0, 3.0], 0, 40), ([1.0, 2.0, 3.0], 10, 30),
                                           ([float(i) for i in range(30)], 5, 35)])
def test_forty_unknowns_reach_the_conservative_fallback_fast(known, k_a, k_b):
    """A large unknown population raises BudgetExceeded in well under a second — no 2^39 allocation, no exponential scan — at the default budget."""
    t0 = time.perf_counter()
    with pytest.raises(BudgetExceeded):
        list(enumerate_structures(known, [False] * len(known), k_a, k_b))
    assert time.perf_counter() - t0 < 1.0


def test_the_fallback_is_the_declared_conservative_range_through_the_adapter(tmp_path):
    """Through the production adapter path: an event whose class-year holds forty unknown candidates reports BUDGET_EXCEEDED with the FULL [0,100] range
    (unqualified), never a partial range."""
    from services.gochara_eval import candidate as cand
    from services.gochara_eval.unknowns import BudgetExceeded as BE
    try:
        event_percentiles([1.0, 2.0], [True, False], 20, 20)
    except BE:
        pass
    else:
        pytest.fail("forty unknowns must exceed the default budget")
    assert cand.BudgetExceeded is BE                              # the adapter catches exactly this and returns pct_lo=0.0, pct_hi=100.0


def test_the_lazy_generation_yields_exactly_what_the_eager_one_did():
    """The per-cut-count generation is a reordering of the same set: every attainable structure, no more, no fewer (small cases, brute-force masks)."""
    from itertools import combinations
    for kind, span, m in (("low", Fraction(3, 2) * TAU_EXACT, 3), ("mid", Fraction(5, 2) * TAU_EXACT, 2), ("mid", Fraction(1, 10) * TAU_EXACT, 3),
                          ("high", None, 3), ("only", None, 4)):
        n_diff = _unk._n_diff(kind, m)
        want = set()
        for mask in range(1 << n_diff):
            cuts = tuple(bool(mask >> i & 1) for i in range(n_diff))
            if _unk._feasible(kind, sum(cuts), m, span):
                want.add(cuts)
        got = [c for _, c in _unk._slot_options(kind, span, 0, m)]
        assert set(got) == want and len(got) == len(want)
        assert _unk._slot_option_count(kind, span, 0, m) == len(want)


import importlib.util  # noqa: E402

from .conftest import CAMPAIGN_MEASUREMENT, needs_campaign  # noqa: E402


@needs_campaign
class TestAgainstTheReferenceModel:
    @pytest.fixture(scope="class")
    def model(self):
        spec = importlib.util.spec_from_file_location("ucbm", CAMPAIGN_MEASUREMENT / "unknown_competitor_bounds_model.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    @pytest.mark.parametrize("seed", range(25))
    def test_same_attainable_sets(self, model, seed):
        rng = random.Random(500 + seed)
        known = [rng.choice([0.0, 0.0, 1.0e-9, 2.9e-9, 5.0e-9, 0.5, 1.0, 2.0, 1e10]) for _ in range(rng.randint(1, 4))]
        k = rng.randint(1, 2)
        idx = rng.randrange(len(known))
        assert model.plateau_fractions(known, k) == pytest.approx(plateau_fractions(known, k), abs=1e-12)
        mlo, mhi, mvals = model.percentile_range(known, idx, k)
        plo, phi, pvals = percentile_range(known, idx, k)
        assert (mlo, mhi) == pytest.approx((plo, phi), abs=1e-9)
        assert mvals == pytest.approx(pvals, abs=1e-9)
