"""The matrix STATION-FIX must leave BIT-IDENTICAL (Codex STATION-CODEX-1/2): everything the writer solves on the arc index, through the PRODUCTION wiring.

`compute(ephe_path, index_for)` takes the callable that yields a body's arc index. The test passes `substrate.production_arc_index` — the ONE function both the substrate
(which stores the stations) and the v5 writer's record phase (which solves every point contact) build their index with — so a design that feeds refined stations into the
index through that wiring changes the digests (the withdrawn design did: Mercury conjunction 295.8493268245402 went from 111 roots to 109). The golden
(`fixtures/station_matrix_golden_main.json`) was produced by running this same function on the UNMODIFIED main tree, with `index_for` = main's inline sample_knots +
build_arc_index (main has no shared function).

Per (body, relation, level) it records what `record_store.solve_point_edges` returns for a transit point edge — for every occurrence: (ordinal, contact_id, t_exact, t_in,
t_out, truncated, solver_method) — over the whole 1998-2085 domain AND over the scored horizon (so truncated spans are exercised), plus digests of the index (stations, arcs,
segments) and of the boundary roots. The levels include the two Mercury cases of the reviews: 295.8493268245402 (the withdrawn design lost two crossings on 2074-01-24) and
5.39 (the withdrawn design moved its exit by up to 70 s).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from services.gochara_kernel import contacts as gk_contacts
from services.gochara_kernel import targets
from services.gochara_kernel.evaluator import RecordEdge
from services.gochara_kernel.record_store import solve_point_edges
from services.gochara_kernel.substrate import PhysicalObjectId

BODIES = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
TARGETS = (295.8493268245402, 5.39, 0.3, 359.7, 1.0, 359.0, 0.0, 90.0, 150.25, 210.5, 330.0)
RELATIONS = ("conjunction", "aspect")                       # the record-store relations (aspect = dṛṣṭi contact)
BOUNDARY = ("sign_ingress", "nakshatra_ingress")
HORIZONS = {
    "domain": (datetime(1998, 1, 1, tzinfo=timezone.utc), datetime(2085, 1, 1, tzinfo=timezone.utc)),
    "scored": (datetime(1998, 1, 1, tzinfo=timezone.utc), datetime(2026, 4, 17, tzinfo=timezone.utc)),
}
CONVENTION = "sha256:" + "0" * 64


def _digest(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def _edge(body: str, relation: str, level: float) -> RecordEdge:
    return RecordEdge(
        event_class="marriage", affected_person="native", frame_kind="lagna", frame_arg=None, agent=body.lower(), relation=relation,
        obj=PhysicalObjectId(body=body.lower(), relation_kind=relation, canonical_target=targets.point_target(level), convention_id=CONVENTION),
        object_kind="degree_point", object_role="lord", path_id="P3", rule_version="1.0.0", provenance="verse_cited", operator_role="scored",
        ruling_ref=None, source_text=None, source_page=None, transit=True)


def compute(ephe_path: str, index_for) -> dict[str, dict]:
    """{key: {"n": count, "sha256": digest}}; `index_for(body, ephe_path)` yields the body's arc index (the production wiring)."""
    out: dict[str, dict] = {}
    for body in BODIES:
        idx = index_for(body, ephe_path)
        lines = [f"S|{s!r}" for s in idx.stations]
        lines += [f"A|{a.arc_index}|{a.start_jd!r}|{a.end_jd!r}|{a.start_lon_unwrapped!r}|{a.end_lon_unwrapped!r}|{a.direction}|{a.wrap_index}|{a.station_bounded}" for a in idx.arcs]
        lines += [f"G|{g.arc_index}|{g.start_jd!r}|{g.end_jd!r}|{g.direction}|{g.station_bounded}" for g in idx.segments]
        out[f"{body}|index"] = {"n": len(idx.arcs), "sha256": _digest(lines)}
        edges = {(relation, level): _edge(body, relation, level) for relation in RELATIONS for level in TARGETS}
        for hname, horizon in HORIZONS.items():
            for (relation, level), edge in edges.items():
                # one edge at a time: a refusal ("solver defect": a root outside its own span, the known wrap-cut defect at the 0/360 seam levels) is itself part of the
                # behaviour that must not change, so it is recorded, not skipped
                try:
                    solved = solve_point_edges([edge], arc_index_for=lambda b, _i=idx: _i, horizon=horizon, ephe_path=ephe_path, refine=True)
                    occs = solved.get(id(edge), [])
                    rows = [f"{o.contact.occurrence_ordinal}|{o.contact.contact_id}|{o.t_exact!r}|{o.t_in!r}|{o.t_out!r}|{o.truncated}|{o.solver_method}" for o in occs]
                    out[f"{body}|{hname}|{relation}|{level!r}"] = {"n": len(occs), "sha256": _digest(rows)}
                except RuntimeError as exc:
                    out[f"{body}|{hname}|{relation}|{level!r}"] = {"n": -1, "sha256": _digest([f"REFUSED|{exc}"])}
        for relation in BOUNDARY:
            roots = gk_contacts.find_boundary_roots(idx, body, relation, ephe_path, refine=True)
            out[f"{body}|{relation}"] = {"n": len(roots), "sha256": _digest([f"{r.level_deg!r}|{r.spline_exact_jd!r}|{r.exact_jd!r}|{r.arc.arc_index}" for r in roots])}
    return out
