"""
tests/test_dhara_sweep.py — unit tests for dhara_sweep.py.

All tests use unittest.mock.MagicMock for FieldEvaluator. No DB, no IO.
"""
from __future__ import annotations

import math
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from services.ka_kshetra.dhara_sweep import (
    assemble_knot_set,
    compute_knot_sources,
    dhara_build_segments,
)
from services.ka_kshetra.contracts import Segment


# ─────────────────────────────────────────────────────────────────────────────
# Helpers for building mock FieldEvaluators
# ─────────────────────────────────────────────────────────────────────────────

def _make_ladder_period(system_id: str, level: str, lord: str, t_start: float, t_end: float):
    """Return a mock LadderPeriod-like object."""
    p = MagicMock()
    p.system_id = system_id
    p.level = level
    p.lord = lord
    p.t_start = t_start
    p.t_end = t_end
    return p


def _make_evaluator(
    *,
    horizon_days: float = 100.0,
    ladder_periods: dict | None = None,   # {system_id: [LadderPeriod-likes]}
    envelope_breakpoints: list[float] | None = None,
    extra_breakpoints: tuple[float, ...] = (),
    ln_lambda_fn=None,
    lord_stacks_at_fn=None,
    terms_at_fn=None,
) -> MagicMock:
    """Build a mock FieldEvaluator with controllable behaviour."""
    ev = MagicMock()
    ev.horizon_days = horizon_days
    ev.extra_breakpoints = extra_breakpoints

    # Ladder: dict[system_id, list[LadderPeriod]]
    if ladder_periods is None:
        ladder_periods = {}
    ev.ladder = ladder_periods

    # _ladder_bsearch: pre-built for delta-update (mirroring FieldEvaluator.__init__)
    bsearch: dict = {}
    for sid, periods in ladder_periods.items():
        from itertools import groupby
        levels_data = []
        # Group by level (periods must be sorted by level already in mock)
        cur_level = None
        lvl_t_starts: list[float] = []
        lvl_t_ends: list[float] = []
        lvl_lords: list[str] = []
        for p in periods:
            if p.level != cur_level:
                if cur_level is not None:
                    levels_data.append((cur_level, lvl_t_starts, lvl_t_ends, lvl_lords))
                cur_level = p.level
                lvl_t_starts = []
                lvl_t_ends = []
                lvl_lords = []
            lvl_t_starts.append(p.t_start)
            lvl_t_ends.append(p.t_end)
            lvl_lords.append(p.lord)
        if cur_level is not None:
            levels_data.append((cur_level, lvl_t_starts, lvl_t_ends, lvl_lords))
        bsearch[sid] = levels_data
    ev._ladder_bsearch = bsearch

    # Envelope breakpoints
    if envelope_breakpoints is None:
        envelope_breakpoints = []
    ev.envelopes = MagicMock()
    ev.envelopes.breakpoints.return_value = envelope_breakpoints

    # lord_stacks_at
    if lord_stacks_at_fn is not None:
        ev.lord_stacks_at.side_effect = lord_stacks_at_fn
    else:
        ev.lord_stacks_at.return_value = {}

    # terms_at / ln_lambda
    if terms_at_fn is not None:
        ev.terms_at.side_effect = terms_at_fn
    if ln_lambda_fn is not None:
        ev.ln_lambda.side_effect = ln_lambda_fn

    return ev


def _make_terms(ln_lambda: float, suppression_term: float = 1.0):
    """Return a mock HazardTerms with just the fields DHARA uses."""
    t = MagicMock()
    t.ln_lambda = ln_lambda
    t.suppression_term = suppression_term
    return t


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: assemble_knot_set contains all clock and envelope knots
# ─────────────────────────────────────────────────────────────────────────────

def test_assemble_knot_set_contains_clock_and_envelope_knots():
    """K must include every clock boundary and every envelope knot."""
    # Clock knots: period [10, 40] and [40, 80]
    periods = [
        _make_ladder_period('vimshottari', 'MD', 'Sun', 10.0, 40.0),
        _make_ladder_period('vimshottari', 'MD', 'Moon', 40.0, 80.0),
    ]
    env_knots = [5.0, 25.0, 60.0, 95.0]
    ev = _make_evaluator(
        horizon_days=100.0,
        ladder_periods={'vimshottari': periods},
        envelope_breakpoints=env_knots,
    )

    K = assemble_knot_set(ev)

    # Must contain: 0.0, 100.0 (horizon ends)
    assert 0.0 in K
    assert 100.0 in K
    # All clock boundaries
    for t in [10.0, 40.0, 80.0]:
        assert t in K, f"Clock knot {t} missing from K"
    # All envelope knots
    for t in env_knots:
        assert t in K, f"Envelope knot {t} missing from K"

    # K is sorted
    assert list(K) == sorted(K)
    # All values in [0, 100]
    assert float(K[0]) >= 0.0
    assert float(K[-1]) <= 100.0


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: assemble_knot_set deduplicates coincident clock/envelope knots
# ─────────────────────────────────────────────────────────────────────────────

def test_assemble_knot_set_deduplicates():
    """When a clock knot coincides with an envelope knot, K has no duplicates."""
    shared_t = 30.0
    periods = [
        _make_ladder_period('vimshottari', 'MD', 'Sun', 0.0, shared_t),
        _make_ladder_period('vimshottari', 'MD', 'Moon', shared_t, 100.0),
    ]
    # Envelope has the same knot
    env_knots = [shared_t, 60.0]
    ev = _make_evaluator(
        horizon_days=100.0,
        ladder_periods={'vimshottari': periods},
        envelope_breakpoints=env_knots,
    )

    K = assemble_knot_set(ev)

    # No duplicates
    assert len(K) == len(np.unique(K))
    # shared_t appears exactly once
    assert np.sum(K == shared_t) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: knot set excludes kinematics roots (extra_breakpoints)
# ─────────────────────────────────────────────────────────────────────────────

def test_knot_set_excludes_kinematics_roots():
    """extra_breakpoints (kinematics roots) must NOT appear in K."""
    kinematics_root = 42.7
    ev = _make_evaluator(
        horizon_days=100.0,
        ladder_periods={},
        envelope_breakpoints=[20.0, 80.0],
        extra_breakpoints=(kinematics_root, 55.0),
    )

    K = assemble_knot_set(ev)

    # Neither kinematics root should be in K
    assert kinematics_root not in K
    assert 55.0 not in K
    # But envelope knots should be
    assert 20.0 in K
    assert 80.0 in K


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: suppression detection uses multiplicative identity (F-02)
# ─────────────────────────────────────────────────────────────────────────────

def test_suppression_detection_uses_multiplicative_identity():
    """suppression_term == 1.0 means no suppression; != 1.0 means active.

    This is F-02: suppression_term = exp(suppression_log) is ALWAYS > 0,
    so comparing != 0.0 would always be True. The correct check is != 1.0
    (the multiplicative identity, i.e. exp(0) = 1.0 means no suppression).
    """
    # Case A: suppression_term = 1.0 everywhere → no suppression → single segment,
    #         no bisection, refinement_depth = 0.
    def terms_no_suppression(t: float):
        # ln_lambda is exactly linear: a = -1.0, gamma = 0.01 => b = -1.0 + 0.01*h
        ln_lam = -1.0 + 0.01 * t
        return _make_terms(ln_lam, suppression_term=1.0)

    ev_no_sup = _make_evaluator(
        horizon_days=10.0,
        ladder_periods={},
        envelope_breakpoints=[5.0],
        terms_at_fn=terms_no_suppression,
        ln_lambda_fn=lambda t: -1.0 + 0.01 * t,
    )
    segs_no_sup = dhara_build_segments(ev_no_sup)
    # All segments should have refinement_depth = 0 (no bisection triggered)
    for seg in segs_no_sup:
        assert seg.refinement_depth == 0, (
            f"Unexpected bisection for non-suppression segment: {seg}"
        )

    # Case B: suppression_term = 0.9 (< 1.0) somewhere → active → DHARA will
    #         check the midpoint residual. The important thing to test is that
    #         suppression_term=0.9 is recognized as active.
    #
    # We set up a tiny evaluator where the true ln_lambda is concave so the
    # residual check fires. Use ln_lambda = -1 - (t-5)^2 on [0,10] with knots
    # only at 0 and 10. The midpoint residual for the linear interpolant is
    # |-1 - 0 - (0.5*(-1-(-1))| = ... let's compute:
    #   a = ln_lam(0) = -1 - 25 = -26
    #   b = ln_lam(10) = -1 - 25 = -26
    #   gamma = (b-a)/10 = 0
    #   ln_mid_stored = -26 + 0*(5-0) = -26
    #   ln_mid_true = -1 - (5-5)^2 = -1
    #   residual = |-1 - (-26)| = 25 >> 0.02
    # So bisection WILL fire.
    # Suppression_term is 0.9 everywhere.

    def ln_lam_concave(t: float) -> float:
        return -1.0 - (t - 5.0) ** 2

    def terms_with_suppression(t: float):
        return _make_terms(ln_lam_concave(t), suppression_term=0.9)

    ev_sup = _make_evaluator(
        horizon_days=10.0,
        ladder_periods={},
        envelope_breakpoints=[],  # K = {0, 10}
        terms_at_fn=terms_with_suppression,
        ln_lambda_fn=ln_lam_concave,
    )
    segs_sup = dhara_build_segments(ev_sup)
    # With suppression_term=0.9 and a highly concave function, bisection fires:
    # we should get 2 sub-segments instead of 1.
    assert len(segs_sup) == 2, (
        f"Expected 2 sub-segments (bisection triggered by suppression), got {len(segs_sup)}"
    )
    for seg in segs_sup:
        assert seg.refinement_depth == 1


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: non-suppression segments have exact (alpha, gamma) — no bisection
# ─────────────────────────────────────────────────────────────────────────────

def test_dhara_build_segments_nosuppression_exact_linear():
    """When suppression_term == 1.0 everywhere, each segment's (alpha, gamma)
    equals the exact log-linear slope — no bisection, refinement_depth == 0.

    Spec: between consecutive knots, clock term is constant and modifier term
    is linear, so ln lambda is EXACTLY linear. The midpoint residual is
    identically zero. DHARA stores the exact endpoints without any midpoint
    evaluation.
    """
    # True ln_lambda: constant -2.0 (flat, no slope)
    ALPHA = -2.0
    GAMMA = 0.0

    def ln_lam_flat(t: float) -> float:
        return ALPHA

    def terms_flat(t: float):
        return _make_terms(ALPHA, suppression_term=1.0)

    # Three clock knots produce two inter-knot intervals: [0,50] and [50,100].
    periods = [
        _make_ladder_period('vimshottari', 'MD', 'Sun', 0.0, 50.0),
        _make_ladder_period('vimshottari', 'MD', 'Moon', 50.0, 100.0),
    ]
    ev = _make_evaluator(
        horizon_days=100.0,
        ladder_periods={'vimshottari': periods},
        envelope_breakpoints=[],
        terms_at_fn=terms_flat,
        ln_lambda_fn=ln_lam_flat,
    )

    segs = dhara_build_segments(ev)

    # Two inter-knot intervals → two segments (no bisection)
    assert len(segs) == 2, f"Expected 2 segments, got {len(segs)}"
    for i, seg in enumerate(segs):
        assert seg.index == i
        assert seg.refinement_depth == 0
        assert not seg.refinement_exhausted
        assert seg.refinement_residual is None
        # alpha equals ln_lambda at t_start (exact)
        assert math.isclose(seg.alpha, ALPHA, abs_tol=1e-12), (
            f"Segment {i}: alpha={seg.alpha} != expected {ALPHA}"
        )
        # gamma should be zero (flat field)
        assert abs(seg.gamma) < 1e-12, (
            f"Segment {i}: gamma={seg.gamma} should be 0 for flat field"
        )

    # Segments are contiguous
    assert math.isclose(segs[0].t_start, 0.0)
    assert math.isclose(segs[0].t_end, 50.0)
    assert math.isclose(segs[1].t_start, 50.0)
    assert math.isclose(segs[1].t_end, 100.0)


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: contiguity and index invariant
# ─────────────────────────────────────────────────────────────────────────────

def test_dhara_build_segments_contiguous_and_indexed():
    """Segments must be contiguous, cover [K[0], K[-1]], and Segment.index == position."""
    periods = [
        _make_ladder_period('vimshottari', 'MD', 'Sun', 0.0, 30.0),
        _make_ladder_period('vimshottari', 'MD', 'Moon', 30.0, 70.0),
        _make_ladder_period('vimshottari', 'MD', 'Mars', 70.0, 100.0),
    ]
    env_knots = [15.0, 50.0, 85.0]

    def ln_lam(t: float) -> float:
        return -1.5 + 0.005 * t  # gentle linear ramp

    def terms_fn(t: float):
        return _make_terms(ln_lam(t), suppression_term=1.0)

    ev = _make_evaluator(
        horizon_days=100.0,
        ladder_periods={'vimshottari': periods},
        envelope_breakpoints=env_knots,
        terms_at_fn=terms_fn,
        ln_lambda_fn=ln_lam,
    )

    segs = dhara_build_segments(ev)

    assert len(segs) > 0
    # Index invariant
    for i, seg in enumerate(segs):
        assert seg.index == i
    # Contiguity
    for a, b in zip(segs, segs[1:]):
        assert math.isclose(a.t_end, b.t_start, abs_tol=1e-12), (
            f"Gap between segments: {a.t_end} != {b.t_start}"
        )
    # Coverage
    assert math.isclose(segs[0].t_start, 0.0)
    assert math.isclose(segs[-1].t_end, 100.0)


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: degenerate case — fewer than 2 knots returns empty list
# ─────────────────────────────────────────────────────────────────────────────

def test_dhara_build_segments_empty_on_single_knot():
    """If K has < 2 knots, dhara_build_segments returns []."""
    ev = _make_evaluator(
        horizon_days=0.0,   # horizon_days == 0 → K = {0.0} (single knot)
        ladder_periods={},
        envelope_breakpoints=[],
    )
    segs = dhara_build_segments(ev)
    assert segs == []


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: compute_knot_sources labels correctly
# ─────────────────────────────────────────────────────────────────────────────

def test_compute_knot_sources_labels():
    """'c' for clock-only, 'e' for envelope-only, 'ce' for both."""
    K_c = {0.0, 30.0, 100.0}
    K_e = {20.0, 30.0, 70.0}
    # K = sorted union
    K_all = sorted(K_c | K_e)
    K = np.array(K_all, dtype=np.float64)

    sources = compute_knot_sources(K, K_c, K_e)

    assert len(sources) == len(K)
    mapping = {float(K[i]): sources[i] for i in range(len(K))}
    assert mapping[0.0] == 'c'    # clock-only
    assert mapping[20.0] == 'e'   # envelope-only
    assert mapping[30.0] == 'ce'  # both
    assert mapping[70.0] == 'e'   # envelope-only
    assert mapping[100.0] == 'c'  # clock-only
