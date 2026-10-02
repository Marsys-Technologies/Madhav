"""test_flip_detector_mutations.py -- MUTATION PROOF for flip_detector.py (a verdict-deciding tool).

For each check the tool relies on, a copy of flip_detector.py is mutated so the check is neutered, and test_flip_detector.py is re-run
against that copy in a subprocess (it loads the tool named by FLIP_DETECTOR_TOOL_UNDER_TEST). The mutation is proven only if

  * the mutation text replaced EXACTLY one place in the source (a stale anchor fails loudly instead of silently proving nothing),
  * the unmutated control run is green (so red can only come from the mutation), and
  * the mutated run is red AND the tests named in `must_fail` are among the failures.

No database, no network: the subprocess runs the same offline tests. Run alone: pytest test_flip_detector_mutations.py -q
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
TESTS = HERE / "test_flip_detector.py"

# (id, old text, new text, test-name substrings of which at least one must fail)
MUTATIONS = [
    ("undeclared_check_neutered",
     'undeclared = [c for c in unattrib if not c["kind_mismatch"]]', "undeclared = []",
     ["test_1a_undeclared_fact_change_fails", "test_1d_no_failure_scenario_is_ever_a_pass[undeclared]"]),
    ("declared_but_absent_check_neutered",
     "            elif n == 0:\n                if e.get(\"optional\"):", "            elif False:\n                if e.get(\"optional\"):",
     ["test_1b_declared_but_absent_fails", "test_1d_no_failure_scenario_is_ever_a_pass[absent]"]),
    ("optional_flag_ignored",
     '                if e.get("optional"):', "                if False:",
     ["test_1b_optional_entry_absent_is_a_named_warning_not_a_failure"]),
    ("kind_check_neutered",
     'return scope_matches(e, c) and c["change"] in (e.get("change_types") or CHANGE_TYPES)', "return scope_matches(e, c)",
     ["test_1c_value_change_under_a_tier_only_hook_is_a_kind_mismatch", "test_1d_no_failure_scenario_is_ever_a_pass[kind]"]),
    ("kind_mismatch_not_classified",
     'kind_mm = [c for c in unattrib if c["kind_mismatch"]]', "kind_mm = []",
     ["test_1c_value_change_under_a_tier_only_hook_is_a_kind_mismatch", "test_1d_no_failure_scenario_is_ever_a_pass[kind]"]),
    ("expectation_check_neutered",
     "                if not ok:\n                    bad.append(", "                if False:\n                    bad.append(",
     ["test_1b_expected_count_governs_the_entry", "test_1d_no_failure_scenario_is_ever_a_pass[expectation]"]),
    ("verdict_ignores_failures",
     'if any(rep["failures"].get(k) for k in FAILURE_CLASSES):', "if False:",
     ["test_1d_no_failure_scenario_is_ever_a_pass[undeclared]", "test_1d_hook_error_is_a_failure"]),
    ("allow_flag_softens_failures",
     "    if v == V_FAIL:\n        return EXIT_FAIL", "    if v == V_FAIL:\n        return EXIT_PASS if allow_not_checked else EXIT_FAIL",
     ["test_1d_no_failure_scenario_is_ever_a_pass[undeclared]", "test_2_not_checked_never_hides_a_failure"]),
    ("alert_not_decided",
     'if rep.get("ALERT_anchor_changed"):\n        return V_ALERT', "if False:\n        return V_ALERT",
     ["test_anchor_change_is_alert_and_wins_over_failures"]),
    ("not_checked_registry_emptied",
     "standing_not_checked=STANDING_NOT_CHECKED):", "standing_not_checked=()):",
     ["test_2_both_uncheckable_tier_changes_are_listed_on_every_compare", "test_2_not_checked_is_a_distinct_verdict_never_a_pass"]),
    ("not_checked_exits_zero",
     "return EXIT_PASS if allow_not_checked else EXIT_NOT_CHECKED", "return EXIT_PASS",
     ["test_2_not_checked_is_a_distinct_verdict_never_a_pass", "test_2_cli_exit_codes_and_printed_output"]),
    ("not_checked_not_printed",
     '    for n in rep["not_checked"]:\n        by =', '    for n in []:\n        by =',
     ["test_2_summary_prints_both_not_checked_lines_even_when_allowed", "test_2_cli_exit_codes_and_printed_output"]),
    ("dasha_tier_entry_treated_as_observable",
     'if e.get("kind") != "dasha_shift" and set(e.get("change_types") or ()) == {"tier"}:', "if False:",
     ["test_2_declared_by_names_the_lane_that_declares_the_unverifiable_tier", "test_real_hooks_with_no_changes_list_exactly_the_entries_a_lane_author_must_fix"]),
    ("require_lanes_check_removed",
     "        if lane and lane not in present:", "        if False:",
     ["test_3_missing_required_lane_fails", "test_real_hook_files_validate"]),
    ("empty_may_change_accepted",
     "if not isinstance(mc, list) or not mc:", "if not isinstance(mc, list):",
     ["test_3_malformed_hook_is_rejected[empty_may_change]", "test_3_each_required_top_level_field_is_required[may_change]"]),
    ("missing_hooks_dir_accepted",
     "    if not os.path.isdir(hooks_dir):", "    if False:",
     ["test_3_missing_empty_and_nested_directories"]),
    ("read_only_guard_removed",
     'if not re.match(r"^\\s*select\\b", sql, re.I) or ";" in sql.strip().rstrip(";"):', "if False:",
     ["test_read_only_guard"]),
    # ---- survivor of the independent review (the author's 17 above are unchanged in intent)
    ("ayanamsha_narrowing_ignored",
     'if e.get("ayanamsha_ids") and c.get("ayanamsha") not in e["ayanamsha_ids"]:', "if False:",
     ["test_hook_ayanamsha_narrowing_is_honoured"]),
    # ---- the review fixes, each with its own mutation
    ("fact_key_narrowing_ignored",
     'if e.get("fact_keys") and c.get("fact_key") not in e["fact_keys"]:', "if False:",
     ["test_hook_fact_key_narrowing_is_honoured"]),
    ("chart_scope_of_a_hook_ignored",
     '    return any(chart_id.lower().startswith(p.lower()) for p in h["charts"])', "    return True",
     ["test_chart_scope_of_a_hook", "test_1b_hook_for_another_chart_is_not_declared_but_absent"]),
    ("med1_continuous_to_null_invisible",
     'if (y[0] or "") != "" or y[1] in ("", None):', "if False:",
     ["test_med1_continuous_number_becoming_null_is_a_value_change", "test_med1_continuous_number_becoming_text_is_a_value_change"]),
    ("med1_continuous_keys_ignored_again",
     'if kinds == {"time"}:', 'if kinds <= {"continuous", "time"}:',
     ["test_med1_whole_continuous_category_disappearing_is_five_changes", "test_med1_continuous_key_appearing_is_a_change_and_can_be_declared_or_missing"]),
    ("med2_empty_read_guard_removed",
     "if not st.get(key):", "if False:",
     ["test_med2_everything_empty_on_a_non_native_chart_is_not_clean", "test_med2_cli_empty_snapshots_exit_2_even_with_allow_not_checked"]),
    ("low3_chart_uuid_validation_removed",
     "if not UUID_RE.match(t):", "if False:",
     ["test_low3_chart_id_must_be_a_uuid"]),
    ("low3_sql_statement_chaining_allowed",
     'or ";" in sql.strip().rstrip(";"):', ":",
     ["test_read_only_guard"]),
    ("low4_chart_id_not_normalised",
     't = str(c).strip().strip("{}").strip().lower()', "t = str(c)",
     ["test_low4_uppercase_or_braced_chart_id_still_gets_the_anchor_check", "test_low3_snapshot_names_and_uuids_resolve"]),
    ("low5_empty_fact_keys_accepted",
     "isinstance(e[f], list) and e[f] and all(", "isinstance(e[f], list) and all(",
     ["test_low5_empty_lists_are_rejected"]),
    ("low5_empty_charts_accepted",
     'isinstance(h["charts"], list) and h["charts"] and all(', 'isinstance(h["charts"], list) and all(',
     ["test_low5_empty_lists_are_rejected"]),
    ("low6_empty_hooks_dir_accepted",
     "if a.hooks_dir is not None and not a.hooks_dir.strip():", "if False:",
     ["test_low6_empty_hooks_dir_or_lanes_is_refused"]),
    ("malformed_report_trusted",
     "    if report_is_malformed(rep):\n        return V_FAIL", "    if False:\n        return V_FAIL",
     ["test_malformed_report_is_a_clean_failure_not_a_keyerror", "test_saved_report_json_verdict_field_is_not_trusted"]),
    # ---- delta-review fixes
    ("f1_timestamp_to_null_invisible",
     'if kind_of(y[0], y[1], key) != "time":', "if False:",
     ["test_f1_timestamp_becoming_null_or_text_is_a_value_change"]),
    ("f2_not_checked_type_unchecked",
     ' or not isinstance(rep["not_checked"], list)', "",
     ["test_malformed_report_is_a_clean_failure_not_a_keyerror"]),
]


def _run_tests(tool_path, tmp_path):
    env = dict(os.environ)
    env["FLIP_DETECTOR_TOOL_UNDER_TEST"] = str(tool_path)
    env.pop("FLIP_DETECTOR_REGEN_GOLDEN", None)
    for k in [k for k in env if k.startswith("PG")] + ["DATABASE_URL", "FLIP_READER"]:
        env.pop(k, None)
    r = subprocess.run([sys.executable, "-m", "pytest", str(TESTS), "-q", "--no-header", "-rf", "-p", "no:cacheprovider"],
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
    code, failed, tail = _run_tests(mutated, tmp_path)
    assert code == 1, f"mutation {name} left the test-suite green (or broke it differently): rc={code}\n{tail}"
    assert any(any(m in f for f in failed) for m in must_fail), f"mutation {name}: expected one of {must_fail} to fail, got {failed}"
