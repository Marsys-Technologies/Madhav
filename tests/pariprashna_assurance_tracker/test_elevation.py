import datetime as dt
import tempfile
import threading
import time
import unittest
import gc
import http.client
import json
import warnings
from pathlib import Path
from typing import Any
import sys

TRACKER = Path(__file__).parents[2] / "00_ARCHITECTURE/briefs/pariprashna_assurance/tracker"
sys.path.insert(0, str(TRACKER))
from elevation import AdapterRunner, ElevationStore, InvariantViolation, parse_time
from elevation_operations import ShadowOperations, cutover_guard
from elevation_server import handler_factory
from elevation_worker import ShadowSyncWorker
from elevation_worker import command_probe
from elevation_worker import command_probes
from elevation_worker import load_command_probes
from elevation_worker import build_sync_launchd_plist
from elevation_worker import builtin_probes


PLAN_V1 = {
    "campaign_id": "pariprashna-experience-assurance-v3",
    "spine": [f"P{i}" for i in range(8)],
    "streams": [f"S{i}" for i in range(1, 7)],
    "catalogue": {
        "P-PIPE": {"scope": "historical-observation-only", "items": [f"S{i}" for i in range(1, 12)]},
        "P-PORTAL": {"scope": "historical-observation-only", "items": [f"J{i}" for i in range(1, 11)]},
        "P-GUIDED": {"scope": "historical-observation-only", "items": ["L-USER", "L-WIRE", "L-CODE"]},
        "PPR": {"scope": "current-assurance", "items": ["pariprashna-product-requirements"]},
        "EDIR": {"scope": "historical-observation-only", "items": ["experience-defect-and-improvement-register"]},
    },
}


class ElevationStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ElevationStore(Path(self.tmp.name) / "shadow.sqlite3")
        self.revision = self.store.register_plan(PLAN_V1, actor="native-surrogate")
        self.store.enroll_independent_verifier("independent-verifier", actor="native-surrogate", approval_evidence=["verifier-roster"])

    def tearDown(self):
        self.tmp.cleanup()

    def test_registered_plan_is_content_addressed_and_never_overwritten(self):
        """Break caught: a changed plan silently mutates a previously registered revision."""
        self.assertEqual(self.revision["revision"], 1)
        self.assertEqual(self.store.plan(self.revision["plan_hash"])["plan"], PLAN_V1)

    def test_initial_plan_rejects_an_incomplete_or_noncanonical_v2_catalogue(self):
        """Break caught: elevation begins without the complete historical v2 scope mapping."""
        with tempfile.TemporaryDirectory() as root:
            store = ElevationStore(Path(root) / "fresh.sqlite3")
            incomplete = {**PLAN_V1, "catalogue": {"P-PIPE": {"scope": "historical-observation-only", "items": ["S1"]}}}
            with self.assertRaises(InvariantViolation) as rejected:
                store.register_plan(incomplete, actor="native-surrogate")
        self.assertEqual(rejected.exception.code, "CATALOGUE_BASELINE")
        changed = {**PLAN_V1, "catalogue": {**PLAN_V1["catalogue"], "EDIR": {"scope": "historical-observation-only", "items": ["E-001", "E-002"]}}}
        revision_two = self.store.register_plan(changed, actor="native-surrogate")
        self.assertEqual(revision_two["revision"], 2)
        self.assertEqual(self.store.plan(self.revision["plan_hash"])["plan"], PLAN_V1)

    def test_observation_idempotency_cursor_retry_and_quarantine_preserve_raw_record(self):
        """Break caught: duplicate or malformed source input either creates credit or disappears."""
        source = {"source_id": "historical-edir", "kind": "EDIR", "fresh_after_seconds": 60}
        first = self.store.observe(source, cursor="115", idempotency_key="edir-115", payload={"id": "E-001", "status": "OPEN"})
        duplicate = self.store.observe(source, cursor="115", idempotency_key="edir-115", payload={"id": "E-001", "status": "OPEN"})
        self.assertEqual(first["observation_id"], duplicate["observation_id"])
        self.assertEqual(self.store.source_state("historical-edir")["cursor"], "115")
        for _attempt in range(3):
            result = self.store.observe(source, cursor="116", idempotency_key="bad", payload="not-an-object")
        self.assertEqual(result["status"], "QUARANTINED")
        self.assertEqual(self.store.quarantine()[0]["attempts"], 3)
        self.assertEqual(self.store.observations()[0]["payload"], {"id": "E-001", "status": "OPEN"})

    def test_reconciliation_keeps_observation_separate_from_accepted_evidence(self):
        """Break caught: an adapter observation or green CI grants progress, a gate, or cutover credit."""
        source = {"source_id": "github", "kind": "GITHUB", "fresh_after_seconds": 60, "authors": ["lead-p1"]}
        self.store.observe(source, cursor="pr-1540", idempotency_key="pr", payload={"pr": 1540, "merged": True, "checks": "SUCCESS", "claims": {"phase": "P1", "progress": 100, "gate": "CG-1"}})
        projection = self.store.reconcile(now="2026-08-26T00:10:00Z")
        self.assertEqual(projection["accepted_progress"], {})
        self.assertEqual(projection["closed_gates"], [])
        self.assertFalse(projection["cutover_eligible"])
        self.store.accept_evidence("evidence-1", observation_id=1, actor="independent-verifier", classification="VERIFIED", scope="P1", supports=["runtime-proof"], authors=["lead-p1"])
        projection = self.store.reconcile(now="2026-08-26T00:10:00Z")
        self.assertEqual(projection["accepted_evidence"][0]["classification"], "VERIFIED")
        self.assertEqual(projection["accepted_progress"], {})
        self.assertEqual(projection["closed_gates"], [])

    def test_evidence_acceptance_rejects_an_unenrolled_or_self_certifying_actor(self):
        """Break caught: a finder/fixer can label its own observation VERIFIED."""
        self.store.observe({"source_id": "tests", "kind": "TEST", "fresh_after_seconds": 60}, cursor="1", idempotency_key="proof", payload={"result": "PASS"})
        with self.assertRaises(InvariantViolation) as self_certified:
            self.store.accept_evidence("self", observation_id=1, actor="lead-p1", classification="VERIFIED", scope="P1", supports=["test"], authors=["lead-p1"])
        self.assertEqual(self_certified.exception.code, "EVIDENCE_VERIFIER_UNENROLLED")
        with self.assertRaises(InvariantViolation) as same_person:
            self.store.accept_evidence("same", observation_id=1, actor="independent-verifier", classification="VERIFIED", scope="P1", supports=["test"], authors=["independent-verifier"])
        self.assertEqual(same_person.exception.code, "EVIDENCE_SELF_CERTIFICATION")

    def test_evidence_acceptance_uses_immutable_observation_authorship_not_caller_claim(self):
        """Break caught: an enrolled verifier lies about authorship to certify their own observation."""
        self.store.observe({"source_id": "review", "kind": "TEST", "fresh_after_seconds": 60, "authors": ["independent-verifier"]}, cursor="1", idempotency_key="self-proof", payload={"result": "PASS"})
        with self.assertRaises(InvariantViolation) as bypass:
            self.store.accept_evidence("forged", observation_id=1, actor="independent-verifier", classification="VERIFIED", scope="P1", supports=["test"], authors=["someone-else"])
        self.assertEqual(bypass.exception.code, "EVIDENCE_SELF_CERTIFICATION")

    def test_plan_activation_requires_explicit_impact_disposition(self):
        """Break caught: a plan revision silently drops mapped scope or carries evidence forward."""
        changed = {**PLAN_V1, "catalogue": {key: value for key, value in PLAN_V1["catalogue"].items() if key != "EDIR"}}
        candidate = self.store.register_plan(changed, actor="native-surrogate")
        preview = self.store.preview_impact(candidate["plan_hash"])
        self.assertIn("EDIR", preview["removed_catalogue_scopes"])
        with self.assertRaises(InvariantViolation) as missing:
            self.store.activate_plan(candidate["plan_hash"], actor="native-surrogate")
        self.assertEqual(missing.exception.code, "IMPACT_DISPOSITION_REQUIRED")
        activation = self.store.activate_plan(candidate["plan_hash"], actor="native-surrogate", dispositions={"EDIR": {"action": "INVALIDATE", "reason": "scope replacement", "evidence": ["governance-review"]}})
        self.assertEqual(activation["active_revision"], 2)
        self.assertEqual(self.store.reconcile()["active_plan_revision"], 2)

    def test_dashboard_exposes_freshness_contradictions_and_non_authoritative_cutover_packet(self):
        """Break caught: stale or contradictory sources render as healthy or become a cutover approval."""
        self.store.observe({"source_id": "runtime", "kind": "RUNTIME", "fresh_after_seconds": 10}, cursor="8", idempotency_key="runtime", payload={"release": "58e9", "projection_as_of": "2026-08-25T18:30:51Z"}, observed_at="2026-08-25T18:31:00Z")
        self.store.record_contradiction("runtime-not-main", sources=["runtime", "git"], detail="runtime release differs from protected main")
        dashboard = self.store.dashboard(now="2026-08-26T00:10:00Z")
        self.assertEqual(dashboard["sources"][0]["freshness"], "STALE")
        self.assertEqual(dashboard["contradictions"][0]["id"], "runtime-not-main")
        packet = self.store.cutover_packet()
        self.assertFalse(packet["eligible"])
        self.assertIn("native decision", packet["missing"])

    def test_idempotent_reobservation_still_advances_source_freshness(self):
        """Break caught: a source whose real-world value is genuinely stable between
        ticks (no codex process running, an unchanged runtime identity, an EDIR
        register that doesn't exist yet) returns idempotent=True on every re-check,
        and observe() was only updating source_cursors.observed_at on the FIRST-ever
        insert -- so a perfectly healthy, actively-polled source falsely alarms as
        STALE purely from time passing, never from an actual failure to re-verify it."""
        source = {"source_id": "runtime", "kind": "DEPLOYED_RUNTIME", "fresh_after_seconds": 10}
        first = self.store.observe(source, cursor="stable", idempotency_key="runtime:stable", payload={"release": "58e9"}, observed_at="2026-08-26T00:00:00Z")
        self.assertFalse(first["idempotent"])
        second = self.store.observe(source, cursor="stable", idempotency_key="runtime:stable", payload={"release": "58e9"}, observed_at="2026-08-26T00:00:20Z")
        self.assertTrue(second["idempotent"])
        self.assertEqual(self.store.source_state("runtime")["observed_at"], "2026-08-26T00:00:20Z")
        dashboard = self.store.dashboard(now="2026-08-26T00:00:25Z")
        self.assertEqual(dashboard["source_states"]["runtime"]["freshness"], "FRESH")

    def test_adapter_runner_records_all_required_sources_only_as_observations(self):
        """Break caught: a missing adapter disappears from the dashboard or adapter data self-accepts."""
        runner = AdapterRunner(self.store, probes={
            "codex_tasks": lambda _cursor: {"cursor": "task-1", "payload": {"task": "Paripraśna - Tracker", "state": "ACTIVE"}},
            "github": lambda _cursor: {"cursor": "pr-1540", "payload": {"pr": 1540, "ci": "SUCCESS", "merge_queue": "MERGED"}},
            "git_worktrees": lambda _cursor: {"cursor": "wt-1", "payload": {"branch": "codex/pariprashna-tracker-elevation"}},
            "runtime": lambda _cursor: {"cursor": "runtime-8", "payload": {"release": "58e9", "integrity": True}},
            "tests_evidence": lambda _cursor: {"cursor": "test-1", "payload": {"suite": "shadow", "result": "PASS"}},
            "edir": lambda _cursor: {"cursor": "edir-115", "payload": {"open": 113, "historical": True}},
        })
        results = runner.collect_all()
        self.assertEqual(set(results), {"codex_tasks", "github", "git_worktrees", "runtime", "tests_evidence", "edir"})
        dashboard = self.store.dashboard()
        self.assertEqual(dashboard["source_states"]["github"]["payload"]["pr"], 1540)
        self.assertEqual(self.store.reconcile()["accepted_evidence"], [])

    def test_shadow_sync_worker_runs_a_full_adapter_tick_without_accepting_evidence(self):
        """Break caught: the deployed dashboard starts but never refreshes its source ledger."""
        worker = ShadowSyncWorker(self.store, probes={
            "codex_tasks": lambda _cursor: {"cursor": "task-1", "payload": {"state": "ACTIVE"}},
            "github": lambda _cursor: {"cursor": "pr-1550", "payload": {"state": "MERGED"}},
            "git_worktrees": lambda _cursor: {"cursor": "main-5f07", "payload": {"main": "5f07"}},
            "runtime": lambda _cursor: {"cursor": "runtime-8788", "payload": {"listener": "127.0.0.1:8788"}},
            "tests_evidence": lambda _cursor: {"cursor": "tests-1", "payload": {"result": "PASS"}},
            "edir": lambda _cursor: {"cursor": "edir-unknown", "payload": {"state": "UNKNOWN"}},
        })
        result = worker.sync_once()
        self.assertEqual(set(result), {"codex_tasks", "github", "git_worktrees", "runtime", "tests_evidence", "edir"})
        self.assertEqual(self.store.dashboard()["source_states"]["github"]["freshness"], "FRESH")
        self.assertEqual(self.store.reconcile()["accepted_evidence"], [])

    def test_command_probe_requires_a_cursor_and_object_payload(self):
        """Break caught: an autonomous adapter accepts malformed command output as fresh source data."""
        probe = command_probe([sys.executable, "-c", "import json; print(json.dumps({'cursor':'runtime-1','payload':{'ok':True}}))"])
        self.assertEqual(probe(None), {"cursor": "runtime-1", "payload": {"ok": True}})
        malformed = command_probe([sys.executable, "-c", "print('not-json')"])
        with self.assertRaises(ValueError):
            malformed(None)

    def test_command_probes_only_accept_required_adapter_names(self):
        """Break caught: deployment configuration can inject an ungoverned adapter name."""
        command = [sys.executable, "-c", "import json; print(json.dumps({'cursor':'1','payload':{'state':'ok'}}))"]
        self.assertEqual(command_probes({"github": command})["github"](None)["cursor"], "1")
        with self.assertRaises(ValueError):
            command_probes({"unapproved": command})

    def test_worker_configuration_is_an_exact_probe_map(self):
        """Break caught: a mutable worker config carries settings outside governed adapter commands."""
        config = Path(self.tmp.name) / "probes.json"
        config.write_text(json.dumps({"github": [sys.executable, "-c", "import json; print(json.dumps({'cursor':'1','payload':{}}))"]}), encoding="utf-8")
        self.assertEqual(load_command_probes(config)["github"](None)["cursor"], "1")
        config.write_text(json.dumps({"github": [], "extra": []}), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_command_probes(config)

    def test_sync_launchd_plist_runs_the_shadow_worker_on_a_bounded_interval(self):
        """Break caught: automation is represented as metadata rather than a runnable, isolated job."""
        import plistlib

        runtime = Path(self.tmp.name) / "runtime"
        release = Path(self.tmp.name) / "release"
        source_repo = Path(self.tmp.name) / "repo"
        plist = plistlib.loads(build_sync_launchd_plist(release, runtime, source_repo, "http://127.0.0.1:8787/api/service-identity", interval_seconds=60))
        self.assertEqual(plist["Label"], "com.marsys.pariprashna-assurance.shadow.sync")
        self.assertEqual(plist["StartInterval"], 60)
        self.assertIn("--source-repo", plist["ProgramArguments"])
        self.assertIn(str(source_repo), plist["ProgramArguments"])
        self.assertIn("--accepted-identity-url", plist["ProgramArguments"])
        self.assertIn("--once", plist["ProgramArguments"])
        self.assertNotIn("--probe-config", plist["ProgramArguments"])
        plist_with_config = plistlib.loads(build_sync_launchd_plist(release, runtime, source_repo, "http://127.0.0.1:8787/api/service-identity", interval_seconds=60, probe_config=runtime / "probes.json"))
        self.assertIn("--probe-config", plist_with_config["ProgramArguments"])
        self.assertIn(str(runtime / "probes.json"), plist_with_config["ProgramArguments"])

    def test_sync_launchd_plist_carries_a_path_the_github_probe_can_find_gh_on(self):
        """Break caught: launchd's minimal default environment has no PATH, so the
        github adapter's `gh` subprocess call fails every tick with ENOENT and that
        source silently stays UNKNOWN forever -- the plist must set an explicit PATH
        covering common gh install locations."""
        import plistlib

        runtime = Path(self.tmp.name) / "runtime"
        release = Path(self.tmp.name) / "release"
        source_repo = Path(self.tmp.name) / "repo"
        plist = plistlib.loads(build_sync_launchd_plist(release, runtime, source_repo, "http://127.0.0.1:8787/api/service-identity", interval_seconds=60))
        env = plist["EnvironmentVariables"]
        path_entries = env["PATH"].split(":")
        self.assertIn("/opt/homebrew/bin", path_entries)
        self.assertIn("/usr/local/bin", path_entries)
        self.assertIn("/usr/bin", path_entries)

    def test_github_probe_stores_a_minimal_projection_not_the_raw_api_response(self):
        """Break caught: the github probe stored the entire raw GitHub API pull-request
        objects (full body text, nested user/head/base/labels objects) as the shadow
        observation payload -- 187KB for 9 real open PRs in this repo -- bloating the
        shadow DB and every dashboard API response for no operational benefit. Only the
        handful of fields the freshness/reconciliation model actually needs should be
        retained."""
        huge_body = "x" * 50_000
        raw_pr = {
            "number": 1550, "state": "open", "draft": False, "merged_at": None,
            "updated_at": "2026-08-26T12:00:00Z", "mergeable_state": "clean",
            "title": "feat(pariprashna): governed shadow tracker elevation",
            "body": huge_body,
            "html_url": "https://github.com/Marsys-Technologies/Madhav/pull/1550",
            "user": {"login": "pb3-bot", "id": 12345, "avatar_url": "https://example.invalid/a.png", "extra": "x" * 5000},
            "head": {"ref": "codex/pariprashna-shadow-sync", "sha": "5f30acf4d", "repo": {"id": 1, "name": "Madhav", "extra": "x" * 5000}},
            "base": {"ref": "main", "sha": "5f07e085", "repo": {"id": 1, "name": "Madhav", "extra": "x" * 5000}},
            "labels": [{"name": "lane:x", "color": "abcdef", "extra": "x" * 1000}],
            "requested_reviewers": [], "assignees": [],
        }
        def run(argv):
            return json.dumps([raw_pr])
        probes = builtin_probes(Path("/repo"), "http://127.0.0.1:8787", run_command=run, fetch_json=lambda _url: {})
        result = probes["github"](None)
        encoded_size = len(json.dumps(result["payload"]))
        self.assertLess(encoded_size, 2000, f"github payload should be a minimal projection, not {encoded_size} bytes")
        pr = result["payload"]["open_pull_requests"][0]
        self.assertEqual(pr["number"], 1550)
        self.assertEqual(pr["state"], "open")
        self.assertEqual(pr["head_ref"], "codex/pariprashna-shadow-sync")
        self.assertEqual(pr["head_sha"], "5f30acf4d")
        self.assertEqual(pr["updated_at"], "2026-08-26T12:00:00Z")
        self.assertNotIn("body", pr)
        self.assertNotIn("user", pr)
        self.assertNotIn("head", pr)
        self.assertNotIn("labels", pr)

    def test_builtin_probes_record_github_git_and_runtime_as_observations(self):
        """Break caught: autonomous polling has no concrete sources and only emits stale placeholders."""
        repo_dir = Path(self.tmp.name) / "fixture-repo"; repo_dir.mkdir()
        commands = {
            ("gh", "api", "repos/Marsys-Technologies/Madhav/pulls?state=open&per_page=100"): '[{"number":1550,"state":"open"}]',
            ("git", "-C", str(repo_dir), "worktree", "list", "--porcelain"): "worktree /repo\nHEAD 5f07\nbranch refs/heads/main\n",
            ("git", "-C", str(repo_dir), "rev-parse", "origin/main"): "5f07\n",
        }
        def run(argv):
            return commands[tuple(argv)]
        tests_dir = Path(self.tmp.name) / "fixture-tests"; tests_dir.mkdir()
        (tests_dir / "test_trivial.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        edir_path = Path(self.tmp.name) / "EDIR_V3_REGISTER_v1_0.md"
        probes = builtin_probes(repo_dir, "http://127.0.0.1:8787", run_command=run, fetch_json=lambda _url: {"source_sha": "58e9", "ok": True}, tests_dir=tests_dir, edir_path=edir_path)
        self.assertEqual(set(probes), {"github", "git_worktrees", "runtime", "codex_tasks", "tests_evidence", "edir"})
        self.assertEqual(probes["runtime"](None)["payload"]["source_sha"], "58e9")
        self.assertEqual(probes["git_worktrees"](None)["payload"]["origin_main"], "5f07")
        self.assertIn(probes["codex_tasks"](None)["payload"]["state"], {"ACTIVE", "IDLE"})
        self.assertEqual(probes["tests_evidence"](None)["payload"]["returncode"], 0)
        self.assertEqual(probes["edir"](None)["payload"]["state"], "NOT_YET_OPENED")
        edir_path.write_text("# EDIR V3\n", encoding="utf-8")
        self.assertEqual(probes["edir"](None)["payload"]["state"], "OPEN")

    def test_adapter_runner_honors_a_distinct_freshness_budget_per_source(self):
        """Break caught (elevation §5.4): a single global freshness value cannot express
        the per-source budgets (git/GitHub 15min, runtime 30min, tests/evidence + EDIR
        60min) -- each adapter's own budget must reach the stored source row and drive
        an independent stale/fresh verdict, not one value shared by every source."""
        runner = AdapterRunner(self.store, probes={
            "github": lambda _cursor: {"cursor": "c1", "payload": {"ok": True}},
            "edir": lambda _cursor: {"cursor": "c2", "payload": {"ok": True}},
        }, fresh_after_seconds={"github": 5, "edir": 600})
        runner.collect_all()
        self.assertEqual(self.store.source_state("github")["fresh_after_seconds"], 5)
        self.assertEqual(self.store.source_state("edir")["fresh_after_seconds"], 600)
        observed_at = self.store.source_state("github")["observed_at"]
        dashboard = self.store.dashboard(now=(parse_time(observed_at) + dt.timedelta(seconds=30)).isoformat().replace("+00:00", "Z"))
        self.assertEqual(dashboard["source_states"]["github"]["freshness"], "STALE")
        self.assertEqual(dashboard["source_states"]["edir"]["freshness"], "FRESH")

    def test_worker_advances_source_freshness_autonomously_with_no_manual_api_call(self):
        """Break caught (elevation §5.1): the deployed worker must keep every configured
        source's observed_at advancing purely from its own background loop over real
        elapsed time -- proving autonomy means never calling sync_once()/an adapter by
        hand, only starting run_forever() and watching it work unattended."""
        calls = {"n": 0}

        def probe(_cursor: str | None) -> dict[str, Any]:
            calls["n"] += 1
            return {"cursor": f"tick-{calls['n']}", "payload": {"tick": calls["n"]}}

        worker = ShadowSyncWorker(self.store, probes={name: probe for name in AdapterRunner.REQUIRED_ADAPTERS}, fresh_after_seconds=1)
        stop = threading.Event()
        thread = threading.Thread(target=worker.run_forever, kwargs={"stop": stop, "interval_seconds": 0.05}, daemon=True)
        thread.start()
        try:
            deadline = time.time() + 3.0
            while calls["n"] < 3 and time.time() < deadline:
                time.sleep(0.05)
        finally:
            stop.set()
            thread.join(timeout=2)
        self.assertGreaterEqual(calls["n"], 3, "worker did not tick autonomously without a manual call")
        dashboard = self.store.dashboard()
        for source in AdapterRunner.REQUIRED_ADAPTERS:
            self.assertEqual(dashboard["source_states"][source]["freshness"], "FRESH")

    def test_shadow_operations_schedule_recovery_but_never_targets_accepted_service(self):
        """Break caught: automation targets the accepted service or omits a required recovery control."""
        operations = ShadowOperations(runtime=Path(self.tmp.name) / "shadow-runtime", source_sha="ca4fd54")
        jobs = operations.launchd_jobs()
        self.assertEqual({job["frequency"] for job in jobs}, {"continuous", "daily", "weekly"})
        self.assertTrue(any(job["purpose"] == "weekly restore verification" for job in jobs))
        self.assertTrue(all(".shadow" in job["label"] for job in jobs))
        with self.assertRaises(InvariantViolation) as blocked:
            cutover_guard(self.store.cutover_packet())
        self.assertEqual(blocked.exception.code, "CUTOVER_NOT_AUTHORIZED")
        with self.assertRaises(InvariantViolation) as fabricated:
            cutover_guard({"eligible": True, "live_runtime_changed": False, "native_decision": "forged"})
        self.assertEqual(fabricated.exception.code, "CUTOVER_NOT_AUTHORIZED")

    def test_shadow_operations_create_private_snapshot_and_verify_isolated_restore(self):
        """Break caught: a scheduled recovery job reports success without a private, replayable shadow snapshot."""
        operations = ShadowOperations(runtime=Path(self.tmp.name) / "ops", source_sha="ca4fd54", store=self.store)
        snapshot = operations.create_snapshot()
        self.assertTrue(snapshot["path"].exists())
        self.assertFalse(snapshot["path"].stat().st_mode & 0o077)
        restored = operations.verify_restore(snapshot["path"])
        self.assertTrue(restored["ok"])
        self.assertEqual(restored["source_hash"], restored["restored_hash"])

    def test_shadow_store_does_not_leave_sqlite_connections_open(self):
        """Break caught: repeated adapter reconciliation leaks descriptors in the watchdog process."""
        with tempfile.TemporaryDirectory() as root, warnings.catch_warnings():
            warnings.simplefilter("error", ResourceWarning)
            store = ElevationStore(Path(root) / "shadow.sqlite3")
            store.register_plan(PLAN_V1, actor="native-surrogate")
            store.dashboard()
            del store
            gc.collect()

    def test_elevation_dashboard_serves_source_freshness_without_live_control_access(self):
        """Break caught: the elevation dashboard hides freshness or reads/writes the accepted control plane."""
        from http.server import ThreadingHTTPServer
        import threading
        from elevation_server import DASHBOARD
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler_factory(self.store, DASHBOARD))
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", httpd.server_port, timeout=2)
            connection.request("GET", "/api/elevation")
            response = connection.getresponse()
            payload = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertEqual(payload["plan_revision"], None)
            connection.request("GET", "/", headers={"Host": "evil.example"})
            self.assertEqual(connection.getresponse().status, 403)
            connection.request("GET", "/", headers={"Host": f"127.0.0.1:{httpd.server_port}"})
            page = connection.getresponse().read().decode("utf-8")
            self.assertIn("Shadow Elevation", page)
        finally:
            httpd.shutdown(); thread.join(timeout=2); httpd.server_close()


if __name__ == "__main__":
    unittest.main()
