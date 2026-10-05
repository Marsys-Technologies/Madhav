#!/usr/bin/env python3
"""Reproducible mutation evidence for the station refinement (STATION-FIX): neuters ONE guard at a time and requires the station suite
(tests/l3/gochara/test_station_refine.py, real pinned files, no database) to fail for each. Files are restored in a `finally` block.
Exit status is non-zero if any mutation survives or a target string is missing.

    SE_EPHE_PATH=<se1 dir> GOCHARA_SE1_REQUIRE=1 python3 scripts/gochara/mutation_check_station_refine.py [--list]

Run from the platform/ directory."""
import subprocess
import sys

K = "python-sidecar/services/gochara_kernel/"
TEST = "tests/l3/gochara/test_station_refine.py"

MUTATIONS = [
    ("the refiner returns the spline station unchanged (no refinement)", K + "knots.py",
     "    jd = centre + xv\n", "    jd = float(jd_spline)\n"),
    ("the refiner no longer refuses a spline station that is not an ephemeris station", K + "knots.py",
     "    if (speed_a > 0.0) == (speed_b > 0.0):\n        raise StationRefinementError(", "    if False:\n        raise StationRefinementError("),
    ("the stored uncertainty is the nominal 1e-9 d again", K + "knots.py",
     "max(STATION_SIGMA_K * sigma_v, spread, 1e-9), centre_jd=centre", "1e-9, centre_jd=centre"),
    ("the stored uncertainty ignores the disagreement of the two estimators", K + "knots.py",
     "max(STATION_SIGMA_K * sigma_v, spread, 1e-9)", "max(STATION_SIGMA_K * sigma_v, 1e-9)"),
    ("the arc index keeps the spline stations for its boundaries (two instants)", K + "arcs.py",
     "        stations = jds_r\n", "        pass\n"),
    ("the arc index accepts a refiner that reorders the stations", K + "arcs.py",
     "        if any(b <= a for a, b in zip(jds_r, jds_r[1:])) or", "        if False and any(b <= a for a, b in zip(jds_r, jds_r[1:])) or"),
    ("the arc index accepts a refiner that moves a station by days", K + "arcs.py",
     "            if abs(r - s0) > STATION_REFINE_MAX_SHIFT_DAYS:", "            if False:"),
    ("the substrate stores spline-grade stations without refusing", K + "substrate.py",
     "        if index.stations and not index.station_refined:", "        if False:"),
    ("the substrate stores the nominal 1e-9 d uncertainty again", K + "substrate.py",
     "delta_t=float(dt_days), precision_regime=", "delta_t=1e-9, precision_regime="),
    ("the substrate builds its index without the refiner", K + "substrate.py",
     "                                            station_refiner=station_refiner(body, ephe_path))", "                                            )"),
    ("the writer's record-phase arc cache builds without the refiner", "python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py",
     "                    station_refiner=station_refiner(body, ephe_path))", "                    )"),
]


def main() -> int:
    if "--list" in sys.argv:
        for name, f, _o, _n in MUTATIONS:
            print(f"{name}  [{f}]")
        return 0
    survivors = []
    for name, path, old, new in MUTATIONS:
        text = open(path, encoding="utf-8").read()
        if old not in text:
            print(f"TARGET MISSING: {name} ({path})")
            survivors.append(name)
            continue
        try:
            open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
            r = subprocess.run([sys.executable, "-m", "pytest", TEST, "-q", "-x", "-p", "no:cacheprovider"], cwd="python-sidecar",
                               capture_output=True, text=True, timeout=1200)
        finally:
            open(path, "w", encoding="utf-8").write(text)
        caught = r.returncode != 0
        print(("CAUGHT  " if caught else "SURVIVED") + f" {name}")
        if not caught:
            survivors.append(name)
    print(f"{len(MUTATIONS) - len(survivors)}/{len(MUTATIONS)} caught")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
