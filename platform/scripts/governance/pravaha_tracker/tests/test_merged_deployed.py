"""SR-BOLD-07: a code item is done when its PR is merged AND contained in a successful deploy of main.

The PR's merged review is the acceptance — no per-item verdict event, no post-deploy verdict. Operation items still
close from executor receipts and decisions from the ledger. Oracle for every claim: the owner ruling SR-BOLD-07
(DECISIONS_SURROGATE.jsonl), plan v3.0 §C (deployment containment = a successful `workflow_run` deploy of main whose
sha contains the merge commit, cli.observe_containment) and A7 D-46 (done with open gates = implemented, with
`activation_pending`).
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pravaha_tracker import detectors as D
from pravaha_tracker import merged_deployed as M
from pravaha_tracker.state import build_snapshot

NOW = dt.datetime(2026, 10, 18, tzinfo=dt.timezone.utc)
MERGE = "a" * 40
BUNDLE_MERGE = "b" * 40
DEPLOYED = "c" * 40
OTHER = "d" * 40


class FakeSource:
    """What GitHub and git would say. `deployed_merges` are the merge commits a successful main deploy contains."""

    def __init__(self, prs=None, diffs=None, trees=None, deployed_merges=(), heads=None, commits=None):
        self.prs, self.diffs, self.trees = prs or {}, diffs or {}, trees or {}
        self.deployed_merges, self.heads = set(deployed_merges), heads or {}
        self.commits = commits or {}

    def pr(self, number):
        return self.prs.get(number)

    def merged_prs_for_branch(self, branch):
        return self.heads.get(branch, [])

    def pr_of_commit(self, sha):
        return self.commits.get(sha)

    def diff_paths(self, merge):
        return frozenset(self.diffs.get(merge, ()))

    def has_path(self, merge, path):
        return path in self.trees.get(merge, self.diffs.get(merge, ()))

    def deployed(self, merge):
        if merge in self.deployed_merges:
            return {"deployed_sha": DEPLOYED, "run_id": 777, "contains_merge": True}
        return {"deployed_sha": None, "run_id": None, "contains_merge": False}


def merged(number, merge, head="f" * 40):
    return {"number": number, "state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge}}


def item(iid, detector, owns=(), kind="code", **extra):
    brief = {"owns": list(owns)} if owns is not None else {}
    return {"id": iid, "title": iid, "track": "K", "owner": "K", "completion_kind": kind, "detector": detector,
            "brief": brief, **extra}


def model_of(*items, guarded=True):
    return {"control_plane": {"guarded_completion": guarded, "declarations": {"reviewer_rule": {}}},
            "tracks": [{"id": "K", "title": "K"}], "decisions": [], "streams": [], "items": list(items)}


def rows_of(model, derived, events=()):
    detectors = {i["id"]: {"status": "done", "detail": "merged", "checked_at": NOW.isoformat()}
                 for i in model["items"] if i.get("detector")}
    snap = build_snapshot(model, list(events), detectors, {}, {}, now=NOW, derived_done=derived)
    return {row["id"]: row for track in snap["tracks"] for row in track["items"]}


# ---- claim 1: merged and deployed, no verdict event -> done ---------------------------------------------------
def test_merged_and_deployed_code_item_is_done_with_no_verdict_event():
    own = item("K-OWN", {"type": "pr_merged", "pr": 10}, owns=["a.py"])
    model = model_of(own)
    source = FakeSource(prs={10: merged(10, MERGE)}, diffs={MERGE: ["a.py"]}, deployed_merges=[MERGE])
    derived = M.derive(model, source)
    assert derived["K-OWN"]["pr"] == 10 and derived["K-OWN"]["merge_commit"] == MERGE
    assert derived["K-OWN"]["deploy_run_id"] == 777 and derived["K-OWN"]["deployed_sha"] == DEPLOYED
    row = rows_of(model, derived)["K-OWN"]          # the event log is empty: no verdict, no guarded done event
    assert row["status"] == "done" and row["source"] == M.SOURCE and row["completion_type"] == "code"
    assert "PR #10 merged" in row["evidence"] and row["merged_pr"] == 10


def test_implemented_with_open_dependency_keeps_activation_pending():
    """A7 D-46 composes: the derived done is 'implemented'; its open gate is still named."""
    gate = {"id": "K-GATE", "title": "gate", "track": "K", "owner": "K"}
    own = item("K-OWN", {"type": "pr_merged", "pr": 10}, owns=["a.py"], depends_on=["K-GATE"])
    model = model_of(gate, own)
    source = FakeSource(prs={10: merged(10, MERGE)}, diffs={MERGE: ["a.py"]}, deployed_merges=[MERGE])
    row = rows_of(model, M.derive(model, source))["K-OWN"]
    assert row["status"] == "done" and row["activation_pending"] == ["K-GATE"]


# ---- claim 2: merged but not deployed -> not done --------------------------------------------------------------
def test_merged_but_not_deployed_is_not_done():
    model = model_of(item("K-OWN", {"type": "pr_merged", "pr": 10}, owns=["a.py"]))
    source = FakeSource(prs={10: merged(10, MERGE)}, diffs={MERGE: ["a.py"]}, deployed_merges=[OTHER])
    assert M.derive(model, source) == {}
    assert rows_of(model, {})["K-OWN"]["status"] != "done"


def test_a_deploy_observation_that_does_not_say_it_contains_the_merge_is_not_enough():
    class Uncontained(FakeSource):
        def deployed(self, merge):
            return {"deployed_sha": DEPLOYED, "run_id": 777, "contains_merge": False}
    model = model_of(item("K-OWN", {"type": "pr_merged", "pr": 10}, owns=["a.py"]))
    assert M.derive(model, Uncontained(prs={10: merged(10, MERGE)}, diffs={MERGE: ["a.py"]})) == {}


# ---- claim 3: open PR -> not done -------------------------------------------------------------------------------
@pytest.mark.parametrize("state", ["OPEN", "CLOSED"])
def test_unmerged_pr_is_not_done_even_if_its_commit_is_in_a_deploy(state):
    model = model_of(item("K-OWN", {"type": "pr_merged", "pr": 10}, owns=["a.py"]))
    pr = {"number": 10, "state": state, "headRefOid": "f" * 40, "mergeCommit": {"oid": MERGE}}
    source = FakeSource(prs={10: pr}, diffs={MERGE: ["a.py"]}, deployed_merges=[MERGE])
    assert M.derive(model, source) == {}


def test_branch_ref_with_only_an_open_pr_is_not_done():
    model = model_of(item("K-BR", {"type": "branch_merged", "ref": "origin/kalayantra/x"}, owns=["a.py"]))
    source = FakeSource(prs={11: {"number": 11, "state": "OPEN", "mergeCommit": None}}, deployed_merges=[MERGE])
    assert M.derive(model, source) == {}


# ---- claim 4: bundle child ---------------------------------------------------------------------------------------
def bundle_model():
    detector = {"type": "branch_merged", "ref": BUNDLE_MERGE, "packet_pr": 3502}
    return model_of(item("J-CHILD", detector, owns=["svc/p1.py", "tests/test_p1.py"]),
                    item("J-STRANGER", detector, owns=["elsewhere/other.py"]))


def test_bundle_child_whose_owned_paths_are_in_a_merged_deployed_bundle_pr_is_done():
    model = bundle_model()
    source = FakeSource(prs={3502: merged(3502, BUNDLE_MERGE)}, diffs={BUNDLE_MERGE: ["svc/p1.py", "tests/test_p1.py", "x"]},
                        deployed_merges=[BUNDLE_MERGE])
    derived = M.derive(model, source)
    assert derived["J-CHILD"]["pr"] == 3502
    assert rows_of(model, derived)["J-CHILD"]["status"] == "done"


def test_bundle_child_whose_owned_paths_are_not_in_the_bundle_diff_is_not_done():
    model = bundle_model()
    source = FakeSource(prs={3502: merged(3502, BUNDLE_MERGE)}, diffs={BUNDLE_MERGE: ["svc/p1.py", "tests/test_p1.py"]},
                        deployed_merges=[BUNDLE_MERGE])
    assert "J-STRANGER" not in M.derive(model, source)


def test_bundle_child_with_an_owned_path_absent_from_the_merged_tree_is_not_done():
    model = bundle_model()
    source = FakeSource(prs={3502: merged(3502, BUNDLE_MERGE)}, diffs={BUNDLE_MERGE: ["svc/p1.py"]},
                        trees={BUNDLE_MERGE: ["svc/p1.py"]}, deployed_merges=[BUNDLE_MERGE])
    assert "J-CHILD" not in M.derive(model, source)


def test_bundle_child_may_own_a_file_an_earlier_merged_pr_landed():
    """Real case (J-4b-pr2817): the bundle's diff holds some owned paths; the rest were already on main."""
    model = bundle_model()
    source = FakeSource(prs={3502: merged(3502, BUNDLE_MERGE)}, diffs={BUNDLE_MERGE: ["svc/p1.py"]},
                        trees={BUNDLE_MERGE: ["svc/p1.py", "tests/test_p1.py"]}, deployed_merges=[BUNDLE_MERGE])
    assert M.derive(model, source)["J-CHILD"]["pr"] == 3502


def test_bundle_pr_named_only_by_the_squash_commit_of_the_ref():
    detector = {"type": "branch_merged", "ref": BUNDLE_MERGE}
    model = model_of(item("J-CHILD", detector, owns=["svc/p1.py"]))
    source = FakeSource(prs={3502: merged(3502, BUNDLE_MERGE)}, diffs={BUNDLE_MERGE: ["svc/p1.py"]},
                        commits={BUNDLE_MERGE: 3502}, deployed_merges=[BUNDLE_MERGE])
    assert M.derive(model, source)["J-CHILD"]["pr"] == 3502


# ---- claim 5: no named PR -> head branch, then the merged PR that carries every owned path ----------------------
def test_branch_ref_maps_to_the_merged_pr_of_that_head_branch():
    model = model_of(item("K-BR", {"type": "branch_merged", "ref": "origin/kalayantra/x"}, owns=["a.py"]))
    source = FakeSource(prs={12: merged(12, MERGE)}, heads={"kalayantra/x": [12]}, diffs={MERGE: ["a.py"]},
                        deployed_merges=[MERGE])
    assert M.derive(model, source)["K-BR"]["pr"] == 12


def test_open_item_is_not_done_from_an_old_pr_that_touched_its_owned_files():
    """B-1 (review of #3741): an OPEN repair item with no named PR and no merged branch PR must stay open, even
    when an old merged+deployed PR on main holds every file it owns (K5G1A-R1 -> #949 shape). N.8: "some PR touched
    these files" is a proxy, not the item's own merged review."""
    owns = ["services/ka_kshetra/writer.py", "services/ka_kshetra/stage5_null.py"]
    repair = item("K5G1A-R1", {"type": "branch_merged", "ref": "origin/kalayantra/k5g1a-r1"}, owns=owns)

    class OldPrOffered(FakeSource):
        def pr_carrying_paths(self, owns):      # a source that offers the old PR must not be asked, or believed
            return 949

    source = OldPrOffered(prs={949: merged(949, MERGE)}, diffs={MERGE: owns}, deployed_merges=[MERGE], heads={})
    assert M.derive(model_of(repair), source) == {}


# ---- claim 6: only code items are derived; operations and decisions keep their own closers ------------------------
@pytest.mark.parametrize("extra", [{"kind": "operation"}, {"kind": "artifact"}, {"kind": "packet"},
                                   {"kind": "code", "done_by": "decision", "decision": "D-1"},
                                   {"kind": "code", "done_by": "join", "join": True}])
def test_only_declared_code_items_are_derived(extra):
    kind = extra.pop("kind")
    model = model_of(item("K-X", {"type": "pr_merged", "pr": 10}, owns=["a.py"], kind=kind, **extra))
    source = FakeSource(prs={10: merged(10, MERGE)}, diffs={MERGE: ["a.py"]}, deployed_merges=[MERGE])
    assert M.derive(model, source) == {}


def test_code_item_with_a_file_detector_is_not_derived_from_a_pr():
    """J-1a-style items measure an activation fact in a file, which a merged PR does not establish."""
    model = model_of(item("K-ACT", {"type": "file_contains", "path": "/x", "pattern": "y"}, owns=["a.py"]))
    source = FakeSource(prs={10: merged(10, MERGE)}, diffs={MERGE: ["a.py"]}, deployed_merges=[MERGE])
    assert M.derive(model, source) == {}


def test_operation_item_with_a_derived_entry_is_still_not_done_without_its_receipt():
    """Even a stray derived proof cannot close an operation or decision item: state.py reads it only for code."""
    model = model_of(item("K-OP", {"type": "file_exists", "path": "/nope"}, kind="operation"))
    stray = {"K-OP": {"pr": 10, "evidence": "x", "detail": "x", "deploy_run_id": 1}}
    assert rows_of(model, stray)["K-OP"]["status"] != "done"


# ---- claim 7: an earlier guarded completion is durable and wins ---------------------------------------------------
def test_recorded_guarded_completion_wins_over_the_derived_proof():
    model = model_of(item("K-OWN", {"type": "pr_merged", "pr": 10}, owns=["a.py"]))
    done = {"kind": "item", "item": "K-OWN", "state": "done", "guarded": True, "evidence": "old", "ts": NOW.isoformat(),
            "completion": {"type": "code"}}
    derived = {"K-OWN": {"pr": 10, "evidence": "new", "detail": "new", "deploy_run_id": 1}}
    row = rows_of(model, derived, [done])["K-OWN"]
    assert row["status"] == "done" and row["evidence"] == "old"


def test_an_unguarded_done_claim_is_still_a_conflict_without_the_derived_proof():
    model = model_of(item("K-OWN", {"type": "pr_merged", "pr": 10}, owns=["a.py"]))
    claim = {"kind": "item", "item": "K-OWN", "state": "done", "ts": NOW.isoformat()}
    assert rows_of(model, {}, [claim])["K-OWN"]["status"] == "conflict"


# ---- claim 8: the GitHub/git source: containment is a successful workflow_run deploy of main -----------------------
class Recorder:
    def __init__(self, replies):
        self.replies, self.calls = replies, []

    def __call__(self, cmd, cwd=None, timeout=5.0, shell=False):
        self.calls.append(list(cmd))
        for prefix, reply in self.replies:
            if list(cmd[:len(prefix)]) == prefix:
                if isinstance(reply, Exception):
                    raise reply
                return reply
        return 1, "unexpected"


RUNS = json.dumps([{"databaseId": 1, "headSha": OTHER, "event": "workflow_dispatch", "createdAt": "t"},
                   {"databaseId": 2, "headSha": DEPLOYED, "event": "workflow_run", "createdAt": "t"}])


def test_source_trusts_only_workflow_run_deploys_that_contain_the_merge(monkeypatch):
    ancestry = {(MERGE, OTHER): 0, (MERGE, DEPLOYED): 0}      # both would contain it; the dispatch run is ignored
    recorder = Recorder([(["gh", "run", "list"], (0, RUNS))])
    def run(cmd, cwd=None, timeout=5.0, shell=False):
        if cmd[:3] == ["git", "merge-base", "--is-ancestor"]:
            recorder.calls.append(list(cmd))
            return ancestry.get((cmd[3], cmd[4]), 1), ""
        return recorder(cmd, cwd, timeout, shell)
    monkeypatch.setattr(D, "_run", run)
    found = M.GitHubSource("/repo").deployed(MERGE)
    assert found == {"deployed_sha": DEPLOYED, "run_id": 2, "contains_merge": True}
    assert not any(c[:5] == ["git", "merge-base", "--is-ancestor", MERGE, OTHER] for c in recorder.calls)


def test_source_reports_not_contained_when_no_successful_deploy_has_the_merge(monkeypatch):
    def run(cmd, cwd=None, timeout=5.0, shell=False):
        if cmd[:3] == ["git", "merge-base", "--is-ancestor"]:
            return 1, ""
        return 0, RUNS
    monkeypatch.setattr(D, "_run", run)
    assert M.GitHubSource("/repo").deployed(MERGE)["contains_merge"] is False


def test_source_reports_not_contained_when_the_deploy_list_cannot_be_read(monkeypatch):
    monkeypatch.setattr(D, "_run", lambda *a, **k: (1, "gh: network"))
    assert M.GitHubSource("/repo").deployed(MERGE)["contains_merge"] is False


def test_source_reads_the_squash_pr_number_from_the_commit_subject(monkeypatch):
    monkeypatch.setattr(D, "_run", lambda cmd, **k: (0, "Wave 4 P02: measuring verifier (#3502)\n"))
    assert M.GitHubSource("/repo").pr_of_commit(BUNDLE_MERGE) == 3502


# ---- claim 9: nothing blocks the tick; a failed pass never un-does a done item -------------------------------------
def test_a_failed_pass_never_flips_a_derived_item_back():
    own = item("K-OWN", {"type": "pr_merged", "pr": 10}, owns=["a.py"])
    model = model_of(own)
    good = FakeSource(prs={10: merged(10, MERGE)}, diffs={MERGE: ["a.py"]}, deployed_merges=[MERGE])
    changes = []
    code_done = M.CodeDone("/repo", source=good, on_change=lambda: changes.append(1))
    code_done.run_once(model)
    assert "K-OWN" in code_done.results() and changes == [1]
    code_done.source = FakeSource()          # GitHub unreachable: the PR can no longer be read
    code_done.run_once(model)
    assert "K-OWN" in code_done.results()


def test_one_timed_out_call_leaves_only_that_item_undecided():
    a = item("K-A", {"type": "pr_merged", "pr": 10}, owns=["a.py"])
    b = item("K-B", {"type": "pr_merged", "pr": 11}, owns=["b.py"])
    source = FakeSource(prs={11: merged(11, BUNDLE_MERGE)}, diffs={BUNDLE_MERGE: ["b.py"]}, deployed_merges=[BUNDLE_MERGE])
    def slow(number):
        if number == 10:
            raise subprocess.TimeoutExpired("gh", 5)
        return merged(11, BUNDLE_MERGE)
    source.pr = slow
    assert list(M.derive(model_of(a, b), source)) == ["K-B"]


def test_poll_returns_at_once_and_runs_the_pass_in_a_worker():
    release, started = threading.Event(), threading.Event()
    class Blocking(FakeSource):
        def pr(self, number):
            started.set()
            release.wait(5)
            return None
    code_done = M.CodeDone("/repo", source=Blocking())
    model = model_of(item("K-OWN", {"type": "pr_merged", "pr": 10}, owns=["a.py"]))
    began = time.monotonic()
    assert code_done.poll(model) is True           # returned although the worker is blocked on an external call
    assert time.monotonic() - began < 1
    assert started.wait(2) and code_done.poll(model) is False and not code_done.due()
    release.set()


def test_events_skip_items_a_guarded_done_event_already_closed():
    seen = []
    class Spy(FakeSource):
        def pr(self, number):
            seen.append(number)
    model = model_of(item("K-A", {"type": "pr_merged", "pr": 10}, owns=["a.py"]),
                     item("K-B", {"type": "pr_merged", "pr": 11}, owns=["b.py"]))
    M.derive(model, Spy(), skip={"K-A"})
    assert seen == [11]
