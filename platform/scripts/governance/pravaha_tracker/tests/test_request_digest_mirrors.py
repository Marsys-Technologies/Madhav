"""A8 §3.9 / §5: every mirror of executor.request_digest agrees on one fixture request.

The rule (fleet/executor.py:request_digest): the request as sorted compact JSON without `acceptance_receipt`, `expires_at` and any
`*_expires_at` field. Its mirrors — the signer (kyd_kinds_ops), the children (v5_small_test_shared) and the tracker's operation-step
check (cli) and audit — must produce the same digest, or a lease renewal reads as an unbound production operation.
"""
import datetime as dt
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

from pravaha_tracker import audit as audit_module
from pravaha_tracker import cli
from pravaha_tracker.tests.test_step_receipt_binding import canonical, operation_step  # noqa: F401  (the real fixture)

REPO = Path(cli.REPO_ROOT)
FLEET = REPO / "00_ARCHITECTURE/briefs/kalayantra/fleet"
CHART = "482012f1-710e-4a25-994a-93821f5871aa"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fixture_request(**over):
    req = {"operation_id": "op-mirror", "kind": "smalltest_teardown", "item_id": "J-1a", "idempotency_key": "k", "requested_by": "adhikarin",
           "kyd": "k", "args": {}, "chart_id": CHART, "lease_id": "lease-1", "reviewed_commit": "a" * 40,
           "expires_at": "2026-10-19T00:00:00+00:00", "lease_expires_at": "2026-10-19T06:00:00+00:00",
           "acceptance_receipt": "/run/ops/acceptance/op-mirror.json"}
    req.update(over)
    return req


def _unbound(request, digest, tmp):
    root = Path(tmp)
    (root / "ops/requests").mkdir(parents=True)
    (root / "ops/acceptance").mkdir(parents=True)
    (root / "ops/requests/op-mirror.json").write_text(json.dumps(request))
    (root / "ops/acceptance/op-mirror.json").write_text(json.dumps(
        {"operation_id": "op-mirror", "result": "ACCEPTED", "by": "v1", "reviewed_commit": request["reviewed_commit"], "request_sha256": digest}))
    now = dt.datetime(2026, 10, 18, tzinfo=dt.timezone.utc)
    findings = audit_module.audit({"items": []}, [], root, since=now - dt.timedelta(minutes=10), now=now)
    return any(f["code"] == "unbound_production_operation" for f in findings)


def test_every_mirror_of_the_request_digest_agrees_on_one_fixture_request(operation_step, tmp_path):
    w = operation_step
    executor = _load("mirrors_executor", FLEET / "executor.py")
    signer = _load("mirrors_kyd_kinds_ops", FLEET / "kyd_kinds_ops.py")
    children = _load("mirrors_v5_small_test_shared", REPO / "platform/scripts/v5_small_test_shared.py")

    req = _fixture_request()
    digest = executor.request_digest(req)
    assert signer.request_digest(req) == children.request_hash(req) == digest

    # audit: the acceptance binds the executor's digest of a request that carries clocks and an acceptance_receipt
    with tempfile.TemporaryDirectory(dir=tmp_path) as bound_dir, tempfile.TemporaryDirectory(dir=tmp_path) as changed_dir:
        assert not _unbound(req, digest, bound_dir), "audit read a clock-bearing request as unbound"
        # the detector can read false: a bound field changed after the signature is flagged
        assert _unbound(_fixture_request(args={"x": "y"}), digest, changed_dir)

    # cli._check_operation_step: the executor receipt carries the executor's digest of the archived request
    w.req.update(acceptance_receipt="/run/ops/acceptance/op-mirror.json", expires_at="2026-10-19T00:00:00+00:00",
                 lease_expires_at="2026-10-19T06:00:00+00:00")
    w.request_path.write_text(json.dumps(w.req))
    w.executor["request_sha256"] = executor.request_digest(w.req)
    w.sync()
    w.run(expected=0)
    # ... and reads false when a bound field of the archived request changes after the receipt
    w.req["kyd"] = "changed-after-receipt"
    w.request_path.write_text(json.dumps(w.req))
    w.run(expected=2)
