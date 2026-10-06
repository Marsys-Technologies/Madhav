"""KĀLA-YANTRA control-plane acceptance cases, built out one capability at a time."""
from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
import threading
import unittest

from pravaha_tracker.claims import ClaimError, claim_item, renew_claim
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
