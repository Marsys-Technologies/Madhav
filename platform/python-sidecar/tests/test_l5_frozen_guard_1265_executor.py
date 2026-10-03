"""1265 owner-path EXECUTOR route on the MIRRORED roles (the part that is not a migration): who executes (the administrator `adm`: CREATEROLE, not a
superuser, no table privilege, no USAGE on schema public), the transient memberships and the transient schema CREATE capability, plan hash,
dry run, apply with the evidence digest, the rollback leg, outcome files, the interpreter binding (exit 92) and the GATE_V2 launch refusal (exit 93).

Needs PostgreSQL <= 15 for the executor-route tests (PostgreSQL 16+ would need ADMIN OPTION for the transient GRANT; production is 15.18).
The administrator password / Secret Manager / the real database are never reached: `connect` is injected (execute) or connect_admin is replaced (main).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import stat

import pytest

from tests.l5_frozen_guard_world import (CHART_A, CHART_B, COMMIT, FORWARD, PKG, REPO, ROLLBACK, add_chart_fks, body, drop_world, load_exec,
                                         make_world, pg_cluster)  # noqa: F401

EX = load_exec("l5_frozen_guard_exec_route")
ES = EX.standards()
GATE_FP = dict(ES.fingerprint(str(EX.gate_dir())), under_test=True)
CLEAN_SOURCE = "x = 1\n# no delete here\n"


@pytest.fixture(autouse=True)
def _only_pg15(pg_cluster):
    if pg_cluster["major"] >= 16:
        pytest.skip("the executor-route tests mirror production (PostgreSQL 15: CREATEROLE may grant a role); on 16+ the transient GRANT needs ADMIN OPTION")


@pytest.fixture()
def world(pg_cluster):
    w = make_world(pg_cluster)
    yield w
    drop_world(pg_cluster, w)


@pytest.fixture()
def evid(tmp_path, monkeypatch):
    root = tmp_path / "evidence"
    monkeypatch.setenv(EX.TEST_EVIDENCE_ENV, str(root))
    return root


def ok_runner(argv):
    if argv[0] == "gcloud":
        return "asia-south1-docker.pkg.dev/madhav-astrology/x/pipeline:" + COMMIT
    if argv[0] == "git":
        return CLEAN_SOURCE
    raise AssertionError(argv)


def bad_image_runner(argv):
    if argv[0] == "gcloud":
        return "asia-south1-docker.pkg.dev/madhav-astrology/x/pipeline:" + "f" * 40
    return CLEAN_SOURCE


def deleting_writer_runner(argv):
    if argv[0] == "git" and argv[-1].endswith("mi_bhavisya.py"):
        return 'cur.execute("DELETE FROM mimamsa_predictions WHERE chart_id = %s AND lifecycle_status IN (\'pending\')")\n'
    return ok_runner(argv)


def failing_runner(argv):
    raise RuntimeError("git show failed")


def run(world, mode, *, expect_plan=None, expect_evidence=None, writer_commit=COMMIT, admin="adm", runner=ok_runner, evidence_root=None, expected_db=None, gate_fp=None):
    args = argparse.Namespace(mode=mode, expect_plan=expect_plan if expect_plan is not None else EX.plan_hash(), expect_evidence=expect_evidence,
                              writer_commit=writer_commit, evidence_root=evidence_root)

    def connect():
        return world.connect(admin)
    try:
        return EX.execute(args, connect, gate_fp=gate_fp or GATE_FP, writer_runner=runner, expected_db=expected_db or world.name)
    except SystemExit as e:
        return ("exit", e.code)


def outcome_of(result):
    return json.loads(pathlib.Path(result["outcome_file"]).read_text())


def latest_outcome(evid, mode_prefix):
    d = sorted(p for p in evid.iterdir() if p.name.startswith(mode_prefix))[-1]
    return json.loads((d / "outcome.json").read_text()), d


def never_connect():
    raise AssertionError("the administrator credential must not be fetched")


# ================================================================ who executes, what it grants, what it leaves behind

def test_the_administrator_is_a_createrole_non_superuser_without_table_privileges_or_usage_on_public(world):
    assert world.query("SELECT rolsuper, rolcreaterole, rolcanlogin FROM pg_roles WHERE rolname = 'adm'") == [(False, True, True)]
    with world.connect("adm") as c:
        assert c.execute("SELECT has_schema_privilege('adm','public','USAGE'), has_schema_privilege('adm','public','CREATE'), "
                         "(SELECT has_table_privilege('adm', c.oid, 'SELECT') FROM pg_class c WHERE c.relname = 'mimamsa_predictions')").fetchone() == (False, False, False)
        assert c.execute("SELECT pg_has_role('adm','data_plane_schema_owner','MEMBER'), pg_has_role('adm','amjis_app','MEMBER')").fetchone() == (False, False)
        with pytest.raises(world.pg["psycopg"].errors.InsufficientPrivilege, match="permission denied for schema public"):
            c.execute("SELECT 'public.mimamsa_predictions'::regclass")      # why the executor reads those objects as amjis_app


def test_count_mode_is_read_only_and_reports_the_preconditions(world, evid):
    before = world.catalog_state()
    code, result = run(world, "count")
    assert code == 0 and result["status"] == "COUNT_READ_ONLY_OK" and result["failed_checks"] == []
    assert world.catalog_state() == before


def test_dry_run_prints_the_exact_diff_changes_nothing_and_records_the_outcome(world, evid):
    before = world.catalog_state()
    code, result = run(world, "dry-run")
    assert code == 0 and result["status"] == "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD" and result["failed_checks"] == []
    assert world.catalog_state() == before and world.schema_acl() == world.baseline_acl
    assert world.query("SELECT r.rolname FROM pg_auth_members am JOIN pg_roles m ON m.oid = am.member JOIN pg_roles r ON r.oid = am.roleid WHERE m.rolname = 'adm'") == [("pg_read_all_stats",)]
    log = "\n".join(result["log"])
    assert "6 added" in log and "8 added" in log and "IDENTICAL" in log and "equals the pre-state" in log and "commit conditions: ALL HOLD" in log
    out = outcome_of(result)
    assert out["status"] == "dry_run" and out["plan_hash"] == EX.plan_hash() and out["evidence_digest"] == result["evidence_digest"]
    for k in EX.RUNTIME_KEYS:
        assert out[k]
    assert out["python_executable"] == __import__("sys").executable and out["under_test"] is True
    d = pathlib.Path(result["evidence_dir"])
    assert stat.S_IMODE(d.stat().st_mode) == 0o700
    for n in ("outcome.json", "report.txt", "result.json", "before_state.json"):
        assert stat.S_IMODE((d / n).stat().st_mode) == 0o600, n


def test_apply_commits_only_with_the_dry_runs_evidence_digest_and_leaves_the_exact_planned_state(world, evid):
    pre = world.catalog_state()
    _, dry = run(world, "dry-run")
    code, res = run(world, "apply", expect_evidence=dry["evidence_digest"])
    assert code == 0 and res["status"] == "COMMITTED", res.get("failed_checks")
    post = world.catalog_state()
    assert post != pre
    # exactly the planned objects were added: 6 functions, 8 triggers; everything else, the schema ACL and the memberships are as before
    assert {r[0].split("(")[0] for r in set(map(tuple, post["function"])) - set(map(tuple, pre["function"]))} == {s.split("(")[0] for s in EX.NEW_FUNCTIONS}
    assert len(set(map(tuple, post["trigger"])) - set(map(tuple, pre["trigger"]))) == 8 and not set(map(tuple, pre["trigger"])) - set(map(tuple, post["trigger"]))
    for k in ("table", "policy", "constraint", "index", "schema_acl", "membership", "rowdata", "event_triggers"):
        assert post[k] == pre[k], k
    assert world.schema_acl() == world.baseline_acl
    assert world.query("SELECT has_schema_privilege('amjis_app','public','CREATE')") == [(False,)]
    out = outcome_of(res)
    assert out["status"] == "applied" and out["evidence_digest"] == dry["evidence_digest"]
    # and the guards are live
    psy = world.pg["psycopg"]
    with world.connect("amjis_app") as c:
        with pytest.raises(psy.errors.InsufficientPrivilege, match="mimamsa_predictions_frozen_row_guard"):
            c.execute("DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_A,))


def test_apply_with_a_wrong_evidence_digest_is_refused_rolled_back_and_recorded_failed(world, evid):
    pre = world.catalog_state()
    code, res = run(world, "apply", expect_evidence="0" * 64)
    assert code == 1 and res["status"] == "REFUSED_ROLLED_BACK" and "evidence_digest_matches_expected" in res["failed_checks"]
    assert world.catalog_state() == pre
    out = outcome_of(res)
    assert out["status"] == "failed" and out["failed_checks"] == ["evidence_digest_matches_expected"]


def test_the_evidence_digest_changes_when_the_pre_state_changes(world, evid):
    _, a = run(world, "dry-run")
    world.exec("INSERT INTO mimamsa_manifestation_sets VALUES (%s, 'pred_extra', 'ch', 'career', 'phala_anchors', '{}', true, now())", (CHART_B,))
    _, b = run(world, "dry-run")
    assert a["evidence_digest"] != b["evidence_digest"]


def test_a_wrong_plan_hash_refuses_before_any_connection_and_the_outcome_says_so(world, evid):
    args = argparse.Namespace(mode="dry-run", expect_plan="0" * 64, expect_evidence=None, writer_commit=None, evidence_root=None)
    with pytest.raises(SystemExit):
        EX.execute(args, never_connect, gate_fp=GATE_FP, expected_db=world.name)
    out, _ = latest_outcome(evid, "dry-run")
    assert out["status"] == "failed" and out["failed_checks"] == ["args_expect_plan_mismatch"]


def test_apply_without_evidence_or_without_a_writer_commit_is_refused_before_any_connection(world, evid):
    for kw, check in (({"expect_evidence": None}, "args_expect_evidence_missing"), ({"expect_evidence": "a" * 64, "writer_commit": None}, "args_writer_commit_missing")):
        args = argparse.Namespace(mode="apply", expect_plan=EX.plan_hash(), evidence_root=None, **{"expect_evidence": None, "writer_commit": COMMIT, **kw})
        with pytest.raises(SystemExit):
            EX.execute(args, never_connect, gate_fp=GATE_FP, expected_db=world.name)
        assert latest_outcome(evid, "apply")[0]["failed_checks"] == [check]


def test_a_hand_edited_sql_script_is_refused_before_any_connection(world, evid, monkeypatch, tmp_path):
    edited = tmp_path / "edited.sql"
    edited.write_text(FORWARD.read_text(encoding="utf8").replace(body(FORWARD.read_text(encoding="utf8"), "predictions"), body(FORWARD.read_text(encoding="utf8"), "predictions") + " "), encoding="utf8")
    monkeypatch.setattr(EX, "FORWARD_SQL", edited)
    args = argparse.Namespace(mode="dry-run", expect_plan=EX.plan_hash(), expect_evidence=None, writer_commit=None, evidence_root=None)
    with pytest.raises(SystemExit):
        EX.execute(args, never_connect, gate_fp=GATE_FP, expected_db=world.name)
    assert latest_outcome(evid, "dry-run")[0]["failed_checks"] == ["expected_diff_mismatch"]


# ================================================================ writer-first (ORDER)

def test_writer_first_image_tag_must_equal_the_commit(world, evid):
    pre = world.catalog_state()
    code, res = run(world, "dry-run", runner=bad_image_runner)
    assert code == 2 and "pre_writer_first" in res["failed_checks"] and "runs image tag" in res["details"]["pre_writer_first"]
    assert world.catalog_state() == pre


def test_writer_first_the_writer_source_at_the_commit_must_not_delete_frozen_rows(world, evid):
    code, res = run(world, "dry-run", runner=deleting_writer_runner)
    assert code == 2 and "still deletes" in res["details"]["pre_writer_first"]


def test_writer_first_unverifiable_and_short_commit_fail_closed(world, evid):
    code, res = run(world, "dry-run", runner=failing_runner)
    assert code == 2 and "pre_writer_first" in res["failed_checks"]
    code, res = run(world, "dry-run", writer_commit="abc123")
    assert code == 2 and "40-hex" in res["details"]["pre_writer_first"]
    code, res = run(world, "apply", writer_commit=COMMIT, expect_evidence="1" * 64, runner=bad_image_runner)
    assert code == 1 and "pre_writer_first" in res["failed_checks"]


def test_writer_check_comment_lines_and_other_tables_do_not_trip_it(world):
    problems, line = EX.writer_check(COMMIT, lambda argv: "tag:" + COMMIT if argv[0] == "gcloud" else '# DELETE FROM mimamsa_predictions (old)\ncur.execute("DELETE FROM phala_anchors WHERE chart_id = %s")\n')
    assert problems == [] and "do not delete" in line


# ================================================================ preconditions: every refusal changes nothing

def test_refused_when_a_build_is_in_flight(world, evid):
    world.exec("INSERT INTO build_runs (id, chart_id, state) VALUES (%s, %s, 'running')", (RUN := "aaaaaaaa-0000-4000-8000-0000000000f1", CHART_A))
    pre = world.catalog_state()
    code, res = run(world, "dry-run")
    assert code == 2 and "pre_no_build_in_flight" in res["failed_checks"] and world.catalog_state() == pre


def test_refused_when_a_builder_session_is_active_or_idle_in_transaction(world, evid):
    held = world.connect("data_plane_builder")
    held.execute("SELECT 1")                                   # opens a transaction and stays idle in it
    try:
        code, res = run(world, "dry-run")
        assert code == 2 and "pre_no_builder_session" in res["failed_checks"]
    finally:
        held.rollback()
        held.close()


def test_an_administrator_who_cannot_see_session_states_is_warned_and_build_runs_alone_guards(world, evid):
    held = world.connect("data_plane_builder")
    held.execute("SELECT 1")
    try:
        code, res = run(world, "dry-run", admin="adm_blind")
        assert code == 0 and any("hidden state (no pg_read_all_stats)" in line for line in res["log"])
    finally:
        held.rollback()
        held.close()


def test_refused_when_the_schema_capability_window_is_already_open(world, evid):
    world.window("grant")
    try:
        code, res = run(world, "dry-run")
        assert code == 2 and "pre_app_owner_has_usage_and_no_create_on_public" in res["failed_checks"]
    finally:
        world.window("revoke")


def test_refused_when_the_captured_builder_guard_is_not_live_as_captured(world, evid):
    world.exec("ALTER FUNCTION public.mimamsa_predictions_builder_guard() SECURITY DEFINER", role="amjis_app")
    code, res = run(world, "dry-run")
    assert code == 2 and "pre_captured_builder_guard_is_live_as_captured" in res["failed_checks"]


def test_refused_when_a_recorded_builder_grant_is_absent_and_the_sql_raises_even_if_the_executor_check_is_bypassed(world, evid, monkeypatch):
    world.exec("REVOKE DELETE ON mimamsa_manifestation_sets FROM data_plane_builder", role="amjis_app")
    pre = world.catalog_state()
    code, res = run(world, "dry-run")
    assert code == 2 and "pre_recorded_builder_grant_mimamsa_manifestation_sets" in res["failed_checks"] and world.catalog_state() == pre
    monkeypatch.setattr(EX, "preconditions", lambda cur, leg, ck, out, expected_db: None)         # the SQL's own assertion is the second, independent line
    code, res = run(world, "dry-run")
    assert code == 2 and any(c.startswith("sql_raised_RaiseException") for c in res["failed_checks"])
    assert "does not create it" in json.dumps(res["details"]) and world.catalog_state() == pre


def test_refused_when_the_repo_objects_it_builds_beside_are_not_the_repos(world, evid):
    world.window("grant")
    try:
        world.exec("CREATE OR REPLACE FUNCTION public.bmpl_freeze_confirmed() RETURNS trigger LANGUAGE plpgsql AS $x$ BEGIN RETURN NEW; END $x$", role="amjis_app")
    finally:
        world.window("revoke")
    code, res = run(world, "dry-run")
    assert code == 2 and "pre_repo_function_bmpl_freeze_confirmed" in res["failed_checks"]


def test_refused_on_another_database_than_the_expected_one(world, evid):
    code, res = run(world, "dry-run", expected_db="amjis")
    assert code == 2 and "pre_database_is_the_expected_one" in res["failed_checks"]


def test_refused_when_the_administrator_cannot_assume_the_owner_roles_and_nothing_changes(world, evid):
    pre = world.catalog_state()
    code, res = run(world, "dry-run", admin="adm_nocr")
    assert code == 2 and res["failed_checks"] == ["pre_admin_can_assume_the_owner_roles"]
    assert world.catalog_state() == pre


def test_apply_is_single_shot_a_second_run_is_refused_until_the_rollback(world, evid):
    _, dry = run(world, "dry-run")
    code, res = run(world, "apply", expect_evidence=dry["evidence_digest"])
    assert code == 0
    code, res = run(world, "dry-run")
    assert code == 2 and "pre_none_of_the_new_objects_exists" in res["failed_checks"]


def test_a_sql_failure_inside_the_transaction_rolls_everything_back(world, evid, monkeypatch, tmp_path):
    mutated = tmp_path / "raises.sql"
    mutated.write_text(FORWARD.read_text(encoding="utf8").replace("  IF bad <> 11 THEN", "  IF bad <> 12 THEN"), encoding="utf8")
    monkeypatch.setattr(EX, "FORWARD_SQL", mutated)
    pre = world.catalog_state()
    code, res = run(world, "dry-run")
    assert code == 2 and any(c.startswith("sql_raised_RaiseException") for c in res["failed_checks"]) and "post-check" in json.dumps(res["details"])
    assert world.catalog_state() == pre and world.schema_acl() == world.baseline_acl
    assert world.query("SELECT r.rolname FROM pg_auth_members am JOIN pg_roles m ON m.oid = am.member JOIN pg_roles r ON r.oid = am.roleid WHERE m.rolname = 'adm'") == [("pg_read_all_stats",)]


def test_a_lock_held_by_another_session_makes_the_plan_fail_clean_and_fast(world, evid):
    pre = world.catalog_state()
    holder = world.connect("amjis_app")
    holder.execute("LOCK TABLE mimamsa_manifestation_sets IN ACCESS EXCLUSIVE MODE")
    try:
        code, res = run(world, "dry-run")
        assert code == 2 and any("LockNotAvailable" in c or "Timeout" in c for c in res["failed_checks"]), res["failed_checks"]
    finally:
        holder.rollback()
        holder.close()
    assert world.catalog_state() == pre


# ================================================================ the interpreter binding (exit 92)

def _tamper(evid, field, value):
    out, d = latest_outcome(evid, "dry-run")
    if value is None:
        out.pop(field, None)
    else:
        out[field] = value
    (d / "outcome.json").write_text(json.dumps(out))


@pytest.mark.parametrize("field,value,check", [("python_executable", "/other/python3.11", "interpreter_differs_from_dry_run"),
                                               ("python_version", "3.99.0 other", "interpreter_differs_from_dry_run"),
                                               ("psycopg_version", "0.0.0", "interpreter_differs_from_dry_run"),
                                               ("libpq_version", 1, "interpreter_differs_from_dry_run"),
                                               ("python_executable", None, "dry_run_evidence_lacks_interpreter_record")])
def test_apply_under_a_different_interpreter_or_driver_than_the_dry_run_refuses_with_exit_92_before_any_connection(world, evid, field, value, check):
    _, dry = run(world, "dry-run")
    _tamper(evid, field, value)
    args = argparse.Namespace(mode="apply", expect_plan=EX.plan_hash(), expect_evidence=dry["evidence_digest"], writer_commit=COMMIT, evidence_root=None)
    with pytest.raises(SystemExit) as ei:
        EX.execute(args, never_connect, gate_fp=GATE_FP, writer_runner=ok_runner, expected_db=world.name)
    assert ei.value.code == EX.EXIT_INTERPRETER == 92
    assert latest_outcome(evid, "apply")[0]["failed_checks"] == [check]


def test_the_runtime_is_bound_into_the_evidence_digest(world, evid, monkeypatch):
    _, a = run(world, "dry-run")
    monkeypatch.setattr(EX, "runtime_record", lambda: {"python_executable": "/x", "python_version": "y", "psycopg_version": "z", "libpq_version": 1})
    _, b = run(world, "dry-run")
    assert a["evidence_digest"] != b["evidence_digest"]


# ================================================================ rollback leg

def test_rollback_dry_run_changes_nothing_and_rollback_restores_the_exact_pre_state(world, evid):
    pre = world.catalog_state()
    _, dry = run(world, "dry-run")
    _, res = run(world, "apply", expect_evidence=dry["evidence_digest"])
    assert res["status"] == "COMMITTED"
    applied = world.catalog_state()
    assert applied != pre
    code, rdry = run(world, "rollback-dry-run")
    assert code == 0 and rdry["status"] == "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD" and world.catalog_state() == applied
    assert "6 removed" in "\n".join(rdry["log"]) and "8 removed" in "\n".join(rdry["log"])
    code, rb = run(world, "rollback", expect_evidence=rdry["evidence_digest"])
    assert code == 0 and rb["status"] == "COMMITTED"
    assert world.catalog_state() == pre, "ROLLBACK PROOF: every function, trigger, ACL, policy, constraint, index, membership, the schema ACL and every row digest equals the pre-state"
    assert outcome_of(rb)["status"] == "applied"
    # the rolled-back state accepts the forward plan again
    _, dry2 = run(world, "dry-run")
    code, res2 = run(world, "apply", expect_evidence=dry2["evidence_digest"])
    assert code == 0 and res2["status"] == "COMMITTED"


def test_rollback_needs_no_schema_capability_and_never_opens_one(world, evid):
    _, dry = run(world, "dry-run")
    run(world, "apply", expect_evidence=dry["evidence_digest"])
    _, rdry = run(world, "rollback-dry-run")
    assert "SCHEMA public CREATE for amjis_app after the plan: False" in "\n".join(rdry["log"])


def test_rollback_is_refused_when_nothing_is_installed_or_something_is_not_as_installed(world, evid):
    code, res = run(world, "rollback-dry-run")
    assert code == 2 and any(c.startswith("pre_installed_function_") for c in res["failed_checks"])
    _, dry = run(world, "dry-run")
    run(world, "apply", expect_evidence=dry["evidence_digest"])
    world.exec("ALTER TABLE mimamsa_predictions DISABLE TRIGGER mimamsa_predictions_frozen_row_guard", role="amjis_app")
    code, res = run(world, "rollback-dry-run")
    assert code == 2 and "pre_installed_trigger_mimamsa_predictions_frozen_row_guard" in res["failed_checks"]


def test_rollback_with_a_wrong_evidence_digest_is_refused(world, evid):
    _, dry = run(world, "dry-run")
    run(world, "apply", expect_evidence=dry["evidence_digest"])
    code, res = run(world, "rollback", expect_evidence="0" * 64)
    assert code == 1 and "evidence_digest_matches_expected" in res["failed_checks"]
    assert world.query("SELECT count(*) FROM pg_trigger WHERE tgenabled = 'A'") == [(8,)]


# ================================================================ commit_state_unknown

def test_a_commit_that_itself_raises_is_recorded_as_commit_state_unknown(world, evid):
    psy = world.pg["psycopg"]
    _, dry = run(world, "dry-run")
    args = argparse.Namespace(mode="apply", expect_plan=EX.plan_hash(), expect_evidence=dry["evidence_digest"], writer_commit=COMMIT, evidence_root=None)

    class Proxy:
        def __init__(self, c):
            self._c = c

        def commit(self):
            raise psy.OperationalError("connection dropped at the acknowledgement")

        def __getattr__(self, n):
            return getattr(self._c, n)

    with pytest.raises(psy.OperationalError):
        EX.execute(args, lambda: Proxy(world.connect("adm")), gate_fp=GATE_FP, writer_runner=ok_runner, expected_db=world.name)
    out, _ = latest_outcome(evid, "apply")
    assert out["status"] == "commit_state_unknown" and out["warnings"] == ["commit_raised:OperationalError"]


# ================================================================ GATE_V2 launch refusal (exit 93 / 95)

def _marker(under_test=True):
    gd = EX.gate_dir()
    return ES.make_marker(str(gd / "prerun_gate.py"), str(gd / "run_gated.sh"), under_test=under_test)


def test_launch_gate_refuses_without_a_marker_with_exit_93():
    with pytest.raises(SystemExit) as ei:
        EX.launch_gate({"PYTEST_CURRENT_TEST": "x"})
    assert ei.value.code == EX.EXIT_NO_LAUNCH == 93


def test_launch_gate_accepts_a_verifying_marker_and_reports_under_test():
    fp = EX.launch_gate({"GATE_V2_LAUNCH": _marker(True), "PYTEST_CURRENT_TEST": "x"})
    assert fp["under_test"] is True and fp["gate_sha256"] == EX.GATE_PINS["prerun_gate.py"] and fp["run_gated_sha256"] == EX.GATE_PINS["run_gated.sh"]


def test_launch_gate_refuses_a_tampered_marker_and_an_under_test_marker_outside_tests():
    m = _marker(True)
    with pytest.raises(SystemExit) as ei:
        EX.launch_gate({"GATE_V2_LAUNCH": m[:-1] + ("0" if m[-1] != "0" else "1"), "PYTEST_CURRENT_TEST": "x"})
    assert ei.value.code == 93
    with pytest.raises(SystemExit) as ei:
        EX.launch_gate({"GATE_V2_LAUNCH": m})          # no pytest, no GATE_V2_UNDER_TEST in the verifier's environment
    assert ei.value.code == 93
    with pytest.raises(SystemExit) as ei:
        EX.refuse_under_test_outside_pytest({"under_test": True}, {})
    assert ei.value.code == 93


def test_launch_gate_refuses_when_executor_standards_differs_from_its_pin(tmp_path, monkeypatch):
    d = tmp_path / "gate"
    shutil.copytree(EX.gate_dir(), d, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    (d / "executor_standards.py").write_text((d / "executor_standards.py").read_text() + "\n# edited\n")
    EX._STD.clear()
    with pytest.raises(SystemExit) as ei:
        EX.launch_gate({EX.GATE_DIR_ENV: str(d), "PYTEST_CURRENT_TEST": "x", "GATE_V2_LAUNCH": _marker(True)})
    EX._STD.clear()
    assert ei.value.code == 93


def test_a_test_gate_directory_is_refused_outside_a_pytest_run_with_exit_95():
    with pytest.raises(SystemExit) as ei:
        EX.gate_dir({EX.GATE_DIR_ENV: "/tmp/x"})
    assert ei.value.code == EX.EXIT_TEST_ENV == 95
    with pytest.raises(SystemExit) as ei:
        EX.resolve_evidence_root(None, {EX.TEST_EVIDENCE_ENV: "/tmp/x"})
    assert ei.value.code == 95


def test_main_runs_the_whole_chain_through_the_gate_marker_and_stops_at_the_database_name_guard(world, evid, monkeypatch, capsys):
    """main(): launch_gate -> parse -> execute with connect_admin replaced by a mirrored-world connection. The default expected database is `amjis`, the
    mirror is not, so the plan refuses at pre_database_is_the_expected_one: exit 2, nothing changed."""
    pre = world.catalog_state()
    monkeypatch.setenv("GATE_V2_LAUNCH", _marker(True))
    monkeypatch.setattr(EX, "connect_admin", lambda: world.connect("adm"))
    code = EX.main(["--dry-run", "--expect-plan", EX.plan_hash()])
    printed = json.loads(capsys.readouterr().out)
    assert code == 2 and printed["failed_checks"] == ["pre_database_is_the_expected_one"] and world.catalog_state() == pre


def test_connect_admin_is_pinned_to_the_proxy_the_amjis_database_and_the_postgres_user():
    src = (PKG / "l5_frozen_guard_exec.py").read_text(encoding="utf8")
    assert 'host="127.0.0.1", port=5433, dbname=EXPECTED_DB, user="postgres"' in src and 'EXPECTED_DB = "amjis"' in src
    assert "cloudsql-postgres-admin-password" in src
    import re
    assert len(re.findall(r"(?<![A-Za-z_.])print\(", src)) == 2, "only main() prints (the result JSON and the failure line), never a secret"


def test_the_run_gated_launcher_in_the_repo_is_the_one_the_executor_pins():
    assert ES.sha256_file(str(EX.gate_dir() / "run_gated.sh")) == EX.GATE_PINS["run_gated.sh"]
    assert ES.sha256_file(str(EX.gate_dir() / "prerun_gate.py")) == EX.GATE_PINS["prerun_gate.py"]


def test_every_check_name_is_a_valid_outcome_check_name():
    import re
    src = (PKG / "l5_frozen_guard_exec.py").read_text(encoding="utf8")
    for m in re.finditer(r'\(\s*"((?:pre|post|args|sql|expected|evidence|interpreter|dry)_[A-Za-z0-9_]*)"', src):
        assert re.fullmatch(r"[A-Za-z0-9_.:\-]{1,80}", m.group(1)), m.group(1)
    longest = max(len(t[1]) for t in EX.NEW_TRIGGERS)
    assert len("pre_installed_trigger_") + longest <= 80



def test_dry_run_apply_and_rollback_work_with_the_1275_foreign_keys_already_present(world, evid):
    add_chart_fks(world)
    pre = world.catalog_state()
    code, dry = run(world, "dry-run")
    assert code == 0 and world.catalog_state() == pre
    code, res = run(world, "apply", expect_evidence=dry["evidence_digest"])
    assert code == 0 and res["status"] == "COMMITTED"
    world.exec("DELETE FROM charts WHERE id = %s", (CHART_A,), role="amjis_app")
    code, rdry = run(world, "rollback-dry-run")
    assert code == 0
    code, rb = run(world, "rollback", expect_evidence=rdry["evidence_digest"])
    assert code == 0
