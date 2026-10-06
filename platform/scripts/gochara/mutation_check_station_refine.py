#!/usr/bin/env python3
"""Reproducible mutation evidence for STATION-FIX (reworked per Codex STATION-CODEX-1): neuters ONE guard at a time and requires the station suite
(tests/l3/gochara/test_station_refine.py, real pinned files, no database) to fail for each. Files are restored in a `finally` block.
Exit status is non-zero if any mutation survives or a target string is missing.

    SE_EPHE_PATH=<se1 dir> GOCHARA_SE1_REQUIRE=1 python3 scripts/gochara/mutation_check_station_refine.py [--list] [--only <text>] [--shard K/N]

Run from the platform/ directory. (The whole suite takes about 2.5 minutes, so the full harness takes tens of minutes; `--only` runs a subset.)"""
import subprocess
import sys

K = "python-sidecar/services/gochara_kernel/"
TEST = "tests/l3/gochara/test_station_refine.py"

MUTATIONS = [
    ("the stored row keeps the SPLINE instant again", K + "substrate.py",
     "assign_occurrence_ordinals(\n                physical_object_id=poid, t_exact_list=[jd_to_utc(fix.jd)]", "assign_occurrence_ordinals(\n                physical_object_id=poid, t_exact_list=[jd_to_utc(jd_station)]"),
    ("the stored delta_t is the nominal 1e-9 d again", K + "substrate.py",
     "delta_t=station_delta_t_bound_days(body), precision_regime=STATION_PRECISION_REGIME", "delta_t=1e-9, precision_regime=STATION_PRECISION_REGIME"),
    ("the stored precision regime keeps the old false name", K + "substrate.py",
     "precision_regime=STATION_PRECISION_REGIME,\n                coverage", "precision_regime=STATION_OLD_FALSE_REGIME,\n                coverage"),
    ("the station identity takes the REFINED longitude (event ids change)", K + "substrate.py",
     "            lon = float(index.evaluate(jd_station)) % 360.0\n            fix = refine_station(body, jd_station, ephe_path)", "            fix = refine_station(body, jd_station, ephe_path)\n            lon = float(fix.lon_deg) % 360.0"),
    ("the old-regime guard is gone", K + "substrate.py", "        if n_old:\n", "        if False:\n"),
    ("the refinement does nothing (the spline instant is returned)", K + "knots.py",
     "    jd = centre + xv\n", "    jd = float(jd_spline)\n"),
    ("the refiner no longer refuses a spline station that is not an ephemeris station", K + "knots.py",
     "    if (speed_a > 0.0) == (speed_b > 0.0):\n        raise StationRefinementError(", "    if False:\n        raise StationRefinementError("),
    ("the Jupiter bound shrinks below the measured estimator deviation", K + "knots.py",
     '"Jupiter": 10.0, "Venus"', '"Jupiter": 4.0, "Venus"'),
    ("the Mercury spline-gap bound shrinks below the measured gap", K + "knots.py",
     '"Mercury": 30.0, "Jupiter": 3.0', '"Mercury": 10.0, "Jupiter": 3.0'),
    ("the ROUND-1 DESIGN: the arc index takes the ephemeris-refined stations (as the withdrawn design fed them through the production wiring)", K + "arcs.py",
     "    stations = _station_times(spline, knot_jds)\n", "    from .knots import refine_station as _rs\n    stations = [_rs(body, s, None).jd for s in _station_times(spline, knot_jds)]\n"),
    ("the arc index moves its stations by ~8.6 s (computation touched)", K + "arcs.py",
     "    stations = _station_times(spline, knot_jds)\n", "    stations = [s + 1e-4 for s in _station_times(spline, knot_jds)]\n"),
    ("the production index wiring is bypassed (the writer builds its own index again)", "python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py",
     "arc_cache[body] = production_arc_index(body, ephe_path)", "arc_cache[body] = gk_arcs.build_arc_index(body, *(lambda k: (k.knot_jds, k.longitudes_deg))(sample_knots(body, SUBSTRATE_DOMAIN_START.date(), SUBSTRATE_DOMAIN_END.date(), ephe_path)))"),
    ("the record store starts to use the refinement", K + "record_store.py",
     "from __future__ import annotations\n", "from __future__ import annotations\nfrom .knots import refine_station  # noqa: F401\n"),
    # the PER-KIND TOLERANCES of the golden comparison (occurrences 1e-8 day, roots 5e-8 day, longitudes 1e-8 degree): a value moved just OUTSIDE its kind's tolerance must be caught ...
    ("a stored occurrence entry time moves by 2e-8 day, just OUTSIDE the 1e-8 occurrence tolerance", K + "record_store.py",
     "                t_in=jd_to_utc(t_in_jd),\n", "                t_in=jd_to_utc(t_in_jd + 2e-8),\n"),
    ("a stored occurrence exact time moves by 2e-8 day, just OUTSIDE the 1e-8 occurrence tolerance", K + "record_store.py",
     "                t_exact=jd_to_utc(root.exact_jd) if exact_inside else None,\n", "                t_exact=jd_to_utc(root.exact_jd + 2e-8) if exact_inside else None,\n"),
    ("the reported stations move by 1e-7 day, just OUTSIDE the 5e-8 root tolerance", K + "arcs.py",
     "        stations=stations,\n", "        stations=[s + 1e-7 for s in stations],\n"),
    ("the boundary (ingress) roots move by 1e-7 day, just OUTSIDE the 5e-8 root tolerance", K + "contacts.py",
     "                    aspect_deg=0.0, level=level, arc=arc, level_u=level_u,\n                    tol_deg=tol_deg, ephe_path=ephe_path, refine=refine,\n                )\n    roots.sort(key=lambda r: r.exact_jd)\n    return roots\n",
     "                    aspect_deg=0.0, level=level, arc=arc, level_u=level_u,\n                    tol_deg=tol_deg, ephe_path=ephe_path, refine=refine,\n                )\n    import dataclasses as _dc\n    roots = [_dc.replace(r, exact_jd=r.exact_jd + 1e-7) for r in roots]\n    roots.sort(key=lambda r: r.exact_jd)\n    return roots\n"),
    ("an arc end longitude moves by 2e-8 degree, just OUTSIDE the 1e-8 longitude tolerance", K + "arcs.py",
     "end_lon_unwrapped=float(end_lon),", "end_lon_unwrapped=float(end_lon) + 2e-8,"),
    ("an occurrence is lost (the first solved root of every object is dropped)", K + "record_store.py",
     "            occs.append(PointOccurrence(\n", "            if not occs and exact_inside:\n                continue\n            occs.append(PointOccurrence(\n"),
]

# POSITIVE CONTROLS: a value moved INSIDE its kind's tolerance (platform-noise size) must NOT be caught — the tolerance is not zero and the test is not over-tight.
SURVIVE_OK = [
    ("a stored occurrence entry time moves by 5e-9 day, INSIDE the 1e-8 occurrence tolerance (must survive)", K + "record_store.py",
     "                t_in=jd_to_utc(t_in_jd),\n", "                t_in=jd_to_utc(t_in_jd + 5e-9),\n"),
    ("the reported stations move by 2.5e-8 day, INSIDE the 5e-8 root tolerance (must survive)", K + "arcs.py",
     "        stations=stations,\n", "        stations=[s + 2.5e-8 for s in stations],\n"),
    ("the boundary (ingress) roots move by 2.5e-8 day, INSIDE the 5e-8 root tolerance (must survive)", K + "contacts.py",
     "                    aspect_deg=0.0, level=level, arc=arc, level_u=level_u,\n                    tol_deg=tol_deg, ephe_path=ephe_path, refine=refine,\n                )\n    roots.sort(key=lambda r: r.exact_jd)\n    return roots\n",
     "                    aspect_deg=0.0, level=level, arc=arc, level_u=level_u,\n                    tol_deg=tol_deg, ephe_path=ephe_path, refine=refine,\n                )\n    import dataclasses as _dc\n    roots = [_dc.replace(r, exact_jd=r.exact_jd + 2.5e-8) for r in roots]\n    roots.sort(key=lambda r: r.exact_jd)\n    return roots\n"),
    ("an arc end longitude moves by 5e-9 degree, INSIDE the 1e-8 longitude tolerance (must survive)", K + "arcs.py",
     "end_lon_unwrapped=float(end_lon),", "end_lon_unwrapped=float(end_lon) + 5e-9,"),
]


def classify(code: int, out: str, xml: str | None = None) -> str:
    """Classify a pytest run from its STRUCTURED report (junit XML), not from text (Codex G12 round 4, item 5: `FAILED ... - psycopg.OperationalError: connection lost` used to read as
    CAUGHT). CAUGHT only when a test's CALL phase failed on an ASSERTION (AssertionError, a pytest `Failed: DID NOT RAISE` at the START of the message, or a rewritten `assert ...`; a failure that merely MENTIONS DID NOT RAISE inside another error text is not detection). Everything else
    is NOT evidence of detection: UNEXPECTED-EXCEPTION (a call-phase failure with another exception type: a database error, PermissionError, TypeError...), SETUP-ERROR
    (a fixture/setup/teardown error), COLLECTION-FAILURE, INFRASTRUCTURE (no readable report, other exits). A passing run is SURVIVED."""
    import xml.etree.ElementTree as ET
    if code == 0:
        return "SURVIVED"
    if not xml:
        return f"INFRASTRUCTURE(exit {code}, no report)"
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return f"INFRASTRUCTURE(exit {code}, unreadable report)"
    assertion, other_call, setup, collection = 0, 0, 0, 0
    for case in root.iter("testcase"):
        for el in case.findall("failure"):
            msg = (el.get("message") or "").strip()
            if msg.startswith(("assert ", "AssertionError", "Failed: DID NOT RAISE")):
                assertion += 1
            else:
                other_call += 1
        for el in case.findall("error"):
            if "collection failure" in (el.get("message") or ""):
                collection += 1
            else:
                setup += 1
    if assertion:
        return "CAUGHT"
    if collection or not any(True for _ in root.iter("testcase")):
        return "COLLECTION-FAILURE"
    if other_call:
        return "UNEXPECTED-EXCEPTION"
    if setup:
        return "SETUP-ERROR"
    return f"INFRASTRUCTURE(exit {code})"


def _run(extra=()):
    """One pytest run of the suite; returns (exit code, combined output, junit XML text or None). The XML is the STRUCTURED report `classify` reads."""
    import os
    import tempfile
    fd, xml_path = tempfile.mkstemp(suffix=".xml")
    os.close(fd)
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", TEST, "-q", "-p", "no:cacheprovider", "-rfEs", f"--junitxml={xml_path}", *extra], cwd="python-sidecar",
                           capture_output=True, text=True, timeout=1800)
        xml = open(xml_path, encoding="utf-8").read() if os.path.getsize(xml_path) else None
    finally:
        os.unlink(xml_path)
    return r.returncode, r.stdout + r.stderr, xml


def main() -> int:
    if "--list" in sys.argv:
        for name, f, _o, _n, *_x in [*MUTATIONS, *SURVIVE_OK]:
            print(f"{name}  [{f}]")
        return 0
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    code, out, xml = _run()
    last = [ln for ln in out.splitlines() if " passed" in ln or " failed" in ln]
    if code != 0 or " skipped" in (last[-1] if last else "") or " passed" not in (last[-1] if last else ""):
        print(f"BASELINE NOT GREEN (exit {code}): {last[-1] if last else out[-300:]!r} — no mutation is meaningful; refusing to run")
        return 2
    print(f"BASELINE green: {last[-1]}")
    survivors = []
    ran = [m + ("CAUGHT",) for m in MUTATIONS if not only or only in m[0]] + [m + ("SURVIVED",) for m in SURVIVE_OK if not only or only in m[0]]
    if "--shard" in sys.argv:                                    # --shard K/N: every N-th entry starting at K (independent checkouts can run the shards in parallel)
        k, n = (int(x) for x in sys.argv[sys.argv.index("--shard") + 1].split("/"))
        ran = ran[k::n]
    for name, path, old, new, expect in ran:
        text = open(path, encoding="utf-8").read()
        if old not in text:
            print(f"TARGET MISSING: {name} ({path})")
            survivors.append(name)
            continue
        try:
            open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
            code, out, xml = _run()                       # the WHOLE suite (no -x): the report must hold every failing test so an assertion anywhere is seen
        finally:
            open(path, "w", encoding="utf-8").write(text)
        verdict = classify(code, out, xml)
        print(f"{verdict:<20} {name}" + ("   [expected to SURVIVE]" if expect == "SURVIVED" else ""))
        if verdict != expect:
            survivors.append(name)
    print(f"{len(ran) - len(survivors)}/{len(ran)} as expected")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
