"""KĀLA-YANTRA control-plane acceptance cases, built out one capability at a time."""
from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
import threading
import unittest

from pravaha_tracker.claims import ClaimError, claim_item, renew_claim


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
