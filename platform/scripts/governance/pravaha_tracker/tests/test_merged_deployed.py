"""SR-BOLD-07: a code item is done when its PR is merged AND contained in a successful deploy of main.

The PR's merged review is the acceptance — no per-item verdict event, no post-deploy verdict. Operation items still
close from executor receipts and decisions from the ledger. Oracle for every claim: the owner ruling SR-BOLD-07
(DECISIONS_SURROGATE.jsonl; ruling 5 of 2026-10-19: ANY successful deploy.yml run of main whose sha contains the merge
commit counts, whatever triggered it, provided a dispatch run's "Require earned deployment outcome" job passed and a
deploy job succeeded - .github/workflows/deploy.yml deployment-outcome), plan v3.0 §C (deployment containment,
cli.observe_containment) and A7 D-46 (done with open gates = implemented, with
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


@pytest.fixture(autouse=True)
def _isolated_pravaha_home(tmp_path, monkeypatch):
    """A GitHubSource built without an explicit proof path must never read or write the live proof cache."""
    monkeypatch.setenv("PRAVAHA_HOME", str(tmp_path / "pravaha-home"))


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


# ---- claim 8: the GitHub/git source: containment is a successful deploy of main (any trigger) ----------------------
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


def _jobs(**results):
    """`gh run view --json jobs` for deploy.yml: the outcome gate and the four deploy jobs, by conclusion."""
    names = {"outcome": M.OUTCOME_JOB, "web": "Build & Deploy Web", "sidecar": "Build & Deploy Sidecar",
             "mcp": "Build & Deploy MCP", "pipeline": "Build & Deploy Pipeline Job Image"}
    return json.dumps({"jobs": [{"name": names[k], "conclusion": v} for k, v in results.items()]})


EARNED = _jobs(outcome="success", web="success", sidecar="success", mcp="success", pipeline="success")
MIGRATE_ONLY = _jobs(outcome="success", web="skipped", sidecar="skipped", mcp="skipped", pipeline="skipped")


def _source(monkeypatch, runs, views, contains=(DEPLOYED,)):
    """GitHubSource over canned `gh run list` / `gh run view` answers; `contains` = the shas that contain MERGE."""
    def run(cmd, cwd=None, timeout=5.0, shell=False):
        if cmd[:3] == ["gh", "run", "list"]:
            return 0, runs
        if cmd[:3] == ["gh", "run", "view"]:
            return views.get(cmd[3], (1, "gh: not found"))
        if cmd[:3] == ["git", "merge-base", "--is-ancestor"]:
            return (0 if cmd[3] == MERGE and cmd[4] in contains else 1), ""
        return 1, "unexpected"
    monkeypatch.setattr(D, "_run", run)
    return M.GitHubSource("/repo")


def _dispatch(run_id=1, sha=DEPLOYED):
    return json.dumps([{"databaseId": run_id, "headSha": sha, "event": "workflow_dispatch", "createdAt": "t"}])


def test_source_counts_a_workflow_run_deploy_that_contains_the_merge(monkeypatch):
    found = _source(monkeypatch, RUNS, {}).deployed(MERGE)      # the dispatch run 1 holds no merge, run 2 does
    assert found == {"deployed_sha": DEPLOYED, "run_id": 2, "contains_merge": True}


def test_source_counts_a_successful_dispatch_deploy_that_contains_the_merge(monkeypatch):
    """BOLD-07: the protected-window run (workflow_dispatch, success, web/MCP/sidecar/pipeline deployed) counts."""
    found = _source(monkeypatch, _dispatch(39237537349), {"39237537349": (0, EARNED)}).deployed(MERGE)
    assert found == {"deployed_sha": DEPLOYED, "run_id": 39237537349, "contains_merge": True}


def test_source_does_not_count_a_dispatch_run_that_only_migrated_and_skipped_every_deploy(monkeypatch):
    """The gate passes with nothing deployed ('no-deployable-change'); GitHub calls the run green: not a deploy."""
    source = _source(monkeypatch, _dispatch(5), {"5": (0, MIGRATE_ONLY)})
    assert source.deployed(MERGE)["contains_merge"] is False


def test_source_does_not_count_a_dispatch_run_whose_outcome_gate_did_not_pass(monkeypatch):
    gate_red = _jobs(outcome="failure", web="success", sidecar="skipped", mcp="skipped", pipeline="skipped")
    assert _source(monkeypatch, _dispatch(5), {"5": (0, gate_red)}).deployed(MERGE)["contains_merge"] is False
    gate_missing = _jobs(web="success")
    assert _source(monkeypatch, _dispatch(5), {"5": (0, gate_missing)}).deployed(MERGE)["contains_merge"] is False


def test_source_does_not_count_a_dispatch_run_whose_jobs_cannot_be_read(monkeypatch):
    assert _source(monkeypatch, _dispatch(5), {}).deployed(MERGE)["contains_merge"] is False
    assert _source(monkeypatch, _dispatch(5), {"5": (0, "not json")}).deployed(MERGE)["contains_merge"] is False


def test_source_does_not_count_a_dispatch_deploy_whose_sha_lacks_the_merge(monkeypatch):
    source = _source(monkeypatch, _dispatch(5, OTHER), {"5": (0, EARNED)}, contains=())
    assert source.deployed(MERGE)["contains_merge"] is False


def test_source_asks_for_successful_runs_only_so_a_failed_run_never_counts(monkeypatch):
    seen = []
    def run(cmd, cwd=None, timeout=5.0, shell=False):
        seen.append(list(cmd))
        return (0, "[]") if cmd[:3] == ["gh", "run", "list"] else (1, "")
    monkeypatch.setattr(D, "_run", run)
    M.GitHubSource("/repo").deployed(MERGE)
    listing = next(c for c in seen if c[:3] == ["gh", "run", "list"])
    assert listing[listing.index("--status") + 1] == "success"


def test_a_failed_dispatch_run_that_slips_into_the_list_does_not_count(monkeypatch):
    """Defence in depth: the list is filtered by `--status success`, but a run with a red gate still never counts."""
    red = _jobs(outcome="failure", web="failure", sidecar="skipped", mcp="skipped", pipeline="skipped")
    assert _source(monkeypatch, _dispatch(9), {"9": (0, red)}).deployed(MERGE)["contains_merge"] is False


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


# ---- claim 10: the CLI's and the D-46 sweep's copies of the rule agree with the source's -----------------------------
def _fake_subprocess(monkeypatch, listing, views, contains):
    from pravaha_tracker import cli
    def run(cmd, cwd=None, capture_output=True, text=True, timeout=0, check=False):
        out, rc = "", 0
        if cmd[:3] == ["gh", "run", "list"]:
            out = listing
        elif cmd[:3] == ["gh", "run", "view"]:
            rc, out = views.get(cmd[3], (1, ""))
        elif cmd[:3] == ["git", "merge-base", "--is-ancestor"]:
            rc = 0 if cmd[4] in contains else 1
        return subprocess.CompletedProcess(cmd, rc, out, "")
    monkeypatch.setattr(cli.subprocess, "run", run)
    return cli


def test_cli_observe_containment_counts_an_earned_dispatch_deploy_and_not_a_migrate_only_one(monkeypatch):
    cli = _fake_subprocess(monkeypatch, _dispatch(7), {"7": (0, EARNED)}, (DEPLOYED,))
    assert cli.observe_containment("/repo", MERGE)["run_id"] == 7
    cli = _fake_subprocess(monkeypatch, _dispatch(7), {"7": (0, MIGRATE_ONLY)}, (DEPLOYED,))
    assert cli.observe_containment("/repo", MERGE)["contains_merge"] is False


def test_d46_sweep_takes_a_dispatch_deploy_only_when_the_evidence_says_it_earned_the_deploy(monkeypatch):
    from pravaha_tracker import d46_sweep
    monkeypatch.setattr(d46_sweep, "is_ancestor", lambda repo, a, b: True)
    run = {"run_id": 3, "head_sha": DEPLOYED, "conclusion": "success", "event": "workflow_dispatch", "branch": "main"}
    assert d46_sweep._first_deploy("/repo", {"deploys": [run]}, MERGE) is None
    assert d46_sweep._first_deploy("/repo", {"deploys": [{**run, "earned_deploy": True}]}, MERGE)["run_id"] == 3
    assert d46_sweep._first_deploy("/repo", {"deploys": [{**run, "earned_deploy": True, "conclusion": "failure"}]},
                                   MERGE) is None


# ---- SR-TRACKER-DONE-NEVER-EXPIRES: a merged+deployed proof never expires -----------------------------------------
# Oracle: owner ruling madhav-44 (a: per-branch lookup beyond the MERGED_LIST_LIMIT window + a persistent proof cache
# keyed (PR number, merge sha), voided only when the merge commit leaves origin/main; b: a skip / not_applicable pass
# never overrides a proven done), on SR-BOLD-07 (merged PR contained in a successful main deploy is done; a merge
# cannot un-happen) and the measured defect of 2026-10-23 (#3555 / #3554 fell out of the newest-300 window).
def _sha_of(number):
    return format(number, "040x")


def _pr(number, branch):
    return {"number": number, "state": "MERGED", "headRefName": branch, "headRefOid": "f" * 40,
            "mergeCommit": {"oid": _sha_of(number)}}


class World:
    """gh and git as one fake: `merged` is the newest-first list of merged PRs on main; `in_main` the merge shas that
    origin/main contains; `gh` is "up", "down" (every gh call fails) or "empty" (gh answers, with nothing)."""

    def __init__(self, merged, gh="up"):
        self.merged, self.gh, self.git_rc = list(merged), gh, None
        self.in_main = {pr["mergeCommit"]["oid"] for pr in merged}
        self.calls = []

    def __call__(self, cmd, cwd=None, timeout=5.0, shell=False, **kw):
        cmd = list(cmd)
        self.calls.append(cmd)
        if cmd[0] == "gh":
            return self._gh(cmd)
        if cmd[:3] == ["git", "merge-base", "--is-ancestor"]:
            if self.git_rc is not None:
                return self.git_rc, ""
            return (0 if cmd[3] in self.in_main else 1), ""
        if cmd[:2] == ["git", "diff-tree"]:
            return 0, "a.py\n"
        if cmd[:2] == ["git", "cat-file"]:
            return 0, ""
        return 0, _sha_of(1) + "\n"                   # git fetch / rev-parse origin/main

    def _gh(self, cmd):
        if self.gh == "down":
            return 1, "gh: network"
        if self.gh == "empty":
            return 0, "" if cmd[:3] == ["gh", "pr", "view"] else "[]"
        if cmd[:3] == ["gh", "pr", "list"]:
            rows = self.merged
            if "--head" in cmd:
                rows = [pr for pr in rows if pr["headRefName"] == cmd[cmd.index("--head") + 1]]
            return 0, json.dumps(rows[:int(cmd[cmd.index("--limit") + 1])])
        if cmd[:3] == ["gh", "pr", "view"]:
            hit = [pr for pr in self.merged if str(pr["number"]) == cmd[3]]
            return (0, json.dumps(hit[0])) if hit else (1, "not found")
        if cmd[:3] == ["gh", "run", "list"]:
            return 0, json.dumps([{"databaseId": 9, "headSha": DEPLOYED, "event": "workflow_run", "createdAt": "t"}])
        return 1, "unexpected"

    def head_lookups(self):
        return [c for c in self.calls if c[:3] == ["gh", "pr", "list"] and "--head" in c]


def _branch_item(iid, branch):
    return item(iid, {"type": "branch_merged", "ref": f"origin/{branch}"}, owns=["a.py"])


def _window_of(target_numbers, filler=300):
    """The newest-first merged list: `filler` unrelated PRs, then the targets (so the first target is #filler+1)."""
    rows = [_pr(5000 - i, f"filler-{i}") for i in range(filler)]
    return rows + [_pr(n, f"kalayantra/k{n}") for n in target_numbers]


def _src(monkeypatch, world, path):
    monkeypatch.setattr(D, "_run", world)
    return M.GitHubSource("/repo", proof_path=str(path))


def test_t1_a_branch_whose_pr_is_beyond_the_window_still_derives_done(monkeypatch, tmp_path):
    world = World(_window_of([3555]))
    src = _src(monkeypatch, world, tmp_path / "p.json")
    src.refresh()
    assert 3555 not in {n for ns in src._heads.values() for n in ns}      # the windowed list really does not hold it
    derived = M.derive(model_of(_branch_item("K5-2", "kalayantra/k3555")), src)
    assert derived["K5-2"]["pr"] == 3555 and derived["K5-2"]["merge_commit"] == _sha_of(3555)


def test_t2_the_proof_survives_a_restart_and_a_refresh_where_gh_returns_nothing(monkeypatch, tmp_path):
    path = tmp_path / "p.json"
    model = model_of(_branch_item("K5-2", "kalayantra/k3555"), item("K-NAMED", {"type": "pr_merged", "pr": 3554}, owns=["a.py"]))
    live = World(_window_of([3555, 3554]))
    first = _src(monkeypatch, live, path)
    first.refresh()
    proofs = M.derive(model, first)
    assert set(proofs) == {"K5-2", "K-NAMED"} and path.exists()
    for mode in ("down", "empty"):
        restarted = _src(monkeypatch, World(_window_of([3555, 3554]), gh=mode), path)       # a new process
        restarted.refresh()                                                                  # gh gives nothing
        again = M.derive(model, restarted)
        assert set(again) == {"K5-2", "K-NAMED"}, mode
        assert again["K5-2"]["deploy_run_id"] == proofs["K5-2"]["deploy_run_id"]
        assert len(restarted.proofs.entries()) == 2, mode                                    # a gh failure clears nothing


def test_t3_the_cache_entry_is_dropped_when_the_merge_sha_leaves_main(monkeypatch, tmp_path):
    monkeypatch.setattr(M, "REVALIDATE_S", 0.0)
    path = tmp_path / "p.json"
    world = World(_window_of([3555]))
    src = _src(monkeypatch, world, path)
    model = model_of(_branch_item("K5-2", "kalayantra/k3555"))
    src.refresh()
    assert "K5-2" in M.derive(model, src)
    world.git_rc = 128                  # git itself failing is not evidence: the proof stays
    src.refresh()
    assert len(src.proofs.entries()) == 1
    world.git_rc = None
    world.in_main.discard(_sha_of(3555))      # the merge commit is no longer contained in origin/main
    src.refresh()
    assert src.proofs.entries() == {} and json.loads(path.read_text())["proofs"] == {}
    gone = _src(monkeypatch, World(_window_of([3555]), gh="down"), path)
    assert M.derive(model, gone) == {}


@pytest.mark.parametrize("position", [300, 301])
def test_t5_the_window_boundary_pr_300_is_in_the_list_pr_301_is_found_on_its_own(monkeypatch, tmp_path, position):
    rows = _window_of([], filler=position - 1) + [_pr(3555, "kalayantra/k3555")]
    world = World(rows + [_pr(4000 + i, f"after-{i}") for i in range(301 - position)])
    assert world.merged.index(next(r for r in rows if r["number"] == 3555)) + 1 == position
    src = _src(monkeypatch, world, tmp_path / "p.json")
    src.refresh()
    window = next(c for c in world.calls if c[:3] == ["gh", "pr", "list"] and "--head" not in c)
    assert window[window.index("--limit") + 1] == str(M.MERGED_LIST_LIMIT) == "300"
    assert "K5-2" in M.derive(model_of(_branch_item("K5-2", "kalayantra/k3555")), src)
    assert bool(world.head_lookups()) is (position > M.MERGED_LIST_LIMIT)      # only the 301st needs its own lookup


def test_a_failed_per_branch_lookup_is_not_remembered_as_no_pr(monkeypatch, tmp_path):
    world = World(_window_of([3555]), gh="down")
    src = _src(monkeypatch, world, tmp_path / "p.json")
    assert src.merged_prs_for_branch("kalayantra/k3555") == []
    world.gh = "up"
    assert src.merged_prs_for_branch("kalayantra/k3555") == [3555]       # gh recovered: asked again at once


def test_the_proof_file_is_written_atomically_and_an_unreadable_one_is_ignored(monkeypatch, tmp_path):
    path = tmp_path / "run" / "p.json"
    src = _src(monkeypatch, World(_window_of([3555])), path)
    src.refresh()
    M.derive(model_of(_branch_item("K5-2", "kalayantra/k3555")), src)
    assert [p.name for p in path.parent.iterdir()] == ["p.json"]          # no temp file left behind
    path.write_text("{not json")
    assert M.ProofStore(str(path)).entries() == {}


# ---- ruling (b): a skip / not_applicable pass never overrides a proven done ---------------------------------------
def test_t4_a_proven_done_is_never_overridden_by_a_skip_or_not_applicable_propagation():
    def with_outcomes(*items):
        model = model_of(*items)
        model["control_plane"]["decision_outcomes"] = {"final": ["approved", "refused"], "open": ["deferred"]}
        return model

    refused = {"kind": "decision", "decision": "D-VC", "state": "decided", "outcome": "refused", "ts": NOW.isoformat()}
    skipped = item("K-SKIPPED", {"type": "pr_merged", "pr": 11}, owns=["b.py"], requires_outcome={"D-VC": "approved"})
    proven = item("K-PROVEN", {"type": "pr_merged", "pr": 10}, owns=["a.py"], requires_outcome={"D-VC": "approved"})
    downstream = item("K-DOWN", {"type": "pr_merged", "pr": 12}, owns=["c.py"], depends_on=["K-SKIPPED"])
    model = with_outcomes(skipped, proven, downstream)
    source = FakeSource(prs={10: merged(10, MERGE), 12: merged(12, BUNDLE_MERGE)},
                        diffs={MERGE: ["a.py"], BUNDLE_MERGE: ["c.py"]}, deployed_merges=[MERGE, BUNDLE_MERGE])
    derived = M.derive(model, source)
    assert set(derived) == {"K-PROVEN", "K-DOWN"}
    rows = rows_of(model, derived, [refused])
    assert rows["K-SKIPPED"]["status"] == "not_applicable"            # the skip pass is live: it does skip an unproven item
    assert rows["K-PROVEN"]["status"] == "done" and rows["K-PROVEN"]["source"] == M.SOURCE
    assert rows["K-DOWN"]["status"] == "done"                         # nor does a skipped dependency reach a proven done
    assert rows["K-DOWN"].get("skip_origin") is None
