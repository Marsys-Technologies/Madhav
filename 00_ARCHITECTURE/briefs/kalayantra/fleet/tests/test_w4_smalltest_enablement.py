"""Wave 4 steps 10–16 admission: no git writes, cloud calls or DB connections."""
import json
from pathlib import Path

import pytest

from smalltest_admission_support import ARG_VALUES, approve, caps, load_executor, request

FLEET = Path(__file__).resolve().parents[1]
BASE_ENABLED = {"readback_sql", "migration_readback", "cloudrun_job_readback", "local_schema_seed", "finalize"}
# A7 D-44 (owner direction): the one read-only kind added after Wave 4; enabled by B-1, not a Wave 4 op, so it is named here rather than folded into W4.
D44_READ_ONLY = {"quiescence_check"}
SCHEDULER = {"scheduler_readback", "scheduler_pause_dryrun", "scheduler_pause", "scheduler_resume_dryrun", "scheduler_resume", "measuring_cancel_dryrun", "measuring_cancel"}   # SR-J3-REAPER-PAUSE + SR-J3-CANCEL-NULL (J-3c): exact bindings are pinned in test_executor_table / test_executor_scheduler_reaper
W4 = {
    "backup_snapshot": ("owner", "platform/scripts/backup_v5_small_test_job.py", ["--operation", "snapshot", "--execute"], ["label", "scope"]),
    "backup_restore_verify": ("owner", "platform/scripts/backup_v5_small_test_job.py", ["--operation", "restore-verify", "--execute"], ["label", "scope"]),
    "smalltest_dispatch_dryrun": ("builder", "platform/scripts/dispatch_v5_small_test_job.py", ["--i-am-steward", "--after-settled-1", "--dry-run"], ["run", "classes", "horizon-start", "horizon-end"]),
    "smalltest_dispatch": ("builder", "00_ARCHITECTURE/briefs/kalayantra/fleet/smalltest_launch.py", [], ["run", "classes", "horizon-start", "horizon-end"]),
    "smalltest_teardown_dryrun": ("owner", "platform/scripts/teardown_v5_small_test_job.py", ["--dry-run"], []),
    "smalltest_teardown": ("owner", "platform/scripts/teardown_v5_small_test_job.py", ["--execute", "--i-am-steward"], []),
}
# J-3a: the four measuring kinds, enabled with the bindings #3607 reviewed (PR #3615 was test pre-build only).
# kind: (needs, script, fixed_args, allowed_args, enabled_by); measuring takes only run and classes — the horizon is census-derived, not requested.
MEASURING = {
    "measuring_dispatch_dryrun": ("builder", "platform/scripts/dispatch_v5_measuring_job.py", ["--i-am-steward", "--after-settled-1", "--dry-run"], ["run", "classes"], "J-3c"),
    "measuring_dispatch": ("builder", "00_ARCHITECTURE/briefs/kalayantra/fleet/measuring_launch.py", [], ["run", "classes"], "J-3c"),
    "measuring_teardown_dryrun": ("owner", "platform/scripts/teardown_v5_small_test_job.py", ["--dry-run"], [], "J-3d"),
    "measuring_teardown": ("owner", "platform/scripts/teardown_v5_small_test_job.py", ["--execute", "--i-am-steward"], [], "J-3d"),
}
# SR-PREBUILD-ALL (enabled_by J-4d, request item J-4e): the century family. century_dispatch = the measuring launch without the test slice (builder: it stages the
# run; gcloud: it launches it). century_teardown (the REAL deletion) stays disabled until the owner's teardown authority is recorded (SR-TEARDOWN-AUTHORITY-GATE).
CENTURY = {
    "century_dispatch_dryrun": ("builder", "platform/scripts/dispatch_v5_century_job.py", ["--i-am-steward", "--after-settled-1", "--dry-run"], ["classes"], "J-4d"),
    "century_dispatch": ("builder", "00_ARCHITECTURE/briefs/kalayantra/fleet/century_launch.py", [], ["classes"], "J-4d"),
    "century_teardown_dryrun": ("owner", "platform/scripts/teardown_v5_small_test_job.py", ["--dry-run"], [], "J-4d"),
}
CENTURY_DISABLED = {"century_teardown": ("owner", "platform/scripts/teardown_v5_small_test_job.py", ["--execute", "--i-am-steward"], [], "J-4d")}
DISABLED = {"verification_job", "publish_head", "rollback_head", *CENTURY_DISABLED,
            "publish_head_dryrun", "rollback_head_dryrun",
            "gochara_role_provisioning_dispatch", "gochara_role_provisioning_dispatch_dryrun",      # U-M-03: shipped disabled
            "orchestrator_rebuild_dryrun", "orchestrator_rebuild", "layer_verify", "layer_publish", "layer_rollback",
            "github_run_readback",   # U-M-12: prepared for W3/W4, shipped disabled; exact binding pinned in test_executor_table
            "protected_window_dispatch_dryrun", "protected_window_dispatch"}   # U-M-01: shipped disabled


@pytest.fixture
def table():
    return json.loads((FLEET / "executor_ops.json").read_text())["ops"]


@pytest.fixture
def executor(tmp_path, monkeypatch):
    return load_executor(tmp_path, monkeypatch)


def test_only_six_wave4_measuring_scheduler_and_century_ops_are_newly_enabled(table):
    assert set(table) == BASE_ENABLED | D44_READ_ONLY | set(W4) | set(MEASURING) | SCHEDULER | set(CENTURY) | DISABLED
    assert {k for k, op in table.items() if op["enabled"] is True} == BASE_ENABLED | D44_READ_ONLY | set(W4) | set(MEASURING) | SCHEDULER | set(CENTURY)
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
    assert op["production"] is (not kind.endswith("_dryrun")) and op["enabled_by"] == "J-1a"   # A8 §3.8: a dry run is read-only with a credential
    assert op.get("requesters", ["adhikarin"]) == ["adhikarin"]
    assert op.get("also_needs", []) == (["gcloud"] if kind == "smalltest_dispatch" else [])
    assert "required_rows" not in op                                                           # A8 §5: retired
    assert op.get("remote_async", False) is (kind == "smalltest_dispatch")                      # A8 §3.11: only the remote launch takes the fence


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
    ('smalltest_teardown', 'dryrun_receipt'),      # A8 §3.8: a dry run has no acceptance, so its receipt is the whole evidence
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


# ───────────── J-3a: the four measuring kinds ─────────────
@pytest.mark.parametrize("kind", MEASURING)
def test_measuring_exact_script_capability_and_argv(table, kind):
    op = table[kind]
    needs, script, fixed, allowed, item = MEASURING[kind]
    assert op["enabled"] is True and next(iter(op)) == "enabled"
    assert op["needs"] == needs and op["script"] == script and (FLEET.parents[3] / script).is_file()   # never TO_BE_SET
    assert op["fixed_args"] == fixed and op["allowed_args"] == allowed and op["enabled_by"] == item
    assert op["production"] is (not kind.endswith("_dryrun"))                                           # A8 §3.8: a dry run is read-only with a credential
    assert op.get("requesters", ["adhikarin"]) == ["adhikarin"]
    assert op.get("also_needs", []) == (["gcloud"] if kind == "measuring_dispatch" else [])
    assert "required_rows" not in op                                                                     # A8 §5: retired
    assert op.get("remote_async", False) is (kind == "measuring_dispatch")                              # A8 §3.11: only the remote launch takes the fence


@pytest.mark.parametrize("kind", MEASURING)
def test_measuring_missing_each_required_capability_is_refused(table, executor, kind):
    req = request(executor, kind)
    for required in [table[kind]["needs"], *table[kind].get("also_needs", [])]:
        assert executor.validate(req, table, {**caps(), required: False}) == f"capability_missing: {required}"


@pytest.mark.parametrize("kind", MEASURING)
def test_measuring_validate_refuses_unlisted_arguments_and_the_smalltest_horizon(table, executor, kind):
    for name in ["execute", "run-id", "operation", "i-am-steward", "sql", "generation", "horizon-start", "horizon-end"]:
        req = request(executor, kind, {name: "fixture"})
        assert executor.validate(req, table, caps()) == f"disallowed args ['{name}']"


@pytest.mark.parametrize("kind", MEASURING)
def test_measuring_requests_reach_the_reviewed_measuring_policy_not_the_enablement_refusal(table, executor, kind):
    # the fixture's item is J-2a; the real measuring policy (loaded from the reviewed commit) must be what answers
    args = {"run": "all_classes_full", "classes": "all"} if "dispatch" in kind else {}
    why = executor.validate(request(executor, kind, args), table, caps())
    assert why is not None and "not enabled" not in why
    if "dispatch" in kind:
        assert why == "measuring dispatch belongs to J-3c"


# ───────────── SR-PREBUILD-ALL: the century family (item J-4e, enabled_by J-4d) ─────────────
@pytest.mark.parametrize("kind", [*CENTURY, *CENTURY_DISABLED])
def test_century_exact_script_capability_and_argv(table, kind):
    op = table[kind]
    needs, script, fixed, allowed, item = {**CENTURY, **CENTURY_DISABLED}[kind]
    assert op["enabled"] is (kind in CENTURY) and next(iter(op)) == "enabled"
    assert op["needs"] == needs and op["script"] == script and (FLEET.parents[3] / script).is_file()       # never TO_BE_SET
    assert op["fixed_args"] == fixed and op["allowed_args"] == allowed and op["enabled_by"] == item
    assert op["production"] is (not kind.endswith("_dryrun"))                                              # A8 §3.8 / SR-TEARDOWN-AUTHORITY-GATE 2: every dryrun sibling is production:false
    assert op.get("requesters", ["adhikarin"]) == ["adhikarin"]
    assert op.get("also_needs", []) == (["gcloud"] if kind == "century_dispatch" else [])
    assert "required_rows" not in op and "timeout_s" not in op
    assert op.get("remote_async", False) is (kind == "century_dispatch")                                  # A8 §3.11: only the remote launch takes the fence


@pytest.mark.parametrize("kind", ["century_dispatch", "century_dispatch_dryrun", "century_teardown_dryrun"])
def test_century_missing_each_required_capability_is_refused(table, executor, kind):
    req = request(executor, kind)
    for required in [table[kind]["needs"], *table[kind].get("also_needs", [])]:
        assert executor.validate(req, table, {**caps(), required: False}) == f"capability_missing: {required}"


@pytest.mark.parametrize("kind", ["century_dispatch", "century_dispatch_dryrun"])
def test_century_validate_refuses_unlisted_arguments_run_names_and_any_horizon(table, executor, kind):
    # the century takes only `classes`: no run name (it is not a slice) and no horizon (the writer decides it, N-G9)
    for name in ["execute", "run", "run-id", "operation", "i-am-steward", "sql", "generation", "horizon-start", "horizon-end"]:
        assert executor.validate(request(executor, kind, {name: "fixture"}), table, caps()) == f"disallowed args ['{name}']"


@pytest.mark.parametrize("kind", ["century_dispatch", "century_dispatch_dryrun", "century_teardown_dryrun"])
def test_century_requests_reach_the_reviewed_century_policy_not_the_enablement_refusal(table, executor, kind):
    # the fixture's item is J-2a; the real century policy (loaded from the reviewed commit) must be what answers
    args = {"classes": "all"} if "dispatch" in kind else {}
    why = executor.validate(request(executor, kind, args), table, caps())
    assert why == ("century dispatch belongs to J-4e" if "dispatch" in kind else "century teardown belongs to J-4e")


def test_century_teardown_stays_disabled_until_the_owner_authority_is_recorded(table, executor):
    assert executor.validate(request(executor, "century_teardown"), table, caps()).startswith("kind century_teardown is not enabled")
