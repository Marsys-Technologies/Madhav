"""Pravāha tracker tests — events, ownership, status rules, joins, stream liveness, detectors,
the model checker, the CLI, and an end-to-end latency check through the real server."""
from __future__ import annotations

import datetime as dt
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pravaha_tracker import cli  # noqa: E402
from pravaha_tracker import detectors as D  # noqa: E402
from pravaha_tracker.events import EventError, EventLog, append, validate  # noqa: E402
from pravaha_tracker.server import check_model, serve  # noqa: E402
from pravaha_tracker.state import build_snapshot  # noqa: E402

REAL_MODEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..",
                                          "00_ARCHITECTURE", "control", "pravaha", "plan_model.json"))


def model_fixture(tmp: str) -> dict:
    return {
        "campaign": "Test", "plan_ref": "x",
        "streams": [{"id": "A", "name": "a", "worktrees": [tmp], "stale_after_s": 60, "dead_after_s": 120},
                    {"id": "B", "name": "b", "worktrees": [], "stale_after_s": 60, "dead_after_s": 120}],
        "phases": [{"id": "P", "title": "P", "lanes": ["LA"]}],
        "tracks": [{"id": "A", "title": "A", "mode": "sequential"}, {"id": "J", "title": "J", "mode": "sequential"}],
        "items": [
            {"id": "a1", "track": "A", "lane": "LA", "title": "first", "owner": "A", "depends_on": []},
            {"id": "a2", "track": "A", "lane": "LA", "title": "second", "owner": "A", "depends_on": ["a1"]},
            {"id": "b1", "track": "A", "lane": "LB", "title": "b's", "owner": "B", "depends_on": []},
            {"id": "d1", "track": "A", "lane": "LA", "title": "detected", "owner": "A", "depends_on": [],
             "detector": {"type": "file_exists", "path": os.path.join(tmp, "proof.md")}},
            {"id": "n1", "track": "A", "lane": "LN", "title": "ruling", "owner": "native", "depends_on": [],
             "done_by": "decision", "decision": "D1"},
            {"id": "j1", "track": "J", "lane": "J", "title": "join", "owner": "steward", "depends_on": ["a1", "b1"], "done_by": "join"},
        ],
        "decisions": [{"id": "D1", "title": "rule", "recommendation": "yes"}],
    }


class TestEvents(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "run", "EVENTS.jsonl")
        self.m = model_fixture(self.tmp)

    def test_done_needs_evidence(self):
        with self.assertRaises(EventError):
            validate({"kind": "item", "actor": "stream-A", "item": "a1", "state": "done"})

    def test_blocked_needs_reason(self):
        with self.assertRaises(EventError):
            validate({"kind": "item", "actor": "stream-A", "item": "a1", "state": "blocked"})

    def test_unknown_item_refused(self):
        with self.assertRaises(EventError):
            append(self.path, {"kind": "item", "actor": "stream-A", "item": "zz", "state": "running"}, self.m)

    def test_other_streams_item_refused(self):
        with self.assertRaises(EventError):
            append(self.path, {"kind": "item", "actor": "stream-A", "item": "b1", "state": "running"}, self.m)

    def test_join_and_decision_items_cannot_be_claimed_done(self):
        for iid in ("j1", "n1"):
            with self.assertRaises(EventError):
                append(self.path, {"kind": "item", "actor": "steward", "item": iid, "state": "done", "evidence": "x"}, self.m)

    def test_only_native_or_steward_decide(self):
        with self.assertRaises(EventError):
            append(self.path, {"kind": "decision", "actor": "stream-B", "decision": "D1", "state": "decided", "detail": "x"}, self.m)
        append(self.path, {"kind": "decision", "actor": "stream-B", "decision": "D1", "state": "requested", "detail": "packet"}, self.m)
        append(self.path, {"kind": "decision", "actor": "native", "decision": "D1", "state": "decided", "detail": "yes"}, self.m)

    def test_concurrent_writers_keep_lines_whole(self):
        def w(s):
            for k in range(200):
                append(self.path, {"kind": "heartbeat", "actor": f"stream-{s}", "detail": "x" * 300 + str(k)})
        ts = [threading.Thread(target=w, args=(s,)) for s in "AB"]
        [t.start() for t in ts]
        [t.join() for t in ts]
        log = EventLog(self.path)
        log.refresh()
        self.assertEqual(len(log.events), 400)
        self.assertEqual(log.malformed, 0)

    def test_reader_tolerates_corruption_and_rotation(self):
        append(self.path, {"kind": "note", "actor": "steward", "detail": "one"})
        with open(self.path, "a") as f:
            f.write("{not json\n")
        log = EventLog(self.path)
        log.refresh()
        self.assertEqual((len(log.events), log.malformed), (1, 1))
        os.replace(self.path, self.path + ".old")
        append(self.path, {"kind": "note", "actor": "steward", "detail": "two"})
        log.refresh()
        self.assertEqual([e["detail"] for e in log.events], ["two"])


class TestMessageBus(unittest.TestCase):
    """Steward <-> stream messages travel through the event log; no human relays them."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "run", "EVENTS.jsonl")
        self.m = model_fixture(self.tmp)
        self._old = cli.EVENTS
        cli.EVENTS = self.path

    def tearDown(self):
        cli.EVENTS = self._old

    def _msg(self, actor, to, mid, detail="x"):
        return append(self.path, {"kind": "message", "actor": actor, "to": to, "msg_id": mid, "detail": detail}, self.m)

    def test_routing_and_ack(self):
        self._msg("steward", "B", "m1")
        self._msg("stream-B", "steward", "m2")
        self.assertEqual([e["msg_id"] for e in cli._unacked("B")], ["m1"])
        self.assertEqual(cli._unacked("A"), [])
        self.assertEqual([e["msg_id"] for e in cli._unacked("steward")], ["m2"])
        append(self.path, {"kind": "ack", "actor": "stream-B", "msg_id": "m1"}, self.m)
        self.assertEqual(cli._unacked("B"), [])
        # an ack by the wrong party does not clear another party's message
        append(self.path, {"kind": "ack", "actor": "stream-A", "msg_id": "m2"}, self.m)
        self.assertEqual([e["msg_id"] for e in cli._unacked("steward")], ["m2"])

    def test_refusals(self):
        with self.assertRaises(EventError):
            self._msg("stream-A", "B", "m3")          # streams only message the steward
        with self.assertRaises(EventError):
            self._msg("steward", "steward", "m4")     # no self-messages
        with self.assertRaises(EventError):
            self._msg("tracker", "A", "m5")           # unknown actor
        with self.assertRaises(EventError):
            validate({"kind": "message", "actor": "steward", "to": "Z", "msg_id": "m6", "detail": "x"})
        with self.assertRaises(EventError):
            validate({"kind": "message", "actor": "steward", "to": "A", "msg_id": "m7"})   # empty body

    def test_inbox_wait_returns_on_arrival(self):
        def later():
            time.sleep(1.5)
            self._msg("steward", "A", "m8", "wake")
        threading.Thread(target=later, daemon=True).start()
        t0 = time.time()
        rc = cli.main(["inbox", "--stream", "A", "--wait", "20"])
        self.assertEqual(rc, 0)
        self.assertLess(time.time() - t0, 10)


class TestState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.m = model_fixture(self.tmp)
        self.now = dt.datetime.now(dt.timezone.utc)

    def snap(self, events, det=None, activity=None):
        return build_snapshot(self.m, events, det or {}, {}, {}, activity or {}, now=self.now)

    def items(self, s):
        return {t["id"]: t for tr in s["tracks"] for t in tr["items"]}

    def ev(self, **kw):
        return {"ts": self.now.isoformat(), **kw}

    def test_readiness_and_join(self):
        s = self.items(self.snap([]))
        self.assertEqual((s["a1"]["status"], s["a2"]["status"], s["j1"]["status"]), ("ready", "waiting", "waiting"))
        evs = [self.ev(kind="item", actor="stream-A", item="a1", state="done", evidence="e"),
               self.ev(kind="item", actor="stream-B", item="b1", state="done", evidence="e")]
        s = self.items(self.snap(evs))
        self.assertEqual((s["a2"]["status"], s["j1"]["status"]), ("ready", "done"))

    def test_detector_decides_and_conflicts(self):
        evs = [self.ev(kind="item", actor="stream-A", item="d1", state="done", evidence="claimed")]
        pending = {"d1": {"status": "pending", "detail": "no file", "checked_at": self.now.isoformat(), "source": "x"}}
        self.assertEqual(self.items(self.snap(evs, pending))["d1"]["status"], "conflict")
        err = {"d1": {"status": "error", "detail": "cannot", "checked_at": self.now.isoformat(), "source": "x"}}
        self.assertEqual(self.items(self.snap([], err))["d1"]["status"], "unknown")
        ok = {"d1": {"status": "done", "detail": "found", "checked_at": self.now.isoformat(), "source": "x"}}
        self.assertEqual(self.items(self.snap([], ok))["d1"]["status"], "done")

    def test_decision_item(self):
        evs = [self.ev(kind="decision", actor="stream-B", decision="D1", state="requested", detail="p")]
        s = self.snap(evs)
        self.assertEqual(self.items(s)["n1"]["status"], "running")
        self.assertEqual([d["id"] for d in s["native_queue"]], ["D1"])
        evs.append(self.ev(kind="decision", actor="native", decision="D1", state="decided", detail="yes"))
        self.assertEqual(self.items(self.snap(evs))["n1"]["status"], "done")

    def test_decision_not_due_until_inputs_exist(self):
        self.m["items"][4]["depends_on"] = ["a1"]          # n1 (decision D1) waits on a1
        s = self.snap([])
        self.assertEqual(self.items(s)["n1"]["status"], "waiting")
        self.assertEqual(s["native_queue"], [])            # not yet due: not shown as waiting on the native
        s = self.snap([self.ev(kind="item", actor="stream-A", item="a1", state="done", evidence="e")])
        self.assertEqual([d["id"] for d in s["native_queue"]], ["D1"])

    def test_stream_liveness(self):
        old = (self.now - dt.timedelta(seconds=200)).isoformat()
        evs = [{"ts": old, "kind": "heartbeat", "actor": "stream-A"},
               {"ts": old, "kind": "item", "actor": "stream-A", "item": "a1", "state": "running"}]
        st = {x["id"]: x for x in self.snap(evs)["streams"]}
        self.assertEqual(st["A"]["liveness"], "silent")   # work running, heartbeat older than dead_after
        self.assertEqual(st["B"]["liveness"], "idle")
        evs.append(self.ev(kind="heartbeat", actor="stream-A", detail="alive"))
        self.assertEqual({x["id"]: x for x in self.snap(evs)["streams"]}["A"]["liveness"], "active")


class TestModelChecker(unittest.TestCase):
    def test_cycle_and_dangling_detected(self):
        m = model_fixture(tempfile.mkdtemp())
        m["items"][0]["depends_on"] = ["a2"]
        m["items"][1]["depends_on"] = ["a1", "nope"]
        probs = " ".join(check_model(m))
        self.assertIn("cycle", probs)
        self.assertIn("unknown nope", probs)

    def test_real_model_is_clean(self):
        with open(REAL_MODEL, encoding="utf-8") as f:
            m = json.load(f)
        self.assertEqual(check_model(m), [])
        owners = {i["owner"] for i in m["items"]}
        self.assertTrue(owners <= {"A", "B", "native", "steward"}, owners)


class TestDetectors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.det = D.Detectors(D.Config(repo=self.tmp, pgenv=None, home=self.tmp))

    def test_files(self):
        p = os.path.join(self.tmp, "f.md")
        self.assertEqual(self.det.d_file_exists({"path": p}).status, "pending")
        with open(p, "w") as f:
            f.write("status: FROZEN\n")
        self.assertEqual(self.det.d_file_exists({"path": p}).status, "done")
        self.assertEqual(self.det.d_file_exists({"path": p, "min_bytes": 10_000}).status, "running")
        self.assertEqual(self.det.d_file_contains({"path": p, "pattern": "^status: FROZEN"}).status, "done")
        self.assertEqual(self.det.d_file_contains({"path": p, "pattern": "^status: SEALED"}).status, "pending")

    def test_db_without_credentials_is_unmeasured_never_done(self):
        self.det._run_one("k", {"type": "db_query", "sql": "select 1"})
        self.assertEqual(self.det.results["k"].status, "error")

    def test_branch_file_contains(self):
        subprocess.run(["git", "init", "-q", "-b", "main", self.tmp], check=True)
        with open(os.path.join(self.tmp, "r.md"), "w") as f:
            f.write("| ADK-0029 | x |\n")
        subprocess.run(["git", "-C", self.tmp, "add", "r.md"], check=True)
        subprocess.run(["git", "-C", self.tmp, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "c"], check=True)
        r = self.det.d_branch_file_contains({"ref": "main", "path": "r.md", "pattern": r"^\| ADK-0029 \|"})
        self.assertEqual(r.status, "done")
        act = D.git_activity(self.tmp)
        self.assertEqual((act["branch"], act["subject"]), ("main", "c"))


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestEndToEnd(unittest.TestCase):
    """A real server on a free port: an event written by the CLI path must reach /api/state fast."""

    def test_event_reaches_dashboard_quickly(self):
        tmp = tempfile.mkdtemp()
        m = model_fixture(tmp)
        mp = os.path.join(tmp, "model.json")
        with open(mp, "w") as f:
            json.dump(m, f)
        cfg = {"home": tmp, "events": os.path.join(tmp, "run", "EVENTS.jsonl"), "snapshot": os.path.join(tmp, "run", "snapshot.json"),
               "backup_dir": os.path.join(tmp, "run", "backup"), "hold": os.path.join(tmp, "run", "HOLD"), "model": mp, "repo": tmp,
               "pgenv": None, "db_port": 1, "detectors_enabled": True, "git_every_s": 3600, "backup_every_s": 3600}
        port = free_port()
        httpd, engine = serve(port, cfg)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            time.sleep(1.5)
            t0 = time.time()
            append(cfg["events"], {"kind": "item", "actor": "stream-A", "item": "a1", "state": "running", "detail": "go"}, m)
            seen = None
            while time.time() - t0 < 5:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/next?stream=A", timeout=2) as r:
                    nx = json.loads(r.read())
                if any(t["id"] == "a1" for t in nx["running"]):
                    seen = time.time() - t0
                    break
                time.sleep(0.05)
            self.assertIsNotNone(seen, "event never reached the tracker")
            self.assertLess(seen, 2.5)
            # the persisted snapshot follows, so the CLI works even if the server dies
            self.assertTrue(os.path.exists(cfg["snapshot"]))
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2) as r:
                self.assertTrue(json.loads(r.read())["ok"])
            # a bad model edit never replaces the last good model
            with open(mp, "w") as f:
                f.write("{broken")
            time.sleep(1.5)
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/state", timeout=2) as r:
                s = json.loads(r.read())
            self.assertIn("rejected", s["health"]["model_error"])
            self.assertEqual(len([t for tr in s["tracks"] for t in tr["items"]]), len(m["items"]))
        finally:
            engine.stop()
            httpd.shutdown()
            httpd.server_close()


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.m = model_fixture(self.tmp)
        mp = os.path.join(self.tmp, "model.json")
        with open(mp, "w") as f:
            json.dump(self.m, f)
        cli.MODEL, cli.EVENTS = mp, os.path.join(self.tmp, "run", "EVENTS.jsonl")
        cli.SNAPSHOT, cli.URL = os.path.join(self.tmp, "run", "snapshot.json"), "http://127.0.0.1:1"

    def test_start_done_and_refusals(self):
        self.assertEqual(cli.main(["start", "a1", "--stream", "A"]), 0)
        self.assertEqual(cli.main(["done", "a1", "--stream", "A"]), 2)                 # no evidence
        self.assertEqual(cli.main(["start", "b1", "--stream", "A"]), 2)                # not A's item
        self.assertEqual(cli.main(["start", "zz", "--stream", "A"]), 2)                # unknown item
        self.assertEqual(cli.main(["done", "a1", "--stream", "A", "--evidence", "PR #1"]), 0)
        self.assertEqual(cli.main(["decide", "D1", "--detail", "yes"]), 0)

    def test_unwritable_log_stops_work(self):
        cli.EVENTS = "/proc/definitely/not/writable/EVENTS.jsonl"
        self.assertEqual(cli.main(["heartbeat", "--stream", "A", "--detail", "x"]), 3)

    def test_preflight_fails_when_tracker_down(self):
        cwd = os.getcwd()
        os.chdir(self.tmp)
        try:
            self.assertEqual(cli.main(["preflight", "--stream", "A"]), 4)
        finally:
            os.chdir(cwd)


if __name__ == "__main__":
    unittest.main(verbosity=2)
