"""SR-OP-STEPS-2 / SR-TEARDOWN-COMPLETION: pre_acceptance and teardown steps bound to the executor's own records.

Claims (one detector each in op_steps.py; every test below fails when its detector is reverted):
 P1 a J-3c pre_acceptance step is evidenced by run/ops/acceptance/<dispatch op>.post.json, with no verdict event;
 P2 that record must accept the digest of the archived request; P3 must not be signed by the requester;
 P4 must be signed by a verifier lane or executor-mechanical with every check true; P5 must be the declared
 <operation_id>.post.json under run/ops/acceptance; P6 must belong to this item's operation.
 T1 a COMMITTED teardown receipt (AWAITING_ABSENCE, proof COMMITTED_AWAITING_ABSENCE, exit 0) plus an ACCEPTED
 absence receipt bound to its evidence_digest completes the teardown (executor.fence_quiescent ->
 v5_small_test_shared.absence_evidence); T2 an absence bound to another digest is refused; T3 an absence that is
 not independently accepted is refused; T4 a teardown that is not committed is refused; T5 a later staged launch
 is refused; T6 the tracker's census equals the reviewed policy's.
"""
import copy
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path

import pytest

from pravaha_tracker import cli, server
from pravaha_tracker.detectors import Config, Detectors
from pravaha_tracker.completion import CompletionError
from pravaha_tracker.op_steps import (ABSENCE_CENSUS, check_acceptance_file_evidence, committed_teardown_absence_accepted,
                                      evidence_digest)
from pravaha_tracker.tests.test_kalayantra_control_plane import declared_model
from pravaha_tracker.tests.test_step_receipt_binding import canonical, operation_step  # noqa: F401  (fixture)
from pravaha_tracker.tests.test_step_receipt_op_steps import _accept, _no_verdict

PLAN = Path(cli.REPO_ROOT) / "00_ARCHITECTURE/control/kalayantra/plan_model.json"
POLICY = Path(cli.REPO_ROOT) / "platform/scripts/v5_small_test_shared.py"
OPID = "J-3c.dispatch"


# ------------------------------------------------------------------------------ pre_acceptance

@pytest.fixture
def pre_step(tmp_path, monkeypatch):
    home = tmp_path / "home"
    ops = home / "run/ops"
    for name in ("done", "receipts", "acceptance"):
        (ops / name).mkdir(parents=True)
    request = {"operation_id": OPID, "kind": "measuring_dispatch", "item_id": "J-3c", "requested_by": "adhikarin",
               "kyd": "fixture", "reviewed_commit": "a" * 40, "acceptance_receipt": "/somewhere/else.json"}
    (ops / "done" / (OPID + ".json")).write_text(json.dumps(request))
    digest = cli._request_digest(request)
    receipt = {"operation_id": OPID, "item_id": "J-3c", "kind": "measuring_dispatch", "status": "COMPLETED",
               "exit_code": 0, "request_sha256": digest, "reviewed_commit": "a" * 40}
    (ops / "receipts" / (OPID + ".json")).write_text(json.dumps(receipt))
    item = copy.deepcopy(next(row for row in json.loads(PLAN.read_text())["items"] if row["id"] == "J-3c"))
    model = declared_model()
    model["items"] = [item]
    spec = item["step_evidence"]["pre_acceptance"]["detector"]
    path = ops / "acceptance" / (OPID + ".post.json")
    spec["path"] = str(path)
    events = tmp_path / "EVENTS.jsonl"
    events.write_text("")
    monkeypatch.setenv("PRAVAHA_HOME", str(home))
    monkeypatch.setattr(cli, "load_model", lambda: model)
    monkeypatch.setattr(cli, "EVENTS", str(events))
    detector = Detectors(Config(repo=str(tmp_path), home=str(home), pgenv=None))
    monkeypatch.setattr(cli, "get", lambda *a, **k: ({"item": "J-3c", "step": "pre_acceptance", "spec": spec,
                                                      "detector": {"status": detector.verify(spec).status}}, "live"))

    def write(target=path, **over):
        record = {"by": "v1", "result": "ACCEPTED", "operation_id": OPID, "request_sha256": digest,
                  "reviewed_commit": "a" * 40, "ts": "2026-10-18T15:16:11+00:00", **over}
        target.write_text(json.dumps(record, indent=1))

    def run(expected, evidence=path):
        code = cli.main(["step", "J-3c", "pre_acceptance", "--stream", "N", "--evidence", str(evidence)])
        assert code == expected
        lines = events.read_text().splitlines()
        if expected:
            assert not lines, "refusal must append no event"
        else:
            assert [json.loads(line)["kind"] for line in lines] == ["item"], "no verdict event is synthesised"

    write()
    yield type("W", (), dict(write=staticmethod(write), run=staticmethod(run), ops=ops, path=path, item=item,
                             request=request, receipt=receipt, digest=digest))
    detector._pool.shutdown(wait=True)


def test_pre_acceptance_is_evidenced_by_the_dispatch_acceptance_file(pre_step):
    pre_step.run(0)


def test_pre_acceptance_refuses_an_acceptance_of_another_request_digest(pre_step):
    pre_step.write(request_sha256="1" * 64)
    pre_step.run(2)


@pytest.mark.parametrize("requester", ["v1", "stream-V:v1"])
def test_pre_acceptance_refuses_the_requester_as_signer(pre_step, requester):
    (pre_step.ops / "done" / (OPID + ".json")).write_text(json.dumps({**pre_step.request, "requested_by": requester}))
    pre_step.receipt["request_sha256"] = cli._request_digest({**pre_step.request, "requested_by": requester})
    (pre_step.ops / "receipts" / (OPID + ".json")).write_text(json.dumps(pre_step.receipt))
    pre_step.write(request_sha256=pre_step.receipt["request_sha256"])
    pre_step.run(2)
    pre_step.write(request_sha256=pre_step.receipt["request_sha256"], by="v2")
    pre_step.run(0)


@pytest.mark.parametrize("change", [
    {"by": "codex"}, {"result": "REJECTED"},
    {"by": "executor-mechanical", "schema": "ky.mechanical_acceptance/1", "phase": "post",
     "checks": {"receipt_completed_exit_zero": True, "output_sha_equals_receipt": False}},
])
def test_pre_acceptance_refuses_a_record_not_signed_by_a_lane_or_by_all_true_mechanical_checks(pre_step, change):
    pre_step.write(**change)
    pre_step.run(2)


def test_pre_acceptance_accepts_the_mechanical_record_with_every_check_true(pre_step):
    pre_step.write(by="executor-mechanical", schema="ky.mechanical_acceptance/1", phase="post",
                   checks={"receipt_completed_exit_zero": True, "request_sha_equals_receipt": True})
    pre_step.run(0)


def test_pre_acceptance_refuses_an_evidence_file_that_is_not_the_declared_post_json(pre_step, tmp_path):
    elsewhere = tmp_path / "copy.post.json"
    pre_step.write(elsewhere)
    pre_step.run(2, evidence=elsewhere)


def test_pre_acceptance_refuses_a_declared_file_that_names_another_operation(pre_step):
    """The declared file J-3c.dispatch.post.json holds the acceptance of a different (valid, same-item) operation."""
    other = {**pre_step.request, "operation_id": "J-3c.other"}
    (pre_step.ops / "done" / "J-3c.other.json").write_text(json.dumps(other))
    digest = cli._request_digest(other)
    (pre_step.ops / "receipts" / "J-3c.other.json").write_text(json.dumps(
        {**pre_step.receipt, "operation_id": "J-3c.other", "request_sha256": digest}))
    pre_step.write(operation_id="J-3c.other", request_sha256=digest)
    # the plan's detector pattern already pins the operation id in the live tracker; the tracker's own check must too
    raw = pre_step.path.read_bytes()
    with pytest.raises(CompletionError, match="<operation_id>.post.json"):
        check_acceptance_file_evidence(raw, str(pre_step.path), {"path": str(pre_step.path)}, "J-3c", "pre_acceptance",
                                       str(pre_step.ops))


def test_pre_acceptance_refuses_another_items_operation(pre_step):
    """The operation, its receipt and the acceptance all agree, but they belong to J-3d, not J-3c."""
    other = {**pre_step.request, "item_id": "J-3d"}
    (pre_step.ops / "done" / (OPID + ".json")).write_text(json.dumps(other))
    digest = cli._request_digest(other)
    (pre_step.ops / "receipts" / (OPID + ".json")).write_text(json.dumps(
        {**pre_step.receipt, "item_id": "J-3d", "request_sha256": digest}))
    pre_step.write(request_sha256=digest)
    pre_step.run(2)


def test_the_plan_declares_j3c_pre_acceptance_as_the_dispatch_acceptance_file():
    plan = json.loads(PLAN.read_text())
    item = next(row for row in plan["items"] if row["id"] == "J-3c")
    declared = item["step_evidence"]["pre_acceptance"]
    assert declared["evidence"] == "acceptance_file"
    assert declared["detector"]["path"].endswith("/run/ops/acceptance/J-3c.dispatch.post.json")
    assert server._check_declarations(plan) == []


# ------------------------------------------------------------------------------ teardown

COUNTS = {name: 0 for name in sorted(ABSENCE_CENSUS)}
RUN_ID = "9b8a3c01-6eb9-4679-9434-680c29cf7492"
TEARDOWN_TS = "2026-10-19T00:35:46+00:00"


def _committed(**over):
    """A committed measuring teardown receipt in the executor's wire format (fleet/executor.py)."""
    return {"operation_id": "J-3d.teardown", "kind": "measuring_teardown", "item_id": "J-3d",
            "status": "AWAITING_ABSENCE", "exit_code": 0, "request_sha256": "4" * 64, "requested_by": "adhikarin",
            "reviewed_commit": "b" * 40, "ts": TEARDOWN_TS,
            "teardown": {"schema": "ky.measuring_teardown/1", "status": "COMMITTED_AWAITING_ABSENCE",
                         "scope": {"run_id": RUN_ID, "chart_id": "c" * 36, "generation": "5.0"},
                         "scope_sha256": "5" * 64, "rowset_sha256": "6" * 64}, **over}


def _write_absence(receipts: Path, acceptance: Path, committed: dict, *, ts="2026-10-19T00:42:20+00:00",
                   counts=None, accepted_over=None, absence_over=None):
    """The independent absence readback of `committed`: receipt + measured output + content acceptance by v1."""
    measured = {"counts": counts or COUNTS, "run_id": RUN_ID, "schema": "ky.smalltest_independent_absence/1",
                "baseline": False, "chart_id": "c" * 36, "generation": "5.0", "scope_sha256": "5" * 64,
                "rowset_sha256": "6" * 64, "registry_inert": True, "teardown_operation_id": committed["operation_id"],
                "teardown_receipt_sha256": evidence_digest(committed),
                "teardown_request_sha256": committed["request_sha256"]}
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(["absence_proof"])
    writer.writerow([json.dumps(measured)])
    output = receipts / "J-3d.absence.output.txt"
    output.write_text(buffer.getvalue())
    sha = hashlib.sha256(output.read_bytes()).hexdigest()
    absence = {"operation_id": "J-3d.absence", "kind": "readback_sql", "item_id": "J-3d", "status": "COMPLETED",
               "exit_code": 0, "request_sha256": "7" * 64, "requested_by": "adhikarin", "reviewed_commit": "b" * 40,
               "output_file": str(output), "output_sha256": sha, "ts": ts, **(absence_over or {})}
    (receipts / "J-3d.absence.json").write_text(json.dumps(absence))
    accepted = {"by": "v1", "result": "ACCEPTED", "operation_id": "J-3d.absence", "request_sha256": "7" * 64,
                "reviewed_commit": "b" * 40, "absence": {**measured, "output_sha256": sha}, **(accepted_over or {})}
    (acceptance / "J-3d.absence.absence.json").write_text(json.dumps(accepted))


@pytest.fixture
def teardown(tmp_path):
    receipts, acceptance = tmp_path / "ops" / "receipts", tmp_path / "ops" / "acceptance"
    receipts.mkdir(parents=True)
    acceptance.mkdir()
    committed = _committed()
    _write_absence(receipts, acceptance, committed)

    def check(committed=committed):
        return committed_teardown_absence_accepted(committed, str(receipts))

    return type("T", (), dict(receipts=receipts, acceptance=acceptance, committed=committed, check=staticmethod(check),
                              write=staticmethod(lambda committed=committed, **kw: _write_absence(receipts, acceptance, committed, **kw))))


def test_a_committed_teardown_with_a_bound_accepted_absence_is_complete(teardown):
    assert teardown.check() is True


def test_an_absence_bound_to_another_receipt_digest_is_refused(teardown):
    edited = {**teardown.committed, "reason": "edited after the absence was measured"}    # evidence_digest changes
    assert teardown.check(edited) is False


@pytest.mark.parametrize("accepted_over", [
    {"result": "REJECTED"}, {"by": "adhikarin"}, {"by": "adhikarin", "schema": "ky.mechanical_acceptance/1"},
    {"operation_id": "J-3x.absence"}, {"request_sha256": "8" * 64},
    {"by": "executor-mechanical", "schema": "ky.mechanical_acceptance/1", "phase": "post", "checks": {"a": True}},
])
def test_an_absence_that_is_not_independently_accepted_is_refused(teardown, accepted_over):
    teardown.write(accepted_over=accepted_over)
    assert teardown.check() is False


def test_an_absence_accepted_by_its_own_requester_is_refused(teardown):
    teardown.write(absence_over={"requested_by": "stream-V:v1"})
    assert teardown.check() is False


def test_a_missing_absence_acceptance_is_refused(teardown):
    (teardown.acceptance / "J-3d.absence.absence.json").unlink()
    assert teardown.check() is False


@pytest.mark.parametrize("change", [
    {"status": "FAILED"}, {"status": "RUNNING"}, {"exit_code": 1}, {"kind": "readback_sql"},
    {"teardown": {**_committed()["teardown"], "status": "ROLLED_BACK"}},
])
def test_a_teardown_that_is_not_committed_is_refused(teardown, change):
    committed = _committed(**change)
    teardown.write(committed)      # an absence honestly bound to THIS receipt: only the commit state is wrong
    assert teardown.check(committed) is False


def test_an_absence_that_does_not_follow_the_teardown_is_refused(teardown):
    teardown.write(ts=TEARDOWN_TS)
    assert teardown.check() is False


def test_a_later_staged_launch_refuses_the_older_absence(teardown):
    (teardown.receipts / "J-3c.dispatch.json").write_text(json.dumps(
        {"operation_id": "J-3c.dispatch", "kind": "measuring_dispatch", "status": "COMPLETED",
         "launch": {"run_id": "x"}, "ts": "2026-10-19T00:40:00+00:00"}))
    assert teardown.check() is False


@pytest.mark.parametrize("counts", [{**COUNTS, "build_runs": 1}, {k: v for k, v in COUNTS.items() if k != "build_runs"}])
def test_an_absence_with_a_nonzero_or_incomplete_census_is_refused(teardown, counts):
    teardown.write(counts=counts)
    assert teardown.check() is False


def test_the_tracker_census_equals_the_reviewed_policys():
    spec = importlib.util.spec_from_file_location("reviewed_policy", POLICY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    required = {table for table, _ in module.ABSENCE_TABLES} | {
        "kala_gochara_publication", "build_runs", "build_run_assets", "asset_provenance_receipts", "asset_freshness",
        "asset_throughput", "ka_gochara_eval_window_record", "ka_gochara_record_prerequisite",
        "ka_gochara_eval_window_verification", "ka_gochara_search_inventory_verification", "owned_test_runs"}
    assert set(ABSENCE_CENSUS) == required


def test_the_teardown_operation_step_binds_through_the_committed_receipt_and_the_absence(operation_step):
    """End to end: the step records for the committed teardown + accepted absence and the executor's own acceptance of
    the teardown request, with no completion.json and no verdict event."""
    w = operation_step
    w.req["kind"] = "measuring_teardown"
    w.request_path.write_text(json.dumps(w.req))
    w.executor.update(kind="measuring_teardown", status="AWAITING_ABSENCE", ts=TEARDOWN_TS,
                      request_sha256=hashlib.sha256(canonical(w.req).rstrip("\n").encode()).hexdigest(),
                      teardown=_committed()["teardown"])
    w.sync()
    _no_verdict(w)
    _accept(w)
    w.run(expected=2)      # committed, but no absence yet
    _write_absence(w.executor_path.parent, w.ops / "acceptance", w.executor)
    w.run(expected=0)
    assert {json.loads(line)["kind"] for line in w.events.read_text().splitlines()} == {"item"}
