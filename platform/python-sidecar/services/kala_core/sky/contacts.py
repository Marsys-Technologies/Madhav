"""The contact solver: arc-index bracket → Swiss refinement, and stations.

One solver, the kernel's, used by import (`find_roots` brackets every root on
the monotone arcs and bisects it under direct Swiss at the instant). This
module adds the half-open horizon, the occurrence identity and coverage.
A station is always Swiss-refined (`refine_station`); a spline station is
only its bracket and is never returned as an answer.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from services.gochara_kernel import knots as _knots
from services.gochara_kernel.arcs import ArcIndex
from services.gochara_kernel.contacts import EXACT_SEPARATION_RELATIONS, find_roots
from services.gochara_kernel.substrate import PhysicalObjectId

from .coverage import SkyResult, coverage_of, unavailable
from .events import REFINED_BACKEND, SPLINE_BACKEND, in_horizon, index_domain, numbered
from .identity import event_object, kernel_body, occurrence_id

STATION_METHOD = "swiss_station_fit"


@dataclass(frozen=True)
class Contact:
    body: str
    relation: str
    target_deg: float
    aspect_deg: float
    level_deg: float        # where the body is at the contact: (target − aspect) mod 360
    jd: float
    spline_jd: float
    direction: int
    ordinal: int
    physical_object: PhysicalObjectId
    event_id: uuid.UUID
    solver_method: str


@dataclass(frozen=True)
class Station:
    body: str
    jd: float
    longitude_deg: float
    delta_t_days: float     # the kernel's per-body stored bound
    spline_jd: float        # the bracket centre the refinement started from
    solver_method: str = STATION_METHOD


def _relation_kind(relation: str, aspect_deg: float) -> str:
    # Each dṛṣṭi angle onto one target is its own physical relation.
    return f"{relation}:{aspect_deg:g}" if relation == "drishti_contact" else relation


def solve_contacts(index: ArcIndex, body: str, relation: str, target_deg: float,
                   horizon: tuple[float, float], convention_id: str, *,
                   ephe_path: str | None = None, refine: bool = True) -> SkyResult[Contact]:
    """Exact contacts of `body` with a target longitude in [start, end)."""
    if relation not in EXACT_SEPARATION_RELATIONS:
        raise ValueError(f"{relation!r} is not a contact relation")
    name = kernel_body(body)
    method = REFINED_BACKEND if refine else SPLINE_BACKEND
    coverage = coverage_of(horizon, index_domain(index), backend=method,
                           convention_id=convention_id)
    if coverage.covered is None:
        return unavailable(coverage)
    try:
        roots = find_roots(index, name, relation, target_deg, ephe_path=ephe_path, refine=refine)
    except _knots.EphemerisBackendError:
        return unavailable(coverage_of(horizon, None, backend=method,
                                       convention_id=convention_id))
    contacts = tuple(
        Contact(body=name, relation=relation, target_deg=root.target_deg,
                aspect_deg=root.aspect_deg, level_deg=root.level_deg, jd=root.exact_jd,
                spline_jd=root.spline_exact_jd, direction=root.arc.direction,
                ordinal=ordinal, physical_object=obj, event_id=occurrence_id(obj, ordinal),
                solver_method=method)
        for root, obj, ordinal in numbered(roots, lambda r: event_object(
            name, _relation_kind(relation, r.aspect_deg), r.target_deg, convention_id))
        if in_horizon(root.exact_jd, horizon)
    )
    return SkyResult(contacts, coverage)


def stations(index: ArcIndex, body: str, horizon: tuple[float, float],
             convention_id: str, *, ephe_path: str | None = None) -> SkyResult[Station]:
    """Every station of `body` in [start, end), each refined under Swiss."""
    name = kernel_body(body)
    coverage = coverage_of(horizon, index_domain(index), backend=REFINED_BACKEND,
                           convention_id=convention_id)
    if coverage.covered is None:
        return unavailable(coverage)
    found = []
    try:
        for spline_jd in index.stations:
            fix = _knots.refine_station(name, spline_jd, ephe_path)
            if in_horizon(fix.jd, horizon):
                found.append(Station(name, fix.jd, fix.lon_deg,
                                     _knots.station_delta_t_bound_days(name), float(spline_jd)))
    except _knots.EphemerisBackendError:
        return unavailable(coverage_of(horizon, None, backend=REFINED_BACKEND,
                                       convention_id=convention_id))
    return SkyResult(tuple(found), coverage)


__all__ = ["Contact", "STATION_METHOD", "Station", "solve_contacts", "stations"]
