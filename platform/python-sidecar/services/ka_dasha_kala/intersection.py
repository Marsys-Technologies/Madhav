"""
intersection.py — R-2 clock-intersection oracle (plan §3 R-2 / §3b SPEC R-2; F-13 repair).

Replaces the exact-(start, end)-pair agreement key (`_build_overlap_key`, F-13) with
atomic simultaneous intersection: every maximal sub-interval on which the set of
supporting clocks is constant becomes one segment carrying its supporter set.
Agreement between clocks = direct co-support on at least one atomic segment —
NEVER transitive merging of any overlappers (A overlapping B and B overlapping C
does not make A and C agree unless they directly share a segment).

BOUNDARY CONVENTION (declared, S-H): every interval is half-open [start, end) —
start-inclusive, end-exclusive. A point exactly equal to `end` is NOT covered.
Contiguous daśā chains (one interval's end == next interval's start) therefore
partition time instead of double-covering boundary instants.

GRAIN: start/end may be `date` or `datetime` (any totally ordered homogeneous
type), so sub-day boundaries flow through the same code path.

PARENT HIERARCHY: every supporter carries its level_n and parent_row_id (the
containing interval of the same system at level_n-1). Nested levels of the SAME
system never inflate agreement: the count is the number of DISTINCT systems
co-supporting a segment, not the number of intervals.

Pure functions only — no DB, no I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional, Tuple

# Boundary convention token, declared per plan §3 R-2 ("boundary convention
# declared (S-H)"). Consumed by evidence detectors and by callers that must
# state the convention on their outputs.
BOUNDARY_CONVENTION = '[start, end)'   # S-H: start-inclusive, end-exclusive


@dataclass(frozen=True)
class SupporterRef:
    """One supporting interval's identity on an atomic segment."""
    system_id: str
    level_n: int
    lord_graha: str
    dasha_row_id: str
    parent_row_id: Optional[str] = None


@dataclass(frozen=True)
class IntersectionSegment:
    """A maximal sub-interval with a constant supporter set."""
    start: Any
    end: Any
    supporters: Tuple[SupporterRef, ...]


@dataclass(frozen=True)
class AgreementSummary:
    """Distinct systems directly co-supporting an interval."""
    count: int
    systems_agreeing: Tuple[str, ...]


def _ref(iv: Any) -> SupporterRef:
    return SupporterRef(
        system_id=iv.system_id,
        level_n=iv.level_n,
        lord_graha=iv.lord_graha,
        dasha_row_id=iv.dasha_row_id,
        parent_row_id=getattr(iv, 'parent_row_id', None),
    )


def intersect_segments(intervals: Iterable[Any]) -> list[IntersectionSegment]:
    """
    Atomic simultaneous intersection of all intervals.

    intervals: objects with start_date / end_date (date or datetime, homogeneous)
    plus the identity fields read by _ref(). Degenerate [d, d) intervals support
    nothing and produce no segment (their agreement is a real, evaluated 0 —
    see agreement_for).

    Returns maximal segments sorted by start, each carrying the sorted tuple of
    supporters. Two intervals agree only where they DIRECTLY co-support a
    segment; chained overlap never propagates.
    """
    ivs = [(iv.start_date, iv.end_date, _ref(iv))
           for iv in intervals
           if iv.end_date > iv.start_date]          # S-H: empty intervals are inert
    if not ivs:
        return []
    bounds = sorted({b for s, e, _ in ivs for b in (s, e)})
    segments: list[IntersectionSegment] = []
    for a, b in zip(bounds, bounds[1:]):
        if a >= b:
            continue
        # `a` is a boundary point, so s <= a < e is exactly the S-H support
        # test for the whole open slab (a, b).
        sup = tuple(sorted((r for s, e, r in ivs if s <= a < e),
                           key=lambda r: (r.system_id, r.level_n, r.dasha_row_id)))
        if not sup:
            continue
        if segments and segments[-1].supporters == sup:
            segments[-1] = IntersectionSegment(segments[-1].start, b, sup)
        else:
            segments.append(IntersectionSegment(a, b, sup))
    return segments


def agreement_for(start: Any, end: Any, segments: list[IntersectionSegment]) -> AgreementSummary:
    """
    Distinct systems directly co-supporting at least one atomic segment of
    [start, end). A degenerate [d, d) interval — or one overlapping no segment —
    returns count 0: a real, EVALUATED zero, never to be confused with a
    service failure (R-2: evaluated-empty and unavailable are distinct states).
    """
    if end <= start:
        return AgreementSummary(count=0, systems_agreeing=())
    systems = {ref.system_id
               for seg in segments
               if seg.start < end and seg.end > start     # S-H segment∩interval
               for ref in seg.supporters}
    return AgreementSummary(count=len(systems), systems_agreeing=tuple(sorted(systems)))
