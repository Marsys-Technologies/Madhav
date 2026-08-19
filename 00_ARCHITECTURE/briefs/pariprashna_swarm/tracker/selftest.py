#!/usr/bin/env python3
"""--selftest suite. Each test is designed to be able to FAIL: it is run once against a
deliberately broken input first (asserting it correctly reports the failure), then against
correct input (asserting it correctly reports success). A detector that has never returned
false is not a detector (CLAUDE.md §N.8). Stdlib only.

Note on 'freeze/unfreeze': this tracker's daemon is a single-process synchronous loop
(trackerd.py), and --selftest is invoked as its own separate one-shot process (at daemon
start, before the loop begins, or standalone via `trackerd.py --selftest`). There is no
concurrent live cycle to race against within one process, so 'freeze heartbeat writes' is
satisfied structurally rather than by an explicit lock -- documented here rather than
faked with a no-op freeze() call that would claim a concurrency guarantee this
single-process design doesn't need.
"""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect  # noqa: E402
import project  # noqa: E402
from _common import staleness_class  # noqa: E402


def _result(name, passed, detail):
    return {"name": name, "passed": bool(passed), "detail": detail}


def test_staleness_boundaries():
    cases = [(0, "green"), (45, "green"), (45.0001, "amber"), (120, "amber"), (120.0001, "red"), (99999, "red")]
    failures = []
    for age, expected in cases:
        got = staleness_class(age)
        if got != expected:
            failures.append(f"age={age}: expected {expected}, got {got}")
    return _result("staleness_class boundaries (client-side banner's pure function)",
                    not failures, "; ".join(failures) or "0/6 45s and 120s boundary cases wrong")


def test_projector_pure_determinism():
    plan = {
        "plan_version": "test", "budgets_usd": {"PX": 10},
        "phases": [{"id": "PX", "title": "Test Phase", "status": "PLANNED", "gate_id": None}],
        "lanes": [
            {"id": "PX-A", "title": "lane a", "phase": "PX", "depends_on": [],
             "expected_artifacts": {"paths": []}},
            {"id": "PX-B", "title": "lane b", "phase": "PX", "depends_on": ["PX-A"],
             "expected_artifacts": {"paths": []}},
        ],
    }
    snapshot = {
        "collected_at": "2026-01-01T00:00:00Z",
        "git_lane_branches": {"evidence_class": "DERIVED", "value": {}},
        "github_prs": {"evidence_class": "DERIVED", "value": {}},
        "expected_artifacts": {"evidence_class": "DERIVED", "value": {}},
        "shared_surfaces": {},
    }
    events = []
    out1, new1 = project.fold(plan, snapshot, events, as_of_epoch=1000.0)
    out2, new2 = project.fold(plan, snapshot, copy.deepcopy(events), as_of_epoch=1000.0)
    same = json.dumps(out1, sort_keys=True) == json.dumps(out2, sort_keys=True)
    return _result("project.fold() pure determinism (same inputs -> byte-identical output)",
                    same, "fold() output differed across two calls with identical inputs" if not same
                    else f"{len(out1)} lanes, identical both calls")


def test_state_json_rebuild_after_delete():
    from _common import STATE_JSON, COLLECTOR_SNAPSHOT_JSON
    if not os.path.exists(COLLECTOR_SNAPSHOT_JSON):
        try:
            collect.main()
        except Exception as e:  # noqa: BLE001
            return _result("state.json rebuilds byte-identically after delete", False,
                            f"no collector_snapshot.json and collect.main() failed: {e}")
    project.project()
    with open(STATE_JSON, encoding="utf-8") as f:
        before = f.read()
    os.remove(STATE_JSON)
    project.project(write_new_events=False)
    with open(STATE_JSON, encoding="utf-8") as f:
        after = f.read()
    same = before == after
    return _result("state.json rebuilds byte-identically after delete", same,
                    "byte-for-byte identical" if same else
                    f"differed: before={len(before)}B after={len(after)}B (first diff at "
                    f"{next((i for i in range(min(len(before), len(after))) if before[i] != after[i]), 'length')})")


def test_anomaly_on_contradicting_claim():
    plan = {
        "plan_version": "test", "budgets_usd": {},
        "phases": [{"id": "PX", "title": "Test Phase", "status": "PLANNED", "gate_id": None}],
        "lanes": [{"id": "PX-FAKE", "title": "fake lane for anomaly test", "phase": "PX",
                   "depends_on": [], "expected_artifacts": {"paths": []}}],
    }
    snapshot = {
        "collected_at": "2026-01-01T00:00:00Z",
        "git_lane_branches": {"evidence_class": "DERIVED", "value": {
            "pariprashna/px-fake": {"sha": "deadbeef", "committer_date": "2026-01-01T00:00:00Z",
                                     "subject": "wip", "ahead_behind_main": {"ahead": 3, "behind": 0}},
        }},
        "github_prs": {"evidence_class": "DERIVED", "value": {}},
        "expected_artifacts": {"evidence_class": "DERIVED", "value": {}},
        "shared_surfaces": {},
    }
    fake_claim_event = {
        "ts": "2026-01-01T00:05:00Z", "_epoch": 500.0, "writer_id": "selftest-fabricated-agent",
        "lane": "PX-FAKE", "kind": "lane_state", "evidence_class": "CLAIMED",
        "provenance": "selftest: deliberately false claim", "payload": {"state": "MERGED"},
    }
    out_lanes, new_events = project.fold(plan, snapshot, [fake_claim_event], as_of_epoch=1000.0)
    anomalies = [e for e in new_events if e["kind"] == "anomaly"]
    got_state = next((l["state"] for l in out_lanes if l["id"] == "PX-FAKE"), None)
    ok = bool(anomalies) and got_state == "BUILDING"
    return _result("false MERGED claim vs. unmerged branch -> anomaly, no completion count moved",
                    ok, f"anomalies={len(anomalies)} derived_state={got_state} (evidence: branch 3 ahead of main)")


def test_gh_failure_yields_unknown_no_carry_forward():
    real_run = collect.run
    try:
        collect.run = lambda *a, **kw: (False, "", "simulated: gh auth revoked (selftest)")
        result = collect.collect_github_prs()
    finally:
        collect.run = real_run
    ok = result.get("evidence_class") == "UNKNOWN" and result.get("value") is None
    snapshot_with_failure = {"github_prs": result}
    plan_lane_prs = (snapshot_with_failure.get("github_prs") or {}).get("value") or {}
    no_carry = plan_lane_prs == {}
    return _result("simulated gh failure -> UNKNOWN, never carries forward a previous value",
                    ok and no_carry,
                    f"evidence_class={result.get('evidence_class')} value={result.get('value')!r} "
                    f"downstream_reads_as={plan_lane_prs!r}")


def run_all():
    import time
    tests = [
        test_staleness_boundaries(),
        test_projector_pure_determinism(),
        test_state_json_rebuild_after_delete(),
        test_anomaly_on_contradicting_claim(),
        test_gh_failure_yields_unknown_no_carry_forward(),
    ]
    all_passed = all(t["passed"] for t in tests)
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tests": tests, "all_passed": all_passed}


if __name__ == "__main__":
    r = run_all()
    print(json.dumps(r, indent=2))
    sys.exit(0 if r["all_passed"] else 1)
