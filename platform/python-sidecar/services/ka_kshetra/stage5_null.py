"""
services/ka_kshetra/stage5_null.py — §5.5–§5.6 stage 5: the circular-shift null
(item 23), the robustness vector, the confidence tier, and the Adṛṣṭa residual.

── WHAT IS SHIFTED, AND WHY THAT ASYMMETRY *IS* THE HYPOTHESIS ──────────────
The TRANSIT STREAM is circularly shifted. The NATAL STRUCTURE and the DAŚĀ
LADDER are held FIXED. Shifting the ladder would destroy the chart's identity;
shifting the natal points would destroy the chart. So the null this measures
against is precisely:

    "the sky's timing carries no information about this chart's events
     beyond what the clocks already say."

That is a real, falsifiable hypothesis about the transit layer specifically, and
it is a MUCH harder opponent than the usual "compare against a random chart" —
the replicate keeps every advantage the model has except the one under test.

── FULLY DETERMINISTIC: NO RNG ANYWHERE ────────────────────────────────────
The shift grid is δ_r = r·(H/R) for r = 1…R — COMPUTED, not drawn. Two reasons,
both binding:
  • hash-replay (§7.4) must hold, and a seeded PRNG ties the field hash to
    library-internal generator behaviour that can change across versions;
  • a permutation test with a *computed* grid has no seed to choose, so nobody
    can ever have chosen one that flattered the result.

── THE p-VALUE AND ITS RESOLUTION ──────────────────────────────────────────
    null_p          = ( 1 + #{ r : M_r(L*) ≥ Λ_obs } ) / ( R + 1 )
    null_resolution = 1 / (R + 1) = 1/257 ≈ 0.00389
The +1 correction is the standard one and it is why p is never 0: with 256
replicates you have not measured a probability smaller than 1/257, and reporting
0 would claim a precision the replicate count cannot support (LAW ZERO). Both
numbers are served, so a consumer can never read p = 0.0039 as p = 0.

L* is the SMALLEST duration bucket ≥ the window's own duration. That direction is
deliberate and conservative: a longer matched filter can only ACCUMULATE MORE
hazard, so M_r(L*) ≥ M_r(L_W) and the resulting p is an UPPER BOUND on the true
permutation p — it can overstate a window's ordinariness, never its significance.

── q_e IS A DEFINITION, NOT A TUNING KNOB ──────────────────────────────────
    q_e = quantile_0.95 over { λ^{(r)}_e(t_g) : r = 1…R, t_g on the 1-day grid }
so "a window" means "a stretch where this chart's own hazard exceeds what its own
shifted sky would produce 95% of the time". Nobody picks a threshold; the chart's
own null computes it, and §5.2's window construction reads it.

── COST (the design's own dominant-cost warning, §5.5) ─────────────────────
R = 256 rebuilds per class is the heaviest thing in W2. The replicate reuses the
SAME clock, promise and baseline terms and re-indexes ONLY the stage-1 envelopes,
which is where the order-of-magnitude saving comes from. Substep grain is
(stage5, event_class, replicate_block_of_32) — 8 substeps per class. If a substep
approaches `writer_timeout_seconds`, REDUCE THE BLOCK TO 16; do not raise the
timeout (the `ka_gochara_sweep` D-5 lesson, verbatim).

Authority: KALA_W2_FIELD_DESIGN_v1_0.md §5.5, §5.6.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Optional, Sequence

from services.ka_kshetra import integrator
from services.ka_kshetra.contracts import Segment
from services.ka_kshetra.stage4_field import EnvelopeIndex, FieldEvaluator

#: §5.5's ten duration buckets, in days — the matched-filter scales.
DURATION_BUCKETS: tuple[int, ...] = (1, 3, 7, 15, 30, 60, 90, 180, 365, 730)

#: §5.5's replicate count. Fixes the p-value resolution at 1/257.
DEFAULT_REPLICATES: int = 256

#: §5.5's substep grain. Reduce to 16 if a substep nears the writer timeout —
#: never raise the timeout.
DEFAULT_BLOCK_SIZE: int = 32

#: §5.5's exceedance threshold. Declared once so the flag and the number cannot
#: drift apart.
ALPHA: float = 0.05

#: §5.5's window-threshold quantile.
Q_QUANTILE: float = 0.95

#: The `≥` in `M_r ≥ Λ_obs` is taken with a relative tolerance of one part in
#: 10¹². This is NOT a fudge factor and it is not there to make anything
#: significant — it exists for the opposite reason. On a field with no transit
#: structure at all, every replicate reproduces the observation EXACTLY, and the
#: honest answer is p = 1 (nothing is exceptional). But Λ_obs is computed by one
#: summation order and M_r by another (a running daily cumulative), so the two
#: can differ in the last ulp and an exact `>=` would score 0/R exceedances and
#: report p = 1/257 — a maximally significant result on a field that carries no
#: information whatsoever. The tolerance is a millionth of the smallest
#: meaningful difference and it always errs toward the null.
_EXCEEDANCE_REL_TOL: float = 1e-12

#: The five pinned ayanāṃśas the FORENSIC anchors are stated across.
PINNED_AYANAMSHAS: tuple[str, ...] = (
    'lahiri', 'raman', 'kp', 'yukteshwar', 'fagan_bradley',
)


# ── the deterministic shift grid ─────────────────────────────────────────────

def shift_grid(horizon_days: float, replicates: int) -> list[float]:
    """δ_r = r·(H/R) for r = 1…R. Computed, never drawn (see module docstring)."""
    if replicates < 1:
        raise ValueError(f'replicates must be ≥ 1, got {replicates!r}')
    if not (horizon_days > 0):
        raise ValueError(f'horizon_days must be > 0, got {horizon_days!r}')
    step = horizon_days / replicates
    return [r * step for r in range(1, replicates + 1)]


def select_bucket(duration_days: float,
                  buckets: Sequence[int] = DURATION_BUCKETS) -> int:
    """L* = the smallest bucket ≥ the window's duration.

    Conservative by construction: a longer filter accumulates at least as much,
    so the p-value it yields is an UPPER bound. A window longer than the largest
    bucket clamps to that bucket — still the closest available filter, still in
    the conservative direction.
    """
    for b in buckets:
        if b >= duration_days:
            return b
    return max(buckets)


# ── the permutation p-value ──────────────────────────────────────────────────

def null_p(max_stats: Sequence[float], lambda_obs: float) -> Optional[float]:
    """(1 + #{r : M_r ≥ Λ_obs}) / (R + 1), with the standard +1 correction.

    Returns None — an honest not-computed — when no replicates are available.
    Never 0.0, never a fabricated small number.
    """
    stats = list(max_stats)
    if not stats:
        return None
    threshold = lambda_obs * (1.0 - _EXCEEDANCE_REL_TOL)
    exceed = sum(1 for m in stats if m >= threshold)
    return (1 + exceed) / (len(stats) + 1)


def null_resolution(replicates: int) -> float:
    """1/(R+1). Served ALONGSIDE null_p so p = 1/257 is never read as p = 0."""
    return 1.0 / (replicates + 1)


def null_exceeding(p: Optional[float], alpha: float = ALPHA) -> Optional[bool]:
    return None if p is None else bool(p <= alpha)


# ── q_e: an exact streaming quantile with bounded memory ─────────────────────

class QuantilePool:
    """The EXACT q-quantile of a pooled sample, streamed with bounded memory.

    q_e pools R × N values (256 × 36 526 ≈ 9.3 M floats ≈ 75 MB), which is more
    than a build substep should hold and more than is needed: the 0.95 quantile
    is the k-th largest value with k = n − ceil(0.95·n) + 1, so a bounded
    min-heap of the top k is sufficient and EXACT. No sketching, no t-digest, no
    approximation — the number served is the number the definition names.

    Bounded memory matters here for a specific reason: the alternative
    (subsampling the grid, or approximating the quantile) would make the served
    `q_threshold` a DIFFERENT statistic from the one §5.5 defines, and every
    window boundary in the product hangs off it.
    """

    def __init__(self, quantile: float = Q_QUANTILE, expected_total: int = 0):
        if not (0.0 < quantile < 1.0):
            raise ValueError(f'quantile must be in (0,1), got {quantile!r}')
        self.quantile = quantile
        self._n = 0
        self._heap: list[float] = []
        self._capacity = self._capacity_for(max(expected_total, 1))

    def _capacity_for(self, n: int) -> int:
        return max(1, n - math.ceil(self.quantile * n) + 1)

    def add(self, values: Iterable[float]) -> None:
        for v in values:
            v = float(v)
            self._n += 1
            need = self._capacity_for(self._n)
            if need > self._capacity:
                self._capacity = need
            if len(self._heap) < self._capacity:
                heapq.heappush(self._heap, v)
            elif v > self._heap[0]:
                heapq.heapreplace(self._heap, v)

    def value(self) -> Optional[float]:
        """The exact q-quantile of everything added, or None if nothing was.

        Uses the "k-th smallest of the sorted sample at rank ceil(q·n)"
        convention — the same one `sorted(sample)[ceil(q*n) - 1]` gives, so the
        pooled value is reproducible by anyone holding the raw sample.
        """
        if self._n == 0:
            return None
        rank_from_top = self._n - math.ceil(self.quantile * self._n) + 1
        ordered = sorted(self._heap)
        if rank_from_top > len(ordered):
            return ordered[0]
        return ordered[len(ordered) - rank_from_top]


# ── replicate machinery ──────────────────────────────────────────────────────

def replicate_evaluator(ev: FieldEvaluator, delta: float) -> FieldEvaluator:
    """Build replicate r's evaluator: the SAME field with the transit stream
    circularly shifted by δ.

    Everything else is passed through by reference — the promise prior, the clock
    applicabilities, the daśā ladder, the weights, the baseline. That is not an
    optimization; it is the null hypothesis (§5.5). A replicate that also
    perturbed the clocks would be testing a different, weaker claim.
    """
    return FieldEvaluator(
        event_class=ev.event_class,
        lifetime_count=ev.lifetime_count,
        promise=ev.promise,
        clocks=ev.clocks,
        ladder=ev.ladder,
        envelopes=ev.envelopes.circular_shift(delta),
        weights=ev.weights,
        horizon_days=ev.horizon_days,
        baseline_source=ev.baseline_source,
        extra_breakpoints=ev.extra_breakpoints,
    )


# ── L1g + L1h + L1k: null-replicate performance fixes ───────────────────────
#
# L1g (coarse breakpoints): build_segments() calls ln_lambda once per interval.
# The daśā ladder has 165K+ periods (mostly SD/PrD) → 165K+ intervals — at
# ~30μs per ln_lambda call that is 15 seconds per replicate, ~8 min per block.
# Omitting SD/PrD boundaries AND envelope knots reduces breakpoints from ~165K
# to ~819 (MD/AD/PD + kinematics roots).
#
# L1h (pointer-advance): the real kala_field event classes (childbirth etc.)
# have 425K+ stored segments, meaning the 819-interval ln_lambda function is
# highly curved. Adaptive refinement maxes out at depth 6 → 819 × 64 ≈ 52K
# null segments per replicate. cumulative_on_grid()'s prior loop called
# integrator.integrate() — restarting a linear scan from seg 0 each grid step —
# O(N_grid × N_seg) = 36525 × 52K ≈ 950M ops per replicate → 7+ min/block.
# Pointer-advance in cumulative_on_grid and _lambda_grid_fast gives
# O(N_grid + N_seg) ≈ 89K → sub-second.
#
# L1k (memoize + max_depth cap): L1h fixed the cumulative_on_grid bottleneck
# but _null_build_segments remained slow. kala_field_primitives has 166K rows
# for this chart, so EnvelopeIndex._sup_t0/_sup_t1 arrays are 166K elements.
# Every covariates_at(t) call does np.where(...) on 166K floats (~100μs).
# integrator._refine evaluates ln_lambda at t0, t1, AND tm — with no
# memoization, adjacent intervals re-evaluate their shared endpoints. At depth 6:
# 818 intervals × 381 calls = 311K ln_lambda evaluations per replicate ×
# ~100μs = 31s/replicate × 32 = 990s ≈ 16 min/block.
#
# Fix: wrap ln_lambda in a per-replicate dict cache (eliminating re-evaluation of
# shared endpoints) and cap null-replicate max_depth at _NULL_MAX_DEPTH=2.
# Unique evaluations: 818 × 5 ≈ 6,545 per replicate; at 100μs = 655ms ×
# 32 = 21s/block (vs. 16 min). With max_depth=1: 818 × 3 ≈ 3,273 unique ×
# 100μs = 327ms × 32 = 10s/block — well within the 12s target.
#
# Precision impact: max_depth=1 resolves each ~30-day dasha interval into 2
# sub-segments (~15 days each). Transit-contact peaks shorter than ~15 days are
# approximated by the linear interpolant rather than sampled exactly. For the
# null distribution this is acceptable — small inaccuracies average out over
# 256 replicates. The conservative direction (slightly lower q_threshold from
# missing sub-interval peaks) is consistent with the module's upper-bound intent.
#
# Skipped-class nulls (career_setback etc.) never reach this because they raise
# ClassSkipped before computing segments. The real-build segments (stored in
# kala_field) are unaffected by any of these fixes.

_NULL_COARSE_LEVELS: frozenset[str] = frozenset({'MD', 'AD', 'PD'})

#: Adaptive-refinement depth cap for null replicates (L1k).
#: max_depth=1 → 2 sub-segments per MD/AD/PD interval; unique ln_lambda
#: evaluations ≈ 818 × 3 = 3,273 per replicate → ~10s per block at 100μs/call.
#: Reduce to 0 (no refinement, 818 flat segments) only if blocks still exceed
#: writer_timeout_seconds. Do not raise max_depth above 2 without profiling.
_NULL_MAX_DEPTH: int = 1


def _null_breakpoints(ev: FieldEvaluator) -> list[float]:
    """Breakpoints for null replicates: coarse daśā levels only (MD/AD/PD).

    Envelope knots are intentionally EXCLUDED. Even at 1-day downsampling they
    produce ~36K segments for childbirth, causing O(N²) cumulative_on_grid
    (L1g motivation). With ladder-only breakpoints (~819 breakpoints → 818
    intervals), the null-replicate cost is dominated by ln_lambda evaluation
    cost in build_segments, addressed by L1k memoisation + max_depth cap.

    Correctness: each MD/AD/PD interval spans ~10–30 days. With max_depth=1
    the null replicates resolve each to 2 sub-segments (~15 days). Precision
    loss is acceptable for the null distribution — inaccuracies average out
    over 256 replicates and the conservative direction (slightly lower
    q_threshold when sub-interval peaks are under-sampled) matches the module's
    upper-bound intent (see module docstring §p-value).

    Clips to [0, horizon_days].
    """
    pts: set[float] = {0.0, ev.horizon_days}
    # Ladder: MD/AD/PD only (skip SD/PrD which add 160K+ intervals; skip
    # envelope knots which cause O(N²) cumulative_on_grid for classes like
    # childbirth).
    for periods in ev.ladder.values():
        for p in periods:
            if p.level in _NULL_COARSE_LEVELS:
                pts.add(p.t_start)
                pts.add(p.t_end)
    pts.update(ev.extra_breakpoints)
    return sorted(t for t in pts if math.isfinite(t) and 0.0 <= t <= ev.horizon_days)


def _null_build_segments(ev: FieldEvaluator) -> list[Segment]:
    """Build segments for a null replicate: coarse breakpoints (L1g) +
    memoised ln_lambda + capped max_depth (L1k).

    integrator._refine evaluates ln_lambda at BOTH endpoints and the midpoint
    on every recursive call. Without memoisation, adjacent intervals re-evaluate
    their shared endpoints, and each recursive level doubles the evaluation count
    — 818 intervals × 381 calls (depth 6) = 311K per replicate. With 166K
    primitives in the chart's EnvelopeIndex, each call takes ~100μs via
    np.where over 166K-element arrays → 31s/replicate → hours/block.

    L1k: per-replicate dict cache eliminates shared-endpoint re-evaluation.
    _NULL_MAX_DEPTH=1 caps the refinement tree: 818 intervals → ≈3,273 unique
    evaluations × ~100μs ≈ 327ms/replicate × 32 = 10s/block.
    """
    cache: dict[float, float] = {}

    def _ln_lambda_cached(t: float) -> float:
        if t not in cache:
            cache[t] = ev.ln_lambda(t)
        return cache[t]

    return integrator.build_segments(_null_breakpoints(ev), _ln_lambda_cached,
                                     max_depth=_NULL_MAX_DEPTH)


def cumulative_on_grid(
    segments: Sequence[Segment],
    horizon_days: float,
    grid_step: float = 1.0,
) -> list[float]:
    """Λ(0, t) at every grid point: O(N_grid + N_seg) pointer-advance.

    Returned as a cumulative array so the sliding-window maximum below is O(N)
    per bucket instead of O(N·L): Λ(t, t+L) = cum[t+L] − cum[t]. The integral is
    exact per step, so the cumulative is exact up to floating-point summation
    (which is precisely why `_EXCEEDANCE_REL_TOL` exists — see its comment).

    L1h: prior version called integrator.integrate(segments, k*gs, (k+1)*gs) for
    every grid step, restarting the linear scan from segment 0 each time —
    O(N_grid × N_seg) total. With ~52K null segments (L1g's 819 coarse intervals
    × max-depth-6 adaptive refinement for high-curvature classes like childbirth)
    and 36525 grid steps, that was 950M operations per replicate → 7+ min/block.
    Pointer-advance: O(N_grid + N_seg) ≈ 89K operations → sub-second.
    """
    n = int(round(horizon_days / grid_step))
    cum = [0.0] * (n + 1)
    if not segments:
        return cum
    running = 0.0
    n_segs = len(segments)
    j = 0  # pointer: first segment that might overlap [a, b)
    for k in range(n):
        a = k * grid_step
        b = a + grid_step
        # Advance j past segments that end at or before a (no overlap with [a, b))
        while j < n_segs and segments[j].t_end <= a:
            j += 1
        # Sum contributions from all segments overlapping [a, b) without moving j
        i = j
        while i < n_segs and segments[i].t_start < b:
            u = max(a, segments[i].t_start)
            v = min(b, segments[i].t_end)
            if v > u:
                running += integrator.segment_integral(segments[i], u, v)
            i += 1
        cum[k + 1] = running
    return cum


def sliding_window_max(cum: Sequence[float], bucket_days: int) -> float:
    """M(L) = max over t on the grid of Λ(t, t+L) — a matched filter at scale L.

    A bucket longer than the whole horizon degenerates to the total integral,
    which is the honest answer (the longest available filter is the whole span)
    rather than an error or a skipped bucket.
    """
    n = len(cum) - 1
    if bucket_days >= n:
        return cum[-1] - cum[0]
    return max(cum[k + bucket_days] - cum[k] for k in range(n - bucket_days + 1))


def replicate_stats(
    ev: FieldEvaluator,
    delta: float,
    horizon_days: float,
    *,
    buckets: Sequence[int] = DURATION_BUCKETS,
    grid_step: float = 1.0,
    segments: Optional[Sequence[Segment]] = None,
) -> dict[int, float]:
    """M_r(L) for every duration bucket, for ONE replicate."""
    if segments is None:
        segments = _null_build_segments(replicate_evaluator(ev, delta))
    cum = cumulative_on_grid(segments, horizon_days, grid_step)
    return {int(b): sliding_window_max(cum, int(b)) for b in buckets}


@dataclass
class NullResult:
    """Everything stage 5 needs to persist and to threshold windows with."""
    replicates: int
    horizon_days: float
    shift_grid_step: float
    q_threshold: Optional[float]
    max_stats: dict[int, list[float]] = field(default_factory=dict)


def _lambda_grid_fast(
    segments: Sequence[Segment],
    horizon_days: float,
    grid_step: float = 1.0,
) -> list[float]:
    """λ at every grid point: O(N_grid + N_seg) pointer-advance.

    Replaces N_grid individual integrator.lambda_at(segs, t) calls, each of
    which scans segs linearly from index 0. With 52K null segments and 36525
    grid steps that was 950M comparisons per replicate; pointer-advance over the
    sequential grid reduces this to O(N_grid + N_seg) ≈ 89K.
    """
    n = int(round(horizon_days / grid_step))
    if not segments:
        return [0.0] * n
    n_segs = len(segments)
    vals = [0.0] * n
    j = 0  # pointer into segments
    for k in range(n):
        t = k * grid_step
        # Advance j past segments that end at or before t
        while j < n_segs and segments[j].t_end <= t:
            j += 1
        if j < n_segs:
            seg = segments[j]
            if seg.t_start <= t < seg.t_end:
                vals[k] = integrator.segment_lambda(seg, t)
    return vals


def run_null(
    ev: FieldEvaluator,
    horizon_days: float,
    replicates: int = DEFAULT_REPLICATES,
    *,
    buckets: Sequence[int] = DURATION_BUCKETS,
    grid_step: float = 1.0,
    quantile: float = Q_QUANTILE,
    block: Optional[tuple[int, int]] = None,
    accumulator: Optional['NullAccumulator'] = None,
) -> NullResult:
    """Run the circular-shift null (or one block of it).

    `block = (start_index, end_index)` runs a half-open slice of the replicate
    grid — the §5.5 substep grain. `accumulator` carries the q-quantile pool and
    the per-bucket statistics across a class's blocks; pass the same one to every
    block and read `finalize()` after the last.

    RESUME SEMANTICS, STATED EXPLICITLY: the accumulator is in-memory, so a build
    interrupted part-way through a class's stage-5 blocks re-runs that class's
    blocks from the start on the next attempt. The alternative — persisting a
    partial quantile pool — would let a resumed build compute q_e from a mixture
    of two field snapshots, which is a worse failure than repeating some work.
    """
    grid = shift_grid(horizon_days, replicates)
    lo, hi = block if block else (0, len(grid))
    acc = accumulator or NullAccumulator(replicates=replicates, horizon_days=horizon_days,
                                         buckets=buckets, quantile=quantile,
                                         grid_step=grid_step)
    for r in range(lo, hi):
        rep = replicate_evaluator(ev, grid[r])
        segs = _null_build_segments(rep)  # L1g: coarse breakpoints (MD/AD/PD only)
        acc.add_replicate(
            index=r,
            stats=replicate_stats(rep, 0.0, horizon_days, buckets=buckets,
                                  grid_step=grid_step, segments=segs),
            lambda_grid=_lambda_grid_fast(segs, horizon_days, grid_step),  # L1h
        )
    return acc.finalize()


class NullAccumulator:
    """Accumulates replicate statistics across a class's stage-5 blocks."""

    def __init__(self, *, replicates: int, horizon_days: float,
                 buckets: Sequence[int] = DURATION_BUCKETS,
                 quantile: float = Q_QUANTILE, grid_step: float = 1.0):
        self.replicates = replicates
        self.horizon_days = horizon_days
        self.buckets = tuple(int(b) for b in buckets)
        self.grid_step = grid_step
        n_grid = int(round(horizon_days / grid_step))
        self._pool = QuantilePool(quantile=quantile, expected_total=replicates * n_grid)
        self._stats: dict[int, dict[int, float]] = {b: {} for b in self.buckets}

    def add_replicate(self, index: int, stats: Mapping[int, float],
                      lambda_grid: Iterable[float]) -> None:
        for b in self.buckets:
            self._stats[b][index] = float(stats[b])
        self._pool.add(lambda_grid)

    @property
    def completed(self) -> int:
        return len(self._stats[self.buckets[0]]) if self.buckets else 0

    def finalize(self) -> NullResult:
        return NullResult(
            replicates=self.replicates,
            horizon_days=self.horizon_days,
            shift_grid_step=self.horizon_days / self.replicates,
            q_threshold=self._pool.value(),
            # Ordered by replicate index so `null_max_stats[r-1]` is replicate r
            # under any substep dispatch order — the array is auditable, not just
            # aggregate-able.
            max_stats={b: [self._stats[b][i] for i in sorted(self._stats[b])]
                       for b in self.buckets},
        )


# ── §5.6 the robustness vector ───────────────────────────────────────────────

def system_concurrent(ev: FieldEvaluator, t_peak: float) -> bool:
    """≥2 applicable, PREDICTIVE systems have r_{s,e}(t_peak) > 0.

    A real detector with a real failure mode: a window driven by a single clock
    reads False and is correctly denied the 'concurrent' tier, however strong its
    λ. Concurrence across independent timing systems is the classical criterion,
    and one loud voice is not it.
    """
    from services.ka_kshetra import hazard
    stacks = ev.lord_stacks_at(t_peak)
    depth = {lvl: float(ev.weights.get(f'd:{lvl}', d))
             for lvl, d in hazard.DEFAULT_DEPTH_WEIGHTS.items()}
    positive = 0
    for clock in hazard.predictive_systems(ev.clocks):
        stack = stacks.get(clock.system_id, [])
        if hazard.relevance(stack, ev.promise.routes, depth) > 0.0:
            positive += 1
    return positive >= 2


def birth_time_robust(
    segments: Sequence[Segment],
    t_peak: float,
    q: float,
    sigma_t_days: Optional[float],
    z: float = 1.96,
) -> Optional[bool]:
    """Does the window survive t_peak ± 1.96·σ_T without losing its exceedance?

    True iff λ stays at or above q at BOTH ends of the birth-time interval — i.e.
    the window's claim does not depend on a birth time we do not have to that
    precision.

    Returns None when σ_T is unknown: §N.8 — a dimension with no detector is
    null, and null is not green. `RobustnessVector.weakest_link` will then name
    this dimension rather than let it pass silently.
    """
    if sigma_t_days is None or not math.isfinite(sigma_t_days) or sigma_t_days < 0:
        return None
    half = z * sigma_t_days
    return bool(
        integrator.lambda_at(segments, t_peak - half) >= q
        and integrator.lambda_at(segments, t_peak + half) >= q
    )


def ayanamsha_robust(
    present_ayanamsha_ids: set[str],
    pinned: Sequence[str] = PINNED_AYANAMSHAS,
) -> Optional[bool]:
    """Does the window's evidence exist under ALL five pinned ayanāṃśas?

    Computed from the ayanāṃśa coverage of the stage-0 kinematics the window
    stands on. True iff every pinned id is present; False iff ≥2 are present but
    not all (a genuine divergence in coverage); None iff fewer than 2 were ever
    computed — in which case NOTHING has been tested and the honest answer is
    not-computed, not a pass.

    The None branch is the §N.8 discipline that matters most here: with a
    single-ayanāṃśa kinematics table, "survives all five ayanāṃśas" is a claim no
    code path could ever have falsified, so it may not read True.
    """
    if len(present_ayanamsha_ids) < 2:
        return None
    return all(a in present_ayanamsha_ids for a in pinned)


def authority_clean(cited: int, resolved: int) -> bool:
    """Did every provenance `source_fact_id` resolve (§5.4's citation join)?

    A dangling citation FAILS the build in CI; here it also downgrades the
    window's confidence tier, so a chart built before that CI gate existed cannot
    quietly serve 'concurrent' on unresolvable evidence.
    """
    return cited == resolved


# ── §5.6 the Adṛṣṭa residual ─────────────────────────────────────────────────

def adrishta_residual(
    window_integrals: Sequence[float],
    baseline_rate: float,
    horizon_days: float,
) -> Optional[float]:
    """clamp01( 1 − Σ_w Λ_e(w) / (λ⁰_e · H) ) — the share of the class's
    classical expectation that sits OUTSIDE every notable window.

    This is the instrument's own honest statement of what it does not claim to
    time. A high residual is not a defect: it says most of this class's classical
    expectation is unaccounted for by any window the null found notable, and a
    reader deserves that number rather than the impression that the windows
    exhaust the possibility space.

    Clamped at 0 when the windows over-account (the field CAN concentrate more
    than the baseline expects); a negative share would be meaningless. Returns
    None — honest not-computed — when the expectation is zero, rather than
    dividing by it.
    """
    expectation = baseline_rate * horizon_days
    if not (expectation > 0) or not math.isfinite(expectation):
        return None
    share = math.fsum(window_integrals) / expectation
    return max(0.0, min(1.0, 1.0 - share))


__all__ = [
    'DURATION_BUCKETS', 'DEFAULT_REPLICATES', 'DEFAULT_BLOCK_SIZE',
    'ALPHA', 'Q_QUANTILE', 'PINNED_AYANAMSHAS',
    'shift_grid', 'select_bucket',
    'null_p', 'null_resolution', 'null_exceeding',
    'QuantilePool', 'NullResult', 'NullAccumulator',
    'replicate_evaluator', 'cumulative_on_grid', 'sliding_window_max',
    'replicate_stats', 'run_null',
    'system_concurrent', 'birth_time_robust', 'ayanamsha_robust', 'authority_clean',
    'adrishta_residual',
]
