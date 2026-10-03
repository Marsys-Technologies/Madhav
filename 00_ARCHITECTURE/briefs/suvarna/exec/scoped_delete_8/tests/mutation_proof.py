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
MUTATIONS = [
    ("server_major_check_neutered", M, 'ck.chk("pre_server_major_is_15", who[4] // 10000 == SERVER_MAJOR,', 'ck.chk("pre_server_major_is_15", True,',
     "test_a_server_major_version_other_than_15_is_refused"),
    ("database_check_neutered", M, 'ck.chk("pre_database_is_expected", who[5] == EXPECTED_DATABASE,', 'ck.chk("pre_database_is_expected", True,',
     "test_the_wrong_database_is_refused"),
    ("administrator_identity_check_neutered", M, 'ck.chk("pre_session_user_is_the_expected_administrator", who[0] == EXPECTED_ADMIN and who[1] == EXPECTED_ADMIN,',
     'ck.chk("pre_session_user_is_the_expected_administrator", True,', "test_the_wrong_role_is_refused"),
    ("exactly_8_check_neutered", M, 'ck.chk("m_pre_exactly_8_rows_match_chart_and_marker", m["match_n"] == len(IDS) == 8,',
     'ck.chk("m_pre_exactly_8_rows_match_chart_and_marker", True,', "test_seven_matching_rows_are_refused or test_nine_matching_rows_are_refused"),
    ("ids_equal_check_neutered", M, 'ck.chk("m_pre_matching_ids_equal_the_bound_ids", m["match_ids"] == sorted(IDS),',
     'ck.chk("m_pre_matching_ids_equal_the_bound_ids", True,', "test_different_ids_are_refused_even_with_exactly_8_matching_rows"),
    ("fingerprint_check_neutered", M, 'ck.chk("m_pre_fingerprint_equals_the_pinned_one", m["match_fingerprint"] == ROWS_FINGERPRINT,',
     'ck.chk("m_pre_fingerprint_equals_the_pinned_one", True,', "test_a_changed_non_private_value_changes_the_fingerprint_and_is_refused"),
    ("payload_check_neutered", M, 'ck.chk("m_pre_no_matching_row_carries_a_life_event_payload", m["match_payload_n"] == 0,',
     'ck.chk("m_pre_no_matching_row_carries_a_life_event_payload", True,', "test_a_row_carrying_a_life_event_payload_is_refused"),
    ("dependents_check_neutered", M, 'ck.chk("m_pre_dependents_are_zero", all(v == 0 for v in dep.values()) and set(dep) == set(DEPENDENT_QUERIES),',
     'ck.chk("m_pre_dependents_are_zero", True,', "test_a_dependent_is_refused"),
    ("referencer_set_check_neutered", M, 'ck.chk("m_pre_referencer_columns_are_the_known_set", m["referencer_columns"] == ",".join(sorted(KNOWN_REFERENCERS)),',
     'ck.chk("m_pre_referencer_columns_are_the_known_set", True,', "test_a_new_column_that_can_refer_to_a_pramana_id_fails_closed"),
    ("build_in_flight_check_neutered", M, 'ck.chk("m_pre_no_build_in_flight", m["builds_in_flight_any"] == 0 and m["builds_in_flight_on_chart"] == 0,',
     'ck.chk("m_pre_no_build_in_flight", True,', "test_a_build_in_flight_is_refused"),
    ("delete_role_privilege_check_neutered", M, 'ck.chk("pre_delete_role_can_delete_and_reader_cannot_write", p is not None and p[0] is True and p[1] is False and p[2] is False, p)',
     'ck.chk("pre_delete_role_can_delete_and_reader_cannot_write", True, p)', "test_a_changed_acl_for_the_delete_role_is_refused"),
    ("foreign_key_check_neutered", M, 'ck.chk("pre_no_foreign_key_references_the_table", pre["fk_referencing"] == 0,',
     'ck.chk("pre_no_foreign_key_references_the_table", True,', "test_a_foreign_key_referencing_the_table_is_refused"),
    ("sql_bound_values_check_neutered", M, 'bound == {"chart": CHART, "ids": IDS_CSV, "fp": ROWS_FINGERPRINT},', 'True,',
     "test_mutation_h_an_edited_id_or_fingerprint_in_the_sql_is_refused_by_the_executors_own_copy"),
    ("post_other_charts_check_neutered", M, 'ck.chk("m_post_other_charts_counts_unchanged", m["other_by_chart"] == pre_m["other_by_chart"],',
     'ck.chk("m_post_other_charts_counts_unchanged", True,', "test_mutation_c_without_any_sql_check_the_python_post_measurement_refuses"),
    ("post_deleted_ids_check_neutered", M, 'ck.chk("m_post_deleted_ids_equal_the_bound_ids", deleted == sorted(IDS),',
     'ck.chk("m_post_deleted_ids_equal_the_bound_ids", True,', "test_mutation_c_without_any_sql_check_the_python_post_measurement_refuses"),
    ("post_chart_total_check_neutered", M, 'ck.chk("m_post_chart_total_reduced_by_exactly_8", m["chart_total"] == pre_m["chart_total"] - 8,',
     'ck.chk("m_post_chart_total_reduced_by_exactly_8", True,', "test_mutation_c2_the_python_measurement_does_not_trust_the_recorded_deleted_ids"),
    ("memberships_restored_check_neutered", M, 'ck.chk("post_memberships_restored", post["memberships"] == pre["memberships"],',
     'ck.chk("post_memberships_restored", True,', "test_mutation_f_memberships_never_revoked_is_refused"),
    ("delete_step_guard_removed", M, "if name == STEP_DELETE and ck.failed:", "if False:", "test_mutation_g_without_the_sql_preconditions"),
    ("interpreter_precheck_neutered", M, "    now, matches = runtime_record(), []\n", "    return\n    now, matches = runtime_record(), []\n",
     "test_apply_refuses_with_exit_92"),
    ("evidence_digest_comparison_neutered", M, 'if args.mode == "apply" and digest != args.expect_evidence:', "if False:",
     "test_a_wrong_plan_or_evidence_is_refused_and_changes_nothing or test_a_stale_dry_run_digest_is_refused_when_the_state_moved"),
    ("plan_hash_comparison_neutered", M, "if args.expect_plan != phash:", "if False:", "test_a_wrong_plan_or_evidence_is_refused_and_changes_nothing"),
    ("sql_delete_without_row_count_assertion",
     "sd8_delete_life_event_miss_phala_pramana.sql", "  IF v_n <> 8 THEN RAISE EXCEPTION 'sd8 delete: % rows deleted, expected exactly 8', v_n; END IF;\n", "",
     "test_mutation_a_marker_only_delete_is_refused_by_the_delete_step_count_check"),
    ("sql_delete_as_builder_role_assertion_removed",
     "sd8_delete_life_event_miss_phala_pramana.sql", "  IF current_user <> 'data_plane_builder' THEN RAISE EXCEPTION 'sd8 delete: the delete must run as data_plane_builder, not %', current_user; END IF;\n", "",
     "test_mutation_e_a_delete_run_as_the_wrong_role_is_refused"),
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
