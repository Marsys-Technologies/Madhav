"""Shared segment/draw preparation, with a separate conditional jury experiment.

Authority: KALA_LAYER_CODE_ARCHITECTURE_PLAN v1.1 §3.2, §6.2(5),
NR-KALA-R13(d). R counts non-identity shifts: the pinned 1,023 shifts plus
one observation give denominator 1,024. No outcome scorer is imported.

Jury statistic: mean number of additional active witness groups during
anchor exposure. D(W) is its observed value minus its shift-null mean.
All non-anchor witnesses receive one common offset, preserving their shared
dependencies; this is never a claim of independence or exchangeability.
Whole-pipeline selection and field-maximum consumers must supply their own
statistic and conditioning, rather than treating the jury result as theirs.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import math
from statistics import fmean, pvariance
from typing import Callable, Iterable


DEFAULT_NON_IDENTITY_SHIFTS = 1023  # DHARA F-01 / PLAN §6.2(5): excludes identity.


class Verdict(StrEnum):
    PASS = 'pass'
    FAIL = 'fail'
    INSUFFICIENT_EVIDENCE = 'insufficient_evidence'
    NOT_EVALUABLE = 'not_evaluable'


@dataclass(frozen=True, order=True)
class Interval:
    start: float
    end: float

    def __post_init__(self):
        object.__setattr__(self, 'start', float(self.start))
        object.__setattr__(self, 'end', float(self.end))
        if not (math.isfinite(self.start) and math.isfinite(self.end) and self.start < self.end and math.isfinite(self.end - self.start)):
            raise ValueError('interval must have finite endpoints and positive duration')

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass(frozen=True)
class Witness:
    """One declared group, not an assertion of statistical independence."""
    witness_id: str
    intervals: tuple[Interval, ...]

    def __post_init__(self):
        if not self.witness_id:
            raise ValueError('witness identity is required')
        object.__setattr__(self, 'intervals', tuple(self.intervals))


@dataclass(frozen=True)
class Segment:
    interval: Interval
    support: frozenset[str]


@dataclass(frozen=True)
class Draw:
    offset: float
    segments: tuple[Segment, ...]


@dataclass(frozen=True)
class ExposureManifest:
    horizon: Interval
    exposure_by_witness: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class Preparation:
    observation: Draw
    null_draws: tuple[Draw, ...]
    anchor_id: str
    exposure: ExposureManifest
    exchangeable: bool
    digest: str


@dataclass(frozen=True)
class Experiment:
    estimand: str
    conditioning: str

    def __post_init__(self):
        if not self.estimand or not self.conditioning:
            raise ValueError('experiment requires distinct estimand and explicit conditioning')


@dataclass(frozen=True)
class NullResult:
    experiment: Experiment
    preparation_digest: str
    observed: float | None
    null_statistics: tuple[float, ...]
    effect: float | None
    standardized_effect: float | None
    p_value: float | None
    denominator: int
    verdict: Verdict
    reason: str | None
    surrogate_diagnostic: bool


def union_intervals(intervals: Iterable[Interval], horizon: Interval) -> tuple[Interval, ...]:
    """Clip, sort and union support; duplicates cannot inflate exposure."""
    clipped = sorted((max(i.start, horizon.start), min(i.end, horizon.end)) for i in intervals if i.start < horizon.end and i.end > horizon.start)
    merged: list[Interval] = []
    for start, end in clipped:
        if merged and start <= merged[-1].end:
            merged[-1] = Interval(merged[-1].start, max(end, merged[-1].end))
        else:
            merged.append(Interval(start, end))
    return tuple(merged)


def intersect_intervals(left: Iterable[Interval], right: Iterable[Interval], horizon: Interval) -> tuple[Interval, ...]:
    a, b = union_intervals(left, horizon), union_intervals(right, horizon)
    answer: list[Interval] = []
    i = j = 0
    while i < len(a) and j < len(b):
        start, end = max(a[i].start, b[j].start), min(a[i].end, b[j].end)
        if start < end:
            answer.append(Interval(start, end))
        if a[i].end < b[j].end:
            i += 1
        else:
            j += 1
    return tuple(answer)


def elementary_segments(horizon: Interval, witnesses: Iterable[Witness]) -> tuple[Segment, ...]:
    """Sweep exact boundaries. End events precede the next half-open segment."""
    witnesses = tuple(witnesses)
    names = [w.witness_id for w in witnesses]
    if len(set(names)) != len(names):
        raise ValueError('witness identities must be unique; combine a group before preparation')
    events: dict[float, list[tuple[str, bool]]] = defaultdict(list)
    events[horizon.start], events[horizon.end] = [], []
    for w in witnesses:
        for interval in union_intervals(w.intervals, horizon):
            events[interval.start].append((w.witness_id, True))
            events[interval.end].append((w.witness_id, False))
    active: set[str] = set()
    segments: list[Segment] = []
    boundaries = sorted(events)
    for start, end in zip(boundaries, boundaries[1:]):
        for name, begins in events[start]:
            if begins:
                active.add(name)
            else:
                active.discard(name)
        support = frozenset(active)
        if segments and segments[-1].support == support:
            segments[-1] = Segment(Interval(segments[-1].interval.start, end), support)
        else:
            segments.append(Segment(Interval(start, end), support))
    return tuple(segments)


def circular_shift(intervals: Iterable[Interval], horizon: Interval, offset: float) -> tuple[Interval, ...]:
    if not math.isfinite(offset):
        raise ValueError('shift offset must be finite')
    delta, length = offset % horizon.duration, horizon.duration
    pieces: list[Interval] = []
    for i in union_intervals(intervals, horizon):
        # Full-horizon support is invariant; splitting it at a floating-point
        # seam can manufacture a tiny gap and spurious null variance.
        if i == horizon:
            pieces.append(horizon)
            continue
        start = horizon.start + ((i.start - horizon.start + delta) % length)
        end = start + i.duration
        if end <= horizon.end:
            pieces.append(Interval(start, end))
        else:
            pieces.append(Interval(start, horizon.end))
            wrapped_end = horizon.start + (end - horizon.end)
            if wrapped_end > horizon.start:
                pieces.append(Interval(horizon.start, wrapped_end))
    return union_intervals(pieces, horizon)


def shift_schedule(horizon: Interval, non_identity_shifts: int = DEFAULT_NON_IDENTITY_SHIFTS) -> tuple[float, ...]:
    if isinstance(non_identity_shifts, bool) or not isinstance(non_identity_shifts, int) or non_identity_shifts < 1:
        raise ValueError('at least one non-identity shift is required')
    offsets = tuple(horizon.duration * (i / (non_identity_shifts + 1)) for i in range(1, non_identity_shifts + 1))
    if len(set(offsets)) != non_identity_shifts or not all(0 < d < horizon.duration for d in offsets):
        raise ValueError('horizon resolution cannot represent distinct non-identity shifts')
    return offsets


def prepare_draws(horizon: Interval, witnesses: Iterable[Witness], *, anchor_id: str,
                  non_identity_shifts: int = DEFAULT_NON_IDENTITY_SHIFTS,
                  exchangeable: bool) -> Preparation:
    witnesses = tuple(sorted((Witness(w.witness_id, union_intervals(w.intervals, horizon)) for w in witnesses), key=lambda w: w.witness_id))
    if anchor_id not in {w.witness_id for w in witnesses}:
        raise ValueError('conditioning anchor must be a declared witness')
    if not isinstance(exchangeable, bool):
        raise ValueError('exchangeability must be explicitly assessed')
    observation = Draw(0, elementary_segments(horizon, witnesses))
    offsets = shift_schedule(horizon, non_identity_shifts)
    draws = tuple(Draw(offset, elementary_segments(horizon, tuple(Witness(w.witness_id, w.intervals if w.witness_id == anchor_id else circular_shift(w.intervals, horizon, offset)) for w in witnesses))) for offset in offsets)
    exposure = ExposureManifest(horizon, tuple((w.witness_id, math.fsum(i.duration for i in w.intervals)) for w in witnesses))
    material = {'version': 'k4-1:conditional_common_shift:v1', 'horizon': [horizon.start, horizon.end], 'anchor': anchor_id, 'exchangeable': exchangeable, 'offsets': offsets, 'witnesses': [(w.witness_id, [(i.start, i.end) for i in w.intervals]) for w in witnesses]}
    digest = hashlib.sha256(json.dumps(material, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return Preparation(observation, draws, anchor_id, exposure, exchangeable, digest)


def evaluate_experiment(preparation: Preparation, experiment: Experiment,
                        statistic: Callable[[Draw], float], *, alpha: float) -> NullResult:
    """Upper-tail test with ties; draw failures propagate, never become zeros."""
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError('alpha must be explicitly supplied in (0,1)')
    observed = float(statistic(preparation.observation))
    nulls = tuple(float(statistic(draw)) for draw in preparation.null_draws)
    denominator = len(nulls) + 1
    surrogate = not preparation.exchangeable
    if not nulls or not all(math.isfinite(n) for n in (observed, *nulls)):
        return NullResult(experiment, preparation.digest, observed if math.isfinite(observed) else None, nulls, None, None, None, denominator, Verdict.NOT_EVALUABLE, 'non_finite_statistic', surrogate)
    effect = observed - fmean(nulls)
    variance = pvariance(nulls)
    if variance == 0:
        return NullResult(experiment, preparation.digest, observed, nulls, effect, None, None, denominator, Verdict.INSUFFICIENT_EVIDENCE, 'zero_null_variance', surrogate)
    p = (1 + sum(n >= observed for n in nulls)) / denominator
    verdict = Verdict.INSUFFICIENT_EVIDENCE if surrogate else Verdict.PASS if p <= alpha else Verdict.FAIL
    return NullResult(experiment, preparation.digest, observed, nulls, effect, effect / math.sqrt(variance), p, denominator, verdict, 'exchangeability_not_established' if surrogate else None, surrogate)


def jury_agreement(preparation: Preparation, *, alpha: float) -> NullResult:
    """Conditional incremental agreement, not odds or a confidence label."""
    experiment = Experiment('jury_incremental_agreement', 'anchor fixed; all additional witness groups jointly circular-shifted')
    exposure = dict(preparation.exposure.exposure_by_witness)[preparation.anchor_id]
    if exposure == 0:
        return NullResult(experiment, preparation.digest, None, (), None, None, None, len(preparation.null_draws) + 1, Verdict.NOT_EVALUABLE, 'no_anchor_exposure', not preparation.exchangeable)
    def joint_support(draw: Draw) -> float:
        return math.fsum(s.interval.duration * (len(s.support) - 1) for s in draw.segments if preparation.anchor_id in s.support) / exposure
    return evaluate_experiment(preparation, experiment, joint_support, alpha=alpha)


__all__ = ['DEFAULT_NON_IDENTITY_SHIFTS', 'Verdict', 'Interval', 'Witness', 'Segment', 'Draw', 'ExposureManifest', 'Preparation', 'Experiment', 'NullResult', 'union_intervals', 'intersect_intervals', 'elementary_segments', 'circular_shift', 'shift_schedule', 'prepare_draws', 'evaluate_experiment', 'jury_agreement']
