"""Append one event to the Suvarṇa event log — the only way any role reports progress.

Examples (run from platform/scripts/governance):
  python -m suvarna_tracker.emit item  --item E1.1 --state running --actor builder --detail "scorecard run"
  python -m suvarna_tracker.emit item  --item E1.1 --state done    --actor builder --evidence "nikasha_test/E1.1_SCORECARD.md"
  python -m suvarna_tracker.emit item  --item A.L0 --state done --step census --actor analyst --evidence "census/L0.json"
  python -m suvarna_tracker.emit decision --decision N-6 --state decided --actor native --detail "fix now"
  python -m suvarna_tracker.emit heartbeat --actor conductor --detail "queue: 3 running, 5 ready"
  python -m suvarna_tracker.emit metric --name T1-T5 --value "T1 PASS, T2 FAIL, ..." --actor builder

Exit codes: 0 written · 2 rejected (the event failed validation; nothing written).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from suvarna_tracker.events import EventError, append  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Append one Suvarṇa event")
    ap.add_argument("kind", choices=["item", "decision", "heartbeat", "note", "metric"])
    ap.add_argument("--actor", required=True)
    ap.add_argument("--item"); ap.add_argument("--state"); ap.add_argument("--step")
    ap.add_argument("--decision"); ap.add_argument("--name"); ap.add_argument("--value")
    ap.add_argument("--detail", default=""); ap.add_argument("--evidence")
    ap.add_argument("--progress", type=float)
    ap.add_argument("--events", default=os.environ.get("SUVARNA_EVENTS",
                    os.path.join(os.environ.get("SUVARNA_HOME", "/Users/Dev/suvarna"), "run", "EVENTS.jsonl")))
    a = ap.parse_args(argv)
    ev = {k: v for k, v in {"kind": a.kind, "actor": a.actor, "item": a.item, "state": a.state, "step": a.step,
                            "decision": a.decision, "name": a.name, "value": a.value, "detail": a.detail,
                            "evidence": a.evidence, "progress": a.progress}.items() if v not in (None, "")}
    try:
        out = append(a.events, ev)
    except EventError as exc:
        print(f"rejected: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
