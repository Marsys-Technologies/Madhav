"""KĀLA-YANTRA control-plane acceptance cases, built out one capability at a time."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

from pravaha_tracker import cli, server
from pravaha_tracker.audit import audit
from pravaha_tracker.claims import ClaimError, claim_item, renew_claim
from pravaha_tracker.completion import CompletionError, guarded_done_event
from pravaha_tracker.events import EventError, append
from pravaha_tracker.state import build_snapshot
from pravaha_tracker.verdicts import accepted_verdict


class ClaimCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.events = os.path.join(self.tmp.name, "run", "EVENTS.jsonl")
        self.model = {
            "control_plane": {"claims": {"streams": ["K", "V"], "lease_s": 5400}},
            "items": [{"id": "K-1", "owner": "K", "depends_on": []}],
        }
        self.now = dt.datetime(2026, 10, 7, tzinfo=dt.timezone.utc)

    def test_two_simultaneous_claims_one_winner(self):
        barrier = threading.Barrier(2)
        outcomes = []

        def attempt(worker):
            barrier.wait()
            try:
                outcomes.append(claim_item(self.events, self.model, "K-1", "K", worker, 5400, now=self.now))
            except ClaimError:
                outcomes.append(None)

        threads = [threading.Thread(target=attempt, args=(worker,)) for worker in ("k1", "k2")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sum(result is not None for result in outcomes), 1)
        with open(self.events, encoding="utf-8") as handle:
            claims = [json.loads(line) for line in handle if '"state":"acquired"' in line]
        self.assertEqual(len(claims), 1)

    def test_stale_snapshot_cannot_claim(self):
        stale_snapshot = {"K-1": "ready"}
        first = claim_item(self.events, self.model, "K-1", "K", "k1", 5400, now=self.now)
        self.assertEqual(stale_snapshot["K-1"], "ready")
        with self.assertRaises(ClaimError):
            claim_item(self.events, self.model, "K-1", "K", "k2", 5400, now=self.now)
        self.assertEqual(first["worker_id"], "k1")

    def test_expired_claim_recovers_with_branch_head_step(self):
        first = claim_item(self.events, self.model, "K-1", "K", "k1", 60, now=self.now,
                           branch="kalayantra/k-1", head="abc123", step="tests")
        later = self.now + dt.timedelta(seconds=61)
        second = claim_item(self.events, self.model, "K-1", "K", "k2", 60, now=later)
        self.assertNotEqual(first["claim_id"], second["claim_id"])
        self.assertEqual((second["branch"], second["head"], second["step"]),
                         ("kalayantra/k-1", "abc123", "tests"))
        with open(os.path.join(self.tmp.name, "run", "claims", "k2.json"), encoding="utf-8") as handle:
            handoff = json.load(handle)
        self.assertEqual(handoff["head"], "abc123")
        with self.assertRaises(ClaimError):
            renew_claim(self.events, self.model, "K-1", "k1", first["claim_id"], 60, now=later)


class VerdictCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.events = os.path.join(self.tmp.name, "EVENTS.jsonl")
        self.model = {
            "control_plane": {"verdict_stream": "V"},
            "items": [{"id": "K-1", "owner": "K"}],
        }

    def read_events(self):
        with open(self.events, encoding="utf-8") as handle:
            return [json.loads(line) for line in handle]

    def test_verdict_stale_after_head_change(self):
        append(self.events, {"kind": "verdict", "actor": "stream-V:v1", "item": "K-1",
                             "head": "a" * 40, "result": "ACCEPTED", "phase": "pre_merge",
                             "detail": "tests and mutation passed"}, self.model)
        self.assertIsNotNone(accepted_verdict(self.read_events(), "K-1", head="a" * 40))
        self.assertIsNone(accepted_verdict(self.read_events(), "K-1", head="b" * 40))
        append(self.events, {"kind": "verdict", "actor": "stream-V:v1", "item": "K-1",
                             "head": "a" * 40, "result": "REJECTED", "phase": "pre_merge",
                             "detail": "mutation now fails"}, self.model)
        self.assertIsNone(accepted_verdict(self.read_events(), "K-1", head="a" * 40))

    def test_author_cannot_verdict_own_item(self):
        with self.assertRaises(EventError):
            append(self.events, {"kind": "verdict", "actor": "stream-K:k1", "item": "K-1",
                                 "head": "a" * 40, "result": "ACCEPTED", "phase": "pre_merge",
                                 "detail": "self review"}, self.model)

    def test_artifact_verdict_has_no_fictional_head(self):
        digest = "f" * 64
        append(self.events, {"kind": "verdict", "actor": "stream-V:v1", "item": "K-1",
                             "artifact_digest": digest, "result": "ACCEPTED", "phase": "artifact",
                             "detail": "artifact checked"}, self.model)
        self.assertIsNotNone(accepted_verdict(self.read_events(), "K-1", artifact_digest=digest,
                                               phase="artifact"))
        self.assertIsNone(accepted_verdict(self.read_events(), "K-1", head="f" * 40))


class GuardedSnapshotCases(unittest.TestCase):
    def setUp(self):
        self.model = {
            "campaign": "fixture", "control_plane": {"guarded_completion": True},
            "streams": [], "decisions": [], "tracks": [{"id": "K", "title": "K"}],
            "items": [
                {"id": "K-1", "track": "K", "owner": "K", "title": "first",
                 "depends_on": [], "detector": {"type": "file_exists", "path": "/fixture"}},
                {"id": "K-2", "track": "K", "owner": "K", "title": "second",
                 "depends_on": ["K-1"], "detector": {"type": "file_exists", "path": "/fixture2"}},
            ],
        }
        self.now = dt.datetime(2026, 10, 7, tzinfo=dt.timezone.utc)

    def snapshot(self, events=(), detector_state="done"):
        measured = {"status": detector_state, "detail": "fixture marker", "checked_at": self.now.isoformat()}
        result = build_snapshot(self.model, list(events), {"K-1": measured}, {}, {}, now=self.now)
        return {item["id"]: item for track in result["tracks"] for item in track["items"]}

    def test_branch_file_marker_alone_cannot_complete_bootstrap(self):
        state = self.snapshot()
        self.assertEqual(state["K-1"]["status"], "ready")
        self.assertEqual(state["K-2"]["status"], "waiting")
        self.assertIn("guarded completion pending", state["K-1"]["detail"])

    def test_unguarded_done_is_conflict_even_with_detector_match(self):
        event = {"kind": "item", "actor": "stream-K", "item": "K-1", "state": "done",
                 "evidence": "unreviewed marker", "ts": self.now.isoformat()}
        self.assertEqual(self.snapshot([event])["K-1"]["status"], "conflict")

    def test_recorded_done_survives_detector_flap(self):
        event = {"kind": "item", "actor": "stream-K", "item": "K-1", "state": "done",
                 "evidence": "accepted typed evidence", "guarded": True,
                 "ts": self.now.isoformat()}
        state = self.snapshot([event], detector_state="pending")
        self.assertEqual(state["K-1"]["status"], "done")
        self.assertEqual(state["K-2"]["deps_open"], [])
        self.assertEqual(state["K-1"]["detector_warning"], "fixture marker")
        later = {"kind": "item", "actor": "stream-K", "item": "K-1", "state": "review",
                 "ts": (self.now + dt.timedelta(minutes=1)).isoformat()}
        self.assertEqual(self.snapshot([event, later], detector_state="pending")["K-1"]["status"], "done")


class GuardedCompletionCases(unittest.TestCase):
    def setUp(self):
        self.head = "a" * 40
        self.merge = "b" * 40
        self.now = dt.datetime(2026, 10, 7, tzinfo=dt.timezone.utc).isoformat()
        self.model = {
            "campaign": "fixture", "control_plane": {"guarded_completion": True, "verdict_stream": "V"},
            "streams": [], "decisions": [], "tracks": [{"id": "K", "title": "K"}],
            "items": [
                {"id": "K-1", "track": "K", "owner": "K", "title": "first", "depends_on": [],
                 "detector": {"type": "branch_merged", "ref": "origin/k-1"}, "steps": ["tests"]},
                {"id": "K-2", "track": "K", "owner": "K", "title": "second", "depends_on": ["K-1"],
                 "detector": {"type": "file_exists", "path": "/fixture"}},
                {"id": "N-1", "track": "K", "owner": "N", "title": "owner artifact", "depends_on": [],
                 "detector": {"type": "file_exists", "path": "/artifact"}},
            ],
        }
        self.pr = {"number": 3210, "headRefOid": self.head, "mergeCommit": {"oid": self.merge},
                   "state": "MERGED"}
        self.proof = {"type": "code", "reviewed_head": self.head, "pr": self.pr}
        self.step = {"kind": "item", "actor": "stream-K:k1", "item": "K-1", "state": "done",
                     "step": "tests", "evidence": "suite passed", "ts": self.now}
        self.verdict = {"kind": "verdict", "actor": "stream-V:v1", "item": "K-1",
                        "head": self.head, "phase": "pre_merge", "result": "ACCEPTED",
                        "detail": "measured suite and mutations", "ts": self.now}
        self.review = {"kind": "item", "actor": "stream-K:k1", "item": "K-1", "state": "review",
                       "detail": f"PR #3210 @ {self.head}", "ts": self.now}
        self.post = {**self.verdict, "head": self.merge, "phase": "post_deploy",
                     "detail": "deployed merge and migration readback verified"}

    def done(self, events, *, item="K-1", detector="done", proof=None, actor="stream-K:k1"):
        return guarded_done_event(self.model, events, item, actor,
                                  {"status": detector, "detail": "observed"}, proof or self.proof)

    def test_rejected_and_merged_is_not_done(self):
        rejected = {**self.verdict, "result": "REJECTED", "detail": "mutation failed"}
        with self.assertRaisesRegex(CompletionError, "verdict"):
            self.done([self.step, self.review, self.verdict, self.post, rejected])

    def test_done_requires_deps_steps_verdict_detector(self):
        with self.assertRaisesRegex(CompletionError, "steps"):
            self.done([self.review, self.verdict, self.post])
        with self.assertRaisesRegex(CompletionError, "detector"):
            self.done([self.step, self.review, self.verdict, self.post], detector="pending")
        with self.assertRaisesRegex(CompletionError, "dependencies"):
            self.done([], item="K-2", proof={"type": "artifact", "artifact_digest": "f" * 64})
        event = self.done([self.step, self.review, self.verdict, self.post])
        self.assertTrue(event["guarded"])
        self.assertIn(self.merge, event["evidence"])

    def test_squash_merge_maps_reviewed_pr_head_to_merge_commit(self):
        self.assertEqual(self.done([self.step, self.review, self.verdict, self.post])["completion"]["pr"], self.pr)
        changed = {**self.pr, "headRefOid": "c" * 40}
        with self.assertRaisesRegex(CompletionError, "reviewed head"):
            self.done([self.step, self.review, self.verdict, self.post], proof={**self.proof, "pr": changed})
        unmerged = {**self.pr, "state": "OPEN"}
        with self.assertRaisesRegex(CompletionError, "merge commit"):
            self.done([self.step, self.review, self.verdict, self.post], proof={**self.proof, "pr": unmerged})

    def test_review_registration_and_post_deploy_verdict_are_required(self):
        with self.assertRaisesRegex(CompletionError, "registered"):
            self.done([self.step, self.verdict, self.post])
        with self.assertRaisesRegex(CompletionError, "post-deploy"):
            self.done([self.step, self.review, self.verdict])

    def test_artifact_item_completes_without_a_fictional_git_head(self):
        digest = "f" * 64
        verdict = {**self.verdict, "item": "N-1", "head": None, "artifact_digest": digest,
                   "phase": "artifact"}
        event = self.done([verdict], item="N-1", actor="stream-S:sutradhara",
                          proof={"type": "artifact", "artifact_digest": digest})
        self.assertEqual(event["completion"]["type"], "artifact")
        self.assertNotIn("head", event["completion"])

    def test_conductor_can_guardedly_complete_independently_accepted_n_or_v_item(self):
        digest = "e" * 64
        verdict = {**self.verdict, "item": "N-1", "head": None, "artifact_digest": digest,
                   "phase": "artifact"}
        proof = {"type": "artifact", "artifact_digest": digest}
        with self.assertRaisesRegex(CompletionError, "S must complete"):
            self.done([verdict], item="N-1", actor="stream-K:k1", proof=proof)
        with self.assertRaisesRegex(CompletionError, "S must complete"):
            self.done([verdict], item="N-1", actor="stream-N:adhikarin", proof=proof)
        self.assertTrue(self.done([verdict], item="N-1", actor="stream-S:sutradhara",
                                  proof=proof)["guarded"])

    def test_plain_done_is_disabled_for_guarded_model(self):
        with patch.object(cli, "load_model", return_value=self.model), patch.object(cli, "write") as write, \
                patch.object(cli, "get", return_value=(None, "unavailable")):
            self.assertEqual(cli.main(["done", "K-1", "--stream", "K", "--evidence", "claim"]), 2)
            write.assert_not_called()

    def test_cli_records_guarded_done_only_after_live_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "EVENTS.jsonl")
            for event in (self.step, self.review, self.verdict, self.post):
                append(path, event, self.model)
            live = ({"item": "K-1", "detector": {"status": "done", "detail": "merged"}}, "live")
            gh = subprocess.CompletedProcess([], 0, stdout=json.dumps(self.pr), stderr="")
            with patch.object(cli, "EVENTS", path), patch.object(cli, "load_model", return_value=self.model), \
                    patch.object(cli, "get", return_value=live), patch.object(cli.subprocess, "run", return_value=gh):
                self.assertEqual(cli.main(["done", "K-1", "--stream", "K", "--pr", "3210",
                                           "--reviewed-head", self.head]), 0)
            with open(path, encoding="utf-8") as handle:
                events = [json.loads(line) for line in handle]
            self.assertEqual(events[-1]["state"], "done")
            self.assertTrue(events[-1]["guarded"])
            self.assertEqual(events[-1]["completion"]["pr"]["mergeCommit"]["oid"], self.merge)


class StructuredDecisionCases(unittest.TestCase):
    def setUp(self):
        self.model = {
            "campaign": "fixture",
            "control_plane": {"decision_outcomes": {
                "final": ["approved", "refused"],
                "open": ["deferred", "insufficient_evidence"]}},
            "streams": [], "tracks": [{"id": "N", "title": "N"}],
            "decisions": [{"id": "D-FLIP", "title": "Flip"}],
            "items": [
                {"id": "D-FLIP", "track": "N", "owner": "N", "title": "decision",
                 "depends_on": [], "done_by": "decision", "decision": "D-FLIP"},
                {"id": "LIVE", "track": "N", "owner": "N", "title": "readback",
                 "depends_on": ["D-FLIP"], "requires_outcome": {"D-FLIP": "approved"}},
                {"id": "REBUILD", "track": "N", "owner": "N", "title": "rebuild",
                 "depends_on": ["LIVE"]},
                {"id": "REPORT", "track": "N", "owner": "N", "title": "report",
                 "depends_on": ["REBUILD"], "done_by": "join",
                 "accepts_not_applicable_dependencies": True},
            ],
        }
        self.now = dt.datetime(2026, 10, 7, tzinfo=dt.timezone.utc)

    def snapshot(self, outcome):
        events = [{"kind": "decision", "actor": "steward", "decision": "D-FLIP",
                   "state": "decided", "outcome": outcome, "detail": "recorded ruling",
                   "ts": self.now.isoformat()}]
        result = build_snapshot(self.model, events, {}, {}, {}, now=self.now)
        return {item["id"]: item for track in result["tracks"] for item in track["items"]}

    def test_refused_flip_skips_live_readback_and_full_rebuild(self):
        state = self.snapshot("refused")
        self.assertEqual(state["D-FLIP"]["status"], "done")
        self.assertEqual(state["LIVE"]["status"], "not_applicable")
        self.assertEqual(state["REBUILD"]["status"], "not_applicable")
        self.assertIn("D-FLIP", state["LIVE"]["skip_origin"])
        self.assertIn("D-FLIP", state["REBUILD"]["skip_origin"])

    def test_deferred_decision_keeps_dependant_waiting(self):
        state = self.snapshot("deferred")
        self.assertEqual(state["D-FLIP"]["status"], "waiting")
        self.assertEqual(state["LIVE"]["status"], "waiting")
        self.assertEqual(state["REBUILD"]["status"], "waiting")

    def test_report_join_accepts_skips_and_lists_originating_gaps(self):
        state = self.snapshot("refused")
        self.assertEqual(state["REPORT"]["status"], "done")
        self.assertEqual(state["REPORT"]["gaps"], ["D-FLIP"])

    def test_structured_outcome_required_only_for_declaring_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "events.jsonl")
            with self.assertRaises(EventError):
                append(path, {"kind": "decision", "actor": "steward", "decision": "D-FLIP",
                              "state": "decided", "detail": "no outcome"}, self.model)
            with self.assertRaises(EventError):
                append(path, {"kind": "decision", "actor": "steward", "decision": "D-FLIP",
                              "state": "decided", "outcome": "maybe", "detail": "bad outcome"}, self.model)
            legacy = {"decisions": [{"id": "D-FLIP"}], "items": []}
            append(path, {"kind": "decision", "actor": "steward", "decision": "D-FLIP",
                          "state": "decided", "detail": "legacy"}, legacy)


class MessagingHoldPreflightCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.events = os.path.join(self.tmp.name, "EVENTS.jsonl")
        self.model = {"control_plane": {"message_policy": {"S": ["N", "V"],
                                                     "V": ["S", "K"], "K": ["S"]}},
                      "streams": [{"id": "S"}, {"id": "N"}, {"id": "V"}, {"id": "K"}],
                      "items": []}

    def test_message_policy_from_model(self):
        append(self.events, {"kind": "message", "actor": "stream-V", "to": "K",
                             "msg_id": "m1", "detail": "review"}, self.model)
        with self.assertRaises(EventError):
            append(self.events, {"kind": "message", "actor": "stream-K", "to": "V",
                                 "msg_id": "m2", "detail": "not allowed"}, self.model)
        with self.assertRaises(EventError):
            append(self.events, {"kind": "message", "actor": "stream-V", "to": "X",
                                 "msg_id": "m3", "detail": "unknown party"}, self.model)
        legacy = {"streams": [{"id": "A"}, {"id": "B"}], "items": []}
        with self.assertRaises(EventError):
            append(self.events, {"kind": "message", "actor": "stream-A", "to": "B",
                                 "msg_id": "m4", "detail": "legacy policy"}, legacy)
        with patch.object(cli, "EVENTS", self.events), patch.object(cli, "load_model", return_value=self.model):
            self.assertEqual(cli.main(["send", "--as", "V", "--to", "K", "--detail", "review ready"]), 0)
        with open(self.events, encoding="utf-8") as handle:
            self.assertTrue(any((row := json.loads(line)).get("actor") == "stream-V" and
                                row.get("to") == "K" for line in handle))

    def test_hold_path_from_env(self):
        hold = os.path.join(self.tmp.name, "HOLD")
        with patch.dict(os.environ, {"PRAVAHA_HOME": self.tmp.name, "PRAVAHA_HOLD": hold}):
            self.assertEqual(server.default_config()["hold"], hold)
            self.assertEqual(cli.hold_path(), hold)
        with patch.dict(os.environ, {"PRAVAHA_HOME": self.tmp.name}, clear=True):
            self.assertEqual(cli.hold_path(), os.path.join(self.tmp.name, "run", "PRAVAHA_HOLD"))

    def test_preflight_accepts_detached_lane_without_claim(self):
        model = {"streams": [{"id": "S", "name": "conductor", "worktrees": [self.tmp.name],
                              "branch_pattern": "^kalayantra/"}]}
        args = type("Args", (), {"stream": "S"})()
        with patch.object(cli, "load_model", return_value=model), \
             patch.object(cli, "get", return_value=({"ok": True}, "live")), \
             patch.object(cli, "git_activity", return_value={"branch": "HEAD"}), \
             patch.object(cli, "write", return_value=0), \
             patch("os.getcwd", return_value=self.tmp.name):
            self.assertEqual(cli.cmd_preflight(args), 0)
            hold = os.path.join(self.tmp.name, "HOLD")
            with open(hold, "w", encoding="utf-8"):
                pass
            with patch.dict(os.environ, {"PRAVAHA_HOLD": hold}):
                self.assertEqual(cli.cmd_preflight(args), 4)

    def test_worker_heartbeat_keeps_lane_identity(self):
        args = type("Args", (), {"cmd": "heartbeat", "stream": "K", "as_": None,
                                   "detail": "cycle alive"})()
        self.model["control_plane"]["claims"] = {"streams": ["K"]}
        with patch.dict(os.environ, {"KY_LANE": "k2"}), \
             patch.object(cli, "load_model", return_value=self.model), \
             patch.object(cli, "write", return_value=0) as write:
            self.assertEqual(cli.main.__name__, "main")
            self.assertEqual(cli.actor_for(args), "stream-K")
            # The command path, rather than actor_for, attaches the lane to this event.
            with patch.object(cli, "EVENTS", self.events):
                self.assertEqual(cli.main(["heartbeat", "--stream", "K", "--detail", "cycle alive"]), 0)
            self.assertEqual(write.call_args.args[0]["actor"], "stream-K:k2")


class AuditCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        self.now = dt.datetime(2026, 10, 7, 2, tzinfo=dt.timezone.utc)
        self.since = self.now - dt.timedelta(minutes=50)
        self.model = {"control_plane": {"guarded_completion": True},
                      "items": [{"id": "K-1", "depends_on": []},
                                {"id": "K-2", "depends_on": ["K-1"]}]}

    def event(self, kind, **fields):
        return {"kind": kind, "ts": (self.now - dt.timedelta(minutes=10)).isoformat(), **fields}

    def codes(self, events):
        return {finding["code"] for finding in audit(self.model, events, self.root,
                                                       since=self.since, now=self.now)}

    def write_json(self, relative, data):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)

    def test_audit_fails_on_each_planted_defect(self):
        claim = self.event("claim", item="K-1", state="acquired", worker_id="k1",
                           claim_id="one", expires_at=(self.now + dt.timedelta(minutes=30)).isoformat())
        other = {**claim, "worker_id": "k2", "claim_id": "two"}
        self.assertIn("duplicate_claim", self.codes([claim, other]))
        expired = {**claim, "expires_at": (self.now - dt.timedelta(seconds=1)).isoformat()}
        self.assertIn("expired_worker", self.codes([expired]))

        bad_done = self.event("item", item="K-2", state="done", guarded=True,
                              head="a" * 40, evidence="PR merged")
        codes = self.codes([self.event("verdict", item="K-2", result="REJECTED",
                                      phase="pre_merge", head="a" * 40), bad_done])
        self.assertIn("rejected_or_stale_verdict", codes)
        self.assertIn("unmet_dependency", codes)
        self.assertIn("unguarded_done", self.codes([{**bad_done, "guarded": False}]))

        operation = self.event("item", item="K-1", state="done", guarded=True,
                               operation_id="op-1", evidence="operation completed")
        self.assertIn("unbound_operation", self.codes([operation]))
        self.write_json("ops/requests/op-2.json", {"operation_id": "op-2", "lease_id": "lease-1"})
        self.assertIn("unbound_production_operation", self.codes([]))
        self.write_json("ops/PRODUCTION_PENDING.json", {"operation_id": "op-2"})
        self.assertIn("unreleased_production_fence", self.codes([]))
        self.assertIn("zero_earned_progress", self.codes([claim]))

    def test_audit_accepts_bound_claim_and_completed_dependency(self):
        claim = self.event("claim", item="K-1", state="acquired", worker_id="k1",
                           claim_id="one", expires_at=(self.now + dt.timedelta(minutes=30)).isoformat())
        release = {**claim, "state": "released"}
        first = self.event("item", item="K-1", state="done", guarded=True, evidence="artifact")
        second = self.event("item", item="K-2", state="done", guarded=True, evidence="artifact")
        self.assertEqual(self.codes([claim, release, first, second]), set())

    def test_audit_detects_later_rejection_and_changed_operation_request(self):
        accepted = self.event("verdict", item="K-1", result="ACCEPTED",
                              phase="pre_merge", head="a" * 40)
        done = self.event("item", item="K-1", state="done", guarded=True,
                          head="a" * 40, evidence="reviewed merge")
        rejected = {**accepted, "result": "REJECTED"}
        self.assertIn("rejected_or_stale_verdict", self.codes([accepted, done, rejected]))

        request = {"operation_id": "op-3", "lease_id": "lease-1", "reviewed_commit": "a" * 40}
        digest = hashlib.sha256(json.dumps(request, sort_keys=True,
                                           separators=(",", ":")).encode()).hexdigest()
        self.write_json("ops/requests/op-3.json", request)
        self.write_json("ops/acceptance/op-3.json", {"operation_id": "op-3", "result": "ACCEPTED",
                                                      "by": "v1", "reviewed_commit": "a" * 40,
                                                      "request_sha256": digest})
        self.assertNotIn("unbound_production_operation", self.codes([]))
        request["reviewed_commit"] = "b" * 40
        self.write_json("ops/requests/op-3.json", request)
        self.assertIn("unbound_production_operation", self.codes([]))

    def test_audit_fails_when_skipped_executable_completes(self):
        self.model["items"].append({"id": "D-FLIP", "depends_on": [],
                                     "done_by": "decision", "decision": "D-FLIP"})
        self.model["items"].append({"id": "LIVE", "depends_on": ["D-FLIP"],
                                     "requires_outcome": {"D-FLIP": "approved"}})
        refusal = self.event("decision", decision="D-FLIP", state="decided", outcome="refused")
        done = self.event("item", item="LIVE", state="done", guarded=True, evidence="wrong")
        self.assertIn("skipped_item_completed", self.codes([refusal, done]))
