"""P05/P07 code merges replace full producer completion, without earning acceptance.

FU-EDGES-N01: run the committed declarations through real snapshot, detector,
step-recording and completion code. Only Git/GitHub I/O is replaced by fixtures;
no fetch, remote command or campaign ledger write occurs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "platform/scripts/governance"))
from pravaha_tracker import cli, detectors  # noqa: E402
from pravaha_tracker.completion import CompletionError, guarded_done_event  # noqa: E402
from pravaha_tracker.detectors import Config, Detectors  # noqa: E402
from pravaha_tracker.state import build_snapshot  # noqa: E402

P05 = "d9ba4934f4bfe7c159ecc42e7fcb7190f4b982c1"
CASES = [("KA-3a", "J-4b-pr2817", "p05_code_merged"),
         ("K-CERT", "J-4d-pr3145", "p07_code_merged")]


@pytest.fixture(params=CASES, ids=["P05", "P07"])
def case(request):
    return request.param


@pytest.fixture
def plan():
    return json.loads((ROOT / "00_ARCHITECTURE/control/kalayantra/plan_model.json").read_text())


def consumer(plan, case):
    return next(row for row in plan["items"] if row["id"] == case[0])


def accepted_inputs(plan, case):
    """All other items are accepted, while consumer and former producer stay open."""
    events = []
    for row in plan["items"]:
        if row["id"] in case[:2]:
            continue
        if row.get("done_by") == "decision":
            events.append(dict(kind="decision", decision=row["id"], actor="steward",
                               state="decided", outcome="approved", ts="2026-10-16T15:00:00Z"))
        else:
            events.append(dict(kind="item", item=row["id"], actor="steward", state="done",
                               guarded=True, evidence="synthetic accepted input", ts="2026-10-16T15:00:00Z"))
    return events


def complete_other_steps(plan, case, events):
    return events + [dict(kind="item", item=case[0], actor="stream-K", state="done", step=step,
                          evidence="synthetic accepted step", ts="2026-10-16T15:01:00Z")
                     for step in consumer(plan, case).get("steps", []) if step != case[2]]


def test_merge_obligation_blocks_completion_without_waiting_for_producer(plan, case):
    events = complete_other_steps(plan, case, accepted_inputs(plan, case))
    view = build_snapshot(plan, events, {}, {}, {})
    rows = {row["id"]: row for track in view["tracks"] for row in track["items"]}
    assert rows[case[1]]["status"] != "done"
    assert rows[case[0]]["deps_open_strict"] == []
    with pytest.raises(CompletionError, match="steps remain open: " + case[2]):
        guarded_done_event(plan, events, case[0], "stream-K", {"status": "done"}, {})


@pytest.fixture
def measure(plan, case, tmp_path, monkeypatch):
    """Execute real detectors, refusing every unrecognised external command."""
    det = Detectors(Config(repo=str(ROOT), home=str(tmp_path), pgenv=None))

    def observe(observation):
        def run(args, **kwargs):
            if args == ["git", "rev-parse", "--verify", "-q", P05]:
                return (1, "") if observation == "missing" else (0, P05)
            if args == ["git", "merge-base", "--is-ancestor", P05, "origin/main"]:
                return (0, "") if observation == "merged" else (1, "")
            if args == ["git", "rev-parse", P05]:
                return 0, P05
            if args == ["git", "rev-list", "--count", "origin/main.." + P05]:
                return 0, "1"
            if args == ["gh", "pr", "list", "--state", "merged", "--base", "main", "--head", P05,
                        "--limit", "5", "--json", "number,headRefOid,mergeCommit,mergedAt"]:
                return 0, "[]"
            if args == ["gh", "pr", "view", "3512", "--json", "state,mergedAt,mergeable"]:
                if observation in ("missing", "unavailable"):
                    return 1, "fixture: unavailable PR"
                state = {"merged": "MERGED", "unmerged": "OPEN", "closed": "CLOSED"}[observation]
                return 0, json.dumps(dict(state=state, mergedAt=None, mergeable="UNKNOWN"))
            raise AssertionError(f"unexpected external command: {args}")

        def fetch(remote):
            assert remote == "main"
            if observation == "unavailable":
                raise RuntimeError("fixture: main unavailable")

        monkeypatch.setattr(detectors, "_run", run)
        monkeypatch.setattr(det, "_fetch", fetch)
        spec = consumer(plan, case)["step_evidence"][case[2]]["detector"]
        return spec, det.verify(spec)

    yield observe
    det._pool.shutdown(wait=True)


@pytest.mark.parametrize("observation", ["missing", "unmerged", "unavailable", "merged"])
def test_only_a_measured_merge_records_the_required_step(plan, case, observation, measure, tmp_path, monkeypatch):
    spec, result = measure(observation)
    want = {"merged": "done", "unmerged": "running", "unavailable": "error",
            "missing": "pending" if case[0] == "KA-3a" else "error"}[observation]
    assert result.status == want
    events = tmp_path / "EVENTS.jsonl"
    evidence = tmp_path / "merge-evidence.json"
    evidence.write_text('{"fixture":"measured merge"}\n')
    monkeypatch.setattr(cli, "load_model", lambda: plan)
    monkeypatch.setattr(cli, "EVENTS", str(events))

    def verify_route(path, **kwargs):
        assert path == f"/api/verify?id={case[0]}&step={case[2]}"
        return {"item": case[0], "step": case[2], "spec": spec,
                "detector": {"status": result.status}}, "live"

    monkeypatch.setattr(cli, "get", verify_route)
    expected_exit = 0 if observation == "merged" else 2
    assert cli.main(["step", case[0], case[2], "--stream", "K", "--evidence", str(evidence)]) == expected_exit
    assert events.exists() == (expected_exit == 0)
    if expected_exit:
        return
    recorded = json.loads(events.read_text())
    assert (recorded["item"], recorded["step"]) == (case[0], case[2])
    assert recorded["evidence_sha256"] == hashlib.sha256(evidence.read_bytes()).hexdigest()
    # A successful merge step never stands in for independent typed acceptance.
    log = complete_other_steps(plan, case, accepted_inputs(plan, case)) + [recorded]
    verdict = dict(kind="verdict", actor="stream-V", item=case[0], result="ACCEPTED",
                   ts="2026-10-16T15:02:00Z")
    if case[0] == "KA-3a":
        head, merge = "a" * 40, "b" * 40
        proof = dict(type="code", reviewed_head=head,
                     pr=dict(number=9999, state="MERGED", headRefOid=head, mergeCommit={"oid": merge}))
        log.append(dict(kind="item", item=case[0], actor="stream-K", state="review",
                        detail=f"PR #9999 @ {head}", ts="2026-10-16T15:01:30Z"))
        verdicts = [dict(verdict, head=head, phase="pre_merge"),
                    dict(verdict, head=merge, phase="post_deploy")]
    else:
        proof = dict(type="artifact", artifact_digest="f" * 64)
        verdicts = [dict(verdict, artifact_digest="f" * 64, phase="artifact")]
    with pytest.raises(CompletionError, match="independent .*verdict.*missing"):
        guarded_done_event(plan, log, case[0], "stream-K", {"status": "done"}, proof)
    with pytest.raises(CompletionError, match="declared detector has not passed"):
        guarded_done_event(plan, log + verdicts, case[0], "stream-K", {"status": "pending"}, proof)
    completed = guarded_done_event(plan, log + verdicts, case[0], "stream-K", {"status": "done"}, proof)
    assert completed["guarded"] is True
    assert completed["completion"]["type"] == proof["type"]


def test_closed_p07_is_not_a_merge(plan, tmp_path, monkeypatch):
    det = Detectors(Config(repo=str(ROOT), home=str(tmp_path), pgenv=None))
    monkeypatch.setattr(detectors, "_run", lambda *a, **kw: (0, json.dumps({"state": "CLOSED"})))
    spec = consumer(plan, CASES[1])["step_evidence"][CASES[1][2]]["detector"]
    try:
        assert det.verify(spec).status == "blocked"
    finally:
        det._pool.shutdown(wait=True)
