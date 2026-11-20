"""test_flip_detector_l2_mutations.py -- MUTATION PROOF for the L2 (Bodha) extension of flip_detector.py (same method as test_flip_detector_mutations.py).

For each mutation a copy of flip_detector.py is changed so one L2 check is neutered, and test_flip_detector_l2.py is re-run against that copy in a subprocess
(it loads the tool named by FLIP_DETECTOR_TOOL_UNDER_TEST). A mutation is proven only if

  * the mutation text replaced EXACTLY one place in the source (a stale anchor fails loudly instead of silently proving nothing),
  * the unmutated control run is green (so red can only come from the mutation), and
  * the mutated run is red AND at least one of the tests named in `must_fail` is among the failures.

No database, no network. Run alone: pytest test_flip_detector_l2_mutations.py -q
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
TOOL = HERE.parent / "flip_detector.py"
TESTS = HERE / "test_flip_detector_l2.py"

# (id, old text, new text, test-name substrings of which at least one must fail)
MUTATIONS = [
    ("table_dropped_from_the_registry",
     '    L2_TABLES[table] = {"from": frm,', '    if table != "bodha_triangulation":\n        L2_TABLES[table] = {"from": frm,',
     ["test_registry_is_the_29_l2_tables_of_the_data_plane_manifest"]),
    ("hook_tables_not_extended",
     "HOOK_TABLES = LEGACY_HOOK_TABLES + tuple(L2_TABLES)", "HOOK_TABLES = LEGACY_HOOK_TABLES",
     ["test_hook_tables_are_additive", "test_a_hook_may_name_an_l2_table_and_validates"]),
    ("key_and_identity_columns_swapped",
     "{_clean(s['key'])}", "{_clean(s['ident'])}",
     ["test_every_table_spec_is_one_read_only_select_of_seven_columns_filtered_by_chart[bodha_msr_signals]",
      "test_generated_identity_is_never_in_the_semantic_key[bodha_msr_signals]"]),
    ("chart_filter_dropped_from_the_l2_select",
     "where t.chart_id='{cid}'", "where 1=1",
     ["test_every_table_spec_is_one_read_only_select_of_seven_columns_filtered_by_chart[bodha_msr_signals]", "test_e2e_snapshot_with_l2_reads_everything_in_one_read_only_transaction"]),
    ("must_have_rows_flag_ignored",
     'if t in L2_TABLES and L2_TABLES[t]["must_have_rows"] and not l2.get(t)]', "if t in L2_TABLES and not l2.get(t)]",
     ["test_empty_read_does_not_apply_to_a_table_that_is_legitimately_empty[bodha_cgm_motifs]"]),
    ("empty_l2_read_never_flagged",
     'if t in L2_TABLES and L2_TABLES[t]["must_have_rows"] and not l2.get(t)]', "if False]",
     ["test_empty_read_applies_to_must_have_rows_tables[bodha_msr_signals]", "test_e2e_snapshot_of_an_empty_must_have_l2_table_is_refused_and_writes_nothing"]),
    ("compare_empty_l2_loop_removed",
     "        for t in empty_l2_tables(st, l2set):", "        for t in []:",
     ["test_empty_read_applies_to_must_have_rows_tables[bodha_msr_signals]"]),
    ("l2_treated_as_always_compared",
     'if e.get("table") in L2_TABLES and e["table"] not in l2_tables:', "if False:",
     ["test_hook_entry_on_an_l2_table_in_a_run_without_l2_is_not_checked_never_absent_never_passing"]),
    ("identity_compare_ignores_text",
     'vf = lambda r: (r[4], "", r[6], r[5])', 'vf = lambda r: ("", "", r[6], r[5])',
     ["test_a_moved_identity_is_one_value_change_not_an_appeared_plus_disappeared_pair[bodha_msr_signals]",
      "test_appeared_disappeared_value_occurrence_and_tier_are_detected_per_table[bodha_msr_signals]"]),
    ("score_compared_as_class_value",
     'vf = lambda r: (r[4], "", r[6], r[5])', 'vf = lambda r: (r[4], r[5], r[6], r[5])',
     ["test_a_continuous_score_change_is_not_a_class_change[bodha_msr_signals]"]),
    ("identical_rows_do_not_cancel",
     "        ra, rb = _l2_cancel_common(a, b)", "        ra, rb = a, b",
     ["test_one_moved_identity_in_a_large_duplicate_group_is_one_change_not_a_cascade"]),
    ("occurrence_totals_not_restored",
     'c["before"], c["after"] = orig[tuple(c["key"])]', "pass",
     ["test_occurrence_count_reports_the_totals_not_what_was_left_after_the_identical_rows_cancel"]),
    ("lost_score_not_a_value_change",
     '            if u != "" and v == "":', "            if False:",
     ["test_a_score_that_becomes_null_is_a_value_change_like_the_l1_continuous_values"]),
    ("l2_changes_not_added_to_the_report",
     "        changes += ch3", "        pass",
     ["test_appeared_disappeared_value_occurrence_and_tier_are_detected_per_table[bodha_msr_signals]", "test_an_undeclared_l2_change_is_undeclared_change"]),
    ("l2_not_compared_row_never_added",
     '    if l2_requested and not_compared.get("l2"):', "    if False:",
     ["test_l2_not_compared_row_only_when_l2_was_requested_and_a_section_is_missing", "test_e2e_compare_reads_only_the_tables_the_snapshot_carries_and_says_so"]),
    ("l2_standing_rows_added_to_every_run",
     "    if not l2_tables:\n        return standing", "    if False:\n        return standing",
     ["test_differential_golden_fixtures_and_all_23_real_hooks_are_identical_without_l2", "test_standing_l2_notes_only_when_l2_is_compared_and_the_stale_l1_era_rows_are_dropped_then"]),
    ("stale_l1_era_standing_rows_kept_in_l2_runs",
     'tuple(n for n in standing if n.get("table") not in l2_tables)', "tuple(standing)",
     ["test_standing_l2_notes_only_when_l2_is_compared_and_the_stale_l1_era_rows_are_dropped_then"]),
    ("l2_flag_ignored_the_default_reads_l2",
     '    if not getattr(a, "l2", False):\n        return ()', '    if False:\n        return ()',
     ["test_differential_cli_snapshot_and_compare_without_l2_are_byte_identical"]),
    ("against_needs_only_one_side",
     "l2_tables = tuple(t for t in want_l2 if t in in_snap and (in_cur is None or t in in_cur))", "l2_tables = tuple(t for t in want_l2 if t in in_snap)",
     ["test_e2e_compare_against_offline_needs_both_sides_and_never_reads_the_database"]),
    ("hook_validation_message_changed",
     "'table' must be one of {LEGACY_HOOK_TABLES}", "'table' must be one of {HOOK_TABLES}",
     ["test_differential_hook_validation_messages_are_identical", "test_a_hook_may_name_an_l2_table_and_validates"]),
    ("snapshot_of_an_empty_l2_read_accepted",
     "empties = empty_tables(st, not a.no_dashas, not a.no_daily) + empty_l2_tables(st)", "empties = empty_tables(st, not a.no_dashas, not a.no_daily)",
     ["test_e2e_snapshot_of_an_empty_must_have_l2_table_is_refused_and_writes_nothing"]),
    ("expectation_report_ignores_compared_l2_tables",
     "exp_rows, exp_bad, absent, warn, entry_unchecked = expectation_report(hooks, counts, chart_id, have_dash, have_daily, shift_counts, l2set)",
     "exp_rows, exp_bad, absent, warn, entry_unchecked = expectation_report(hooks, counts, chart_id, have_dash, have_daily, shift_counts)",
     ["test_with_l2_compared_the_same_entry_is_judged_like_any_other", "test_declared_but_absent_and_optional_on_an_l2_entry"]),
]


def _run_tests(tool_path, tmp_path, selection=None):
    """selection: test names (or name[param] ids) to run; None runs the whole file. A name that does not exist makes pytest exit 4, so a stale name fails loudly."""
    env = dict(os.environ)
    env["FLIP_DETECTOR_TOOL_UNDER_TEST"] = str(tool_path)
    env.pop("FLIP_DETECTOR_REGEN_GOLDEN", None)
    for k in [k for k in env if k.startswith("PG")] + ["DATABASE_URL", "FLIP_READER"]:
        env.pop(k, None)
    targets = [f"{TESTS}::{n}" for n in selection] if selection else [str(TESTS)]
    r = subprocess.run([sys.executable, "-m", "pytest", *targets, "-q", "--no-header", "-rf", "-p", "no:cacheprovider"],
                       capture_output=True, text=True, env=env, cwd=str(tmp_path), timeout=240)
    failed = re.findall(r"^FAILED \S+?::(\S+)", r.stdout, re.M)
    return r.returncode, failed, r.stdout[-1500:]


def test_control_unmutated_tool_is_green(tmp_path):
    code, failed, tail = _run_tests(TOOL, tmp_path)
    assert code == 0 and not failed, tail


@pytest.mark.parametrize("name,old,new,must_fail", MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_mutation_is_caught(tmp_path, name, old, new, must_fail):
    src = TOOL.read_text()
    assert src.count(old) == 1, f"mutation anchor for {name} matches {src.count(old)} places (must be exactly 1): {old!r}"
    mutated = tmp_path / "flip_detector.py"
    mutated.write_text(src.replace(old, new))
    code, failed, tail = _run_tests(mutated, tmp_path, must_fail)  # only the named tests: each mutation costs one pytest start-up
    assert code == 1, f"mutation {name} left the test-suite green (or broke it differently): rc={code}\n{tail}"
    assert any(any(m in f for f in failed) for m in must_fail), f"mutation {name}: expected one of {must_fail} to fail, got {failed}"
