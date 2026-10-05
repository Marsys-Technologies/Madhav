"""The matrix STATION-FIX must leave BIT-IDENTICAL (Codex STATION-CODEX-1, ruling A): the arc index and everything solved on it — arcs, segments, point-contact
roots (conjunction and dṛṣṭi), their in-orb spans, and the boundary (sign / nakṣatra) roots — over the WHOLE 1998-2085 substrate domain, for the five bodies that have
stations, including the Mercury conjunction target 295.8493268245402 on which a refinement that moved the arc boundary lost two real crossings (2074-01-24).

`compute(ephe_path)` returns {key: {"n": count, "sha256": digest}}. The golden file next to this module was produced by running exactly this function on the UNMODIFIED
main tree (`fixtures/station_matrix_golden_main.json`); the test recomputes it on the branch and compares. Nothing here passes a station refiner anywhere.
"""
from __future__ import annotations

import hashlib
from datetime import date

from services.gochara_kernel import arcs as gk_arcs
from services.gochara_kernel import contacts as gk_contacts
from services.gochara_kernel.knots import sample_knots
from services.gochara_kernel.record_store import _in_orb_span_around_root

BODIES = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
TARGETS = (295.8493268245402, 0.3, 359.7, 1.0, 359.0, 0.0, 90.0, 150.25, 210.5, 330.0)
RELATIONS = ("conjunction", "drishti_contact")
BOUNDARY = ("sign_ingress", "nakshatra_ingress")
ORB_DEG = 1.0
DOMAIN = (date(1998, 1, 1), date(2085, 1, 1))


def _digest(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def compute(ephe_path: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for body in BODIES:
        ks = sample_knots(body, DOMAIN[0], DOMAIN[1], ephe_path)
        idx = gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg)
        lines = [f"S|{s!r}" for s in idx.stations]
        lines += [f"A|{a.arc_index}|{a.start_jd!r}|{a.end_jd!r}|{a.start_lon_unwrapped!r}|{a.end_lon_unwrapped!r}|{a.direction}|{a.wrap_index}|{a.station_bounded}" for a in idx.arcs]
        lines += [f"G|{g.arc_index}|{g.start_jd!r}|{g.end_jd!r}|{g.direction}|{g.station_bounded}" for g in idx.segments]
        out[f"{body}|index"] = {"n": len(idx.arcs), "sha256": _digest(lines)}
        for relation in RELATIONS:
            for target in TARGETS:
                roots = gk_contacts.find_roots(idx, body, relation, target, ephe_path, refine=True)
                rows = []
                for r in roots:
                    a, b = _in_orb_span_around_root(idx, r, ORB_DEG)
                    rows.append(f"{r.level_deg!r}|{r.aspect_deg!r}|{r.spline_exact_jd!r}|{r.exact_jd!r}|{r.arc.arc_index}|{a!r}|{b!r}")
                out[f"{body}|{relation}|{target!r}"] = {"n": len(roots), "sha256": _digest(rows)}
        for relation in BOUNDARY:
            roots = gk_contacts.find_boundary_roots(idx, body, relation, ephe_path, refine=True)
            out[f"{body}|{relation}"] = {"n": len(roots), "sha256": _digest([f"{r.level_deg!r}|{r.spline_exact_jd!r}|{r.exact_jd!r}|{r.arc.arc_index}" for r in roots])}
    return out
