#!/usr/bin/env python3
"""
run_l1_ganita_build.py — Cloud Run Job entrypoint for L1 Gaṇita full build.

Calls build_runner.run() directly (bypassing the broken argparse main()).
Exits 0 on PASS, 1 on FAIL/HALT.
"""
import json
import sys
import os

sys.path.insert(0, "/app")

from ga_writers.build_runner import run

CHART_ID = os.environ.get(
    "BUILD_CHART_ID",
    "482012f1-710e-4a25-994a-93821f5871aa",
)

print(f"[run_l1_ganita_build] Starting full build for chart_id={CHART_ID}", flush=True)

result = run(chart_id=CHART_ID)

print(json.dumps(result, indent=2, default=str), flush=True)

status = result.get("status", "UNKNOWN")
print(f"\n[run_l1_ganita_build] Build complete — status={status}", flush=True)

sys.exit(0 if status == "PASS" else 1)
