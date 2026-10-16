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
