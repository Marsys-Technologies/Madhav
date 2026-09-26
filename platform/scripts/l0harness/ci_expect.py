#!/usr/bin/env python3
"""ci_expect.py — W-L0-7 readings-runner expectation gate.

Asserts that reading_verdicts.json matches the EXPECTED harness state, pinned
2026-09-26 (report v1.6):

  verdicts:  V-C0-S3 PASS, V-R2-S4 PASS,
             V-R1-S5 / V-R2-S6 / V-R3-S7 UNMEASURED
  findings:  exactly {F-W-L0-7-9, F-W-L0-7-5, F-W-L0-7-8, F-W-L0-7-7}
  step 0 fixture gate green; step 9 reseed+replay green.

ANY divergence fails CI — in both directions. A PASS turning FAIL is a
regression; an UNMEASURED turning PASS means the L1/L2 producer-path findings
(F-W-L0-7-9/-5/-8/-7) were answered upstream and this pin is stale; a new
finding id is a new defect. All three require a deliberate human re-pin of
this file in the same commit that changes the state — fix the artifact, never
weaken the check to get green.

Usage: python3 scripts/l0harness/ci_expect.py [path/to/reading_verdicts.json]
Exit 0 = expected state; exit 1 = divergence (details on stdout).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

DEFAULT_VERDICTS = Path(__file__).resolve().parent / "reading_verdicts.json"

EXPECTED_VERDICTS = {
    "V-C0-S3": "PASS",
    "V-R2-S4": "PASS",
    "V-R1-S5": "UNMEASURED",
    "V-R2-S6": "UNMEASURED",
    "V-R3-S7": "UNMEASURED",
}
EXPECTED_FINDINGS = {"F-W-L0-7-9", "F-W-L0-7-5", "F-W-L0-7-8", "F-W-L0-7-7"}


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_VERDICTS
    state = json.loads(path.read_text())
    failures: list[str] = []

    step0 = state["steps"].get("0") or {}
    if not step0.get("ok"):
        failures.append("step 0 fixture rebuild/state-B gate not green")

    for vid, want in EXPECTED_VERDICTS.items():
        got = (state["verdicts"].get(vid) or {}).get("verdict")
        if got != want:
            failures.append(f"{vid}: expected {want}, measured {got!r}")
    extra = set(state["verdicts"]) - set(EXPECTED_VERDICTS)
    if extra:
        failures.append(f"unexpected verdict ids: {sorted(extra)}")

    findings = {f["id"] for f in state.get("findings", [])}
    if findings != EXPECTED_FINDINGS:
        failures.append(
            f"finding set drift: missing={sorted(EXPECTED_FINDINGS - findings)}, "
            f"new={sorted(findings - EXPECTED_FINDINGS)}")

    replay = state["steps"].get("9_reseed_replay") or {}
    if not (replay.get("ok") and replay.get("r2_catalog_citations_restored")):
        failures.append("step 9 reseed+replay not green (fixture not back in state B)")

    if failures:
        print("ci_expect: DIVERGENCE from the pinned W-L0-7 harness state:")
        for f in failures:
            print(f"  - {f}")
        print("Re-pin EXPECTED_VERDICTS/EXPECTED_FINDINGS deliberately in the "
              "commit that changes the state; do not weaken this gate to get green.")
        return 1
    print("ci_expect: harness state matches the 2026-09-26 pin "
          "(2 PASS / 3 UNMEASURED / 4 named findings / state-B restored)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
