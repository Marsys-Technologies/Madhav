"""Overlay projection on the kernel (WP9 5.3; plan §4.3, §5.4; F-11, A08/H-6).

The contact ledger deliberately stores no overlay copy (plan §4.3): overlay
state at any instant is RECOMPUTED from interval sets — the vedha/moorti
writers persist DATE-grain interval rows, and this module is the projection
that turns those intervals into an answer at an instant. Because the ledger
stores no copy, recomputation at a stored contact instant reproduces the
projection's own interval-set answer exactly (plan §10 "Overlay at instant").

Honesty rules implemented here:

  - F-11: an instant OUTSIDE the searched horizon is `unavailable`, never
    `quality_gates=1.0` by default. The legacy path (gochara_v3 engine
    `_compute_quality_gates_from_context`) serves 1.0 wherever no vedha row
    overlaps, which outside the ±460 d build window reads unknown-as-clear;
    this projection takes the searched horizon explicitly so the gap is a
    first-class state, not a silent default.
  - A08 / H-6: one physical obstruction root attenuates ONCE. Vedha rows
    carrying the same `independence_group` (one physical occupancy reached
    through several rules) contribute a single suppression factor to the
    product, not one per row.
  - Cancelled intervals (M-8 vipareeta) are coverage with
    suppression_factor=1.0 — the vedha was searched and classically
    cancelled; the instant is not "no vedha data".

Pure and DB-free: callers map their own rows onto `OverlayInterval`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Mapping

JD_UNIX_EPOCH = 2440587.5
SECONDS_PER_DAY = 86400.0

VEDHA_KINDS = ("house_vedha", "sarvatobhadra", "latta")
MOORTI_KIND = "moorti"


def date_to_jd(d: date) -> float:
    """UT midnight Julian day for a civil date — the shared DATE→instant seam
    used when DATE-grain overlay rows must answer instant-shaped questions."""
    return JD_UNIX_EPOCH + datetime(
        d.year, d.month, d.day, tzinfo=timezone.utc,
    ).timestamp() / SECONDS_PER_DAY


def jd_to_date(jd: float) -> date:
    return datetime.fromtimestamp(
        (jd - JD_UNIX_EPOCH) * SECONDS_PER_DAY, tz=timezone.utc,
    ).date()


@dataclass(frozen=True)
class OverlayInterval:
    """One overlay interval in instant space. `kind` ∈ VEDHA_KINDS ∪ {moorti};
    [start_jd, end_jd] inclusive; `independence_group` is the kernel ids.py
    group of the physical root (None when the row has no active obstruction);
    `suppression_factor` is 1.0 for cancelled (vipareeta) rows and for rows
    with no graded obstruction; `payload` carries kind-specific fields
    (moorti_name, quality_tier, vedha detail, ...)."""

    kind: str
    start_jd: float
    end_jd: float
    independence_group: str | None = None
    suppression_factor: float = 1.0
    cancelled: bool = False
    payload: Mapping[str, Any] = field(default_factory=dict)

    def covers(self, t_jd: float) -> bool:
        return self.start_jd <= t_jd <= self.end_jd


def _merge(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    merged: list[tuple[float, float]] = []
    for a, b in sorted(intervals):
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged


def coverage_gaps(
    intervals: list[OverlayInterval],
    requested_start_jd: float,
    requested_end_jd: float,
) -> list[tuple[float, float]]:
    """Sub-intervals of the requested horizon covered by NO interval — every
    one of these is an `unavailable` span in the coverage manifest (F-11),
    never a silent `quality_gates=1.0`. Empty list = full coverage."""
    if requested_end_jd < requested_start_jd:
        raise ValueError("requested horizon must satisfy start <= end")
    covered = _merge([
        (max(i.start_jd, requested_start_jd), min(i.end_jd, requested_end_jd))
        for i in intervals
        if i.end_jd >= requested_start_jd and i.start_jd <= requested_end_jd
    ])
    gaps: list[tuple[float, float]] = []
    cursor = requested_start_jd
    for a, b in covered:
        if a > cursor:
            gaps.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < requested_end_jd:
        gaps.append((cursor, requested_end_jd))
    return gaps


def quality_gates_at(
    intervals: list[OverlayInterval],
    t_jd: float,
    *,
    searched_horizon: tuple[float, float] | None = None,
) -> tuple[float | None, dict[str, Any]]:
    """The quality-gates projection at one instant, from the vedha interval
    set alone. Returns (factor, detail); factor is None iff the instant is
    `unavailable` (outside the searched horizon — F-11), in which case detail
    carries state='unavailable'. Inside coverage with no overlapping vedha the
    factor is 1.0 with state='clear'. With overlapping vedha the factor is the
    product over DISTINCT independence groups (A08: one root attenuates once),
    each group contributing the strongest (smallest) factor among its rows;
    rows with independence_group=None contribute individually.
    """
    vedha = [i for i in intervals if i.kind in VEDHA_KINDS]
    if searched_horizon is not None and not (
        searched_horizon[0] <= t_jd <= searched_horizon[1]
    ):
        return None, {
            "state": "unavailable",
            "reason": "instant outside the searched overlay horizon (F-11)",
            "searched_horizon": [searched_horizon[0], searched_horizon[1]],
            "fired_vedha": [],
        }
    covering = [i for i in vedha if i.covers(t_jd)]
    if not covering:
        return 1.0, {"state": "clear", "fired_vedha": []}

    by_group: dict[str, float] = {}
    ungrouped: list[float] = []
    for iv in covering:
        factor = 1.0 if iv.cancelled else float(iv.suppression_factor)
        if iv.independence_group:
            prev = by_group.get(iv.independence_group)
            by_group[iv.independence_group] = (
                factor if prev is None else min(prev, factor)
            )
        else:
            ungrouped.append(factor)
    factors = list(by_group.values()) + ungrouped
    product = 1.0
    for f in factors:
        product *= f
    return product, {
        "state": "obstructed",
        "fired_vedha": [
            {
                "vedha_kind": iv.kind,
                "independence_group": iv.independence_group,
                "cancelled": iv.cancelled,
                "suppression_factor": (
                    1.0 if iv.cancelled else float(iv.suppression_factor)
                ),
            }
            for iv in covering
        ],
        "independent_roots": len(by_group) + len(ungrouped),
    }


def moorti_at(
    intervals: list[OverlayInterval],
    t_jd: float,
    *,
    searched_horizon: tuple[float, float] | None = None,
) -> dict[str, Any]:
    """The moorti projection at one instant. Outside the searched horizon →
    state='unavailable' (F-11); inside with no moorti interval → state='absent'
    (a legitimate gap — e.g. an uncomputed truncated run); otherwise the active
    interval's payload with state='active'."""
    if searched_horizon is not None and not (
        searched_horizon[0] <= t_jd <= searched_horizon[1]
    ):
        return {
            "state": "unavailable",
            "reason": "instant outside the searched overlay horizon (F-11)",
        }
    active = [i for i in intervals if i.kind == MOORTI_KIND and i.covers(t_jd)]
    if not active:
        return {"state": "absent"}
    iv = min(active, key=lambda i: i.start_jd)
    return {"state": "active", **dict(iv.payload)}


__all__ = [
    "JD_UNIX_EPOCH",
    "MOORTI_KIND",
    "OverlayInterval",
    "VEDHA_KINDS",
    "coverage_gaps",
    "date_to_jd",
    "jd_to_date",
    "moorti_at",
    "quality_gates_at",
]
