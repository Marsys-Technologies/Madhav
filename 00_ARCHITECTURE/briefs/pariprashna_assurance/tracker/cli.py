#!/usr/bin/env python3
"""Operational CLI for bootstrap, event emission, replay, and immutable snapshots."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from control import EventStore, RejectedEvent


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--runtime", required=True)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("provision-credentials")
    event = sub.add_parser("emit"); event.add_argument("--actor", required=True); event.add_argument("--token", required=True); event.add_argument("--key", required=True); event.add_argument("--type", required=True); event.add_argument("--payload", required=True); event.add_argument("--evidence", default="[]"); event.add_argument("--stream"); event.add_argument("--expected-seq", type=int)
    init = sub.add_parser("init"); init.add_argument("--token", required=True)
    sub.add_parser("projection"); sub.add_parser("verify")
    snap = sub.add_parser("snapshot"); snap.add_argument("--path", required=True)
    args = p.parse_args(); store = EventStore(args.runtime)
    try:
        if args.command == "provision-credentials": result = store.provision_local_credentials()
        elif args.command == "init":
            if store.authenticate(args.token) != "integrator": raise RejectedEvent("UNAUTHENTICATED", "init requires the provisioned integrator token")
            result = store.submit({"actor_id": "integrator", "idempotency_key": "bootstrap-v1", "event_type": "campaign_bootstrapped", "payload": {"campaign_id": "pariprashna-experience-assurance-v3"}, "evidence": [{"kind": "charter", "uri": "repo://00_ARCHITECTURE/briefs/pariprashna_assurance/ADR_P0_TRACKER_ARCHITECTURE_v1_0.md"}]})
        elif args.command == "emit":
            if store.authenticate(args.token) != args.actor: raise RejectedEvent("UNAUTHENTICATED", "actor does not match the supplied provisioned token")
            result = store.submit({"actor_id": args.actor, "idempotency_key": args.key, "event_type": args.type, "payload": json.loads(args.payload), "evidence": json.loads(args.evidence), "stream_id": args.stream, "expected_stream_seq": args.expected_seq})
        elif args.command == "projection": result = store.projection()
        elif args.command == "verify": result = store.verify_replay()
        else: result = store.export_snapshot(args.path)
        print(json.dumps(result, indent=2, sort_keys=True))
    except RejectedEvent as exc:
        print(json.dumps({"accepted": False, "code": exc.code, "error": str(exc)})); raise SystemExit(2)


if __name__ == "__main__": main()
