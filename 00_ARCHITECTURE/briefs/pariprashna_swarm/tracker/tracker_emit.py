#!/usr/bin/env python3
"""Append one event line to this writer's event log. Stdlib only. ~30 lines by design."""
import json
import os
import sys
import time

RUNTIME_DIR = os.path.expanduser("~/.pariprashna-tracker")
EVENTS_DIR = os.path.join(RUNTIME_DIR, "events")
VALID_KINDS = {"lane_state", "claim", "gate", "budget", "anomaly", "daemon"}
VALID_EVIDENCE = {"DERIVED", "CLAIMED", "UNKNOWN"}


def emit(writer_id, kind, payload, lane=None, evidence_class="CLAIMED", provenance="tracker_emit.py"):
    if kind not in VALID_KINDS:
        raise ValueError(f"kind must be one of {VALID_KINDS}")
    if evidence_class not in VALID_EVIDENCE:
        raise ValueError(f"evidence_class must be one of {VALID_EVIDENCE}")
    event = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "writer_id": writer_id,
        "lane": lane,
        "kind": kind,
        "payload": payload,
        "evidence_class": evidence_class,
        "provenance": provenance,
    }
    line = (json.dumps(event, separators=(",", ":")) + "\n").encode("utf-8")
    if len(line) > 4096:
        raise ValueError(f"event line {len(line)}B exceeds 4KiB atomic-write budget")
    os.makedirs(EVENTS_DIR, exist_ok=True)
    path = os.path.join(EVENTS_DIR, f"{writer_id}.jsonl")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Emit one Paripraśna tracker event.")
    p.add_argument("--writer-id", required=True)
    p.add_argument("--kind", required=True, choices=sorted(VALID_KINDS))
    p.add_argument("--payload", required=True, help="JSON object string")
    p.add_argument("--lane", default=None)
    p.add_argument("--evidence-class", default="CLAIMED", choices=sorted(VALID_EVIDENCE))
    p.add_argument("--provenance", default="tracker_emit.py (cli)")
    args = p.parse_args()
    emit(args.writer_id, args.kind, json.loads(args.payload), args.lane, args.evidence_class, args.provenance)
