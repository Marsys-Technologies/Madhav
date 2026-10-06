"""The matrix STATION-FIX must leave UNCHANGED (Codex STATION-CODEX-1/2): everything the writer solves on the arc index, through the PRODUCTION wiring.

`compute(ephe_path, index_for)` takes the callable that yields a body's arc index. The test passes `substrate.production_arc_index` — the ONE function both the substrate
(which stores the stations) and the v5 writer's record phase (which solves every point contact) build their index with — so a design that feeds refined stations into the
index through that wiring changes the result (the withdrawn design did: Mercury conjunction 295.8493268245402 went from 111 roots to 109). The golden
(`fixtures/station_matrix_golden_main.json`) is produced by running this same module on the UNMODIFIED main tree (`python station_golden_matrix.py OUT.json`), with
`index_for` = main's inline sample_knots + build_arc_index (main has no shared function; `main_index` below is that inline construction).

Per (body, relation, level) it records what `record_store.solve_point_edges` returns for a transit point edge — for every occurrence: (ordinal, contact_id, truncated,
solver_method) as DISCRETE values and (t_exact, t_in, t_out) as CONTINUOUS values — over the whole 1998-2085 domain AND over the scored horizon (so truncated spans are
exercised), plus the arc index (stations, arcs, segments) and the boundary roots. The levels include the two Mercury cases of the reviews: 295.8493268245402 (the withdrawn
design lost two crossings on 2074-01-24) and 5.39 (the withdrawn design moved its exit by up to 70 s).

GOLDEN FORMAT (schema 2). {"schema": 2, "tolerance_days": ..., "tolerance_deg": ..., "cases": {key: {"n": int, "rows": [[discrete_list, continuous_list], ...]}}}.
Continuous values are days (unix days for instants, jd for station/arc instants) or degrees (longitudes); None stays None and must match exactly.

WHY A TOLERANCE (and not a digest of float reprs, which schema 1 used): the same code, the same SHA-pinned ephemeris files and the same requirements produce DIFFERENT last
bits of the floats on different platforms — measured Mac arm64 against Linux x86_64 (libm / fused multiply-add): 37 of the 47 Jupiter golden keys had a different sha256 on
Linux although every occurrence count was identical. A digest over repr() is therefore a machine fingerprint, not a regression test. The comparison below is EXACT for
everything discrete (the key set, the occurrence count, the row count, ordinals, contact ids, truncated flags, solver_method, arc/segment structure, refusals) and uses an
absolute tolerance of 1e-7 day (about 8.6 ms) on the continuous instants and 1e-7 degree on the continuous longitudes. The platform difference is of the order 1e-12; the
defects this test exists for are far outside the tolerance (a station moved by 8.6 s, an exit moved by up to 70 s, a lost crossing). A missing or an extra occurrence is
always a failure."""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone

from services.gochara_kernel import contacts as gk_contacts
from services.gochara_kernel import targets
from services.gochara_kernel.evaluator import RecordEdge
from services.gochara_kernel.record_store import solve_point_edges
from services.gochara_kernel.substrate import PhysicalObjectId

SCHEMA = 2
TOLERANCE_DAYS = 1e-7        # continuous instants: ~8.6 ms
TOLERANCE_DEG = 1e-7         # continuous longitudes

BODIES = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
TARGETS = (295.8493268245402, 5.39, 0.3, 359.7, 1.0, 359.0, 0.0, 90.0, 150.25, 210.5, 330.0)
RELATIONS = ("conjunction", "aspect")                       # the record-store relations (aspect = dṛṣṭi contact)
BOUNDARY = ("sign_ingress", "nakshatra_ingress")
HORIZONS = {
    "domain": (datetime(1998, 1, 1, tzinfo=timezone.utc), datetime(2085, 1, 1, tzinfo=timezone.utc)),
    "scored": (datetime(1998, 1, 1, tzinfo=timezone.utc), datetime(2026, 4, 17, tzinfo=timezone.utc)),
}
CONVENTION = "sha256:" + "0" * 64
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _unix_days(t: datetime | None) -> float | None:
    return None if t is None else (t - _EPOCH).total_seconds() / 86400.0


def _edge(body: str, relation: str, level: float) -> RecordEdge:
    return RecordEdge(
        event_class="marriage", affected_person="native", frame_kind="lagna", frame_arg=None, agent=body.lower(), relation=relation,
        obj=PhysicalObjectId(body=body.lower(), relation_kind=relation, canonical_target=targets.point_target(level), convention_id=CONVENTION),
        object_kind="degree_point", object_role="lord", path_id="P3", rule_version="1.0.0", provenance="verse_cited", operator_role="scored",
        ruling_ref=None, source_text=None, source_page=None, transit=True)


def main_index(body: str, ephe_path: str):
    """main's inline index construction (what `substrate.production_arc_index` names on this branch)."""
    from services.gochara_kernel import arcs as gk_arcs
    from services.gochara_kernel import substrate
    from services.gochara_kernel.knots import sample_knots
    ks = sample_knots(body, substrate.SUBSTRATE_DOMAIN_START.date(), substrate.SUBSTRATE_DOMAIN_END.date(), ephe_path)
    return gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg)


def _plain(value):
    """JSON-shaped (tuples are lists), so a computed value and its stored form compare equal."""
    return [_plain(v) for v in value] if isinstance(value, (list, tuple)) else value


def _case(rows: list) -> dict:
    return {"n": len(rows), "rows": rows}


def compute(ephe_path: str, index_for, bodies=BODIES) -> dict:
    """{key: {"n": count, "rows": [[discrete, continuous], ...]}}; `index_for(body, ephe_path)` yields the body's arc index (the production wiring)."""
    out: dict[str, dict] = {}
    for body in bodies:
        idx = index_for(body, ephe_path)
        rows = [[["S"], [float(s)]] for s in idx.stations]
        rows += [[["A", a.arc_index, a.direction, a.wrap_index, a.station_bounded], [a.start_jd, a.end_jd, a.start_lon_unwrapped, a.end_lon_unwrapped]] for a in idx.arcs]
        rows += [[["G", g.arc_index, g.direction, g.station_bounded], [g.start_jd, g.end_jd]] for g in idx.segments]
        out[f"{body}|index"] = {"n": len(idx.arcs), "rows": rows}
        edges = {(relation, level): _edge(body, relation, level) for relation in RELATIONS for level in TARGETS}
        for hname, horizon in HORIZONS.items():
            for (relation, level), edge in edges.items():
                # one edge at a time: a refusal ("solver defect": a root outside its own span) is itself part of the behaviour that must not change, so it is recorded, not skipped
                key = f"{body}|{hname}|{relation}|{level!r}"
                try:
                    solved = solve_point_edges([edge], arc_index_for=lambda b, _i=idx: _i, horizon=horizon, ephe_path=ephe_path, refine=True)
                    occs = solved.get(id(edge), [])
                    out[key] = _case([[[o.contact.occurrence_ordinal, str(o.contact.contact_id), o.truncated, o.solver_method],
                                       [_unix_days(o.t_exact), _unix_days(o.t_in), _unix_days(o.t_out)]] for o in occs])
                except RuntimeError as exc:
                    out[key] = {"n": -1, "rows": [[["REFUSED", type(exc).__name__], []]]}
        for relation in BOUNDARY:
            roots = gk_contacts.find_boundary_roots(idx, body, relation, ephe_path, refine=True)
            out[f"{body}|{relation}"] = _case([[["R", r.arc.arc_index], [r.level_deg, r.spline_exact_jd, r.exact_jd]] for r in roots])
    return out


def compare(golden_cases: dict, got_cases: dict, tol_days: float = TOLERANCE_DAYS, tol_deg: float = TOLERANCE_DEG) -> list[str]:
    """Every difference between a golden and a freshly computed matrix, as readable strings (empty = identical within tolerance).

    EXACT: the key set, `n`, the row count, every discrete value, and which continuous values are None. TOLERANT: a continuous value within `tol_days` (instants) of the
    golden. The first discrete column is a tag; a continuous column's unit is the tolerance of its tag: longitudes of an arc (columns 2 and 3 of an "A" row) and the level
    of a boundary root (column 0 of an "R" row) are degrees, everything else is days."""
    problems: list[str] = []
    if set(golden_cases) != set(got_cases):
        problems.append(f"key set differs: missing {sorted(set(golden_cases) - set(got_cases))[:5]}, extra {sorted(set(got_cases) - set(golden_cases))[:5]}")
    for key in sorted(set(golden_cases) & set(got_cases)):
        g, c = golden_cases[key], got_cases[key]
        if g["n"] != c["n"]:
            problems.append(f"{key}: occurrence/arc count {g['n']} -> {c['n']}")
            continue
        if len(g["rows"]) != len(c["rows"]):
            problems.append(f"{key}: row count {len(g['rows'])} -> {len(c['rows'])}")
            continue
        for i, ((gd, gc), (cd, cc)) in enumerate(zip(g["rows"], c["rows"])):
            if _plain(gd) != _plain(cd):
                problems.append(f"{key}: row {i} discrete {gd} -> {cd}")
                break
            if len(gc) != len(cc):
                problems.append(f"{key}: row {i} continuous width {len(gc)} -> {len(cc)}")
                break
            bad = None
            for j, (a, b) in enumerate(zip(gc, cc)):
                if a is None or b is None:
                    if a is not b:
                        bad = f"column {j} {a} -> {b}"
                        break
                    continue
                if not (math.isfinite(a) and math.isfinite(b)):
                    bad = f"column {j} non-finite {a} -> {b}"
                    break
                degrees = (gd[0] == "A" and j >= 2) or (gd[0] == "R" and j == 0)
                tol = tol_deg if degrees else tol_days
                if abs(a - b) > tol:
                    bad = f"column {j} moved by {abs(a - b):.3e} ({'deg' if degrees else 'day'}, tolerance {tol:g})"
                    break
            if bad:
                problems.append(f"{key}: row {i} {bad}")
                break
    return problems


def golden_document(cases: dict) -> dict:
    return {"schema": SCHEMA, "tolerance_days": TOLERANCE_DAYS, "tolerance_deg": TOLERANCE_DEG, "cases": cases}


def dumps(document: dict) -> str:
    """Compact, stable text: one case per line, keys sorted (a reviewable diff, no float reformatting)."""
    lines = [json.dumps({k: document[k] for k in ("schema", "tolerance_days", "tolerance_deg")}, sort_keys=True)[:-1] + ', "cases": {']
    keys = sorted(document["cases"])
    for n, k in enumerate(keys):
        lines.append(json.dumps(k) + ": " + json.dumps(document["cases"][k], separators=(",", ":")) + ("," if n < len(keys) - 1 else ""))
    lines.append("}}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import os
    if len(sys.argv) != 2:
        raise SystemExit("usage: SE_EPHE_PATH=<se1 dir> python station_golden_matrix.py OUT.json   (run on the UNMODIFIED main tree; see the module docstring)")
    open(sys.argv[1], "w", encoding="utf-8").write(dumps(golden_document(compute(os.environ["SE_EPHE_PATH"], main_index))))
