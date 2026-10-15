"""Boundary-event enumeration per body, with its canonical event key.

Roots come from the kernel's arc index (`find_boundary_roots`, every 360°
band and the 0° seam included); this module adds the half-open horizon,
the physical identity and the occurrence ordinal. Ordinals are assigned over
the index's whole domain before the horizon is applied, so a partition never
renumbers an event and an event on a partition edge belongs to exactly one
partition: the one it starts.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from services.gochara_kernel.arcs import ArcIndex
from services.gochara_kernel.contacts import ContactRoot, find_boundary_roots
from services.gochara_kernel.convention import KAKSHYA_CELL_DEG, NAKSHATRA_DEG, SIGN_DEG
from services.gochara_kernel.knots import EphemerisBackendError
from services.gochara_kernel.substrate import PhysicalObjectId

from .coverage import SkyResult, coverage_of, unavailable
from .identity import event_object, kernel_body, occurrence_id

CELL_WIDTH_DEG = {
    "sign_ingress": SIGN_DEG,
    "nakshatra_ingress": NAKSHATRA_DEG,
    "kakshya_cell_crossing": KAKSHYA_CELL_DEG,
}

# Solver labels: refined roots are Swiss-bisected at the instant; unrefined
# roots are the spline's and say so.
REFINED_BACKEND = "swieph"
SPLINE_BACKEND = "arc_spline_unrefined"


def index_domain(index: ArcIndex) -> tuple[float, float]:
    return float(index.knot_jds[0]), float(index.knot_jds[-1])


def numbered(roots: Sequence[ContactRoot],
             obj_of: Callable[[ContactRoot], PhysicalObjectId]
             ) -> list[tuple[ContactRoot, PhysicalObjectId, int]]:
    """Ordinals 1..N per physical object in solved-time order."""
    counts: dict[PhysicalObjectId, int] = {}
    out = []
    for root in sorted(roots, key=lambda r: r.exact_jd):
        obj = obj_of(root)
        counts[obj] = counts.get(obj, 0) + 1
        out.append((root, obj, counts[obj]))
    return out


def in_horizon(jd: float, horizon: tuple[float, float]) -> bool:
    return horizon[0] <= jd < horizon[1]


@dataclass(frozen=True)
class SkyEvent:
    body: str
    relation: str
    level_deg: float
    jd: float
    direction: int          # +1 direct crossing, -1 retrograde crossing
    cell_after: int         # the half-open cell [k·w, (k+1)·w) occupied just after
    ordinal: int
    physical_object: PhysicalObjectId
    event_id: uuid.UUID
    solver_method: str


def boundary_events(index: ArcIndex, body: str, relations: Iterable[str],
                    horizon: tuple[float, float], convention_id: str, *,
                    ephe_path: str | None = None, refine: bool = True) -> SkyResult[SkyEvent]:
    """Every sign / nakṣatra / kakṣyā boundary crossing of `body` in [start, end)."""
    name = kernel_body(body)
    method = REFINED_BACKEND if refine else SPLINE_BACKEND
    coverage = coverage_of(horizon, index_domain(index), backend=method,
                           convention_id=convention_id)
    if coverage.covered is None:
        return unavailable(coverage)
    events: list[SkyEvent] = []
    for relation in relations:
        width = CELL_WIDTH_DEG[relation]
        cells = round(360.0 / width)
        try:
            roots = find_boundary_roots(index, name, relation, ephe_path=ephe_path, refine=refine)
        except EphemerisBackendError:
            return unavailable(coverage_of(horizon, None, backend=method,
                                           convention_id=convention_id))
        for root, obj, ordinal in numbered(
                roots, lambda r: event_object(name, relation, r.level_deg, convention_id)):
            if not in_horizon(root.exact_jd, horizon):
                continue
            boundary = round(root.level_deg / width)
            events.append(SkyEvent(
                body=name, relation=relation, level_deg=root.level_deg % 360.0,
                jd=root.exact_jd, direction=root.arc.direction,
                cell_after=(boundary if root.arc.direction > 0 else boundary - 1) % cells,
                ordinal=ordinal, physical_object=obj,
                event_id=occurrence_id(obj, ordinal), solver_method=method,
            ))
    events.sort(key=lambda e: (e.jd, e.relation, e.level_deg))
    return SkyResult(tuple(events), coverage)


__all__ = ["CELL_WIDTH_DEG", "REFINED_BACKEND", "SPLINE_BACKEND", "SkyEvent",
           "boundary_events", "in_horizon", "index_domain", "numbered"]
