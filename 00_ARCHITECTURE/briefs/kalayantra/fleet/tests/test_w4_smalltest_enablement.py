"""Wave 4 steps 10–16 admission: no git writes, cloud calls or DB connections."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

FLEET = Path(__file__).resolve().parents[1]
BASE_ENABLED = {"readback_sql", "migration_readback", "local_schema_seed", "finalize"}
W4 = {
    "backup_snapshot": ("owner", "platform/scripts/backup_v5_small_test_job.py", ["--operation", "snapshot", "--execute"], ["label"]),
    "backup_restore_verify": ("owner", "platform/scripts/backup_v5_small_test_job.py", ["--operation", "restore-verify", "--execute"], ["label"]),
    "smalltest_dispatch_dryrun": ("builder", "platform/scripts/dispatch_v5_small_test_job.py", ["--i-am-steward", "--after-settled-1", "--dry-run"], ["run", "classes", "horizon-start", "horizon-end"]),
    "smalltest_dispatch": ("builder", "00_ARCHITECTURE/briefs/kalayantra/fleet/smalltest_launch.py", [], ["run", "classes", "horizon-start", "horizon-end"]),
    "smalltest_teardown_dryrun": ("owner", "platform/scripts/teardown_v5_small_test_job.py", ["--dry-run"], []),
    "smalltest_teardown": ("owner", "platform/scripts/teardown_v5_small_test_job.py", ["--execute", "--i-am-steward"], []),
}
DISABLED = {"measuring_dispatch", "verification_job", "century_dispatch", "publish_head", "rollback_head",
            "orchestrator_rebuild_dryrun", "orchestrator_rebuild", "layer_verify", "layer_publish", "layer_rollback"}


@pytest.fixture
def table():
    return json.loads((FLEET / "executor_ops.json").read_text())["ops"]


@pytest.fixture
def executor(tmp_path, monkeypatch):
    monkeypatch.setenv("KY_ROOT", str(tmp_path))
    spec = importlib.util.spec_from_file_location("w4_executor", FLEET / "executor.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Only validate() runs. All external observations are injected; execution is forbidden.
    monkeypatch.setattr(mod, "lease_live", lambda _: True)
    monkeypatch.setattr(mod, "git", lambda *a, **kw: SimpleNamespace(returncode=0))
    monkeypatch.setattr(mod, "seen", lambda _: False)
    mod.ACC.mkdir(parents=True)
    return mod


def request(executor, kind, args=None):
    req = dict(operation_id="w4-proof", idempotency_key="w4-proof", item_id="J-2a", kind=kind,
               requested_by="adhikarin", kyd="PRE-D-TEARDOWN", chart_id=executor.CANONICAL_CHART,
               lease_id="fixture", reviewed_commit="a" * 40, args=args or {},
               expires_at=(dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=10)).isoformat())
    acceptance = executor.ACC / "w4-proof.json"
    req["acceptance_receipt"] = str(acceptance)
    acceptance.write_text(json.dumps(dict(result="ACCEPTED", by="v1", operation_id=req["operation_id"],
        reviewed_commit=req["reviewed_commit"], ts=executor.now(), request_sha256=executor.request_digest(req),
        rows={k: True for k in ["2", "3", "7", "9", "11"]},
        checks=dict(backup_taken=True, restore_verified=True, dry_run_passed=True))))
    return req


def caps():
    return {k: True for k in ["owner", "builder", "gcloud", "pgenv", "none"]}


def test_only_six_wave4_ops_are_newly_enabled(table):
    assert set(table) == BASE_ENABLED | set(W4) | DISABLED
    assert {k for k, op in table.items() if op["enabled"] is True} == BASE_ENABLED | set(W4)
    for kind in DISABLED:
        assert table[kind]["enabled"] is False
        if "prepared_dry_run" in table[kind]:
            assert table[kind]["prepared_dry_run"]["enabled"] is False


@pytest.mark.parametrize("kind", W4)
def test_exact_script_capability_and_argv(table, kind):
    op = table[kind]
    needs, script, fixed, allowed = W4[kind]
    assert op["enabled"] is True
    assert op["needs"] == needs
    assert op["script"] == script
    assert op["fixed_args"] == fixed
    assert op["allowed_args"] == allowed
    assert op["production"] is True and op["enabled_by"] == "J-1a"
    assert op.get("requesters", ["adhikarin"]) == ["adhikarin"]
    assert op.get("also_needs", []) == (["gcloud"] if kind == "smalltest_dispatch" else [])
    assert op["required_rows"] == ([] if kind.startswith("backup_") else ["2", "3", "7", "9", "11"])


@pytest.mark.parametrize("kind", list(W4) + ["readback_sql", "migration_readback"])
def test_real_validate_accepts_only_listed_arguments(table, executor, kind):
    args = {name: "fixture" for name in table[kind]["allowed_args"]}
    req = request(executor, kind, args)
    assert executor.validate(req, table, caps()) is None
    for name in ["execute", "run-id", "operation", "i-am-steward", "sql", "generation"]:
        req = request(executor, kind, {**args, name: "fixture"})
        assert executor.validate(req, table, caps()) == f"disallowed args ['{name}']"


@pytest.mark.parametrize("kind", W4)
def test_missing_each_required_capability_is_refused(table, executor, kind):
    req = request(executor, kind)
    for required in [table[kind]["needs"], *table[kind].get("also_needs", [])]:
        missing = {**caps(), required: False}
        assert executor.validate(req, table, missing) == f"capability_missing: {required}"


@pytest.mark.parametrize("kind", sorted(DISABLED))
def test_every_future_operation_stays_refused(table, executor, kind):
    assert "is not enabled" in executor.validate(request(executor, kind), table, caps())


def test_unknown_kind_stays_refused(table, executor):
    assert executor.validate(request(executor, "unlisted"), table, caps()) == "unknown kind unlisted"
