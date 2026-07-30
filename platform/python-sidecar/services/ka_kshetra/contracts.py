"""
services.ka_kshetra.contracts — the cross-lane dataclass contract for the W2
field pipeline.

OWNED BY NOBODY (KALA_W2_FIELD_DESIGN_v1_0.md §0): this module is frozen by
the design doc and is edited only by a cross-lane PR. A lane never reads
another lane's *code*; it reads another lane's *table* or calls its one
published function, whose input/output shapes live here.

Lane A (this PR) seeds the two shapes its own published function
(`stage2_promise.promise_prior`) needs: `Route` and `PromisePrior`
(design §3.3). Lanes B/C/D/E add their own published-function shapes here in
their own PRs — this file is additive-only across lanes; no lane renames or
removes another lane's dataclass without a cross-lane PR.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    """One Yen's-algorithm route from a significator seed to an event_class sink
    (KALA_W2_FIELD_DESIGN_v1_0.md §3.3). Mirrors a `kala_field_routes` row."""

    event_class: str
    route_rank: int
    path_node_ids: tuple[str, ...]          # ordered, source -> ... -> 'event_class:<e>'
    path_edge_ids: tuple[int, ...]          # FK-shaped refs into kala_field_promise_edges.id
    route_gain: float                       # p_r = Pi_edges c = exp(-cost(r)) in (0, 1]
    is_primary: bool                        # route_rank == 1
    suppressed_by: tuple[str, ...] = ()     # vighna keys obstructing this route


@dataclass(frozen=True)
class PromisePrior:
    """Return shape of the Lane A -> Lanes C/D published function
    `stage2_promise.promise_prior(chart_id, event_class, conn)`
    (KALA_W2_FIELD_DESIGN_v1_0.md §3.3, "Published function" block)."""

    p: float                      # noisy-OR promise prior P_e in [0, 1)
    routes: tuple[Route, ...]
    n_routes: int
    dropped_below_floor: int      # routes with p_r < route_floor (0.02), dropped
    fact_ids: tuple[str, ...]     # source_fact_id lineage across the routes' edges
