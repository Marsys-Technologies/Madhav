"""Single-writer-lease coverage for the `cli.py` direct-EventStore write path (lane A3).

Background — the gap this file exists to detect
-----------------------------------------------
`server.py` exposes `POST /api/events`; `cli.py` instantiates `EventStore` directly and
never touches the HTTP process at all.  If the `writer_instance_id` single-writer lease
(and the numeric-slot dedup guard) were enforced *in the request handler*, `cli.py` would
be a silent bypass: a second, unaware session could record scenario executions against a
stream whose lease another live writer holds, which is exactly the S5 concurrency incident
(D-127-class collision) the lease was introduced to prevent.

They are not.  Enforcement lives in the shared `EventStore` (`control.py`) and is backed by
the `stream_scenario_write_leases` SQLite table, so every caller — HTTP handler, CLI, or a
future writer nobody has written yet — inherits it.  Nothing in the existing suite proved
that at the CLI boundary, though: every prior lease test drives `EventStore.submit()`
in-process.  Per CLAUDE.md §N.8 (Earned-Signal Principle), a property that holds only "by
construction", with no detector that could ever read false, is not an earned signal.  These
tests are that detector.

Every test here runs `cli.py` as a genuinely separate OS process against an isolated
temporary runtime.  Cross-process rejection is only possible if the lease is DB-backed —
the in-process `threading.RLock` in `EventStore` cannot span processes — so a passing run is
positive evidence for the shared-enforcement claim, not merely absence of a counterexample.

No test in this file touches the live control-plane runtime or the live 8787 service.
"""

import http.client
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

TRACKER = Path(__file__).parents[2] / "00_ARCHITECTURE/briefs/pariprashna_assurance/tracker"
sys.path.insert(0, str(TRACKER))
from control import EventStore, RejectedEvent  # noqa: E402
from server import EventBus, handler_factory  # noqa: E402

EVIDENCE = [{"kind": "test-artifact", "uri": "file://evidence/a3-cli-lease.json"}]
PLANNED_SCENARIOS = 6


class CliWriterLeaseTests(unittest.TestCase):
    """`cli.py`'s direct-EventStore path must obey the same single-writer lease as HTTP."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.runtime = Path(self.tmp.name) / "runtime"
        self.store = EventStore(self.runtime)
        credentials = self.store.provision_local_credentials()
        self.tokens = json.loads(Path(credentials["path"]).read_text(encoding="utf-8"))["tokens"]
        self.store.submit({"actor_id": "integrator", "idempotency_key": "bootstrap", "event_type": "campaign_bootstrapped", "payload": {"campaign_id": "a3-cli-lease"}, "evidence": EVIDENCE})
        self.store.submit({"actor_id": "lead-s1", "idempotency_key": "s1-charter", "event_type": "work_started", "payload": {"session_id": "a3-cli-lease-session", "assignment": "A3 cli lease coverage", "planned_scenarios": PLANNED_SCENARIOS}, "stream_id": "S1", "expected_stream_seq": self.store.next_stream_seq("S1"), "evidence": EVIDENCE})

    # ---- helpers -------------------------------------------------------------------

    def cli(self, *arguments: str) -> subprocess.CompletedProcess:
        """Run `cli.py` in a genuinely separate OS process against the same runtime."""
        return subprocess.run(
            [sys.executable, str(TRACKER / "cli.py"), "--runtime", str(self.runtime), *arguments],
            cwd=str(TRACKER), capture_output=True, text=True, timeout=120,
        )

    def cli_scenario(self, key: str, scenario_id: str, *, writer: str | None, seq: int | None = None) -> subprocess.CompletedProcess:
        arguments = [
            "emit", "--actor", "lead-s1", "--token", self.tokens["lead-s1"],
            "--key", key, "--type", "scenario_executed", "--stream", "S1",
            "--expected-seq", str(self.store.next_stream_seq("S1") if seq is None else seq),
            "--payload", json.dumps({"scenario_id": scenario_id}),
            "--evidence", json.dumps(EVIDENCE),
        ]
        if writer is not None:
            arguments += ["--writer-instance-id", writer]
        return self.cli(*arguments)

    def cli_result(self, completed: subprocess.CompletedProcess) -> dict:
        self.assertTrue(completed.stdout.strip(), f"cli.py produced no stdout; stderr={completed.stderr}")
        return json.loads(completed.stdout)

    def scenario_writes(self) -> list[dict]:
        return [
            {"scenario_id": event["payload"].get("scenario_id"), "writer_instance_id": event["payload"].get("writer_instance_id")}
            for event in self.store.events()
            if event["event_type"] == "scenario_executed"
        ]

    def http_scenario(self, port: int, key: str, scenario_id: str, writer: str) -> tuple[int, dict]:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            body = json.dumps({
                "idempotency_key": key, "event_type": "scenario_executed", "stream_id": "S1",
                "expected_stream_seq": self.store.next_stream_seq("S1"),
                "writer_instance_id": writer, "payload": {"scenario_id": scenario_id}, "evidence": EVIDENCE,
            })
            connection.request("POST", "/api/events", body, {"Authorization": f"Bearer {self.tokens['lead-s1']}", "Content-Type": "application/json", "Host": f"127.0.0.1:{port}"})
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    # ---- the reproduction the A3 lane was opened on ---------------------------------

    def test_cli_write_is_rejected_while_an_http_writer_holds_the_stream_lease(self):
        """THE lane-A3 question: hold the lease over the real HTTP API as writer A, then
        attempt a direct `cli.py` write on the same stream as writer B.  The CLI write must
        be rejected — if it succeeded, `cli.py` would be a live single-writer bypass."""
        bus = EventBus()
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler_factory(self.store, bus, TRACKER / "dashboard.html"))
        self.addCleanup(httpd.server_close)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(httpd.shutdown)

        status, accepted = self.http_scenario(httpd.server_port, "http-a-1", "S1-SC-01-http-writer-a", "writer-a-http")
        self.assertEqual(status, 201, accepted)
        self.assertEqual(accepted["event"]["event_type"], "scenario_executed")

        blocked = self.cli_scenario("cli-b-1", "S1-SC-02-cli-writer-b", writer="writer-b-cli")
        result = self.cli_result(blocked)
        self.assertEqual(blocked.returncode, 2, blocked.stdout)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["code"], "CONCURRENT_WRITER_LEASE_CONFLICT")
        self.assertIn("writer-a-http", result["error"])

        self.assertEqual(self.scenario_writes(), [{"scenario_id": "S1-SC-01-http-writer-a", "writer_instance_id": "writer-a-http"}])
        self.assertIn("CONCURRENT_WRITER_LEASE_CONFLICT", [row["code"] for row in self.store.rejected()])

    def test_cli_write_is_rejected_while_another_cli_process_holds_the_stream_lease(self):
        """Process-to-process, with no HTTP server anywhere in the picture.  Only a
        DB-backed lease can reject this; an in-process lock or handler-local check cannot."""
        held = self.cli_result(self.cli_scenario("cli-a-1", "S1-SC-01-cli-writer-a", writer="writer-a-cli"))
        self.assertTrue(held["accepted"])

        blocked = self.cli_scenario("cli-b-1", "S1-SC-02-cli-writer-b", writer="writer-b-cli")
        result = self.cli_result(blocked)
        self.assertEqual(blocked.returncode, 2, blocked.stdout)
        self.assertEqual(result["code"], "CONCURRENT_WRITER_LEASE_CONFLICT")
        self.assertEqual(self.scenario_writes(), [{"scenario_id": "S1-SC-01-cli-writer-a", "writer_instance_id": "writer-a-cli"}])

    def test_lease_holding_cli_writer_may_keep_writing(self):
        """Negative control — proves the two rejection tests above are load-bearing rather
        than a `cli.py` that simply cannot write scenarios at all."""
        first = self.cli_result(self.cli_scenario("cli-a-1", "S1-SC-01-cli-writer-a", writer="writer-a-cli"))
        self.assertTrue(first["accepted"])
        second = self.cli_result(self.cli_scenario("cli-a-2", "S1-SC-02-cli-writer-a", writer="writer-a-cli"))
        self.assertTrue(second["accepted"])
        self.assertEqual(
            self.scenario_writes(),
            [{"scenario_id": "S1-SC-01-cli-writer-a", "writer_instance_id": "writer-a-cli"},
             {"scenario_id": "S1-SC-02-cli-writer-a", "writer_instance_id": "writer-a-cli"}],
        )

    def test_cli_scenario_write_without_a_writer_instance_id_is_rejected(self):
        """`--writer-instance-id` is optional at the argparse layer; the shared store — not
        the CLI, and not the HTTP handler — is what makes it mandatory for a scenario write."""
        missing = self.cli_scenario("cli-no-writer", "S1-SC-01-anonymous", writer=None)
        result = self.cli_result(missing)
        self.assertEqual(missing.returncode, 2, missing.stdout)
        self.assertEqual(result["code"], "WRITER_INSTANCE_ID_REQUIRED")
        self.assertEqual(self.scenario_writes(), [])

    def test_numeric_slot_dedup_holds_across_the_cli_boundary(self):
        """The other half of PR #1638: a relabelled retry of an already-executed numeric slot
        must be rejected on the CLI path too, even from the lease-holding writer."""
        self.assertTrue(self.cli_result(self.cli_scenario("cli-a-1", "S1-SC-01-first-pass", writer="writer-a-cli"))["accepted"])
        relabelled = self.cli_scenario("cli-a-2", "S1-SC-01-relabelled-retry", writer="writer-a-cli")
        result = self.cli_result(relabelled)
        self.assertEqual(relabelled.returncode, 2, relabelled.stdout)
        self.assertEqual(result["code"], "DUPLICATE_SCENARIO")
        self.assertEqual(len(self.scenario_writes()), 1)

    def test_cli_rejection_leaves_the_ledger_and_projection_verifiably_intact(self):
        """A rejected bypass attempt must not disturb the hash chain or the projection."""
        self.assertTrue(self.cli_result(self.cli_scenario("cli-a-1", "S1-SC-01-first-pass", writer="writer-a-cli"))["accepted"])
        self.assertEqual(self.cli_scenario("cli-b-1", "S1-SC-02-second-pass", writer="writer-b-cli").returncode, 2)
        self.assertTrue(self.store.verify_replay()["ok"])
        stream = next(s for s in self.store.projection()["canonical"]["streams"] if s["id"] == "S1")
        self.assertEqual(stream["scenarios"]["executed"], 1)


class LeaseEnforcementLocationTests(unittest.TestCase):
    """Anti-drift guard: enforcement must stay in the shared store, never move into the
    HTTP handler.  If a future refactor relocates the lease check into `server.py`, every
    non-HTTP caller (`cli.py`, `demo.py`, any future writer) silently loses it — these two
    assertions are what turn that regression red instead of invisible."""

    def test_lease_conflict_is_raised_by_the_shared_event_store_with_no_server_involved(self):
        with tempfile.TemporaryDirectory() as root:
            store = EventStore(Path(root) / "runtime")
            store.submit({"actor_id": "integrator", "idempotency_key": "bootstrap", "event_type": "campaign_bootstrapped", "payload": {"campaign_id": "a3-location"}, "evidence": EVIDENCE})
            store.submit({"actor_id": "lead-s1", "idempotency_key": "charter", "event_type": "work_started", "payload": {"session_id": "a3-location", "planned_scenarios": PLANNED_SCENARIOS}, "stream_id": "S1", "expected_stream_seq": store.next_stream_seq("S1"), "evidence": EVIDENCE})
            store.submit({"actor_id": "lead-s1", "idempotency_key": "sc-1", "event_type": "scenario_executed", "payload": {"scenario_id": "S1-SC-01"}, "stream_id": "S1", "expected_stream_seq": store.next_stream_seq("S1"), "evidence": EVIDENCE, "writer_instance_id": "writer-a"})
            with self.assertRaises(RejectedEvent) as conflict:
                store.submit({"actor_id": "lead-s1", "idempotency_key": "sc-2", "event_type": "scenario_executed", "payload": {"scenario_id": "S1-SC-02"}, "stream_id": "S1", "expected_stream_seq": store.next_stream_seq("S1"), "evidence": EVIDENCE, "writer_instance_id": "writer-b"})
            self.assertEqual(conflict.exception.code, "CONCURRENT_WRITER_LEASE_CONFLICT")

    def test_http_server_holds_no_private_copy_of_the_lease_enforcement(self):
        server_source = (TRACKER / "server.py").read_text(encoding="utf-8")
        for marker in ("stream_scenario_write_leases", "CONCURRENT_WRITER_LEASE_CONFLICT", "_enforce_scenario_writer_lease", "SCENARIO_WRITER_LEASE_TTL_SECONDS"):
            self.assertNotIn(marker, server_source, f"{marker} appeared in server.py: single-writer enforcement must live in the shared EventStore so every caller inherits it")
        control_source = (TRACKER / "control.py").read_text(encoding="utf-8")
        for marker in ("stream_scenario_write_leases", "CONCURRENT_WRITER_LEASE_CONFLICT", "_enforce_scenario_writer_lease"):
            self.assertIn(marker, control_source)


if __name__ == "__main__":
    unittest.main()
