"""B-7p: the initial builder pool stays closed until reviewed launch evidence holds."""

from io import BytesIO
import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "release_pool.py"
spec = importlib.util.spec_from_file_location("release_pool", SOURCE)
pool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pool)


@pytest.fixture
def ready(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "KY_WORKERS").write_text("0\n")
    (run / "KY_VERIFIERS").write_text("2\n")
    (run / "TRACKER_INSTALL_RECEIPT.json").write_text(json.dumps({"accepted": True, "audit_available": True}))
    camp = tmp_path / "wt/campaign"
    camp.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(camp)], check=True)
    for source in pool.SOURCES.values():
        path = camp / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
    subprocess.run(["git", "-C", str(camp), "add", "."], check=True)
    subprocess.run(["git", "-C", str(camp), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"], check=True)
    head = subprocess.check_output(["git", "-C", str(camp), "rev-parse", "HEAD"], text=True).strip()
    receipt = {"mode": "launch", "checks": ["ok:tracker", "warn:optional"], "campaign_head": head}
    receipt.update({key: pool.digest(camp / path) for key, path in pool.SOURCES.items()})
    receipt_path = run / "LAUNCH_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt))
    (run / "LAUNCH_ACCEPTED.json").write_text(json.dumps({"result": "ACCEPTED", "by": "v1", "launch_receipt_sha256": pool.digest(receipt_path)}))
    state = {"tracks": [{"items": [{"id": item, "status": "done"} for item in pool.BOOTSTRAP]}]}
    return tmp_path, state


def check(ready, **kwargs):
    root, state = ready
    return pool.validate(root, state, audit_ok=kwargs.get("audit_ok", True), verifier_held=kwargs.get("verifier_held", {"v1": True, "v2": True}))


def test_release_conditions_accept_only_complete_evidence(ready):
    check(ready)


def test_release_writes_exactly_four_and_is_idempotent(ready, monkeypatch):
    root, state = ready
    binary = root / "bin/ky"
    binary.parent.mkdir()
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)
    monkeypatch.setattr(pool, "urlopen", lambda *_args, **_kwargs: BytesIO(json.dumps(state).encode()))
    monkeypatch.setattr(pool, "lane_lock_held", lambda *_args: True)
    pool.release(root)
    assert (root / "run/KY_WORKERS").read_text() == "4\n"
    pool.release(root)
    assert (root / "run/KY_WORKERS").read_text() == "4\n"


@pytest.mark.parametrize("failure", ["HOLD", "STOP_sutradhara", "STOP_v1", "STOP_v2", "verifier_count", "verifier_lane", "audit", "missing_B7", "missing_B7p", "install", "stale_receipt", "stale_verdict", "rejected_verdict", "backoff"])
def test_each_failed_gate_refuses_release(ready, failure):
    root, state = ready
    run = root / "run"
    kwargs = {}
    if failure == "HOLD":
        (root / "HOLD").touch()
    elif failure.startswith("STOP_"):
        (run / failure).touch()
    elif failure == "verifier_count":
        (run / "KY_VERIFIERS").write_text("1")
    elif failure == "verifier_lane":
        kwargs["verifier_held"] = {"v1": True, "v2": False}
    elif failure == "audit":
        kwargs["audit_ok"] = False
    elif failure in ("missing_B7", "missing_B7p"):
        target = "B-7" if failure == "missing_B7" else "B-7p"
        next(item for item in state["tracks"][0]["items"] if item["id"] == target)["status"] = "ready"
    elif failure == "install":
        (run / "TRACKER_INSTALL_RECEIPT.json").write_text(json.dumps({"accepted": True, "audit_available": False}))
    elif failure == "stale_receipt":
        (root / "wt/campaign" / pool.SOURCES["model_sha256"]).write_text("changed")
    elif failure in ("stale_verdict", "rejected_verdict"):
        verdict = json.loads((run / "LAUNCH_ACCEPTED.json").read_text())
        verdict["result" if failure == "rejected_verdict" else "launch_receipt_sha256"] = "REJECTED" if failure == "rejected_verdict" else "0" * 64
        (run / "LAUNCH_ACCEPTED.json").write_text(json.dumps(verdict))
    elif failure == "backoff":
        (run / "KY_QUOTA_BACKOFF").write_text("9999999999")
    with pytest.raises(pool.Refused):
        check(ready, **kwargs)
    assert (run / "KY_WORKERS").read_text().strip() == "0"


def test_missing_bootstrap_guard_mutation_is_killed(ready):
    root, state = ready
    next(item for item in state["tracks"][0]["items"] if item["id"] == "B-7")["status"] = "ready"
    with pytest.raises(pool.Refused):
        check(ready)
    # The oracle must fail if the guarded-done check is removed.
    source = SOURCE.read_text().replace("if missing:\n        raise Refused", "if False:\n        raise Refused", 1)
    assert source != SOURCE.read_text()
    namespace = {"__name__": "release_pool_mutant"}
    exec(compile(source, str(SOURCE), "exec"), namespace)
    namespace["validate"](root, state, audit_ok=True, verifier_held={"v1": True, "v2": True})
