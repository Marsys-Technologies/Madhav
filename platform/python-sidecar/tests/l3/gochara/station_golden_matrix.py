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

GOLDEN FORMAT (schema 2). {"schema": 2, "tolerances": {...}, "provenance": {...}, "cases": {key: {"n": int, "rows": [[discrete_list, continuous_list], ...]}}}.
Continuous values are days (unix days for instants, jd for station/arc instants) or degrees (longitudes); None stays None and must match exactly.

WHY A TOLERANCE (and not a digest of float reprs, which schema 1 used): the same code, the same SHA-pinned ephemeris files and the same library versions give DIFFERENT last
bits of the floats on different Python builds and platforms, so a digest over repr() is a machine fingerprint, not a regression test (CI failed on a golden that passed locally;
37 of the 47 Jupiter digests differed). MEASURED over all 69,044 continuous values of the 235 cases, golden (macOS arm64, Python 3.13.7) against two other environments:
    - Mac arm64 Python 3.11.15 (same numpy 2.4.6 / scipy 1.17.1 / pyswisseph 20230604): 66,317 bit-identical; maximum difference 1.40e-08 day (stations and arcs/segments),
      9.3e-09 day (ingress roots), 2.8e-09 day (occurrences), 1.29e-09 degree. So the PYTHON BUILD ALONE (3.13 vs 3.11) accounts for the whole maximum.
    - Linux x86_64 Python 3.11.16 (glibc 2.41, the same library versions): 66,326 bit-identical; the same maxima. Mac 3.11 against Linux 3.11 (architecture/OS alone):
      68,989 bit-identical, maxima 9.4e-10 day (occurrences), 4.7e-10 day (roots), 1.1e-13 degree.
    CI runs `ubuntu-latest` (x86_64) with Python 3.11 (`actions/setup-python` '3.11') and unpinned numpy/scipy (requirements-ci.txt: numpy>=2.1.1, scipy>=1.13.0), which the
    Linux Docker image python:3.11-slim reproduces; the tolerance covers BOTH effects (Python build and architecture).
    Every DISCRETE value (counts, ordinals, contact ids, truncated flags, solver_method, arc/segment structure) was identical in all three environments.
The tolerances (TOLERANCES, per kind) are the measurement plus headroom: occurrences 1e-8 day (3.6x the measured 2.8e-9: tight where the solver is well-conditioned and what the
writer stores); station, arc, segment and sign/nakshatra ingress roots 5e-8 day (3.6x the measured 1.40e-8; looser because a station is the zero of the spline's velocity and an
ingress is a boundary root - ill-conditioned root-finds that amplify last-bit differences, the occurrence solver's own accuracy being delta_t 1e-9 day); longitudes 1e-8 degree
(7.8x the measured 1.29e-9). The defects this test exists for are orders of magnitude outside them (a station moved by 8.6 s = 1e-4 day, an exit moved by up to 70 s, a lost
crossing). The comparison is EXACT for everything discrete (key set, counts, row counts, ordinals, contact ids, truncated flags, solver_method, arc/segment structure, refusal
identity = exception type + message with the floats masked) - a missing or an extra occurrence is always a failure. The measurement and both environments are recorded in the
fixture's `provenance`."""
from __future__ import annotations

import json
import math
import re
import sys
from datetime import datetime, timezone

from services.gochara_kernel import contacts as gk_contacts
from services.gochara_kernel import targets
from services.gochara_kernel.evaluator import RecordEdge
from services.gochara_kernel.record_store import solve_point_edges
from services.gochara_kernel.substrate import PhysicalObjectId

SCHEMA = 2
# Absolute tolerances on CONTINUOUS values, per kind (see the docstring for the measurement they rest on).
TOLERANCES = {"occurrence_days": 1e-8,      # solved occurrence t_exact / t_in / t_out (what the writer stores): ~0.86 ms
              "root_days": 5e-8,            # station, arc, segment and sign/nakshatra ingress-root instants (jd): ~4.3 ms
              "longitude_deg": 1e-8}        # arc longitudes and boundary levels

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


_NUMBER = re.compile(r"[-+]?\d+\.\d+(?:[eE][-+]?\d+)?")


def refusal_identity(exc: BaseException) -> list:
    """What a refusal IS: its exception type and its message with every floating-point literal replaced by `<num>` (the message quotes instants and longitudes, which carry
    the platform's last bits); the rest of the text is compared EXACTLY, so a refusal for a different reason is a different refusal."""
    return ["REFUSED", type(exc).__name__, _NUMBER.sub("<num>", str(exc))]


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
                    out[key] = {"n": -1, "rows": [[refusal_identity(exc), []]]}
        for relation in BOUNDARY:
            roots = gk_contacts.find_boundary_roots(idx, body, relation, ephe_path, refine=True)
            out[f"{body}|{relation}"] = _case([[["R", r.arc.arc_index], [r.level_deg, r.spline_exact_jd, r.exact_jd]] for r in roots])
    return out


def kind_of(tag, column: int) -> str:
    """The tolerance kind of one continuous column: an 'S' station row (jd), an 'A' arc row (columns 0-1 jd, 2-3 longitude), a 'G' segment row (jd), an 'R' ingress root
    (column 0 the boundary level in degrees, 1-2 jd); any other row is a solved occurrence (t_exact, t_in, t_out)."""
    if tag == "A":
        return "longitude_deg" if column >= 2 else "root_days"
    if tag == "R":
        return "longitude_deg" if column == 0 else "root_days"
    if tag in ("S", "G"):
        return "root_days"
    return "occurrence_days"


def compare(golden_cases: dict, got_cases: dict, tolerances: dict | None = None) -> list[str]:
    """Every difference between a golden and a freshly computed matrix, as readable strings (empty = identical within tolerance).

    EXACT: the key set, `n`, the row count, every discrete value, and which continuous values are None. TOLERANT: a continuous value within the tolerance of its kind
    (`kind_of`; `TOLERANCES`) of the golden."""
    tol = TOLERANCES if tolerances is None else tolerances
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
                kind = kind_of(gd[0], j)
                if abs(a - b) > tol[kind]:
                    bad = f"column {j} ({kind}) moved by {abs(a - b):.3e} (tolerance {tol[kind]:g})"
                    break
            if bad:
                problems.append(f"{key}: row {i} {bad}")
                break
    return problems


def difference_table(a: dict, b: dict) -> dict:
    """The measurement the tolerances rest on: over every continuous value of two computed matrices, how many are bit-identical and the maximum absolute difference per kind
    (and the number of DISCRETE differences, which must be zero)."""
    out = {"values": 0, "bit_identical": 0, "discrete_differences": 0, "max_difference": {k: 0.0 for k in TOLERANCES}}
    for key in a:
        for (ad, ac), (bd, bc) in zip(a[key]["rows"], b[key]["rows"]):
            out["discrete_differences"] += _plain(ad) != _plain(bd)
            for j, (x, y) in enumerate(zip(ac, bc)):
                if x is None or y is None:
                    continue
                out["values"] += 1
                out["bit_identical"] += x == y
                kind = kind_of(ad[0], j)
                out["max_difference"][kind] = max(out["max_difference"][kind], abs(x - y))
    return out


def golden_document(cases: dict, provenance: dict | None = None) -> dict:
    doc = {"schema": SCHEMA, "tolerances": TOLERANCES}
    if provenance is not None:
        doc["provenance"] = provenance
    doc["cases"] = cases
    return doc


MEASUREMENT_REASON = ("tolerances = measured maximum over all continuous values + headroom; station/arc/segment/ingress roots are looser than occurrences because a station is the "
                      "zero of the spline velocity and an ingress a boundary root, ill-conditioned root-finds that amplify last-bit differences (the occurrence solver's own accuracy is "
                      "delta_t 1e-9 day)")


def measurement_block(cases: dict, others: dict) -> dict:
    """`others` = {name: {"environment": {...}, "cases": <computed matrix>}}: the cross-environment measurement the tolerances rest on, with the headroom per kind."""
    pairs, worst = {}, {k: 0.0 for k in TOLERANCES}
    for name, other in others.items():
        table = difference_table(cases, other["cases"])
        pairs[name] = {"environment": other["environment"], **table}
        worst = {k: max(worst[k], table["max_difference"][k]) for k in worst}
    return {"reason": MEASUREMENT_REASON, "pairs": pairs, "max_difference_over_pairs": worst, "tolerances": TOLERANCES,
            "headroom_factor": {k: (TOLERANCES[k] / worst[k] if worst[k] else None) for k in worst}}


def provenance_of(ephe_path: str) -> dict:
    """Where a golden came from: the tree it was computed on (commit and cleanliness), the machine, the library versions and the sha256 of the ephemeris files it read."""
    import hashlib
    import os
    import platform
    import subprocess
    import numpy
    import scipy
    import swisseph

    def git(*args):
        try:
            return subprocess.run(["git", *args], capture_output=True, text=True, cwd=os.getcwd()).stdout.strip()
        except OSError:
            return "unavailable"

    files = {}
    for name in sorted(os.listdir(ephe_path)):
        if name.endswith(".se1"):
            files[name] = hashlib.sha256(open(os.path.join(ephe_path, name), "rb").read()).hexdigest()
    return {"source_commit": git("rev-parse", "HEAD"), "source_tree_clean": git("status", "--porcelain", "--untracked-files=no") == "",
            "generator": "tests/l3/gochara/station_golden_matrix.py (python station_golden_matrix.py OUT.json), index_for = main_index",
            "platform": platform.platform(), "machine": platform.machine(), "python": platform.python_version(),
            "pyswisseph": swisseph.__version__, "swisseph_c_version": swisseph.version, "numpy": numpy.__version__, "scipy": scipy.__version__,
            "ephemeris_files_sha256": files, "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def dumps(document: dict) -> str:
    """Compact, stable text: the header (schema, tolerances, provenance) on the first line, then one case per line, keys sorted (a reviewable diff, no float reformatting)."""
    head = {k: v for k, v in document.items() if k != "cases"}
    lines = [json.dumps(head, sort_keys=True)[:-1] + ', "cases": {']
    keys = sorted(document["cases"])
    for n, k in enumerate(keys):
        lines.append(json.dumps(k) + ": " + json.dumps(document["cases"][k], separators=(",", ":")) + ("," if n < len(keys) - 1 else ""))
    lines.append("}}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import os
    if len(sys.argv) != 2:
        raise SystemExit("usage: SE_EPHE_PATH=<se1 dir> [STATION_GOLDEN_MEASUREMENT=<spec.json>] python station_golden_matrix.py OUT.json   (run on the UNMODIFIED main tree; see the module docstring)")
    _ephe = os.environ["SE_EPHE_PATH"]
    _cases = compute(_ephe, main_index)
    _prov = provenance_of(_ephe)
    if os.environ.get("STATION_GOLDEN_MEASUREMENT"):         # {name: {"environment": {...}, "cases_file": path}} of the OTHER environments computed separately
        _spec = json.load(open(os.environ["STATION_GOLDEN_MEASUREMENT"]))
        _prov["cross_environment_measurement"] = measurement_block(
            json.loads(json.dumps(_cases)), {n: {"environment": s["environment"], "cases": json.load(open(s["cases_file"]))} for n, s in _spec.items()})
    open(sys.argv[1], "w", encoding="utf-8").write(dumps(golden_document(_cases, _prov)))
