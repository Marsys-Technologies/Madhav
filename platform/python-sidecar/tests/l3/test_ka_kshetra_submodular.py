"""
Tests for services.ka_kshetra.submodular — KALA_W2_FIELD_DESIGN_v1_0.md §6.2.

Pure-Python module, no DB -- all tests here are pure unit tests, including a
from-scratch brute-force comparison that verifies the lazy-greedy
implementation reproduces the SAME result a naive (non-lazy) greedy would,
and that it clears the classical (1 - 1/e) submodular approximation bound
against a small brute-forced optimum.
"""
from __future__ import annotations

import itertools
import os
import sys

import pytest

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.ka_kshetra.submodular import (
    ProvenanceTerm,
    SubmodularCandidate,
    select_submodular,
    window_family_id,
)


def _cand(window_id, event_class, salience, lord_stack, terms):
    return SubmodularCandidate(
        window_id=window_id, event_class=event_class, salience=salience,
        lord_stack_at_peak=tuple(lord_stack),
        provenance_terms=tuple(ProvenanceTerm(k, v) for k, v in terms),
    )


class TestWindowFamilyId:
    def test_deterministic(self):
        a = window_family_id("career_change", ("Saturn", "Rahu"))
        b = window_family_id("career_change", ("Saturn", "Rahu"))
        assert a == b

    def test_order_invariant(self):
        a = window_family_id("career_change", ("Saturn", "Rahu"))
        b = window_family_id("career_change", ("Rahu", "Saturn"))
        assert a == b

    def test_different_event_class_differs(self):
        a = window_family_id("career_change", ("Saturn",))
        b = window_family_id("career_setback", ("Saturn",))
        assert a != b

    def test_16_char_hex(self):
        fid = window_family_id("x", ("Saturn",))
        assert len(fid) == 16
        int(fid, 16)  # raises if not hex


class TestSelectSubmodularBasics:
    def test_empty_candidates(self):
        result = select_submodular([], k=5)
        assert result.selected == ()
        assert result.trace == ()
        assert result.largest_omission is None
        assert result.coverage_fraction == 0.0

    def test_single_candidate(self):
        c = _cand("w1", "career_entry", 0.8, ("Jupiter",), [("baseline", 1.0)])
        result = select_submodular([c], k=5)
        assert result.selected == ("w1",)
        assert result.largest_omission is None
        assert result.coverage_fraction == 1.0

    def test_budget_caps_selection_count(self):
        cands = [
            _cand(f"w{i}", f"class{i}", 0.5 + i * 0.01, (f"Lord{i}",), [(f"term{i}", 1.0 + i)])
            for i in range(10)
        ]
        result = select_submodular(cands, k=3)
        assert len(result.selected) == 3

    def test_deterministic_repeat_run(self):
        cands = [
            _cand(f"w{i}", f"class{i}", 0.5, (f"Lord{i}",), [(f"term{i}", 1.0)])
            for i in range(8)
        ]
        r1 = select_submodular(cands, k=4)
        r2 = select_submodular(cands, k=4)
        assert r1.selected == r2.selected
        assert r1.coverage_fraction == r2.coverage_fraction


class TestFamilyDiversification:
    """
    The headline scenario §6.2 exists to fix: "14 of 15 rows are the same
    signal type". Many candidates share the SAME (event_class,
    window_family_id) and carry near-identical top driver terms -- once one
    is selected, the rest's marginal gain collapses toward zero (their
    coverage is already claimed), so a small budget spends itself across
    DIFFERENT atoms/families rather than repeating one family.
    """

    def test_redundant_family_members_are_not_all_selected(self):
        # 5 candidates, all career_change with the same lord stack (one
        # family), all driven by the same term at nearly the same strength.
        family = [
            _cand(f"fam{i}", "career_change", 0.9 - i * 0.001, ("Saturn", "Rahu"),
                  [("clock:vimshottari:AD:Sa", 2.0 - i * 0.01)])
            for i in range(5)
        ]
        # One genuinely different signal: different class, different family,
        # different driver term.
        distinct = _cand("distinct1", "education_milestone", 0.85, ("Jupiter",),
                          [("clock:vimshottari:AD:Ju", 1.8)])

        result = select_submodular(family + [distinct], k=2)
        # With budget 2: the first pick is the strongest family member
        # (highest salience/contribution), the second pick should be the
        # genuinely distinct signal, NOT the second-best family member,
        # because the family's atom is already covered after pick 1.
        assert len(result.selected) == 2
        assert "distinct1" in result.selected

    def test_second_family_member_marginal_gain_near_zero(self):
        family = [
            _cand("fam0", "career_change", 0.9, ("Saturn",), [("t", 2.0)]),
            _cand("fam1", "career_change", 0.9, ("Saturn",), [("t", 2.0)]),  # identical family+term+contrib
        ]
        result = select_submodular(family, k=2)
        # Both share exactly one atom (same event_class/family/term) with
        # identical contribution -- once the first is picked, cov is already
        # 1.0 for that atom, so the second's marginal gain is exactly 0.
        assert len(result.trace) >= 1
        first_gain = result.trace[0].marginal_gain
        assert first_gain > 0
        if len(result.trace) == 2:
            assert result.trace[1].marginal_gain == pytest.approx(0.0, abs=1e-9)


class TestZeroMaxContribution:
    """
    Defect #7 (Gate-Chain MORNING REPORT, commit 5ff0791d): `max_contrib[atom]`
    can be legitimately zero when every candidate carrying an atom has
    log_contribution == 0.0 for that driver term -- e.g. chart 1c826d5a's
    field build, where 2 of 12 discovered classes (marriage, separation)
    have real N_e coverage and the rest carry zero-strength provenance
    terms. This must not raise ZeroDivisionError; an atom with nothing to
    normalize against contributes marginal gain 0 for that window, not an
    error.
    """

    def test_single_candidate_zero_contribution_term_does_not_raise(self):
        # Sole carrier of its atom, with log_contribution == 0.0 -> max_contrib
        # for that atom is 0.0. cov(i, c) must resolve to 0 (nothing to
        # normalize against), not divide by zero.
        c = _cand("w1", "marriage", 0.8, ("Jupiter",), [("baseline", 0.0)])
        result = select_submodular([c], k=5)
        assert result.selected == ("w1",)
        # No atom had anything to normalize against, so no gain accrues and
        # F(S) == 0 -- honest zero, not a fabricated nonzero value.
        assert result.trace[0].marginal_gain == 0.0
        assert result.coverage_fraction == 0.0

    def test_mixed_zero_and_nonzero_atoms_only_nonzero_contributes_gain(self):
        # w1 carries two atoms: one with a real (nonzero) contribution, one
        # with an all-zero contribution across its carriers. Only the real
        # atom should contribute marginal gain; the zero-max atom must be
        # inert, not crash the selection.
        c = _cand(
            "w1", "separation", 0.9, ("Saturn",),
            [("real_term", 2.0), ("dead_term", 0.0)],
        )
        result = select_submodular([c], k=5)
        assert result.selected == ("w1",)
        # Only the real_term atom's u_c contributes: u_c = salience = 0.9,
        # cov = 2.0/2.0 = 1.0 -> gain = 0.9. The dead_term atom contributes 0.
        assert result.trace[0].marginal_gain == pytest.approx(0.9, abs=1e-9)

    def test_multiple_candidates_sharing_a_zero_contribution_atom(self):
        # Two candidates share the same (event_class, family, term) atom,
        # both with log_contribution == 0.0 -- max_contrib is 0 across BOTH
        # carriers, not just a single-candidate edge case.
        cands = [
            _cand("w1", "marriage", 0.7, ("Venus",), [("dead", 0.0)]),
            _cand("w2", "marriage", 0.6, ("Venus",), [("dead", 0.0)]),
        ]
        result = select_submodular(cands, k=5)
        assert set(result.selected) == {"w1", "w2"}
        for entry in result.trace:
            assert entry.marginal_gain == 0.0


class TestLazyGreedyMatchesNaiveGreedy:
    """Lazy evaluation must be an EXACT optimization of the same greedy —
    it changes speed, not the result (§6.2)."""

    def _naive_greedy(self, candidates, k):
        """Full recompute of every candidate's marginal gain at every step —
        the textbook (slow) greedy, used here only as a ground truth."""
        from services.ka_kshetra.submodular import _build_atoms

        atoms = _build_atoms(candidates)
        salience_by_id = {c.window_id: c.salience for c in candidates}
        u = {a: max(salience_by_id[wid] for wid, _ in carriers) for a, carriers in atoms.items()}
        max_contrib = {a: max(v for _, v in carriers) for a, carriers in atoms.items()}
        contrib_by_atom = {a: dict(carriers) for a, carriers in atoms.items()}
        atoms_by_window = {}
        for a, carriers in atoms.items():
            for wid, _ in carriers:
                atoms_by_window.setdefault(wid, []).append(a)

        cov_max = {a: 0.0 for a in atoms}
        selected, trace = [], []
        remaining = {c.window_id: c for c in candidates}
        f_s = 0.0
        while remaining and len(selected) < k:
            best_wid, best_gain, best_atoms = None, -1.0, []
            for wid in sorted(remaining):  # deterministic tie-break: lower window_id
                gain, newly = 0.0, []
                for atom in atoms_by_window.get(wid, ()):
                    cov_i = contrib_by_atom[atom][wid] / max_contrib[atom]
                    d = cov_i - cov_max[atom]
                    if d > 0:
                        gain += u[atom] * d
                        newly.append(atom)
                if gain > best_gain:
                    best_gain, best_wid, best_atoms = gain, wid, newly
            if best_gain < 0.01 * f_s:
                break
            selected.append(best_wid)
            trace.append(best_gain)
            for atom in best_atoms:
                cov_i = contrib_by_atom[atom][best_wid] / max_contrib[atom]
                cov_max[atom] = max(cov_max[atom], cov_i)
            f_s += best_gain
            del remaining[best_wid]
        return selected, trace

    @pytest.mark.parametrize("seed_case", range(5))
    def test_lazy_equals_naive_on_random_small_cases(self, seed_case):
        import random
        rng = random.Random(seed_case)
        n = 12
        term_pool = [f"term{i}" for i in range(4)]
        lord_pool = ["Saturn", "Jupiter", "Rahu", "Mars", "Venus"]
        classes = ["career_change", "education_milestone", "relocation"]

        cands = []
        for i in range(n):
            terms = [(rng.choice(term_pool), round(rng.uniform(0.1, 3.0), 3)) for _ in range(3)]
            stack = tuple(rng.sample(lord_pool, k=rng.randint(1, 3)))
            cands.append(_cand(
                f"w{i}", rng.choice(classes), round(rng.uniform(0.1, 1.0), 3), stack, terms,
            ))

        k = 4
        lazy_result = select_submodular(cands, k=k)
        naive_selected, naive_gains = self._naive_greedy(cands, k=k)

        assert list(lazy_result.selected) == naive_selected
        for entry, naive_gain in zip(lazy_result.trace, naive_gains):
            assert entry.marginal_gain == pytest.approx(naive_gain, abs=1e-9)


class TestApproximationGuarantee:
    """Empirical (1 - 1/e) check: greedy F(S) against a brute-forced optimum
    on a small enough instance to exhaustively search."""

    def test_greedy_clears_one_minus_one_over_e_bound(self):
        cands = [
            _cand("a", "c1", 0.9, ("Saturn",), [("t0", 3.0)]),
            _cand("b", "c1", 0.85, ("Saturn",), [("t0", 2.5)]),
            _cand("c", "c2", 0.7, ("Jupiter",), [("t1", 2.0)]),
            _cand("d", "c3", 0.6, ("Mars",), [("t2", 1.5)]),
            _cand("e", "c3", 0.5, ("Mars",), [("t2", 1.0)]),
        ]
        k = 2

        result = select_submodular(cands, k=k)
        greedy_value = _evaluate_F(cands, set(result.selected))

        best_value = 0.0
        for combo in itertools.combinations([c.window_id for c in cands], k):
            best_value = max(best_value, _evaluate_F(cands, set(combo)))

        assert best_value > 0
        assert greedy_value >= (1 - 1 / 2.718281828) * best_value - 1e-9


def _evaluate_F(candidates, selected_ids):
    """Standalone re-implementation of F(S) for the approximation-bound test
    (deliberately independent of submodular.py's internal state variables,
    so this is a real cross-check, not a tautology)."""
    from services.ka_kshetra.submodular import _build_atoms

    atoms = _build_atoms(candidates)
    salience_by_id = {c.window_id: c.salience for c in candidates}
    total = 0.0
    for atom, carriers in atoms.items():
        u_c = max(salience_by_id[wid] for wid, _ in carriers)
        max_contrib = max(v for _, v in carriers)
        best_cov = 0.0
        for wid, contrib in carriers:
            if wid in selected_ids:
                best_cov = max(best_cov, contrib / max_contrib)
        total += u_c * best_cov
    return total
