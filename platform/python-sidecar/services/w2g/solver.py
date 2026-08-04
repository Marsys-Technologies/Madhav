"""W2G — the contact solver, and the one architectural claim it has to keep.

THE CLAIM: **a chart's contact computation reads the arc substrate a constant
number of times, no matter how many targets, bodies or primitives it involves.**

That claim is the whole reason W2G exists in its present shape. The v1 sweep's
dominant cost is not ephemeris computation — that premise was FALSIFIED by
clean A/B measurement on 2026-08-04 (SHAD_DARSHANA_STATE.md lane (a):
cross-class ephemeris cache reuse is minimal; the "warm" run was not faster
than the cold control and had MORE misses). The dominant cost is
~110-120ms per contact-primitive call, "regardless of whether it touches the
DB at all" — a per-call floor that multiplies by
(targets x primitives x windows) and reproduces the measured 550-650s for a
THIRTY-DAY window almost exactly.

You do not fix that by making each call faster. You fix it by not making
(targets x primitives x windows) calls. So:

    load the arcs ONCE  ->  every crossing thereafter is pure CPU bisection

`ArcSource` is the seam. `DbArcSource` is the one-query implementation; the
test suite substitutes a counting source and asserts the read count does not
move when the target count grows 40x. That test is the detector; this
docstring is not evidence (§N.8).

TIER ENFORCEMENT. `solve()` refuses Tier C (Moon) by default —
ADJUDICATION-14's "never materialized full-span" — and takes
`include_lazy=True` for the explicit drill-down case (an election query, or a
window the slow layers already elevated). Refusing by default is what keeps
the ≤15-minute onboarding SLO from being quietly spent on the body that is
76.1% of all contact events.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol, Sequence

from .arcs import DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC, MonotoneArc
from .crossings import ContactEvent, find_contacts
from .tiers import TIER_LAZY, body_tier


class ArcSource(Protocol):
    """Anything that can hand over a body's arcs. One call, many bodies."""

    def load(self, bodies: Sequence[str]) -> dict[str, list[MonotoneArc]]:
        ...


@dataclass
class SolveStats:
    """What the solve actually did — earned counters, not estimates."""

    arc_reads: int = 0
    arcs_scanned: int = 0
    crossings_found: int = 0
    bodies_skipped_lazy: tuple[str, ...] = ()


class ContactSolver:
    """Solve every (body x target) crossing from ONE arc read."""

    def __init__(self, source: ArcSource):
        self._source = source
        self.stats = SolveStats()

    def solve(
        self,
        bodies: Sequence[str],
        target_degs: Iterable[float],
        orb_deg: float,
        include_lazy: bool = False,
        tolerance_arcsec: float = DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC,
    ) -> list[ContactEvent]:
        bodies = tuple(bodies)
        targets = [float(t) % 360.0 for t in target_degs]

        # THE one read. Every body is fetched in the same call, including the
        # lazy ones — filtering after the read keeps the read count at exactly
        # one regardless of tier composition, which is the property under test.
        arcs_by_body = self._source.load(bodies)
        self.stats = SolveStats(arc_reads=1)

        skipped: list[str] = []
        events: list[ContactEvent] = []
        for body in bodies:
            if not include_lazy and body_tier(body) == TIER_LAZY:
                skipped.append(body)
                continue
            arcs = arcs_by_body.get(body) or []
            self.stats.arcs_scanned += len(arcs)
            for target in targets:
                events.extend(find_contacts(arcs, target, orb_deg, tolerance_arcsec))

        events.sort(key=lambda e: (e.exact_jd, e.body, e.target_deg))
        self.stats.crossings_found = len(events)
        self.stats.bodies_skipped_lazy = tuple(skipped)
        return events


class InMemoryArcSource:
    """An `ArcSource` over already-materialized arcs (tests, drill-downs)."""

    def __init__(self, arcs_by_body: dict[str, list[MonotoneArc]]):
        self._arcs = arcs_by_body

    def load(self, bodies: Sequence[str]) -> dict[str, list[MonotoneArc]]:
        return {b: self._arcs.get(b, []) for b in bodies}


__all__ = ["ArcSource", "ContactSolver", "InMemoryArcSource", "SolveStats"]
