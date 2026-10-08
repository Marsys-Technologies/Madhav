"""Coverage records for chart-free sky answers.

Every sky result names the interval its source can answer, the backend and
whether the request was answered completely. A request the source does not
cover is `information_unavailable`; a partial answer is never labelled
complete. The record is derived, so it cannot be hand-promoted.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Generic, TypeVar

from services.kala_core.vocab import NullReason

T = TypeVar("T")

# The two reasons a sky result may carry no values.
EMPTY_RESULT_REASONS = frozenset({
    NullReason.INFORMATION_UNAVAILABLE, NullReason.METHOD_INAPPLICABLE,
})


def _interval(value: tuple[float, float], name: str) -> tuple[float, float]:
    start, end = (float(v) for v in value)
    if not (isfinite(start) and isfinite(end)) or end < start:
        raise ValueError(f"{name} must be a finite [start, end) JD interval")
    return start, end


def _intersect(source: tuple[float, float] | None,
               requested: tuple[float, float]) -> tuple[float, float] | None:
    """Half-open intersection; an instant request (start == end) is a point."""
    if source is None:
        return None
    if requested[0] == requested[1]:
        return requested if source[0] <= requested[0] < source[1] else None
    start, end = max(source[0], requested[0]), min(source[1], requested[1])
    return (start, end) if start < end else None


@dataclass(frozen=True)
class SkyCoverage:
    requested: tuple[float, float]
    source_interval: tuple[float, float] | None   # None: the source has no data
    covered: tuple[float, float] | None
    complete: bool
    backend: str
    convention_id: str

    def __post_init__(self) -> None:
        if not self.backend or not self.convention_id:
            raise ValueError("coverage must name its backend and convention")
        requested = _interval(self.requested, "requested")
        source = (None if self.source_interval is None
                  else _interval(self.source_interval, "source_interval"))
        expected = _intersect(source, requested)
        if self.covered != expected:
            raise ValueError(f"covered {self.covered!r} is not source ∩ request {expected!r}")
        if self.complete != (expected == requested):
            raise ValueError("complete must be true exactly when the whole request is covered")

    @property
    def gaps(self) -> tuple[tuple[float, float], ...]:
        if self.covered is None:
            return (self.requested,)
        lo, hi = self.requested
        return tuple(g for g in ((lo, self.covered[0]), (self.covered[1], hi)) if g[0] < g[1])


def coverage_of(requested: tuple[float, float], source_interval: tuple[float, float] | None,
                *, backend: str, convention_id: str) -> SkyCoverage:
    requested = _interval(requested, "requested")
    source = None if source_interval is None else _interval(source_interval, "source_interval")
    covered = _intersect(source, requested)
    return SkyCoverage(requested, source, covered, covered == requested, backend, convention_id)


@dataclass(frozen=True)
class SkyResult(Generic[T]):
    """Values with their coverage; an empty answer carries its typed null."""

    values: tuple[T, ...]
    coverage: SkyCoverage
    null_reason: NullReason | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.coverage, SkyCoverage):
            raise TypeError("every sky result names its coverage")
        object.__setattr__(self, "values", tuple(self.values))
        if self.null_reason is not None and self.null_reason not in EMPTY_RESULT_REASONS:
            raise ValueError(f"not a sky null reason: {self.null_reason!r}")
        if self.coverage.covered is None and self.null_reason is None:
            raise ValueError("an uncovered request is information_unavailable")
        if self.null_reason is not None and self.values:
            raise ValueError("a null result carries no values")

    @property
    def available(self) -> bool:
        return self.null_reason is None


def unavailable(coverage: SkyCoverage,
                reason: NullReason = NullReason.INFORMATION_UNAVAILABLE) -> SkyResult:
    return SkyResult((), coverage, reason)


__all__ = ["SkyCoverage", "SkyResult", "coverage_of", "unavailable"]
