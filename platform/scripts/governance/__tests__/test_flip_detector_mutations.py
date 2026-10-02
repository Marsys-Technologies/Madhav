"""test_flip_detector_mutations.py -- MUTATION PROOF for flip_detector.py (a verdict-deciding tool).

For each check the tool relies on, a copy of flip_detector.py is mutated so the check is neutered, and test_flip_detector.py is re-run
against that copy in a subprocess (it loads the tool named by FLIP_DETECTOR_TOOL_UNDER_TEST). The mutation is proven only if

  * the mutation text replaced EXACTLY one place in the source (a stale anchor fails loudly instead of silently proving nothing),
  * the unmutated control run is green (so red can only come from the mutation), and
  * the mutated run is red AND the tests named in `must_fail` are among the failures.

No database, no network: the subprocess runs the same offline tests. Each mutated run executes only the tests named for it (the control runs everything). Run alone: pytest test_flip_detector_mutations.py -q
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
     "standing_not_checked=STANDING_NOT_CHECKED,", "standing_not_checked=(),",
     ["test_2_both_uncheckable_tier_changes_are_listed_on_every_compare", "test_2_not_checked_is_a_distinct_verdict_never_a_pass"]),
    ("not_checked_exits_zero",
     "return EXIT_PASS if allow_not_checked else EXIT_NOT_CHECKED", "return EXIT_PASS",
     ["test_2_not_checked_is_a_distinct_verdict_never_a_pass", "test_2_cli_exit_codes_and_printed_output"]),
    ("not_checked_not_printed",
     '    for n in rep["not_checked"]:\n        by =', '    for n in []:\n        by =',
     ["test_2_summary_prints_both_not_checked_lines_even_when_allowed", "test_2_cli_exit_codes_and_printed_output"]),
    ("dasha_tier_entry_treated_as_observable",
     'if e.get("kind") != "dasha_shift" and set(e.get("change_types") or ()) == {"tier"}:', "if False:",
     ["test_2_declared_by_names_the_lane_that_declares_the_unverifiable_tier", "test_every_integration_hook_states_its_absence_rule"]),
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
     "if on and not st.get(key)]", "if False]",
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
    # ---- second independent review (R-T2) + SS rulings
    ("f1_not_compared_row_removed",
     '        if not on:\n            not_checked.append({"id": f"{tname}.not_compared"', '        if False:\n            not_checked.append({"id": f"{tname}.not_compared"',
     ["test_f1_no_dashas_makes_a_real_dasha_change_not_checked_and_never_green", "test_f1_no_daily_makes_a_real_panchanga_change_not_checked"]),
    ("f1_green_ok_line_for_a_skipped_class",
     'if not na.get(k, ("", True))[1]:', "if False:",
     ["test_f1_no_dashas_makes_a_real_dasha_change_not_checked_and_never_green"]),
    ("f1_skipped_sections_not_recorded",
     '"skipped_sections": skipped,', '"skipped_sections": [],',
     ["test_f1_cli_records_flags_and_skipped_sections_in_meta"]),
    ("ss_dasha_skip_with_require_lanes_not_refused",
     "if a.compare and (a.no_dashas or a.no_daily) and a.require_lanes and not a.i_know_dashas_are_not_compared:", "if False:",
     ["test_ss_skipping_with_require_lanes_is_refused_unless_acknowledged"]),
    ("m20_against_disables_dashas",
     "have[tname] = not why", "have[tname] = False",
     ["test_f4_against_with_both_sections_compares_dashas"]),
    ("f3_dasha_shift_expected_count_accepted",
     '            if "expected_count" in e:\n                errs.append', '            if False:\n                errs.append',
     ["test_f3_f16_expected_count_misuse_is_rejected"]),
    ("f16_boolean_count_accepted",
     "isinstance(v, int) and not isinstance(v, bool) and v >= 0", "isinstance(v, int) and v >= 0",
     ["test_f3_f16_expected_count_misuse_is_rejected"]),
    ("f16_min_above_max_accepted",
     ' and not ("min" in ec and "max" in ec and ec["min"] > ec["max"]))', ")",
     ["test_f3_f16_expected_count_misuse_is_rejected"]),
    ("f9_tier_not_in_the_sort_key",
     ', (v[2] if len(v) > 2 else "") or ""))', "))",
     ["test_f9_equal_rows_differing_only_in_tier_pair_in_a_fixed_order"]),
    ("f5_iso_prefix_only_match",
     r'ISO = re.compile(r"^\d{4}-\d\d-\d\d[T ]\d\d:\d\d(:\d\d(\.\d+)?)?(Z|[+-]\d\d(:?\d\d)?)?$")', r'ISO = re.compile(r"^\d{4}-\d\d-\d\d[T ]\d\d:\d\d")',
     ["test_f5_kind_of_requires_a_full_iso_timestamp", "test_f5_a_text_fact_that_starts_like_a_timestamp_is_a_class_change"]),
    ("f6_baseline_overwrite_allowed",
     # two points: the existence pre-check AND the never-overwrite link (os.link refuses an existing target), so overwriting really becomes possible
     ['if os.path.exists(out) or os.path.exists(out + ".sha256"):', "        os.link(tmp, out)\n        try:"], ["if False:", "        os.replace(tmp, out)\n        try:"],
     ["test_f6_snapshot_never_overwrites_a_baseline"]),
    ("f6_sidecar_never_verified",
     "if not want or want[0].lower() != got:", "if False:",
     ["test_f6_compare_verifies_the_sha256_sidecar"]),
    ("f7_not_one_repeatable_read_transaction",
     'script = ["BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY"]', 'script = ["BEGIN"]',
     ["test_f7_read_state_is_one_repeatable_read_read_only_transaction"]),
    ("f7_no_subprocess_timeout",
     "env=_read_env(), timeout=_timeout_sec())", "env=_read_env())",
     ["test_f7_timeout_and_persistent_failure_have_a_defined_exit_and_a_report"]),
    ("f8_pgoptions_not_set",
     'env["PGOPTIONS"] = (env.get("PGOPTIONS", "") + " " + RO_PGOPTIONS).strip()', "pass",
     ["test_f7_read_state_is_one_repeatable_read_read_only_transaction", "test_f8_operator_pgoptions_are_kept_and_read_only_is_added"]),
    ("f8_read_only_session_not_proven",
     'if got["ro"] != [["on"]]:', "if False:",
     ["test_f8_a_session_that_is_not_read_only_reads_nothing"]),
    ("f8_phantom_chart_allowed",
     'if t.replace("-", "").startswith(PHANTOM_PREFIX):', "if False:",
     ["test_f8_phantom_chart_id_is_refused_whatever_the_shape"]),
    ("f7_dsn_not_scrubbed",
     r't = re.sub(r"(?i)(postgres(?:ql)?://)\S+", r"\1***", t)', "pass",
     ["test_f7_error_text_is_cut_to_200_chars_and_never_shows_a_dsn_or_password"]),
    ("f7_password_not_scrubbed",
     r't = re.sub(r"(?i)\b(password|passwd|pwd|pgpassword|secret|token)\b(\s*[=:]\s*)\S+", r"\1\2***", t)', "pass",
     ["test_f7_error_text_is_cut_to_200_chars_and_never_shows_a_dsn_or_password"]),
    ("f7_error_text_not_truncated",
     "return t[:200]", "return t",
     ["test_f7_error_text_is_cut_to_200_chars_and_never_shows_a_dsn_or_password"]),
    ("f7_incomplete_read_accepted",
     "if order != want:", "if False:",
     ["test_f7_a_reader_that_prints_only_the_last_result_set_is_an_incomplete_read"]),
    ("f18_column_count_unchecked",
     "if len(r) != ncols:", "if False:",
     ["test_f18_a_row_with_the_wrong_column_count_is_a_read_error"]),
    ("f21_empty_native_reads_as_alert",
     'if chart_id == NATIVE and cur["chart_facts"]:', "if chart_id == NATIVE:",
     ["test_f21_an_empty_current_native_is_an_empty_read_not_an_alert"]),
    ("m15_dasha_threshold_lowered",
     "moved = [x for x in v if abs(x) > 2.0]", "moved = [x for x in v if abs(x) > 0.5]",
     ["test_f4_dasha_shift_threshold_is_two_seconds"]),
    ("m18_never_passing_line_dropped",
     'L.append("NOT CHECKED items are never counted as passing" + (', 'L.append("" + (',
     ["test_f4_the_never_counted_as_passing_line_is_printed"]),
    ("m10_missing_anchor_row_reads_ok",
     "ok = bool(vals) and all(v == want for v in vals)", "ok = all(v == want for v in vals)",
     ["test_f4_an_anchor_row_missing_from_the_current_state_is_an_alert"]),
    ("m6_read_state_chart_filter_dropped",
     "from chart_facts where chart_id='{chart_id}' order by ayanamsha_id", "from chart_facts where true order by ayanamsha_id",
     ["test_f4_read_state_filters_by_chart_and_reads_only_that_chart"]),
    ("f10_registry_row_renamed",
     '{"id": "ga_medical", "table": "ga_medical"', '{"id": "ga_medical_x", "table": "ga_medical"',
     ["test_f10_standing_registry_names_every_known_unobserved_scope", "test_2_both_uncheckable_tier_changes_are_listed_on_every_compare"]),
    ("f15_snapshot_tool_version_hardcoded",
     '"tool_version": TOOL_VERSION, "chart_id": chart_id, "taken_at_utc": now', '"tool_version": "1.1", "chart_id": chart_id, "taken_at_utc": now',
     ["test_f15_snapshot_meta_carries_the_tool_version"]),
    ("f7_command_tags_treated_as_data",
     'if lines and lines[0] == "BEGIN":', "if False:",
     ["test_f7_psql_runs_quiet_and_command_tags_are_never_data"]),
    ("ss_empty_snapshot_accepted",
     "    if empties:\n        # the baseline is the evidence", "    if False:\n        # the baseline is the evidence",
     ["test_ss_a_snapshot_of_an_empty_read_is_refused_and_writes_nothing"]),
    ("ss_snapshot_temp_files_left_behind",
     "    finally:\n        for t in (tmp, tmp_sha):", "    finally:\n        for t in ():",
     ["test_ss_snapshot_write_is_atomic_and_leaves_no_temporary_file"]),
    ("ss_half_baseline_left_when_the_sidecar_cannot_be_linked",
     "            os.unlink(out)\n            raise", "            raise",
     ["test_ss_snapshot_write_is_atomic_and_leaves_no_temporary_file"]),
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
    pairs = list(zip(old, new)) if isinstance(old, list) else [(old, new)]
    for o, n in pairs:
        assert src.count(o) == 1, f"mutation anchor for {name} matches {src.count(o)} places (must be exactly 1): {o!r}"
        src = src.replace(o, n)
    mutated = tmp_path / "flip_detector.py"
    mutated.write_text(src)
    code, failed, tail = _run_tests(mutated, tmp_path, must_fail)  # only the named tests: each mutation costs one pytest start-up, not the whole file
    assert code == 1, f"mutation {name} left the test-suite green (or broke it differently): rc={code}\n{tail}"
    assert any(any(m in f for f in failed) for m in must_fail), f"mutation {name}: expected one of {must_fail} to fail, got {failed}"
