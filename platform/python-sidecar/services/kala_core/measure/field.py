"""Class-specific field maxima, distinct from jury incremental agreement.

ALGO 3.20; PLAN 6.2(5,8). Shared schedule, separately conditioned field
geometry. Callers supply the FULL reference evaluator; this core never imports
a stage or an outcome scorer. Numeric reductions below moved verbatim from
stage5_null (bitwise contract); no compact evaluator is introduced.
"""
from dataclasses import dataclass
import hashlib
import heapq
import json
import math
from typing import Iterable, Optional, Sequence
from . import DEFAULT_NON_IDENTITY_SHIFTS, Experiment, Interval, bind_schedule, prepare_schedule

DURATION_BUCKETS = (1, 3, 7, 15, 30, 60, 90, 180, 365, 730)
ALPHA = 0.05
Q_QUANTILE = 0.95
_EXCEEDANCE_REL_TOL = 1e-12

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



@dataclass(frozen=True)
class FieldPreparation:
    event_class: str
    horizon_days: float
    offsets: tuple[float, ...]
    experiment: Experiment
    digest: str
    schedule_digest: str = ''


def prepare_field(event_class, horizon_days, *, non_identity_shifts=None, schedule=None):
    if not event_class:
        raise ValueError('event class is required')
    horizon = Interval(0, horizon_days)
    # One candidate-level schedule is consumed by every experiment; a caller
    # without one gets an equivalent private schedule (same offsets and digest).
    schedule = (prepare_schedule(horizon, DEFAULT_NON_IDENTITY_SHIFTS if non_identity_shifts is None else non_identity_shifts)
                if schedule is None else bind_schedule(schedule, horizon_days, non_identity_shifts))
    offsets = schedule.offsets
    experiment = Experiment('class_specific_field_maximum:' + event_class,
        'natal promise, baseline and clocks fixed; all stage-1 transit and obstruction envelopes circularly shifted; full reference rebuilt per draw')
    material = [experiment.estimand, experiment.conditioning, horizon_days, offsets]
    digest = hashlib.sha256(json.dumps(material, separators=(',', ':')).encode()).hexdigest()
    return FieldPreparation(event_class, horizon_days, offsets, experiment, digest, schedule.digest)


@dataclass(frozen=True)
class FieldNullResult:
    replicates: int
    horizon_days: float
    shift_grid_step: float
    q_threshold: float
    max_stats: dict[int, list[float]]
    experiment: Experiment
    preparation_digest: str
    denominator: int
    exchangeable: bool = False
    surrogate_diagnostic: bool = True

    @property
    def resolution(self):
        return 1.0 / self.denominator


class FieldAccumulator:
    """Exact maxima and pooled quantile; block retries never double count.

    Identical repeated draws are accepted by content digest. Changed repeats,
    missing draws, non-finite values and empty grids refuse a result.
    """
    def __init__(self, preparation, *, buckets=DURATION_BUCKETS, quantile=Q_QUANTILE):
        self.preparation = preparation
        self.buckets = tuple(buckets)
        if not self.buckets or any(type(b) is not int or b < 1 for b in self.buckets):
            raise ValueError('positive integral duration buckets required')
        self._pool = QuantilePool(quantile, expected_total=len(preparation.offsets) * int(round(preparation.horizon_days)))
        self._stats = {b: {} for b in self.buckets}
        self._digests = {}

    def add_replicate(self, index, stats, lambda_grid):
        values = list(lambda_grid)
        if type(index) is not int or not 0 <= index < len(self.preparation.offsets):
            raise ValueError('draw index outside preparation')
        if (set(stats) != set(self.buckets) or len(values) != int(round(self.preparation.horizon_days))
                or not values or not all(math.isfinite(v) and v >= 0 for v in [*stats.values(), *values])):
            raise ValueError('complete finite non-negative draw required')
        digest = hashlib.sha256(json.dumps([stats, values], sort_keys=True).encode()).hexdigest()
        if index in self._digests:
            if self._digests[index] != digest:
                raise ValueError('draw changed on retry')
            return
        self._digests[index] = digest
        for b in self.buckets:
            self._stats[b][index] = float(stats[b])
        self._pool.add(values)

    @property
    def completed(self):
        return len(self._digests)

    def finalize(self):
        p = self.preparation
        if self.completed != len(p.offsets):
            raise ValueError('incomplete field null')
        return FieldNullResult(self.completed, p.horizon_days,
            p.horizon_days / (self.completed + 1), self._pool.value(),
            {b: [s[i] for i in range(self.completed)] for b, s in self._stats.items()},
            p.experiment, p.digest, self.completed + 1)


def collect_field_block(accumulator, draw_statistics, *, start, end):
    """Same shared schedule as jury; statistic callbacks remain consumer-owned."""
    p = accumulator.preparation
    if not 0 <= start <= end <= len(p.offsets):
        raise ValueError('invalid draw block')
    for i in range(start, end):
        stats, values = draw_statistics(p.offsets[i])
        accumulator.add_replicate(i, stats, values)
