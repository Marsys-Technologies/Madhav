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


def test_teardown_awaiting_absence_needs_the_executor_completion_bound_to_the_absence_receipt(operation_step):
    """fleet/executor.py: a committed teardown is AWAITING_ABSENCE until fence_quiescent() publishes
    <op>.completion.json (ky.smalltest_completion/1) naming the accepted absence receipt by sha256."""
    w = operation_step
    receipts = w.executor_path.parent
    absence = receipts / "ABSENCE-readback.json"
    absence.write_text(json.dumps({"operation_id": "ABSENCE-readback", "status": "COMPLETED"}))
    w.req["kind"] = "smalltest_teardown"
    w.request_path.write_text(json.dumps(w.req))
    w.executor.update(kind="smalltest_teardown", status="AWAITING_ABSENCE",
                      request_sha256=hashlib.sha256(canonical(w.req).rstrip("\n").encode()).hexdigest())
    w.sync()
    completion = receipts / (w.item["id"] + ".completion.json")
    completion.write_text(json.dumps({
        "schema": "ky.smalltest_completion/1", "status": "COMPLETED", "operation_id": w.item["id"],
        "request_sha256": w.executor["request_sha256"],
        "commit_receipt_sha256": hashlib.sha256(w.executor_path.read_bytes()).hexdigest(),
        "absence_receipt": {"name": absence.name, "sha256": hashlib.sha256(absence.read_bytes()).hexdigest()}}))
    w.run(expected=0)
    # The absence receipt changed after the executor named it: the step must be refused again.
    w.events.write_text(json.dumps(w.verdict) + "\n")
    absence.write_text(json.dumps({"operation_id": "ABSENCE-readback", "status": "FAILED"}))
    w.run(expected=2)


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


@pytest.fixture
def evidence_step(receipt_step):
    root, path, receipt, result_path, result, spec, run = receipt_step
    request = {'request_id': 'REQ-1', 'operation_id': 'OP-1', 'kind': 'publish_head',
               'chart_id': '482012f1-710e-4a25-994a-93821f5871aa',
               'args': {'generation': '5.0', 'manifest-id': '0d1f8a52-6f0e-4c7e-9a3b-5a2a2f6f9c11'},
               'reviewed_commit': 'a'*40}
    request_sha = hashlib.sha256(canonical(request).strip().encode()).hexdigest()
    source_receipt = {'operation_id': 'OP-1', 'kind': 'publish_head', 'status': 'COMPLETED',
                      'exit_code': 0, 'request_sha256': request_sha, 'reviewed_commit': 'a'*40}
    readback = {'request_id': 'REQ-1', 'operation_id': 'OP-1', 'request_sha256': request_sha,
                'result': 'ACCEPTED', 'by': 'v2', 'reviewed_commit': 'a'*40}
    sources = {}
    for key, value in [('request', request), ('receipt', source_receipt), ('readback', readback)]:
        if key == 'readback': value['executor_receipt_sha256'] = sources['receipt']['sha256']
        p = root / (key + '.json')
        p.write_text(canonical(value))
        sources[key] = {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    evidence = root / 'observed.json'
    evidence.write_text(canonical({'request_id': 'REQ-1', 'operation_id': 'OP-1', 'sources': sources}))
    receipt.update(evidence_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),
                   request_id='REQ-1', operation_id='OP-1')
    result['steps'] = [{**receipt, 'evidence_path': str(evidence)}]
    result_path.write_text(json.dumps(result))
    path.write_text(canonical(receipt))
    return root, path, receipt, result_path, result, evidence, run


def test_operational_step_accepts_actual_evidence_and_source_chain(evidence_step):
    *_, run = evidence_step
    run(expected=0)


@pytest.mark.parametrize('damage', ['evidence_sha256', 'request_id', 'operation_id', 'evidence_bytes',
                                  'source_bytes', 'source_identity', 'source_request_digest', 'readback_receipt_digest', 'missing_evidence_path'])
def test_operational_step_rejects_unbound_evidence_at_real_command(evidence_step, damage):
    root, path, receipt, result_path, result, evidence, run = evidence_step
    if damage in ('evidence_sha256', 'request_id', 'operation_id'):
        receipt[damage] = '0' * 64 if damage.endswith('sha256') else 'OTHER'
        path.write_text(canonical(receipt))
    elif damage == 'evidence_bytes': evidence.write_text(evidence.read_text() + ' ')
    elif damage == 'source_bytes':
        source = root / 'readback.json'
        source.write_text(source.read_text() + ' ')
    elif damage == 'missing_evidence_path':
        del result['steps'][0]['evidence_path']
        result_path.write_text(json.dumps(result))
    else:
        key = ('operation_id' if damage == 'source_identity' else 'executor_receipt_sha256'
               if damage == 'readback_receipt_digest' else 'request_sha256')
        source = root / 'readback.json'
        value = json.loads(source.read_text()); value[key] = 'OTHER'
        source.write_text(canonical(value))
        doc = json.loads(evidence.read_text())
        doc['sources']['readback']['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
        evidence.write_text(canonical(doc))
        receipt['evidence_sha256'] = hashlib.sha256(evidence.read_bytes()).hexdigest()
        result['steps'][0]['evidence_sha256'] = receipt['evidence_sha256']
        path.write_text(canonical(receipt)); result_path.write_text(json.dumps(result))
    run()


def _soak_fixture(evidence_step):
    import base64
    root, path, receipt, result_path, result, evidence, run = evidence_step
    rule = {'schema': 'ky.soak_rule/1', 'decision_id': 'KYD-soak-fixture',
            'approved_at': '2026-10-16T00:00:00Z', 'start': '2026-10-16T01:00:00Z',
            'end': '2026-10-16T01:00:20Z', 'cadence_s': 10, 'max_lateness_s': 1,
            'max_latency_ms': 500, 'required_classes': ['marriage'],
            'chart_id': '482012f1-710e-4a25-994a-93821f5871aa',
            'generation': '5.0', 'manifest_id': '0d1f8a52-6f0e-4c7e-9a3b-5a2a2f6f9c11',
            'deployment': {'commit': 'a'*40, 'image_digest': 'sha256:'+'b'*64,
                           'migration_set_sha256': 'c'*64},
            'transport': 'authority_selected_http'}
    rule_path = root / 'rule.json'; rule_path.write_text(canonical(rule))
    rule_ref = {'path': str(rule_path), 'sha256': hashlib.sha256(rule_path.read_bytes()).hexdigest()}
    doc = json.loads(evidence.read_text())
    doc.update(schema='ky.served_soak/1', rule=rule_ref, samples=[])
    body = {'schema': 'gochara_v5_windows/1', 'chart_id': rule['chart_id'], 'generation': '5.0', 'manifest_id': rule['manifest_id'],
            'refusal': None, 'manifest_status': 'published',
            'seal': {'chart_id': rule['chart_id'], 'generation': '5.0', 'manifest_id': rule['manifest_id']},
            'classes': [{'event_class': 'marriage', 'completeness': 'complete_within_scope'}]}
    raw = canonical(body).encode()
    for n in (0, 10, 20):
        doc['samples'].append({'scheduled_at': f'2026-10-16T01:00:{n:02d}Z',
            'observed_at': f'2026-10-16T01:00:{n:02d}Z', 'latency_ms': 100, 'http_status': 200,
            'transport': rule['transport'], 'deployment': rule['deployment'],
            'response_base64': base64.b64encode(raw).decode(), 'response_sha256': hashlib.sha256(raw).hexdigest()})
    readback_path = root/'readback.json'; readback = json.loads(readback_path.read_text())
    readback.update(chart_id=rule['chart_id'], generation='5.0', manifest_id=rule['manifest_id'],
                    deployment=rule['deployment'])
    readback_path.write_text(canonical(readback))
    doc['sources']['readback']['sha256'] = hashlib.sha256(readback_path.read_bytes()).hexdigest()
    def save():
        evidence.write_text(canonical(doc))
        receipt['evidence_sha256'] = hashlib.sha256(evidence.read_bytes()).hexdigest()
        result['steps'][0].update(evidence_sha256=receipt['evidence_sha256'],
                                 soak_rule_sha256=rule_ref['sha256'], effective_soak_decision=rule['decision_id'])
        result_path.write_text(json.dumps(result)); path.write_text(canonical(receipt))
    save()
    return root, doc, rule, save, run


def test_soak_measures_all_preregistered_samples(evidence_step):
    *_, run = _soak_fixture(evidence_step)
    run(expected=0)


@pytest.mark.parametrize('damage', ['wrong_generation', 'wrong_manifest', 'wrong_chart', 'domain_refusal',
    'timeout', 'missing_sample', 'duplicate_sample', 'late_sample', 'rolled_back', 'wrong_deployment',
    'explicit_generation_transport', 'bytes_changed', 'stale_class', 'missing_class', 'unreviewed_rule',
    'unregistered_rule', 'missing_schema', 'wrong_envelope_schema', 'missing_refusal'])
def test_soak_rejects_bad_provenance_timeout_gaps_and_rollback(evidence_step, damage):
    import base64
    root, doc, rule, save, run = _soak_fixture(evidence_step)
    sample = doc['samples'][1]
    if damage in ('wrong_generation', 'wrong_manifest', 'wrong_chart', 'domain_refusal', 'stale_class', 'missing_class',
                  'wrong_envelope_schema', 'missing_refusal'):
        body = json.loads(base64.b64decode(sample['response_base64']))
        if damage == 'wrong_generation': body['generation'] = '3.0'
        elif damage == 'wrong_manifest': body['manifest_id'] = 'other'
        elif damage == 'wrong_chart': body['chart_id'] = 'other'
        elif damage == 'domain_refusal': body['refusal'] = {'code': 'not_sealed'}
        elif damage == 'wrong_envelope_schema': body['schema'] = 'unrelated_envelope/1'
        elif damage == 'missing_refusal': del body['refusal']
        elif damage == 'stale_class': body['classes'][0]['completeness'] = 'stale_binding'
        else: body['classes'] = []
        raw = canonical(body).encode(); sample.update(response_base64=base64.b64encode(raw).decode(),
                                                    response_sha256=hashlib.sha256(raw).hexdigest())
    elif damage == 'timeout': sample['latency_ms'] = 501
    elif damage == 'missing_sample': doc['samples'].pop(1)
    elif damage == 'duplicate_sample': doc['samples'].append(dict(sample))
    elif damage == 'late_sample': sample['observed_at'] = '2026-10-16T01:00:12Z'
    elif damage == 'rolled_back': doc['rollback_operation_id'] = 'ROLLBACK-1'
    elif damage == 'wrong_deployment': sample['deployment'] = {'commit': 'd'*40}
    elif damage == 'explicit_generation_transport': sample['transport'] = 'explicit_generation_http'
    elif damage == 'bytes_changed': sample['response_base64'] = base64.b64encode(b'{}').decode()
    elif damage == 'missing_schema': del doc['schema']
    elif damage == 'unregistered_rule':
        rule['approved_at'] = '2026-10-16T01:00:01Z'
        (root/'rule.json').write_text(canonical(rule))
        doc['rule']['sha256'] = hashlib.sha256((root/'rule.json').read_bytes()).hexdigest()
    save()
    if damage == 'unreviewed_rule':
        result_path = evidence_step[3]; result = evidence_step[4]
        result['steps'][0]['soak_rule_sha256'] = '0'*64
        result_path.write_text(json.dumps(result))
    # Enforce the same schema at the named production step as well as generic tests.
    if damage == 'missing_schema':
        from pravaha_tracker.operation_evidence import check_operation_evidence
        with pytest.raises(cli.CompletionError):
            check_operation_evidence({**evidence_step[2], 'item': 'J-6l-a61',
                                      'step': 'owner_soak_rule_and_live_readback'},
                                     evidence_step[4]['steps'][0], str(evidence_step[3]))
    else: run()


def _as_executor_operation(soak, home, monkeypatch):
    """Re-bind the soak chain's sources to the executor wire formats the operation step also checks:
    ops/receipts/<op>.json, ops/done/<op>.json (request_id == operation_id), a measured output, and an
    independent ACCEPTED verdict at the executor receipt digest (cli._check_operation_step)."""
    root, doc, rule, save, _ = soak
    item = 'J-6l-a61'
    ops = home / 'run/ops'
    for sub in ('receipts', 'done'):
        (ops / sub).mkdir(parents=True)
    request_path = root / 'request.json'
    request = json.loads(request_path.read_text())
    request.update(request_id='OP-1', item_id=item, operation_id='OP-1', requested_by='adhikarin', kyd='fixture')
    request_path.write_text(canonical(request))
    (ops / 'done/OP-1.json').write_bytes(request_path.read_bytes())
    request_sha = hashlib.sha256(canonical(request).strip().encode()).hexdigest()
    output = ops / 'receipts/OP-1.output.txt'
    output.write_bytes(b'independently measured fixture readback\n')
    executed = json.loads((root / 'receipt.json').read_text())
    executed.update(item_id=item, requested_by='adhikarin', kyd='fixture', request_sha256=request_sha,
                    output_file=str(output), output_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
    (root / 'receipt.json').write_text(canonical(executed))
    (ops / 'receipts/OP-1.json').write_bytes((root / 'receipt.json').read_bytes())
    executor_sha = hashlib.sha256((root / 'receipt.json').read_bytes()).hexdigest()
    readback_path = root / 'readback.json'
    readback = json.loads(readback_path.read_text())
    readback.update(request_id='OP-1', request_sha256=request_sha, executor_receipt_sha256=executor_sha)
    readback_path.write_text(canonical(readback))
    for key in ('request', 'receipt', 'readback'):
        doc['sources'][key]['sha256'] = hashlib.sha256((root / (key + '.json')).read_bytes()).hexdigest()
    doc['request_id'] = 'OP-1'
    verdict = {'kind': 'verdict', 'actor': 'stream-V:v2', 'item': item, 'phase': 'artifact',
               'artifact_digest': executor_sha, 'result': 'ACCEPTED', 'detail': 'independent measured readback'}
    events = home / 'run/EVENTS.jsonl'
    events.write_text(json.dumps(verdict) + '\n')
    monkeypatch.setenv('PRAVAHA_HOME', str(home))
    monkeypatch.setattr(cli, 'EVENTS', str(events))
    return events


@pytest.mark.parametrize('damage', ['evidence_sha256', 'request_id', 'operation_id', 'no_acceptance',
                                    'executor_receipt_not_at_ops', 'soak_without_evidence_path', 'none'])
def test_j6l_actual_named_soak_step_command_binds_review_and_samples(evidence_step, monkeypatch, tmp_path, damage):
    from pathlib import Path
    soak = _soak_fixture(evidence_step)
    root, doc, rule, save, _ = soak
    events = _as_executor_operation(soak, tmp_path / 'home', monkeypatch)
    save()
    _, path, receipt, result_path, result, evidence, _ = evidence_step
    item, step = 'J-6l-a61', 'owner_soak_rule_and_live_readback'
    receipt.update(item=item, step=step, request_id='OP-1')
    result.update(item=item)
    result['steps'][0].update(item=item, step=step, request_id='OP-1')
    if damage in ('evidence_sha256', 'request_id', 'operation_id'):
        receipt[damage] = '0'*64 if damage == 'evidence_sha256' else 'OTHER'
    elif damage == 'no_acceptance': events.write_text('')
    elif damage == 'soak_without_evidence_path':
        # Main-form (executor digest only) must not dodge the soak sample check by omitting evidence_path.
        del result['steps'][0]['evidence_path']
        receipt['evidence_sha256'] = result['steps'][0]['evidence_sha256'] = hashlib.sha256(
            (tmp_path / 'home/run/ops/receipts/OP-1.json').read_bytes()).hexdigest()
    elif damage == 'executor_receipt_not_at_ops': (tmp_path / 'home/run/ops/receipts/OP-1.json').unlink()
    path.write_text(canonical(receipt)); result_path.write_text(json.dumps(result))
    repo = Path(__file__).resolve().parents[5]
    model = json.loads((repo/'00_ARCHITECTURE/control/kalayantra/plan_model.json').read_text())
    row = next(row for row in model['items'] if row['id'] == item)
    spec = {'type': 'file_contains', 'path': str(path), 'pattern': 'MET'}
    row['step_evidence'][step]['detector'] = spec
    monkeypatch.setattr(cli, 'load_model', lambda: model)
    monkeypatch.setattr(cli, 'get', lambda *a, **k: ({'item': item, 'step': step, 'spec': spec,
                                                   'detector': {'status': 'done'}}, 'live'))
    before = events.read_bytes()
    code = cli.main(['step', item, step, '--as', 'steward', '--evidence', str(path)])
    assert code == (0 if damage == 'none' else 2)
    assert (events.read_bytes() == before) == (damage != 'none')
