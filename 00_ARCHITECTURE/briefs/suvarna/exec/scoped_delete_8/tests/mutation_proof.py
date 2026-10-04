#!/usr/bin/env python3
"""Mutation proof for the PYTHON layer of scoped_delete_8_exec.py (a script, NOT collected by pytest/CI: it starts disposable PostgreSQL clusters).

For each mutation it copies the package to a sibling folder of exec/gate_v2 (so the gate files and the repo layout resolve), neuters ONE safeguard in the copy's
executor (or its SQL), runs the tests that must catch it and requires them to go RED (a non-zero pytest exit). The unmutated package is run first and must be green, and so must the same tests on the unmutated copy.
(The SQL-layer mutations are ordinary tests in test_mirror.py: test_mutation_*.)

    python3 tests/mutation_proof.py [--pg-bin /opt/homebrew/opt/postgresql@15/bin]

Process rule: every cluster is started and stopped by the test fixture (recorded PID, SIGINT to that PID, directory deleted); this script signals nothing.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent
EXEC = PKG.parent

M = "scoped_delete_8_exec.py"
SQLF = "sd8_delete_life_event_miss_phala_pramana.sql"
MUTATIONS = [
    ("server_major_check_neutered", M, 'ck.chk("pre_server_major_is_15", who[4] // 10000 == SERVER_MAJOR,', 'ck.chk("pre_server_major_is_15", True,',
     "test_a_server_major_version_other_than_15_is_refused"),
    ("database_check_neutered", M, 'ck.chk("pre_database_is_expected", who[5] == EXPECTED_DATABASE,', 'ck.chk("pre_database_is_expected", True,',
     "test_the_wrong_database_is_refused"),
    ("administrator_identity_check_neutered", M, 'ck.chk("pre_session_user_is_the_expected_administrator", who[0] == EXPECTED_ADMIN and who[1] == EXPECTED_ADMIN,',
     'ck.chk("pre_session_user_is_the_expected_administrator", True,', "test_the_wrong_role_is_refused"),
    ("exactly_n_rows_check_neutered_both_tables", M, 'x["match_n"] == len(t["ids"]) == n,', "True,",
     "test_seven_matching_rows_are_refused or test_nine_matching_rows_are_refused or test_fifteen_matching_snapshot_rows_are_refused or test_seventeen_matching_snapshot_rows_are_refused or test_zero_matching_phaladesa_snapshot_rows_are_refused or test_two_matching_phaladesa_snapshot_rows_are_refused"),
    ("ids_equal_check_neutered_both_tables", M, 'x["match_ids"] == sorted(t["ids"]),', "True,",
     "test_different_ids_are_refused_even_with_exactly_8_matching_rows or test_different_snapshot_ids_are_refused_even_with_exactly_16_matching_rows or test_a_different_phaladesa_snapshot_id_is_refused"),
    ("fingerprint_check_neutered_both_tables", M, 'x["match_fingerprint"] == t["fp"],', "True,",
     "test_a_changed_non_private_value_changes_the_fingerprint_and_is_refused or test_a_changed_non_private_snapshot_value_is_refused or test_a_changed_non_private_phaladesa_snapshot_value_is_refused"),
    ("payload_check_neutered_both_tables", M, 'x["match_payload_n"] == 0,', "True,",
     "test_a_row_carrying_a_life_event_payload_is_refused or test_a_snapshot_row_carrying_a_life_event_payload_is_refused"),
    ("duplicate_id_check_neutered", M, 'x["bound_ids_present_n"] == n,', "True,", "test_a_duplicate_of_a_bound_snapshot_id_elsewhere_in_the_table_is_refused or test_a_duplicate_of_the_bound_phaladesa_snapshot_id_elsewhere_is_refused"),
    ("dependents_check_neutered", M, 'all(v == 0 for v in dep.values()) and set(dep) == set(DEPENDENT_QUERIES),', "True,",
     "test_a_dependent_is_refused or test_a_dependent_of_a_snapshot_id_is_refused or test_the_two_tables_must_not_carry_each_others_ids or test_a_pramana_dependent_carrying_the_phaladesa_id_is_refused"),
    ("referencer_set_check_neutered", M, 'm["referencer_columns"] == ",".join(sorted(KNOWN_REFERENCERS)),', "True,",
     "test_a_new_column_that_can_refer_to_a_pramana_id_fails_closed"),
    ("build_in_flight_check_neutered", M, 'm["builds_in_flight_any"] == 0 and m["builds_in_flight_on_chart"] == 0,', "True,", "test_a_build_in_flight_is_refused"),
    ("foreign_key_check_neutered_both_tables", M, 'f["fk_referencing"] == 0, f["fk_referencing"])', "True, f[\"fk_referencing\"])",
     "test_a_foreign_key_referencing_the_table_is_refused or test_a_snapshot_guard_or_shape_change_is_refused_and_nothing_is_bypassed"),
    ("trigger_rule_policy_view_inheritance_check_neutered_both_tables", M,
     'f["user_triggers"] == 0 and f["rules"] == 0 and f["policies"] == 0 and f["dependent_views"] == 0 and f["inheritance"] == 0,', "True,",
     "test_a_trigger_rule_or_inheritance_child_is_refused or test_a_snapshot_guard_or_shape_change_is_refused_and_nothing_is_bypassed"),
    ("table_owner_rls_check_neutered_both_tables", M, 'tb is not None and tb[0] == OWNER_ROLE and tb[1] == "r" and tb[2] is False and tb[3] is False,', "True,",
     "test_row_level_security_on_the_table_is_refused or test_a_snapshot_guard_or_shape_change_is_refused_and_nothing_is_bypassed"),
    ("delete_role_privilege_check_neutered_both_tables", M, 'pv is not None and pv[0] is True and not any(pv[1:])', "True",
     "test_a_changed_acl_for_the_delete_role_is_refused or test_a_snapshot_guard_or_shape_change_is_refused_and_nothing_is_bypassed or test_a_phaladesa_snapshot_guard_or_shape_change_is_refused_and_nothing_is_bypassed"),
    ("live_phaladesa_precondition_neutered", M, 'lp["match_n"] == 0 and lp["id_present_n"] == 0,', "True,",
     "test_a_live_phaladesa_miss_row_for_the_chart_is_refused or test_a_live_phaladesa_row_carrying_the_bound_id_is_refused"),
    ("live_phaladesa_unchanged_post_check_neutered", M, 'm["live_phd"] == pre_m["live_phd"],', "True,", "test_mutation_a_write_to_the_live_phaladesa_is_refused_by_the_python_layer_alone"),
    ("phaladesa_referencer_set_check_neutered", M, 'm["phd_referencer_columns"] == "phala_phaladesa.phaladesa_id,phala_phaladesa__ssv_20260728b.phaladesa_id",', "True,",
     "test_a_new_column_that_can_refer_to_a_phaladesa_id_fails_closed"),
    ("event_trigger_check_neutered", M, 'ck.chk("pre_no_event_trigger_exists", pre["event_triggers"] == 0,', 'ck.chk("pre_no_event_trigger_exists", True,',
     "test_an_event_trigger_anywhere_is_refused"),
    ("sql_bound_values_check_neutered", M, 'bound == {"chart": CHART, "ids": IDS_CSV, "fp": ROWS_FINGERPRINT, "shadow_ids": SHADOW_IDS_CSV, "shadow_fp": SHADOW_FINGERPRINT, "phd_ids": PHD_IDS_CSV, "phd_fp": PHD_FINGERPRINT},', "True,",
     "test_mutation_h_an_edited_id_or_fingerprint_in_the_sql_is_refused_by_the_executors_own_copy or test_the_shadow_sql_values_edited_are_refused_by_the_executors_own_copy or test_the_phaladesa_sql_values_edited_are_refused_by_the_executors_own_copy"),
    ("post_other_charts_check_neutered_both_tables", M, 'x["other_by_chart"] == y["other_by_chart"],', "True,",
     "test_mutation_c_without_any_sql_check_the_python_post_measurement_refuses or test_mutation_snapshot_without_any_sql_check_the_python_post_measurement_refuses"),
    ("post_deleted_ids_check_neutered_both_tables", M, 'deleted[k] == sorted(t["ids"]),', "True,",
     "test_mutation_c_without_any_sql_check_the_python_post_measurement_refuses or test_mutation_snapshot_without_any_sql_check_the_python_post_measurement_refuses"),
    ("post_chart_total_check_neutered", M, 'x["chart_total"] == y["chart_total"] - n, f"{y', 'True, f"{y',
     "test_mutation_c2_the_python_measurement_does_not_trust_the_recorded_deleted_ids"),
    ("memberships_restored_check_neutered", M, 'ck.chk("post_memberships_restored", post["memberships"] == pre["memberships"],',
     'ck.chk("post_memberships_restored", True,', "test_mutation_f_memberships_never_revoked_is_refused"),
    ("delete_step_guard_removed", M, "if name in (STEP_DELETE, STEP_DELETE_SHADOW, STEP_DELETE_PHD) and ck.failed:", "if False:",
     "test_mutation_g_without_the_sql_preconditions or test_mutation_snapshot_sql_preconditions_removed_the_python_ones_still_refuse"),
    ("interpreter_precheck_neutered", M, "    now, matches = runtime_record(), []\n", "    return\n    now, matches = runtime_record(), []\n",
     "test_apply_refuses_with_exit_92"),
    ("evidence_digest_comparison_neutered", M, 'if args.mode == "apply" and digest != args.expect_evidence:', "if False:",
     "test_a_wrong_plan_or_evidence_is_refused_and_changes_nothing or test_a_stale_dry_run_digest_is_refused_when_the_state_moved"),
    ("plan_hash_comparison_neutered", M, "if args.expect_plan != phash:", "if False:", "test_a_wrong_plan_or_evidence_is_refused_and_changes_nothing"),
    ("sql_delete_without_row_count_assertion", SQLF, "  IF v_n <> 8 THEN RAISE EXCEPTION 'sd8 delete: % rows deleted, expected exactly 8', v_n; END IF;\n", "",
     "test_mutation_a_marker_only_delete_is_refused_by_the_delete_step_count_check"),
    ("sql_delete_as_builder_role_assertion_removed", SQLF,
     "  IF current_user <> 'data_plane_builder' THEN RAISE EXCEPTION 'sd8 delete: the delete must run as data_plane_builder, not %', current_user; END IF;\n", "",
     "test_mutation_e_a_delete_run_as_the_wrong_role_is_refused"),
    ("sql_shadow_delete_without_row_count_assertion", SQLF, "  IF v_n <> 16 THEN RAISE EXCEPTION 'sd8 shadow delete: % rows deleted, expected exactly 16', v_n; END IF;\n", "",
     "test_mutation_snapshot_marker_only_delete_is_refused_by_the_step_count_check"),
    ("sql_shadow_delete_role_assertion_removed", SQLF,
     "  IF current_user <> 'amjis_app' THEN RAISE EXCEPTION 'sd8 shadow delete: the delete must run as amjis_app, not %', current_user; END IF;\n", "",
     "test_mutation_a_snapshot_delete_run_as_the_wrong_role_is_refused"),
    # (removing only the SQL row COUNT check, or only the SQL ids-equality check, of the snapshot are EQUIVALENT mutants: the other two of {count, ids-equal, fingerprint} subsume each
    # one, so they are not listed; the fingerprint one is not subsumed and is)
    ("sql_shadow_fingerprint_precondition_removed", SQLF, "  IF v_fp IS DISTINCT FROM current_setting('madhav.sd8_shadow_fp') THEN", "  IF false THEN",
     "test_a_changed_non_private_snapshot_value_is_refused"),
    ("sql_phaladesa_delete_without_row_count_assertion", SQLF, "  IF v_n <> 1 THEN RAISE EXCEPTION 'sd8 phaladesa delete: % rows deleted, expected exactly 1', v_n; END IF;\n", "",
     "test_mutation_phaladesa_marker_only_delete_is_refused_by_the_step_count_check"),
    ("sql_phaladesa_delete_role_assertion_removed", SQLF,
     "  IF current_user <> 'amjis_app' THEN RAISE EXCEPTION 'sd8 phaladesa delete: the delete must run as amjis_app, not %', current_user; END IF;\n", "",
     "test_mutation_a_phaladesa_delete_run_as_the_wrong_role_is_refused"),
    ("sql_phaladesa_fingerprint_precondition_removed", SQLF, "  IF v_fp IS DISTINCT FROM current_setting('madhav.sd8_phd_fp') THEN", "  IF false THEN",
     "test_a_changed_non_private_phaladesa_snapshot_value_is_refused"),
    ("sql_live_phaladesa_miss_precondition_removed", SQLF, "  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % LIVE phala_phaladesa row(s) are (chart, life_event_miss)", "  IF false THEN RAISE EXCEPTION 'sd8 precondition: % LIVE phala_phaladesa row(s) are (chart, life_event_miss)",
     "test_the_sql_refuses_a_live_phaladesa_miss_row_on_its_own"),
    ("sql_live_phaladesa_unchanged_post_assertion_removed", SQLF, "    RAISE EXCEPTION 'sd8 post: the id set of the LIVE phala_phaladesa changed';", "    NULL;",
     "test_mutation_a_write_to_the_live_phaladesa_is_refused_by_the_sql_post_assertion"),
    ("sql_shadow_event_trigger_precondition_removed", SQLF, "  IF v_x <> 0 THEN RAISE EXCEPTION 'sd8 precondition: % event trigger(s) exist", "  IF false THEN RAISE EXCEPTION 'sd8 precondition: % event trigger(s) exist",
     "test_an_event_trigger_is_refused_by_the_sql_layer_on_its_own"),
]


def run_pytest(pkg: pathlib.Path, selector: str | None, env) -> int:
    cmd = [sys.executable, "-m", "pytest", str(pkg / "tests"), "-q", "-x", "-p", "no:cacheprovider"]
    if selector:
        cmd += ["-k", selector]
    return subprocess.run(cmd, env=env, capture_output=True, text=True).returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pg-bin")
    ap.add_argument("--only")
    a = ap.parse_args()
    env = dict(os.environ)
    if a.pg_bin:
        env["PG_BIN"] = a.pg_bin
    tmp = EXEC / "_sd8_mutation_tmp"
    bad = 0
    try:
        for name, fname, old, new, selector in [(None, None, None, None, None)] + MUTATIONS:
            if name is None:
                rc = run_pytest(PKG, None, env)
                print(f"{'ok  ' if rc == 0 else 'FAIL'} unmutated package: full suite exit {rc} (must be 0)")
                bad += rc != 0
                continue
            if a.only and a.only != name:
                continue
            if tmp.exists():
                shutil.rmtree(tmp)
            shutil.copytree(PKG, tmp, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
            base_rc = run_pytest(tmp, selector, env)               # the SAME tests on the UNMUTATED copy must be green: a red run is then the mutation's doing
            if base_rc != 0:
                print(f"FAIL {name}: the selected tests are not green on the unmutated copy (exit {base_rc}); the proof would be meaningless")
                bad += 1
                continue
            target = tmp / fname
            src = target.read_text()
            if src.count(old) < 1:
                print(f"FAIL {name}: the mutation anchor is not in {fname}")
                bad += 1
                continue
            target.write_text(src.replace(old, new, 1))
            rc = run_pytest(tmp, selector, env)
            caught = rc != 0
            print(f"{'ok  ' if caught else 'FAIL'} {name}: tests [{selector}] went {'RED (mutation caught)' if caught else 'GREEN (mutation NOT caught)'}")
            bad += not caught
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("ALL MUTATIONS CAUGHT" if not bad else f"{bad} PROBLEM(S)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
