"""W2G — contact solving on monotone arcs.

A "contact" is the classical object v1's `find_aspect_events` produces: a
transiting body reaching a natal degree, with an orb-entry / exact / orb-exit
triple. v1 finds it by day-stepping the window with live ephemeris calls and
bisecting wherever the arc-difference changes sign. 2.0 finds it by asking the
arc index which arcs contain the degree at all and bisecting INSIDE the
bracket that answer already hands over.

The difference is not a constant factor. v1's cost scales with the LENGTH of
the window scanned (plus a per-call floor of ~110-120ms that dominates in
practice); 2.0's cost scales with the NUMBER OF ACTUAL CROSSINGS, which is the
quantity the answer is made of. A century-wide question costs the same per
crossing as a 30-day one.

WHAT IS DELIBERATELY NOT HERE: no astrology. Aspect angles, orb policy per
primitive, target selection, weighting, valence — all of that is v1's grammar,
frozen per design §5 ("2.0 changes HOW, never WHAT"). This module answers one
geometric question and nothing else.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .arcs import (
    ARCSEC_PER_DEG,
    DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC,
    MAX_BISECTION_ITERATIONS,
    MonotoneArc,
    arcs_covering_degree,
)


# How far the interpolant may disagree with an arc's stored endpoint before
# that disagreement is treated as a real out-of-range condition rather than
# endpoint-snapping noise. 0.01° = 36″ — two orders of magnitude above V3's
# measured worst-case spline error (0.314″) and far below any orb that carries
# astrological meaning.
ENDPOINT_SNAP_TOLERANCE_DEG = 0.01


@dataclass(frozen=True)
class ContactWindow:
    """Orb entry / exact / exit for one crossing, on one arc.

    `entry_truncated` / `exit_truncated` are earned flags, not decoration: an
    orb edge that would fall outside the arc's own validity is CLIPPED to the
    arc and the flag says so, rather than extrapolating the interpolant past
    the span it was fitted for (§N.7 item 6 — an honest bound beats a
    plausible-looking invented one). A truncated edge is normally continued by
    the adjacent arc, which the caller can stitch; nothing is lost, but nothing
    is fabricated either.
    """

    arc: MonotoneArc
    target_deg: float
    orb_deg: float
    entry_jd: float
    exact_jd: float
    exit_jd: float
    entry_truncated: bool
    exit_truncated: bool

    @property
    def duration_days(self) -> float:
        return self.exit_jd - self.entry_jd


@dataclass(frozen=True)
class ContactEvent:
    """One crossing, flattened for persistence/serving."""

    body: str
    target_deg: float
    exact_jd: float
    entry_jd: float
    exit_jd: float
    direction: int
    arc_index: int
    entry_truncated: bool = False
    exit_truncated: bool = False

    @property
    def duration_days(self) -> float:
        return self.exit_jd - self.entry_jd


def _bisect_for_level(arc: MonotoneArc, level_unwrapped: float, tol_deg: float) -> float:
    lo, hi = arc.start_jd, arc.end_jd
    f_lo = arc.unwrapped_longitude_at(lo) - level_unwrapped
    f_hi = arc.unwrapped_longitude_at(hi) - level_unwrapped
    if f_lo == 0.0:
        return lo
    if f_hi == 0.0:
        return hi
    if f_lo * f_hi > 0.0:
        # An arc's STORED endpoints are authoritative; the interpolant is not.
        # A wrap-boundary endpoint is recorded as exactly 360k (see
        # `arcs.build_arcs`), while the spline evaluated at that same instant
        # returns 360k ± a fraction of an arcsecond. So a level that IS the
        # endpoint can come back unbracketed by a hair. Accept the endpoint in
        # that case; raise only when the level is genuinely outside the arc.
        nearest = lo if abs(f_lo) <= abs(f_hi) else hi
        if min(abs(f_lo), abs(f_hi)) <= max(tol_deg, ENDPOINT_SNAP_TOLERANCE_DEG):
            return nearest
        raise ValueError(
            f"level {level_unwrapped}° is not bracketed by arc "
            f"{arc.body}#{arc.arc_index}"
        )
    for _ in range(MAX_BISECTION_ITERATIONS):
        mid = 0.5 * (lo + hi)
        f_mid = arc.unwrapped_longitude_at(mid) - level_unwrapped
        if abs(f_mid) <= tol_deg or (hi - lo) < 1e-9:
            return mid
        if f_lo * f_mid <= 0.0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return 0.5 * (lo + hi)


def _unwrapped_level(arc: MonotoneArc, target_deg: float) -> float:
    return float(target_deg) % 360.0 + 360.0 * arc.wrap_index


def solve_crossing_jd(
    arc: MonotoneArc,
    target_deg: float,
    tolerance_arcsec: float = DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC,
) -> float:
    """The instant this arc reaches `target_deg`. Unique, because the arc is
    monotone and spans at most one revolution.

    Raises ValueError when the arc does not cover the degree — an honest
    refusal, never a nearest-endpoint guess that a caller could mistake for a
    real contact.
    """
    t = float(target_deg) % 360.0
    if not arc.covers_degree(t):
        raise ValueError(
            f"arc {arc.body}#{arc.arc_index} covers "
            f"[{arc.lon_lo_deg:.6f}, {arc.lon_hi_deg:.6f}]°, not {t:.6f}°"
        )
    return _bisect_for_level(arc, _unwrapped_level(arc, t), float(tolerance_arcsec) / ARCSEC_PER_DEG)


def solve_contact_window(
    arc: MonotoneArc,
    target_deg: float,
    orb_deg: float,
    tolerance_arcsec: float = DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC,
) -> ContactWindow | None:
    """Orb entry / exact / exit for the crossing of `target_deg` on this arc.

    Returns None when the arc does not reach the degree at all — the honest
    empty, distinguished from a zero-width window.
    """
    t = float(target_deg) % 360.0
    if not arc.covers_degree(t):
        return None

    tol_deg = float(tolerance_arcsec) / ARCSEC_PER_DEG
    exact_level = _unwrapped_level(arc, t)
    exact_jd = _bisect_for_level(arc, exact_level, tol_deg)

    lo_level = exact_level - float(orb_deg)
    hi_level = exact_level + float(orb_deg)
    # On a direct arc, longitude rises with time: the lower orb edge is
    # entered first. On a retrograde arc the roles swap.
    first_level, second_level = (lo_level, hi_level) if arc.direction == 1 else (hi_level, lo_level)

    span_lo = min(arc.start_lon_unwrapped, arc.end_lon_unwrapped)
    span_hi = max(arc.start_lon_unwrapped, arc.end_lon_unwrapped)

    def _edge(level: float, fallback_jd: float) -> tuple[float, bool]:
        if span_lo - 1e-9 <= level <= span_hi + 1e-9:
            return _bisect_for_level(arc, level, tol_deg), False
        return fallback_jd, True

    entry_jd, entry_truncated = _edge(first_level, arc.start_jd)
    exit_jd, exit_truncated = _edge(second_level, arc.end_jd)

    return ContactWindow(
        arc=arc,
        target_deg=t,
        orb_deg=float(orb_deg),
        entry_jd=entry_jd,
        exact_jd=exact_jd,
        exit_jd=exit_jd,
        entry_truncated=entry_truncated,
        exit_truncated=exit_truncated,
    )


def find_contacts(
    arcs: Sequence[MonotoneArc],
    target_deg: float,
    orb_deg: float,
    tolerance_arcsec: float = DEFAULT_ROOT_FIND_TOLERANCE_ARCSEC,
) -> list[ContactEvent]:
    """Every crossing of `target_deg` across a body's arcs, in time order.

    Retrograde re-crossings are SEPARATE events, because they are separate
    contacts. That is not a stylistic choice: V4's live measurement of 779,595
    contact events (vs design §2.3's assumed 10k-100k) is only meaningful if
    re-crossings are counted as they occur — ADJUDICATION-14 withdrew §2.3's
    "1-3x per cycle" multiplier on exactly this evidence.
    """
    events: list[ContactEvent] = []
    for arc in arcs_covering_degree(arcs, target_deg):
        window = solve_contact_window(arc, target_deg, orb_deg, tolerance_arcsec)
        if window is None:
            continue
        events.append(
            ContactEvent(
                body=arc.body,
                target_deg=window.target_deg,
                exact_jd=window.exact_jd,
                entry_jd=window.entry_jd,
                exit_jd=window.exit_jd,
                direction=arc.direction,
                arc_index=arc.arc_index,
                entry_truncated=window.entry_truncated,
                exit_truncated=window.exit_truncated,
            )
        )
    events.sort(key=lambda e: e.exact_jd)
    return events


def count_contacts(
    arcs_by_body: dict[str, Sequence[MonotoneArc]],
    target_degs: Iterable[float],
) -> int:
    """How many crossings a (bodies x targets) question actually contains.

    Cheap enough to call before materializing anything — it is a range-predicate
    count, no root-finding — which is what makes ADJUDICATION-14's tier policy
    enforceable rather than aspirational.
    """
    total = 0
    targets = [float(t) % 360.0 for t in target_degs]
    for arcs in arcs_by_body.values():
        for t in targets:
            total += len(arcs_covering_degree(arcs, t))
    return total


__all__ = [
    "ContactEvent",
    "ContactWindow",
    "count_contacts",
    "find_contacts",
    "solve_contact_window",
    "solve_crossing_jd",
]
