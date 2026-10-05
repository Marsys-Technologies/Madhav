#!/usr/bin/env python3
"""Reproducible mutation evidence for STATION-FIX (reworked per Codex STATION-CODEX-1): neuters ONE guard at a time and requires the station suite
(tests/l3/gochara/test_station_refine.py, real pinned files, no database) to fail for each. Files are restored in a `finally` block.
Exit status is non-zero if any mutation survives or a target string is missing.

    SE_EPHE_PATH=<se1 dir> GOCHARA_SE1_REQUIRE=1 python3 scripts/gochara/mutation_check_station_refine.py [--list] [--only <text>]

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
    ("the arc index moves its stations by ~8.6 s (computation touched)", K + "arcs.py",
     "    stations = _station_times(spline, knot_jds)\n", "    stations = [s + 1e-4 for s in _station_times(spline, knot_jds)]\n"),
    ("the record store starts to use the refinement", K + "record_store.py",
     "from __future__ import annotations\n", "from __future__ import annotations\nfrom .knots import refine_station  # noqa: F401\n"),
]


def main() -> int:
    if "--list" in sys.argv:
        for name, f, _o, _n in MUTATIONS:
            print(f"{name}  [{f}]")
        return 0
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    survivors = []
    ran = [m for m in MUTATIONS if not only or only in m[0]]
    for name, path, old, new in ran:
        text = open(path, encoding="utf-8").read()
        if old not in text:
            print(f"TARGET MISSING: {name} ({path})")
            survivors.append(name)
            continue
        try:
            open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
            r = subprocess.run([sys.executable, "-m", "pytest", TEST, "-q", "-x", "-p", "no:cacheprovider"], cwd="python-sidecar",
                               capture_output=True, text=True, timeout=1800)
        finally:
            open(path, "w", encoding="utf-8").write(text)
        caught = r.returncode != 0
        print(("CAUGHT  " if caught else "SURVIVED") + f" {name}")
        if not caught:
            survivors.append(name)
    print(f"{len(ran) - len(survivors)}/{len(ran)} caught")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
