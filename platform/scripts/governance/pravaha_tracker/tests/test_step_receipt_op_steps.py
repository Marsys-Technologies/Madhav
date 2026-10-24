"""SR-OP-STEPS / SR-OP-STEPS-2: mechanical evidence for operation-item steps.

(a) a lease_held step is evidenced by the lease row on origin/campaign-coordination at a cited commit;
(b) a plan-declared not-applicable step is satisfied only by a recorded decision, and shows as N/A;
(c) the executor's own recorded acceptance is the accepted verdict at the receipt's digest.

Each claim has one detector in production code; each test below fails when that detector is reverted.
"""
import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from pravaha_tracker import cli, server
from pravaha_tracker.completion import CompletionError, guarded_done_event
from pravaha_tracker.detectors import Config, Detectors
from pravaha_tracker.op_steps import COORDINATION_FILE
from pravaha_tracker.state import build_snapshot
from pravaha_tracker.tests.test_kalayantra_control_plane import declared_model
from pravaha_tracker.tests.test_step_receipt_binding import canonical, operation_step  # noqa: F401  (fixture)

PLAN = Path(cli.REPO_ROOT) / "00_ARCHITECTURE/control/kalayantra/plan_model.json"
LEASE_ID = "L-KY-TEST-20261019"
HEADER = "| # | campaign | purpose | started (IST) | expiry (IST) | status |\n|---|---|---|---|---|---|\n"
ROW = f"| {LEASE_ID} | KĀLA-YANTRA v3 / Claude Code cockpit | J-3c window | 2026-10-18 18:25 | 2026-10-19 10:55 | ACTIVE |"
RELEASED_ROW = ROW.replace("| ACTIVE |", "| RELEASED 2026-10-19 06:14 IST — window complete |")


def git(repo, *args):
    out = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                          "-c", "commit.gpgsign=false", *args], check=True, capture_output=True, text=True)
    return out.stdout.strip()


# ------------------------------------------------------------------------------------------ (a) lease row

@pytest.fixture
def lease_step(tmp_path, monkeypatch):
    repo = tmp_path / "coordination"
    ledger = repo / COORDINATION_FILE
    ledger.parent.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    ledger.write_text(HEADER + ROW + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "take")
    taken = git(repo, "rev-parse", "HEAD")
    ledger.write_text(HEADER + RELEASED_ROW + "\n")
    git(repo, "commit", "-q", "-am", "release")
    released = git(repo, "rev-parse", "HEAD")
    git(repo, "update-ref", "refs/remotes/origin/campaign-coordination", released)
    git(repo, "checkout", "-q", "-b", "elsewhere", taken)
    ledger.write_text(HEADER + ROW + "\n| other | other | other | 1 | 2 | ACTIVE |\n")
    git(repo, "commit", "-q", "-am", "never reaches the coordination branch")
    stray = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-q", "main")

    item = copy.deepcopy(next(row for row in json.loads(PLAN.read_text())["items"] if row["id"] == "J-3c"))
    model = declared_model()
    model["items"] = [item]
    spec = item["step_evidence"]["lease_held"]["detector"]
    path = tmp_path / "J-3c.lease_held.json"
    spec["path"] = str(path)
    events = tmp_path / "EVENTS.jsonl"
    events.write_text("")
    monkeypatch.setattr(cli, "load_model", lambda: model)
    monkeypatch.setattr(cli, "EVENTS", str(events))
    monkeypatch.setenv("PRAVAHA_REPO", str(repo))
    detector = Detectors(Config(repo=str(tmp_path), home=str(tmp_path), pgenv=None))
    monkeypatch.setattr(cli, "get", lambda *a, **k: ({"item": "J-3c", "step": "lease_held", "spec": spec,
                                                      "detector": {"status": detector.verify(spec).status}}, "live"))

    def write(**over):
        record = {"coordination_commit": taken, "expires": "2026-10-19 10:55", "item": "J-3c",
                  "lease_id": LEASE_ID, "row": ROW, "schema": "ky.lease_row_evidence/1", "step": "lease_held",
                  "taken": "2026-10-18 18:25", **over}
        path.write_text(canonical(record))

    def run(expected):
        code = cli.main(["step", "J-3c", "lease_held", "--stream", "N", "--evidence", str(path)])
        assert code == expected
        lines = events.read_text().splitlines()
        if expected:
            assert not lines, "refusal must append no event"
        else:
            assert [json.loads(line)["kind"] for line in lines] == ["item"], "no verdict event is synthesised"
            assert json.loads(lines[0])["step"] == "lease_held"

    write()
    yield type("W", (), dict(write=staticmethod(write), run=staticmethod(run), taken=taken, released=released,
                             stray=stray, path=path))
    detector._pool.shutdown(wait=True)


def test_lease_row_step_accepts_the_row_active_at_the_cited_commit(lease_step):
    # the row is RELEASED at the branch tip: ACTIVE is read at the cited "take" commit, not at the tip
    lease_step.run(expected=0)


def test_lease_row_step_refuses_a_commit_that_is_not_on_the_coordination_branch(lease_step):
    lease_step.write(coordination_commit=lease_step.stray)
    lease_step.run(expected=2)


def test_lease_row_step_refuses_a_row_that_is_not_active_at_the_cited_commit(lease_step):
    lease_step.write(coordination_commit=lease_step.released, row=RELEASED_ROW)
    lease_step.run(expected=2)


@pytest.mark.parametrize("change", [
    {"lease_id": "L-KY-NO-SUCH-LEASE"}, {"row": ROW.replace("J-3c window", "another purpose")},
    {"taken": "2026-10-18 18:26"}, {"expires": "2026-10-20 10:55"},
])
def test_lease_row_step_refuses_evidence_that_differs_from_the_ledger_row(lease_step, change):
    lease_step.write(**change)
    lease_step.run(expected=2)


def test_lease_row_step_refuses_a_commit_the_repository_does_not_have(lease_step):
    lease_step.write(coordination_commit="0" * 40)
    lease_step.run(expected=2)


# ------------------------------------------------------------------- (c) the executor's own acceptance

def _opid(w):
    return w.executor["operation_id"]


def _no_verdict(w):
    """The V-stream holds no verdict for this operation: only the executor's recorded acceptance can bind."""
    w.sync()
    w.events.write_text("")


def _accept(w, name_suffix=".post.json", **over):
    record = {"schema": "ky.mechanical_acceptance/1", "phase": "post", "by": "executor-mechanical",
              "result": "ACCEPTED", "operation_id": _opid(w), "request_sha256": w.executor["request_sha256"],
              "receipt_sha256": hashlib.sha256(w.executor_path.read_bytes()).hexdigest(),
              "output_sha256": w.executor["output_sha256"], "reviewed_commit": w.executor["reviewed_commit"],
              "checks": {"receipt_completed_exit_zero": True, "output_sha_equals_receipt": True}}
    record.update(over)
    for key in [key for key, value in record.items() if value is None]:
        del record[key]
    directory = w.ops / "acceptance"
    directory.mkdir(exist_ok=True)
    (directory / (_opid(w) + name_suffix)).write_text(json.dumps(record))


def test_step_binds_to_the_executor_mechanical_acceptance_without_a_verdict_event(operation_step):
    w = operation_step
    _no_verdict(w)
    _accept(w)
    w.run(expected=0)
    assert {json.loads(line)["kind"] for line in w.events.read_text().splitlines()} == {"item"}


def test_step_binds_to_a_single_verifier_lane_acceptance_of_the_request(operation_step):
    w = operation_step
    _no_verdict(w)
    _accept(w, ".json", by="v2", schema=None, phase=None, checks=None, receipt_sha256=None, output_sha256=None)
    w.run(expected=0)


def test_step_without_an_acceptance_file_still_refuses(operation_step):
    w = operation_step
    _no_verdict(w)
    w.run(expected=2)


@pytest.mark.parametrize("change", [
    {"operation_id": "J-2x.some-other-operation"}, {"request_sha256": "1" * 64}, {"receipt_sha256": "2" * 64},
])
def test_step_refuses_an_acceptance_for_a_different_operation_or_digest(operation_step, change):
    w = operation_step
    _no_verdict(w)
    _accept(w, **change)
    w.run(expected=2)


@pytest.mark.parametrize("requester", ["v2", "stream-V:v2", "executor-mechanical"])
def test_step_refuses_an_acceptance_signed_by_the_requester(operation_step, requester):
    w = operation_step
    w.req["requested_by"] = w.executor["requested_by"] = requester
    w.request_path.write_text(json.dumps(w.req))
    w.executor["request_sha256"] = hashlib.sha256(canonical(w.req).rstrip("\n").encode()).hexdigest()
    _no_verdict(w)
    _accept(w, **({"by": "v2"} if requester != "executor-mechanical" else {}))
    w.run(expected=2)
    _accept(w, by="v3")    # the same request, accepted by a lane that is not the requester
    w.run(expected=0)


@pytest.mark.parametrize("change", [
    {"checks": {"receipt_completed_exit_zero": True, "output_sha_equals_receipt": False}}, {"checks": {}},
    {"by": "codex"}, {"result": "REJECTED"},
])
def test_step_refuses_an_acceptance_that_is_not_mechanical_or_lane_signed(operation_step, change):
    w = operation_step
    _no_verdict(w)
    _accept(w, **change)
    w.run(expected=2)


def test_a_recorded_rejection_at_the_digest_is_not_overridden_by_the_executor_acceptance(operation_step):
    w = operation_step
    w.verdict["result"] = "REJECTED"
    w.sync()
    _accept(w)
    w.run(expected=2)


# --------------------------------------------------------------------- (b) not-applicable steps by decision

NA_REASON = ("not applicable: restore proof dropped by OWNER-MINIMAL-PROTECTION-NOW-20261018; "
             "backup taken per receipt J-3c.backup (label j3c_20261018t130045z)")


def _decision(state="delegated", **extra):
    return {"kind": "decision", "actor": "steward", "decision": "SR-OP-STEPS", "state": state,
            "detail": "ruling", "ts": "2026-10-19T03:20:12+00:00", **extra}


def _na_model():
    model = declared_model()
    item = next(row for row in model["items"] if row["id"] == "N-OP")
    item.update(steps=["lease_held", "backup_restore_verified"],
                not_applicable_steps={"backup_restore_verified": {"decision": "SR-OP-STEPS", "reason": NA_REASON}})
    model["decisions"] = [{"id": "SR-OP-STEPS", "title": "t", "owner": "o", "default": "d"}]
    return model, item


def _steps(model, events):
    snapshot = build_snapshot(model, events, {}, {}, {})
    row = next(it for track in snapshot["tracks"] for it in track["items"] if it["id"] == "N-OP")
    return {step["name"]: step for step in row["steps"]}, row


def test_a_not_applicable_step_with_a_recorded_decision_is_satisfied_and_cited():
    model, _ = _na_model()
    steps, row = _steps(model, [_decision()])
    assert steps["backup_restore_verified"] == {"name": "backup_restore_verified", "done": True,
                                                "not_applicable": True, "decision": "SR-OP-STEPS", "reason": NA_REASON}
    assert steps["lease_held"]["done"] is False and "not_applicable" not in steps["lease_held"]
    assert row["progress"] == 0.5


@pytest.mark.parametrize("events", [
    [], [_decision("requested")], [_decision(outcome="deferred")],
    [{**_decision(), "decision": "SR-ANOTHER"}],
])
def test_a_not_applicable_step_without_its_recorded_decision_stays_open(events):
    model, _ = _na_model()
    steps, row = _steps(model, events)
    assert steps["backup_restore_verified"]["done"] is False
    assert "not_applicable" not in steps["backup_restore_verified"] and row["progress"] == 0


def test_a_not_applicable_step_needs_a_reason():
    model, item = _na_model()
    item["not_applicable_steps"]["backup_restore_verified"]["reason"] = "  "
    assert _steps(model, [_decision()])[0]["backup_restore_verified"]["done"] is False


def _complete(model, events):
    digest = "a" * 64
    receipt = {"operation_id": "op-1", "item_id": "N-OP", "status": "COMPLETED"}
    verdict = {"kind": "verdict", "actor": "stream-V:v1", "item": "N-OP", "phase": "artifact", "head": None,
               "artifact_digest": digest, "result": "ACCEPTED", "detail": "measured", "ts": "2026-10-19T03:00:00+00:00"}
    step = {"kind": "item", "actor": "stream-N:n1", "item": "N-OP", "state": "done", "step": "lease_held",
            "ts": "2026-10-19T03:00:00+00:00"}
    return guarded_done_event(model, [step, verdict, *events], "N-OP", "stream-S:sutradhara", {"status": "done"},
                              {"type": "operation", "operation_id": "op-1", "receipt": receipt,
                               "artifact_digest": digest})


def test_completion_counts_a_recorded_not_applicable_step_as_satisfied():
    model, _ = _na_model()
    assert _complete(model, [_decision()])["item"] == "N-OP"


def test_completion_refuses_while_the_not_applicable_step_has_no_recorded_decision():
    model, _ = _na_model()
    with pytest.raises(CompletionError, match="steps remain open: backup_restore_verified"):
        _complete(model, [])


def test_the_plan_marks_j3c_restore_proof_not_applicable_by_the_surrogate_ruling():
    plan = json.loads(PLAN.read_text())
    item = next(row for row in plan["items"] if row["id"] == "J-3c")
    assert item["not_applicable_steps"] == {"backup_restore_verified": {"decision": "SR-OP-STEPS", "reason": NA_REASON}}
    assert "SR-OP-STEPS" in {decision["id"] for decision in plan["decisions"]}
    assert item["step_evidence"]["lease_held"]["evidence"] == "lease_row"
    assert server._check_declarations(plan) == []


def test_the_plan_refuses_a_not_applicable_step_citing_an_undeclared_decision():
    plan = json.loads(PLAN.read_text())
    item = next(row for row in plan["items"] if row["id"] == "J-3c")
    item["not_applicable_steps"]["backup_restore_verified"]["decision"] = "SR-NOT-IN-THE-PLAN"
    assert any("SR-NOT-IN-THE-PLAN" in problem for problem in server._check_declarations(plan))


# ------------------------------------------------------------------------ (d) SR-A12-BACKUP-REMOVAL: the restore-proof step is waived by the plan's own mechanism

A12_ITEMS = ("J-2a", "J-4e", "J-6", "K9-4a")      # J-3c keeps its earlier SR-OP-STEPS waiver (a backup really was taken there)


def _a12_decision(state="delegated", **extra):
    return {**_decision(state, **extra), "decision": "SR-A12-BACKUP-REMOVAL"}


def _a12_step(item_id, events):
    snapshot = build_snapshot(json.loads(PLAN.read_text()), events, {}, {}, {})
    row = next(it for track in snapshot["tracks"] for it in track["items"] if it["id"] == item_id)
    return next(step for step in row["steps"] if step["name"] == "backup_restore_verified")


@pytest.mark.parametrize("item_id", A12_ITEMS)
def test_the_plan_waives_the_restore_proof_step_citing_sr_a12_backup_removal_and_never_deletes_it(item_id):
    plan = json.loads(PLAN.read_text())
    item = next(row for row in plan["items"] if row["id"] == item_id)
    assert "backup_restore_verified" in item["steps"] and "backup_restore_verified" in item["step_evidence"]      # waived, not removed
    waived = item["not_applicable_steps"]["backup_restore_verified"]
    assert waived["decision"] == "SR-A12-BACKUP-REMOVAL" and "SR-A12-BACKUP-REMOVAL" in waived["reason"]
    assert "SR-A12-BACKUP-REMOVAL" in {decision["id"] for decision in plan["decisions"]}
    assert server._check_declarations(plan) == []


@pytest.mark.parametrize("item_id", A12_ITEMS)
def test_the_detector_reads_the_waived_step_as_waived_with_its_citation_not_as_evidence_of_a_backup(item_id):
    step = _a12_step(item_id, [_a12_decision()])
    assert step["not_applicable"] is True and step["decision"] == "SR-A12-BACKUP-REMOVAL" and step["done"] is True   # satisfied by the ruling alone: no step event exists
    assert "SR-A12-BACKUP-REMOVAL" in step["reason"]


@pytest.mark.parametrize("item_id", A12_ITEMS)
def test_the_waived_step_is_an_open_gap_until_the_ruling_is_recorded(item_id):
    for events in ([], [_a12_decision("requested")], [_a12_decision(outcome="deferred")]):
        step = _a12_step(item_id, events)
        assert step["done"] is False and "not_applicable" not in step, events
