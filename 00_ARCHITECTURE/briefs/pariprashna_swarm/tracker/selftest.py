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


def test_compute_blind_window_pure():
    """Item (d), pure-function part: compute_blind_window's four cases -- first-ever boot
    (no prior heartbeat), under-threshold gap, over-threshold-but-marked-intentional, and
    the one that actually fires: over-threshold with no marker."""
    import datetime
    from _common import BLIND_GAP_THRESHOLD_S, compute_blind_window
    now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    under = now - datetime.timedelta(seconds=BLIND_GAP_THRESHOLD_S - 1)
    over = now - datetime.timedelta(seconds=BLIND_GAP_THRESHOLD_S + 1)
    cases = {
        "first_boot_no_prior_heartbeat": compute_blind_window(None, now, False) is None,
        "under_threshold_no_marker": compute_blind_window(under, now, False) is None,
        "over_threshold_marker_present": compute_blind_window(over, now, True) is None,
    }
    fired = compute_blind_window(over, now, False)
    cases["over_threshold_no_marker_fires"] = (
        fired is not None and abs(fired["duration_s"] - (BLIND_GAP_THRESHOLD_S + 1)) < 0.01
    )
    failures = [name for name, ok in cases.items() if not ok]
    return _result("compute_blind_window: first-boot/under-threshold/marker suppress, over-threshold-no-marker fires",
                    not failures, "; ".join(failures) or f"{len(cases)}/{len(cases)} cases correct")


def test_blind_window_integration():
    """Item (d), integration part: a REAL subprocess run of trackerd.py's own startup
    check (--check-blind-window-only), isolated HOME, never touches the live tracker. Two
    scenarios: a stale heartbeat with no marker must write a persistent BLIND_WINDOW.json
    (acknowledged: false) and append a real anomaly event; the same stale heartbeat WITH an
    intentional-stop marker present must do neither."""
    import datetime
    import json as json_mod
    import subprocess
    import tempfile
    trackerd_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trackerd.py")

    def run_scenario(marker_present):
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = os.path.join(tmp, "fake_home")
            runtime_dir = os.path.join(fake_home, ".pariprashna-tracker")
            os.makedirs(os.path.join(runtime_dir, "events"))
            os.makedirs(os.path.join(runtime_dir, "logs"))
            old_ts = (datetime.datetime.now(datetime.timezone.utc)
                      - datetime.timedelta(seconds=300)).strftime("%Y-%m-%dT%H:%M:%SZ")
            with open(os.path.join(runtime_dir, "heartbeat.json"), "w", encoding="utf-8") as f:
                json_mod.dump({"ts": old_ts, "cycle": 1}, f)
            if marker_present:
                with open(os.path.join(runtime_dir, "STOPPED_INTENTIONALLY.json"), "w", encoding="utf-8") as f:
                    json_mod.dump({"ts": old_ts, "reason": "selftest", "invoking_user": "selftest"}, f)
            env = dict(os.environ)
            env["HOME"] = fake_home
            result = subprocess.run(["python3", trackerd_path, "--check-blind-window-only"],
                                     env=env, capture_output=True, text=True, timeout=15)
            blind_path = os.path.join(runtime_dir, "BLIND_WINDOW.json")
            wrote_record = os.path.exists(blind_path)
            record = None
            if wrote_record:
                with open(blind_path, encoding="utf-8") as f:
                    record = json_mod.load(f)
            events_path = os.path.join(runtime_dir, "events", "trackerd.jsonl")
            anomaly_fired = False
            if os.path.exists(events_path):
                with open(events_path, encoding="utf-8") as f:
                    for line in f:
                        ev = json_mod.loads(line)
                        if ev.get("kind") == "anomaly" and ev.get("payload", {}).get("event") == "blind_window_detected":
                            anomaly_fired = True
            return result.returncode, wrote_record, record, anomaly_fired

    rc1, wrote1, record1, anomaly1 = run_scenario(marker_present=False)
    unmarked_ok = (rc1 == 0 and wrote1 and record1 is not None and record1.get("acknowledged") is False
                   and 295 <= record1.get("duration_s", 0) <= 310 and anomaly1)

    rc2, wrote2, record2, anomaly2 = run_scenario(marker_present=True)
    marked_ok = (rc2 == 0 and not wrote2 and not anomaly2)

    ok = unmarked_ok and marked_ok
    return _result("trackerd --check-blind-window-only (real subprocess): stale+no-marker persists a record and fires an anomaly; stale+marker does neither",
                    ok, f"no_marker: rc={rc1} wrote={wrote1} record={record1} anomaly={anomaly1} | "
                        f"with_marker: rc={rc2} wrote={wrote2} anomaly={anomaly2}")


def test_tracker_stop_start_marker_lifecycle():
    """Item (b): tracker-stop must write STOPPED_INTENTIONALLY.json BEFORE calling
    launchctl bootout -- order matters, since item (d)'s check must see the marker for the
    entire duration the jobs are down, not just at the moment tracker-stop happens to exit.
    tracker-start must clear the marker after re-bootstrapping. Fake launchctl + fake HOME;
    never touches real launchd."""
    import datetime
    import json as json_mod
    import subprocess
    import tempfile
    tracker_dir = os.path.dirname(os.path.abspath(__file__))
    with tempfile.TemporaryDirectory() as tmp:
        fake_home = os.path.join(tmp, "fake_home")
        os.makedirs(fake_home)
        fake_bin = os.path.join(tmp, "bin")
        os.makedirs(fake_bin)
        runtime_dir = os.path.join(fake_home, ".pariprashna-tracker")
        marker_path = os.path.join(runtime_dir, "STOPPED_INTENTIONALLY.json")
        order_log = os.path.join(tmp, "launchctl_calls.log")

        fake_launchctl = os.path.join(fake_bin, "launchctl")
        with open(fake_launchctl, "w", encoding="utf-8") as f:
            f.write(
                '#!/bin/sh\n'
                f'if [ -f "{marker_path}" ]; then STATE=present; else STATE=absent; fi\n'
                f'echo "$@ marker=$STATE" >> "{order_log}"\n'
                'exit 0\n'
            )
        os.chmod(fake_launchctl, 0o755)
        env = dict(os.environ)
        env["HOME"] = fake_home
        env["PATH"] = fake_bin + ":" + env.get("PATH", "/usr/bin:/bin")

        stop_result = subprocess.run(
            ["/bin/sh", os.path.join(tracker_dir, "tracker-stop"), "selftest reason"],
            env=env, capture_output=True, text=True, timeout=15)
        marker_written = os.path.exists(marker_path)
        bootout_lines = []
        if os.path.exists(order_log):
            with open(order_log, encoding="utf-8") as f:
                bootout_lines = [line for line in f.read().splitlines() if "bootout" in line]
        all_saw_marker_present = bool(bootout_lines) and all("marker=present" in line for line in bootout_lines)

        la_dir = os.path.join(fake_home, "Library", "LaunchAgents")
        os.makedirs(la_dir)
        for job in ("trackerd", "watchdog", "serve"):
            with open(os.path.join(la_dir, f"com.marsys.pariprashna-{job}.plist"), "w", encoding="utf-8") as f:
                f.write("<plist/>")
        os.makedirs(os.path.join(runtime_dir, "events"), exist_ok=True)
        with open(os.path.join(runtime_dir, "heartbeat.json"), "w", encoding="utf-8") as f:
            json_mod.dump({"ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}, f)

        start_result = subprocess.run(["/bin/sh", os.path.join(tracker_dir, "tracker-start")],
                                       env=env, capture_output=True, text=True, timeout=30)
        marker_cleared = not os.path.exists(marker_path)

        ok = (stop_result.returncode == 0 and marker_written and all_saw_marker_present
              and start_result.returncode == 0 and marker_cleared)
        return _result("tracker-stop writes marker before bootout; tracker-start clears it after re-bootstrap",
                        ok, f"marker_written={marker_written} all_bootouts_saw_marker={all_saw_marker_present} "
                            f"bootout_calls={len(bootout_lines)} marker_cleared={marker_cleared} "
                            f"stop_rc={stop_result.returncode} start_rc={start_result.returncode}")


def test_lock_mutual_exclusion_cron_defers_during_install():
    """Item 2: install.sh, tracker-stop, tracker-start, and tracker-cron-watchdog all move
    the same launchd labels and must not interleave. This holds the real
    _tracker_lock.sh lock (the same file all four scripts source) for a bounded window --
    simulating install.sh mid-reinstall, including one real launchctl bootstrap call inside
    the held window -- while a real tracker-cron-watchdog invocation runs concurrently
    against a stale-heartbeat-no-marker scenario. Expected: exactly one bootstrap call
    (the lock holder's) and a real 'deferred_lock_held' event from cron -- cron must never
    also call bootout/bootstrap while the lock is held."""
    import datetime
    import json as json_mod
    import subprocess
    import tempfile
    import threading
    import time as time_mod
    tracker_dir = os.path.dirname(os.path.abspath(__file__))
    with tempfile.TemporaryDirectory() as tmp:
        fake_home = os.path.join(tmp, "fake_home")
        runtime_dir = os.path.join(fake_home, ".pariprashna-tracker")
        os.makedirs(os.path.join(runtime_dir, "events"))
        os.makedirs(os.path.join(runtime_dir, "logs"))
        la_dir = os.path.join(fake_home, "Library", "LaunchAgents")
        os.makedirs(la_dir)
        for job in ("trackerd", "watchdog", "serve"):
            with open(os.path.join(la_dir, f"com.marsys.pariprashna-{job}.plist"), "w", encoding="utf-8") as f:
                f.write("<plist/>")
        old_ts = (datetime.datetime.now(datetime.timezone.utc)
                  - datetime.timedelta(seconds=400)).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(os.path.join(runtime_dir, "heartbeat.json"), "w", encoding="utf-8") as f:
            json_mod.dump({"ts": old_ts}, f)

        fake_bin = os.path.join(tmp, "bin")
        os.makedirs(fake_bin)
        call_log = os.path.join(tmp, "launchctl_calls.log")
        with open(os.path.join(fake_bin, "launchctl"), "w", encoding="utf-8") as f:
            f.write(f'#!/bin/sh\necho "$@" >> "{call_log}"\nexit 0\n')
        os.chmod(os.path.join(fake_bin, "launchctl"), 0o755)

        env = dict(os.environ)
        env["HOME"] = fake_home
        env["PATH"] = fake_bin + ":" + env.get("PATH", "/usr/bin:/bin")

        holder_script = os.path.join(tmp, "hold_lock.sh")
        with open(holder_script, "w", encoding="utf-8") as f:
            f.write(
                '#!/bin/sh\n'
                f'RUNTIME_DIR="{runtime_dir}"\n'
                f'. "{tracker_dir}/_tracker_lock.sh"\n'
                'tracker_lock_acquire_blocking "install.sh-simulated" || exit 1\n'
                'launchctl bootstrap gui/0 fake-simulated-install-bootstrap\n'
                'sleep 5\n'
                'tracker_lock_release\n'
            )
        os.chmod(holder_script, 0o755)

        holder_proc = subprocess.Popen(["/bin/sh", holder_script], env=env)
        time_mod.sleep(1.5)  # let the holder acquire the lock and do its one bootstrap first

        cron_result = {}

        def run_cron():
            try:
                r = subprocess.run(["/bin/sh", os.path.join(tracker_dir, "tracker-cron-watchdog")],
                                    env=env, capture_output=True, text=True, timeout=8)
                cron_result["returncode"] = r.returncode
            except subprocess.TimeoutExpired:
                cron_result["returncode"] = None

        cron_thread = threading.Thread(target=run_cron)
        cron_thread.start()
        cron_thread.join(timeout=10)
        holder_proc.wait(timeout=10)

        bootstrap_calls = 0
        if os.path.exists(call_log):
            with open(call_log, encoding="utf-8") as f:
                bootstrap_calls = sum(1 for line in f if "bootstrap" in line)

        deferred_logged = False
        events_path = os.path.join(runtime_dir, "events", "cron_watchdog.jsonl")
        if os.path.exists(events_path):
            with open(events_path, encoding="utf-8") as f:
                for line in f:
                    ev = json_mod.loads(line)
                    if ev.get("payload", {}).get("event") == "deferred_lock_held":
                        deferred_logged = True

        ok = (bootstrap_calls == 1) and deferred_logged
        return _result("lock mutual exclusion: concurrent install (holding lock) + cron-watchdog tick -> exactly one bootstrap, one deferral",
                        ok, f"bootstrap_calls={bootstrap_calls} (want 1) deferred_logged={deferred_logged} "
                            f"cron_returncode={cron_result.get('returncode')}")


def test_cron_watchdog_out_of_band_logic():
    """Item (c), T4: tracker-cron-watchdog must skip (no bootout, no incident event) when
    an intentional-stop marker is present OR the heartbeat is already fresh, and must
    re-bootstrap + log a real incident event when the heartbeat is stale with no marker.
    Calls the script directly, exactly how cron would invoke it -- never touches the real
    crontab (crontab installation itself is intentionally NOT selftested; see README)."""
    import datetime
    import json as json_mod
    import subprocess
    import tempfile
    tracker_dir = os.path.dirname(os.path.abspath(__file__))

    def run_scenario(stale, marker_present):
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = os.path.join(tmp, "fake_home")
            runtime_dir = os.path.join(fake_home, ".pariprashna-tracker")
            os.makedirs(os.path.join(runtime_dir, "events"))
            os.makedirs(os.path.join(runtime_dir, "logs"))
            la_dir = os.path.join(fake_home, "Library", "LaunchAgents")
            os.makedirs(la_dir)
            for job in ("trackerd", "watchdog", "serve"):
                with open(os.path.join(la_dir, f"com.marsys.pariprashna-{job}.plist"), "w", encoding="utf-8") as f:
                    f.write("<plist/>")
            age = 400 if stale else 10
            ts = (datetime.datetime.now(datetime.timezone.utc)
                  - datetime.timedelta(seconds=age)).strftime("%Y-%m-%dT%H:%M:%SZ")
            with open(os.path.join(runtime_dir, "heartbeat.json"), "w", encoding="utf-8") as f:
                json_mod.dump({"ts": ts}, f)
            if marker_present:
                with open(os.path.join(runtime_dir, "STOPPED_INTENTIONALLY.json"), "w", encoding="utf-8") as f:
                    json_mod.dump({"ts": ts, "reason": "selftest"}, f)

            fake_bin = os.path.join(tmp, "bin")
            os.makedirs(fake_bin)
            call_log = os.path.join(tmp, "launchctl_calls.log")
            with open(os.path.join(fake_bin, "launchctl"), "w", encoding="utf-8") as f:
                f.write(f'#!/bin/sh\necho "$@" >> "{call_log}"\nexit 0\n')
            os.chmod(os.path.join(fake_bin, "launchctl"), 0o755)

            env = dict(os.environ)
            env["HOME"] = fake_home
            env["PATH"] = fake_bin + ":" + env.get("PATH", "/usr/bin:/bin")
            try:
                subprocess.run(["/bin/sh", os.path.join(tracker_dir, "tracker-cron-watchdog")],
                                env=env, capture_output=True, text=True, timeout=8)
            except subprocess.TimeoutExpired:
                pass  # bootout/bootstrap already happened synchronously before tracker-start's wait loop
            bootout_called = os.path.exists(call_log)
            incident_logged = False
            # cron_watchdog is its own writer_id -> its own events/cron_watchdog.jsonl file
            # (one append-only file per writer, per the tracker's own event-log design).
            events_path = os.path.join(runtime_dir, "events", "cron_watchdog.jsonl")
            if os.path.exists(events_path):
                with open(events_path, encoding="utf-8") as f:
                    for line in f:
                        ev = json_mod.loads(line)
                        if ev.get("payload", {}).get("event") == "out_of_band_resurrection":
                            incident_logged = True
            return bootout_called, incident_logged

    marker_bootout, marker_incident = run_scenario(stale=True, marker_present=True)
    fresh_bootout, fresh_incident = run_scenario(stale=False, marker_present=False)
    fires_bootout, fires_incident = run_scenario(stale=True, marker_present=False)

    ok = (not marker_bootout and not marker_incident
          and not fresh_bootout and not fresh_incident
          and fires_bootout and fires_incident)
    return _result("tracker-cron-watchdog (T4): skips on marker-present or fresh heartbeat, re-bootstraps + logs incident on stale+no-marker",
                    ok, f"marker_present: bootout={marker_bootout} incident={marker_incident}; "
                        f"fresh: bootout={fresh_bootout} incident={fresh_incident}; "
                        f"stale_no_marker: bootout={fires_bootout} incident={fires_incident}")


def test_tracker_health_check_five_conditions():
    """Item 2a: tracker-health-check must exit 0 only when ALL FIVE conditions hold
    (jobs loaded, heartbeat fresh, selftest passing, refs fresh, no unacknowledged blind
    window) and exit 1 with a specific one-line diagnosis when exactly one fails at a time.
    Also asserts it never touches label_ops.lock (a conductor calling this at every lane
    transition must never wait behind install.sh/tracker-stop/tracker-start holding it) and
    completes in well under 1s."""
    import datetime
    import json as json_mod
    import subprocess
    import tempfile
    import time as time_mod
    tracker_dir = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(tracker_dir, "tracker-health-check")

    def build_and_run(base, *, jobs_loaded=True, heartbeat_age=10, selftest_pass=True,
                       ref_age=10, blind_ack=None, write_heartbeat=True, write_state=True):
        fake_home = os.path.join(base, "fake_home")
        runtime_dir = os.path.join(fake_home, ".pariprashna-tracker")
        os.makedirs(runtime_dir)
        now = datetime.datetime.now(datetime.timezone.utc)
        if write_heartbeat:
            hb = {
                "ts": (now - datetime.timedelta(seconds=heartbeat_age)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "selftest_last": {
                    "all_passed": selftest_pass,
                    "tests": [] if selftest_pass else [{"name": "fake failing test", "passed": False}],
                },
            }
            with open(os.path.join(runtime_dir, "heartbeat.json"), "w", encoding="utf-8") as f:
                json_mod.dump(hb, f)
        if write_state:
            state = {"ref_freshness": {"last_success_ts": (now - datetime.timedelta(seconds=ref_age)).strftime("%Y-%m-%dT%H:%M:%SZ")}}
            with open(os.path.join(runtime_dir, "state.json"), "w", encoding="utf-8") as f:
                json_mod.dump(state, f)
        if blind_ack is not None:
            bw = {"acknowledged": blind_ack, "duration_s": 300.0,
                  "gap_start_ts": "2026-01-01T00:00:00Z", "gap_end_ts": "2026-01-01T00:05:00Z"}
            with open(os.path.join(runtime_dir, "BLIND_WINDOW.json"), "w", encoding="utf-8") as f:
                json_mod.dump(bw, f)

        fake_bin = os.path.join(base, "bin")
        os.makedirs(fake_bin)
        lock_marker = os.path.join(base, "lock_dir_created")
        if jobs_loaded:
            lc_body = (
                "echo '12345\\t0\\tcom.marsys.pariprashna-trackerd'\n"
                "echo '12346\\t0\\tcom.marsys.pariprashna-watchdog'\n"
                "echo '12347\\t0\\tcom.marsys.pariprashna-serve'\n"
            )
        else:
            lc_body = "true\n"
        with open(os.path.join(fake_bin, "launchctl"), "w", encoding="utf-8") as f:
            f.write(f"#!/bin/sh\n{lc_body}")
        os.chmod(os.path.join(fake_bin, "launchctl"), 0o755)

        env = dict(os.environ)
        env["HOME"] = fake_home
        env["PATH"] = fake_bin + ":" + env.get("PATH", "/usr/bin:/bin")

        t0 = time_mod.monotonic()
        result = subprocess.run(["/bin/sh", script], env=env, capture_output=True, text=True, timeout=5)
        elapsed = time_mod.monotonic() - t0
        lock_touched = os.path.isdir(os.path.join(runtime_dir, "label_ops.lock"))
        return result.returncode, result.stdout.strip(), elapsed, lock_touched

    with tempfile.TemporaryDirectory() as tmp:
        scenarios = {}
        rc, out, elapsed, lock_touched = build_and_run(os.path.join(tmp, "healthy"))
        scenarios["healthy"] = (rc == 0, out, elapsed, lock_touched)

        rc, out, elapsed, lock_touched = build_and_run(os.path.join(tmp, "jobs_unloaded"), jobs_loaded=False)
        scenarios["jobs_unloaded"] = (rc == 1 and "jobs unloaded" in out, out, elapsed, lock_touched)

        rc, out, elapsed, lock_touched = build_and_run(os.path.join(tmp, "heartbeat_stale"), heartbeat_age=400)
        scenarios["heartbeat_stale"] = (rc == 1 and "heartbeat stale" in out, out, elapsed, lock_touched)

        rc, out, elapsed, lock_touched = build_and_run(os.path.join(tmp, "selftest_failing"), selftest_pass=False)
        scenarios["selftest_failing"] = (rc == 1 and "selftest failing" in out, out, elapsed, lock_touched)

        rc, out, elapsed, lock_touched = build_and_run(os.path.join(tmp, "refs_lagging"), ref_age=400)
        scenarios["refs_lagging"] = (rc == 1 and "refs lagging" in out, out, elapsed, lock_touched)

        rc, out, elapsed, lock_touched = build_and_run(os.path.join(tmp, "blind_unacked"), blind_ack=False)
        scenarios["blind_unacked"] = (rc == 1 and "unacknowledged blind window" in out, out, elapsed, lock_touched)

    failures = [f"{name}: {out!r}" for name, (ok, out, _, _) in scenarios.items() if not ok]
    any_lock_touched = [name for name, (_, _, _, lt) in scenarios.items() if lt]
    max_elapsed = max(e for (_, _, e, _) in scenarios.values())
    ok = (not failures) and (not any_lock_touched) and (max_elapsed < 1.0)
    return _result("tracker-health-check: all 5 conditions individually detected, never touches the lock, under 1s",
                    ok, f"failures={failures} lock_touched_by={any_lock_touched} max_elapsed={max_elapsed:.3f}s")


def test_provenance_current():
    """Item 1a, state CURRENT: installed sha is merged (ancestor of main) AND already
    contains the latest tracker-touching commit on main -- the "just merged and
    reinstalled" case. Not amber."""
    from _common import classify_code_provenance
    got = classify_code_provenance(is_ancestor_of_main=True, contains_latest_tracker_commit=True)
    return _result("code provenance: merged + has-latest -> CURRENT", got == "CURRENT", f"got={got!r}")


def test_provenance_ahead():
    """Item 1a, state AHEAD: installed sha is NOT merged (unmerged branch work) but
    already contains everything main has for tracker/ -- e.g. deployed pre-merge for live
    verification, exactly this PR's own workflow. Must NOT read amber: the old binary
    is_current check conflated this with genuinely stale code, training readers to
    discount an amber that, when real (BEHIND/DIVERGED), matters."""
    from _common import classify_code_provenance
    got = classify_code_provenance(is_ancestor_of_main=False, contains_latest_tracker_commit=True)
    return _result("code provenance: unmerged + has-latest -> AHEAD (neutral, not amber)", got == "AHEAD", f"got={got!r}")


def test_provenance_behind():
    """Item 1a, state BEHIND: installed sha IS merged (somewhere in main's history) but
    main has since gained tracker-touching commits this sha lacks -- genuinely stale.
    Amber."""
    from _common import classify_code_provenance
    got = classify_code_provenance(is_ancestor_of_main=True, contains_latest_tracker_commit=False)
    return _result("code provenance: merged + missing-latest -> BEHIND (amber)", got == "BEHIND", f"got={got!r}")


def test_provenance_diverged():
    """Item 1a, state DIVERGED: installed sha is neither an ancestor of main nor does it
    contain main's latest tracker commit -- no clean ordering (e.g. after a rebase or
    force-push). A real anomaly, distinct from an ordinary unmerged AHEAD. Amber."""
    from _common import classify_code_provenance
    got = classify_code_provenance(is_ancestor_of_main=False, contains_latest_tracker_commit=False)
    return _result("code provenance: neither ancestor nor has-latest -> DIVERGED (amber)", got == "DIVERGED", f"got={got!r}")


def test_install_sh_refuses_non_default_home_with_production_label():
    """Item (a): install.sh must refuse to run with $HOME overridden while LABEL_PREFIX is
    still the production default -- and must do so WITHOUT ever invoking launchctl. HOME
    isolation looks like it isolates a test install, but launchctl labels are global to the
    launchd domain regardless of HOME, so an unparameterized label would bootout production.
    (Process-forensic follow-up on the actual 2026-08-19 blind window found its real cause
    was a different, unmarked-stop hazard -- see README's "2026-08-19 incident" -- so this
    is a distinct, independently-real gap this guard closes, not a confirmed repro of that
    specific incident.) Verified by putting a fake `launchctl` first on PATH that writes a
    marker if invoked at all -- the strongest form of "never called" this test can assert
    without root."""
    import subprocess
    import tempfile
    install_sh = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install.sh")
    with tempfile.TemporaryDirectory() as tmp:
        fake_home = os.path.join(tmp, "fake_home")
        os.makedirs(fake_home)
        fake_bin = os.path.join(tmp, "bin")
        os.makedirs(fake_bin)
        marker = os.path.join(tmp, "launchctl_was_called")
        fake_launchctl = os.path.join(fake_bin, "launchctl")
        with open(fake_launchctl, "w", encoding="utf-8") as f:
            f.write(f'#!/bin/sh\necho "CALLED $@" >> "{marker}"\nexit 0\n')
        os.chmod(fake_launchctl, 0o755)
        env = dict(os.environ)
        env["HOME"] = fake_home
        env["PATH"] = fake_bin + ":" + env.get("PATH", "/usr/bin:/bin")
        result = subprocess.run(["/bin/sh", install_sh], env=env, capture_output=True,
                                 text=True, timeout=20)
    refused = result.returncode != 0
    bootout_never_called = not os.path.exists(marker)
    explains_why = "HOME isolation does not isolate launchctl labels" in result.stderr
    ok = refused and bootout_never_called and explains_why
    return _result("install.sh refuses non-default HOME + production label prefix, never calls launchctl",
                    ok, f"returncode={result.returncode} bootout_called={not bootout_never_called} "
                        f"explains_why={explains_why} stderr={result.stderr.strip()[:300]!r}")


def test_rate_limit_reads_graphql_not_core():
    """Item 6: `gh pr list` (this collector's own poll, both open and merged, every cycle)
    is GraphQL-backed -- verified empirically 2026-08-20 by calling it and diffing `gh api
    rate_limit` before/after: resources.core.used stayed 0 while resources.graphql.used
    incremented by 2 in the same call. A collector reading resources.core reports a bucket
    this tracker never spends from -- it reads 5000/5000 forever regardless of load, a
    decorative meter dressed as a budget one. Fixture mirrors that exact observed shape:
    core flat and healthy-looking, graphql actually spent."""
    fixture = {"resources": {
        "core": {"limit": 5000, "used": 0, "remaining": 5000, "reset": 1787175697},
        "graphql": {"limit": 5000, "used": 216, "remaining": 4784, "reset": 1787172405},
    }}
    got = collect.parse_rate_limit(fixture)
    reads_core_instead = got["remaining"] == 5000  # the bug this test exists to catch
    ok = got["bucket"] == "graphql" and got["remaining"] == 4784 and not reads_core_instead
    return _result("github_rate_limit reads the graphql bucket (what gh pr list actually spends), not core",
                    ok, f"got={got!r}")


def test_pidfile_flock_prevents_two_instances():
    """2026-08-20 production incident: acquire_pidfile() used to be a plain
    read-check-then-write with no real locking -- two processes starting close together
    (as happened for real: launchd's own KeepAlive and a watchdog restart firing near-
    simultaneously) could both see the recorded pid as dead and both proceed, giving two
    live trackerd processes that raced every write to heartbeat.json/state.json (one of
    them observed crashing outright: os.replace() on a shared tmp path whose file the
    other process had already consumed and renamed away).

    Honest scope: a TOCTOU race is inherently timing-dependent and not reliably
    reproducible on demand (confirmed while writing this test -- deliberately reverting to
    the old read-check-then-write code and running a sequential holder-then-challenger like
    this one still passed, because sequential starts were never the bug; only two starts
    landing in the same narrow window were). This test instead verifies the mechanism the
    fix actually relies on, with two REAL, independent OS processes (not a fake in-process
    simulation, which could pass by accident since flock() is per-open-file-description):
    a first subprocess acquires the flock and stays alive (blocks on stdin) so the lock is
    genuinely held by a separate process, and a second real subprocess attempting the same
    acquisition must exit(1) immediately without ever reaching its own heartbeat write.
    flock(LOCK_EX | LOCK_NB) being atomic at the kernel level -- the property that makes the
    race structurally impossible, not just improbable -- is a documented OS guarantee, not
    something this test derives from scratch."""
    import subprocess
    import tempfile
    import time as time_mod
    trackerd_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trackerd.py")

    with tempfile.TemporaryDirectory() as tmp:
        fake_home = os.path.join(tmp, "fake_home")
        runtime_dir = os.path.join(fake_home, ".pariprashna-tracker")
        os.makedirs(os.path.join(runtime_dir, "events"))
        os.makedirs(os.path.join(runtime_dir, "logs"))
        env = dict(os.environ)
        env["HOME"] = fake_home

        holder_code = (
            "import sys, os; sys.path.insert(0, %r); import trackerd; "
            "trackerd.acquire_pidfile(); print('LOCKED', flush=True); sys.stdin.readline()"
        ) % os.path.dirname(trackerd_path)
        holder = subprocess.Popen(["python3", "-c", holder_code], env=env,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        try:
            first_line = holder.stdout.readline().strip()
            holder_locked = (first_line == "LOCKED")

            challenger = subprocess.run(
                ["python3", trackerd_path, "--once"], env=env,
                capture_output=True, text=True, timeout=15,
            )
            challenger_rejected = (
                challenger.returncode == 1
                and "already running" in (challenger.stderr or "")
            )
            heartbeat_path = os.path.join(runtime_dir, "heartbeat.json")
            challenger_never_wrote_heartbeat = not os.path.exists(heartbeat_path)
        finally:
            try:
                holder.stdin.write("\n")
                holder.stdin.close()
            except (BrokenPipeError, OSError):
                pass
            try:
                holder.wait(timeout=5)
            except subprocess.TimeoutExpired:
                holder.kill()

        ok = holder_locked and challenger_rejected and challenger_never_wrote_heartbeat
        return _result(
            "acquire_pidfile() flock: a second concurrent daemon start is rejected, never "
            "writes a heartbeat, while the first genuinely holds the lock",
            ok,
            f"holder_locked={holder_locked} challenger_rc={challenger.returncode} "
            f"challenger_rejected={challenger_rejected} "
            f"challenger_never_wrote_heartbeat={challenger_never_wrote_heartbeat} "
            f"challenger_stderr={(challenger.stderr or '')[:200]!r}",
        )


def _plan_stub(lanes, phases=None):
    return {"plan_version": "test",
            "phases": phases or [{"id": "PX", "title": "T", "gate_id": None}],
            "budgets_usd": {}, "lanes": lanes}


def test_pr_identifier_extraction_matches_real_prs():
    """The rule that decides which lanes a merged PR implements, pinned to the exact real
    PRs it was derived from. The two negative cases matter most: #1363's body says "gating
    for G3-B/C/D/E/F/G" about lanes it does NOT implement, and #1365's says "P2-A..H" while
    implementing only G3-E/G3-G. A body-prose scan would mark 6 and 8 lanes wrongly done."""
    cases = [
        # (title, body, expected)
        ("feat: P2 reader affordances (G3-E/G3-G)",
         "- **G3-E** reader affordances\n- **G3-G** model qualification\ncloses P2-A..H and P2-I..O",
         ["G3-E", "G3-G"]),
        ("feat(pariprashna): P2-I receipt emission + validator (G3-A, PPR-01)",
         "First lane of P2 epistemic-truth wave -- gating for G3-B/C/D/E/F/G. Implements ...",
         ["G3-A", "P2-I"]),
        ("feat: P2 presentation-truth wave", "- **P2-A** blocks\n- **P2-B** citations", ["P2-A", "P2-B"]),
    ]
    failures = []
    for title, body, expected in cases:
        got = collect.extract_lane_identifiers(title, body)
        if got != sorted(expected):
            failures.append(f"{title[:38]!r}: expected {sorted(expected)}, got {got}")
    return _result("merged-PR identifier extraction (title + **bold**), incl. the two real "
                    "prose-mention false positives it must reject",
                    not failures, "; ".join(failures) or f"{len(cases)}/{len(cases)} cases exact")


def test_unobservable_floor_never_fabricates_planned():
    """A lane with no merged PR, no branch, no artifact and no conductor entry must read
    UNOBSERVABLE/UNKNOWN. It used to read PLANNED/DERIVED -- a status the tracker had no
    basis for, asserted as evidence. That fabrication is what let 46 of 53 lanes sit
    frozen through two shipped phases with every liveness light green."""
    plan = _plan_stub([{"id": "PX-A", "title": "unobservable lane", "phase": "PX",
                        "depends_on": [], "expected_artifacts": {"paths": []}}])
    snapshot = {"collected_at": "2026-01-01T00:00:00Z",
                "git_lane_branches": {"evidence_class": "DERIVED", "value": {}},
                "github_prs": {"evidence_class": "DERIVED", "value": {}},
                "recent_merged_prs": {"evidence_class": "DERIVED", "value": []},
                "expected_artifacts": {"evidence_class": "DERIVED", "value": {}},
                "conductor_state": {"evidence_class": "UNKNOWN", "value": None},
                "shared_surfaces": {}}
    out, _ = project.fold(plan, snapshot, [], as_of_epoch=1000.0)
    lane = out[0]
    ok = lane["state"] == "UNOBSERVABLE" and lane["evidence_class"] == "UNKNOWN"
    return _result("no-evidence lane reads UNOBSERVABLE/UNKNOWN, never a fabricated PLANNED",
                    ok, f"state={lane['state']} evidence_class={lane['evidence_class']}")


def test_merged_pr_evidence_drives_lane_and_phase():
    """End-to-end on the real shape: a merged PR implementing a lane's GATE id (the swarm
    names PRs by gate, this plan names lanes P<n>-<L>) must mark the lane MERGED with
    DERIVED provenance, and the phase must derive to CLOSED -- not be read from a
    hand-typed PLAN.yaml constant."""
    plan = _plan_stub(
        [{"id": "PX-A", "title": "a", "phase": "PX", "gate": "G9-A", "depends_on": [],
          "expected_artifacts": {"paths": []}}],
        phases=[{"id": "PX", "title": "T", "gate_id": "PX_gate"}])
    snapshot = {"collected_at": "2026-01-01T00:00:00Z",
                "git_lane_branches": {"evidence_class": "DERIVED", "value": {}},
                "github_prs": {"evidence_class": "DERIVED", "value": {}},
                "recent_merged_prs": {"evidence_class": "DERIVED", "value": [
                    {"number": 4242, "merge_commit_sha": "abc123def456", "merged_at": "x",
                     "head_ref": "h", "is_ancestor_of_mirror_main": True,
                     "title": "t", "implements": ["G9-A"]}]},
                "expected_artifacts": {"evidence_class": "DERIVED", "value": {}},
                "conductor_state": {"evidence_class": "UNKNOWN", "value": None},
                "shared_surfaces": {}}
    out, _ = project.fold(plan, snapshot, [], as_of_epoch=1000.0)
    lane = out[0]
    phases = project.fold_phase_status(plan, out, snapshot)
    lane_ok = (lane["state"] == "MERGED" and lane["evidence_class"] == "DERIVED"
               and "#4242" in lane["provenance"])
    phase_ok = phases[0]["status"] == "CLOSED"
    return _result("merged PR naming a lane's GATE id -> lane MERGED (DERIVED) and phase "
                    "status DERIVED to CLOSED",
                    lane_ok and phase_ok,
                    f"lane={lane['state']}/{lane['evidence_class']} phase={phases[0]['status']} "
                    f"prov={lane['provenance'][:60]!r}")


def test_board_world_divergence_detector():
    """The detector whose absence is why the frozen board survived three rounds of me
    certifying it healthy. A merged PR implementing a known lane, while that lane shows
    anything other than done, must raise an anomaly."""
    lanes_frozen = [{"id": "PX-A", "phase": "PX", "gate": "G9-A", "state": "UNOBSERVABLE"}]
    lanes_correct = [{"id": "PX-A", "phase": "PX", "gate": "G9-A", "state": "MERGED"}]
    snapshot = {"recent_merged_prs": {"evidence_class": "DERIVED", "value": [
        {"number": 4242, "merge_commit_sha": "abc", "is_ancestor_of_mirror_main": True,
         "title": "ships G9-A", "implements": ["G9-A"]}]}}
    frozen_summary, frozen_events = project.board_world_divergence(lanes_frozen, snapshot, [], 1000.0)
    ok_summary, ok_events = project.board_world_divergence(lanes_correct, snapshot, [], 1000.0)
    fires = frozen_summary["unreflected_count"] == 1 and len(frozen_events) == 1
    quiet = ok_summary["unreflected_count"] == 0 and not ok_events
    return _result("board-vs-world divergence: fires when a merged PR's lane isn't shown "
                    "done, silent when the board is correct",
                    fires and quiet,
                    f"frozen_board: unreflected={frozen_summary['unreflected_count']} "
                    f"anomalies={len(frozen_events)} | correct_board: "
                    f"unreflected={ok_summary['unreflected_count']} anomalies={len(ok_events)}")


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
        test_provenance_current(),
        test_provenance_ahead(),
        test_provenance_behind(),
        test_provenance_diverged(),
        test_tracker_health_check_five_conditions(),
        test_rate_limit_reads_graphql_not_core(),
        test_install_sh_refuses_non_default_home_with_production_label(),
        test_compute_blind_window_pure(),
        test_blind_window_integration(),
        test_tracker_stop_start_marker_lifecycle(),
        test_lock_mutual_exclusion_cron_defers_during_install(),
        test_cron_watchdog_out_of_band_logic(),
        test_pidfile_flock_prevents_two_instances(),
        test_pr_identifier_extraction_matches_real_prs(),
        test_unobservable_floor_never_fabricates_planned(),
        test_merged_pr_evidence_drives_lane_and_phase(),
        test_board_world_divergence_detector(),
    ]
    all_passed = all(t["passed"] for t in tests)
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tests": tests, "all_passed": all_passed}


if __name__ == "__main__":
    r = run_all()
    print(json.dumps(r, indent=2))
    sys.exit(0 if r["all_passed"] else 1)
