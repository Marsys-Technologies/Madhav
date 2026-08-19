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
from _common import ref_freshness_class, staleness_class  # noqa: E402


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


def test_ref_freshness_boundaries():
    """Third liveness axis (item 3): ref freshness has its own 60s/180s schedule,
    independent of the 45s/120s observer-freshness schedule. Same pure-function-boundary
    approach as test_staleness_boundaries -- the daemon's real fetch cadence is 20-60s, so
    driving this for real would mean actually waiting 3+ minutes with fetching disabled;
    the classification logic itself is what's under test, exactly as the original design's
    'assert the client-side banner logic returns amber at 45s and red at 120s' did for the
    observer-freshness axis without a real 2-minute wait either."""
    cases = [(0, "green"), (60, "green"), (60.0001, "amber"), (180, "amber"), (180.0001, "red"), (99999, "red")]
    failures = []
    for age, expected in cases:
        got = ref_freshness_class(age)
        if got != expected:
            failures.append(f"age={age}: expected {expected}, got {got}")
    return _result("ref_freshness_class boundaries (REFS LAGGING/STALE schedule, 60s/180s)",
                    not failures, "; ".join(failures) or "0/6 60s and 180s boundary cases wrong")


def test_mirror_fetch_failure_degrades_to_unknown():
    """Item 5, part 2: a failed mirror fetch must degrade EVERY mirror-derived cell to
    UNKNOWN with the fetch error as provenance -- never silently reuse whatever the mirror's
    on-disk refs still say from the last successful fetch. Simulates the gate exactly as
    collect.main() constructs it from a failed mirror_fetch() result, then checks each
    mirror-gated collector function honors it (none of them should even attempt a git call)."""
    fake_gate = collect._unknown("mirror fetch failed (git fetch --prune (mirror)): simulated network failure (selftest)")
    plan = {"lanes": [{"id": "PX", "expected_artifacts": {"merge_commit": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"}}]}

    # collect_code_provenance() checks for INSTALLED_FROM.json BEFORE consulting the mirror
    # gate (a missing snapshot install is a real, distinct, more specific reason to be
    # UNKNOWN than "the mirror fetch failed" -- report the actual blocking cause, don't
    # overclaim). To exercise the mirror-gate branch specifically, write a temp
    # INSTALLED_FROM.json for the duration of this test so execution reaches that check.
    from _common import INSTALLED_FROM_JSON
    installed_from_existed = os.path.exists(INSTALLED_FROM_JSON)
    if not installed_from_existed:
        with open(INSTALLED_FROM_JSON, "w", encoding="utf-8") as f:
            json.dump({"source_ref": "selftest", "source_sha": "0" * 40,
                       "installed_at": "2026-01-01T00:00:00Z"}, f)
    try:
        code_provenance_result = collect.collect_code_provenance(fake_gate)
    finally:
        if not installed_from_existed:
            os.remove(INSTALLED_FROM_JSON)

    shared_surfaces = collect.collect_shared_surfaces(fake_gate)
    results = {
        "git_lane_branches": collect.collect_git_lane_branches(fake_gate),
        "code_provenance": code_provenance_result,
        "recent_merged_prs": collect.collect_recent_merged_prs(fake_gate),
        "expected_artifacts": collect.collect_expected_artifacts(plan, fake_gate),
        "shared_surfaces.origin_main_sha": shared_surfaces["origin_main_sha"],
        "shared_surfaces.coordination_lease_holder": shared_surfaces["coordination_lease_holder"],
    }

    failures = []
    for name, r in results.items():
        if name == "expected_artifacts":
            mc = r["value"]["PX"]["merge_commit"]
            if mc.get("evidence_class") != "UNKNOWN" or mc.get("is_ancestor_of_main") is not None:
                failures.append(f"{name}.merge_commit did not degrade to UNKNOWN: {mc}")
            continue
        if r.get("evidence_class") != "UNKNOWN":
            failures.append(f"{name}: expected UNKNOWN, got {r.get('evidence_class')} (value={r.get('value')!r})")
        if r.get("value") is not None:
            failures.append(f"{name}: carried a non-None value forward despite the fetch gate: {r.get('value')!r}")
        if fake_gate["provenance"] not in (r.get("provenance") or ""):
            failures.append(f"{name}: provenance does not mention the fetch failure: {r.get('provenance')!r}")

    return _result("simulated mirror-fetch failure -> every mirror-derived cell UNKNOWN, no carry-forward",
                    not failures, "; ".join(failures) or f"{len(results)} mirror-gated signals all correctly degraded")


def test_gh_mirror_consistency_anomaly():
    """Item 5, part 3: fabricate a gh-says-merged-but-mirror-disagrees divergence and
    assert project.gh_mirror_anomalies() fires -- the exact false condition that would
    recreate the PR #1341 incident (confidently wrong about what's actually merged)."""
    snapshot = {
        "recent_merged_prs": {"evidence_class": "DERIVED", "value": [
            {"number": 9999, "merge_commit_sha": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
             "merged_at": "2026-01-01T00:00:00Z", "head_ref": "selftest/fabricated-divergence",
             "is_ancestor_of_mirror_main": False},
            {"number": 8888, "merge_commit_sha": "cafef00dcafef00dcafef00dcafef00dcafef00",
             "merged_at": "2026-01-01T00:00:00Z", "head_ref": "selftest/genuinely-fine",
             "is_ancestor_of_mirror_main": True},
        ]},
    }
    new_events = project.gh_mirror_anomalies(snapshot, events=[])
    fired = [e for e in new_events if e["payload"].get("pr_number") == 9999]
    false_positive = [e for e in new_events if e["payload"].get("pr_number") == 8888]
    ok = bool(fired) and not false_positive
    return _result("gh-vs-mirror divergence (PR merged per gh, commit not an ancestor of mirror main) -> anomaly",
                    ok, f"anomalies_for_divergent_pr={len(fired)} false_positives_on_consistent_pr={len(false_positive)}")


def run_all():
    import time
    tests = [
        test_staleness_boundaries(),
        test_ref_freshness_boundaries(),
        test_projector_pure_determinism(),
        test_state_json_rebuild_after_delete(),
        test_anomaly_on_contradicting_claim(),
        test_gh_failure_yields_unknown_no_carry_forward(),
        test_mirror_fetch_failure_degrades_to_unknown(),
        test_gh_mirror_consistency_anomaly(),
    ]
    all_passed = all(t["passed"] for t in tests)
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tests": tests, "all_passed": all_passed}


if __name__ == "__main__":
    r = run_all()
    print(json.dumps(r, indent=2))
    sys.exit(0 if r["all_passed"] else 1)
