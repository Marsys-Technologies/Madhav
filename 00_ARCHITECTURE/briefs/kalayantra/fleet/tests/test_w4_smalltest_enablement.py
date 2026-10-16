"""Wave 4 steps 10–16 admission: no git writes, cloud calls or DB connections."""
import json
from pathlib import Path

import pytest

from smalltest_admission_support import ARG_VALUES, approve, caps, load_executor, request

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
DISABLED = {"publish_head_dryrun", "rollback_head_dryrun", "measuring_dispatch", "verification_job", "century_dispatch", "publish_head", "rollback_head",
            "measuring_dispatch_dryrun", "measuring_teardown", "measuring_teardown_dryrun",
            "orchestrator_rebuild_dryrun", "orchestrator_rebuild", "layer_verify", "layer_publish", "layer_rollback"}


@pytest.fixture
def table():
    return json.loads((FLEET / "executor_ops.json").read_text())["ops"]


@pytest.fixture
def executor(tmp_path, monkeypatch):
    return load_executor(tmp_path, monkeypatch)


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
    args = {name: ARG_VALUES[name] for name in table[kind]["allowed_args"]}
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


@pytest.mark.parametrize('kind,field', [
    ('smalltest_teardown_dryrun', 'smalltest_scope'),
    ('smalltest_teardown', 'dryrun_receipt'),
    ('smalltest_teardown', 'dryrun_acceptance'),
    ('smalltest_dispatch', 'absence_receipt'),
    ('smalltest_dispatch', 'absence_acceptance'),
])
def test_valid_authorization_cannot_replace_required_evidence(table, executor, kind, field):
    args = {key: ARG_VALUES[key] for key in table[kind]['allowed_args']}
    req = request(executor, kind, args)
    assert executor.validate(req, table, caps()) is None
    del req[field]
    approve(executor, req)  # Keep complete-request approval valid; exercise the evidence detector.
    assert executor.validate(req, table, caps()) == (
        'identified staged small-test scope required' if field == 'smalltest_scope'
        else 'named evidence reference required')


@pytest.mark.parametrize('kind,field', [
    ('smalltest_teardown', 'dryrun_receipt'),
    ('smalltest_dispatch', 'absence_receipt'),
])
def test_changed_evidence_bytes_refuse_even_with_valid_request_approval(table, executor, kind, field):
    req = request(executor, kind, {key: ARG_VALUES[key] for key in table[kind]['allowed_args']})
    assert executor.validate(req, table, caps()) is None
    path = executor.REC / req[field]['name']
    path.write_text(path.read_text() + '\n')
    assert executor.validate(req, table, caps()) == 'evidence byte digest mismatch'
