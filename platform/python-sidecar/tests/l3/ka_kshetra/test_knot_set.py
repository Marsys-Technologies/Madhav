"""
tests/l3/ka_kshetra/test_knot_set.py — C-1 condition (PARĪKṢAKA FM-26 verdict on #1284)

Two required property tests for assemble_knot_set() after F5 (SM-R-11 decade-seam fix):

  (a) Decade-knot presence: all nine interior decade boundaries d·H/10 for d=1..9
      must appear in the output of assemble_knot_set().

  (b) Full-horizon contiguity: after running dhara_build_segments() on a synthetic
      full-horizon evaluator, the resulting segments must cover [0, H] with
      gaps == 0 (no uncovered interval between consecutive segments).

Authority: PARĪKṢAKA FM-26 C-1 condition on PR #1284; PURNA_KSHETRA_PLAN_v1_1.md §2 P1;
DHARA_ENGINE_SPEC_v1_0.md §5.

These tests run unconditionally (no DB, no IO) — they are part of the always-on CI gate.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.ka_kshetra import stage4_field as S4
from services.ka_kshetra.contracts import ClockApplicability, PromisePrior, Route
from services.ka_kshetra.dhara_sweep import assemble_knot_set, dhara_build_segments

# ---------------------------------------------------------------------------
# Full-horizon synthetic FieldEvaluator factory (no DB, no IO)
# ---------------------------------------------------------------------------
_H = S4.HORIZON_DAYS  # 36525.0


def _make_full_horizon_evaluator() -> S4.FieldEvaluator:
    """Build a minimal but realistic FieldEvaluator spanning the full 36 525-day horizon.

    The ladder covers the entire horizon with two vimshottari MD periods and one
    yogini MD period, ensuring at least one clock-knot boundary falls in each
    decade (at the mid-point of the horizon).  The envelope places a contact
    hump in decade 0 so the sweep has real structure to integrate.

    No DB, no IO, no RNG — deterministic by construction.
    """
    mid = _H / 2.0

    # Two-period vimshottari ladder spanning the full horizon.
    ladder = {
        "vimshottari": [
            S4.LadderPeriod("vimshottari", "MD", "Ju", 0.0, mid),
            S4.LadderPeriod("vimshottari", "MD", "Sa", mid, _H),
        ],
        "yogini": [
            S4.LadderPeriod("yogini", "MD", "Ju", 0.0, _H),
        ],
    }

    # Contact envelope: a gentle hump centred around year 25 (≈9131 days).
    hump = 365.25 * 25
    primitives = [
        S4.Primitive(
            primitive_kind="contact_moon_ref",
            subject="Ju",
            object_ref="Mo",
            polarity="supportive",
            class_label=None,
            knots=((hump - 365, 0.0), (hump, 0.8), (hump + 365, 0.0)),
        ),
    ]
    env = S4.EnvelopeIndex(primitives, _H)

    weights = {
        "w_s:vimshottari": 1.0,
        "w_s:yogini": 0.6,
        "w_s:naisargika": 0.0,
        "beta:x1": 0.9,
        "beta:x2": 0.4,
        "beta:x3": 0.3,
        "rho:vedha": 0.4,
        "rho:default": 0.25,
        "d:MD": 1.0,
        "d:AD": 0.7,
    }

    clocks = [
        ClockApplicability(
            system_id="vimshottari",
            applicability_state="applicable",
            competence_class="fruition",
            seniority_rank=1,
            is_predictive=True,
            quality=0.92,
        ),
        ClockApplicability(
            system_id="yogini",
            applicability_state="applicable",
            competence_class="flavour",
            seniority_rank=3,
            is_predictive=True,
            quality=0.71,
        ),
    ]

    promise = PromisePrior(
        p=0.62,
        routes=(
            Route(
                event_class="career_change",
                route_rank=1,
                path_node_ids=("graha:Ju", "bhava:10", "event_class:career_change"),
                path_edge_ids=(101,),
                route_gain=0.62,
                is_primary=True,
                suppressed_by=(),
            ),
        ),
        n_routes=1,
        fact_ids=("fact:kin:5001",),
    )

    return S4.FieldEvaluator(
        event_class="career_change",
        lifetime_count=2.0,
        promise=promise,
        clocks=clocks,
        ladder=ladder,
        envelopes=env,
        weights=weights,
        horizon_days=_H,
    )


# ===========================================================================
# (a) Decade-knot presence test
# ===========================================================================

class TestDecadeKnotPresence:
    """assemble_knot_set() must contain all nine interior decade boundaries.

    F5 (SM-R-11) adds d·H/10 for d=1..9 to K_c.  These tests verify the fix
    is in the deployed code and cannot regress silently.
    """

    def _get_knots(self) -> np.ndarray:
        ev = _make_full_horizon_evaluator()
        return assemble_knot_set(ev)

    def test_nine_interior_decade_knots_present(self):
        """All nine interior decade boundaries must appear in the knot array."""
        K = self._get_knots()
        for d in range(1, 10):
            expected = d * _H / 10
            # Use np.isclose to handle float64 precision (d·H/10 is exact for H=36525).
            found = np.any(np.isclose(K, expected, atol=1e-9))
            assert found, (
                f"Decade knot d={d} → {expected:.4f} days missing from assemble_knot_set() output. "
                f"F5 (SM-R-11) fix may have been lost.  K contains {len(K)} knots; "
                f"nearest = {K[np.argmin(np.abs(K - expected))]:.6f}."
            )

    @pytest.mark.parametrize("d", range(1, 10))
    def test_individual_decade_knot(self, d: int):
        """Parametrized: each of the nine decade knots individually."""
        K = self._get_knots()
        expected = d * _H / 10
        found = np.any(np.isclose(K, expected, atol=1e-9))
        assert found, (
            f"Decade knot d={d} ({expected:.4f} days) not in K "
            f"(nearest = {K[np.argmin(np.abs(K - expected))]:.6f})"
        )

    def test_knot_set_starts_at_zero(self):
        """K must begin at 0.0 (the field origin)."""
        K = self._get_knots()
        assert math.isclose(K[0], 0.0, abs_tol=1e-12), f"K[0] = {K[0]} ≠ 0.0"

    def test_knot_set_ends_at_horizon(self):
        """K must end at H = 36525.0 (the field horizon)."""
        K = self._get_knots()
        assert math.isclose(K[-1], _H, abs_tol=1e-9), f"K[-1] = {K[-1]} ≠ {_H}"

    def test_knot_set_monotonically_increasing(self):
        """K must be strictly monotonically increasing (np.unique contract)."""
        K = self._get_knots()
        diffs = np.diff(K)
        assert np.all(diffs > 0), (
            f"K is not strictly monotonically increasing; "
            f"found {np.sum(diffs <= 0)} non-positive consecutive differences."
        )

    def test_maximum_inter_knot_gap_below_decade_length(self):
        """The largest gap between consecutive knots must be < H/10 after F5.

        Before F5, two adjacent dasa knots spanning a decade boundary could
        create a gap of up to one full decade (≈3652.5 days).  F5 closes all
        such seams by inserting the decade boundary itself into K_c, guaranteeing
        that the maximum K-gap is determined by the dasa ladder density, not by
        the absence of decade boundaries.

        F5 guarantees that every decade boundary d·H/10 (d=1..9) is a knot.
        Therefore the maximum gap between consecutive knots is at most H/10
        (one decade), never more.  The bound is ≤ H/10 (not strictly less),
        because adjacent decade knots produce gaps of exactly H/10 in sparse
        ladders.  The key invariant: before F5, a single dasa period spanning
        two decades could produce a gap > H/10; after F5 that is impossible.
        """
        K = self._get_knots()
        max_gap = float(np.max(np.diff(K)))
        decade_length = _H / 10  # ≈ 3652.5 days
        assert max_gap <= decade_length, (
            f"Maximum consecutive knot gap = {max_gap:.3f} days > one decade "
            f"({decade_length:.3f} days).  F5 (SM-R-11) must prevent gaps larger than one decade."
        )


# ===========================================================================
# (b) Full-horizon contiguity test
# ===========================================================================

class TestFullHorizonContiguity:
    """dhara_build_segments() must produce contiguous coverage over [0, H].

    "gaps == 0" means: for every pair of consecutive segments (s_i, s_{i+1}),
    s_i.t_end == s_{i+1}.t_start (within floating-point precision).  No interval
    in [0, H] is left uncovered by the segment list.

    F5 (SM-R-11) is the fix that closes decade-seam gaps in segment coverage.
    These tests confirm that gap == 0 holds at production horizon scale.
    """

    _GAP_TOL: float = 1e-9  # days; segment boundaries are float64 arithmetic

    def _get_segments(self):
        ev = _make_full_horizon_evaluator()
        return dhara_build_segments(ev)

    def test_segments_not_empty(self):
        """dhara_build_segments() must return at least one segment for a non-trivial evaluator."""
        segs = self._get_segments()
        assert segs, "dhara_build_segments() returned an empty list — evaluator is too sparse"

    def test_segments_start_at_zero(self):
        """First segment must start at 0.0."""
        segs = self._get_segments()
        assert math.isclose(segs[0].t_start, 0.0, abs_tol=self._GAP_TOL), (
            f"First segment starts at {segs[0].t_start} ≠ 0.0"
        )

    def test_segments_end_at_horizon(self):
        """Last segment must end at H = 36525.0."""
        segs = self._get_segments()
        assert math.isclose(segs[-1].t_end, _H, abs_tol=self._GAP_TOL), (
            f"Last segment ends at {segs[-1].t_end} ≠ {_H}"
        )

    def test_no_gaps_between_consecutive_segments(self):
        """For every consecutive pair (s_i, s_{i+1}): s_i.t_end == s_{i+1}.t_start.

        gaps == 0 over [0, 36525].
        """
        segs = self._get_segments()
        gaps = []
        for i in range(len(segs) - 1):
            gap = abs(segs[i + 1].t_start - segs[i].t_end)
            if gap > self._GAP_TOL:
                gaps.append((i, segs[i].t_end, segs[i + 1].t_start, gap))
        assert not gaps, (
            f"Found {len(gaps)} gap(s) in segment coverage (gaps > {self._GAP_TOL} days):\n"
            + "\n".join(
                f"  gap after seg[{i}]: {end:.6f} → {start:.6f} (gap = {g:.6g} days)"
                for i, end, start, g in gaps[:5]
            )
        )

    def test_total_segment_length_equals_horizon(self):
        """Sum of all segment lengths must equal H (no holes, no overlaps)."""
        segs = self._get_segments()
        total = sum(s.t_end - s.t_start for s in segs)
        assert math.isclose(total, _H, rel_tol=1e-9), (
            f"Total segment coverage = {total:.6f} days ≠ H = {_H:.6f} days "
            f"(delta = {abs(total - _H):.2e} days)"
        )

    def test_segments_monotonically_increasing(self):
        """Segment t_start values must be strictly increasing."""
        segs = self._get_segments()
        for i in range(len(segs) - 1):
            assert segs[i].t_start < segs[i + 1].t_start, (
                f"Segments not ordered: segs[{i}].t_start={segs[i].t_start} "
                f">= segs[{i+1}].t_start={segs[i+1].t_start}"
            )
