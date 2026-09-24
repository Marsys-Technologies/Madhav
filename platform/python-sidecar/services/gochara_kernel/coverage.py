"""Search-coverage records (plan §4.4; WP1_CONTRACTS.md §4).

One record per (chart, generation, partition = body × target_type, or
event_class, or a moon_on_demand / bodies_on_demand interval). The kernel does not persist
(WP6 owns the table); it builds the row-shaped record so every search —
including a zero-answer search — carries its coverage object (Strategy §3;
L3-Q08).

Moon on demand is first-class (R7): a Moon search writes a coverage record
for its requested interval even though Moon contacts are not persisted by
default — otherwise L3-Q08 cannot be answered for Moon-dependent classes.

Invariant (WP1 §4): targets_resolved + targets_unresolved = targets_requested;
target_resolution_state_counts sums to targets_unresolved across the
non-resolved states; completed_horizon ⊄ requested_horizon only with a
non-NULL unsearched_reason (H-3).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CoverageRecord:
    chart_id: str
    generation: str
    partition_kind: str          # 'body_target' | 'event_class' | 'moon_on_demand'
                                 #   | 'bodies_on_demand' (D-S1(a))
    partition_key: str           # e.g. 'saturn:karaka' | 'moon:interval:<start>/<end>'
    requested_horizon: tuple[float, float]
    completed_horizon: tuple[float, float]
    resolution_arcsec: float
    relations_searched: tuple[str, ...]
    targets_requested: int
    targets_resolved: int
    targets_unresolved: int
    target_resolution_state_counts: dict[str, int]
    unavailable_inputs: dict[str, Any]
    unsearched_reason: str | None
    convention_id: str
    ephemeris_backend: dict[str, Any]

    def __post_init__(self) -> None:
        if self.targets_resolved + self.targets_unresolved != self.targets_requested:
            raise ValueError(
                "coverage invariant violated: resolved + unresolved must equal "
                f"requested, got {self.targets_resolved} + {self.targets_unresolved} "
                f"!= {self.targets_requested}"
            )
        if sum(self.target_resolution_state_counts.values()) != self.targets_unresolved:
            raise ValueError(
                "target_resolution_state_counts must sum to targets_unresolved"
            )
        if (
            self.completed_horizon[1] < self.requested_horizon[0]
            or self.completed_horizon[0] > self.requested_horizon[1]
        ) and self.unsearched_reason is None:
            raise ValueError(
                "completed_horizon outside requested_horizon requires an "
                "unsearched_reason (H-3)"
            )


def build_coverage(
    chart_id: str,
    generation: str,
    partition_kind: str,
    partition_key: str,
    requested_horizon: tuple[float, float],
    completed_horizon: tuple[float, float],
    resolution_arcsec: float,
    relations_searched: tuple[str, ...],
    resolution_states: dict[str, int],
    *,
    convention_id: str,
    ephemeris_backend: dict[str, Any],
    unavailable_inputs: dict[str, Any] | None = None,
    unsearched_reason: str | None = None,
) -> CoverageRecord:
    """Assemble a coverage record from per-target resolution states.

    `resolution_states` counts targets by target_resolution_state: exactly one
    'resolved' entry per resolved target, plus {'unavailable': n,
    'unqualified': n} for the honest nulls (WP1_CONTRACTS.md §2.1). A dangling
    yoga id or an absent overlay is counted here — never a silent skip.
    """
    if partition_kind not in ("body_target", "event_class", "moon_on_demand",
                              "bodies_on_demand"):
        raise ValueError(f"unknown partition_kind {partition_kind!r}")
    resolved = resolution_states.get("resolved", 0)
    unresolved = {k: v for k, v in resolution_states.items() if k != "resolved"}
    return CoverageRecord(
        chart_id=chart_id,
        generation=generation,
        partition_kind=partition_kind,
        partition_key=partition_key,
        requested_horizon=tuple(requested_horizon),
        completed_horizon=tuple(completed_horizon),
        resolution_arcsec=float(resolution_arcsec),
        relations_searched=tuple(relations_searched),
        targets_requested=resolved + sum(unresolved.values()),
        targets_resolved=resolved,
        targets_unresolved=sum(unresolved.values()),
        target_resolution_state_counts=unresolved,
        unavailable_inputs=dict(unavailable_inputs or {}),
        unsearched_reason=unsearched_reason,
        convention_id=convention_id,
        ephemeris_backend=dict(ephemeris_backend),
    )


__all__ = ["CoverageRecord", "build_coverage"]
