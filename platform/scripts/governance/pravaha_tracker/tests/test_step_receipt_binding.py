"""W4-MR-B01: bind CLI step events to canonical receipt and source evidence."""
import hashlib
import json
from pathlib import Path

import pytest

from pravaha_tracker import cli
from pravaha_tracker.detectors import Config, Detectors
from pravaha_tracker.tests.test_kalayantra_control_plane import declared_model


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"


@pytest.fixture
def receipt_step(tmp_path, monkeypatch):
    receipt_path = tmp_path / "K-C.tests.json"
    jobs = tmp_path / "jobs"
    result_path = jobs / "X-review" / "result.json"
    result_path.parent.mkdir(parents=True)
    receipt = {"item": "K-C", "step": "tests", "verdict": "MET", "review_job": "X-review"}
    result = {"item": "K-C", "status": "done", "steps": [{"step": "tests", "verdict": "MET"}]}
    receipt_path.write_text(canonical(receipt))
    result_path.write_text(json.dumps(result))
    spec = {"type": "file_contains", "path": str(receipt_path), "pattern": "MET"}
    model = declared_model()
    model["items"][0].update(steps=["tests"], step_evidence={"tests": {"detector": spec}})
    events = tmp_path / "EVENTS.jsonl"
    monkeypatch.setattr(cli, "load_model", lambda: model)
    monkeypatch.setattr(cli, "EVENTS", str(events))
    monkeypatch.setenv("PRAVAHA_REVIEW_JOBS", str(jobs))
    detector = Detectors(Config(repo=str(tmp_path), home=str(tmp_path), pgenv=None))

    def live(*args, **kwargs):
        return {"item": "K-C", "step": "tests", "spec": spec,
                "detector": {"status": detector.verify(spec).status}}, "live"

    monkeypatch.setattr(cli, "get", live)

    def run(evidence=None, expected=2):
        code = cli.main(["step", "K-C", "tests", "--stream", "K", "--evidence",
                         str(evidence or receipt_path)])
        assert code == expected
        if expected:
            assert not events.exists(), "refusal must append no event"
        else:
            event = json.loads(events.read_text().splitlines()[-1])
            assert event["evidence_sha256"] == hashlib.sha256(Path(evidence or receipt_path).read_bytes()).hexdigest()
        return code

    return tmp_path, receipt_path, receipt, result_path, result, spec, run


def test_refuses_unrelated_evidence(receipt_step):
    root, _, _, _, _, _, run = receipt_step
    unrelated = root / "unrelated.txt"
    unrelated.write_text("unrelated evidence")
    run(unrelated)


@pytest.mark.parametrize("raw", [
    'not JSON MET',
    '["MET"]',
    '{"item":"K-C","step":"tests","verdict":"MET"} {}',
    '{"item":"wrong","item":"K-C","step":"tests","verdict":"MET"}',
    '{"item": "K-C", "step": "tests", "verdict": "MET"}',
    '{"step":"tests","item":"K-C","verdict":"MET"}',
    '{"item":"K-C","step":"tests","value":NaN,"verdict":"MET"}',
])
def test_refuses_noncanonical_receipt(receipt_step, raw):
    _, path, _, _, _, _, run = receipt_step
    path.write_text(raw)
    run()


@pytest.mark.parametrize("field,value", [("item", "K-D"), ("step", "docs"), ("item", None), ("step", None)])
def test_refuses_wrong_receipt_identity(receipt_step, field, value):
    _, path, receipt, _, _, _, run = receipt_step
    receipt[field] = value
    path.write_text(canonical(receipt))
    run()


@pytest.mark.parametrize("raw", [None, "not JSON", "[]"])
def test_refuses_missing_or_invalid_review_result(receipt_step, raw):
    _, _, _, result_path, _, _, run = receipt_step
    if raw is None:
        result_path.unlink()
    else:
        result_path.write_text(raw)
    run()


@pytest.mark.parametrize("change", ["wrong_item", "wrong_step", "not_met", "no_steps", "duplicate_step"])
def test_refuses_review_without_this_step_met(receipt_step, change):
    _, _, _, result_path, result, _, run = receipt_step
    if change == "wrong_item":
        result["item"] = "K-D"
    elif change == "wrong_step":
        result["steps"][0]["step"] = "docs"
    elif change == "not_met":
        result["steps"][0]["verdict"] = "UNMET"
    elif change == "no_steps":
        del result["steps"]
    else:
        result["steps"].append({"step": "tests", "verdict": "UNMET"})
    result_path.write_text(json.dumps(result))
    run()


@pytest.mark.parametrize("job", ["../outside", "/absolute", "", None, ["X-review"]])
def test_refuses_invalid_review_job(receipt_step, job):
    _, path, receipt, _, _, _, run = receipt_step
    receipt["review_job"] = job
    path.write_text(canonical(receipt))
    run()


@pytest.mark.parametrize("problem", ["wrong_hash", "missing_artifact", "missing_path"])
def test_refuses_unbound_artifact(receipt_step, problem):
    root, path, receipt, _, _, _, run = receipt_step
    artifact = root / "artifact.txt"
    artifact.write_bytes(b"reviewed artifact")
    receipt.update(artifact_path=str(artifact), artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest())
    if problem == "wrong_hash":
        receipt["artifact_sha256"] = "0" * 64
    elif problem == "missing_artifact":
        artifact.unlink()
    else:
        del receipt["artifact_path"]
    path.write_text(canonical(receipt))
    run()


def test_artifact_hash_does_not_replace_a_named_missing_review(receipt_step):
    root, path, receipt, result_path, _, _, run = receipt_step
    artifact = root / "artifact.txt"
    artifact.write_bytes(b"reviewed artifact")
    receipt.update(artifact_path=str(artifact), artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest())
    path.write_text(canonical(receipt))
    result_path.unlink()
    run()


def test_refuses_review_job_symlink_outside_jobs_root(receipt_step):
    root, _, _, result_path, result, _, run = receipt_step
    outside = root / "outside.json"
    outside.write_text(json.dumps(result))
    result_path.unlink()
    result_path.symlink_to(outside)
    run()


@pytest.mark.parametrize("newline", ["", "\n"])
def test_accepts_canonical_receipt_without_review_job(receipt_step, newline):
    _, path, receipt, _, _, _, run = receipt_step
    del receipt["review_job"]
    path.write_text(canonical(receipt).rstrip("\n") + newline)
    run(expected=0)


def test_accepts_bound_review_receipt_and_resolved_alias(receipt_step):
    root, path, _, _, _, _, run = receipt_step
    alias = root / "alias.json"
    alias.symlink_to(path)
    run(alias, expected=0)


def test_accepts_artifact_hash_alternative(receipt_step):
    root, path, receipt, result_path, result, _, run = receipt_step
    artifact = root / "artifact.txt"
    artifact.write_bytes(b"reviewed artifact")
    receipt.update(artifact_path=artifact.name, artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest())
    result["steps"] = []
    result_path.write_text(json.dumps(result))
    path.write_text(canonical(receipt))
    run(expected=0)


def test_file_exists_steps_keep_existing_behavior(receipt_step):
    root, _, _, _, _, spec, run = receipt_step
    spec["type"] = "file_exists"
    # The observation transport is isolated; other detector types keep their prior contract.
    unrelated = root / "tests.log"
    unrelated.write_text("tests passed")
    run(unrelated, expected=0)


@pytest.mark.parametrize("position", [0, 1])
@pytest.mark.parametrize("bind_artifact", [False, True])
def test_accepts_batched_review_for_exactly_one_matching_item(receipt_step, position, bind_artifact):
    root, path, receipt, result_path, result, _, run = receipt_step
    if bind_artifact:
        artifact = root / "artifact.txt"
        artifact.write_bytes(b"reviewed artifact")
        receipt.update(artifact_path=str(artifact), artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest())
        path.write_text(canonical(receipt))
    items = [{"item": "K-D", "steps": [{"step": "tests", "verdict": "NOT_MET"}]}]
    items.insert(position, result)
    result_path.write_text(json.dumps({"head": "reviewed-head", "items": items}))
    run(expected=0)


@pytest.mark.parametrize("problem", [
    "absent", "duplicate", "not_met", "wrong_step", "no_steps", "duplicate_step",
    "items_null", "items_object", "items_string",
])
@pytest.mark.parametrize("bind_artifact", [False, True])
def test_refuses_invalid_batched_review_without_single_item_fallback(receipt_step, problem, bind_artifact):
    root, path, receipt, result_path, result, _, run = receipt_step
    if bind_artifact:
        artifact = root / "artifact.txt"
        artifact.write_bytes(b"artifact hash cannot authorize a batch verdict")
        receipt.update(artifact_path=str(artifact), artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest())
        path.write_text(canonical(receipt))
    entry = {"item": "K-C", "steps": [{"step": "tests", "verdict": "MET"}]}
    items = [entry, {"item": "K-D", "steps": [{"step": "tests", "verdict": "MET"}]}]
    if problem == "absent":
        items.pop(0)
    elif problem == "duplicate":
        items.append({"item": "K-C", "steps": []})
    elif problem == "not_met":
        entry["steps"][0]["verdict"] = "NOT_MET"
    elif problem == "wrong_step":
        entry["steps"][0]["step"] = "docs"
    elif problem == "no_steps":
        del entry["steps"]
    elif problem == "duplicate_step":
        entry["steps"].append({"step": "tests", "verdict": "MET"})
    elif problem == "items_null":
        items = None
    elif problem == "items_object":
        items = entry
    else:
        items = "K-C"
    # Even valid legacy fields cannot override a present, invalid batch.
    result_path.write_text(json.dumps({**result, "items": items}))
    run()


@pytest.fixture(params=["J-4b-a55j", "J-4c-a55m"])
def operation_step(tmp_path, monkeypatch, request):
    """Actual operation-step declarations and executor.py receipt/request wire formats."""
    import copy
    from types import SimpleNamespace

    source = json.loads((Path(cli.REPO_ROOT) / "00_ARCHITECTURE/control/kalayantra/plan_model.json").read_text())
    item = copy.deepcopy(next(row for row in source["items"] if row["id"] == request.param))
    model = declared_model()
    model["items"] = [item]
    step = item["steps"][0]
    spec = item["step_evidence"][step]["detector"]
    home = tmp_path / "home"
    ops = home / "run/ops"
    executor_path = ops / "receipts" / (item["id"] + ".json")
    executor_path.parent.mkdir(parents=True)
    item["detector"]["path"] = str(executor_path)
    receipt_path = home / "run/reviews/steps" / (item["id"] + "." + step + ".json")
    receipt_path.parent.mkdir(parents=True)
    spec["path"] = str(receipt_path)
    output = executor_path.with_suffix(".output.txt")
    output.write_bytes(b"independently measured fixture readback\n")
    req = {"operation_id": item["id"], "kind": "readback_sql", "item_id": item["id"],
           "requested_by": "adhikarin", "kyd": "fixture", "reviewed_commit": "a" * 40,
           "idempotency_key": item["id"], "args": {"sql_file": "fixture.sql"}}
    request_path = ops / "done" / (item["id"] + ".json")
    request_path.parent.mkdir()
    request_path.write_text(json.dumps(req))
    executor = {"operation_id": item["id"], "kind": req["kind"], "item_id": item["id"],
                "status": "COMPLETED", "reason": "", "exit_code": 0, "stdout_tail": "fixture readback",
                "ts": "2026-10-16T00:00:00Z", "reviewed_commit": req["reviewed_commit"],
                "requested_by": req["requested_by"], "kyd": req["kyd"],
                "request_sha256": hashlib.sha256(canonical(req).rstrip("\n").encode()).hexdigest(),
                "output_file": str(output), "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "output_bytes": output.stat().st_size}
    job = "X-20261016T000000Z-operation-review"
    jobs = tmp_path / "jobs"
    result_path = jobs / job / "result.json"
    result_path.parent.mkdir(parents=True)
    result = {"item": item["id"], "steps": [{"step": step, "verdict": "MET"}], "status": "done"}
    result_path.write_text(json.dumps(result))
    receipt = {"item": item["id"], "step": step, "verdict": "MET", "review_job": job,
               "operation_id": item["id"], "request_id": item["id"], "evidence_sha256": "0" * 64}
    events = home / "run/EVENTS.jsonl"
    verdict = {"kind": "verdict", "actor": "stream-V:v2", "item": item["id"], "phase": "artifact",
               "artifact_digest": "0" * 64, "result": "ACCEPTED", "detail": "independent measured readback"}
    monkeypatch.setenv("PRAVAHA_HOME", str(home))
    monkeypatch.setenv("PRAVAHA_REVIEW_JOBS", str(jobs))
    monkeypatch.setattr(cli, "load_model", lambda: model)
    monkeypatch.setattr(cli, "EVENTS", str(events))
    detector = Detectors(Config(repo=str(tmp_path), home=str(home), pgenv=None))

    def live(*args, **kwargs):
        return {"item": item["id"], "step": step, "spec": spec,
                "detector": {"status": detector.verify(spec).status}}, "live"

    monkeypatch.setattr(cli, "get", live)

    def sync():
        executor_path.write_text(json.dumps(executor, sort_keys=True, indent=2) + "\n")
        digest = hashlib.sha256(executor_path.read_bytes()).hexdigest()
        receipt["evidence_sha256"] = digest
        verdict["artifact_digest"] = digest
        receipt_path.write_text(canonical(receipt))
        # Keep this fixture's event setup real, but allow deliberately invalid identities.
        events.write_text(json.dumps(verdict) + "\n")

    def run(expected=2):
        before = events.read_bytes() if events.exists() else None
        code = cli.main(["step", item["id"], step, "--stream", "N", "--evidence", str(receipt_path)])
        assert code == expected
        if expected:
            assert (events.read_bytes() if events.exists() else None) == before, "refusal must append no event"
        else:
            event = json.loads(events.read_text().splitlines()[-1])
            assert (event["item"], event["step"], event["state"]) == (item["id"], step, "done")
            assert event["evidence_sha256"] == hashlib.sha256(receipt_path.read_bytes()).hexdigest()
        return code

    sync()
    yield SimpleNamespace(**locals())
    detector._pool.shutdown(wait=True)


def test_accepts_bound_operation_step(operation_step):
    operation_step.run(expected=0)


@pytest.mark.parametrize("problem", [
    "missing_receipt", "wrong_evidence_digest", "wrong_operation", "wrong_item", "wrong_request",
    "wrong_request_digest", "changed_request", "missing_request", "wrong_request_item",
    "wrong_request_operation", "wrong_requester", "missing_requester", "receipt_outside_root",
    "receipt_symlink_escape", "not_completed", "exit_nonzero", "exit_false", "missing_output",
    "wrong_output_digest", "empty_output", "output_symlink_escape", "missing_output_digest",
    "missing_acceptance", "wrong_acceptance_digest", "wrong_acceptance_item", "wrong_acceptance_phase",
    "rejected_acceptance", "revoked_acceptance", "requester_accepts", "requester_slot_accepts",
    "no_acceptance_slot", "wrong_acceptance_stream", "missing_review", "unbound_artifact_alternative",
])
def test_refuses_unbound_operation_step(operation_step, problem):
    w = operation_step
    # Each mutation isolates a formerly unchecked binding; sync keeps the receipt digest valid
    # after mutations to the executor JSON so an earlier digest refusal cannot mask the check.
    if problem == "wrong_operation":
        w.executor["operation_id"] = "OTHER-OP"
    elif problem == "wrong_item":
        w.executor["item_id"] = "OTHER-ITEM"
    elif problem == "wrong_request_digest":
        w.executor["request_sha256"] = "f" * 64
    elif problem == "not_completed":
        w.executor["status"] = "FAILED"
    elif problem == "exit_nonzero":
        w.executor["exit_code"] = 1
    elif problem == "exit_false":
        w.executor["exit_code"] = False
    elif problem == "missing_requester":
        del w.executor["requested_by"]
    elif problem == "wrong_requester":
        w.executor["requested_by"] = "surrogate"
    elif problem == "wrong_output_digest":
        w.executor["output_sha256"] = "e" * 64
    elif problem == "missing_output_digest":
        del w.executor["output_sha256"]
    elif problem in ("requester_accepts", "requester_slot_accepts"):
        w.req["requested_by"] = "stream-N:v2" if problem == "requester_slot_accepts" else "v2"
        w.request_path.write_text(json.dumps(w.req))
        w.executor["requested_by"] = w.req["requested_by"]
        w.executor["request_sha256"] = hashlib.sha256(canonical(w.req).rstrip("\n").encode()).hexdigest()
    w.sync()
    if problem == "missing_receipt":
        w.executor_path.unlink()
    elif problem == "wrong_evidence_digest":
        w.receipt["evidence_sha256"] = "0" * 64
    elif problem == "wrong_request":
        w.receipt["request_id"] = "UNRELATED-REQUEST"
    elif problem == "missing_request":
        w.request_path.unlink()
    elif problem in ("changed_request", "wrong_request_item", "wrong_request_operation"):
        key = {"changed_request": "args", "wrong_request_item": "item_id",
               "wrong_request_operation": "operation_id"}[problem]
        w.req[key] = {"sql_file": "unreviewed.sql"} if key == "args" else "OTHER"
        w.request_path.write_text(json.dumps(w.req))
    elif problem in ("receipt_outside_root", "receipt_symlink_escape"):
        outside = w.tmp_path / "outside.json"
        outside.write_bytes(w.executor_path.read_bytes())
        if problem == "receipt_outside_root":
            w.executor_path.unlink()
            w.item["detector"]["path"] = str(outside)
        else:
            w.executor_path.unlink()
            w.executor_path.symlink_to(outside)
    elif problem == "missing_output":
        w.output.unlink()
    elif problem == "empty_output":
        w.output.write_bytes(b"")
        w.executor["output_sha256"] = hashlib.sha256(b"").hexdigest()
        w.executor["output_bytes"] = 0
        w.sync()
    elif problem == "output_symlink_escape":
        outside = w.tmp_path / "outside.txt"
        outside.write_bytes(w.output.read_bytes())
        w.output.unlink()
        w.output.symlink_to(outside)
    elif problem == "missing_acceptance":
        w.events.write_text("")
    elif problem.startswith("wrong_acceptance_"):
        key = {"wrong_acceptance_digest": "artifact_digest", "wrong_acceptance_item": "item",
               "wrong_acceptance_phase": "phase", "wrong_acceptance_stream": "actor"}[problem]
        w.verdict[key] = "0" * 64 if key == "artifact_digest" else "OTHER"
        w.events.write_text(json.dumps(w.verdict) + "\n")
    elif problem == "no_acceptance_slot":
        w.verdict["actor"] = "stream-V"
        w.events.write_text(json.dumps(w.verdict) + "\n")
    elif problem in ("rejected_acceptance", "revoked_acceptance"):
        w.verdict["result"] = "REJECTED"
        with w.events.open("a" if problem == "revoked_acceptance" else "w") as handle:
            handle.write(json.dumps(w.verdict) + "\n")
    elif problem == "missing_review":
        del w.receipt["review_job"]
        # An operation must not inherit the legacy artifact-without-review shortcut.
        w.spec["pattern"] = "MET"
    elif problem == "unbound_artifact_alternative":
        w.result["steps"] = []
        w.result_path.write_text(json.dumps(w.result))
        w.receipt.update(artifact_path=str(w.output), artifact_sha256=w.executor["output_sha256"])
        w.spec["pattern"] = "MET"
    w.receipt_path.write_text(canonical(w.receipt))
    w.run()


@pytest.mark.parametrize("position", [0, 1])
def test_accepts_bound_operation_with_batched_step_review(operation_step, position):
    w = operation_step
    items = [{"item": "OTHER", "steps": []}]
    items.insert(position, w.result)
    w.result_path.write_text(json.dumps({"items": items}))
    w.run(expected=0)


def test_operation_kind_cannot_bypass_binding_with_file_exists(operation_step):
    w = operation_step
    w.spec["type"] = "file_exists"
    w.executor_path.unlink()
    w.run()


def test_operation_step_preserves_recording_lane(operation_step, monkeypatch):
    w = operation_step
    monkeypatch.setenv("KY_LANE", "n1")
    w.run(expected=0)
    assert json.loads(w.events.read_text().splitlines()[-1])["actor"] == "stream-N:n1"


def test_accepts_actual_executor_producer_receipt(operation_step, monkeypatch):
    import importlib.util

    w = operation_step
    path = Path(cli.REPO_ROOT) / "00_ARCHITECTURE/briefs/kalayantra/fleet/executor.py"
    spec = importlib.util.spec_from_file_location("step_binding_executor_fixture", path)
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    # Importing the executor does not start it. Only its real receipt encoder runs,
    # with every write redirected into this test's disposable home.
    monkeypatch.setattr(producer, "KY_ROOT", w.home)
    monkeypatch.setattr(producer, "REC", w.executor_path.parent)
    (w.home / "logs").mkdir()
    w.req["acceptance_receipt"] = str(w.ops / "acceptance" / (w.item["id"] + ".json"))
    w.request_path.write_text(json.dumps(w.req))
    producer.receipt(w.req, "COMPLETED", rc=0, out="independent executor encoder fixture\n")
    digest = hashlib.sha256(w.executor_path.read_bytes()).hexdigest()
    w.receipt["evidence_sha256"] = digest
    w.receipt_path.write_text(canonical(w.receipt))
    w.verdict["artifact_digest"] = digest
    w.events.write_text(json.dumps(w.verdict) + "\n")
    w.run(expected=0)


def test_accepts_operation_output_relative_to_receipt(operation_step):
    w = operation_step
    w.executor["output_file"] = w.output.name
    w.sync()
    w.run(expected=0)


def test_operation_step_resolves_the_cited_executor_id(operation_step):
    w = operation_step
    # The real dispatcher defaults to OP-<item> (and OP-<item>-s<n> for
    # multiple operations), independently of the item's terminal detector path.
    opid = "OP-" + w.item["id"] + "-s1"
    w.req.update(operation_id=opid, idempotency_key=opid)
    w.request_path.unlink()
    (w.ops / "done" / (opid + ".json")).write_text(json.dumps(w.req))
    w.executor["operation_id"] = opid
    w.executor["request_sha256"] = hashlib.sha256(canonical(w.req).rstrip("\n").encode()).hexdigest()
    new_path = w.executor_path.with_name(opid + ".json")
    new_path.write_text(json.dumps(w.executor))
    w.executor_path.unlink()
    digest = hashlib.sha256(new_path.read_bytes()).hexdigest()
    w.receipt.update(operation_id=opid, request_id=opid, evidence_sha256=digest)
    w.receipt_path.write_text(canonical(w.receipt))
    w.verdict["artifact_digest"] = digest
    w.events.write_text(json.dumps(w.verdict) + "\n")
    w.run(expected=0)
