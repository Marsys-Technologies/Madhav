import http.client
import json
import os
import plistlib
import queue
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

TRACKER = Path(__file__).parents[2] / "00_ARCHITECTURE/briefs/pariprashna_assurance/tracker"
sys.path.insert(0, str(TRACKER))
from control import EventStore, RejectedEvent, canonical, digest, fold, programme_definition, presence_overlay  # noqa: E402
from server import EventBus, ReplayMonitor, handler_factory, adapter_health, seed_empty_demo_runtime  # noqa: E402
from service import CANONICAL_MADHAV_ORIGIN, RELEASE_FILES, SERVICE_LABEL, _PROVENANCE_GIT_CONFIG, _secure_service_logs, assert_release_attestation, attest_release, build_launchd_plist, runtime_preflight  # noqa: E402
from http.server import ThreadingHTTPServer

EVIDENCE = [{"kind": "test-artifact", "uri": "file://evidence/result.json"}]


class ControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.store = EventStore(self.tmp.name)
        credentials = self.store.provision_local_credentials(); self.tokens = json.loads(Path(credentials["path"]).read_text())["tokens"]
        self.store.submit({"actor_id": "integrator", "idempotency_key": "bootstrap", "event_type": "campaign_bootstrapped", "payload": {"campaign_id": "demo"}, "evidence": EVIDENCE})

    def tearDown(self): self.tmp.cleanup()

    def emit(self, actor, typ, payload=None, stream=None, evidence=EVIDENCE, key=None, seq=None):
        return self.store.submit({"actor_id": actor, "idempotency_key": key or f"{actor}-{typ}-{time.time_ns()}", "event_type": typ, "payload": payload or {}, "stream_id": stream, "expected_stream_seq": self.store.next_stream_seq(stream) if stream and seq is None else seq, "evidence": evidence})

    def accepted_s1_item(self):
        self.emit("lead-s1", "work_started", {"session_id": "s1", "assignment": "baseline", "branch": "b", "worktree": "w", "baseline_sha": "a", "current_sha": "a", "verifier": "verifier", "participants": [{"actor_id": "surrogate", "role": "NATIVE_SURROGATE", "state": "ACTIVE", "assignment": "triage", "model": "product-model", "reasoning_config": "standard"}, {"actor_id": "a11y-specialist", "role": "SPECIALIST", "state": "WAITING", "assignment": "accessibility review", "model": "audit-model", "reasoning_config": "high"}], "model": "test-model", "reasoning_config": "test", "cost": {"amount": 125000, "currency": "INR", "basis": "approved ceiling"}, "planned_scenarios": 12}, "S1")
        verify = self.emit("verifier", "verification_accepted", {"verification_id": "v1", "work_item_id": "S1:charter", "finder_actor_id": "lead-s1", "fixer_actor_id": "lead-s1"}, "S1")
        self.emit("integrator", "work_item_accepted", {"work_item_id": "S1:charter", "verification_event_id": verify["event"]["event_id"]}, "S1")

    def test_replay_hash_is_identical(self):
        self.accepted_s1_item(); before = self.store.projection()["canonical_hash"]
        self.assertTrue(self.store.verify_replay()["ok"]); self.store.rebuild(self.store.projection()["projection_as_of"])
        self.assertEqual(before, self.store.projection()["canonical_hash"])

    def test_replay_detects_tampered_event_chain_before_rebuild(self):
        with self.store.connection() as con:
            con.execute("DROP TRIGGER events_no_update")
            con.execute("UPDATE events SET event_hash='tampered' WHERE ledger_seq=1")
        result = self.store.verify_replay()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "event hash mismatch")

    def test_replay_rejects_tampered_programme_definition_before_rebuild(self):
        definition = self.store.definition(); definition["phases"][0]["campaign_weight"] = 999
        with self.store.connection() as con:
            con.execute("UPDATE ledger_meta SET definition_json=? WHERE id=1", (canonical(definition),))
        result = self.store.verify_replay()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "programme definition mismatch")
        with self.assertRaises(RejectedEvent) as rebuild:
            self.store.rebuild()
        self.assertEqual(rebuild.exception.code, "LEDGER_INTEGRITY")
        with self.assertRaises(RejectedEvent) as startup:
            EventStore(self.tmp.name)
        self.assertEqual(startup.exception.code, "DEFINITION_INTEGRITY")

    def test_snapshot_restores_to_a_separate_empty_runtime_with_matching_hash(self):
        self.accepted_s1_item()
        with tempfile.TemporaryDirectory() as root:
            snapshot_path = Path(root) / "source.snapshot.json"
            source = self.store.export_snapshot(snapshot_path)
            recovery = EventStore(Path(root) / "recovery-runtime")
            restored = recovery.restore_snapshot(snapshot_path)
            self.assertEqual(restored["canonical_hash"], self.store.projection()["canonical_hash"])
            self.assertEqual(restored["event_log_hash"], source["event_log_hash"])
            with self.assertRaises(RejectedEvent) as non_empty:
                recovery.restore_snapshot(snapshot_path)
            self.assertEqual(non_empty.exception.code, "RECOVERY_RUNTIME_NOT_EMPTY")

    def test_malformed_snapshot_projection_leaves_recovery_runtime_empty(self):
        with tempfile.TemporaryDirectory() as root:
            snapshot_path = Path(root) / "malformed.snapshot.json"
            self.store.export_snapshot(snapshot_path)
            snapshot = json.loads(snapshot_path.read_text()); snapshot["projection"] = {}
            os.chmod(snapshot_path, 0o600); snapshot_path.write_text(canonical(snapshot)); os.chmod(snapshot_path, 0o444)
            recovery = EventStore(Path(root) / "recovery-runtime")
            with self.assertRaises(RejectedEvent) as invalid:
                recovery.restore_snapshot(snapshot_path)
            self.assertEqual(invalid.exception.code, "SNAPSHOT_INVALID")
            self.assertEqual(recovery.events(), [])
            with recovery.connection() as con:
                self.assertIsNone(con.execute("SELECT 1 FROM projection_state WHERE id=1").fetchone())

    def test_monitor_failure_publishes_unknown_and_removes_green_state(self):
        bus = EventBus(); updates = bus.subscribe(); original = self.store.verify_replay
        self.store.verify_replay = lambda: (_ for _ in ()).throw(RuntimeError("injected monitor fault"))
        monitor = ReplayMonitor(self.store, bus, 0.01); monitor.start()
        try:
            update = json.loads(updates.get(timeout=1))
            self.assertEqual(update["service_health"], "UNKNOWN")
        finally:
            monitor.stop(); monitor.join(timeout=1); bus.unsubscribe(updates); self.store.verify_replay = original
        projection = self.store.projection()
        self.assertEqual(projection["monitor_health"]["status"], "UNKNOWN")
        self.assertTrue(all(stream["health"] == "INTEGRITY_DEGRADED" for stream in projection["display"]["streams"]))

    def test_monitor_persistence_failure_still_publishes_unknown(self):
        bus = EventBus(); updates = bus.subscribe(); original = self.store.record_monitor_status
        self.store.record_monitor_status = lambda *_args: (_ for _ in ()).throw(sqlite3.OperationalError("injected persistence fault"))
        monitor = ReplayMonitor(self.store, bus, 0.01); monitor.start()
        try:
            update = json.loads(updates.get(timeout=1))
            self.assertEqual(update["service_health"], "UNKNOWN")
            self.assertTrue(bus.service_unavailable())
        finally:
            monitor.stop(); monitor.join(timeout=1); bus.unsubscribe(updates); self.store.record_monitor_status = original

    def test_service_unavailable_sentinel_replaces_projection_response(self):
        bus = EventBus(); bus.mark_service_unavailable()
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler_factory(self.store, bus, TRACKER / "dashboard.html")); thread = threading.Thread(target=httpd.serve_forever, daemon=True); thread.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", httpd.server_port, timeout=2); conn.request("GET", "/api/projection")
            response = conn.getresponse(); payload = json.loads(response.read()); conn.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(payload["service_health"], "UNKNOWN")
        finally:
            httpd.shutdown(); thread.join(timeout=2); httpd.server_close()

    def test_duplicate_idempotency_returns_original(self):
        request = {"actor_id": "lead-s1", "idempotency_key": "same", "event_type": "work_started", "payload": {"session_id": "same", "planned_scenarios": 1}, "stream_id": "S1", "expected_stream_seq": 0, "evidence": EVIDENCE}
        first = self.store.submit(request); second = self.store.submit(request)
        self.assertFalse(first["idempotent"]); self.assertTrue(second["idempotent"]); self.assertEqual(len(self.store.events()), 2)

        conflicting = {**request, "payload": {"session_id": "different", "planned_scenarios": 1}}
        with self.assertRaises(RejectedEvent) as reuse:
            self.store.submit(conflicting)
        self.assertEqual(reuse.exception.code, "IDEMPOTENCY_CONFLICT")
        with self.assertRaises(RejectedEvent) as unauthenticated:
            self.store.submit({**request, "actor_id": "unknown-actor"})
        self.assertEqual(unauthenticated.exception.code, "UNAUTHENTICATED")
        separate_actor = {**request, "actor_id": "lead-s2", "payload": {"session_id": "actor-scoped", "planned_scenarios": 1}, "stream_id": "S2"}
        self.assertFalse(self.store.submit(separate_actor)["idempotent"])

    def test_event_timestamp_is_server_assigned(self):
        request = {"actor_id": "lead-s1", "idempotency_key": "client-time", "event_type": "work_started", "payload": {"session_id": "client-time", "planned_scenarios": 1}, "stream_id": "S1", "expected_stream_seq": 0, "evidence": EVIDENCE, "occurred_at": "2000-01-01T00:00:00Z"}
        with self.assertRaises(RejectedEvent) as timestamp:
            self.store.submit(request)
        self.assertEqual(timestamp.exception.code, "OCCURRED_AT_FORBIDDEN")

    def test_runtime_credentials_are_random_private_and_not_reprovisioned(self):
        self.assertIsNone(self.store.authenticate("local-integrator")); self.assertEqual(self.store.authenticate(self.tokens["integrator"]), "integrator")
        credential_file = Path(self.tmp.name) / "local-credentials.json"; self.assertFalse(credential_file.stat().st_mode & 0o077)
        with self.assertRaises(RejectedEvent) as ctx: self.store.provision_local_credentials()
        self.assertEqual(ctx.exception.code, "CREDENTIALS_EXIST")

    def test_p0b_operators_have_distinct_role_scoped_credentials(self):
        with tempfile.TemporaryDirectory() as runtime:
            store = EventStore(runtime, p0b_only=True)
            tokens = json.loads(Path(store.provision_local_credentials()["path"]).read_text())["tokens"]
            expected = {
                "lead-p0b": "STREAM_LEAD",
                "surrogate-p0b": "NATIVE_SURROGATE",
                "verifier-p0b": "INDEPENDENT_VERIFIER",
                "integrator-p0b": "PROGRAMME_INTEGRATOR",
            }
            self.assertEqual(set(tokens), set(expected))
            for actor_id, role in expected.items():
                self.assertEqual(store.actor_role(actor_id), role)
                self.assertEqual(store.authenticate(tokens[actor_id]), actor_id)
                with store.connection() as con:
                    row = con.execute("SELECT streams_json FROM actors WHERE actor_id=?", (actor_id,)).fetchone()
                self.assertEqual(json.loads(row["streams_json"]), ["P0"])
            self.assertEqual(len(set(tokens.values())), len(tokens))
            store.submit({"actor_id": "integrator-p0b", "idempotency_key": "p0b-bootstrap", "event_type": "campaign_bootstrapped", "payload": {"campaign_id": "pariprashna-experience-assurance-v3"}, "evidence": EVIDENCE})
            with self.assertRaises(RejectedEvent) as p1_start:
                store.submit({"actor_id": "lead-p0b", "idempotency_key": "p1-forbidden", "event_type": "work_started", "payload": {"session_id": "p1-forbidden"}, "stream_id": "P1", "expected_stream_seq": 0, "evidence": EVIDENCE})
            self.assertEqual(p1_start.exception.code, "STREAM_FORBIDDEN")

    def test_p0b_integrator_can_only_record_post_cg0_p0_to_p1_handoff(self):
        with tempfile.TemporaryDirectory() as runtime:
            store = EventStore(runtime, p0b_only=True)
            store.submit({"actor_id": "integrator-p0b", "idempotency_key": "p0b-bootstrap", "event_type": "campaign_bootstrapped", "payload": {"campaign_id": "pariprashna-experience-assurance-v3"}, "evidence": EVIDENCE})
            handoff = {"actor_id": "integrator-p0b", "idempotency_key": "p0-p1-handoff", "event_type": "dependency_resolved", "payload": {"from": "P0", "to": "P1"}, "stream_id": "P1", "expected_stream_seq": 0, "evidence": EVIDENCE}
            with self.assertRaises(RejectedEvent) as premature:
                store.submit(handoff)
            self.assertEqual(premature.exception.code, "P0B_HANDOFF_PREREQUISITE")

            item_verification = store.submit({"actor_id": "verifier-p0b", "idempotency_key": "p0-item-verification", "event_type": "verification_accepted", "payload": {"verification_id": "p0-item", "work_item_id": "P0:completion", "finder_actor_id": "lead-p0b", "fixer_actor_id": "lead-p0b"}, "stream_id": "P0", "expected_stream_seq": 0, "evidence": EVIDENCE})
            store.submit({"actor_id": "integrator-p0b", "idempotency_key": "p0-item-acceptance", "event_type": "work_item_accepted", "payload": {"work_item_id": "P0:completion", "verification_event_id": item_verification["event"]["event_id"]}, "stream_id": "P0", "expected_stream_seq": 1, "evidence": EVIDENCE})
            gate_verification = store.submit({"actor_id": "verifier-p0b", "idempotency_key": "cg0-verification", "event_type": "verification_accepted", "payload": {"verification_id": "cg0", "gate_id": "CG-0", "finder_actor_id": "lead-p0b", "fixer_actor_id": "lead-p0b"}, "stream_id": "P0", "expected_stream_seq": 2, "evidence": EVIDENCE})
            store.submit({"actor_id": "integrator-p0b", "idempotency_key": "cg0-closure", "event_type": "gate_closed", "payload": {"gate_id": "CG-0", "verification_event_id": gate_verification["event"]["event_id"]}, "stream_id": "P0", "expected_stream_seq": 3, "evidence": EVIDENCE})

            self.assertTrue(store.submit(handoff)["accepted"])
            dependency = next(item for item in store.projection()["canonical"]["dependencies"] if item["from"] == "P0" and item["to"] == "P1")
            self.assertEqual(dependency["status"], "RESOLVED")
            self.assertTrue(store.verify_replay()["ok"])
            with tempfile.TemporaryDirectory() as recovery_root:
                snapshot_path = Path(recovery_root) / "p0b-handoff.snapshot.json"
                source = store.export_snapshot(snapshot_path)
                recovery = EventStore(Path(recovery_root) / "recovery", p0b_only=True)
                restored = recovery.restore_snapshot(snapshot_path)
                self.assertEqual(restored["event_log_hash"], source["event_log_hash"])
                self.assertTrue(recovery.verify_replay()["ok"])
                recovered_dependency = next(item for item in recovery.projection()["canonical"]["dependencies"] if item["from"] == "P0" and item["to"] == "P1")
                self.assertEqual(recovered_dependency["status"], "RESOLVED")
            with self.assertRaises(RejectedEvent) as unrelated_p1:
                store.submit({"actor_id": "integrator-p0b", "idempotency_key": "unrelated-p1", "event_type": "integration_baseline_advanced", "payload": {}, "stream_id": "P1", "expected_stream_seq": 1, "evidence": EVIDENCE})
            self.assertEqual(unrelated_p1.exception.code, "STREAM_FORBIDDEN")
            with self.assertRaises(RejectedEvent) as p1_start:
                store.submit({"actor_id": "lead-p0b", "idempotency_key": "p1-start", "event_type": "work_started", "payload": {"session_id": "p1-start"}, "stream_id": "P1", "expected_stream_seq": 1, "evidence": EVIDENCE})
            self.assertEqual(p1_start.exception.code, "STREAM_FORBIDDEN")

    def test_runtime_and_database_permissions_are_private(self):
        with tempfile.TemporaryDirectory() as runtime:
            os.chmod(runtime, 0o755)
            store = EventStore(runtime)
            self.assertEqual(Path(runtime).stat().st_mode & 0o777, 0o700)
            self.assertEqual(store.db_path.stat().st_mode & 0o777, 0o600)

    def test_launchd_preflight_requires_private_approved_runtime_and_filevault(self):
        with tempfile.TemporaryDirectory() as root:
            runtime = Path(root) / "approved-runtime"
            runtime_preflight(runtime, runtime, "FileVault is On.")
            self.assertEqual(runtime.stat().st_mode & 0o777, 0o700)
            with self.assertRaises(ValueError): runtime_preflight(runtime, runtime.parent / "wrong-runtime", "FileVault is On.")
            with self.assertRaises(ValueError): runtime_preflight(runtime, runtime, "FileVault is Off.")
            plist = build_launchd_plist(Path("/immutable/release"), runtime).decode()
            self.assertIn(SERVICE_LABEL, plist)
            self.assertIn("127.0.0.1", plist)
            self.assertIn("--p0b-only", plist)
            self.assertIn(str(runtime), plist)

    def test_service_logs_are_private_before_launchd_starts(self):
        with tempfile.TemporaryDirectory() as runtime:
            runtime_path = Path(runtime)
            _secure_service_logs(runtime_path)
            for name in ("service.log", "service.error.log"):
                self.assertEqual((runtime_path / name).stat().st_mode & 0o777, 0o600)

    def test_concurrent_credential_provisioning_has_one_winner(self):
        with tempfile.TemporaryDirectory() as runtime:
            first, second = EventStore(runtime), EventStore(runtime)
            barrier = threading.Barrier(3); outcomes = []
            def provision(store):
                barrier.wait()
                try: outcomes.append(("accepted", store.provision_local_credentials()))
                except RejectedEvent as exc: outcomes.append(("rejected", exc.code))
            workers = [threading.Thread(target=provision, args=(store,)) for store in (first, second)]
            [worker.start() for worker in workers]; barrier.wait(); [worker.join() for worker in workers]
            self.assertEqual([result[0] for result in outcomes].count("accepted"), 1); self.assertEqual([result[1] for result in outcomes if result[0] == "rejected"], ["CREDENTIALS_EXIST"])
            credentials = json.loads(Path(next(result[1]["path"] for result in outcomes if result[0] == "accepted")).read_text())
            self.assertEqual(first.authenticate(credentials["tokens"]["integrator"]), "integrator")

    def test_demo_seed_requires_an_empty_runtime(self):
        with tempfile.TemporaryDirectory() as root:
            runtime = Path(root) / "demo"
            seed_empty_demo_runtime(runtime)
            projection = EventStore(runtime).projection()
            self.assertTrue(projection["canonical"]["bootstrapped"])
            self.assertEqual(projection["canonical"]["runtime_mode"], "DEMONSTRATION")
            self.assertTrue(any(stream["lifecycle"] == "COMPLETE" for stream in projection["display"]["streams"]))
            with self.assertRaises(ValueError): seed_empty_demo_runtime(runtime)
            non_directory = Path(root) / "not-a-runtime"; non_directory.write_text("preserve me")
            with self.assertRaises(ValueError): seed_empty_demo_runtime(non_directory)
            self.assertEqual(non_directory.read_text(), "preserve me")

    def test_bootstrap_has_no_fabricated_historical_credit(self):
        canonical = self.store.projection()["canonical"]
        self.assertTrue(canonical["bootstrapped"]); self.assertEqual(canonical["completion"]["earned_campaign_points"], 0); self.assertTrue(all(g["status"] == "OPEN" for g in canonical["gates"]))

    def test_non_demo_bootstrap_projects_campaign_runtime(self):
        with tempfile.TemporaryDirectory() as runtime:
            store = EventStore(runtime)
            store.submit({"actor_id": "integrator", "idempotency_key": "campaign-bootstrap", "event_type": "campaign_bootstrapped", "payload": {"campaign_id": "pariprashna-experience-assurance-v3"}, "evidence": EVIDENCE})
            self.assertEqual(store.projection()["canonical"]["runtime_mode"], "CAMPAIGN")
            self.assertTrue(store.verify_replay()["ok"])

    def test_invalid_and_out_of_order_are_rejected_and_retained(self):
        with self.assertRaises(RejectedEvent) as invalid: self.emit("lead-s1", "work_item_accepted", {"work_item_id": "S1:charter"}, "S1")
        self.assertEqual(invalid.exception.code, "ROLE_FORBIDDEN")
        with self.assertRaises(RejectedEvent) as conflict: self.emit("lead-s1", "work_started", {"session_id": "bad", "planned_scenarios": 1}, "S1", seq=99)
        self.assertEqual(conflict.exception.code, "SEQUENCE_CONFLICT"); self.assertGreaterEqual(len(self.store.rejected()), 2)
        with self.assertRaises(RejectedEvent) as transition: self.emit("lead-s1", "paused", {}, "S1")
        self.assertEqual(transition.exception.code, "INVALID_TRANSITION")
        with self.assertRaises(RejectedEvent) as participants: self.emit("lead-s1", "work_started", {"session_id": "bad-participants", "planned_scenarios": 1, "participants": "not-a-list"}, "S1")
        self.assertEqual(participants.exception.code, "PARTICIPANT_ROSTER_INVALID")

    def test_participant_roster_is_registered_and_stream_eligible(self):
        valid = {"actor_id": "surrogate", "role": "NATIVE_SURROGATE", "state": "ACTIVE"}
        self.assertTrue(self.emit("lead-p0", "work_started", {"session_id": "p0-roster", "participants": [valid]}, "P0")["accepted"])
        with tempfile.TemporaryDirectory() as runtime:
            store = EventStore(runtime)
            store.submit({"actor_id": "integrator", "idempotency_key": "bootstrap", "event_type": "campaign_bootstrapped", "payload": {"campaign_id": "demo"}, "evidence": EVIDENCE})
            def submit(payload, key):
                return store.submit({"actor_id": "lead-s1", "idempotency_key": key, "event_type": "work_started", "payload": payload, "stream_id": "S1", "expected_stream_seq": 0, "evidence": EVIDENCE})
            with self.assertRaises(RejectedEvent) as fabricated:
                submit({"session_id": "fabricated", "planned_scenarios": 1, "participants": [{"actor_id": "invented-native", "role": "NATIVE", "state": "ACTIVE"}]}, "fabricated")
            self.assertEqual(fabricated.exception.code, "PARTICIPANT_ROSTER_UNVERIFIED")
            with self.assertRaises(RejectedEvent) as mismatch:
                submit({"session_id": "mismatch", "planned_scenarios": 1, "participants": [{"actor_id": "surrogate", "role": "NATIVE", "state": "ACTIVE"}]}, "mismatch")
            self.assertEqual(mismatch.exception.code, "PARTICIPANT_ROSTER_UNVERIFIED")
            with self.assertRaises(RejectedEvent) as wrong_stream:
                submit({"session_id": "wrong-stream", "planned_scenarios": 1, "participants": [{"actor_id": "lead-s2", "role": "STREAM_LEAD", "state": "ACTIVE"}]}, "wrong-stream")
            self.assertEqual(wrong_stream.exception.code, "PARTICIPANT_ROSTER_UNVERIFIED")
            with self.assertRaises(RejectedEvent) as missing_session:
                submit({"planned_scenarios": 1}, "missing-session")
            self.assertEqual(missing_session.exception.code, "SESSION_ID_REQUIRED")

    def test_each_phase_has_a_scoped_execution_lead(self):
        p1 = self.emit("lead-p1", "work_started", {"session_id": "p1-takeover", "assignment": "takeover reconciliation"}, "P1")
        self.assertTrue(p1["accepted"])
        self.store.record_presence("lead-p1", "p1-takeover", "P1", "ACTIVE")
        phase = next(phase for phase in self.store.projection()["canonical"]["phases"] if phase["id"] == "P1")
        self.assertEqual(phase["responsible_session"], "p1-takeover")
        liveness = self.store.projection()["liveness"]
        self.assertEqual([(dependency["from"], dependency["to"]) for dependency in liveness["dependency_warnings"]], [("P0", "P1")]); self.assertEqual(liveness["overall_health"], "ATTENTION_REQUIRED"); self.assertIn("UNRESOLVED ACTIVE DEPENDENCY", liveness["warning"])
        with self.assertRaises(RejectedEvent) as missing_evidence:
            self.emit("integrator", "dependency_resolved", {"from": "P0", "to": "P1"}, "P1", evidence=[])
        self.assertEqual(missing_evidence.exception.code, "EVIDENCE_REQUIRED")
        with self.assertRaises(RejectedEvent) as malformed_dependency:
            self.emit("integrator", "dependency_resolved", {"from": [], "to": "P1"}, "P1")
        self.assertEqual(malformed_dependency.exception.code, "DEPENDENCY_SCHEMA")
        self.emit("integrator", "dependency_resolved", {"from": "P0", "to": "P1"}, "P1")
        dependency = next(dependency for dependency in self.store.projection()["canonical"]["dependencies"] if (dependency["from"], dependency["to"]) == ("P0", "P1"))
        self.assertEqual(dependency["status"], "RESOLVED"); self.assertEqual(self.store.projection()["liveness"]["dependency_warnings"], [])
        with self.assertRaises(RejectedEvent) as duplicate_dependency:
            self.emit("integrator", "dependency_resolved", {"from": "P0", "to": "P1"}, "P1")
        self.assertEqual(duplicate_dependency.exception.code, "DEPENDENCY_ALREADY_RESOLVED")
        self.emit("lead-p1", "paused", {"reason": "phase control-plane fixture"}, "P1")
        paused = self.store.projection()
        self.assertEqual(next(phase for phase in paused["display"]["phases"] if phase["id"] == "P1")["health"], "ATTENTION_REQUIRED"); self.assertEqual(paused["liveness"]["overall_health"], "ATTENTION_REQUIRED")
        with self.assertRaises(RejectedEvent) as wrong_phase:
            self.emit("lead-p0", "work_started", {"session_id": "wrong-phase"}, "P1")
        self.assertEqual(wrong_phase.exception.code, "STREAM_FORBIDDEN")

    def test_control_events_are_bound_to_their_declared_target(self):
        self.emit("lead-s1", "work_started", {"session_id": "target-fixture", "planned_scenarios": 1}, "S1")
        misplaced_verification = self.emit("verifier", "verification_accepted", {"verification_id": "misplaced-item", "work_item_id": "S1:charter", "finder_actor_id": "lead-s1", "fixer_actor_id": "lead-s1"}, "S2")
        with self.assertRaises(RejectedEvent) as wrong_item_target:
            self.emit("integrator", "work_item_accepted", {"work_item_id": "S1:charter", "verification_event_id": misplaced_verification["event"]["event_id"]}, "S2")
        self.assertEqual(wrong_item_target.exception.code, "WORK_ITEM_TARGET")
        gate_verification = self.emit("verifier", "verification_accepted", {"verification_id": "misplaced-gate", "gate_id": "CG-0", "finder_actor_id": "lead-p0", "fixer_actor_id": "lead-p0"}, "P1")
        with self.assertRaises(RejectedEvent) as wrong_gate_target:
            self.emit("integrator", "gate_closed", {"gate_id": "CG-0", "verification_event_id": gate_verification["event"]["event_id"]}, "P1")
        self.assertEqual(wrong_gate_target.exception.code, "GATE_TARGET")
        with self.assertRaises(RejectedEvent) as wrong_packet_target:
            self.emit("integrator", "result_packet_accepted", {"stream_id": "S1"}, "S2")
        self.assertEqual(wrong_packet_target.exception.code, "RESULT_PACKET_TARGET")
        with self.assertRaises(RejectedEvent) as wrong_native_target:
            self.emit("native", "native_acceptance", {}, "P5")
        self.assertEqual(wrong_native_target.exception.code, "NATIVE_TARGET")

    def test_concurrent_stream_writers_retry_without_loss(self):
        self.emit("lead-s1", "work_started", {"session_id": "concurrent", "planned_scenarios": 12}, "S1")
        failures = []; accepted = []
        def write(i):
            for _ in range(100):
                try:
                    accepted.append(self.emit("lead-s1", "scenario_executed", {"scenario_id": f"x{i}"}, "S1", key=f"concurrent-{i}")); return
                except RejectedEvent as exc:
                    if exc.code != "SEQUENCE_CONFLICT": failures.append(exc); return
        threads = [threading.Thread(target=write, args=(i,)) for i in range(12)]
        [t.start() for t in threads]; [t.join() for t in threads]
        self.assertFalse(failures); self.assertEqual(len(accepted), 12); self.assertEqual(self.store.next_stream_seq("S1"), 13); self.assertTrue(self.store.verify_replay()["ok"])

    def test_stream_writer_cannot_write_another_stream(self):
        with self.assertRaises(RejectedEvent) as ctx: self.emit("lead-s1", "work_started", {"session_id": "no"}, "S2")
        self.assertEqual(ctx.exception.code, "STREAM_FORBIDDEN")

    def test_rebuild_and_presence_are_privilege_bound(self):
        self.emit("lead-s1", "work_started", {"session_id": "owned-session", "planned_scenarios": 1}, "S1")
        with self.assertRaises(RejectedEvent) as duplicate_session: self.emit("lead-s2", "work_started", {"session_id": "owned-session", "planned_scenarios": 1}, "S2")
        self.assertEqual(duplicate_session.exception.code, "SESSION_ID_CONFLICT")
        with self.assertRaises(RejectedEvent) as impersonation: self.store.record_presence("integrator", "owned-session", "S1", "ACTIVE")
        self.assertEqual(impersonation.exception.code, "PRESENCE_FORBIDDEN")
        with self.assertRaises(RejectedEvent) as unknown: self.store.record_presence("lead-s1", "unknown-session", "S1", "ACTIVE")
        self.assertEqual(unknown.exception.code, "UNKNOWN_SESSION")
        bus = EventBus(); httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler_factory(self.store, bus, TRACKER / "dashboard.html")); thread = threading.Thread(target=httpd.serve_forever, daemon=True); thread.start()
        def post(path, body, token):
            conn = http.client.HTTPConnection("127.0.0.1", httpd.server_port, timeout=2)
            conn.request("POST", path, body=json.dumps(body), headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
            response = conn.getresponse(); payload = json.loads(response.read()); status = response.status; conn.close(); return status, payload
        try:
            status, body = post("/api/rebuild", {}, self.tokens["lead-s1"]); self.assertEqual(status, 409); self.assertEqual(body["code"], "ROLE_FORBIDDEN")
            status, body = post("/api/rebuild", {}, self.tokens["integrator"]); self.assertEqual(status, 200); self.assertTrue(body["integrity"]["ok"])
            status, body = post("/api/presence", {"session_id": "owned-session", "stream_id": "S1", "state": "ACTIVE", "observed_at": "2020-01-01T00:00:00Z"}, self.tokens["lead-s1"]); self.assertEqual(status, 409); self.assertEqual(body["code"], "PRESENCE_TIMESTAMP_FORBIDDEN")
            status, body = post("/api/presence", {"session_id": "owned-session", "stream_id": "S1", "state": "ACTIVE"}, self.tokens["lead-s1"]); self.assertEqual(status, 201); self.assertTrue(body["accepted"])
        finally:
            httpd.shutdown(); thread.join(timeout=2); httpd.server_close()

    def test_finder_or_fixer_cannot_self_verify(self):
        with self.assertRaises(RejectedEvent) as ctx: self.emit("lead-s1", "verification_accepted", {"finder_actor_id": "lead-s1", "fixer_actor_id": "lead-s1"}, "S1")
        self.assertEqual(ctx.exception.code, "ROLE_FORBIDDEN")
        with self.assertRaises(RejectedEvent) as ctx: self.emit("verifier", "verification_accepted", {"finder_actor_id": "verifier", "fixer_actor_id": "lead-s1"}, "S1")
        self.assertEqual(ctx.exception.code, "SELF_VERIFICATION")

    def test_surrogate_cannot_close_native_gate(self):
        decision = self.emit("surrogate", "decision_recorded", {"decision": "ordinary UX choice"}, "S1")
        self.assertTrue(decision["accepted"]); self.assertIn("SURROGATE DECISION", self.store.projection()["canonical"]["decisions"][0]["label"])
        with self.assertRaises(RejectedEvent) as ctx: self.emit("surrogate", "gate_closed", {"gate_id": "CG-6"}, "P6")
        self.assertEqual(ctx.exception.code, "ROLE_FORBIDDEN")

    def test_running_presence_stales_but_paused_does_not(self):
        self.emit("lead-s1", "work_started", {"session_id": "live", "planned_scenarios": 1}, "S1")
        old = "2020-01-01T00:00:00Z"; self.store.record_presence("lead-s1", "live", "S1", "ACTIVE", observed_at=old)
        self.assertEqual(self.store.projection(as_of="2026-01-01T00:00:00Z")["display"]["streams"][0]["health"], "STALE")
        self.emit("lead-s1", "paused", {}, "S1"); p = self.store.projection(as_of="2026-01-01T00:00:00Z")
        self.assertEqual(p["display"]["streams"][0]["health"], "ATTENTION_REQUIRED")
        self.assertEqual(p["liveness"]["cells"][0]["health"], "ATTENTION_REQUIRED")

    def test_integrity_degraded_never_appears_green(self):
        with self.store.connection() as con: con.execute("UPDATE projection_state SET projection_hash='bad'")
        projection = self.store.projection(); self.assertFalse(projection["integrity"]["ok"]); self.assertTrue(all(s["health"] == "INTEGRITY_DEGRADED" for s in projection["display"]["streams"]))

    def test_projector_recovery_and_corruption_detection(self):
        with self.store.connection() as con: con.execute("DELETE FROM projection_state")
        self.assertTrue(self.store.projection()["integrity"]["ok"])
        with self.store.connection() as con: con.execute("UPDATE projection_state SET canonical_json='{}'")
        self.assertFalse(self.store.verify_replay()["ok"])
        degraded = self.store.projection(); self.assertEqual(degraded["display"]["streams"][0]["health"], "INTEGRITY_DEGRADED")
        self.store.rebuild(); self.assertTrue(self.store.verify_replay()["ok"])

    def test_periodic_replay_monitor_publishes_integrity_degradation(self):
        with self.store.connection() as con: con.execute("UPDATE projection_state SET canonical_json='{}'")
        bus = EventBus(); received = bus.subscribe(); monitor = ReplayMonitor(self.store, bus, 0.01); monitor.start()
        try:
            update = json.loads(received.get(timeout=1)); self.assertFalse(update["integrity"]["ok"])
            self.assertTrue(all(stream["health"] == "INTEGRITY_DEGRADED" for stream in update["display"]["streams"]))
        finally:
            monitor.stop(); monitor.join(timeout=1); bus.unsubscribe(received)

    def test_evidence_progress_and_no_heartbeat_credit(self):
        initial = self.store.projection()["canonical"]["completion"]["completion_pct"]; self.accepted_s1_item()
        self.assertGreater(self.store.projection()["canonical"]["completion"]["completion_pct"], initial)
        with self.assertRaises(RejectedEvent): self.emit("lead-s1", "heartbeat", {}, "S1", evidence=[])
        with self.assertRaises(RejectedEvent): self.emit("lead-s1", "scenario_executed", {"progress": 99}, "S1")

    def test_scenario_denominator_is_frozen(self):
        self.emit("lead-s1", "work_started", {"session_id": "scenario-contract", "planned_scenarios": 1}, "S1")
        self.assertTrue(self.emit("lead-s1", "scenario_executed", {"scenario_id": "happy-path"}, "S1")["accepted"])
        with self.assertRaises(RejectedEvent) as duplicate: self.emit("lead-s1", "scenario_executed", {"scenario_id": "happy-path"}, "S1")
        self.assertEqual(duplicate.exception.code, "DUPLICATE_SCENARIO")
        with self.assertRaises(RejectedEvent) as excess: self.emit("lead-s1", "scenario_executed", {"scenario_id": "second-path"}, "S1")
        self.assertEqual(excess.exception.code, "SCENARIO_DENOMINATOR_EXCEEDED")

    def test_remediation_plan_is_frozen_after_triage(self):
        self.emit("lead-s1", "work_started", {"session_id": "remediation-contract", "planned_scenarios": 1}, "S1")
        self.emit("lead-s1", "finding_discovered", {"finding_id": "finding-1", "severity": "HIGH", "root_cause_group": "contract"}, "S1")
        with self.assertRaises(RejectedEvent) as duplicate_finding:
            self.emit("lead-s1", "finding_discovered", {"finding_id": "finding-1", "severity": "HIGH"}, "S1")
        self.assertEqual(duplicate_finding.exception.code, "FINDING_ID_CONFLICT")
        with self.assertRaises(RejectedEvent) as untriaged:
            self.emit("surrogate", "remediation_approved", {"remediation_plan": [{"id": "fix-1", "finding_id": "finding-1"}]}, "S1")
        self.assertEqual(untriaged.exception.code, "TRIAGE_INCOMPLETE")
        self.emit("surrogate", "finding_triaged", {"finding_id": "finding-1", "severity": "HIGH"}, "S1")
        self.emit("surrogate", "remediation_approved", {"remediation_plan": [{"id": "fix-1", "finding_id": "finding-1"}]}, "S1")
        with self.assertRaises(RejectedEvent) as unplanned:
            self.emit("lead-s1", "remediation_implemented", {"remediation_id": "fix-2", "finding_id": "finding-1"}, "S1")
        self.assertEqual(unplanned.exception.code, "REMEDIATION_CONTRACT")
        self.emit("lead-s1", "remediation_implemented", {"remediation_id": "fix-1", "finding_id": "finding-1"}, "S1")
        with self.assertRaises(RejectedEvent) as missing_finding:
            self.emit("verifier", "verification_accepted", {"verification_id": "fix-1-missing", "remediation_id": "fix-1", "finder_actor_id": "lead-s1", "fixer_actor_id": "lead-s1"}, "S1")
        self.assertEqual(missing_finding.exception.code, "REMEDIATION_VERIFICATION_REFERENCE")
        with self.assertRaises(RejectedEvent) as wrong_stream:
            self.emit("verifier", "verification_accepted", {"verification_id": "fix-1-wrong-stream", "remediation_id": "fix-1", "finding_id": "finding-1", "finder_actor_id": "lead-s1", "fixer_actor_id": "lead-s1"}, "S2")
        self.assertEqual(wrong_stream.exception.code, "REMEDIATION_VERIFICATION_REFERENCE")
        verification = self.emit("verifier", "verification_accepted", {"verification_id": "fix-1-verified", "remediation_id": "fix-1", "finding_id": "finding-1", "finder_actor_id": "lead-s1", "fixer_actor_id": "lead-s1"}, "S1")
        self.assertTrue(verification["accepted"])
        stream = next(stream for stream in self.store.projection()["canonical"]["streams"] if stream["id"] == "S1")
        self.assertEqual(stream["remediations"], {"planned": 1, "implemented": 1, "verified": 1})
        with self.assertRaises(RejectedEvent) as refreeze:
            self.emit("surrogate", "remediation_approved", {"remediation_plan": [{"id": "fix-1", "finding_id": "finding-1"}]}, "S1")
        self.assertEqual(refreeze.exception.code, "REMEDIATION_PLAN_LOCKED")
        with self.assertRaises(RejectedEvent) as late_finding:
            self.emit("lead-s1", "finding_discovered", {"finding_id": "finding-2", "severity": "LOW"}, "S1")
        self.assertEqual(late_finding.exception.code, "FINDING_FREEZE")

        with tempfile.TemporaryDirectory() as runtime:
            store = EventStore(runtime)
            store.submit({"actor_id": "integrator", "idempotency_key": "bootstrap", "event_type": "campaign_bootstrapped", "payload": {"campaign_id": "demo"}, "evidence": EVIDENCE})
            store.submit({"actor_id": "lead-s1", "idempotency_key": "start", "event_type": "work_started", "payload": {"session_id": "no-remediation-plan", "planned_scenarios": 1}, "stream_id": "S1", "expected_stream_seq": 0, "evidence": EVIDENCE})
            for stage in ("charter", "baseline", "triage"):
                verification = store.submit({"actor_id": "verifier", "idempotency_key": f"verify-{stage}", "event_type": "verification_accepted", "payload": {"verification_id": stage, "work_item_id": f"S1:{stage}", "finder_actor_id": "lead-s1", "fixer_actor_id": "lead-s1"}, "stream_id": "S1", "expected_stream_seq": store.next_stream_seq("S1"), "evidence": EVIDENCE})
                store.submit({"actor_id": "integrator", "idempotency_key": f"accept-{stage}", "event_type": "work_item_accepted", "payload": {"work_item_id": f"S1:{stage}", "verification_event_id": verification["event"]["event_id"]}, "stream_id": "S1", "expected_stream_seq": store.next_stream_seq("S1"), "evidence": EVIDENCE})
            verification = store.submit({"actor_id": "verifier", "idempotency_key": "verify-remediation", "event_type": "verification_accepted", "payload": {"verification_id": "remediation", "work_item_id": "S1:remediation", "finder_actor_id": "lead-s1", "fixer_actor_id": "lead-s1"}, "stream_id": "S1", "expected_stream_seq": store.next_stream_seq("S1"), "evidence": EVIDENCE})
            with self.assertRaises(RejectedEvent) as missing_plan:
                store.submit({"actor_id": "integrator", "idempotency_key": "accept-remediation", "event_type": "work_item_accepted", "payload": {"work_item_id": "S1:remediation", "verification_event_id": verification["event"]["event_id"]}, "stream_id": "S1", "expected_stream_seq": store.next_stream_seq("S1"), "evidence": EVIDENCE})
            self.assertEqual(missing_plan.exception.code, "REMEDIATION_PLAN_REQUIRED")

    def test_regression_requires_scenarios_and_completed_session_is_not_stale(self):
        self.emit("lead-s1", "work_started", {"session_id": "full-stream", "planned_scenarios": 1}, "S1")
        self.emit("surrogate", "remediation_approved", {"remediation_plan": []}, "S1")
        def accept(stage):
            verification = self.emit("verifier", "verification_accepted", {"verification_id": f"verify-{stage}", "work_item_id": f"S1:{stage}", "finder_actor_id": "lead-s1", "fixer_actor_id": "lead-s1"}, "S1")
            return self.emit("integrator", "work_item_accepted", {"work_item_id": f"S1:{stage}", "verification_event_id": verification["event"]["event_id"]}, "S1")
        for stage in ("charter", "baseline", "triage", "remediation", "verification"): accept(stage)
        with self.assertRaises(RejectedEvent) as incomplete: accept("regression")
        self.assertEqual(incomplete.exception.code, "REGRESSION_INCOMPLETE")
        self.emit("lead-s1", "scenario_executed", {"scenario_id": "all-chartered-work"}, "S1")
        self.emit("integrator", "scope_change_approved", {"reason": "approved extra regression scenario", "added_work_items": [{"id": "S1:scope-regression", "phase_id": "P3", "stream_id": "S1", "title": "scope regression", "campaign_points": 1}], "added_scenarios": [{"id": "scope-regression-scenario", "stream_id": "S1"}]}, "P3")
        with self.assertRaises(RejectedEvent) as scoped_incomplete: accept("regression")
        self.assertEqual(scoped_incomplete.exception.code, "REGRESSION_INCOMPLETE")
        self.emit("lead-s1", "scenario_executed", {"scenario_id": "scope-regression-scenario"}, "S1")
        accept("regression")
        with self.assertRaises(RejectedEvent) as direct_closure: accept("closure")
        self.assertEqual(direct_closure.exception.code, "RESULT_PACKET_REQUIRED")
        scope_verification = self.emit("verifier", "verification_accepted", {"verification_id": "verify-scope-regression", "work_item_id": "S1:scope-regression", "finder_actor_id": "lead-s1", "fixer_actor_id": "lead-s1"}, "S1")
        self.emit("integrator", "work_item_accepted", {"work_item_id": "S1:scope-regression", "verification_event_id": scope_verification["event"]["event_id"]}, "S1")
        self.emit("verifier", "stream_closure_recommended", {"finder_actor_id": "lead-s1"}, "S1")
        self.emit("integrator", "result_packet_accepted", {"stream_id": "S1"}, "S1")
        projection = self.store.projection(); stream = next(s for s in projection["display"]["streams"] if s["id"] == "S1")
        cell = next(cell for cell in projection["liveness"]["cells"] if cell["stream_id"] == "S1")
        self.assertEqual(stream["scenarios"], {"planned": 2, "executed": 2}); self.assertEqual(stream["lifecycle"], "COMPLETE"); self.assertEqual(cell["health"], "UNKNOWN")

    def test_failed_stream_cannot_receive_packet_closure_credit(self):
        self.emit("lead-s1", "work_started", {"session_id": "failed-before-packet", "planned_scenarios": 1}, "S1")
        self.emit("surrogate", "remediation_approved", {"remediation_plan": []}, "S1")
        self.emit("lead-s1", "scenario_executed", {"scenario_id": "required"}, "S1")
        for stage in ("charter", "baseline", "triage", "remediation", "verification", "regression"):
            verification = self.emit("verifier", "verification_accepted", {"verification_id": f"failed-{stage}", "work_item_id": f"S1:{stage}", "finder_actor_id": "lead-s1", "fixer_actor_id": "lead-s1"}, "S1")
            self.emit("integrator", "work_item_accepted", {"work_item_id": f"S1:{stage}", "verification_event_id": verification["event"]["event_id"]}, "S1")
        self.emit("lead-s1", "failed", {"reason": "adversarial terminal failure"}, "S1")
        with self.assertRaises(RejectedEvent) as packet: self.emit("integrator", "result_packet_accepted", {"stream_id": "S1"}, "S1")
        self.assertEqual(packet.exception.code, "FAILED_STREAM")
        stream = next(stream for stream in self.store.projection()["canonical"]["streams"] if stream["id"] == "S1")
        self.assertEqual(stream["lifecycle"], "FAILED"); self.assertFalse(next(item for item in self.store.projection()["canonical"]["work_items"] if item["id"] == "S1:closure")["accepted"])

    def test_execution_session_projection_exposes_governance_fields(self):
        self.accepted_s1_item(); projection = self.store.projection()
        stream = next(s for s in projection["canonical"]["streams"] if s["id"] == "S1")
        self.assertEqual(stream["scenarios"], {"planned": 12, "executed": 0}); self.assertEqual(stream["lifecycle_stage"]["id"], "baseline")
        self.assertEqual(stream["execution_session"]["model"], "test-model"); self.assertEqual(stream["execution_session"]["reasoning_config"], "test")
        cell = projection["liveness"]["cells"][0]
        self.assertEqual(cell["conversation_id"], "s1"); self.assertIn("elapsed_seconds", cell); self.assertIn("last_presence_at", cell); self.assertEqual(cell["cost"], {"amount": 125000, "currency": "INR", "basis": "approved ceiling"}); self.assertEqual(cell["participants"][1]["actor_id"], "a11y-specialist")

    def test_scope_change_is_only_denominator_expansion_and_explains_drop(self):
        self.accepted_s1_item(); before = self.store.projection()["canonical"]["completion"]["planned_campaign_points"]
        self.emit("integrator", "scope_change_approved", {"reason": "approved new regression scenario", "added_work_items": [{"id": "S1:extra", "phase_id": "P3", "stream_id": "S1", "title": "extra", "campaign_points": 1}]}, "P3")
        after = self.store.projection()["canonical"]; self.assertGreater(after["completion"]["planned_campaign_points"], before); self.assertEqual(after["scope_changes"][0]["reason"], "approved new regression scenario"); self.assertGreater(after["scope_changes"][0]["completion_before_pct"], after["scope_changes"][0]["completion_after_pct"])
        verification = self.emit("verifier", "verification_accepted", {"verification_id": "extra-verification", "work_item_id": "S1:extra", "finder_actor_id": "lead-s1", "fixer_actor_id": "lead-s1"}, "S1")
        self.assertTrue(self.emit("integrator", "work_item_accepted", {"work_item_id": "S1:extra", "verification_event_id": verification["event"]["event_id"]}, "S1")["accepted"])
        with self.assertRaises(RejectedEvent) as duplicate: self.emit("integrator", "scope_change_approved", {"reason": "duplicate", "added_work_items": [{"id": "S1:extra", "phase_id": "P3", "title": "duplicate", "campaign_points": 1}]}, "P3")
        self.assertEqual(duplicate.exception.code, "SCOPE_CHANGE_SCHEMA")

    def test_gate_closure_requires_evidence_and_integrator(self):
        with self.assertRaises(RejectedEvent) as ctx: self.emit("integrator", "gate_closed", {"gate_id": "CG-0"}, "P0", evidence=[])
        self.assertEqual(ctx.exception.code, "EVIDENCE_REQUIRED")
        with self.assertRaises(RejectedEvent) as ctx: self.emit("integrator", "gate_closed", {"gate_id": "CG-0"}, "P0")
        self.assertEqual(ctx.exception.code, "VERIFICATION_REQUIRED")
        premature = self.emit("verifier", "verification_accepted", {"verification_id": "premature-cg0", "gate_id": "CG-0", "finder_actor_id": "lead-p0", "fixer_actor_id": "lead-p0"}, "P0")
        with self.assertRaises(RejectedEvent) as ctx: self.emit("integrator", "gate_closed", {"gate_id": "CG-0", "verification_event_id": premature["event"]["event_id"]}, "P0")
        self.assertEqual(ctx.exception.code, "GATE_PREREQUISITE")
        item_verification = self.emit("verifier", "verification_accepted", {"verification_id": "p0-item", "work_item_id": "P0:completion", "finder_actor_id": "lead-p0", "fixer_actor_id": "lead-p0"}, "P0")
        self.emit("integrator", "work_item_accepted", {"work_item_id": "P0:completion", "verification_event_id": item_verification["event"]["event_id"]}, "P0")
        verification = self.emit("verifier", "verification_accepted", {"verification_id": "cg0-verification", "gate_id": "CG-0", "finder_actor_id": "lead-p0", "fixer_actor_id": "lead-p0"}, "P0")
        self.assertTrue(self.emit("integrator", "gate_closed", {"gate_id": "CG-0", "verification_event_id": verification["event"]["event_id"]}, "P0")["accepted"])

    def test_append_only_and_corrections(self):
        with self.store.connection() as con:
            with self.assertRaises(Exception): con.execute("DELETE FROM events")
        bootstrap_id = self.store.events()[0]["event_id"]
        self.assertTrue(self.emit("lead-s1", "correction_recorded", {"corrects_event_id": bootstrap_id, "reason": "new evidence"}, "S1", evidence=[])["accepted"])
        with self.assertRaises(RejectedEvent) as missing: self.emit("lead-s1", "correction_recorded", {"corrects_event_id": "missing", "reason": "bad reference"}, "S1", evidence=[])
        self.assertEqual(missing.exception.code, "CORRECTION_REFERENCE_REQUIRED")

    def test_snapshot_export_reconciles(self):
        path = Path(self.tmp.name) / "snap.json"; receipt = self.store.export_snapshot(path)
        snapshot = json.loads(path.read_text()); self.assertEqual(receipt["event_log_hash"], snapshot["event_log_hash"]); self.assertEqual(path.stat().st_mode & 0o777, 0o400)
        self.assertEqual(snapshot["event_log_hash"], digest(snapshot["events"]))

    def test_snapshot_export_never_overwrites_or_replaces_runtime_files(self):
        existing = Path(self.tmp.name) / "existing.snapshot.json"; existing.write_text("original\n")
        with self.assertRaises(RejectedEvent) as collision:
            self.store.export_snapshot(existing)
        self.assertEqual(collision.exception.code, "SNAPSHOT_TARGET_EXISTS")
        self.assertEqual(existing.read_text(), "original\n")
        with self.assertRaises(RejectedEvent) as protected:
            self.store.export_snapshot(self.store.db_path)
        self.assertEqual(protected.exception.code, "SNAPSHOT_PATH_FORBIDDEN")
        self.assertTrue(self.store.verify_replay()["ok"])

    def test_snapshot_export_remains_reconcilable_under_concurrent_writes(self):
        self.emit("lead-s1", "work_started", {"session_id": "concurrent-snapshot", "planned_scenarios": 30}, "S1")
        failures = []
        peer = EventStore(self.tmp.name)
        def writer():
            for index in range(20):
                try:
                    peer.submit({"actor_id": "lead-s1", "idempotency_key": f"concurrent-snapshot-{index}", "event_type": "scenario_executed", "payload": {"scenario_id": f"concurrent-snapshot-{index}"}, "stream_id": "S1", "expected_stream_seq": peer.next_stream_seq("S1"), "evidence": EVIDENCE})
                except Exception as exc:  # pragma: no cover - asserted below
                    failures.append(exc)
        thread = threading.Thread(target=writer); thread.start()
        successful_exports = 0
        with tempfile.TemporaryDirectory() as root:
            for index in range(12):
                snapshot_path = Path(root) / f"snapshot-{index}.json"
                try:
                    self.store.export_snapshot(snapshot_path)
                except RejectedEvent as exc:
                    self.assertEqual(exc.code, "INTEGRITY_DEGRADED")
                    continue
                snapshot = json.loads(snapshot_path.read_text())
                recovery = EventStore(Path(root) / f"recovery-{index}")
                restored = recovery.restore_snapshot(snapshot_path)
                self.assertEqual(restored["event_log_hash"], snapshot["event_log_hash"])
                self.assertTrue(recovery.verify_replay()["ok"])
                successful_exports += 1
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive()); self.assertFalse(failures); self.assertGreater(successful_exports, 0)

    def test_unstarted_campaign_liveness_is_unknown(self):
        projection = self.store.projection()
        self.assertTrue(all(health == "UNKNOWN" for health in projection["liveness"]["stream_health"].values()))
        self.assertEqual(projection["liveness"]["overall_health"], "UNKNOWN")

    def test_hostile_host_cannot_read_loopback_endpoints(self):
        bus = EventBus(); httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler_factory(self.store, bus, TRACKER / "dashboard.html")); thread = threading.Thread(target=httpd.serve_forever, daemon=True); thread.start()
        def get(path, host):
            conn = http.client.HTTPConnection("127.0.0.1", httpd.server_port, timeout=2)
            conn.request("GET", path, headers={"Host": host}); response = conn.getresponse(); body = response.read(); status = response.status; conn.close(); return status, body
        try:
            self.assertEqual(get("/", "evil.example")[0], 403)
            self.assertEqual(get("/api/projection", "evil.example")[0], 403)
            self.assertEqual(get("/", f"127.0.0.1:{httpd.server_port}")[0], 200)
        finally:
            httpd.shutdown(); thread.join(timeout=2); httpd.server_close()

    @staticmethod
    def _git(repo: Path, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
        return result.stdout.strip()

    def _approved_release_fixture(self, root: Path) -> tuple[Path, Path, str, Path]:
        source = root / "source"; source.mkdir()
        self._git(source, "init", "-b", "main")
        self._git(source, "config", "user.email", "test@example.invalid")
        self._git(source, "config", "user.name", "Tracker Test")
        tracker = source / "00_ARCHITECTURE/briefs/pariprashna_assurance/tracker"; tracker.mkdir(parents=True)
        for name in RELEASE_FILES:
            (tracker / name).write_text(f"approved:{name}\n")
        self._git(source, "add", "00_ARCHITECTURE")
        self._git(source, "commit", "-m", "approved tracker release")
        source_sha = self._git(source, "rev-parse", "HEAD")
        remote = root / "origin.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, text=True)
        self._git(source, "remote", "add", "origin", str(remote))
        self._git(source, "push", "-u", "origin", "main")
        self._git(source, "fetch", "origin", "main")
        self._git(source, "remote", "set-url", "origin", CANONICAL_MADHAV_ORIGIN)
        release_parent = root / "release-parent"; release_parent.mkdir()
        release = release_parent / "release"; release.mkdir()
        for name in RELEASE_FILES:
            (release / name).write_bytes((tracker / name).read_bytes())
        return source, release, source_sha, remote

    def test_release_attestation_requires_approved_merged_source_and_immutable_tree(self):
        with tempfile.TemporaryDirectory() as root:
            source, release, source_sha, local_remote = self._approved_release_fixture(Path(root))
            real_run = subprocess.run
            canonical_source = str(source.resolve())
            def fresh_remote(command, *args, **kwargs):
                if "ls-remote" in command and CANONICAL_MADHAV_ORIGIN in command:
                    return subprocess.CompletedProcess(command, 0, f"{source_sha}\trefs/heads/main\n", "")
                if "fetch" in command and CANONICAL_MADHAV_ORIGIN in command:
                    bare = command[command.index("-C") + 1]
                    return real_run(["git", "-C", bare, "fetch", "--quiet", str(local_remote), "refs/heads/main:refs/heads/verified-origin-main"], check=False, capture_output=True, text=True)
                return real_run(command, *args, **kwargs)
            self._git(source, "remote", "set-url", "origin", str(local_remote))
            with self.assertRaises(ValueError) as untrusted_origin:
                attest_release(release, source_sha, source)
            self.assertIn("canonical Marsys-Technologies/Madhav", str(untrusted_origin.exception))
            self._git(source, "remote", "set-url", "origin", CANONICAL_MADHAV_ORIGIN)
            self._git(source, "config", f"url.{local_remote}.insteadOf", CANONICAL_MADHAV_ORIGIN)
            with self.assertRaises(ValueError) as rewritten_origin:
                attest_release(release, source_sha, source)
            self.assertIn("forbidden Git URL rewrite", str(rewritten_origin.exception))
            self._git(source, "config", "--unset-all", f"url.{local_remote}.insteadOf")
            self._git(source, "config", f"http.{CANONICAL_MADHAV_ORIGIN}.proxy", "http://127.0.0.1:9")
            self._git(source, "config", f"http.{CANONICAL_MADHAV_ORIGIN}.sslVerify", "false")
            (release / "server.py").write_text("arbitrary fixture content\n")
            with patch("service.subprocess.run", side_effect=fresh_remote):
                with self.assertRaises(ValueError) as arbitrary:
                    attest_release(release, source_sha, source)
                self.assertIn("does not match", str(arbitrary.exception))
                (release / "server.py").write_bytes((source / "00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/server.py").read_bytes())
                def stale_remote(command, *args, **kwargs):
                    if "ls-remote" in command and CANONICAL_MADHAV_ORIGIN in command:
                        return subprocess.CompletedProcess(command, 0, f"{'b' * 40}\trefs/heads/main\n", "")
                    if "fetch" in command and CANONICAL_MADHAV_ORIGIN in command:
                        bare = command[command.index("-C") + 1]
                        return real_run(["git", "-C", bare, "fetch", "--quiet", str(local_remote), "refs/heads/main:refs/heads/verified-origin-main"], check=False, capture_output=True, text=True)
                    return real_run(command, *args, **kwargs)
                with patch("service.subprocess.run", side_effect=stale_remote):
                    with self.assertRaises(ValueError) as stale_tip:
                        attest_release(release, source_sha, source)
                self.assertIn("does not match the freshly authenticated", str(stale_tip.exception))
                with self.assertRaises(ValueError) as missing_sha:
                    attest_release(release, "a" * 40, source)
                self.assertIn("not an immutable commit", str(missing_sha.exception))
                (source / "00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/README.md").write_text("unmerged source\n")
                self._git(source, "add", "00_ARCHITECTURE")
                self._git(source, "commit", "-m", "unmerged source")
                unmerged_sha = self._git(source, "rev-parse", "HEAD")
                with self.assertRaises(ValueError) as unmerged:
                    attest_release(release, unmerged_sha, source)
                self.assertIn("not an immutable commit", str(unmerged.exception))
                intermediate = Path(root) / "linked-parent"; intermediate.symlink_to(release.parent, target_is_directory=True)
                with self.assertRaises(ValueError) as symlink_component:
                    attest_release(intermediate / "release", source_sha, source)
                self.assertIn("symlinked component", str(symlink_component.exception))
                manifest = attest_release(release, source_sha, source)
            self.assertEqual(manifest.stat().st_mode & 0o777, 0o444)
            canonical_release = assert_release_attestation(release, source_sha)
            plist = plistlib.loads(build_launchd_plist(canonical_release, Path("/private/runtime")))
            self.assertEqual(plist["ProgramArguments"][1], str(release.resolve() / "server.py"))
            os.chmod(release, 0o755)
            manifest_body = json.loads(manifest.read_text()); manifest_body["origin_remote"] = "file:///attacker/Madhav.git"
            os.chmod(manifest, 0o600); manifest.write_text(json.dumps(manifest_body)); os.chmod(manifest, 0o444); os.chmod(release, 0o555)
            with self.assertRaises(ValueError) as forged_origin:
                assert_release_attestation(release, source_sha)
            self.assertIn("does not attest", str(forged_origin.exception))
            os.chmod(release, 0o755)
            with self.assertRaises(ValueError) as mutable:
                assert_release_attestation(release, source_sha)
            self.assertIn("mutable", str(mutable.exception))
            os.chmod(release, 0o555)
            link = Path(root) / "release-link"; link.symlink_to(release, target_is_directory=True)
            with self.assertRaises(ValueError) as symlink:
                assert_release_attestation(link, source_sha)
            self.assertIn("symlink", str(symlink.exception))

    def test_external_adapter_failure_is_visible_not_canonical(self):
        before = self.store.projection()["canonical_hash"]; adapter = adapter_health()
        self.assertEqual(adapter["github"]["health"], "UNKNOWN"); self.assertTrue(adapter["canonical_state_unchanged"]); self.assertEqual(before, self.store.projection()["canonical_hash"])

    def test_every_lifecycle_and_health_has_a_fixture_surface(self):
        self.assertEqual({"NOT_STARTED", "READY", "RUNNING", "BLOCKED", "PAUSED", "IN_VERIFICATION", "COMPLETE", "FAILED"}, __import__("control").LIFECYCLES)
        self.assertEqual({"HEALTHY", "ATTENTION_REQUIRED", "STALE", "INTEGRITY_DEGRADED", "UNKNOWN"}, __import__("control").HEALTH)
        self.emit("lead-s1", "work_started", {"session_id": "lifecycle-fixture", "planned_scenarios": 1}, "S1")
        self.emit("lead-s1", "verification_started", {}, "S1"); self.assertEqual(next(s for s in self.store.projection()["canonical"]["streams"] if s["id"] == "S1")["lifecycle"], "IN_VERIFICATION")
        self.emit("lead-s1", "failed", {}, "S1"); self.assertEqual(next(s for s in self.store.projection()["canonical"]["streams"] if s["id"] == "S1")["lifecycle"], "FAILED")

    def test_sse_update_and_dashboard_accessibility_contract(self):
        bus = EventBus(); httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler_factory(self.store, bus, TRACKER / "dashboard.html")); thread = threading.Thread(target=httpd.serve_forever, daemon=True); thread.start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", httpd.server_port, timeout=2); conn.request("GET", "/events"); response = conn.getresponse(); self.assertEqual(response.status, 200); self.assertIn(b"event: projection", response.fp.readline()); response.fp.readline(); response.fp.readline()
            payload = json.dumps({"idempotency_key": "sse-live-update", "event_type": "work_started", "payload": {"session_id": "sse-session", "planned_scenarios": 1}, "stream_id": "S1", "expected_stream_seq": 0, "evidence": EVIDENCE}).encode()
            writer = http.client.HTTPConnection("127.0.0.1", httpd.server_port, timeout=2); started = time.monotonic(); writer.request("POST", "/api/events", body=payload, headers={"Authorization": f"Bearer {self.tokens['lead-s1']}", "Content-Type": "application/json"}); self.assertEqual(writer.getresponse().status, 201)
            self.assertIn(b"event: projection", response.fp.readline()); self.assertLess(time.monotonic() - started, 1.0); writer.close(); conn.close()
        finally: httpd.shutdown(); thread.join(timeout=2); httpd.server_close()
        html = (TRACKER / "dashboard.html").read_text(); self.assertIn("EventSource", html); self.assertIn("service_health==='UNKNOWN'", html); self.assertIn("@media", html); self.assertIn("aria-label", html); self.assertIn("Tracker Integrity and Audit", html); self.assertIn("blockedStreams", html); self.assertIn("location.protocol==='file:'", html); self.assertIn("start the local control plane", html); self.assertIn("SYNTHETIC DEMONSTRATION", html); self.assertIn("Cost not reported", html); self.assertIn("No participant roster reported", html); self.assertIn("triage-frozen remediations verified", html); self.assertIn("dependency_warnings", html); self.assertIn("safeUri", html); self.assertIn("dashboardMarkup", html)


if __name__ == "__main__": unittest.main(verbosity=2)
