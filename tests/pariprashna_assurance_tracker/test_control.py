import http.client
import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

TRACKER = Path(__file__).parents[2] / "00_ARCHITECTURE/briefs/pariprashna_assurance/tracker"
sys.path.insert(0, str(TRACKER))
from control import EventStore, RejectedEvent, fold, programme_definition, presence_overlay  # noqa: E402
from server import EventBus, ReplayMonitor, handler_factory, adapter_health, seed_empty_demo_runtime  # noqa: E402
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
        self.emit("lead-s1", "work_started", {"session_id": "s1", "assignment": "baseline", "branch": "b", "worktree": "w", "baseline_sha": "a", "current_sha": "a", "verifier": "verifier", "model": "test-model", "reasoning_config": "test", "cost": {"amount": 125000, "currency": "INR", "basis": "approved ceiling"}, "planned_scenarios": 12}, "S1")
        verify = self.emit("verifier", "verification_accepted", {"verification_id": "v1", "work_item_id": "S1:charter", "finder_actor_id": "lead-s1", "fixer_actor_id": "lead-s1"}, "S1")
        self.emit("integrator", "work_item_accepted", {"work_item_id": "S1:charter", "verification_event_id": verify["event"]["event_id"]}, "S1")

    def test_replay_hash_is_identical(self):
        self.accepted_s1_item(); before = self.store.projection()["canonical_hash"]
        self.assertTrue(self.store.verify_replay()["ok"]); self.store.rebuild(self.store.projection()["projection_as_of"])
        self.assertEqual(before, self.store.projection()["canonical_hash"])

    def test_duplicate_idempotency_returns_original(self):
        request = {"actor_id": "lead-s1", "idempotency_key": "same", "event_type": "work_started", "payload": {"session_id": "same", "planned_scenarios": 1}, "stream_id": "S1", "expected_stream_seq": 0, "evidence": EVIDENCE}
        first = self.store.submit(request); second = self.store.submit(request)
        self.assertFalse(first["idempotent"]); self.assertTrue(second["idempotent"]); self.assertEqual(len(self.store.events()), 2)

    def test_runtime_credentials_are_random_private_and_not_reprovisioned(self):
        self.assertIsNone(self.store.authenticate("local-integrator")); self.assertEqual(self.store.authenticate(self.tokens["integrator"]), "integrator")
        credential_file = Path(self.tmp.name) / "local-credentials.json"; self.assertFalse(credential_file.stat().st_mode & 0o077)
        with self.assertRaises(RejectedEvent) as ctx: self.store.provision_local_credentials()
        self.assertEqual(ctx.exception.code, "CREDENTIALS_EXIST")

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

    def test_regression_requires_scenarios_and_completed_session_is_not_stale(self):
        self.emit("lead-s1", "work_started", {"session_id": "full-stream", "planned_scenarios": 1}, "S1")
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
        self.assertEqual(cell["conversation_id"], "s1"); self.assertIn("elapsed_seconds", cell); self.assertIn("last_presence_at", cell); self.assertEqual(cell["cost"], {"amount": 125000, "currency": "INR", "basis": "approved ceiling"})

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
        snapshot = json.loads(path.read_text()); self.assertEqual(receipt["event_log_hash"], snapshot["event_log_hash"]); self.assertFalse(path.stat().st_mode & 0o222)

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
        html = (TRACKER / "dashboard.html").read_text(); self.assertIn("EventSource", html); self.assertIn("@media", html); self.assertIn("aria-label", html); self.assertIn("Tracker Integrity and Audit", html); self.assertIn("blockedStreams", html); self.assertIn("location.protocol==='file:'", html); self.assertIn("start the local control plane", html); self.assertIn("SYNTHETIC DEMONSTRATION", html); self.assertIn("Cost not reported", html); self.assertIn("safeUri", html); self.assertIn("dashboardMarkup", html)


if __name__ == "__main__": unittest.main(verbosity=2)
