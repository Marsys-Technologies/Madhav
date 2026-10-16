"""Trial DHARA adapter and independent, strict null-statistic comparator.

The estimator remains the existing daily midpoint / linearly shifted E grid,
ten duration buckets and pooled order statistic. Only C/full evaluation is
replaced by the compact field. An analytic field bound does NOT grant a null
reproduction PASS: maxima, quantile and tail ranks are compared separately.
"""
from __future__ import annotations

import math
from typing import Mapping, Sequence

import numpy as np

from services.ka_kshetra.contracts import NullResult
from services.ka_kshetra.stage4_field import EnvelopeIndex, FieldEvaluator
from services.ka_kshetra.stage5_null import (
    DURATION_BUCKETS, Q_QUANTILE, QuantilePool, sliding_window_max, null_p, _EXCEEDANCE_REL_TOL,
)
from .compiler import compile_field

NULL_RTOL = 1e-12
NULL_ATOL = 1e-12


def compute_null(ev: FieldEvaluator, *, replicates: int = 1024, alpha: float = .05) -> NullResult:
    if type(replicates) is not int or replicates < 2 or not 0 < alpha < 1:
        raise ValueError('integer replicates >= 2 and alpha in (0,1) required')
    H = ev.horizon_days
    if not math.isfinite(H) or H < 1 or H != int(H):
        raise ValueError('the existing daily estimator requires an integer-day horizon')
    full = compile_field(ev).field
    # Preserve the reference's constructor arguments and operation order. Its
    # clock-only evaluator defaults shape_only=False, even for a shape-only ev;
    # changing that here would change the comparator's estimand.
    clock_ev = FieldEvaluator(
        event_class=ev.event_class, lifetime_count=ev.lifetime_count, promise=ev.promise,
        clocks=ev.clocks, ladder=ev.ladder, envelopes=EnvelopeIndex([], H),
        weights=ev.weights, horizon_days=H, baseline_source=ev.baseline_source,
        extra_breakpoints=ev.extra_breakpoints,
    )
    clock = compile_field(clock_ev).field
    n = int(H)
    t_grid = np.arange(n, dtype=np.float64) + .5
    C_fine = np.fromiter((clock.ln_lambda(t) for t in t_grid), dtype=np.float64, count=n)
    full_fine = np.fromiter((full.ln_lambda(t) for t in t_grid), dtype=np.float64, count=n)
    E_fine = full_fine - C_fine
    pool = QuantilePool(quantile=Q_QUANTILE, expected_total=(replicates - 1) * n)
    stats = {int(b): [] for b in DURATION_BUCKETS}
    shift_step = H / replicates
    for r in range(1, replicates):
        delta = r * shift_step
        src_idx = (t_grid - delta - .5) % H
        i_low = np.floor(src_idx).astype(np.intp) % n
        i_high = (i_low + 1) % n
        frac = src_idx - np.floor(src_idx)
        E_shifted = E_fine[i_low] * (1 - frac) + E_fine[i_high] * frac
        lam = np.exp(C_fine + E_shifted)
        cum = np.empty(n + 1, dtype=np.float64)
        cum[0] = 0.0
        cum[1:] = np.cumsum(lam)
        for b in DURATION_BUCKETS:
            stats[int(b)].append(sliding_window_max(cum, int(b)))
        pool.add(lam)
    return NullResult(
        replicates=replicates, shift_count=replicates - 1, horizon_days=H,
        shift_grid_step=shift_step, q_threshold=pool.value(), max_stats=stats, alpha=alpha,
    )


def compare_null(reference: NullResult, candidate: NullResult, *,
                 observations: Mapping[int, Sequence[float]]) -> dict:
    """No proxy greens: malformed/empty results and changed tail ties fail."""
    context_equal = (
        type(reference.replicates) is int and reference.replicates >= 2 and
        reference.replicates == candidate.replicates and
        reference.shift_count == candidate.shift_count == reference.replicates - 1 and
        reference.horizon_days == candidate.horizon_days and reference.horizon_days > 0 and
        reference.shift_grid_step == candidate.shift_grid_step == reference.horizon_days / reference.replicates and
        reference.alpha == candidate.alpha and 0 < reference.alpha < 1 and
        reference.resolution == candidate.resolution == 1 / reference.replicates
    )
    expected_buckets = {int(b) for b in DURATION_BUCKETS}
    shape_ok = set(reference.max_stats) == set(candidate.max_stats) == expected_buckets
    if shape_ok:
        shape_ok = all(
            len(reference.max_stats[b]) == len(candidate.max_stats[b]) == reference.replicates - 1 and
            all(math.isfinite(v) for v in reference.max_stats[b] + candidate.max_stats[b])
            for b in expected_buckets
        )
    max_error = None
    stats_equal = False
    if shape_ok:
        max_error = max(abs(a - b) for bucket in expected_buckets
                        for a, b in zip(reference.max_stats[bucket], candidate.max_stats[bucket]))
        stats_equal = all(math.isclose(a, b, rel_tol=NULL_RTOL, abs_tol=NULL_ATOL)
                          for bucket in expected_buckets
                          for a, b in zip(reference.max_stats[bucket], candidate.max_stats[bucket]))
    q_ok = (reference.q_threshold is not None and candidate.q_threshold is not None and
            math.isfinite(reference.q_threshold) and math.isfinite(candidate.q_threshold))
    q_error = abs(reference.q_threshold - candidate.q_threshold) if q_ok else None
    q_equal = q_ok and math.isclose(reference.q_threshold, candidate.q_threshold,
                                  rel_tol=NULL_RTOL, abs_tol=NULL_ATOL)
    probes_ok = (bool(observations) and all(b in expected_buckets and len(probes) > 0 and
                 all(math.isfinite(v) for v in probes) for b, probes in observations.items()))
    tails_equal = bool(shape_ok and probes_ok and all(
        null_p(reference.max_stats[b], obs) == null_p(candidate.max_stats[b], obs)
        for b, probes in observations.items() for obs in probes
    ))
    return {
        'passed': bool(context_equal and shape_ok and stats_equal and q_equal and tails_equal),
        'context_equal': bool(context_equal), 'shape_valid': bool(shape_ok),
        'maxima_equal': bool(stats_equal), 'max_stat_abs_error': max_error,
        'quantile_equal': bool(q_equal), 'q_abs_error': q_error,
        'tail_probabilities_equal': tails_equal,
        'tail_probe_count': sum(len(v) for v in observations.values()),
        'rtol': NULL_RTOL, 'atol': NULL_ATOL,
        'tail_exceedance_relative_tolerance': _EXCEEDANCE_REL_TOL,
    }
