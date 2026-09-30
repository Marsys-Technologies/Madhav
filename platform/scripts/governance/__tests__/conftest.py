"""Conditional skips for tests that pin campaign artifacts absent from this branch.

E4.1-001 landing note. These tests were authored on `campaign/nikasha-test`, where
they assert properties of Nikasha-campaign documents / ledgers / derived artifacts
that are NOT part of this landing (T4 template, L0 v3 strategy, L0 pilot briefs,
asset_gaps.jsonl ledger, producer_provenance.derived.json). Each entry below skips
the test ONLY while its required input is absent, and the reason names the missing
file. The moment the input lands the skip disarms itself and the test runs for real.
A test not listed here is never skipped by this file. Tests that build their own
fixtures (tmp_path) are unaffected and run everywhere.
"""
import pathlib

import pytest

_REPO = pathlib.Path(__file__).resolve().parents[4]

_TEMPLATE = "00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md"
_STRATEGY = "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md"
_BRIEF = "00_ARCHITECTURE/briefs/nirmana/l0_assets/BG_ONTOLOGY_ELEVATION_BRIEF_v1_0.md"
_BRIEF_PANCH = "00_ARCHITECTURE/briefs/nirmana/l0_assets/BG_PANCHANGA_ELEVATION_BRIEF_v1_0.md"
_LEDGER = "00_ARCHITECTURE/control/asset_gaps.jsonl"
_DERIVED = "00_ARCHITECTURE/briefs/nirmana/nikasha_test/provenance/producer_provenance.derived.json"

# module file name -> (required path, None for every test in the module | set of test base names)
_CATALOG_PROVENANCE_REAL_ARTIFACT_TESTS = {
    "test_all_committed_exemption_producers_are_snapshot_backed",
    "test_all_committed_source_query_producers_are_snapshot_bound",
    "test_all_snapshot_declared_producers_are_present_in_the_committed_artifact",
    "test_check_fails_on_a_no_detector_reason_containing_a_trigger_substring_but_no_exact_prefix",
    "test_check_fails_on_a_prefixed_reason_whose_class_token_is_not_exact",
    "test_check_fails_on_a_route_evidence_reason_with_no_route_evidence_producer",
    "test_check_fails_on_a_service_probe_producer_for_an_unprobed_asset",
    "test_check_fails_when_a_fake_producer_is_appended_beside_a_real_one",
    "test_check_fails_when_a_fake_producer_is_placed_first_and_every_fake_is_named",
    "test_check_fails_when_a_real_claim_is_copied_onto_the_wrong_scu",
    "test_check_fails_when_a_real_service_probe_is_copied_onto_the_wrong_scu",
    "test_check_fails_when_a_reviewed_claim_is_demoted_beside_derived_producers",
    "test_check_fails_when_a_reviewed_scus_producers_are_erased_and_replaced_with_a_fake_reason",
    "test_check_fails_when_all_no_detector_scus_get_a_fake_route_evidence_only_producer",
    "test_check_fails_when_all_no_detector_scus_get_a_fake_source_query_producer",
    "test_check_fails_when_get_dignity_is_given_a_fake_reviewed_output_producer",
    "test_check_fails_when_temporal_activation_is_cut_to_route_evidence_with_the_honest_reason",
    "test_check_fails_when_temporal_activation_is_reduced_to_only_its_route_evidence_producer",
    "test_check_passes_on_the_real_committed_artifact_unmodified",
}
_REQUIRES = {
    "test_f7_l0v3_line526_320_gates.py": (_STRATEGY, None),
    "test_r63_t4_nine_gates.py": (_TEMPLATE, None),
    "test_r64_t4_nine_checks_heading.py": (_TEMPLATE, None),
    "test_r68_t4_na_spelling.py": (_TEMPLATE, None),
    "test_r69_l0v3_0_360_gates.py": (_STRATEGY, None),
    "test_r70_l0v3_stale_figures_datestamped.py": (_STRATEGY, None),
    "test_r77_l0_pilot_briefs_build_row.py": (_BRIEF, None),
    "test_catalog_provenance.py": (_DERIVED, _CATALOG_PROVENANCE_REAL_ARTIFACT_TESTS),
    "test_r15_r29_hand_row_census_run_id.py": (
        _LEDGER, {"test_real_ledger_has_zero_violations_today_every_row_predates_the_cutoff"}),
    "test_r80_schema_superseded_by_field.py": (
        _LEDGER, {"test_real_ledger_schema_row_now_documents_superseded_by"}),
    "test_r81_apply_script.py": (
        _LEDGER, {"test_real_ledger_is_confirmed_already_migrated_dry_run_only"}),
    "test_r81_ledger_overlap_fold.py": (_LEDGER, {
        "test_real_ledger_all_11_pairs_old_ids_are_now_superseded",
        "test_real_ledger_bg_panchanga_partial_overlap_left_its_census_siblings_untouched",
        "test_real_ledger_migration_is_now_a_confirmed_no_op",
        "test_real_ledger_schema_row_documents_superseded_by",
    }),
}


def pytest_collection_modifyitems(config, items):
    for item in items:
        entry = _REQUIRES.get(pathlib.Path(str(item.fspath)).name)
        if entry is None:
            continue
        required, only = entry
        name = getattr(item, "originalname", None) or item.name
        if only is not None and name not in only:
            continue
        if not (_REPO / required).exists():
            item.add_marker(pytest.mark.skip(
                reason=f"input absent on this branch (Nikasha campaign artifact, not landed): {required}"))
