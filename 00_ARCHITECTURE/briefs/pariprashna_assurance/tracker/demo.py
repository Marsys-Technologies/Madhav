#!/usr/bin/env python3
"""Seed a disposable demonstration runtime; never use this for campaign evidence."""
from __future__ import annotations
import argparse
from control import EventStore

E = [{"kind": "demo-fixture", "uri": "fixture://pariprashna-assurance/demo"}]

def submit(store, actor, typ, payload, stream=None, key=""):
    return store.submit({"actor_id": actor, "idempotency_key": key or f"{actor}-{typ}-{stream}-{store.next_stream_seq(stream) if stream else 0}", "event_type": typ, "payload": payload, "stream_id": stream, "expected_stream_seq": store.next_stream_seq(stream) if stream else None, "evidence": E})

def accept_item(store, stream, item, number):
    lead = f"lead-{stream.lower()}" if stream.startswith("S") else "lead-p0"
    v = submit(store, "verifier", "verification_accepted", {"verification_id": f"demo-v-{item}", "work_item_id": item, "finder_actor_id": lead, "fixer_actor_id": lead}, stream, f"v-{item}")
    submit(store, "integrator", "work_item_accepted", {"work_item_id": item, "verification_event_id": v["event"]["event_id"]}, stream, f"a-{item}")

def seed(runtime):
    store = EventStore(runtime)
    submit(store, "integrator", "campaign_bootstrapped", {"campaign_id": "demo"}, key="bootstrap")
    v = submit(store, "verifier", "verification_accepted", {"verification_id": "p0-v", "work_item_id": "P0:completion", "finder_actor_id": "lead-p0", "fixer_actor_id": "lead-p0"}, "P0", "p0-v")
    submit(store, "integrator", "work_item_accepted", {"work_item_id": "P0:completion", "verification_event_id": v["event"]["event_id"]}, "P0", "p0-a")
    submit(store, "lead-s1", "work_started", {"session_id": "demo-running", "assignment": "S1 baseline"}, "S1", "running")
    store.record_presence("lead-s1", "demo-running", "S1", "ACTIVE")
    submit(store, "lead-s2", "work_started", {"session_id": "demo-blocked", "assignment": "S2 investigation"}, "S2", "blocked-start")
    submit(store, "lead-s2", "blocked", {"reason": "fixture blocker"}, "S2", "blocked")
    submit(store, "lead-s3", "work_started", {"session_id": "demo-paused", "assignment": "S3 investigation"}, "S3", "paused-start")
    submit(store, "lead-s3", "paused", {"reason": "fixture pause"}, "S3", "paused")
    submit(store, "lead-s4", "work_started", {"session_id": "demo-verifying", "assignment": "S4 verification"}, "S4", "verify-start")
    submit(store, "lead-s4", "verification_started", {}, "S4", "verify")
    submit(store, "lead-s5", "work_started", {"session_id": "demo-failed", "assignment": "S5 test"}, "S5", "failed-start")
    submit(store, "lead-s5", "failed", {"reason": "fixture failure"}, "S5", "failed")
    for n, stage in enumerate(("charter", "baseline", "triage", "remediation", "verification", "regression", "closure")):
        accept_item(store, "S6", f"S6:{stage}", n)
    return store.projection()

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--runtime", required=True); a = p.parse_args(); print(seed(a.runtime)["canonical_hash"])
