import tempfile
import unittest
import gc
import http.client
import json
import warnings
from pathlib import Path
import sys

TRACKER = Path(__file__).parents[2] / "00_ARCHITECTURE/briefs/pariprashna_assurance/tracker"
sys.path.insert(0, str(TRACKER))
from elevation import AdapterRunner, ElevationStore, InvariantViolation
from elevation_operations import ShadowOperations, cutover_guard
from elevation_server import handler_factory
from elevation_service import (
    APPROVED_SHADOW_RUNTIME,
    SHADOW_DASHBOARD_LABEL,
    assert_shadow_release_attestation,
    build_shadow_dashboard_plist,
)


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

    def test_shadow_dashboard_launchd_spec_is_pinned_to_the_shadow_runtime_and_loopback(self):
        """Break caught: a shadow dashboard job can target the accepted tracker or a network listener."""
        import plistlib

        release = Path(self.tmp.name) / "sealed-release"
        plist = plistlib.loads(build_shadow_dashboard_plist(release, APPROVED_SHADOW_RUNTIME, "a" * 40))
        self.assertEqual(plist["Label"], SHADOW_DASHBOARD_LABEL)
        self.assertIn("127.0.0.1", plist["ProgramArguments"])
        self.assertIn("8788", plist["ProgramArguments"])
        self.assertIn(str(APPROVED_SHADOW_RUNTIME / "elevation.sqlite3"), plist["ProgramArguments"])
        with self.assertRaises(ValueError):
            build_shadow_dashboard_plist(release, Path("/Users/Dev/.pariprashna-assurance-control"), "a" * 40)

    def test_shadow_dashboard_refuses_an_unsealed_or_mutable_release(self):
        """Break caught: launchd can execute an arbitrary mutable dashboard tree."""
        release = Path(self.tmp.name) / "release"
        release.mkdir()
        with self.assertRaises(ValueError) as rejected:
            assert_shadow_release_attestation(release, "a" * 40)
        self.assertIn("attested", str(rejected.exception))

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
