"""
services/ka_kshetra/dhara_sweep.py — DHARA event-driven sweep algorithm.

DHARA (Deterministic Hazard-rate Analytic Recomputation Architecture) replaces
`integrator.build_segments()` for the analytic engine. It sweeps over the exact
global knot set K = sort(K_c UNION K_e) — dasa-boundary clock knots plus envelope
primitive knots — rather than the adaptive-bisection approach that redundantly
evaluates ln_lambda at midpoints of intervals that are already exactly log-linear.

The key mathematical finding (DHARA_DESIGN_v1_0.md §1.3):

  Between consecutive knots in K, ln lambda_e(t) is:
    - EXACTLY LOG-LINEAR when no suppression is active (suppression_term == 1.0),
      because the clock term is piecewise-constant and the modifier term is
      piecewise-linear — so the sum is affine.
    - LOG-AFFINE (concave) when suppression is active, because ln(1 - rho*u(t))
      is a log of a linear function. One level of bisection at the midpoint catches
      the cases where the concavity error exceeds tau = 0.02 nats.

PURITY: no DB, no IO, no RNG. Same constraint as hazard.py and integrator.py.
The same code path must serve (a) the real build and (b) the R=256 null replicates.

Authority: DHARA_DESIGN_v1_0.md §2 (algorithm), §1 (mathematical basis).
Spec version: v1.1 (F-02 suppression check corrected to != 1.0; F-09 delta-update
runtime assertion added).
"""
from __future__ import annotations

import logging
import math
from dataclasses import replace
from typing import TYPE_CHECKING

import numpy as np

from services.ka_kshetra.contracts import Segment
from services.ka_kshetra.integrator import DEFAULT_TAU

if TYPE_CHECKING:
    from services.ka_kshetra.stage4_field import FieldEvaluator

logger = logging.getLogger(__name__)

#: How often (in clock-knot count) to fire the F-09 delta-update correctness
#: assertion. Every 100th clock knot = ~400 extra lord_stacks_at() calls per
#: class at 40K knots, negligible vs. the build cost.
_F09_ASSERTION_STRIDE: int = 100


# ── Section 2.1 — global knot set assembly ────────────────────────────────────

def assemble_knot_set(evaluator: "FieldEvaluator") -> np.ndarray:
    """Build K = sort(K_c UNION K_e), clipped to [0, horizon_days].

    K_c: all t_start and t_end from every LadderPeriod across all systems,
         plus 0.0 and horizon_days.
    K_e: evaluator.envelopes.breakpoints() — the envelope primitive knot times.
    K  : sorted, deduped union, float64.

    EXCLUDES extra_breakpoints (kinematics roots): those are astronomical event
    times used only to improve sampling density in the adaptive scheme. Between
    consecutive K_c / K_e knots, ln lambda is already exactly linear (or concave),
    so adding kinematics roots provides no information to DHARA.

    Returns a float64 numpy array of monotonically increasing knot times.
    """
    H = evaluator.horizon_days

    # K_c: dasa-boundary clock knots (all systems, all levels) + horizon ends.
    K_c: set[float] = {0.0, H}
    for periods in evaluator.ladder.values():
        for p in periods:
            if math.isfinite(p.t_start):
                K_c.add(p.t_start)
            if math.isfinite(p.t_end):
                K_c.add(p.t_end)

    # K_e: envelope primitive knot times.
    K_e: set[float] = set()
    for t in evaluator.envelopes.breakpoints():
        if math.isfinite(t):
            K_e.add(t)

    # Union, clip to [0, H], sort, deduplicate via np.unique.
    merged = [t for t in (K_c | K_e) if 0.0 <= t <= H]
    return np.unique(np.array(merged, dtype=np.float64))


def compute_knot_sources(
    K: np.ndarray,
    K_c: set[float],
    K_e: set[float],
) -> np.ndarray:
    """Annotation array marking each knot's provenance: 'c', 'e', or 'ce'.

    'c'  — clock knot only (dasa boundary)
    'e'  — envelope knot only (primitive breakpoint)
    'ce' — both

    The array has the same length as K and dtype=object (Python str).
    Used for diagnostics and testing; not required by the sweep itself.
    """
    sources = np.empty(len(K), dtype=object)
    for i, t in enumerate(K):
        in_c = t in K_c
        in_e = t in K_e
        if in_c and in_e:
            sources[i] = 'ce'
        elif in_c:
            sources[i] = 'c'
        else:
            sources[i] = 'e'
    return sources


# ── Section 2.2 — delta-update lord stacks ────────────────────────────────────

def _delta_update_lord_stacks(
    current_stacks: dict[str, list[tuple[str, str]]],
    t: float,
    ladder_bsearch: dict[str, list[tuple[str, list[float], list[float], list[str]]]],
) -> None:
    """Update current_stacks IN PLACE at clock knot t.

    At a clock knot, lord_stacks_at(t) uses [t_start, t_end) half-open
    containment — exactly the same convention as FieldEvaluator.lord_stacks_at.
    We re-derive each system's stack from scratch at t using the pre-built
    binary-search arrays (O(log N) per level), matching the _ladder_bsearch
    approach in FieldEvaluator.

    This REPLACES the running stack for every system — simple and correct.
    The F-09 assertion verifies equivalence to a fresh lord_stacks_at(t) call.
    """
    import bisect as _bisect
    new_stacks: dict[str, list[tuple[str, str]]] = {}
    for sid, levels_data in ladder_bsearch.items():
        stack: list[tuple[str, str]] = []
        for level, lvl_t_starts, lvl_t_ends, lvl_lords in levels_data:
            idx = _bisect.bisect_right(lvl_t_starts, t) - 1
            if idx >= 0 and lvl_t_ends[idx] > t:
                stack.append((level, lvl_lords[idx]))
        if stack:
            new_stacks[sid] = stack
    current_stacks.clear()
    current_stacks.update(new_stacks)


# ── Section 2.4 — the DHARA sweep ─────────────────────────────────────────────

def dhara_build_segments(evaluator: "FieldEvaluator") -> list[Segment]:
    """Build the stored log-linear segments via the DHARA event-driven sweep.

    Replaces integrator.build_segments() for the analytic engine.

    Algorithm (DHARA_DESIGN_v1_0.md §2.4):
      1. Assemble K = sort(K_c UNION K_e) — the exact global knot set.
      2. Initialize running lord stacks at K[0] via lord_stacks_at(K[0]).
      3. Sweep K[0..n-2]:
         a. At each right endpoint t_{i+1}, if it is a clock knot, delta-update
            the lord stacks.
         b. Evaluate terms_at(t_{i+1}) using the updated stacks.
         c. Determine suppression activity: terms.suppression_term != 1.0
            (F-02 corrected — suppression_term = exp(suppression_log); neutral
            value is 1.0, not 0.0).
         d. Non-suppression: store exact (alpha, gamma) — residual is identically
            zero, no bisection needed.
         e. Suppression-active: check midpoint residual; if > tau, apply one
            level of bisection (create two sub-segments instead of one).
      4. Every _F09_ASSERTION_STRIDE clock knots, assert delta stacks == fresh
         lord_stacks_at(t) (F-09 runtime correctness check).

    Returns a list of Segment objects with contiguous, non-overlapping spans
    covering [K[0], K[-1]], indexed from 0.
    """
    K = assemble_knot_set(evaluator)
    n = len(K)
    if n < 2:
        return []

    H = evaluator.horizon_days

    # Build K_c as a set for O(1) membership tests during the sweep.
    K_c_set: set[float] = {0.0, H}
    for periods in evaluator.ladder.values():
        for p in periods:
            if math.isfinite(p.t_start):
                K_c_set.add(p.t_start)
            if math.isfinite(p.t_end):
                K_c_set.add(p.t_end)

    # Initialize running lord stacks at the first knot.
    running_stacks: dict[str, list[tuple[str, str]]] = evaluator.lord_stacks_at(K[0])
    clock_knot_counter = 0

    # Evaluate hazard terms at the first knot — reused as the left endpoint for
    # the first segment to avoid a redundant evaluation.
    terms_left = evaluator.terms_at(K[0])

    out: list[Segment] = []

    for i in range(n - 1):
        t_i = float(K[i])
        t_ip1 = float(K[i + 1])

        # Step (a): if t_{i+1} is a clock knot, update lord stacks BEFORE
        # evaluating terms there. half-open [t_start, t_end) convention means
        # t_{i+1} belongs to the NEW period (same as lord_stacks_at(t_{i+1})).
        if t_ip1 in K_c_set:
            _delta_update_lord_stacks(running_stacks, t_ip1, evaluator._ladder_bsearch)
            clock_knot_counter += 1

            # F-09: every _F09_ASSERTION_STRIDE clock knots, assert equivalence
            # to a fresh lord_stacks_at(t) call.
            if clock_knot_counter % _F09_ASSERTION_STRIDE == 0:
                fresh = evaluator.lord_stacks_at(t_ip1)
                assert fresh == running_stacks, (
                    f"F-09 delta-update assertion failed at t={t_ip1}: "
                    f"delta_stacks={running_stacks!r} != fresh={fresh!r}"
                )

        # Step (b): evaluate terms at the right endpoint using updated stacks.
        terms_right = evaluator.terms_at(t_ip1)

        a = terms_left.ln_lambda   # ln lambda(t_i^+)
        b = terms_right.ln_lambda  # ln lambda(t_{i+1}^+)

        width = t_ip1 - t_i
        if width < 1e-12:
            gamma = 0.0
        else:
            gamma = (b - a) / width

        # Step (c): suppression detection — F-02 corrected.
        # suppression_term = exp(suppression_log); neutral (no suppression) = 1.0.
        suppression_active = (
            terms_left.suppression_term != 1.0
            or terms_right.suppression_term != 1.0
        )

        if not suppression_active:
            # Step (d): non-suppression — stored form is EXACTLY log-linear.
            # Residual is identically zero; no bisection needed.
            out.append(Segment(
                index=len(out),
                t_start=t_i,
                t_end=t_ip1,
                alpha=a,
                gamma=gamma,
                refinement_depth=0,
                refinement_exhausted=False,
                refinement_residual=None,
            ))
        else:
            # Step (e): suppression-active — the true ln lambda is concave
            # (not linear). The stored linear interpolant may deviate from the
            # true function by up to (1/8)*rho^2*(delta_u)^2/(1-rho*u)^2 nats
            # (F-03 corrected bound). Apply one midpoint check; if residual > tau,
            # bisect once to produce two sub-segments.
            t_mid = 0.5 * (t_i + t_ip1)
            ln_mid_true = evaluator.ln_lambda(t_mid)
            ln_mid_stored = a + gamma * (t_mid - t_i)
            residual = abs(ln_mid_true - ln_mid_stored)

            if residual <= DEFAULT_TAU:
                # Good enough — store as a single segment.
                out.append(Segment(
                    index=len(out),
                    t_start=t_i,
                    t_end=t_ip1,
                    alpha=a,
                    gamma=gamma,
                    refinement_depth=0,
                    refinement_exhausted=False,
                    refinement_residual=None,
                ))
            else:
                # Bisect: two sub-segments. Left half uses (a, ln_mid_true);
                # right half uses (ln_mid_true, b).
                w_left = t_mid - t_i
                g_left = (ln_mid_true - a) / w_left if w_left >= 1e-12 else 0.0
                out.append(Segment(
                    index=len(out),
                    t_start=t_i,
                    t_end=t_mid,
                    alpha=a,
                    gamma=g_left,
                    refinement_depth=1,
                    refinement_exhausted=False,
                    refinement_residual=None,
                ))
                w_right = t_ip1 - t_mid
                g_right = (b - ln_mid_true) / w_right if w_right >= 1e-12 else 0.0
                out.append(Segment(
                    index=len(out),
                    t_start=t_mid,
                    t_end=t_ip1,
                    alpha=ln_mid_true,
                    gamma=g_right,
                    refinement_depth=1,
                    refinement_exhausted=False,
                    refinement_residual=None,
                ))

        # Advance: left terms for the next iteration = right terms of this one.
        # No re-evaluation needed at t_{i+1}.
        terms_left = terms_right

    # Re-index so Segment.index == position in list (invariant the integrator
    # module and its callers expect).
    return [replace(s, index=i) for i, s in enumerate(out)]


__all__ = [
    'assemble_knot_set',
    'compute_knot_sources',
    'dhara_build_segments',
]
