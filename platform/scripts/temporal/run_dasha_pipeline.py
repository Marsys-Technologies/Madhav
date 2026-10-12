"""
Dasha pipeline orchestrator (M3-B+ scope).

At M3-W2-B1, only the Vimshottari leg is implemented. Yogini, Chara, Narayana,
and KP legs land at M3-W2-B2 and M3-W3-C* per PHASE_M3_PLAN_v1_0.md §3.2-§3.3.

Usage:
    python3 platform/scripts/temporal/run_dasha_pipeline.py --systems vimshottari
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


SYSTEMS = {
    "vimshottari": "platform/scripts/temporal/compute_vimshottari.py",
    "yogini":     "platform/scripts/temporal/compute_yogini.py",       # M3-W2-B2
    # Future:
    # "chara":      "platform/scripts/temporal/compute_chara.py",       # M3-W3-C1 (gated on tradition-fork verdict)
    # "narayana":   "platform/scripts/temporal/compute_narayana.py",    # M3-W3-C1 (gated on tradition-fork verdict)
    # "kp":         "platform/scripts/temporal/compute_kp.py",          # M3-W3-C2
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--systems", nargs="+", default=["vimshottari", "yogini"],
        choices=list(SYSTEMS),
        help="Which dasha system(s) to compute. Default: vimshottari + yogini.",
    )
    parser.add_argument("--chart-id", required=True,
                        help="Chart UUID (the charts.chart_id of the chart under test). REQUIRED.")
    parser.add_argument("--birth", required=True,
                        help="ISO8601 birth datetime of the chart under test (timezone-aware), from its `charts` row. REQUIRED: no birth datetime is embedded in this script.")
    parser.add_argument("--horizon-end", default="2061-01-01",
                        help="Forwarded to each engine. M3-W2-B1 + B2 horizon.")
    args = parser.parse_args()

    rc = 0
    for system in args.systems:
        script = ROOT / SYSTEMS[system]
        if not script.exists():
            print(f"[skip] {system}: {script} not yet implemented")
            continue
        cmd = [
            sys.executable, str(script),
            "--chart-id", args.chart_id,
            "--birth", args.birth,
            "--horizon-end", args.horizon_end,
        ]
        print(f"[run] {' '.join(cmd)}")
        result = subprocess.run(cmd)
        rc |= result.returncode

    return rc


if __name__ == "__main__":
    sys.exit(main())
