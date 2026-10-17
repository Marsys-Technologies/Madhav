"""KĀLA-YANTRA control-plane acceptance cases, built out one capability at a time."""
from __future__ import annotations

import datetime as dt
import contextlib
import hashlib
import io
import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import threading
import types
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

from pravaha_tracker import cli, server, verdicts
from pravaha_tracker.audit import audit
from pravaha_tracker.claims import ClaimError, claim_item, renew_claim
from pravaha_tracker.completion import (CompletionError, evidence_requirements, guarded_done_event,
                                        writes_data)
from pravaha_tracker.events import EventError, append
from pravaha_tracker.state import build_snapshot
from pravaha_tracker.verdicts import accepted_verdict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), *[".."] * 5))
COMMITTED_MODEL = os.path.join(REPO_ROOT, "00_ARCHITECTURE", "control", "kalayantra", "plan_model.json")


def predicate(answer=True, calls=None):
    """A stub of the shared inheritance predicate (top-level module `kyverdicts`, KV3-B-KYVERDICTS)."""
    module = types.ModuleType("kyverdicts")

    def inherits(repo, old_head, new_head):
        if calls is not None:
            calls.append((repo, old_head, new_head))
        if isinstance(answer, Exception):
            raise answer
        return answer

    module.inherits = inherits
    return patch.dict(sys.modules, {"kyverdicts": module})


def no_predicate():
    """`import kyverdicts` raises ImportError, whatever is on sys.path."""
    return patch.dict(sys.modules, {"kyverdicts": None})


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

    def test_refused_decision_cannot_be_claimed_as_approved_work(self):
        self.model["control_plane"]["decision_outcomes"] = {
            "final": ["approved", "refused"], "open": ["deferred", "insufficient_evidence"]}
        self.model["items"] = [
            {"id": "D-FLIP", "owner": "N", "depends_on": [],
             "done_by": "decision", "decision": "D-FLIP"},
            {"id": "K-1", "owner": "K", "depends_on": ["D-FLIP"],
             "requires_outcome": {"D-FLIP": "approved"}},
        ]
        self.model["decisions"] = [{"id": "D-FLIP", "title": "Flip"}]
        append(self.events, {"kind": "decision", "actor": "steward", "decision": "D-FLIP",
                             "state": "decided", "outcome": "refused", "detail": "unsafe",
                             "ts": self.now.isoformat()}, self.model)
        with self.assertRaisesRegex(ClaimError, "not_applicable"):
            claim_item(self.events, self.model, "K-1", "K", "k1", 5400, now=self.now)

    def test_skipped_dependency_is_claimable_only_when_item_accepts_it(self):
        self.model["control_plane"]["decision_outcomes"] = {
            "final": ["approved", "refused"], "open": ["deferred", "insufficient_evidence"]}
        self.model["items"] = [
            {"id": "D-FLIP", "owner": "N", "depends_on": [],
             "done_by": "decision", "decision": "D-FLIP"},
            {"id": "K-SKIP", "owner": "K", "depends_on": ["D-FLIP"],
             "requires_outcome": {"D-FLIP": "approved"}},
            {"id": "K-1", "owner": "K", "depends_on": ["K-SKIP"]},
            {"id": "K-REPORT", "owner": "K", "depends_on": ["K-SKIP"],
             "accepts_not_applicable_dependencies": True},
        ]
        self.model["decisions"] = [{"id": "D-FLIP", "title": "Flip"}]
        append(self.events, {"kind": "decision", "actor": "steward", "decision": "D-FLIP",
                             "state": "decided", "outcome": "refused", "detail": "unsafe",
                             "ts": self.now.isoformat()}, self.model)
        with self.assertRaisesRegex(ClaimError, "not_applicable"):
            claim_item(self.events, self.model, "K-1", "K", "k1", 5400, now=self.now)
        claim = claim_item(self.events, self.model, "K-REPORT", "K", "k1", 5400, now=self.now)
        self.assertEqual(claim["item"], "K-REPORT")


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

    def test_verifier_artifact_author_needs_another_lane_or_bound_external_review(self):
        self.model["items"].append({"id": "V-OWN", "owner": "V"})
        append(self.events, {"kind": "item", "actor": "stream-V:v1", "item": "V-OWN",
                             "state": "running"}, self.model)
        verdict = {"kind": "verdict", "actor": "stream-V:v1", "item": "V-OWN",
                   "artifact_digest": "a" * 64, "phase": "artifact", "result": "ACCEPTED",
                   "detail": "artifact checked"}
        with self.assertRaisesRegex(EventError, "independent"):
            append(self.events, verdict, self.model)
        self.assertEqual(len(self.read_events()), 1)
        append(self.events, {**verdict, "actor": "stream-V:v2"}, self.model)
        review_path = os.path.join(self.tmp.name, "external-review.json")
        raw = b'{"by":"astra","result":"ACCEPTED","item":"V-OWN","artifact_digest":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}'
        with open(review_path, "wb") as handle:
            handle.write(raw)
        external = {"path": review_path, "sha256": hashlib.sha256(raw).hexdigest()}
        append(self.events, {**verdict, "external_review": external}, self.model)
        with self.assertRaisesRegex(EventError, "external review"):
            append(self.events, {**verdict, "external_review": {**external, "sha256": "f" * 64}}, self.model)
        self_review = raw.replace(b'"astra"', b'"v1"')
        with open(review_path, "wb") as handle:
            handle.write(self_review)
        with self.assertRaisesRegex(EventError, "external review"):
            append(self.events, {**verdict, "external_review": {"path": review_path,
                                     "sha256": hashlib.sha256(self_review).hexdigest()}}, self.model)

    def test_campaign_cli_actor_includes_lane_identity(self):
        with patch.dict(os.environ, {"KY_LANE": "v1"}), \
             patch.object(cli, "load_model", return_value=self.model), \
             patch.object(cli, "EVENTS", self.events):
            self.assertEqual(cli.write({"kind": "verdict", "actor": "stream-V", "item": "K-1",
                                        "head": "a" * 40, "phase": "pre_merge", "result": "ACCEPTED",
                                        "detail": "independent check"}), 0)
        self.assertEqual(self.read_events()[0]["actor"], "stream-V:v1")

    def test_verdict_cli_binds_external_review_for_author_lane(self):
        self.model["items"].append({"id": "V-OWN", "owner": "V"})
        append(self.events, {"kind": "item", "actor": "stream-V:v1", "item": "V-OWN",
                             "state": "running"}, self.model)
        digest = "a" * 64
        review_path = os.path.join(self.tmp.name, "external-review.json")
        raw = json.dumps({"by": "astra", "item": "V-OWN", "result": "ACCEPTED",
                          "artifact_digest": digest}).encode()
        with open(review_path, "wb") as handle:
            handle.write(raw)
        with patch.dict(os.environ, {"KY_LANE": "v1"}), \
             patch.object(cli, "load_model", return_value=self.model), \
             patch.object(cli, "EVENTS", self.events):
            self.assertEqual(cli.main(["verdict", "V-OWN", "--stream", "V",
                                       "--artifact-digest", digest, "--phase", "artifact",
                                       "--result", "ACCEPTED", "--detail", "reviewed",
                                       "--external-review-path", review_path,
                                       "--external-review-sha256", hashlib.sha256(raw).hexdigest()]), 0)
        self.assertEqual(self.read_events()[-1]["external_review"]["sha256"],
                         hashlib.sha256(raw).hexdigest())

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

    def test_pravaha_model_behaviour_unchanged(self):
        legacy = {key: value for key, value in self.model.items() if key != "control_plane"}
        measured = {"status": "done", "detail": "fixture marker", "checked_at": self.now.isoformat()}
        pending = {"status": "pending", "detail": "no marker", "checked_at": self.now.isoformat()}
        snapshot = build_snapshot(legacy, [], {"K-1": measured, "K-2": pending}, {}, {}, now=self.now)
        rows = {item["id"]: item for track in snapshot["tracks"] for item in track["items"]}
        self.assertEqual(rows["K-1"]["status"], "done")
        self.assertEqual(rows["K-2"]["status"], "ready")


class GuardedCompletionCases(unittest.TestCase):
    def setUp(self):
        self.head = "a" * 40
        self.merge = "b" * 40
        self.now = dt.datetime(2026, 10, 7, tzinfo=dt.timezone.utc).isoformat()
        self.model = {
            "campaign": "fixture", "control_plane": {"guarded_completion": True, "verdict_stream": "V"},
            "streams": [], "decisions": [], "tracks": [{"id": "K", "title": "K"}],
            "items": [
                # K-1 writes data (a migration): it keeps the second, post-deploy verdict (amendment §5)
                {"id": "K-1", "track": "K", "owner": "K", "title": "first", "depends_on": [],
                 "detector": {"type": "branch_merged", "ref": "origin/k-1"}, "steps": ["tests"],
                 "brief": {"migration": "1400_fixture.sql"}},
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
        # A7 D-46: a code item needs no step receipt (its PR acceptance covers them); only the detector, verdict and
        # post-deploy evidence remain, and an operation still waits for its dependencies (SR-A4-01).
        self.assertTrue(self.done([self.review, self.verdict, self.post])["guarded"])
        with self.assertRaisesRegex(CompletionError, "detector"):
            self.done([self.step, self.review, self.verdict, self.post], detector="pending")
        with self.assertRaisesRegex(CompletionError, "dependencies"):
            self.done([], item="K-2", proof={"type": "operation"})
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

    def test_operational_item_completes_without_a_fictional_git_head(self):
        self.model["items"].append({"id": "N-OP", "track": "K", "owner": "N", "title": "operation",
                                    "depends_on": [], "detector": {"type": "file_exists", "path": "/receipt"}})
        digest = "d" * 64
        receipt = {"operation_id": "op-42", "item_id": "N-OP", "status": "COMPLETED"}
        verdict = {**self.verdict, "item": "N-OP", "head": None, "artifact_digest": digest,
                   "phase": "artifact"}
        proof = {"type": "operation", "operation_id": "op-42", "receipt": receipt,
                 "artifact_digest": digest}
        event = self.done([verdict], item="N-OP", actor="stream-S:sutradhara", proof=proof)
        self.assertEqual(event["completion"]["operation_id"], "op-42")
        self.assertNotIn("head", event["completion"])
        for bad in ({**receipt, "status": "FAILED"}, {**receipt, "item_id": "N-OTHER"},
                    {**receipt, "operation_id": "op-43"}):
            with self.assertRaisesRegex(CompletionError, "completed receipt"):
                self.done([verdict], item="N-OP", actor="stream-S:sutradhara",
                          proof={**proof, "receipt": bad})

    def test_cli_operation_reads_declared_receipt_and_independent_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt_path = os.path.join(tmp, "N-OP.dispatch.json")
            event_path = os.path.join(tmp, "EVENTS.jsonl")
            self.model["items"].append({"id": "N-OP", "track": "K", "owner": "N", "title": "operation",
                                        "depends_on": [], "detector": {"type": "file_exists", "path": receipt_path}})
            raw = json.dumps({"operation_id": "op-42", "item_id": "N-OP", "status": "COMPLETED"}).encode()
            with open(receipt_path, "wb") as handle:
                handle.write(raw)
            append(event_path, {**self.verdict, "item": "N-OP", "head": None,
                                "artifact_digest": hashlib.sha256(raw).hexdigest(), "phase": "artifact"}, self.model)
            live = ({"item": "N-OP", "detector": {"status": "done", "detail": "receipt"}}, "live")
            with patch.object(cli, "load_model", return_value=self.model), patch.object(cli, "get", return_value=live), \
                    patch.object(cli, "EVENTS", event_path):
                self.assertEqual(cli.main(["done", "N-OP", "--stream", "S",
                                           "--operation-receipt", receipt_path,
                                           "--operation-id", "op-42"]), 0)
            with open(event_path, encoding="utf-8") as handle:
                recorded = [json.loads(line) for line in handle][-1]
            self.assertEqual(recorded["completion"]["type"], "operation")
            self.assertNotIn("head", recorded["completion"])

    def _packet_fixture(self):
        self.model["items"].append({"id": "V-K0a", "track": "K", "owner": "V",
                                    "title": "packet", "depends_on": [],
                                    "detector": {"type": "file_contains", "path": "/run/reviews/K0A.VERDICT.json"}})
        packet = {"item": "V-K0a", "packet": "K0A", "result": "ACCEPTED",
                  "blocking_open": 0, "review_sha256": "e" * 64}
        digest = "f" * 64
        verdict = {**self.verdict, "item": "V-K0a", "head": None,
                   "artifact_digest": digest, "phase": "artifact"}
        proof = {"type": "packet", "packet": packet, "artifact_digest": digest,
                 "review_sha256": "e" * 64}
        return packet, verdict, proof

    def test_packet_ids_are_model_ids_not_uppercased_labels(self):
        packet, verdict, proof = self._packet_fixture()
        self.assertTrue(self.done([verdict], item="V-K0a", actor="stream-S:sutradhara",
                                  proof=proof)["guarded"])
        with self.assertRaisesRegex(CompletionError, "exact model item"):
            self.done([verdict], item="V-K0a", actor="stream-S:sutradhara",
                      proof={**proof, "packet": {**packet, "item": "V-K0A"}})

    def test_packet_json_rejects_accepted_with_open_blockers(self):
        packet, verdict, proof = self._packet_fixture()
        with self.assertRaisesRegex(CompletionError, "open blockers"):
            self.done([verdict], item="V-K0a", actor="stream-S:sutradhara",
                      proof={**proof, "packet": {**packet, "blocking_open": 1}})

    def test_packet_json_rejects_missing_review_or_changed_review_digest(self):
        packet, verdict, proof = self._packet_fixture()
        with self.assertRaisesRegex(CompletionError, "reviewed packet"):
            self.done([verdict], item="V-K0a", actor="stream-S:sutradhara",
                      proof={**proof, "packet": {**packet, "review_sha256": "a" * 64}})
        with tempfile.TemporaryDirectory() as tmp:
            verdict_path = os.path.join(tmp, "K0A.VERDICT.json")
            review_path = os.path.join(tmp, "ASTRA_REVIEW_K0A_v1.md")
            self.model["items"][-1]["detector"]["path"] = verdict_path
            with open(review_path, "w", encoding="utf-8") as handle:
                handle.write("review evidence")
            packet = {**packet, "review_path": review_path,
                      "review_sha256": hashlib.sha256(b"review evidence").hexdigest()}
            with open(verdict_path, "w", encoding="utf-8") as handle:
                json.dump(packet, handle)
            live = ({"item": "V-K0a", "detector": {"status": "done", "detail": "accepted"}}, "live")
            with patch.object(cli, "load_model", return_value=self.model), patch.object(cli, "get", return_value=live), \
                    patch.object(cli, "EVENTS", os.path.join(tmp, "EVENTS.jsonl")):
                self.assertEqual(cli.main(["done", "V-K0a", "--stream", "S",
                                           "--packet-verdict", verdict_path]), 2)
            os.unlink(review_path)
            with patch.object(cli, "load_model", return_value=self.model), patch.object(cli, "get", return_value=live), \
                    patch.object(cli, "EVENTS", os.path.join(tmp, "EVENTS.jsonl")):
                self.assertEqual(cli.main(["done", "V-K0a", "--stream", "S",
                                           "--packet-verdict", verdict_path]), 2)

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

    def test_cli_refuses_failed_live_measurement_despite_ready_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "EVENTS.jsonl")
            for event in (self.step, self.review, self.verdict, self.post):
                append(path, event, self.model)
            before = Path(path).read_bytes()
            live = ({"item": "K-1", "detector": {"status": "error", "detail": "fetch failed"}}, "live")
            gh = subprocess.CompletedProcess([], 0, stdout=json.dumps(self.pr), stderr="")
            with patch.object(cli, "EVENTS", path), patch.object(cli, "load_model", return_value=self.model), \
                    patch.object(cli, "get", return_value=live), patch.object(cli.subprocess, "run", return_value=gh):
                self.assertEqual(cli.main(["done", "K-1", "--stream", "K", "--pr", "3210",
                                           "--reviewed-head", self.head]), 2)
            self.assertEqual(Path(path).read_bytes(), before)


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

    def test_refused_decision_makes_dependant_not_applicable(self):
        self.assertEqual(self.snapshot("approved")["LIVE"]["status"], "ready")
        refused = self.snapshot("refused")["LIVE"]
        self.assertEqual(refused["status"], "not_applicable")
        self.assertEqual(refused["skip_origin"], ["D-FLIP"])

    def test_deferred_decision_keeps_dependant_waiting(self):
        state = self.snapshot("deferred")
        self.assertEqual(state["D-FLIP"]["status"], "waiting")
        self.assertEqual(state["LIVE"]["status"], "waiting")
        self.assertEqual(state["REBUILD"]["status"], "waiting")

    def test_report_join_accepts_skips_and_lists_originating_gaps(self):
        state = self.snapshot("refused")
        self.assertEqual(state["REPORT"]["status"], "done")
        self.assertEqual(state["REPORT"]["gaps"], ["D-FLIP"])

    def test_not_applicable_satisfies_join_and_is_reported_separately(self):
        snapshot = build_snapshot(self.model, [{"kind": "decision", "actor": "steward",
                                                "decision": "D-FLIP", "state": "decided",
                                                "outcome": "refused", "detail": "recorded ruling",
                                                "ts": self.now.isoformat()}],
                                  {}, {}, {}, now=self.now)
        rows = {item["id"]: item for track in snapshot["tracks"] for item in track["items"]}
        self.assertEqual(rows["REPORT"]["status"], "done")
        self.assertEqual(rows["REPORT"]["gaps"], ["D-FLIP"])
        self.assertEqual(snapshot["overall"]["not_applicable"], 2)
        self.assertEqual(snapshot["overall"]["done"], 2)

    def test_refused_teardown_skips_dispatch_teardown_and_measuring_descendants(self):
        self.model["items"] = [
            {"id": "D-TEARDOWN", "track": "N", "owner": "N", "title": "decision",
             "depends_on": [], "done_by": "decision", "decision": "D-TEARDOWN"},
            {"id": "J-2a", "track": "N", "owner": "N", "title": "dispatch",
             "depends_on": ["D-TEARDOWN"],
             "requires_outcome": {"D-TEARDOWN": "approved"}},
            {"id": "J-2b", "track": "N", "owner": "N", "title": "teardown",
             "depends_on": ["J-2a"]},
            {"id": "J-3c", "track": "N", "owner": "N", "title": "measuring build",
             "depends_on": ["J-2b"]},
            {"id": "J-3d", "track": "N", "owner": "N", "title": "measuring readback",
             "depends_on": ["J-3c"]},
        ]
        state = {item["id"]: item for track in build_snapshot(
            self.model, [{"kind": "decision", "actor": "steward", "decision": "D-TEARDOWN",
                          "state": "decided", "outcome": "refused", "detail": "no teardown",
                          "ts": self.now.isoformat()}], {}, {}, {}, now=self.now)["tracks"]
                 for item in track["items"]}
        for item_id in ("J-2a", "J-2b", "J-3c", "J-3d"):
            self.assertEqual(state[item_id]["status"], "not_applicable")
            self.assertEqual(state[item_id]["skip_origin"], ["D-TEARDOWN"])

    def test_open_optional_decision_does_not_satisfy_join_all(self):
        self.model["items"].append({"id": "D-OPTIONAL", "track": "N", "owner": "N",
                                    "title": "optional decision", "mandatory": False,
                                    "depends_on": [], "done_by": "decision",
                                    "decision": "D-OPTIONAL"})
        self.model["items"].append({"id": "JOIN-ALL", "track": "N", "owner": "N",
                                    "title": "join", "depends_on": ["REPORT", "D-OPTIONAL"],
                                    "done_by": "join",
                                    "accepts_not_applicable_dependencies": True})
        self.model["decisions"].append({"id": "D-OPTIONAL", "title": "optional"})
        state = self.snapshot("refused")
        self.assertEqual(state["REPORT"]["status"], "done")
        self.assertEqual(state["D-OPTIONAL"]["status"], "ready")
        self.assertEqual(state["JOIN-ALL"]["status"], "waiting")
        self.assertIn("D-OPTIONAL", state["JOIN-ALL"]["deps_open"])

    def test_refused_promised_tulana_or_second_writer_retirement_forces_partial_close(self):
        for decision, promised in (("D-R6", "K7-4"), ("D-KR", "KR-2")):
            with self.subTest(decision=decision):
                model = {"control_plane": self.model["control_plane"],
                         "streams": [], "tracks": self.model["tracks"],
                         "decisions": [{"id": decision, "title": decision}],
                         "items": [
                             {"id": decision, "track": "N", "owner": "N", "title": decision,
                              "depends_on": [], "done_by": "decision", "decision": decision},
                             {"id": promised, "track": "N", "owner": "N", "title": promised,
                              "mandatory": True, "depends_on": [decision],
                              "requires_outcome": {decision: "approved"}},
                             {"id": "JOIN-ALL", "track": "N", "owner": "N", "title": "join",
                              "depends_on": [promised], "done_by": "join",
                              "accepts_not_applicable_dependencies": True},
                         ]}
                snapshot = build_snapshot(model, [{"kind": "decision", "actor": "steward",
                                                   "decision": decision, "state": "decided",
                                                   "outcome": "refused", "detail": "ruling",
                                                   "ts": self.now.isoformat()}],
                                          {}, {}, {}, now=self.now)
                rows = {item["id"]: item for track in snapshot["tracks"] for item in track["items"]}
                self.assertEqual(rows[promised]["status"], "not_applicable")
                self.assertEqual(rows["JOIN-ALL"]["status"], "done")
                self.assertEqual(rows["JOIN-ALL"]["gaps"], [decision])
                self.assertEqual(snapshot["overall"]["not_applicable"], 1)

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

    def test_note_does_not_unblock(self):
        model = {"control_plane": {"guarded_completion": True},
                 "streams": [], "tracks": [{"id": "K", "title": "K"}],
                 "decisions": [],
                 "items": [{"id": "K-1", "track": "K", "owner": "K",
                            "title": "blocked work", "depends_on": []}]}
        append(self.events, {"kind": "item", "actor": "stream-K", "item": "K-1",
                             "state": "blocked", "detail": "missing input"}, model)
        append(self.events, {"kind": "note", "actor": "stream-K",
                             "detail": "input may now be available"}, model)
        with open(self.events, encoding="utf-8") as handle:
            events = [json.loads(line) for line in handle]
        snapshot = build_snapshot(model, events, {}, {}, {})
        row = snapshot["tracks"][0]["items"][0]
        self.assertEqual(row["status"], "blocked")
        self.assertEqual(row["detail"], "missing input")

    def test_unblock_requires_owner_and_explicit_blocked_state(self):
        model = {"control_plane": {"guarded_completion": True},
                 "streams": [], "tracks": [{"id": "K", "title": "K"}], "decisions": [],
                 "items": [{"id": "K-1", "track": "K", "owner": "K", "title": "work",
                            "depends_on": []}]}
        append(self.events, {"kind": "item", "actor": "stream-K", "item": "K-1",
                             "state": "blocked", "detail": "missing input"}, model)
        with patch.object(cli, "EVENTS", self.events), patch.object(cli, "load_model", return_value=model):
            self.assertEqual(cli.main(["unblock", "K-1", "--stream", "S", "--detail", "not mine"]), 2)
            self.assertEqual(cli.main(["unblock", "K-1", "--stream", "K", "--detail", "input arrived"]), 0)
            self.assertEqual(cli.main(["unblock", "K-1", "--stream", "K", "--detail", "again"]), 2)
        with open(self.events, encoding="utf-8") as handle:
            events = [json.loads(line) for line in handle]
        row = build_snapshot(model, events, {}, {}, {})["tracks"][0]["items"][0]
        self.assertEqual(row["status"], "ready")
        self.assertEqual(events[-1]["detail"], "input arrived")

    def test_reopen_requires_failed_or_review_and_cannot_undo_done(self):
        model = {"control_plane": {"guarded_completion": True},
                 "streams": [], "tracks": [{"id": "K", "title": "K"}], "decisions": [],
                 "items": [{"id": "K-1", "track": "K", "owner": "K", "title": "work",
                            "depends_on": []}]}
        append(self.events, {"kind": "item", "actor": "stream-K", "item": "K-1",
                             "state": "failed", "detail": "test failed"}, model)
        with patch.object(cli, "EVENTS", self.events), patch.object(cli, "load_model", return_value=model):
            self.assertEqual(cli.main(["reopen", "K-1", "--stream", "K", "--detail", "fixed tests"]), 0)
            self.assertEqual(cli.main(["reopen", "K-1", "--stream", "K", "--detail", "again"]), 2)
        with open(self.events, encoding="utf-8") as handle:
            events = [json.loads(line) for line in handle]
        self.assertEqual(build_snapshot(model, events, {}, {}, {})["tracks"][0]["items"][0]["status"], "ready")
        append(self.events, {"kind": "item", "actor": "stream-K", "item": "K-1",
                             "state": "done", "evidence": "accepted", "guarded": True}, model)
        with patch.object(cli, "EVENTS", self.events), patch.object(cli, "load_model", return_value=model):
            self.assertEqual(cli.main(["reopen", "K-1", "--stream", "K", "--detail", "undo"]), 2)


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

    def test_audit_checks_typed_completion_head_and_operation_identity(self):
        head = "a" * 40
        merge = "b" * 40
        accepted = self.event("verdict", item="K-1", result="ACCEPTED",
                              phase="pre_merge", head=head)
        code_done = self.event("item", item="K-1", state="done", guarded=True,
                               completion={"type": "code", "reviewed_head": head,
                                           "pr": {"number": 3210, "headRefOid": head,
                                                  "mergeCommit": {"oid": merge},
                                                  "state": "MERGED"}})
        self.assertIn("rejected_or_stale_verdict", self.codes([code_done]))
        self.assertIn("missing_post_deploy_verdict", self.codes([accepted, code_done]))
        rejected = {**accepted, "result": "REJECTED"}
        self.assertIn("rejected_or_stale_verdict", self.codes([accepted, code_done, rejected]))

        operation_done = self.event("item", item="K-1", state="done", guarded=True,
                                    completion={"type": "operation", "operation_id": "op-typed",
                                                "artifact_digest": "f" * 64,
                                                "receipt": {"operation_id": "op-typed",
                                                            "item_id": "K-1", "status": "COMPLETED"}})
        self.assertIn("unbound_operation", self.codes([operation_done]))

    def test_audit_detects_revoked_typed_artifact_verdict(self):
        digest = "f" * 64
        accepted = self.event("verdict", item="K-1", result="ACCEPTED",
                              phase="artifact", artifact_digest=digest)
        done = self.event("item", item="K-1", state="done", guarded=True,
                          completion={"type": "artifact", "artifact_digest": digest},
                          evidence="accepted artifact")
        rejected = {**accepted, "result": "REJECTED"}
        self.assertNotIn("missing_artifact_verdict", self.codes([accepted, done]))
        self.assertIn("missing_artifact_verdict", self.codes([accepted, done, rejected]))
        self.assertIn("missing_artifact_verdict", self.codes([done, accepted]))

    def test_audit_fails_when_skipped_executable_completes(self):
        self.model["items"].append({"id": "D-FLIP", "depends_on": [],
                                     "done_by": "decision", "decision": "D-FLIP"})
        self.model["items"].append({"id": "LIVE", "depends_on": ["D-FLIP"],
                                     "requires_outcome": {"D-FLIP": "approved"}})
        refusal = self.event("decision", decision="D-FLIP", state="decided", outcome="refused")
        done = self.event("item", item="LIVE", state="done", guarded=True, evidence="wrong")
        self.assertIn("skipped_item_completed", self.codes([refusal, done]))


def test_released_running_item_can_be_reclaimed(tmp_path):
    """Owner reset 2026-10-07: a worker released its claim while the item stayed RUNNING from its step events;
    the next claimant recovers the item instead of being refused with 'not claimable: running'."""
    import datetime as dt, json, os
    from pravaha_tracker import claims
    model = {"control_plane": {"claims": {"streams": ["K"], "lease_s": 5400}},
             "items": [{"id": "X-1", "owner": "K", "depends_on": [], "track": "K", "title": "x"}], "tracks": [{"id": "K"}], "streams": [{"id": "K"}], "decisions": []}
    events = tmp_path / "EVENTS.jsonl"; events.write_text("")
    os.makedirs(tmp_path / "claims", exist_ok=True)
    now = dt.datetime(2026, 10, 7, 11, 0, tzinfo=dt.timezone.utc)
    first = claims.claim_item(str(events), model, "X-1", "K", "k1", 5400, now=now)
    with open(events, "a") as f:
        f.write(json.dumps({"kind": "item", "actor": "stream-K:k1", "id": "X-1", "state": "running", "step": "s1", "ts": "2026-10-07T11:05:00+00:00"}) + "\n")
    claims.release_claim(str(events), "X-1", "k1", first["claim_id"])
    ev = claims.claim_item(str(events), model, "X-1", "K", "k4", 5400, now=now + dt.timedelta(minutes=20))
    assert ev["state"] == "acquired" and ev["worker_id"] == "k4"


class VelocityAmendmentCases(unittest.TestCase):
    """Amendment §3 and §5: containment completes code-only items; verdicts survive merge-only pushes;
    a lane may hold one waiting claim beside one running claim."""

    def setUp(self):
        self.head, self.merge, self.deployed = "a" * 40, "b" * 40, "c" * 40
        self.now = dt.datetime(2026, 10, 8, tzinfo=dt.timezone.utc).isoformat()
        self.model = {
            "campaign": "fixture", "control_plane": {"guarded_completion": True, "verdict_stream": "V"},
            "streams": [], "decisions": [], "tracks": [{"id": "K", "title": "K"}],
            "items": [{"id": "K-C", "track": "K", "owner": "K", "title": "code only", "depends_on": [],
                       "detector": {"type": "branch_merged", "ref": "origin/k-c"}, "brief": {"owns": ["a.py"]}}],
        }
        pr = {"number": 7, "headRefOid": self.head, "mergeCommit": {"oid": self.merge}, "state": "MERGED"}
        self.proof = {"type": "code", "reviewed_head": self.head, "pr": pr}
        self.review = {"kind": "item", "actor": "stream-K:k1", "item": "K-C", "state": "review",
                       "detail": f"PR #7 @ {self.head}", "ts": self.now}
        self.verdict = {"kind": "verdict", "actor": "stream-V:v1", "item": "K-C", "head": self.head,
                        "phase": "pre_merge", "result": "ACCEPTED", "detail": "diff and item tests", "ts": self.now}

    def done(self, events, proof):
        return guarded_done_event(self.model, events, "K-C", "stream-K:k1", {"status": "done"}, proof)

    def test_code_only_item_completes_on_containment_without_post_deploy_verdict(self):
        proof = {**self.proof, "deploy": {"deployed_sha": self.deployed, "run_id": 42, "contains_merge": True}}
        event = self.done([self.review, self.verdict], proof)
        self.assertTrue(event["guarded"])
        self.assertIn("contains the merge commit", event["evidence"])

    def test_code_only_item_is_refused_without_an_observed_containing_deployment(self):
        with self.assertRaisesRegex(CompletionError, "deployment"):
            self.done([self.review, self.verdict], self.proof)
        with self.assertRaisesRegex(CompletionError, "deployment"):
            self.done([self.review, self.verdict], {**self.proof, "deploy": {"deployed_sha": self.deployed,
                                                                               "run_id": 42, "contains_merge": False}})

    def test_data_writing_item_still_needs_post_deploy_verdict(self):
        model = json.loads(json.dumps(self.model)); model["items"][0]["brief"]["migration"] = "1401_x.sql"
        proof = {**self.proof, "deploy": {"deployed_sha": self.deployed, "run_id": 42, "contains_merge": True}}
        with self.assertRaisesRegex(CompletionError, "post-deploy"):
            guarded_done_event(model, [self.review, self.verdict], "K-C", "stream-K:k1", {"status": "done"}, proof)

    def test_verdict_survives_merge_only_push_but_not_a_new_commit(self):
        """Rewritten for the shared reviewed-patch predicate (plan §6): the tracker asks `kyverdicts.inherits`
        and nothing else; ancestry alone, a missing predicate or any answer other than True inherits nothing."""
        with tempfile.TemporaryDirectory() as repo:
            # Inheritance is decided exclusively by the injected shared predicate.
            # Real git commits add no coverage here and require write access to git.
            h1, h2, h3 = "a" * 40, "d" * 40, "e" * 40
            verdict = {**self.verdict, "head": h1}
            calls = []
            with predicate(True, calls):
                self.assertEqual(accepted_verdict([verdict], "K-C", head=h2, repo=repo), verdict)
                self.assertEqual(calls, [(repo, h1, h2)])
                self.assertIsNone(accepted_verdict([verdict], "K-C", head=h2))              # no repo → never inherited
                self.assertIsNone(accepted_verdict([verdict], "K-C", head=h2, repo=repo, phase="post_deploy"))
                rejected = {**verdict, "result": "REJECTED", "ts": self.now}
                self.assertIsNone(accepted_verdict([verdict, rejected], "K-C", head=h2, repo=repo))
                self.assertEqual(len(calls), 1)      # only the pre-merge verdict of an ACCEPTED head is ever asked about
            with predicate(False, calls):
                self.assertIsNone(accepted_verdict([verdict], "K-C", head=h3, repo=repo))   # a new commit
                self.assertEqual(calls[-1], (repo, h1, h3))
            # h2 only merged main in: the retired ancestry rule would have inherited here; the predicate decides alone
            with no_predicate():
                self.assertIsNone(accepted_verdict([verdict], "K-C", head=h2, repo=repo))
            for answer in (None, 1, "True", {"inherits": True}, RuntimeError("git timed out")):
                with self.subTest(answer=answer), predicate(answer):
                    self.assertIsNone(accepted_verdict([verdict], "K-C", head=h2, repo=repo))
            broken = types.ModuleType("kyverdicts")                                         # no `inherits` at all
            with patch.dict(sys.modules, {"kyverdicts": broken}):
                self.assertIsNone(accepted_verdict([verdict], "K-C", head=h2, repo=repo))
            self.assertFalse(hasattr(verdicts, "merge_only_between"))

    def test_lane_may_hold_one_waiting_claim_beside_one_running_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            events = os.path.join(tmp, "run", "EVENTS.jsonl")
            model = {"control_plane": {"claims": {"streams": ["K"], "lease_s": 10800}},
                     "items": [{"id": "K-1", "owner": "K", "depends_on": []}, {"id": "K-2", "owner": "K", "depends_on": []},
                               {"id": "K-3", "owner": "K", "depends_on": []}]}
            now = dt.datetime(2026, 10, 8, tzinfo=dt.timezone.utc)
            claim_item(events, model, "K-1", "K", "k1", 3600, now=now)
            with self.assertRaisesRegex(ClaimError, "not waiting"):      # K-1 is still being built
                claim_item(events, model, "K-2", "K", "k1", 3600, now=now)
            append(events, {"kind": "item", "actor": "stream-K:k1", "item": "K-1", "state": "review",
                            "detail": "PR #1 @ " + "a" * 40, "ts": now.isoformat()}, model)
            claim_item(events, model, "K-2", "K", "k1", 3600, now=now)   # K-1 waits for a verdict → one more
            with self.assertRaisesRegex(ClaimError, "already holds"):    # two is the ceiling
                claim_item(events, model, "K-3", "K", "k1", 3600, now=now)


def pathlib_write(repo, name, text):
    with open(os.path.join(repo, name), "w", encoding="utf-8") as handle:
        handle.write(text)


class ReadyAtMergeCases(unittest.TestCase):
    """Owner direction 2026-10-08: dependants start once a dependency is merged with an accepted verdict;
    completion and joins still wait for the dependency to be done."""

    def model(self, flag=True):
        return {"campaign": "fixture", "control_plane": {"guarded_completion": True, "verdict_stream": "V",
                                                         "ready_at_merge": flag},
                "streams": [], "decisions": [], "tracks": [{"id": "K", "title": "K"}],
                "items": [{"id": "A", "track": "K", "owner": "K", "title": "a", "depends_on": [],
                           "detector": {"type": "branch_merged", "ref": "origin/a"}},
                          {"id": "B", "track": "K", "owner": "K", "title": "b", "depends_on": ["A"],
                           "detector": {"type": "branch_merged", "ref": "origin/b"}},
                          {"id": "J", "track": "K", "owner": "K", "title": "j", "depends_on": ["A"], "done_by": "join"}]}

    def rows(self, model, events):
        now = dt.datetime(2026, 10, 8, tzinfo=dt.timezone.utc)
        det = {"A": {"status": "done", "detail": "merged", "checked_at": now.isoformat()},
               "B": {"status": "pending", "detail": "no branch", "checked_at": now.isoformat()}}
        snap = build_snapshot(model, events, det, {}, {}, now=now)
        return {r["id"]: r for t in snap["tracks"] for r in t["items"]}

    def test_dependant_ready_when_dependency_merged_and_accepted(self):
        verdict = {"kind": "verdict", "actor": "stream-V:v1", "item": "A", "head": "a" * 40, "phase": "pre_merge",
                   "result": "ACCEPTED", "detail": "ok", "ts": "2026-10-08T00:00:00+00:00"}
        rows = self.rows(self.model(), [verdict])
        self.assertEqual(rows["B"]["status"], "ready")
        self.assertEqual(rows["B"]["deps_open_strict"], ["A"])
        self.assertNotEqual(rows["J"]["status"], "done")          # a join still needs A done

    def test_no_relaxation_without_verdict_or_flag(self):
        self.assertEqual(self.rows(self.model(), [])["B"]["status"], "waiting")
        verdict = {"kind": "verdict", "actor": "stream-V:v1", "item": "A", "head": "a" * 40, "phase": "pre_merge",
                   "result": "ACCEPTED", "detail": "ok", "ts": "2026-10-08T00:00:00+00:00"}
        self.assertEqual(self.rows(self.model(flag=False), [verdict])["B"]["status"], "waiting")


class ReadyAtAcceptedCases(ReadyAtMergeCases):
    def test_dependant_ready_when_dependency_only_accepted(self):
        model = self.model(); model["control_plane"]["ready_at_accepted"] = True
        verdict = {"kind": "verdict", "actor": "stream-V:v1", "item": "A", "head": "a" * 40, "phase": "pre_merge",
                   "result": "ACCEPTED", "detail": "ok", "ts": "2026-10-08T00:00:00+00:00"}
        now = dt.datetime(2026, 10, 8, tzinfo=dt.timezone.utc)
        det = {"A": {"status": "pending", "detail": "open PR", "checked_at": now.isoformat()},
               "B": {"status": "pending", "detail": "no branch", "checked_at": now.isoformat()}}
        snap = build_snapshot(model, [verdict], det, {}, {}, now=now)
        rows = {r["id"]: r for tr in snap["tracks"] for r in tr["items"]}
        self.assertEqual(rows["B"]["status"], "ready")
        rejected = {**verdict, "result": "REJECTED", "ts": "2026-10-08T00:01:00+00:00"}
        snap = build_snapshot(model, [verdict, rejected], det, {}, {}, now=now)
        rows = {r["id"]: r for tr in snap["tracks"] for r in tr["items"]}
        self.assertEqual(rows["B"]["status"], "waiting")


# ---------------------------------------------------------------- KV3-B-TRACKER (relaunch plan v2.7 §6, KU-01)

RULES = ("v_exact_head_then_deploy_containment", "v_exact_head_then_post_deploy_at_merge_commit",
         "v_artifact_digest_reviewer_not_author", "finalizer_independent_review_artifact_digest",
         "v_pre_acceptance_then_receipt_readback_digest", "v_packet_verdict_bound_to_external_review")
CONTAINMENT, POST_DEPLOY, ARTIFACT, FINALIZER, OPERATION, PACKET = RULES


def declared_model() -> dict:
    """A model that declares its items (control_plane.declarations), one item per reviewer rule."""
    def item(item_id, owner, kind, rule, detector, **extra):
        return {"id": item_id, "track": "K", "owner": owner, "producer": owner, "title": item_id, "depends_on": [],
                "completion_kind": kind, "reviewer_rule": rule, "detector": detector, **extra}

    return {
        "campaign": "fixture",
        "control_plane": {
            "guarded_completion": True, "verdict_stream": "V",
            "decision_outcomes": {"final": ["approved", "refused"], "open": ["deferred", "insufficient_evidence"]},
            "declarations": {"completion_kind": {k: k for k in ("code", "artifact", "operation", "packet")},
                             "reviewer_rule": {rule: rule for rule in RULES}}},
        "streams": [{"id": "K"}, {"id": "N"}, {"id": "V"}, {"id": "S"}],
        "decisions": [], "tracks": [{"id": "K", "title": "K"}],
        "items": [
            item("K-C", "K", "code", CONTAINMENT, {"type": "branch_merged", "ref": "origin/k-c"},
                 brief={"owns": ["a.py"]}),
            item("K-D", "K", "code", POST_DEPLOY, {"type": "branch_merged", "ref": "origin/k-d"},
                 brief={"migration": "1401_fixture.sql"}),
            item("N-A", "N", "artifact", ARTIFACT, {"type": "file_exists", "path": "/artifact"}),
            item("N-F", "N", "artifact", FINALIZER, {"type": "file_exists", "path": "/receipt"},
                 brief={"op": ["finalize"]}),
            item("N-OP", "N", "operation", OPERATION, {"type": "file_exists", "path": "/op-receipt"},
                 brief={"op": ["readback_sql"]}),
            item("V-PKT", "V", "packet", PACKET, {"type": "file_contains", "path": "/run/reviews/PKT.VERDICT.json"}),
        ],
    }


class DeclaredCase(unittest.TestCase):
    """Runs one completion through BOTH the guard and the audit, on the same events (KU-01)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        self.model = declared_model()
        self.head, self.merge, self.deployed, self.other = "a" * 40, "b" * 40, "c" * 40, "d" * 40
        self.at = dt.datetime(2026, 10, 12, 2, tzinfo=dt.timezone.utc)
        self.ts = self.at.isoformat()
        self.deploy = {"deployed_sha": self.deployed, "run_id": 42, "contains_merge": True}

    def pr(self, head=None):
        return {"number": 7, "headRefOid": head or self.head, "mergeCommit": {"oid": self.merge}, "state": "MERGED"}

    def review(self, item, head=None):
        return {"kind": "item", "actor": "stream-K:k1", "item": item, "state": "review",
                "detail": f"PR #7 @ {head or self.head}", "ts": self.ts}

    def verdict(self, item, *, head=None, digest=None, phase="pre_merge", result="ACCEPTED", actor="stream-V:v1"):
        return {"kind": "verdict", "actor": actor, "item": item, "head": head, "artifact_digest": digest,
                "phase": phase, "result": result, "detail": "measured", "ts": self.ts}

    def code_proof(self, **extra):
        return {"type": "code", "reviewed_head": self.head, "pr": self.pr(), **extra}

    def both(self, item, events, proof, *, actor=None, later=()):
        """→ (the code the guard refused with, or None; the audit codes for the same completion)."""
        owner = next(row["owner"] for row in self.model["items"] if row["id"] == item)
        actor = actor or ("stream-K:k1" if owner == "K" else "stream-S:sutradhara")
        refused = None
        try:
            guarded_done_event(self.model, list(events), item, actor, {"status": "done", "detail": "observed"}, proof)
        except CompletionError as exc:
            refused = exc.code
            self.assertIsNotNone(refused, f"a refusal on typed evidence names its code: {exc}")
        recorded = {"kind": "item", "actor": actor, "item": item, "state": "done", "guarded": True,
                    "evidence": "fixture", "completion": {"type": proof.get("type"), **proof}, "ts": self.ts}
        findings = audit(self.model, [*events, recorded, *later], self.root, since=self.at - dt.timedelta(minutes=50),
                         now=self.at + dt.timedelta(minutes=10), repo=proof.get("repo"))
        return refused, {finding["code"] for finding in findings if finding["ref"] == item}

    def assert_passes(self, item, events, proof, **kw):
        self.assertEqual(self.both(item, events, proof, **kw), (None, set()))

    def assert_refused(self, code, item, events, proof, **kw):
        """the guard refuses with `code` and the audit reports the same completion under the same code"""
        refused, codes = self.both(item, events, proof, **kw)
        self.assertEqual(refused, code)
        self.assertIn(code, codes)
        return codes


class KU01Fixtures(DeclaredCase):
    """The four acceptance fixtures of KU-01, each on the guard and on the audit."""

    def test_code_only_completion_without_post_deploy_passes(self):
        events = [self.review("K-C"), self.verdict("K-C", head=self.head)]
        self.assert_passes("K-C", events, self.code_proof(deploy=self.deploy))
        # no post_deploy obligation is invented for a code-only item
        self.assertEqual(evidence_requirements(self.model, self.model["items"][0])["evidence"],
                         ("reviewed_head_verdict", "deployment_containment"))

    def test_missing_deployment_containment_fails(self):
        events = [self.review("K-C"), self.verdict("K-C", head=self.head)]
        for deploy in (None, {}, {**self.deploy, "contains_merge": False}, {**self.deploy, "contains_merge": "true"},
                       {**self.deploy, "run_id": None}, {**self.deploy, "deployed_sha": "c" * 39},
                       {**self.deploy, "deployed_sha": None}, "deployed"):
            with self.subTest(deploy=deploy):
                proof = self.code_proof() if deploy is None else self.code_proof(deploy=deploy)
                codes = self.assert_refused("missing_deployment_containment", "K-C", events, proof)
                self.assertNotIn("missing_post_deploy_verdict", codes)
        # a post_deploy verdict is not a substitute for containment on a code-only item
        post = self.verdict("K-C", head=self.merge, phase="post_deploy")
        self.assert_refused("missing_deployment_containment", "K-C", [*events, post], self.code_proof())

    def test_data_writing_completion_needs_post_deploy_at_the_merge_commit(self):
        events = [self.review("K-D"), self.verdict("K-D", head=self.head)]
        post = self.verdict("K-D", head=self.merge, phase="post_deploy")
        self.assert_passes("K-D", [*events, post], self.code_proof())
        self.assert_passes("K-D", [*events, post], self.code_proof(deploy=self.deploy))
        wrong = (
            [],                                                                       # missing
            [self.verdict("K-D", head=self.other, phase="post_deploy")],              # another commit
            [self.verdict("K-D", head=self.head, phase="post_deploy")],               # the reviewed head, not the merge
            [self.verdict("K-D", head=self.merge, phase="pre_merge")],                # the merge commit, wrong phase
            [self.verdict("K-C", head=self.merge, phase="post_deploy")],              # another item
            [post, {**post, "result": "REJECTED"}],                                   # revoked
            [{**post, "actor": "stream-K:k2"}],                                       # not the verdict stream
        )
        for extra in wrong:
            with self.subTest(extra=extra):
                # recorded containment never stands in for the post-deploy verdict
                codes = self.assert_refused("missing_post_deploy_verdict", "K-D", [*events, *extra],
                                            self.code_proof(deploy=self.deploy))
                self.assertNotIn("missing_deployment_containment", codes)

    def test_invalid_inheritance_fails(self):
        old, repo = "e" * 40, "/fixture/repo"
        events = [self.review("K-C"), self.verdict("K-C", head=old)]      # reviewed at `old`; the PR head moved on
        proof = self.code_proof(deploy=self.deploy, repo=repo)
        calls = []
        with predicate(True, calls):
            self.assert_passes("K-C", events, proof)
            self.assertEqual(set(calls), {(repo, old, self.head)})
            # without a repository nothing can be proven: no inheritance
            self.assert_refused("rejected_or_stale_verdict", "K-C", events, self.code_proof(deploy=self.deploy))
        for answer in (False, None, "yes", OSError("no git")):
            with self.subTest(answer=answer), predicate(answer):
                self.assert_refused("rejected_or_stale_verdict", "K-C", events, proof)
        with no_predicate():
            self.assert_refused("rejected_or_stale_verdict", "K-C", events, proof)
        # the latest verdict at any head decides: a later rejection is never inherited past
        rejected = self.verdict("K-C", head="f" * 40, result="REJECTED")
        with predicate(True):
            self.assert_refused("rejected_or_stale_verdict", "K-C", [*events, rejected], proof)

    def test_audit_rechecks_typed_evidence_at_the_end_of_the_log(self):
        events = [self.review("K-D"), self.verdict("K-D", head=self.head),
                  self.verdict("K-D", head=self.merge, phase="post_deploy")]
        self.assert_passes("K-D", events, self.code_proof())
        for revoked, code in ((events[1], "rejected_or_stale_verdict"), (events[2], "missing_post_deploy_verdict")):
            refused, codes = self.both("K-D", events, self.code_proof(), later=[{**revoked, "result": "REJECTED"}])
            self.assertIsNone(refused)                       # the guard saw the log before the revocation
            self.assertEqual(codes, {code})


class EvidenceTableCases(DeclaredCase):
    """Contract rule 2: one table, keyed by reviewer_rule, read by the guard and by the audit."""

    def test_table_covers_every_declared_rule_and_nothing_else(self):
        want = {CONTAINMENT: ("code", ("reviewed_head_verdict", "deployment_containment")),
                POST_DEPLOY: ("code", ("reviewed_head_verdict", "post_deploy_verdict")),
                ARTIFACT: ("artifact", ("artifact_verdict",)),
                FINALIZER: ("artifact", ("artifact_verdict",)),
                OPERATION: ("operation", ("completed_receipt", "artifact_verdict")),
                PACKET: ("packet", ("packet_verdict", "artifact_verdict"))}
        for row in self.model["items"]:
            req = evidence_requirements(self.model, row)
            self.assertEqual((req["completion_kind"], req["evidence"]), want[row["reviewer_rule"]])
            self.assertIsNone(req["conflict"])
        legacy = {**self.model, "control_plane": {"guarded_completion": True, "verdict_stream": "V"}}
        self.assertIsNone(evidence_requirements(legacy, self.model["items"][0]))     # others as today

    def test_committed_model_declares_no_conflict(self):
        with open(COMMITTED_MODEL, encoding="utf-8") as handle:
            model = json.load(handle)
        executable = [row for row in model["items"] if row.get("done_by") not in ("decision", "join")]
        self.assertGreater(len(executable), 100)
        for row in executable:
            req = evidence_requirements(model, row)
            self.assertIsNone(req["conflict"], row["id"])
            self.assertEqual(req["completion_kind"], row["completion_kind"])
            if row["completion_kind"] == "code":
                self.assertEqual("post_deploy_verdict" in req["evidence"], writes_data(row), row["id"])

    def test_writes_data_normalises_migration_metadata(self):
        for brief, expected in (
                (None, False), ({}, False), ("prose", False),
                ({"migration": ""}, False), ({"migration": "  "}, False), ({"migration": "NONE"}, False),
                ({"migration": " NONE "}, False), ({"migration": None}, False), ({"migration": True}, False),
                ({"migration": 1401}, False), ({"migration": {"file": "1401_x.sql"}}, False),
                ({"migration": []}, False), ({"migration": ["NONE", ""]}, False), ({"migration": [1401]}, False),
                ({"op": "NONE"}, False), ({"op": []}, False), ({"migration": "NONE", "op": ["NONE"]}, False),
                ({"migration": "1401_x.sql"}, True), ({"migration": "additive"}, True),
                ({"migration": ["1401_x.sql"]}, True), ({"op": ["readback_sql"]}, True),
                ({"op": "century_dispatch"}, True), ({"migration": "NONE", "op": ["readback_sql"]}, True)):
            with self.subTest(brief=brief):
                self.assertIs(writes_data({"brief": brief}), expected)
        self.assertIs(writes_data({}), False)

    def test_guard_and_audit_refuse_a_proof_of_another_kind(self):
        digest = "f" * 64
        events = [self.review("K-C"), self.verdict("K-C", head=self.head),
                  self.verdict("K-C", digest=digest, phase="artifact"),
                  self.verdict("N-A", head=self.head), self.verdict("N-A", digest=digest, phase="artifact")]
        artifact = {"type": "artifact", "artifact_digest": digest}
        self.assert_refused("completion_kind_mismatch", "K-C", events, artifact)
        code = {"type": "code", "reviewed_head": self.head, "pr": self.pr(), "deploy": self.deploy}
        self.assert_refused("completion_kind_mismatch", "N-A", [*events, {**self.review("N-A"), "actor": "stream-N:n1"}],
                            code)
        self.assert_refused("completion_kind_mismatch", "N-A", events,
                            {"type": "operation", "operation_id": "op-1", "artifact_digest": digest,
                             "receipt": {"operation_id": "op-1", "item_id": "N-A", "status": "COMPLETED"}})
        self.assert_refused("completion_kind_mismatch", "N-A", events, {"artifact_digest": digest})
        self.assert_passes("N-A", events, artifact)

    def test_guard_and_audit_refuse_a_declaration_that_contradicts_the_item(self):
        events = [self.review("K-C"), self.verdict("K-C", head=self.head),
                  self.verdict("K-C", head=self.merge, phase="post_deploy")]
        proof = self.code_proof(deploy=self.deploy)
        self.assert_passes("K-C", events, proof)
        row = self.model["items"][0]
        for change in ({"brief": {"migration": "1402_x.sql"}},                       # data-writing under containment
                       {"reviewer_rule": POST_DEPLOY},                               # post-deploy rule, writes nothing
                       {"reviewer_rule": ARTIFACT}, {"completion_kind": "artifact"},  # rule and kind disagree
                       {"reviewer_rule": "v_trust_me"}, {"reviewer_rule": None}, {"completion_kind": None}):
            with self.subTest(change=change):
                saved = dict(row)
                row.update(change)
                try:
                    self.assertIsNotNone(evidence_requirements(self.model, row)["conflict"])
                    self.assert_refused("declaration_conflict", "K-C", events, proof)
                finally:
                    row.clear()
                    row.update(saved)
        # a rule the table knows but the model's legend does not declare is a conflict too
        del self.model["control_plane"]["declarations"]["reviewer_rule"][CONTAINMENT]
        self.assert_refused("declaration_conflict", "K-C", events, proof)

    def test_reviewed_head_must_be_the_merged_pr_head(self):
        events = [self.review("K-C"), self.verdict("K-C", head=self.head)]
        for pr in ({**self.pr(), "state": "OPEN"}, {**self.pr(), "headRefOid": self.other},
                   {**self.pr(), "mergeCommit": None}, {**self.pr(), "number": "7"}, None):
            with self.subTest(pr=pr):
                self.assert_refused("rejected_or_stale_verdict", "K-C", events,
                                    {"type": "code", "reviewed_head": self.head, "pr": pr, "deploy": self.deploy})
        for verdict in (self.verdict("K-C", head=self.head, result="REJECTED"),
                        self.verdict("K-C", head=self.head, actor="stream-K:k2")):
            with self.subTest(verdict=verdict):
                self.assert_refused("rejected_or_stale_verdict", "K-C", [self.review("K-C"), verdict],
                                    self.code_proof(deploy=self.deploy))

    def test_artifact_and_finalizer_rules_bind_the_digest(self):
        digest = "f" * 64
        for item in ("N-A", "N-F"):
            with self.subTest(item=item):
                accepted = self.verdict(item, digest=digest, phase="artifact")
                self.assert_passes(item, [accepted], {"type": "artifact", "artifact_digest": digest})
                for events, proof_digest in (([], digest), ([accepted], "e" * 64), ([accepted], "f" * 63), ([accepted], None),
                                             ([accepted, {**accepted, "result": "REJECTED"}], digest),
                                             ([{**accepted, "actor": "stream-N:n1"}], digest),
                                             ([self.verdict(item, head=self.head)], digest)):
                    self.assert_refused("missing_artifact_verdict", item, events,
                                        {"type": "artifact", "artifact_digest": proof_digest})

    def test_operation_rule_needs_the_completed_receipt_and_its_digest_verdict(self):
        digest = "d" * 64
        receipt = {"operation_id": "op-42", "item_id": "N-OP", "status": "COMPLETED"}
        os.makedirs(os.path.join(self.root, "ops", "receipts"))
        with open(os.path.join(self.root, "ops", "receipts", "op-42.json"), "w", encoding="utf-8") as handle:
            json.dump(receipt, handle)
        accepted = self.verdict("N-OP", digest=digest, phase="artifact")
        proof = {"type": "operation", "operation_id": "op-42", "receipt": receipt, "artifact_digest": digest}
        self.assert_passes("N-OP", [accepted], proof)
        for bad in ({**receipt, "status": "FAILED"}, {**receipt, "item_id": "N-OTHER"},
                    {**receipt, "operation_id": "op-43"}, None):
            with self.subTest(receipt=bad):
                self.assert_refused("unbound_operation", "N-OP", [accepted], {**proof, "receipt": bad})
        self.assert_refused("unbound_operation", "N-OP", [accepted], {**proof, "operation_id": None})
        # the pre-acceptance record and a script-head verdict are not the receipt verdict (plan §6 POST-READBACK)
        for events in ([], [self.verdict("N-OP", digest="e" * 64, phase="artifact")],
                       [self.verdict("N-OP", head=self.head)], [{**accepted, "result": "REJECTED"}]):
            with self.subTest(events=events):
                self.assert_refused("missing_artifact_verdict", "N-OP", events, proof)

    def test_packet_rule_as_today_on_both_sides(self):
        digest, review = "f" * 64, "e" * 64
        packet = {"item": "V-PKT", "packet": "PKT", "result": "ACCEPTED", "blocking_open": 0, "review_sha256": review}
        accepted = self.verdict("V-PKT", digest=digest, phase="artifact")
        proof = {"type": "packet", "packet": packet, "artifact_digest": digest, "review_sha256": review}
        self.assert_passes("V-PKT", [accepted], proof)
        for bad in ({**packet, "blocking_open": 1}, {**packet, "result": "REJECTED"}, {**packet, "item": "V-PKt"},
                    {**packet, "packet": "OTHER"}, {**packet, "review_sha256": "a" * 64}, {**packet, "blocking_open": False}):
            with self.subTest(packet=bad):
                self.assert_refused("missing_artifact_verdict", "V-PKT", [accepted], {**proof, "packet": bad})
        self.assert_refused("missing_artifact_verdict", "V-PKT", [], proof)

    def test_undeclared_model_completes_and_audits_as_today(self):
        """Rules 2–3 apply only to a declaring model: the legacy audit still asks every code completion for a
        post_deploy verdict and never for containment."""
        legacy = {key: value for key, value in self.model.items() if key != "control_plane"}
        legacy["control_plane"] = {"guarded_completion": True, "verdict_stream": "V"}
        events = [self.review("K-C"), self.verdict("K-C", head=self.head)]
        proof = self.code_proof(deploy=self.deploy)
        event = guarded_done_event(legacy, events, "K-C", "stream-K:k1", {"status": "done"}, proof)
        self.assertIn("contains the merge commit", event["evidence"])
        recorded = {**event, "ts": self.ts}
        codes = {f["code"] for f in audit(legacy, [*events, recorded], self.root,
                                          since=self.at - dt.timedelta(minutes=50), now=self.at)}
        self.assertEqual(codes, {"missing_post_deploy_verdict"})
        with self.assertRaisesRegex(CompletionError, "unknown typed evidence"):
            guarded_done_event(legacy, events, "K-C", "stream-K:k1", {"status": "done"}, {"type": "wish"})


class DeclaredModelCheckCases(unittest.TestCase):
    """Contract rule 1: server.check_model rejects an executable item that does not declare itself."""

    def problems(self, change=None, item="K-C", drop=()):
        model = declared_model()
        row = next(entry for entry in model["items"] if entry["id"] == item)
        row.update(change or {})
        for key in drop:
            row.pop(key)
        return server.check_model(model)

    def test_declared_fixture_and_committed_model_pass(self):
        self.assertEqual(self.problems(), [])
        with open(COMMITTED_MODEL, encoding="utf-8") as handle:
            self.assertEqual(server.check_model(json.load(handle)), [])

    def test_each_missing_or_wrong_declaration_is_rejected(self):
        for label, kwargs in (
                ("completion_kind", {"drop": ("completion_kind",)}),
                ("completion_kind", {"change": {"completion_kind": "review"}}),
                ("producer", {"drop": ("producer",)}),
                ("producer", {"change": {"producer": "S"}}),
                ("reviewer_rule", {"drop": ("reviewer_rule",)}),
                ("reviewer_rule", {"change": {"reviewer_rule": "v_trust_me"}}),
                ("detector", {"drop": ("detector",)}),
                ("detector", {"change": {"detector": None}}),
                ("step_evidence", {"change": {"steps": ["tests"],
                                              "step_evidence": {"tests": {"detector": None}, "docs": {"detector": None}}}}),
                ("step_evidence", {"change": {"step_evidence": {"tests": {"detector": None}}}}),
                ("step_evidence", {"change": {"steps": ["tests"], "step_evidence": ["tests"]}}),
                ("join", {"change": {"join": True}}),
                ("join", {"change": {"done_by": "join"}}),
                ("join", {"change": {"done_by": "join", "join": False}})):
            with self.subTest(label=label, kwargs=kwargs):
                problems = self.problems(**kwargs)
                self.assertTrue([text for text in problems if text.startswith("K-C") and label in text], problems)

    def test_decision_and_join_items_declare_nothing_and_steps_may_be_declared(self):
        model = declared_model()
        model["decisions"].append({"id": "D-1", "title": "decision"})
        model["items"] += [
            {"id": "D-1", "track": "K", "owner": "N", "title": "decision", "depends_on": [],
             "done_by": "decision", "decision": "D-1"},
            {"id": "J-1", "track": "K", "owner": "S", "title": "join", "depends_on": ["K-C"],
             "done_by": "join", "join": True}]
        model["items"][0].update(steps=["tests", "docs"], step_evidence={"tests": {"evidence": "pr_head_evidence",
                                                                                   "detector": None}})
        self.assertEqual(server.check_model(model), [])

    def test_undeclared_model_is_checked_as_today(self):
        model = declared_model()
        del model["control_plane"]["declarations"]
        for row in model["items"]:
            for key in ("completion_kind", "producer", "reviewer_rule", "detector"):
                row.pop(key)
        model["items"][0]["join"] = True
        self.assertEqual(server.check_model(model), [])


class VerdictSlotCases(unittest.TestCase):
    """Contract rule 5: a verdict comes from a slot, and never from a slot that registered the item's review."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.events = os.path.join(self.tmp.name, "EVENTS.jsonl")
        self.model = declared_model()
        self.verdict = {"kind": "verdict", "actor": "stream-V:v1", "item": "K-C", "head": "a" * 40,
                        "phase": "pre_merge", "result": "ACCEPTED", "detail": "measured"}

    def lines(self):
        with open(self.events, encoding="utf-8") as handle:
            return [json.loads(line) for line in handle]

    def test_verdict_actor_needs_a_slot(self):
        append(self.events, {"kind": "item", "actor": "stream-K:k1", "item": "K-C", "state": "review",
                             "detail": "PR #7 @ " + "a" * 40}, self.model)
        for actor in ("stream-V", "stream-V:", "stream-V: "):
            with self.subTest(actor=actor), self.assertRaisesRegex(EventError, "slot"):
                append(self.events, {**self.verdict, "actor": actor}, self.model)
        self.assertEqual(len(self.lines()), 1)
        append(self.events, self.verdict, self.model)
        self.assertEqual(self.lines()[-1]["actor"], "stream-V:v1")

    def test_verdict_slot_differs_from_every_slot_that_registered_a_review(self):
        for actor in ("stream-K:k1", "stream-K:k2"):
            append(self.events, {"kind": "item", "actor": actor, "item": "K-C", "state": "review",
                                 "detail": "PR #7 @ " + "a" * 40}, self.model)
        append(self.events, {"kind": "item", "actor": "stream-K:k3", "item": "K-C", "state": "running"}, self.model)
        append(self.events, {"kind": "item", "actor": "stream-K:k4", "item": "K-D", "state": "review",
                             "detail": "PR #8 @ " + "b" * 40}, self.model)
        for slot in ("k1", "k2"):
            with self.subTest(slot=slot), self.assertRaisesRegex(EventError, "slot"):
                append(self.events, {**self.verdict, "actor": f"stream-V:{slot}"}, self.model)
        self.assertEqual(len(self.lines()), 4)
        for slot in ("k3", "k4", "v1"):       # k3 only ran the item; k4 registered another item's review
            append(self.events, {**self.verdict, "actor": f"stream-V:{slot}"}, self.model)
        self.assertEqual(len(self.lines()), 7)

    def test_undeclared_model_keeps_todays_verdict_rule(self):
        legacy = {"control_plane": {"verdict_stream": "V"}, "items": [{"id": "K-C", "owner": "K"}]}
        append(self.events, {"kind": "item", "actor": "stream-K:k1", "item": "K-C", "state": "review",
                             "detail": "PR #7 @ " + "a" * 40}, legacy)
        append(self.events, {**self.verdict, "actor": "stream-V"}, legacy)
        append(self.events, {**self.verdict, "actor": "stream-V:k1"}, legacy)
        self.assertEqual(len(self.lines()), 3)


class StepGuardCases(unittest.TestCase):
    """Contract rule 6 (plan §6 STEP): a step is recorded only after its named detector passed, live."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.events = os.path.join(self.tmp.name, "EVENTS.jsonl")
        self.evidence = os.path.join(self.tmp.name, "tests.log")
        with open(self.evidence, "wb") as handle:
            handle.write(b"12 passed\n")
        self.spec = {"type": "file_exists", "path": os.path.join(self.tmp.name, "marker")}
        self.model = declared_model()
        self.model["items"][0].update(steps=["tests", "docs"], step_evidence={
            "tests": {"evidence": "pr_head_evidence", "detector": self.spec},
            "docs": {"evidence": "pr_head_evidence", "detector": None}})
        self.asked = []

    def live(self, status="done", via="live", **override):
        def get(path, timeout=3.0):
            self.asked.append(path)
            body = {"item": "K-C", "step": "tests", "spec": self.spec,
                    "detector": {"status": status, "detail": "fixture"}, **override}
            return body, via
        return get

    def run_step(self, argv, get=None):
        with patch.object(cli, "load_model", return_value=self.model), patch.object(cli, "EVENTS", self.events), \
                patch.object(cli, "get", side_effect=get or self.live()), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return cli.main(argv)

    def written(self):
        if not os.path.exists(self.events):
            return []
        with open(self.events, encoding="utf-8") as handle:
            return [json.loads(line) for line in handle]

    def test_step_is_recorded_with_absolute_path_and_digest_after_live_verification(self):
        relative = os.path.relpath(self.evidence)
        self.assertEqual(self.run_step(["step", "K-C", "tests", "--stream", "K", "--evidence", relative]), 0)
        event = self.written()[-1]
        self.assertEqual((event["item"], event["step"], event["state"]), ("K-C", "tests", "done"))
        self.assertTrue(os.path.isabs(event["evidence"]))
        self.assertEqual(os.path.realpath(event["evidence"]), os.path.realpath(self.evidence))
        self.assertEqual(event["evidence_sha256"], hashlib.sha256(b"12 passed\n").hexdigest())
        self.assertEqual(self.asked, ["/api/verify?id=K-C&step=tests"])

    def test_step_is_refused_and_nothing_written(self):
        ok = ["step", "K-C", "tests", "--stream", "K", "--evidence", self.evidence]
        missing = os.path.join(self.tmp.name, "absent.log")
        cases = (
            ("undeclared step", ["step", "K-C", "lint", "--stream", "K", "--evidence", self.evidence], None),
            ("null detector", ["step", "K-C", "docs", "--stream", "K", "--evidence", self.evidence], None),
            ("item without steps", ["step", "K-D", "tests", "--stream", "K", "--evidence", self.evidence], None),
            ("unknown item", ["step", "K-X", "tests", "--stream", "K", "--evidence", self.evidence], None),
            ("no evidence", ["step", "K-C", "tests", "--stream", "K"], None),
            ("evidence absent", ["step", "K-C", "tests", "--stream", "K", "--evidence", missing], None),
            ("evidence is a directory", ["step", "K-C", "tests", "--stream", "K", "--evidence", self.tmp.name], None),
            ("tracker not live", ok, self.live(via="stale-snapshot")),
            ("tracker unavailable", ok, lambda path, timeout=3.0: (None, "unavailable")),
            ("detector pending", ok, self.live(status="pending")),
            ("detector error", ok, self.live(status="error")),
            ("no detector result", ok, self.live(detector=None)),
            ("another item verified", ok, self.live(item="K-D")),
            ("another step verified", ok, self.live(step="docs")),
            ("item-level verification", ok, self.live(step=None)),
            ("another detector verified", ok, self.live(spec={"type": "file_exists", "path": "/elsewhere"})),
            ("another stream", ["step", "K-C", "tests", "--stream", "N", "--evidence", self.evidence], None),
        )
        for label, argv, get in cases:
            with self.subTest(label=label):
                self.assertEqual(self.run_step(argv, get), 2)
                self.assertEqual(self.written(), [])
        # a step without a named detector never reaches the tracker at all
        self.asked.clear()
        self.run_step(["step", "K-C", "docs", "--stream", "K", "--evidence", self.evidence])
        self.assertEqual(self.asked, [])

    def test_undeclared_model_records_a_step_as_today(self):
        del self.model["control_plane"]["declarations"]
        self.assertEqual(self.run_step(["step", "K-C", "docs", "--stream", "K"]), 0)
        self.assertEqual(self.written()[-1]["evidence"], "step docs reported by stream-K")
        self.assertEqual(self.asked, [])


class TrackerServiceCases(unittest.TestCase):
    """Rule 6 (`/api/verify?...&step=`), rule 7 (`ky next --json` rows) and the read-only guarantee, against an
    engine this test starts on a temporary home (never the installed tracker)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = self.tmp.name
        os.makedirs(os.path.join(self.home, "run"))
        self.marker = os.path.join(self.home, "marker")
        self.model = declared_model()
        self.model["items"][0].update(steps=["tests", "docs"], step_evidence={
            "tests": {"evidence": "pr_head_evidence", "detector": {"type": "file_exists", "path": self.marker}},
            "docs": {"evidence": "pr_head_evidence", "detector": None}})
        self.model_path = os.path.join(self.home, "plan_model.json")
        with open(self.model_path, "w", encoding="utf-8") as handle:
            json.dump(self.model, handle)
        self.events = os.path.join(self.home, "run", "EVENTS.jsonl")
        self.cfg = {"home": self.home, "events": self.events,
                    "snapshot": os.path.join(self.home, "run", "snapshot.json"),
                    "backup_dir": os.path.join(self.home, "run", "backup"),
                    "hold": os.path.join(self.home, "run", "HOLD"), "model": self.model_path, "repo": self.home,
                    "pgenv": None, "db_port": 1, "detectors_enabled": False, "git_every_s": 3600, "backup_every_s": 0}

    def serve(self):
        engine = server.Engine(self.cfg)
        engine.tick()
        self.assertIsNone(engine.model_error)
        httpd = server._QuietServer(("127.0.0.1", 0), server.make_handler(engine))
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()

        def stop():
            httpd.shutdown()
            httpd.server_close()
            thread.join(5)
        self.addCleanup(stop)
        return f"http://127.0.0.1:{httpd.server_address[1]}"

    def fetch(self, url):
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def test_verify_measures_the_named_step_detector(self):
        base = self.serve()
        status, body = self.fetch(base + "/api/verify?id=K-C&step=tests")
        self.assertEqual((status, body["item"], body["step"]), (200, "K-C", "tests"))
        self.assertEqual(body["detector"]["status"], "pending")
        self.assertEqual(body["spec"], {"type": "file_exists", "path": self.marker})
        with open(self.marker, "w", encoding="utf-8") as handle:
            handle.write("ok")
        self.assertEqual(self.fetch(base + "/api/verify?id=K-C&step=tests")[1]["detector"]["status"], "done")
        for query in ("id=K-C&step=docs", "id=K-C&step=lint", "id=K-D&step=tests", "id=K-X&step=tests", "id=K-C&step="):
            with self.subTest(query=query):
                self.assertEqual(self.fetch(base + "/api/verify?" + query)[0], 404)
        status, body = self.fetch(base + "/api/verify?id=N-A")           # the item-level check is unchanged
        self.assertEqual((status, body["item"]), (200, "N-A"))
        self.assertNotIn("step", body)

    def test_next_rows_carry_the_declaration(self):
        append(self.events, {"kind": "item", "actor": "stream-K:k1", "item": "K-C", "state": "running"}, self.model)
        status, body = self.fetch(self.serve() + "/api/next?stream=K")
        self.assertEqual(status, 200)
        row = next(entry for entry in body["running"] if entry["id"] == "K-C")
        self.assertEqual((row["completion_kind"], row["producer"], row["reviewer_rule"]), ("code", "K", CONTAINMENT))
        self.assertEqual(row["step_evidence"], self.model["items"][0]["step_evidence"])
        self.assertEqual([step["name"] for step in row["steps"]], ["tests", "docs"])

    def test_model_load_tick_and_audit_leave_the_event_log_untouched(self):
        ts = "2026-10-12T02:00:00+00:00"
        lines = [{"kind": "item", "actor": "stream-K:k1", "item": "K-C", "state": "review",
                  "detail": "PR #7 @ " + "a" * 40, "ts": ts},
                 {"kind": "verdict", "actor": "stream-V:v1", "item": "K-C", "head": "a" * 40, "phase": "pre_merge",
                  "result": "ACCEPTED", "detail": "measured", "ts": ts},
                 {"kind": "item", "actor": "stream-K:k1", "item": "K-C", "state": "done", "guarded": True,
                  "evidence": "PR #7", "ts": ts, "completion": {"type": "code", "reviewed_head": "a" * 40}}]
        raw = "".join(json.dumps(line) + "\n" for line in lines).encode() + b"not json\n"
        with open(self.events, "wb") as handle:
            handle.write(raw)
        before = (raw, os.stat(self.events).st_mtime_ns, os.stat(self.events).st_ino)
        engine = server.Engine(self.cfg)
        for _ in range(3):
            engine.tick()
        self.assertEqual(len(engine.log.events), 3)
        self.assertTrue(os.path.exists(self.cfg["snapshot"]))
        out = io.StringIO()
        with patch.object(cli, "MODEL", self.model_path), patch.object(cli, "EVENTS", self.events), \
                contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["audit", "--since", "kickoff"]), 1)
        self.assertIn("FAIL missing_deployment_containment K-C: ", out.getvalue())
        with open(self.events, "rb") as handle:
            after = (handle.read(), os.stat(self.events).st_mtime_ns, os.stat(self.events).st_ino)
        self.assertEqual(after, before)


class AuditCommandCases(DeclaredCase):
    """Contract rule 3: `ky audit` passes the repository as `ky done` does; its lines and exit codes are unchanged."""

    def run_audit(self, events, **patches):
        path = os.path.join(self.root, "EVENTS.jsonl")
        with open(path, "w", encoding="utf-8") as handle:
            handle.writelines(json.dumps(event) + "\n" for event in events)
        out = io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(cli, "EVENTS", path))
            stack.enter_context(patch.object(cli, "load_model", return_value=self.model))
            for name, value in patches.items():
                stack.enter_context(patch.object(cli, name, value))
            stack.enter_context(contextlib.redirect_stdout(out))
            stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
            code = cli.main(["audit", "--since", "kickoff"])
        return code, out.getvalue().splitlines()

    def done(self, item, completion):
        return {"kind": "item", "actor": "stream-K:k1", "item": item, "state": "done", "guarded": True,
                "evidence": "fixture", "completion": completion, "ts": self.ts}

    def test_audit_passes_the_repository_to_the_shared_predicate(self):
        old = "e" * 40
        events = [self.review("K-C"), self.verdict("K-C", head=old),
                  self.done("K-C", {**self.code_proof(deploy=self.deploy), "repo": "/recorded/by/the/event"})]
        calls = []
        with predicate(True, calls), patch.dict(os.environ, {"PRAVAHA_REPO": "/fixture/repo"}):
            self.assertEqual(self.run_audit(events), (0, ["AUDIT PASS: 0 findings"]))
        self.assertEqual(set(calls), {("/fixture/repo", old, self.head)})     # never the path an event recorded
        with predicate(True, calls), patch.dict(os.environ, clear=False) as env:
            env.pop("PRAVAHA_REPO", None)
            self.run_audit(events)
        self.assertEqual(calls[-1][0], cli.REPO_ROOT)
        with predicate(False):
            code, lines = self.run_audit(events)
        self.assertEqual(code, 1)
        self.assertRegex(lines[0], r"^FAIL rejected_or_stale_verdict K-C: \S")
        self.assertEqual(lines[-1], "AUDIT FAIL: 1 findings")

    def test_every_finding_is_printed_and_counted(self):
        events = [self.review("K-C"), self.verdict("K-C", head=self.head), self.done("K-C", self.code_proof()),
                  self.done("K-D", self.code_proof(deploy=self.deploy)),
                  self.done("N-A", {"type": "code", "reviewed_head": self.head}),
                  self.done("N-OP", {"type": "operation"})]
        code, lines = self.run_audit(events)
        self.assertEqual(code, 1)
        fails = [line for line in lines if line.startswith("FAIL ")]
        self.assertEqual(lines[-1], f"AUDIT FAIL: {len(fails)} findings")
        self.assertEqual(len(lines), len(fails) + 1)
        for line in fails:
            self.assertRegex(line, r"^FAIL [a-z_]+ [A-Za-z0-9-]+: \S")
        found = {tuple(line.split(":")[0].split()[1:]) for line in fails}
        self.assertLessEqual({("missing_deployment_containment", "K-C"), ("rejected_or_stale_verdict", "K-D"),
                              ("missing_post_deploy_verdict", "K-D"), ("completion_kind_mismatch", "N-A"),
                              ("unbound_operation", "N-OP"), ("missing_artifact_verdict", "N-OP")}, found)
        self.assertNotIn(("missing_post_deploy_verdict", "K-C"), found)

    def test_audit_unavailable_is_exit_2(self):
        def broken():
            raise OSError("no model")
        code, lines = self.run_audit([], load_model=broken)
        self.assertEqual((code, lines), (2, []))


class DeclaredSnapshotCases(unittest.TestCase):
    """Contract rule 7: rows carry the declaration; a staged retirement is not a question for the owner."""

    def setUp(self):
        self.now = dt.datetime(2026, 10, 12, tzinfo=dt.timezone.utc)
        self.model = declared_model()
        self.model["items"][0].update(steps=["tests"], step_evidence={"tests": {"evidence": "pr_head_evidence",
                                                                                "detector": None}})
        self.model["decisions"] = [{"id": "D-RETIRE-K-R", "title": "Retire K-R"}, {"id": "D-ASK", "title": "Ask"}]
        self.model["items"] += [
            {"id": "D-RETIRE-K-R", "track": "K", "owner": "N", "title": "retire", "depends_on": [],
             "done_by": "decision", "decision": "D-RETIRE-K-R", "triage": {"class": "retire_decision", "retires": "K-R"}},
            {"id": "D-ASK", "track": "K", "owner": "N", "title": "ask", "depends_on": [],
             "done_by": "decision", "decision": "D-ASK", "triage": {"class": "a"}},
            {"id": "K-R", "track": "K", "owner": "K", "producer": "K", "title": "retired work",
             "depends_on": ["D-RETIRE-K-R"], "requires_outcome": {"D-RETIRE-K-R": "approved"},
             "completion_kind": "code", "reviewer_rule": CONTAINMENT,
             "detector": {"type": "branch_merged", "ref": "origin/k-r"}, "triage": {"class": "retired"}}]

    def snapshot(self, events=(), model=None):
        return build_snapshot(model or self.model, list(events), {}, {}, {}, now=self.now)

    @staticmethod
    def rows(snapshot):
        return {row["id"]: row for track in snapshot["tracks"] for row in track["items"]}

    def test_rows_carry_the_declaration_and_nothing_else_changes(self):
        self.assertEqual(server.check_model(self.model), [])
        declared = self.rows(self.snapshot())
        by_id = {row["id"]: row for row in self.model["items"]}
        added = ("completion_kind", "producer", "reviewer_rule", "step_evidence")
        for item_id, row in declared.items():
            for key in added:
                self.assertEqual(row[key], by_id[item_id].get(key), (item_id, key))
        self.assertEqual(declared["K-C"]["step_evidence"], {"tests": {"evidence": "pr_head_evidence", "detector": None}})
        self.assertIsNone(declared["D-ASK"]["completion_kind"])
        legacy_model = json.loads(json.dumps(self.model))
        del legacy_model["control_plane"]["declarations"]
        legacy = self.rows(self.snapshot(model=legacy_model))
        for item_id, row in legacy.items():
            self.assertFalse(set(added) & set(row))
            self.assertEqual({key: value for key, value in declared[item_id].items() if key not in added}, row)

    def test_staged_retirement_is_marked_and_kept_out_of_the_native_queue(self):
        snapshot = self.snapshot()
        decisions = {row["id"]: row for row in snapshot["decisions"]}
        self.assertIs(decisions["D-RETIRE-K-R"]["staged"], True)
        self.assertNotIn("staged", decisions["D-ASK"])
        self.assertEqual([row["id"] for row in snapshot["native_queue"]], ["D-ASK"])
        self.assertEqual(self.rows(snapshot)["K-R"]["status"], "waiting")       # staged is not published
        # a request, or an open outcome, is still no final outcome
        requested = {"kind": "decision", "actor": "stream-K:k1", "decision": "D-RETIRE-K-R", "state": "requested",
                     "detail": "please", "ts": self.now.isoformat()}
        deferred = {"kind": "decision", "actor": "steward", "decision": "D-RETIRE-K-R", "state": "decided",
                    "outcome": "deferred", "detail": "later", "ts": self.now.isoformat()}
        for events in ([requested], [requested, deferred]):
            snapshot = self.snapshot(events)
            self.assertIs({row["id"]: row for row in snapshot["decisions"]}["D-RETIRE-K-R"]["staged"], True)
            self.assertEqual([row["id"] for row in snapshot["native_queue"]], ["D-ASK"])
        # without the declaration block the same model reads as today
        legacy_model = json.loads(json.dumps(self.model))
        del legacy_model["control_plane"]["declarations"]
        snapshot = self.snapshot(model=legacy_model)
        self.assertEqual({row["id"] for row in snapshot["native_queue"]}, {"D-RETIRE-K-R", "D-ASK"})
        self.assertFalse([row for row in snapshot["decisions"] if "staged" in row])

    def test_snapshot_and_audit_never_publish_the_staged_decision(self):
        events = []
        self.snapshot(events)
        audit(self.model, events, tempfile.gettempdir(), since=self.now, now=self.now)
        self.assertEqual(events, [])

    def test_published_refusal_makes_the_retired_item_not_applicable(self):
        """B-2 publishes with `ky decide <D-id> --outcome refused --as steward --delegated --detail "<text>"`."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "EVENTS.jsonl")
            with patch.object(cli, "EVENTS", path), patch.object(cli, "load_model", return_value=self.model), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(["decide", "D-RETIRE-K-R", "--outcome", "refused", "--as", "steward",
                                           "--delegated", "--detail", "retired by owner decision"]), 0)
            with open(path, encoding="utf-8") as handle:
                events = [json.loads(line) for line in handle]
        self.assertEqual((events[0]["state"], events[0]["outcome"], events[0]["actor"]),
                         ("delegated", "refused", "steward"))
        snapshot = self.snapshot(events)
        rows = self.rows(snapshot)
        self.assertEqual(rows["K-R"]["status"], "not_applicable")
        self.assertEqual(rows["K-R"]["skip_origin"], ["D-RETIRE-K-R"])
        self.assertNotIn("staged", {row["id"]: row for row in snapshot["decisions"]}["D-RETIRE-K-R"])
        self.assertEqual([row["id"] for row in snapshot["native_queue"]], ["D-ASK"])

    def test_committed_model_stages_exactly_its_two_retirements(self):
        with open(COMMITTED_MODEL, encoding="utf-8") as handle:
            model = json.load(handle)
        snapshot = self.snapshot(model=model)
        staged = {row["id"] for row in snapshot["decisions"] if row.get("staged")}
        self.assertEqual(staged, {"D-RETIRE-B-K-INBOX", "D-RETIRE-B-CLAIM-RECOVERY"})
        self.assertFalse(staged & {row["id"] for row in snapshot["native_queue"]})


class InboxContractCases(unittest.TestCase):
    """Contract rule 8, pinned for kyloop.py `poll_inboxes`: exit 0 with a JSON list carrying msg_id, 1 when empty."""

    def test_inbox_json_exit_codes(self):
        model = {"control_plane": {"message_policy": {"S": ["K"], "K": ["S"]}},
                 "streams": [{"id": "S"}, {"id": "K"}], "items": []}
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "EVENTS.jsonl")

            def inbox(*args):
                out = io.StringIO()
                with patch.object(cli, "EVENTS", path), patch.object(cli, "load_model", return_value=model), \
                        contextlib.redirect_stdout(out):
                    return cli.main(["inbox", *args, "--json"]), json.loads(out.getvalue())

            self.assertEqual(inbox("--stream", "S"), (1, []))
            self.assertEqual(inbox("--steward"), (1, []))
            append(path, {"kind": "message", "actor": "stream-K", "to": "S", "msg_id": "M1", "detail": "for S"}, model)
            append(path, {"kind": "message", "actor": "stream-K", "to": "steward", "msg_id": "M2", "detail": "for steward"}, model)
            code, messages = inbox("--stream", "S")
            self.assertEqual((code, [message["msg_id"] for message in messages]), (0, ["M1"]))
            code, messages = inbox("--steward")
            self.assertEqual((code, [message["msg_id"] for message in messages]), (0, ["M2"]))
            append(path, {"kind": "ack", "actor": "stream-S", "msg_id": "M1"}, model)
            self.assertEqual(inbox("--stream", "S"), (1, []))
